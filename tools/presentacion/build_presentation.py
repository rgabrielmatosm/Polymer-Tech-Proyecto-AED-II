"""Builds docs/final/presentacion/POLYMER-presentation.html: a single self-contained file (team photos embedded).

Usage:  python tools/presentacion/build_presentation.py [--check]
"""
import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "tools" / "presentacion" / "presentation.template.html"
OUTPUT = ROOT / "docs" / "final" / "presentacion" / "POLYMER-presentation.html"
PHOTOS = ROOT / "services" / "order-api" / "src" / "main" / "resources" / "static" / "img" / "equipo"
TOKENS = {
    "__PHOTO_RONALDO__": "ronaldo-matos.jpg",
    "__PHOTO_KHYARA__": "khyara-morales.jpg",
    "__PHOTO_JONATHAN__": "jonathan-retuerto.jpg",
}


def build() -> str:
    html = TEMPLATE.read_text(encoding="utf-8")
    for token, name in TOKENS.items():
        data = base64.b64encode((PHOTOS / name).read_bytes()).decode("ascii")
        html = html.replace(token, "data:image/jpeg;base64," + data)
    return html


def main() -> int:
    html = build()
    if "--check" in sys.argv:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != html:
            print(f"{OUTPUT.relative_to(ROOT)} is out of date: run python tools/presentacion/build_presentation.py")
            return 1
        print("presentation up to date")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(html) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
