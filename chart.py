"""
chart.py
--------
Embeds a small matplotlib bar chart in the sidebar, tracking the most
recent execution time recorded for each algorithm so they can be visually
compared after being run at least once each.
"""

import tkinter as tk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ExecutionChart(tk.Frame):
    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, bg=theme["panel_bg"], **kwargs)
        self.theme = theme
        self.times = {"Dijkstra": None, "BFS": None, "DFS": None}

        self.figure = Figure(figsize=(2.8, 2.2), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 8))

        self._draw()

    def record(self, algorithm: str, exec_time_s: float) -> None:
        if algorithm not in self.times:
            return
        self.times[algorithm] = exec_time_s
        self._draw()

    def reset(self) -> None:
        self.times = {k: None for k in self.times}
        self._draw()

    def _draw(self) -> None:
        self.ax.clear()
        labels = list(self.times.keys())
        values = [(self.times[k] or 0) * 1000 for k in labels]
        bars = self.ax.bar(labels, values, color=["#378ADD", "#639922", "#D85A30"])

        self.ax.set_ylabel("ms", fontsize=8)
        self.ax.tick_params(labelsize=8)
        for bar, key in zip(bars, labels):
            height = bar.get_height()
            label = f"{height:.3f}" if self.times[key] is not None else "n/a"
            self.ax.text(bar.get_x() + bar.get_width() / 2, height, label,
                         ha="center", va="bottom", fontsize=7)

        self.figure.tight_layout()
        self.canvas.draw()
