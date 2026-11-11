"""Turn an SVG design into a PNG.

Usage: python /workspace/render.py /workspace/designs/<name>.svg
Writes /workspace/out/<name>.png. The first run downloads the design's fonts
from Google Fonts, so it takes a few extra seconds.
"""

import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import resvg_py

FONTS = Path("/workspace/.fonts")


def download_font(family: str) -> None:
    """Save a Google Font's regular and bold weights as TTF files, once per sandbox."""
    if list(FONTS.glob(family.replace(" ", "") + "-*.ttf")):
        return
    for weights in (":wght@400;500;600;700", ":wght@400;700", ""):
        url = f"https://fonts.googleapis.com/css2?family={urllib.parse.quote_plus(family)}{weights}"
        try:
            # A plain user agent makes Google Fonts serve TTF files, which resvg can read.
            css = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"})).read().decode()
            break
        except urllib.error.HTTPError:
            continue
    else:
        print(f"Couldn't find {family!r} on Google Fonts, so it was left out.")
        return
    for weight, src in re.findall(r"font-weight:\s*(\d+);.*?src:\s*url\((.*?)\)", css, re.S):
        (FONTS / f"{family.replace(' ', '')}-{weight}.ttf").write_bytes(urllib.request.urlopen(src).read())


svg_path = Path(sys.argv[1])
svg = svg_path.read_text()
FONTS.mkdir(parents=True, exist_ok=True)
for family in set(re.findall(r"font-family=[\"']([^\"',]+)", svg)):
    download_font(family.strip())

png_path = Path("/workspace/out") / (svg_path.stem + ".png")
png_path.parent.mkdir(parents=True, exist_ok=True)
png_path.write_bytes(bytes(resvg_py.svg_to_bytes(svg_string=svg, font_dirs=[str(FONTS)])))
print(f"Saved {png_path}")
