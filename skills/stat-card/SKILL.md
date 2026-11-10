---
name: stat-card
description: Layout recipe for a card built around one headline number, like a weekly metric, a milestone, or a survey result. Use when someone asks for a stat card or wants to highlight a number.
---

# Stat Card

One number, big. Everything else supports it. Default format: `square` (1080x1080).

Colors and fonts below are **roles**. Look up the actual hex values and font
names in `brand-guidelines`.

## Getting the number

- Use the exact number from the source, formatted with thousands separators (1,284, not 1284).
- For weekly numbers, call `get_weekly_metrics`. For anything else, use the
  number the user gave you, or a source you can name.
- Always include a source line saying where the number came from.

## Layout

Use the **background** color as the canvas.

1. **The number:** heading font, weight 700, 220 to 320px, in **primary**. Its baseline sits just below the middle of the canvas.
2. **Label:** what the number counts, body font, weight 600, 40 to 48px, in **text**, about 100px below the number's baseline.
3. **Context** (optional): the change, like "Up 7.3% from last week", body font, weight 500, 32px. Highlight just the change with a small **accent** box behind it, and make sure the text on the box passes contrast.
4. **Source:** body font, weight 400, 24px, in **muted**, at the bottom left.

Keep a 96px margin on every side, and left-align everything.

## Checks before you call it done

- The number matches the source exactly.
- The number is the first thing you see.
