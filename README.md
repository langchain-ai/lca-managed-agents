# Design Studio: Starter Repo

The starting point for the Managed Agents course labs. Across three labs,
you'll turn this repo into your own design agent: one that makes on-brand
graphics for a brand you create, works from your own documents, and lives in Slack.

The agent draws each design as an SVG. Once it has a sandbox (Lab 2), it turns
the SVG into a PNG and looks at its own work. Look for `TODO (Lab N)` comments.

## Get Started

```bash
uv sync
cp .env.example .env    # add LANGSMITH_API_KEY and ANTHROPIC_API_KEY
mda dev
```

Then open the Module 1 lab.

## What's Here

| Path | What it is | You'll... |
| --- | --- | --- |
| `agent.py` | The agent definition | Wire everything in (Labs 1 to 3) |
| `instructions.md` | How the agent handles every request | Read it (Lab 1) |
| `brand.json` | Your brand, as data that code can check | Fill it in (Lab 1) |
| `tools/brand.py` | Looks up the brand's exact values | Write `get_brand` (Lab 1) |
| `middleware/brand_lint.py` | Blocks off-brand designs before they're saved | Wire in (Lab 1) |
| `skills/` | Your brand guidelines, a recipe for each kind of graphic, and `render` | Write your brand guidelines and a new skill (Lab 1) |
| `tools/data.py` | Data the agent owns, for scheduled work | Wire in (Lab 2) |
| `tools/slack_tools.py` | Publishing and concept buttons in Slack | Wire in (Labs 1 and 3) |
| `identity.py` | Who's calling. Schedules and Slack need it | Nothing: it's already set up |
| `data/` | Sample weekly numbers | Use in Lab 2 |
| `examples/northbeam/` | A complete example brand | Use as a reference if you get stuck (Lab 1) |

You'll also **create** these, each in its lab: `tools/mcp.py`, `sandbox/`,
`schedules/`, and `channels/`.
