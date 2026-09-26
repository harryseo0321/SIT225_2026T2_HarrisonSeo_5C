"""Offline test: replay my Week 8 phone CSVs through the same Dash graph.

Run: python replay_week8.py [folder] [--speed 5]

This is only for testing the dashboard without Arduino Cloud. It is not live data.
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

DATA = Path(__file__).resolve().parent / "data"
AXES = ("X", "Y", "Z")


def load_events(folder: Path):
    """Read the X/Y/Z CSVs and return all readings sorted by time."""
    events = []
    for axis in AXES:
        path = folder / f"iPhone Thing-Accelerometer_{axis}.csv"
        if not path.exists():
            raise SystemExit(f"Missing file: {path}")
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                stamp = row.get("time") or row.get("timestamp")
                if not stamp or not row.get("value"):
                    continue
                recorded_at = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                events.append((recorded_at, axis, float(row["value"])))
    return sorted(events)


def main():
    parser = argparse.ArgumentParser(description="Replay Week 8 accelerometer CSVs.")
    parser.add_argument("folder", type=Path, nargs="?", default=DATA,
                        help="Folder with the three Week 8 X/Y/Z CSV files (default: ./data)")
    parser.add_argument("--speed", type=float, default=5.0,
                        help="Replay speed relative to the original timing (default: 5)")
    args = parser.parse_args()
    if args.speed <= 0:
        parser.error("--speed must be positive")

    events = load_events(args.folder)
    stream = SmoothStream(AXES)

    def replay():
        previous = None
        for recorded_at, axis, value in events:
            if previous is not None:
                gap = (recorded_at - previous).total_seconds() / args.speed
                time.sleep(min(max(gap, 0), 10))  # cap long pauses at 10 s
            stream.publish(axis, value, recorded_at.isoformat(timespec="milliseconds"))
            previous = recorded_at
        print("Replay finished.")

    Thread(target=replay, name="week8-replay", daemon=True).start()

    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.H2("Week 8 CSV replay (not live Cloud data)"),
            add_smooth_stream(
                app,
                stream,
                graph_id="replay-acceleration",
                title="Week 8 accelerometer replay (X, Y, Z)",
                y_title="Acceleration (g)",
            ),
        ],
        style={"fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "auto"},
    )
    print(f"Loaded {len(events)} readings. Open http://127.0.0.1:8050 (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=8050, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
