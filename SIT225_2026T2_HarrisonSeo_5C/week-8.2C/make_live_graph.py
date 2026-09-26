"""Create a static record of the REAL live Arduino Cloud readings saved by 5C."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


root = Path(__file__).resolve().parent
source = root / "data" / "live_accelerometer.csv"
frame = pd.read_csv(source)
frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)

fig, ax = plt.subplots(figsize=(11, 5))
for channel in ("X", "Y", "Z"):
    readings = frame.loc[frame["channel"] == channel]
    ax.plot(readings["timestamp_utc"], readings["value"], label=channel, linewidth=0.9)
ax.set(
    title="SIT225 5C real phone-to-Cloud accelerometer capture",
    xlabel="Time (UTC)",
    ylabel="Value (phone units)",
)
ax.grid(alpha=0.25)
ax.legend()
fig.autofmt_xdate()
fig.tight_layout()
target = root / "live_accelerometer_graph.png"
fig.savefig(target, dpi=160)
print(target)
