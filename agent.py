# agent.py
#
# Your design studio's agent. Each lab adds to this file: look for the TODOs.
# Most of what it needs, like the tools and middleware, is already written.
# Your job is to wire it in, plus write a skill and a tool of your own in Lab 1.
from managed_deepagents import define_deep_agent

# TODO (Lab 1): write view_design in tools/design.py, then import the three
#               design tools,
#               the brand_lint middleware from middleware/brand_lint.py,
#               and CRITIC_PROMPT from prompts.py.
# TODO (Lab 2): import get_weekly_metrics from tools/data.py.
# TODO (Lab 3): import choose_concept from tools/concepts.py.

agent = define_deep_agent(
    name="design-studio",
    model="anthropic:claude-sonnet-4-6",
    # TODO (Lab 1): give the agent its tools.
    # TODO (Lab 1): pause for a person's approval before it publishes.
    # TODO (Lab 1): run the brand-lint middleware around every tool call.
    # TODO (Lab 1): add the critic subagent.
)
