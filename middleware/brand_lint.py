"""Brand-lint middleware (Lab 1): the brand is code.

Runs around every render_design call. Before anything renders, it reads the
design's SVG and checks every color and font against brand/brand.json. If it
finds a problem, the tool never runs, and the agent gets the list of fixes
instead. The agent never decides whether this check happens.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

from studio.brand import lint_source


@wrap_tool_call
async def brand_lint(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
) -> ToolMessage | Command:
    call = request.tool_call
    if call["name"] == "render_design":
        problems = lint_source(call["args"].get("svg", ""))
        if problems:
            return ToolMessage(
                content="Not rendered. Fix these brand problems and try again:\n- " + "\n- ".join(problems),
                tool_call_id=call["id"],
                name=call["name"],
                status="error",
            )
    return await handler(request)
