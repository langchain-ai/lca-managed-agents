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

### Optional: use LangSmith LLM Gateway

Direct Anthropic access remains the default and requires your actual
`ANTHROPIC_API_KEY`. To route this agent's chat calls through
[LangSmith LLM Gateway](https://docs.langchain.com/langsmith/llm-gateway-direct-model-access),
add these values to `.env` before starting `mda dev`:

```dotenv
LANGSMITH_GATEWAY=true
LANGSMITH_API_KEY=lsv2_...
```

Replace the placeholder with your real LangSmith key. Configure an Anthropic
provider secret in that key's workspace and enable access to the model selected
in `agent.py`. The dependencies require `langchain-anthropic>=1.5.1` and
`langchain-core>=1.5.3` for gateway routing, LangSmith key fallback, and an empty
flag behaving as direct access. You do not need to replace the model string.
The chat integration does not need a local Anthropic key in gateway mode, but
Managed Deep Agents CLI credential checks have a separate limitation below.
Optionally set `LANGSMITH_GATEWAY_API_KEY` to a separate gateway key; otherwise
chat calls use `LANGSMITH_API_KEY`. Keep `LANGSMITH_API_KEY` for Managed Deep Agents
authentication. Do not put a gateway key in `ANTHROPIC_API_KEY`.

Use `true`, `1`, or `yes` for the default US gateway, or set `LANGSMITH_GATEWAY` to a
regional root URL such as `https://eu.gateway.smith.langchain.com`. The integration
appends `/anthropic`. Unset the flag or use `false`, `0`, `no`, or an empty value to
return to direct access. Remove `ANTHROPIC_API_URL` and `ANTHROPIC_BASE_URL`
overrides, which take precedence over the flag. `LANGSMITH_ENDPOINT` configures the LangSmith API, not the gateway;
tracing settings do not switch model routing.

`mda dev` stages the project's `.env` for the local runtime. With the locked
Managed Deep Agents CLI, the unchanged `anthropic:` model string still triggers
an Anthropic-key check: local development can warn about a missing key even when
gateway routing works, and `mda deploy` requires a real `ANTHROPIC_API_KEY` as a
deployment secret. Keep that credential for deployment preflight; do not replace
it with a LangSmith key. The CLI does not infer gateway mode from this flag.

For deployment, include the gateway variables and credentials in the deployment's
secrets as well, then verify its model call. A flag exported only in your terminal
does not configure an already-running hosted agent. Keep Slack, sandbox, MCP,
and other runtime credentials required by later labs; model routing does not
replace them.

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
