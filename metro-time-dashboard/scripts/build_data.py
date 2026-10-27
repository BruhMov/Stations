#!/usr/bin/env python3
"""
Build data/stations.json from source.txt.

source.txt can contain either:

1. Markdown table rows:
   | Павелецкая | 8 мин | 17 мин |

2. Telegram-style blocks:
   🚇 **Павелецкая**
   ┣ 📍 Тульская: `8 мин`
   ┗ 📍 ЗИЛ: `17 мин`
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "source.txt"
DATA_DIR = ROOT / "data"
OUTPUT_FILE = DATA_DIR / "stations.json"

SAMPLE_DATA = [
    {"station": "Тульская", "to_tulskaya": 0, "to_zil": 19},
    {"station": "ЗИЛ", "to_tulskaya": 19, "to_zil": 0},
    {"station": "Добрынинская / Серпуховская", "to_tulskaya": 3, "to_zil": 22},
    {"station": "Автозаводская", "to_tulskaya": 15, "to_zil": 3},
    {"station": "Нагатинская / Верхние котлы", "to_tulskaya": 4, "to_zil": 3},
    {"station": "Полянка", "to_tulskaya": 5, "to_zil": 24},
    {"station": "Павелецкая", "to_tulskaya": 8, "to_zil": 17},
    {"station": "Октябрьская", "to_tulskaya": 8, "to_zil": 20},
]


def parse_time(value: str) -> int | None:
    if not value:
        return None

    match = re.search(r"\d+", value)
    if not match:
        return None

    return int(match.group(0))


def parse_telegram_style(text: str) -> list[dict]:
    """
    Parses blocks like:

    🚇 **Павелецкая**
    ┣ 📍 Тульская: `8 мин`
    ┗ 📍 ЗИЛ: `17 мин`
    """
    items = []

    chunks = text.split("🚇")

    for chunk in chunks:
        if not chunk.strip():
            continue

        name_match = re.search(r"\*\*(.+?)\*\*", chunk)

        if not name_match:
            first_line = chunk.strip().splitlines()[0].strip() if chunk.strip() else ""
            if first_line and not any(
                marker in first_line
                for marker in ["┣", "┗", "🟢", "🟡", "🟠", "🔴", "Станции метро"]
            ):
                name = first_line
            else:
                continue
        else:
            name = name_match.group(1).strip()

        tulskaya_match = re.search(r"Тульская:\s*`?(\d+)", chunk)
        zil_match = re.search(r"ЗИЛ:\s*`?(\d+)", chunk)

        if not tulskaya_match or not zil_match:
            continue

        items.append(
            {
                "station": name,
                "to_tulskaya": int(tulskaya_match.group(1)),
                "to_zil": int(zil_match.group(1)),
            }
        )

    return items


def parse_markdown_table(text: str) -> list[dict]:
    """
    Parses Markdown table rows like:

    | Павелецкая | 8 мин | 17 мин |
    """
    items = []

    for line in text.splitlines():
        line = line.strip()

        if not line.startswith("|"):
            continue

        if "---" in line:
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]

        if len(cells) < 3:
            continue

        if "Станция" in cells[0]:
            continue

        station = cells[0].strip()
        to_tulskaya = parse_time(cells[1])
        to_zil = parse_time(cells[2])

        if not station or to_tulskaya is None or to_zil is None:
            continue

        items.append(
            {
                "station": station,
                "to_tulskaya": to_tulskaya,
                "to_zil": to_zil,
            }
        )

    return items


def main() -> None:
    items = []

    if SOURCE_FILE.exists():
        text = SOURCE_FILE.read_text(encoding="utf-8")

        items = parse_telegram_style(text)

        if not items:
            items = parse_markdown_table(text)

    if not items:
        items = SAMPLE_DATA
        print(
            "source.txt not found or could not be parsed. "
            "Using sample data so you can test the app."
        )

    # Keep only stations where at least one target is <= 40 minutes.
    items = [
        item
        for item in items
        if min(item["to_tulskaya"], item["to_zil"]) <= 40
    ]

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Saved {len(items)} stations to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
