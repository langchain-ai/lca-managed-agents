"""Slack tools (Lab 3). You wire these in, but you don't need to change them.

- publish_design: posts a finished design's PNG to a public Slack channel. It's
  listed in `interrupt_on` (Lab 1), so a person approves every publish.
- choose_concept: an agent-owned interrupt. It posts its own Slack message with a
  button per concept, then pauses the run until someone clicks. interrupt_on can
  only show Approve and Reject, so a choice needs its own buttons.
"""

import json
import os

import httpx
from langchain.tools import tool
from langgraph.types import interrupt
from langsmith import uuid7
from managed_deepagents import INTERRUPT_CORRELATION_KEY, ManagedDeepAgentRuntime, connections


@tool(parse_docstring=True)
async def publish_design(name: str, caption: str, runtime: ManagedDeepAgentRuntime) -> str:
    """Publish a finished design to the brand's public channel.

    Only publish when the user asks you to. A person approves every publish.

    Args:
        name: The design's name, like "launch-card". Its PNG must be at /workspace/out/<name>.png.
        caption: A short caption to post with the design.
    """
    channel_id = os.environ.get("PUBLIC_SLACK_CHANNEL_ID")
    if not channel_id:
        return f"Approved {name}. There's no public channel set up yet, so nothing was posted."

    png = (await runtime.backend.adownload_files([f"/workspace/out/{name}.png"]))[0]
    if png.error or png.content is None:
        return f"There's no PNG for {name!r} yet. Render it first."

    # Slack's upload flow: get an upload URL, send the file, then share it in the channel.
    token = await connections.get("mda/slack-bot-token", {"type": "agent"})
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=60) as client:
        upload = (await client.post(
            "https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            data={"filename": f"{name}.png", "length": str(len(png.content))},
        )).json()
        await client.post(upload["upload_url"], content=png.content)
        done = (await client.post(
            "https://slack.com/api/files.completeUploadExternal",
            headers=headers,
            json={"files": [{"id": upload["file_id"]}], "channel_id": channel_id, "initial_comment": caption},
        )).json()
    return f"Published {name} to Slack." if done.get("ok") else f"Slack said: {done.get('error')}"


@tool(parse_docstring=True)
async def choose_concept(question: str, options: list[str], runtime: ManagedDeepAgentRuntime) -> str:
    """Ask the user to pick one concept, with a button for each option.

    Attach the concept images with upload_files before calling this.

    Args:
        question: The question to show, like "Which direction should I take?".
        options: Two to four short concept labels, like ["A: Bold type", "B: Big number"].
    """
    channel = runtime.channel
    if channel is None or channel.provider != "slack":
        return "Concept buttons only work in Slack. Ask the user in chat which concept they prefer."

    correlation_id = str(uuid7())
    # When the run resumes, the tool runs again from the top, so only post on the first pass.
    if channel.event["type"] != "user_prompt_response":
        event = channel.raw_event
        value = json.dumps({INTERRUPT_CORRELATION_KEY: correlation_id})
        buttons = [
            {"type": "button", "action_id": f"concept-{i}", "text": {"type": "plain_text", "text": label[:75]}, "value": value}
            for i, label in enumerate(options)
        ]
        token = await connections.get("mda/slack-bot-token", {"type": "agent"})
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "channel": event["channel"],
                    "thread_ts": event.get("thread_ts") or event["ts"],
                    "text": question,
                    "blocks": [
                        {"type": "section", "text": {"type": "mrkdwn", "text": question}},
                        {"type": "actions", "elements": buttons},
                    ],
                },
            )

    response = interrupt({INTERRUPT_CORRELATION_KEY: correlation_id})
    return f"The user chose: {options[int(response['action'].removeprefix('concept-'))]}"
