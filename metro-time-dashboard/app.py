from pathlib import Path
import json
from typing import Literal

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "stations.json"

app = FastAPI(title="Moscow Metro Travel Time Explorer")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_stations() -> list[dict]:
    """
    Load station travel time data from JSON.
    Expected item shape:
    {
      "station": "Павелецкая",
      "to_tulskaya": 8,
      "to_zil": 17
    }
    """
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as f:
        raw_items = json.load(f)

    cleaned = []

    for item in raw_items:
        try:
            station = str(item.get("station", "")).strip()
            to_tulskaya = item.get("to_tulskaya")
            to_zil = item.get("to_zil")

            if not station or to_tulskaya is None or to_zil is None:
                continue

            to_tulskaya = int(to_tulskaya)
            to_zil = int(to_zil)

            min_time = min(to_tulskaya, to_zil)

            cleaned.append(
                {
                    "station": station,
                    "to_tulskaya": to_tulskaya,
                    "to_zil": to_zil,
                    "min_time": min_time,
                    "best_target": "Тульская" if to_tulskaya <= to_zil else "ЗИЛ",
                }
            )
        except Exception:
            # Skip malformed rows silently for MVP.
            continue

    return cleaned


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/stations")
def api_stations(
    q: str = Query("", description="Search station name"),
    max_minutes: int = Query(40, ge=0, le=120),
    target: Literal["any", "tulskaya", "zil"] = Query("any"),
    sort: Literal["min", "station", "tulskaya", "zil"] = Query("min"),
):
    stations = load_stations()

    q = q.strip().lower()

    if q:
        stations = [s for s in stations if q in s["station"].lower()]

    if target == "tulskaya":
        stations = [s for s in stations if s["to_tulskaya"] <= max_minutes]
    elif target == "zil":
        stations = [s for s in stations if s["to_zil"] <= max_minutes]
    else:
        stations = [
            s for s in stations if min(s["to_tulskaya"], s["to_zil"]) <= max_minutes
        ]

    if sort == "station":
        stations.sort(key=lambda s: s["station"].lower())
    elif sort == "tulskaya":
        stations.sort(key=lambda s: s["to_tulskaya"])
    elif sort == "zil":
        stations.sort(key=lambda s: s["to_zil"])
    else:
        stations.sort(key=lambda s: s["min_time"])

    return {
        "count": len(stations),
        "stations": stations,
    }
