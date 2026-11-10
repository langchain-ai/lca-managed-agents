# Design Studio: Starter Repo

The starting point for the Managed Agents course labs. Across three labs,
you'll turn this repo into your own design agent: one that makes finished,
on-brand graphics for a brand you create, works from your own documents, and
lives in Slack.

**Most of the code is already written.** The renderer, most of the tools, the
middleware's logic, and the gallery app are all here. Your job in the labs is
mostly the Managed Agents part: putting each piece in the right place and wiring
it up. You'll also create your own brand, and write a skill and a tool. Look for
`TODO (Lab N)` comments.

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
| `agent.py` | The agent definition | Wire in tools, middleware, and subagents (Labs 1 to 3) |
| `instructions.md` | The agent's always-on guidance | Read it (Lab 1) |
| `skills/` | Brand guidelines, the request process, and one skill per kind of graphic | Write your brand guidelines and a new skill (Lab 1) |
| `brand/brand.json` | Your brand, as data that code can check | Fill it in (Lab 1) |
| `tools/design.py` | Render, view, and publish designs | Write `view_design`, then wire them in (Lab 1) |
| `tools/data.py` | Data the agent owns, for scheduled work | Wire in (Lab 2) |
| `tools/scheduling.py` | Tools for users to set up their own schedules | Optional: a Lab 2 stretch goal |
| `tools/concepts.py` | Concept buttons in Slack | Wire in (Lab 3) |
| `middleware/brand_lint.py` | Blocks off-brand designs before they render | Wire in (Lab 1) |
| `prompts.py` | The subagents' system prompts | Use in your subagents (Lab 1) |
| `studio/` | The renderer and brand checks. You won't need to change it. | Nothing |
| `data/` | Sample weekly numbers | Use in Lab 2 |
| `examples/northbeam/` | A complete example brand | Use as a reference (Lab 1) |
| `frontend/streamlit_app.py` | A request form and gallery, outside Slack | Optional: a Lab 3 stretch goal |

You'll also **create** these, each in its lab: `tools/mcp.py`, `sandbox/`,
`schedules/`, and `channels/`.

## Your Brand

In Lab 1, you'll choose a company, real or made up, and describe its brand in two places:

1. `brand/brand.json`: its colors, its fonts from [Google Fonts](https://fonts.google.com), and its contrast rule. Code checks every design against this file.
2. `skills/brand-guidelines/SKILL.md`: the same brand in plain language, so the agent knows how to design for it.

For a complete example, see `examples/northbeam/`, a made-up coffee roaster.
