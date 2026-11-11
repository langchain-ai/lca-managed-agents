---
name: render
description: Turn an SVG design into a PNG and look at it. Use after you write or change a design, but only if execute is one of your tools.
---

# Render a Design

**Only follow this if `execute` is one of your tools.** If it isn't, you don't have
a sandbox yet, so skip rendering, and don't ask a subagent to run anything for
you. Carry on with the rest of the request, including the critic's review: the
critic can read the SVG itself.

1. The first time in a thread, read `/skills/render/scripts/render.py` with
   `read_file`, and save a copy with `write_file` as `/workspace/render.py`.
   Your skills aren't inside the sandbox, so `cp` can't reach them.
2. Run `python /workspace/render.py /workspace/designs/<name>.svg`. It saves
   `/workspace/out/<name>.png`.
3. Look at the PNG with `read_file`. Check that no text runs past an edge, that
   everything is easy to read, and that it follows the brand.
4. If anything is wrong, fix the SVG and render again, with the same name.
