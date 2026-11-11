"""Look up the brand (Lab 1).

brand.json is the brand as data: exact colors, fonts, and canvas sizes. The
agent calls get_brand before it draws, so it uses the exact values. The
brand_lint middleware checks every design against the same file.
"""

import json
from pathlib import Path

from langchain.tools import tool

BRAND_FILE = Path(__file__).resolve().parent.parent / "brand.json"


def load_brand() -> dict:
    return json.loads(BRAND_FILE.read_text())


def describe_brand(format: str) -> str:
    """The logic behind get_brand: the brand's colors and fonts, plus one format's canvas size."""
    brand = load_brand()
    if format not in brand["formats"]:
        return f"There's no format called {format!r}. Choose one of: {', '.join(brand['formats'])}."
    width, height = brand["formats"][format]
    return json.dumps(
        {"brand": brand["name"], "colors": brand["colors"], "fonts": brand["fonts"], "canvas": {"width": width, "height": height}},
        indent=2,
    )


# TODO (Lab 1): write the get_brand tool here. The agent calls it before it draws,
# so it uses your brand's exact values, and the critic uses it to check them.
# The logic is already written in describe_brand above: the tool's body is just
#     return describe_brand(format)
