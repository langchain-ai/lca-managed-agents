"""Let the user pick a concept with buttons in Slack (Lab 3).

This is an agent-owned interrupt: the tool posts its own Slack message with one
button per concept, then calls interrupt() to pause the run until someone
clicks. The agent should render the concepts and attach them with the built-in
upload_files tool first, so people can see what they're choosing between.
"""

from __future__ import annotations

import json

import httpx
from langchain.tools import tool
from langgraph.types import interrupt
from langsmith import uuid7
from managed_deepagents import INTERRUPT_CORRELATION_KEY, ManagedDeepAgentRuntime, connections


@tool(parse_docstring=True)
async def choose_concept(question: str, options: list[str], runtime: ManagedDeepAgentRuntime) -> str:
    """Ask the user to pick one concept, with a button for each option.

    Attach the concept images with upload_files before calling this.

    Args:
        question: The question to show, like "Which direction should I take?".
        options: Two to four short concept labels, like ["A: Bold type", "B: Photo-led"].
    """
    if not 2 <= len(options) <= 4:
        return "Offer between two and four concepts."
    channel = runtime.channel
    if channel is None or channel.provider != "slack":
        return "Concept buttons only work in Slack. Ask the user in chat which concept they prefer."

    correlation_id = str(uuid7())
    # The tool runs again from the top when the run resumes, so only post on the first pass.
    if channel.event["type"] != "user_prompt_response":
        await _post_buttons(channel.raw_event, question, options, correlation_id)

    response = interrupt({INTERRUPT_CORRELATION_KEY: correlation_id})
    choice = options[int(response["action"].removeprefix("concept-"))]
    return f"The user chose: {choice}"


async def _post_buttons(raw_event: dict, question: str, options: list[str], correlation_id: str) -> None:
    bot_token = await connections.get("mda/slack-bot-token", {"type": "agent"})
    value = json.dumps({INTERRUPT_CORRELATION_KEY: correlation_id})
    buttons = [
        {"type": "button", "action_id": f"concept-{i}", "text": {"type": "plain_text", "text": label[:75]}, "value": value}
        for i, label in enumerate(options)
    ]
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {bot_token}"},
            json={
                "channel": raw_event["channel"],
                "thread_ts": raw_event.get("thread_ts") or raw_event["ts"],
                "text": question,
                "blocks": [
                    {"type": "section", "text": {"type": "mrkdwn", "text": question}},
                    {"type": "actions", "elements": buttons},
                ],
            },
        )
