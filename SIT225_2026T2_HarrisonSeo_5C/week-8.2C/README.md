# SIT225 5C – smooth live accelerometer Dash

This folder is ready to copy into your GitHub repository at
`SIT225_2024T2/week-8.2C/`. It contains the reusable wrapper, live app,
offline rehearsal, dependencies, original Week 8 CSVs, and a static reference
graph. The static graph and replay are **not** evidence of a live Cloud run.

## Live run (Windows PowerShell)

1. On your phone, open Arduino IoT Remote, connect the existing iPhone Thing,
   and enable Accelerometer X/Y/Z. In Arduino Cloud, check the Python receiver
   Thing still has the three synced variables.
2. Open PowerShell in this folder (File Explorer address bar: type `powershell`
   and press Enter).
3. Install once: `& 'C:\Users\harri\.conda\envs\notebook-env\python.exe' -m pip install -r requirements.txt`
4. Run: `& 'C:\Users\harri\.conda\envs\notebook-env\python.exe' .\live_accelerometer.py`
5. Enter the **Python device ID** and **secret key** privately. For variable
   prompts, just press Enter if the default names are correct.
6. Open `http://127.0.0.1:8050` and move your phone. Check X, Y, Z traces
   advance without disappearing/replacing the whole plot. The raw event log
   is saved to `data/live_accelerometer.csv`.
7. Press `Ctrl+C` in PowerShell when finished. Never record or upload the
   secret key. Stop the earlier Week 8 receiver before this run.
8. To create a static graph from the real live CSV, run:
   `& 'C:\Users\harri\.conda\envs\notebook-env\python.exe' .\make_live_graph.py`

## Offline rehearsal (clearly labelled as replay)

`& 'C:\Users\harri\.conda\envs\notebook-env\python.exe' .\replay_week8.py .\data --speed 5`

This proves the Dash display can process the student's existing Week 8 CSVs
without needing Cloud access, but does not replace the required live demo.

## Reusable API

```python
from dash import Dash
from smooth_stream import SmoothStream, add_smooth_stream

app = Dash(__name__)
stream = SmoothStream(("temperature", "humidity"))
app.layout = add_smooth_stream(app, stream, graph_id="room", max_points=300)
# In your own receiver thread: stream.publish("temperature", 23.4)
```

The wrapper uses a bounded thread-safe queue, a browser cursor and Dash
`Graph.extendData` to append only new observations. It does not interpolate
missing observations or alter Plotly's installed library. Each browser stores
its own cursor; old unrendered items can be dropped if the queue overflows.

No Arduino sketch is needed: the phone's Arduino IoT Remote app is the device.
Do not invent a sketch for this task.
