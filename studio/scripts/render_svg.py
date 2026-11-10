"""Render one SVG design to a PNG and report what was drawn.

Runs inside the sandbox (or the eval container), not in the agent's process.
It needs only `resvg-py` and `pillow`: no browser.

Usage: python3 render_svg.py <design.svg> <out.png> <brand.json> <fonts_dir>
Prints a JSON report on its last line of output.
"""

import copy
import json
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import resvg_py
from PIL import Image, ImageFont

SVG = "{http://www.w3.org/2000/svg}"
HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
INHERITED = {"fill", "font-family", "font-size", "font-weight", "text-anchor", "letter-spacing"}
DEFAULTS = {"fill": "#000000", "font-size": "16", "font-weight": "400", "text-anchor": "start", "letter-spacing": "0"}
WEIGHTS = {"normal": 400, "bold": 700}


# ---------- fonts ----------

WEIGHT_TRIES = ["400;500;600;700", "400;700", None]


def _get(url: str) -> bytes:
    # A plain user agent makes Google Fonts serve TTF files, which resvg and Pillow can read.
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"}), timeout=30).read()


def _font_css(family: str) -> str:
    """Get Google Fonts CSS for one family, asking for common weights and falling back
    to fewer when the family doesn't have them all."""
    name = urllib.parse.quote_plus(family)
    for weights in WEIGHT_TRIES:
        url = f"https://fonts.googleapis.com/css2?family={name}" + (f":wght@{weights}" if weights else "")
        try:
            return _get(url).decode()
        except urllib.error.HTTPError:
            continue
    raise RuntimeError(f"Google Fonts has no font called {family!r}. Check the name in brand.json.")


def fetch_fonts(brand: dict, fonts_dir: Path) -> list[tuple[str, int, str]]:
    """Download the brand's fonts from Google Fonts as TTF files, once per sandbox.

    Returns (family, weight, path) for every weight found.
    """
    fonts_dir.mkdir(parents=True, exist_ok=True)
    manifest = fonts_dir / "fonts.json"
    families = sorted(set(brand["fonts"].values()))
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        if saved.get("families") == families:
            return [tuple(f) for f in saved["fonts"]]

    fonts = []
    for family in families:
        for block in re.findall(r"@font-face\s*{([^}]*)}", _font_css(family)):
            style = re.search(r"font-style:\s*(\w+)", block)
            if style and style.group(1) != "normal":
                continue
            weight = int(re.search(r"font-weight:\s*(\d+)", block).group(1))
            src = re.search(r"url\((https://[^)]+)\)", block).group(1)
            path = fonts_dir / f"{family.replace(' ', '')}-{weight}.ttf"
            if not path.exists():
                path.write_bytes(_get(src))
            fonts.append((family, weight, str(path)))
    manifest.write_text(json.dumps({"families": families, "fonts": fonts}))
    return fonts


def font_file(fonts, family: str, weight: int):
    matches = [f for f in fonts if f[0].lower() == family.lower()]
    if not matches:
        return None
    return min(matches, key=lambda f: abs(f[1] - weight))[2]


# ---------- reading the SVG ----------

def norm_hex(value: str) -> str:
    value = value.strip().upper()
    return "#" + "".join(c * 2 for c in value[1:]) if len(value) == 4 else value


def style_of(el) -> dict:
    out = {}
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def prop(el, name: str, parents: dict) -> str:
    """Resolve an SVG presentation property, following inheritance up the tree."""
    node = el
    while node is not None:
        value = style_of(node).get(name) or node.get(name)
        if value:
            return value
        if name not in INHERITED:
            break
        node = parents.get(node)
    return DEFAULTS.get(name, "")


def number(value: str, font_size: float = 16.0) -> float:
    value = value.strip()
    if value.endswith("em"):
        return float(value[:-2]) * font_size
    return float(re.sub(r"[a-z%]+$", "", value) or 0)


def translation(el, parents: dict):
    """Sum translate() transforms on the element and its ancestors. None if there's another transform."""
    dx = dy = 0.0
    node = el
    while node is not None:
        t = (node.get("transform") or "").strip()
        if t:
            m = re.fullmatch(r"translate\(\s*([-\d.]+)[\s,]*([-\d.]*)\s*\)", t)
            if not m:
                return None
            dx += float(m.group(1))
            dy += float(m.group(2) or 0)
        node = parents.get(node)
    return dx, dy


def text_lines(root, parents: dict) -> list[dict]:
    """Split each <text> into lines. A <tspan> with x, y, or dy starts a new line."""
    lines = []
    for text in root.iter(f"{SVG}text"):
        size = number(prop(text, "font-size", parents))
        x, y = number(text.get("x", "0")), number(text.get("y", "0"))
        current = {"el": text, "text": text.text or "", "x": x, "y": y}
        for child in text:
            if child.tag == f"{SVG}tspan" and any(child.get(a) for a in ("x", "y", "dy")):
                lines.append(current)
                child_size = number(prop(child, "font-size", parents))
                x = number(child.get("x")) if child.get("x") else current["x"]
                y = number(child.get("y")) if child.get("y") else current["y"] + number(child.get("dy", "0"), child_size)
                current = {"el": child, "text": "".join(child.itertext()), "x": x, "y": y}
            else:
                current["text"] += "".join(child.itertext())
            current["text"] += child.tail or ""
        lines.append(current)
    return [line for line in lines if line["text"].strip()]


# ---------- measuring and checking ----------

def luminance(hex_value: str) -> float:
    rgb = [int(hex_value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def render_png(svg_text: str, fonts, brand: dict) -> bytes:
    fonts_dirs = sorted({str(Path(f[2]).parent) for f in fonts})
    return bytes(resvg_py.svg_to_bytes(
        svg_string=svg_text,
        font_dirs=fonts_dirs,
        skip_system_fonts=True,
        serif_family=brand["fonts"]["heading"],
        sans_serif_family=brand["fonts"]["body"],
    ))


def main() -> None:
    svg_path, out_path, brand_path, fonts_dir = sys.argv[1:5]
    brand = json.loads(Path(brand_path).read_text())
    fonts = fetch_fonts(brand, Path(fonts_dir))
    svg_text = Path(svg_path).read_text()

    png = render_png(svg_text, fonts, brand)
    Path(out_path).write_bytes(png)
    image = Image.open(out_path).convert("RGB")
    width, height = image.size

    ET.register_namespace("", SVG[1:-1])
    root = ET.fromstring(svg_text)
    parents = {child: parent for parent in root.iter() for child in parent}

    # Render once more with the text removed, to see the background behind each line.
    bare = copy.deepcopy(root)
    bare_parents = {child: parent for parent in bare.iter() for child in parent}
    for text in list(bare.iter(f"{SVG}text")):
        bare_parents[text].remove(text)
    background = Image.open(__import__("io").BytesIO(render_png(ET.tostring(bare, encoding="unicode"), fonts, brand))).convert("RGB")

    colors = {norm_hex(c) for c in HEX.findall(svg_text)}
    used_fonts, overflow, measured, contrasts = set(), [], [], []
    for line in text_lines(root, parents):
        el, words = line["el"], " ".join(line["text"].split())
        family = prop(el, "font-family", parents).split(",")[0].strip().strip("'\"") or brand["fonts"]["body"]
        size = number(prop(el, "font-size", parents))
        weight_raw = prop(el, "font-weight", parents)
        weight = WEIGHTS.get(weight_raw, int(weight_raw) if weight_raw.isdigit() else 400)
        fill = prop(el, "fill", parents)
        fill_hex = norm_hex(fill) if HEX.fullmatch(fill.strip()) else None
        if fill_hex:
            colors.add(fill_hex)
        used_fonts.add(family)

        shift = translation(el, parents)
        path = font_file(fonts, family, weight)
        if shift is None or path is None:
            measured.append({"text": words, "measured": False})
            continue
        font = ImageFont.truetype(path, max(1, round(size)))
        text_width = font.getlength(words) + number(prop(el, "letter-spacing", parents), size) * max(0, len(words) - 1)
        ascent, descent = font.getmetrics()
        anchor = prop(el, "text-anchor", parents)
        x, y = line["x"] + shift[0], line["y"] + shift[1]
        left = x - {"middle": text_width / 2, "end": text_width}.get(anchor, 0)
        right, top, bottom = left + text_width, y - ascent, y + descent
        measured.append({"text": words, "measured": True, "left": round(left), "right": round(right), "font": f"{family} {weight} {size:g}px"})

        short = words if len(words) <= 40 else words[:37] + "..."
        if right > width:
            overflow.append(f'"{short}" runs {round(right - width)}px past the right edge')
        if left < 0:
            overflow.append(f'"{short}" starts {round(-left)}px before the left edge')
        if bottom > height or top < 0:
            overflow.append(f'"{short}" is cut off at the top or bottom')

        if fill_hex:
            box = (max(0, int(left)), max(0, int(top)), min(width, int(right) + 1), min(height, int(bottom) + 1))
            if box[2] > box[0] and box[3] > box[1]:
                pixels = list(background.crop(box).getdata())
                bg = "#" + "".join(f"{int(statistics.median(p[i] for p in pixels)):02X}" for i in range(3))
                contrasts.append(contrast(fill_hex, bg))

    all_text = " ".join(" ".join(line["text"].split()) for line in text_lines(root, parents))
    print(json.dumps({
        "width": width,
        "height": height,
        "colors": sorted(colors),
        "fonts": sorted(used_fonts),
        "fonts_loaded": sorted({f[0] for f in fonts}),
        "min_contrast": round(min(contrasts), 2) if contrasts else 21,
        "overflow": overflow[:10],
        "lines": measured,
        "text": all_text,
    }))


if __name__ == "__main__":
    main()
