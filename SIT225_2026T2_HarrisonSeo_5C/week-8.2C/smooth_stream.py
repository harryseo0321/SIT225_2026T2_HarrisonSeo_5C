"""Reusable Dash graph that smoothly appends live data from any source.

A data source (sensor, cloud receiver, file replay...) calls
``stream.publish(channel, value)`` from its own thread. ``add_smooth_stream``
creates the graph and a small Dash callback that sends only the new points to
the browser with ``extendData``, so the figure is never rebuilt from scratch.
No Plotly or Dash library files are modified.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Iterable

from dash import Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

__all__ = ["Sample", "SmoothStream", "add_smooth_stream"]

COLORS = ("#1261a0", "#df622c", "#25854b", "#8737a2")


@dataclass(frozen=True)
class Sample:
    """One reading: its position in the stream, channel, time and value."""

    sequence: int
    channel: str
    timestamp: str
    value: float


class SmoothStream:
    """Thread-safe buffer holding the most recent readings.

    Parameters
    ----------
    channels : iterable of str
        Names of the data channels, e.g. ("X", "Y", "Z"). Each one becomes a
        line on the graph.
    capacity : int, default 5000
        Maximum number of readings kept. When full, the oldest are removed.
    """

    def __init__(self, channels: Iterable[str], capacity: int = 5000):
        self.channels = tuple(channels)
        if not self.channels or len(set(self.channels)) != len(self.channels):
            raise ValueError("channels must be a non-empty list of distinct names")
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._samples: deque[Sample] = deque(maxlen=capacity)
        self._sequence = 0
        self._lock = Lock()

    def publish(self, channel: str, value: float, timestamp: str | None = None) -> Sample:
        """Add one reading. Safe to call from a background thread.

        If no timestamp is given, the current UTC time is used.
        """
        if channel not in self.channels:
            raise ValueError(f"unknown channel: {channel}")
        value = float(value)
        sample_time = timestamp or datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with self._lock:
            self._sequence += 1
            sample = Sample(self._sequence, channel, sample_time, value)
            self._samples.append(sample)
            return sample

    def since(self, sequence: int) -> tuple[list[Sample], int, bool]:
        """Return readings newer than ``sequence``, the latest sequence number,
        and whether some readings after ``sequence`` were already removed."""
        with self._lock:
            items = list(self._samples)
            latest = self._sequence
        dropped = bool(items) and sequence + 1 < items[0].sequence
        return [s for s in items if s.sequence > sequence], latest, dropped


def add_smooth_stream(
    app,
    stream: SmoothStream,
    graph_id: str = "live-stream",
    interval_ms: int = 200,
    max_points: int = 300,
    title: str = "Live data",
    y_title: str = "Value",
):
    """Register a live rolling graph and return the component to put in a layout.

    Parameters
    ----------
    app : dash.Dash
        The Dash app to register the update callback on.
    stream : SmoothStream
        Buffer holding the data. Its channel names become the trace names.
        stream.publish() can be called from another thread.
    graph_id : str, default "live-stream"
        Unique ID for this graph. Use a different ID for each graph in the
        same app, as reusing one causes a duplicate callback error.
    interval_ms : int, default 200
        How often the browser checks for new points. Must be at least 50.
    max_points : int, default 300
        Maximum points kept per trace in the browser. Must be at least 1.
    title : str, default "Live data"
        Graph title.
    y_title : str, default "Value"
        Y-axis label.

    Returns
    -------
    dash.html.Div
        Component to add to app.layout. New points are appended with
        dcc.Graph.extendData, so the figure is not redrawn from scratch.

    Raises
    ------
    ValueError
        If interval_ms < 50 or max_points < 1.
    """
    if interval_ms < 50 or max_points < 1:
        raise ValueError("interval_ms must be >= 50 and max_points must be >= 1")

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
                    "line": {"color": COLORS[index % len(COLORS)], "width": 2},
                }
                for index, channel in enumerate(stream.channels)
            ],
            "layout": {
                "title": {"text": title},
                "xaxis": {"title": {"text": "Time (UTC)"}, "type": "date"},
                "yaxis": {"title": {"text": y_title}},
                "margin": {"l": 65, "r": 20, "t": 90, "b": 55},
                "legend": {"orientation": "h", "y": 1.08},
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
        cursor = int(cursor or 0)
        unseen, latest, dropped = stream.since(cursor)
        if not unseen:
            raise PreventUpdate

        grouped = {channel: {"x": [], "y": []} for channel in stream.channels}
        for sample in unseen:
            grouped[sample.channel]["x"].append(sample.timestamp)
            grouped[sample.channel]["y"].append(sample.value)

        # Only channels with new points are updated; each is capped at
        # max_points so a freshly opened page doesn't receive the whole buffer.
        active = [i for i, channel in enumerate(stream.channels) if grouped[channel]["x"]]
        update = {
            "x": [grouped[stream.channels[i]]["x"][-max_points:] for i in active],
            "y": [grouped[stream.channels[i]]["y"][-max_points:] for i in active],
        }

        status = f"Received {latest} readings. Showing the latest {max_points} per trace."
        # A new page starts at cursor 0, so only warn about drops that
        # happened while this page was already open.
        if dropped and cursor > 0:
            status += " Some readings were skipped because the page fell behind."
        return (update, active, max_points), latest, status

    return html.Div(
        [
            graph,
            html.P("Waiting for the first reading…", id=f"{graph_id}-status"),
            # "memory" resets on page refresh, so a refreshed page (or a
            # restarted app) starts again from the buffered data.
            dcc.Store(id=f"{graph_id}-cursor", data=0, storage_type="memory"),
            dcc.Interval(id=f"{graph_id}-timer", interval=interval_ms, n_intervals=0),
        ]
    )
