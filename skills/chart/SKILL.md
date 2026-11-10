---
name: chart
description: Recipe for on-brand bar charts drawn in SVG, for comparisons and trends across several numbers. Use when someone asks for a chart, a graph, or a visual comparison of numbers.
---

# Chart

Draw charts directly in SVG, with a `<rect>` per bar, so every color and font
goes through the brand check. Default format: `square` (1080x1080).

Colors and fonts below are **roles**. Look up the actual hex values and font
names in `brand-guidelines`.

## Rules

- **Bar charts start at zero.** Work out the scale first: bar height = value / max value x the plot height.
- **Label every bar with its exact value**, centered above the bar, in the body font.
- Draw the bars in **primary**. Use **accent** for at most one bar you want to call out.
- A title that says what the chart shows, like "Orders this week", in the heading font, in **primary**.
- A baseline under the bars, in **text**, and category labels under it, in **muted**.
- A source line at the bottom, in **muted**.
- No gridlines, no 3D, no legend when there's only one series.

## Working out the geometry

On a square canvas, a good plot runs from x=88 to x=992, with its baseline at y=880 and a height of 560px.

For `n` bars with a `gap` of 28px between them:

- bar width = (992 - 88 - gap x (n - 1)) / n
- bar `i` starts at x = 88 + i x (bar width + gap)
- a bar's top = 880 - its height; its value label sits 16px above that, at the bar's center, with `text-anchor="middle"`

Compute these numbers carefully before you write the SVG.

## Checks before you call it done

- Every value in the data appears on the chart, exactly.
- The tallest bar and its label fit inside the canvas.
