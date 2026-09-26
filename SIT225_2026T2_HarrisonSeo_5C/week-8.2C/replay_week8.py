"""Optional OFFLINE rehearsal using the student's earlier Week 8 phone CSVs.

This is labelled replay, not live cloud evidence. It helps verify the app
before the student records a genuine live phone demonstration.
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path
from threading import Thread

from dash import Dash, html

from smooth_stream import SmoothStream, add_smooth_stream


def load_events(folder: Path):
    events = []
    for axis in ("X", "Y", "Z"):
        path = folder / f"iPhone Thing-Accelerometer_{axis}.csv"
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                stamp = row.get("time") or row.get("timestamp")
                events.append((datetime.fromisoformat(stamp.replace("Z", "+00:00")), axis, float(row["value"])))
    return sorted(events)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, help="Folder containing the three original Week 8 X/Y/Z CSV files")
    parser.add_argument("--speed", type=float, default=5.0, help="Replay speed relative to original time")
    args = parser.parse_args()
    if args.speed <= 0:
        parser.error("--speed must be positive")
    events = load_events(args.folder)
    stream = SmoothStream(("X", "Y", "Z"))

    def replay():
        previous = None
        for recorded_at, axis, value in events:
            if previous is not None:
                time.sleep(min(max((recorded_at - previous).total_seconds() / args.speed, 0), 10))
            stream.publish(axis, value, recorded_at.isoformat())
            previous = recorded_at

    Thread(target=replay, name="week8-offline-replay", daemon=True).start()
    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.H2("Week 8 CSV replay · not live Cloud data"),
            add_smooth_stream(app, stream),
        ],
        style={"fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "auto"},
    )
    print(f"Loaded {len(events)} original events. Open http://127.0.0.1:8050")
    app.run(host="127.0.0.1", port=8050, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
