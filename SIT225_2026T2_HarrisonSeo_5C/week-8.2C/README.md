# SIT225 Week 8.2C – Smooth live accelerometer dashboard

This folder is my submission for the Week 8.2C credit task. My phone streams accelerometer X/Y/Z to Arduino IoT Cloud, a Python receiver picks up the values, and a Plotly Dash page shows them as a graph that updates smoothly instead of redrawing the whole figure every N samples.

## Files

| File | What it is |
|---|---|
| `smooth_stream.py` | My reusable wrapper (`SmoothStream` and `add_smooth_stream`) |
| `live_accelerometer.py` | Live app: Arduino IoT Cloud receiver + Dash graph |
| `make_live_graph.py` | Makes a static graph from the live capture CSV |
| `live_accelerometer_graph.png` | Graph generated from my real live capture |
| `replay_week8.py` | Offline replay of my Week 8 CSVs (for testing only) |
| `make_reference_graph.py` | Makes a static graph from the Week 8 CSVs |
| `week8_reference_graph.png` | Graph of the original Week 8 data |
| `data/` | My original Week 8 X/Y/Z CSVs and `live_accelerometer.csv` from the live run |
| `requirements.txt` | Python packages needed |

There's no Arduino sketch because the phone (Arduino IoT Remote app) is the sensor.

Note: `week8_reference_graph.png` and the replay use old Week 8 data, so they aren't a live run. The live result is `live_accelerometer_graph.png` and the demo video.

## Running it live

1. On the phone, open Arduino IoT Remote, connect the phone Thing and turn on Accelerometer X/Y/Z. In Arduino Cloud, check the Python device Thing still has the three synced variables.
2. Stop any old Week 8 receiver that's still running.
3. Open a terminal in this folder and install the packages (once):
   ```
   python -m pip install -r requirements.txt
   ```
4. Start the app:
   ```
   python live_accelerometer.py
   ```
5. Enter the Python device ID and secret key when asked. They're typed in at runtime, not stored in any file. Press Enter at the variable name prompts if the defaults match your Thing.
6. Open http://127.0.0.1:8050 and move the phone. The X, Y and Z lines should keep extending without the plot flickering or being replaced. Readings are also saved to `data/live_accelerometer.csv`.
7. Press `Ctrl+C` to stop.
8. To make a static graph of the capture:
   ```
   python make_live_graph.py
   ```

(I ran this from my conda environment. If `python` isn't on your PATH, use the full path to your environment's `python.exe`.)

## Offline replay

To test the dashboard without Arduino Cloud, this replays my Week 8 CSVs at 5x speed:

```
python replay_week8.py ./data --speed 5
```

This is only for checking the display works. It's not a replacement for the live demo.

## Using the wrapper

```python
from dash import Dash
from smooth_stream import SmoothStream, add_smooth_stream

app = Dash(__name__)
stream = SmoothStream(("temperature", "humidity"))
app.layout = add_smooth_stream(
    app, stream, graph_id="room", max_points=300, y_title="Value"
)

# From your own data thread, whenever a new reading comes in:
# stream.publish("temperature", 23.4)

app.run(debug=False)
```

Parameters of `add_smooth_stream`:

| Parameter | Default | Meaning |
|---|---|---|
| `app` | – | Your Dash app |
| `stream` | – | A `SmoothStream` with your channel names |
| `graph_id` | `"live-acceleration"` | Unique ID, so you can have more than one graph |
| `interval_ms` | `200` | How often the page checks for new points (min 50 ms) |
| `max_points` | `300` | Points kept per line in the browser |
| `y_title` | `"Accelerometer value (phone units)"` | Y-axis label, so change it for other data |

## How it works

- Incoming readings go into a bounded, thread-safe buffer (up to 5,000 events), protected by a lock.
- The Cloud receiver runs on a background thread so the Dash server stays responsive.
- Every 200 ms the page asks for anything new since its last cursor. If nothing's new it does nothing. Otherwise it sends only the new points through `dcc.Graph`'s `extendData`, so the existing figure isn't rebuilt.
- Each browser keeps its own cursor. If the buffer ever fills before the page catches up, the oldest unrendered events are dropped and the status line reports it.
- Values aren't interpolated, so every point is a real reading timestamped when it arrived. I didn't modify the Plotly library.
- There's still some polling and network delay, so it's smoother incremental updating rather than zero latency.
