"""Phone -> Arduino IoT Cloud -> Python -> smooth Plotly Dash monitor.

Run: python live_accelerometer.py
Credentials are entered at runtime, are never saved, and are not needed for
the offline replay script. Close any earlier Python Cloud receiver first.
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
NAMES = {"X": "Accelerometer_X", "Y": "Accelerometer_Y", "Z": "Accelerometer_Z"}


def main():
    print("Enter the Python DEVICE ID (not your Arduino login).")
    device_id = input("Python device ID: ").strip()
    secret = getpass("Python device secret key (hidden): ").strip()
    if not device_id or not secret:
        raise ValueError("Both Python device ID and secret key are required.")
    variable_names = {
        axis: input(f"Python Thing variable for {axis} [{default}]: ").strip() or default
        for axis, default in NAMES.items()
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    stream = SmoothStream(NAMES)

    def receive(axis, value):
        if value is None:
            return
        try:
            sample = stream.publish(axis, value)
        except (TypeError, ValueError):
            return
        first = not OUT.exists() or OUT.stat().st_size == 0
        with OUT.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            if first:
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

    Thread(target=run_cloud, name="arduino-cloud-receiver", daemon=True).start()

    app = Dash(__name__)
    app.layout = html.Div(
        [
            html.H2("SIT225 5C · smooth live accelerometer"),
            html.P("Move the phone. Each arriving reading extends one trace; no full redraw or fake interpolation."),
            add_smooth_stream(app, stream),
        ],
        style={"fontFamily": "Arial, sans-serif", "maxWidth": "1200px", "margin": "auto"},
    )
    print("Open http://127.0.0.1:8050 in a browser. Press Ctrl+C to stop.")
    app.run(host="127.0.0.1", port=8050, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
