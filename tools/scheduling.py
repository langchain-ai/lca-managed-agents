"""Let users set up their own recurring designs (Lab 2).

A runtime schedule with a `user` owner runs as the person who asked, so it can
use their own connections, like their Notion. Declared schedules can't.
"""

from __future__ import annotations

from langchain.tools import tool
from managed_deepagents import ManagedDeepAgentRuntime


@tool(parse_docstring=True)
async def schedule_for_me(
    prompt: str, cron: str, runtime: ManagedDeepAgentRuntime, timezone: str = "UTC"
) -> str:
    """Make a design for the current user on a recurring schedule.

    Args:
        prompt: What to make each time, written as a request to yourself.
        cron: A five-field cron expression, like "0 9 * * 5" for 9am every Friday.
        timezone: An IANA time zone, like "America/New_York".
    """
    item = await runtime.schedules.create(owner={"type": "user"}, cron=cron, timezone=timezone, prompt=prompt)
    return f"Created schedule {item['id']}."


@tool
async def list_my_schedules(runtime: ManagedDeepAgentRuntime) -> str:
    """List the current user's recurring designs, with their IDs."""
    page = await runtime.schedules.list(owner={"type": "user"}, limit=20)
    return str(page["items"])


@tool(parse_docstring=True)
async def cancel_my_schedule(schedule_id: str, runtime: ManagedDeepAgentRuntime) -> str:
    """Cancel one of the current user's recurring designs.

    Args:
        schedule_id: The schedule's ID, from list_my_schedules.
    """
    await runtime.schedules.delete(schedule_id, owner={"type": "user"})
    return f"Canceled schedule {schedule_id}."
