"""Tools for making, reviewing, and publishing designs.

- render_design (Lab 1, moved into the sandbox in Lab 2): render an SVG design
  to a PNG, check it against the brand, and show the image to the model so it
  can look at its own work.
- view_design (Lab 1): you write this one. It looks at a design that was
  already rendered, and the critic subagent uses it.
- publish_design (Lab 1, posts to Slack in Lab 3): share a finished design.
  It's listed in `interrupt_on`, so a person must approve every publish.
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

import httpx
from langchain.tools import tool
from managed_deepagents import ManagedDeepAgentRuntime, connections

from studio.brand import load_brand
from studio.render import is_sandbox, output_root, read_design, render


def _image_block(png: bytes) -> dict[str, Any]:
    return {"type": "image", "base64": base64.b64encode(png).decode(), "mime_type": "image/png"}


def _summary(report: dict[str, Any], problems: list[str]) -> str:
    lines = [
        f"Canvas: {report.get('width')}x{report.get('height')}",
        f"Colors drawn: {', '.join(report.get('colors', []))}",
        f"Fonts drawn: {', '.join(report.get('fonts', []))}",
        f"Lowest text contrast: {report.get('min_contrast')}:1",
    ]
    unmeasured = [line["text"] for line in report.get("lines", []) if not line.get("measured")]
    if unmeasured:
        lines.append(f"Couldn't measure (check these fit by eye): {'; '.join(unmeasured)}")
    if problems:
        lines.append("Brand check FAILED:\n- " + "\n- ".join(problems))
    else:
        lines.append("Brand check passed.")
    return "\n".join(lines)


@tool(parse_docstring=True)
async def render_design(name: str, format: str, svg: str, runtime: ManagedDeepAgentRuntime) -> list[dict[str, Any]]:
    """Render an SVG design to a PNG, check it against the brand, and show you the result.

    Always look at the returned image before calling a design finished. Rendering
    again with the same name replaces the earlier version.

    Args:
        name: Short file name for the design, lowercase with hyphens, like "launch-card".
        format: One of the brand formats, like "social-card", "square", "story", or "slide".
        svg: The design as one <svg> element. It's sized to the format for you, so draw on a canvas of the format's width and height. Use only the brand's hex colors and fonts. SVG text doesn't wrap, so put each line in its own <text> or <tspan>.
    """
    try:
        result = await render(runtime.backend, name, format, svg)
    except (ValueError, RuntimeError) as error:
        return [{"type": "text", "text": f"Not rendered: {error}"}]
    text = f"Rendered {result.png_path}\n" + _summary(result.report, result.problems)
    return [{"type": "text", "text": text}, _image_block(result.png)]


async def _look_at_design(name: str, runtime: ManagedDeepAgentRuntime) -> list[dict[str, Any]]:
    """The logic behind view_design: read a rendered design and show it with its report."""
    try:
        png, report = await read_design(runtime.backend, name)
    except (ValueError, FileNotFoundError) as error:
        return [{"type": "text", "text": str(error)}]
    return [{"type": "text", "text": _summary(report, [])}, _image_block(png)]


# TODO (Lab 1): write the view_design tool. It lets the agent (and the critic
# subagent) look at a design that was already rendered. The logic is written for
# you in _look_at_design above. You write the parts that make it a tool:
#
#   - the @tool(parse_docstring=True) decorator
#   - its name, view_design, as an async function
#   - its parameters, with type hints: the design's name, and the injected
#     runtime (ManagedDeepAgentRuntime), just like render_design
#   - its return type, the same as render_design's
#   - a docstring: one line on what it does, plus an Args: section for name
#
# Its body is one line:  return await _look_at_design(name, runtime)


@tool(parse_docstring=True)
async def publish_design(name: str, caption: str, runtime: ManagedDeepAgentRuntime) -> str:
    """Publish a finished design to the brand's public channel and gallery.

    Only publish when the user asks you to. A person approves every publish.

    Args:
        name: The design's name, as passed to render_design.
        caption: A short caption to post with the design.
    """
    try:
        png, report = await read_design(runtime.backend, name)
    except (ValueError, FileNotFoundError) as error:
        return str(error)

    record = {"name": name, "caption": caption, "published_at": int(time.time())}
    where: list[str] = []

    # Lab 3: post to the public Slack channel, if one is configured.
    channel_id = os.environ.get("PUBLIC_SLACK_CHANNEL_ID")
    if channel_id:
        await _post_to_slack(channel_id, f"{name}.png", png, caption)
        where.append("Slack")

    # Lab 3 (frontend): save to the shared gallery the Streamlit app reads.
    if runtime.store is not None:
        await runtime.store.aput(
            ("gallery",),
            name,
            {**record, "brand": load_brand()["name"], "png_base64": base64.b64encode(png).decode()},
        )
        where.append("the gallery")

    # Always leave a record next to the design. Evals check for it.
    path = f"{output_root(runtime.backend)}/published/{name}.json"
    if is_sandbox(runtime.backend):
        await runtime.backend.aupload_files([(path, json.dumps(record).encode())])
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(record, f)

    return f"Published {name} to {' and '.join(where) or 'the local record only'}."


async def _post_to_slack(channel_id: str, filename: str, content: bytes, caption: str) -> None:
    """Upload a file to a Slack channel with the bot token of the Slack app MDA set up."""
    token = await connections.get("mda/slack-bot-token", {"type": "agent"})
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        ticket = (await client.post(
            "https://slack.com/api/files.getUploadURLExternal",
            headers=headers,
            data={"filename": filename, "length": str(len(content))},
        )).json()
        if not ticket.get("ok"):
            raise RuntimeError(f"Slack upload failed: {ticket.get('error')}")
        (await client.post(ticket["upload_url"], content=content)).raise_for_status()
        done = (await client.post(
            "https://slack.com/api/files.completeUploadExternal",
            headers=headers,
            json={
                "files": [{"id": ticket["file_id"], "title": filename}],
                "channel_id": channel_id,
                "initial_comment": caption,
            },
        )).json()
        if not done.get("ok"):
            raise RuntimeError(f"Slack upload failed: {done.get('error')}")
