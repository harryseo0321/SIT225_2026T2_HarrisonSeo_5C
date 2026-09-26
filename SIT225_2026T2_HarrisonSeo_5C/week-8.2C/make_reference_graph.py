"""Make an honest static reference graph from the original Week 8 CSV data.

This output is NOT a screenshot of the live 5C Dash app. Include a genuine
live-app screenshot and Panopto recording after running live_accelerometer.py.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
fig, ax = plt.subplots(figsize=(11, 5))
for axis in ("X", "Y", "Z"):
    path = ROOT / "data" / f"iPhone Thing-Accelerometer_{axis}.csv"
    frame = pd.read_csv(path)
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    ax.plot(frame["time"], frame["value"], label=axis, linewidth=0.8)
ax.set(title="Original Week 8 phone accelerometer data (offline reference)", xlabel="Time (UTC)", ylabel="Value (phone units)")
ax.legend()
ax.grid(alpha=0.25)
fig.autofmt_xdate()
fig.tight_layout()
output = ROOT / "week8_reference_graph.png"
fig.savefig(output, dpi=160)
print(output)
