---
name: design-request
description: The step-by-step process for any design request, from a vague idea to a finished PNG. Use whenever someone asks you to make, change, or resize a graphic.
---

# Handling a Design Request

## 1. Understand the ask

Work out four things: **what** it is, **where** it's going (which format),
**the exact copy**, and **any data**. If something important is missing, ask at
most two short questions. Otherwise, decide and say what you decided.

If the content lives in the user's own documents, like "from my launch doc",
read it with the Notion tools. If the user hasn't connected Notion yet, the run
pauses and they're asked to sign in.

## 2. Pick the skill for the asset

| The user wants... | Load this skill | Default format |
| --- | --- | --- |
| An announcement, a launch, or an event | `social-card` | `social-card` |
| One headline number, like a metric or milestone | `stat-card` | `square` |
| A comparison or trend across several numbers | `chart` | `square` |

For anything else, follow the brand guidelines and pick the closest format.

## 3. Concepts, when the ask is open-ended

If the user left the direction open ("make something for our launch"), render
**two or three** small variations with different names (`launch-a`, `launch-b`).
In Slack, attach them with `upload_files`, then call `choose_concept` so the user
can pick with a button. Outside Slack, show them and ask which one to continue.

Skip this step when the request is specific.

## 4. Render, look, fix

1. Write the design as an SVG (see **Writing the SVG** below) and call `render_design`.
2. If the brand check fails, or the image has any problem (text past an edge,
   cramped spacing, weak hierarchy), fix it and render again with the same name.
   SVG text doesn't wrap, so a line that's too long needs a manual line break.
3. When it looks right, send it to the `critic` subagent and apply its fixes.

## 5. Other formats

If the user wants the design in more formats, finish and approve the first one,
then hand each extra format to the `format-studio` subagent, all in the same
turn, so they're made in parallel. Look at each result before you deliver it.

## 6. Deliver

Attach the final PNG (in Slack, with `upload_files`) and say what you made in a
sentence or two. Only call `publish_design` if the user asked you to publish or
post it publicly.

## Writing the SVG

- **Colors and fonts come from `brand-guidelines`.** The asset skills describe
  colors and fonts by role, like "primary" or "the heading font". Use the exact
  hex values and font names that `brand-guidelines` gives for each role.
- **Set colors and fonts with attributes**, like `fill="#1F3A2E"` and
  `font-family="Inter"`, not CSS classes.
- **SVG text never wraps.** Put each line in its own `<tspan x="..." dy="...">`,
  with `dy` about 1.15 times the font size for headlines and 1.4 times for body
  text. Break lines between words, at natural pauses.
- **Estimate line length before you render.** One line holds about
  (available width / font size) x 1.8 characters. The render report tells you
  exactly which lines run past an edge, so fix those by breaking the line or
  making the text smaller.
- **Write uppercase text in uppercase letters.** SVG has no text-transform.
