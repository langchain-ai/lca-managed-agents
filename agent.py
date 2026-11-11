# agent.py
#
# Your design studio's agent. Each lab adds to this file: look for the TODOs.
from managed_deepagents import define_deep_agent

# TODO (Lab 1): import get_brand from tools/brand.py (once you've written it),
#               brand_lint from middleware/brand_lint.py,
#               and publish_design from tools/slack_tools.py.
# TODO (Lab 2): import get_weekly_metrics from tools/data.py.
# TODO (Lab 3): import choose_concept from tools/slack_tools.py.

agent = define_deep_agent(
    name="design-studio",
    model="anthropic:claude-sonnet-4-6",
    # TODO (Lab 1): give the agent its tools.
    # TODO (Lab 1): pause for a person's approval before it publishes.
    # TODO (Lab 1): run the brand-lint middleware around every tool call.
    # TODO (Lab 1): add the critic subagent.
)
