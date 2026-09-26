"""Save a static graph of the live readings in data/live_accelerometer.csv.

Run: python make_live_graph.py
Output: live_accelerometer_graph.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save to file without opening a window
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "live_accelerometer.csv"
TARGET = ROOT / "live_accelerometer_graph.png"


def main():
    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE} not found. Run live_accelerometer.py first.")
    frame = pd.read_csv(SOURCE)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, format="ISO8601")

    fig, ax = plt.subplots(figsize=(11, 5))
    for channel in ("X", "Y", "Z"):
        readings = frame.loc[frame["channel"] == channel]
        ax.plot(readings["timestamp_utc"], readings["value"], label=channel, linewidth=0.9)
    ax.set(
        title="Live phone accelerometer readings via Arduino IoT Cloud",
        xlabel="Time (UTC)",
        ylabel="Acceleration (g)",
    )
    ax.grid(alpha=0.25)
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(TARGET, dpi=160)
    print(f"Saved {TARGET}")


if __name__ == "__main__":
    main()
