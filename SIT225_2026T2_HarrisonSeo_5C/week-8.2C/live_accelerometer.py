"""Phone -> Arduino IoT Cloud -> Python -> smooth Plotly Dash graph.

Run: python live_accelerometer.py

The device ID and secret key are typed in when the script starts and are not
saved anywhere. Stop any other Python receiver using the same device first.
Readings are appended to data/live_accelerometer.csv.
"""

from __future__ import annotations

import csv
from getpass import getpass
from pathlib import Path
from threading import Thread

from arduino_iot_cloud import ArduinoCloudClient
from dash import Dash, html

from smooth_stream import SmoothStream, add_smooth_stream

OUT = Path(__file__).resolve().parent / "data" / "live_accelerometer.csv"
# Default Cloud variable name for each axis (can be changed at the prompt).
NAMES = {"X": "Accelerometer_X", "Y": "Accelerometer_Y", "Z": "Accelerometer_Z"}


def main():
    print("Enter the Python device ID (not your Arduino account login).")
    device_id = input("Python device ID: ").strip()
    secret = getpass("Python device secret key (hidden): ").strip()
    if not device_id or not secret:
        raise SystemExit("Both the device ID and secret key are required.")
    variable_names = {
        axis: input(f"Cloud variable for {axis} [{default}]: ").strip() or default
        for axis, default in NAMES.items()
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    stream = SmoothStream(tuple(NAMES))

    def receive(axis, value):
        if value is None:
            return
        try:
            sample = stream.publish(axis, value)
        except (TypeError, ValueError):
            return
        new_file = not OUT.exists() or OUT.stat().st_size == 0
        with OUT.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if new_file:
                writer.writerow(["timestamp_utc", "channel", "value"])
            writer.writerow([sample.timestamp, axis, sample.value])
        print(f"{sample.timestamp}  {axis}={sample.value:.3f}")

    client = ArduinoCloudClient(device_id=device_id, username=device_id, password=secret)
    for axis, variable in variable_names.items():
        client.register(variable, value=None, on_write=lambda _client, value, a=axis: receive(a, value))

    def run_cloud():
        try:
            client.start()
        except Exception as exc:
            print(f"Arduino Cloud connection stopped: {exc}")

    # The Cloud client runs in the background so the Dash server stays responsive.
    Thread(target=run_cloud, name="arduino-cloud-receiver", daemon=True).start()

    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.H2("SIT225 8.2C · Live phone accelerometer"),
            html.P("Move the phone. New readings are added to the graph as they arrive."),
            add_smooth_stream(
                app,
                stream,
                graph_id="live-acceleration",
                title="Live smartphone accelerometer (X, Y, Z)",
                y_title="Acceleration (g)",
            ),
        ],
        style={"fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "auto"},
    )
    print(f"Saving readings to {OUT}")
    print("Open http://127.0.0.1:8050 in a browser. Press Ctrl+C to stop.")
    app.run(host="127.0.0.1", port=8050, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
