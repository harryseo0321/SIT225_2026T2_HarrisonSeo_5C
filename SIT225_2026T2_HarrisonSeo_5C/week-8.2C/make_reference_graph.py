"""Save a static graph of my original Week 8 accelerometer CSVs.

Run: python make_reference_graph.py
Output: week8_reference_graph.png (old Week 8 data, not the live 8.2C run)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # save to file without opening a window
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "week8_reference_graph.png"


def main():
    fig, ax = plt.subplots(figsize=(11, 5))
    for axis in ("X", "Y", "Z"):
        path = ROOT / "data" / f"iPhone Thing-Accelerometer_{axis}.csv"
        frame = pd.read_csv(path)
        frame["time"] = pd.to_datetime(frame["time"], utc=True, format="ISO8601")
        ax.plot(frame["time"], frame["value"], label=axis, linewidth=0.8)
    ax.set(
        title="Week 8 phone accelerometer data (reference)",
        xlabel="Time (UTC)",
        ylabel="Acceleration (g)",
    )
    ax.legend()
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(TARGET, dpi=160)
    print(f"Saved {TARGET}")


if __name__ == "__main__":
    main()
