#!/usr/bin/env python3
"""
Export a fully static version of the dashboard to dist/ for GitHub Pages.

Takes templates/index.html (Jinja2 template), renders it, and copies it
together with data/stations.json into dist/. The page's JS automatically
falls back to fetching data/stations.json when no FastAPI backend is present.
"""

from pathlib import Path

from jinja2 import Template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = ROOT / "templates" / "index.html"
DATA_FILE = ROOT / "data" / "stations.json"
DIST_DIR = ROOT / "dist"


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            "data/stations.json not found. Run `python scripts/build_data.py` first."
        )

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    html = Template(TEMPLATE_FILE.read_text(encoding="utf-8")).render(request=None)
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")

    (DIST_DIR / "data").mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "data" / "stations.json").write_text(
        DATA_FILE.read_text(encoding="utf-8"), encoding="utf-8"
    )

    print(f"Static site exported to {DIST_DIR}")


if __name__ == "__main__":
    main()
