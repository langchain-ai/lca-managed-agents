"""Render a design to a PNG.

The agent writes each design as an SVG. This module sizes it to the brand
format, renders it with resvg (a small renderer, no browser needed), and
returns the PNG plus a report of what was actually drawn.

Where it renders:
- In a deployment or `mda dev`, inside the thread's **sandbox** (Module 2).
  Files live under /workspace, so in Slack the agent can attach them with the
  built-in `upload_files` tool.
- In an eval run there's no sandbox, so it renders in the eval container itself,
  under /app, where the Harbor verifiers look for files.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from studio.brand import BRAND_PATH, check_report, format_size, load_brand

SCRIPT = Path(__file__).resolve().parent / "scripts" / "render_svg.py"
SANDBOX_ROOT = "/workspace"
_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}$")
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.IGNORECASE | re.DOTALL)


@dataclass
class RenderResult:
    name: str
    fmt: str
    png_path: str
    png: bytes
    report: dict[str, Any]
    problems: list[str] = field(default_factory=list)


def check_name(name: str) -> None:
    if not _NAME.match(name):
        raise ValueError("Use a short lowercase name with hyphens, like 'launch-card'.")


def prepare_svg(svg: str, width: int, height: int) -> str:
    """Size the SVG's root element to the format, whatever the agent wrote there."""
    match = _SVG_OPEN.search(svg)
    if not match:
        raise ValueError("The design must be a single <svg> element.")
    tag = match.group(0)
    for attr in ("width", "height", "xmlns"):
        tag = re.sub(rf'\s{attr}\s*=\s*("[^"]*"|\'[^\']*\')', "", tag)
    if not re.search(r"\sviewBox\s*=", tag):
        tag = tag[:-1].rstrip("/") + f' viewBox="0 0 {width} {height}">'
    tag = tag.replace("<svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"', 1)
    return svg[: match.start()] + tag + svg[match.end():]


def is_sandbox(backend: Any) -> bool:
    return backend is not None and hasattr(backend, "aexecute")


def output_root(backend: Any) -> str:
    if is_sandbox(backend):
        return SANDBOX_ROOT
    configured = os.environ.get("STUDIO_WORKDIR")
    if configured:
        return configured
    if os.path.isdir("/app") and os.access("/app", os.W_OK):
        return "/app"
    return str(Path(tempfile.gettempdir()) / "design-studio")


def _parse_report(output: str) -> dict[str, Any]:
    for line in reversed(output.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"The renderer did not return a report. Output:\n{output[-2000:]}")


async def render(backend: Any, name: str, fmt: str, svg: str) -> RenderResult:
    check_name(name)
    brand = load_brand()
    width, height = format_size(fmt, brand)
    design = prepare_svg(svg, width, height)
    if is_sandbox(backend):
        result = await _render_in_sandbox(backend, name, fmt, design)
    else:
        result = await _render_locally(name, fmt, design)
    result.problems = check_report(result.report, fmt, brand)
    return result


async def _render_in_sandbox(backend: Any, name: str, fmt: str, design: str) -> RenderResult:
    root = SANDBOX_ROOT
    studio = f"{root}/.studio"
    script, brand_path, fonts = f"{studio}/render_svg.py", f"{studio}/brand.json", f"{studio}/fonts"
    svg_path, png_path, report_path = f"{root}/designs/{name}.svg", f"{root}/out/{name}.png", f"{root}/out/{name}.report.json"

    await backend.aexecute(f"mkdir -p {studio} {root}/designs {root}/out")
    uploads = await backend.aupload_files([
        (script, SCRIPT.read_bytes()),
        (brand_path, BRAND_PATH.read_bytes()),
        (svg_path, design.encode()),
    ])
    errors = [u.error for u in uploads if getattr(u, "error", None)]
    if errors:
        raise RuntimeError(f"Could not write to the sandbox: {errors}")

    response = await backend.aexecute(f"python3 {script} {svg_path} {png_path} {brand_path} {fonts}")
    if getattr(response, "exit_code", 0):
        raise RuntimeError(f"Rendering failed:\n{response.output[-2000:]}")
    report = _parse_report(response.output)

    await backend.aupload_files([(report_path, json.dumps(report, indent=2).encode())])
    downloaded = (await backend.adownload_files([png_path]))[0]
    if getattr(downloaded, "error", None) or downloaded.content is None:
        raise RuntimeError("The rendered PNG could not be read back from the sandbox.")
    return RenderResult(name, fmt, png_path, downloaded.content, report)


async def _render_locally(name: str, fmt: str, design: str) -> RenderResult:
    root = Path(output_root(None))
    for folder in ("designs", "out", ".studio/fonts"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    svg_path, png_path = root / "designs" / f"{name}.svg", root / "out" / f"{name}.png"
    svg_path.write_text(design)

    process = await asyncio.create_subprocess_exec(
        sys.executable, str(SCRIPT), str(svg_path), str(png_path), str(BRAND_PATH), str(root / ".studio" / "fonts"),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await process.communicate()
    output = stdout.decode(errors="replace")
    if process.returncode:
        raise RuntimeError(f"Rendering failed:\n{output[-2000:]}")
    report = _parse_report(output)
    (root / "out" / f"{name}.report.json").write_text(json.dumps(report, indent=2))
    return RenderResult(name, fmt, str(png_path), png_path.read_bytes(), report)


async def read_design(backend: Any, name: str) -> tuple[bytes, dict[str, Any]]:
    """Read back a design that was already rendered."""
    check_name(name)
    root = output_root(backend)
    png_path, report_path = f"{root}/out/{name}.png", f"{root}/out/{name}.report.json"
    if is_sandbox(backend):
        png, report = await backend.adownload_files([png_path, report_path])
        if getattr(png, "error", None) or png.content is None:
            raise FileNotFoundError(f"No design named {name!r}. Render it first.")
        return png.content, json.loads(report.content or b"{}")
    if not Path(png_path).exists():
        raise FileNotFoundError(f"No design named {name!r}. Render it first.")
    return Path(png_path).read_bytes(), json.loads(Path(report_path).read_text())
