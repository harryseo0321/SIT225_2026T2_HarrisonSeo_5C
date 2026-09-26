"""Reusable, incremental Dash graph for any labelled continuous data streams.

The source calls ``stream.publish(channel, value)`` from its own thread.
``add_smooth_stream`` supplies a graph and registers a lightweight Dash callback.
No existing Plotly or Dash library file is modified.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Iterable

from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate


@dataclass(frozen=True)
class Sample:
    sequence: int
    channel: str
    timestamp: str
    value: float


class SmoothStream:
    """Thread-safe bounded event buffer; each event retains its own timestamp."""

    def __init__(self, channels: Iterable[str], capacity: int = 5000):
        self.channels = tuple(channels)
        if not self.channels or len(set(self.channels)) != len(self.channels):
            raise ValueError("channels must contain distinct names")
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._samples: deque[Sample] = deque(maxlen=capacity)
        self._sequence = 0
        self._lock = Lock()

    def publish(self, channel: str, value: float, timestamp: str | None = None) -> Sample:
        """Add one real observation; callable from a sensor/Cloud worker thread."""
        if channel not in self.channels:
            raise ValueError(f"unknown channel: {channel}")
        sample_time = timestamp or datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with self._lock:
            self._sequence += 1
            sample = Sample(self._sequence, channel, sample_time, float(value))
            self._samples.append(sample)
            return sample

    def since(self, sequence: int) -> tuple[list[Sample], int, bool]:
        """Return unseen samples, latest cursor and whether old data was dropped."""
        with self._lock:
            items = list(self._samples)
            latest = self._sequence
        overflow = bool(items and sequence < items[0].sequence - 1)
        return [sample for sample in items if sample.sequence > sequence], latest, overflow


def add_smooth_stream(
    app,
    stream: SmoothStream,
    graph_id: str = "live-acceleration",
    interval_ms: int = 200,
    max_points: int = 300,
    y_title: str = "Accelerometer value (phone units)",
):
    """Register a rolling graph and return the Dash component to place in a layout.

    Parameters
    ----------
    app : dash.Dash
        The Dash application. Call once per graph ID.
    stream : SmoothStream
        A buffer whose channel names become trace names. The publisher may run
        in another thread; no Dash callback is called by that thread.
    graph_id : str
        Unique component ID, including when several graphs share one app.
    interval_ms : int
        Browser polling interval; it does not fabricate extra sensor samples.
    max_points : int
        Rolling point limit for each trace, bounding browser memory.
    y_title : str
        Y-axis description and units.

    Returns
    -------
    dash.html.Div
        Add this component to ``app.layout``. Incoming points are appended via
        ``dcc.Graph.extendData``; the complete figure is not reconstructed.
    """
    if interval_ms < 50 or max_points < 1:
        raise ValueError("interval_ms must be >= 50 and max_points must be positive")

    colors = ("#1261a0", "#df622c", "#25854b", "#8737a2")
    graph = dcc.Graph(
        id=graph_id,
        figure={
            "data": [
                {
                    "type": "scattergl",
                    "mode": "lines",
                    "name": channel,
                    "x": [],
                    "y": [],
                    "line": {"color": colors[index % len(colors)], "width": 2},
                }
                for index, channel in enumerate(stream.channels)
            ],
            "layout": {
                "title": "Live smartphone accelerometer (X, Y, Z)",
                "xaxis": {"title": "Timestamp (UTC)", "type": "date"},
                "yaxis": {"title": y_title},
                "margin": {"l": 65, "r": 20, "t": 60, "b": 55},
                "legend": {"orientation": "h", "y": 1.12},
                "template": "plotly_white",
            },
        },
        config={"displaylogo": False},
        style={"height": "65vh"},
    )

    @app.callback(
        Output(graph_id, "extendData"),
        Output(f"{graph_id}-cursor", "data"),
        Output(f"{graph_id}-status", "children"),
        Input(f"{graph_id}-timer", "n_intervals"),
        State(f"{graph_id}-cursor", "data"),
    )
    def append_new_samples(_tick, cursor):
        unseen, latest, overflow = stream.since(int(cursor or 0))
        if not unseen:
            raise PreventUpdate
        grouped = {channel: {"x": [], "y": []} for channel in stream.channels}
        for sample in unseen:
            grouped[sample.channel]["x"].append(sample.timestamp)
            grouped[sample.channel]["y"].append(sample.value)
        active = [index for index, channel in enumerate(stream.channels) if grouped[channel]["x"]]
        update = {
            "x": [grouped[stream.channels[index]]["x"] for index in active],
            "y": [grouped[stream.channels[index]]["y"] for index in active],
        }
        status = f"Received {latest} samples. Showing latest {max_points} per trace."
        if overflow:
            status += " Earlier unrendered samples were dropped after buffer capacity was reached."
        return (update, active, max_points), latest, status

    return html.Div(
        [
            graph,
            html.P("Waiting for the first sensor reading…", id=f"{graph_id}-status"),
            dcc.Store(id=f"{graph_id}-cursor", data=0, storage_type="session"),
            dcc.Interval(id=f"{graph_id}-timer", interval=interval_ms, n_intervals=0),
        ]
    )
