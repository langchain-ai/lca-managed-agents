"""Load the brand and check designs against it.

`brand/brand.json` is the machine-readable brand. The `brand-guidelines` skill
tells the model *how* to design for the brand; this module lets code *check*
that it did. The brand-lint middleware, the render tool, and the evals all use it.

Designs are SVG, so lint_source reads SVG attributes and inline styles.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

BRAND_PATH = Path(__file__).resolve().parent.parent / "brand" / "brand.json"

GENERIC_FONTS = {"serif", "sans-serif", "monospace", "system-ui", "inherit", "initial", "unset"}

_HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_RAW_COLOR_FUNCTION = re.compile(r"\b(?:rgba?|hsla?)\(", re.IGNORECASE)
_NAMED_COLOR = re.compile(r"\b(?:fill|stroke|stop-color|flood-color)\s*[:=]\s*[\"']?\s*([a-zA-Z]+)\b")
_ALLOWED_KEYWORDS = {"none", "transparent", "currentcolor", "inherit", "url"}
# Matches font-family="..." attributes and font-family: ... in style attributes.
_FONT_FAMILY = re.compile(r"font-family\s*(?:=\s*(?:\"([^\"]*)\"|'([^']*)')|:\s*([^;\"'>]+))", re.IGNORECASE)


@lru_cache
def load_brand() -> dict[str, Any]:
    return json.loads(BRAND_PATH.read_text())


def normalize_hex(value: str) -> str:
    value = value.strip().upper()
    if len(value) == 4:
        value = "#" + "".join(ch * 2 for ch in value[1:])
    return value


def palette(brand: dict[str, Any] | None = None) -> set[str]:
    brand = brand or load_brand()
    return {normalize_hex(value) for value in brand["colors"].values()}


def font_names(brand: dict[str, Any] | None = None) -> set[str]:
    brand = brand or load_brand()
    return {name.lower() for name in brand["fonts"].values()}


def format_size(name: str, brand: dict[str, Any] | None = None) -> tuple[int, int]:
    brand = brand or load_brand()
    if name not in brand["formats"]:
        options = ", ".join(sorted(brand["formats"]))
        raise ValueError(f"Unknown format {name!r}. Use one of: {options}.")
    width, height = brand["formats"][name]
    return int(width), int(height)


def lint_source(svg: str, brand: dict[str, Any] | None = None) -> list[str]:
    """Check a design's SVG before it renders. Returns a list of problems."""
    brand = brand or load_brand()
    problems: list[str] = []
    brand_colors = ", ".join(sorted(palette(brand)))

    if "<svg" not in svg.lower():
        problems.append("The design must be a single <svg> element.")
    if "<foreignobject" in svg.lower():
        problems.append("<foreignObject> isn't supported. Draw everything with SVG shapes and <text>.")

    off_brand = sorted({normalize_hex(c) for c in _HEX.findall(svg)} - palette(brand))
    if off_brand:
        problems.append(f"Off-brand colors: {', '.join(off_brand)}. Use only the brand colors: {brand_colors}.")
    if _RAW_COLOR_FUNCTION.search(svg):
        problems.append(f"Write colors as brand hex values, not rgb() or hsl(). Brand colors: {brand_colors}.")
    named = sorted({m.lower() for m in _NAMED_COLOR.findall(svg)} - _ALLOWED_KEYWORDS)
    if named:
        problems.append(f"Named colors aren't allowed ({', '.join(named)}). Use the brand hex values: {brand_colors}.")

    used_fonts: set[str] = set()
    for groups in _FONT_FAMILY.findall(svg):
        declaration = next((g for g in groups if g), "")
        for part in declaration.split(","):
            name = part.strip().strip("'\"").lower()
            if name and name not in GENERIC_FONTS:
                used_fonts.add(name)
    off_brand_fonts = sorted(used_fonts - font_names(brand))
    if off_brand_fonts:
        allowed = " or ".join(brand["fonts"].values())
        problems.append(f"Off-brand fonts: {', '.join(off_brand_fonts)}. Use {allowed}.")
    return problems


def check_report(report: dict[str, Any], fmt: str, brand: dict[str, Any] | None = None) -> list[str]:
    """Check a rendered design's report (from render_svg.py). Returns a list of problems."""
    brand = brand or load_brand()
    problems: list[str] = []

    width, height = format_size(fmt, brand)
    if (report.get("width"), report.get("height")) != (width, height):
        problems.append(f"Size is {report.get('width')}x{report.get('height')}, expected {width}x{height}.")

    off_brand = sorted({normalize_hex(c) for c in report.get("colors", [])} - palette(brand))
    if off_brand:
        problems.append(f"Rendered colors outside the brand palette: {', '.join(off_brand)}.")

    fonts = {f.lower() for f in report.get("fonts", [])} - font_names(brand) - GENERIC_FONTS
    if fonts:
        problems.append(f"Rendered text uses off-brand fonts: {', '.join(sorted(fonts))}.")

    missing = font_names(brand) - {f.lower() for f in report.get("fonts_loaded", [])}
    used = {f.lower() for f in report.get("fonts", [])}
    if missing & used:
        problems.append(f"Brand fonts did not load: {', '.join(sorted(missing & used))}.")

    min_contrast = brand["rules"]["min_contrast"]
    if report.get("min_contrast", 21) < min_contrast:
        problems.append(
            f"Lowest text contrast is {report['min_contrast']}:1, below the brand minimum of {min_contrast}:1."
        )

    for issue in report.get("overflow", []):
        problems.append(f"Text doesn't fit: {issue}. Break the line or make it smaller.")
    return problems
