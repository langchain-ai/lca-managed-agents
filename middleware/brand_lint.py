"""Brand-lint middleware (Lab 1): the brand is enforced in code.

Runs around every tool call. When the agent saves an SVG, it checks every color
and font against brand.json first. If it finds one that isn't in the brand, the
file is never saved, and the agent gets the problems back instead. The agent
never decides whether this check happens.
"""

import re

from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

from tools.brand import load_brand


def find_problems(svg: str) -> list[str]:
    """Every color and font in an SVG that isn't in the brand."""
    brand = load_brand()
    colors = {c.lower() for c in brand["colors"].values()}
    fonts = {f.lower() for f in brand["fonts"].values()}
    used_colors = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", svg)}
    problems = [f"{c} isn't a brand color" for c in sorted(used_colors - colors)]
    for family in sorted(set(re.findall(r"font-family\s*[=:]\s*[\"']?([^\"';>]+)", svg))):
        first = family.split(",")[0].strip().strip("'\"")
        if first.lower() not in fonts:
            problems.append(f"{first} isn't a brand font")
    return problems


@wrap_tool_call
async def brand_lint(request, handler):
    call = request.tool_call
    args = call["args"]
    if call["name"] in ("write_file", "edit_file") and str(args.get("file_path", "")).endswith(".svg"):
        problems = find_problems(args.get("content") or args.get("new_string") or "")
        if problems:
            return ToolMessage(
                content="Not saved. Fix these brand problems and try again:\n- " + "\n- ".join(problems),
                tool_call_id=call["id"],
                name=call["name"],
                status="error",
            )
    return await handler(request)
