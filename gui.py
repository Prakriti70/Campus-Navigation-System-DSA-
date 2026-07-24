"""
gui.py
------
The Tkinter application shell and map rendering engine.

This file is purely presentation: it draws the real campus aerial image,
overlays the graph, animates traversals, and displays results. It never
implements BFS/DFS/Dijkstra itself - all of that comes from algorithms.py,
operating on the Graph built from config.py. Pixel coordinates in
config.py exist ONLY for rendering; the Graph/algorithms never see them.

Rendering model
----------------
Every frame is a full redraw driven by `_redraw()`, which draws (in this
exact stacking order, matching the required layer order):

    1. Campus aerial image (assets/campus_map.png), resized for zoom
    2. Graph edges, colored by current state (normal/relaxing/visited/path)
    3. Graph nodes, colored by current state (default/current/visited/
       path/selected), with a soft shadow, white border, hover glow, and
       a gentle pulse when selected as Start or End
    4. (Algorithm animation is just a different node/edge state - same
       drawing code, no separate layer)
    5. Building name labels
    6. Hover tooltip (drawn last, so it's always on top)

Because every frame recomputes screen position as `world * zoom + pan`,
the image, graph, labels, and tooltip always stay perfectly aligned
during zoom and pan - there's no separate coordinate system to drift out
of sync.
"""

from __future__ import annotations
import os
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Tuple, Dict

from PIL import Image, ImageTk

from graph import Graph
from algorithms import ALGORITHMS, AlgorithmResult
from chart import ExecutionChart
from config import (
    CAMPUS_BUILDINGS, CAMPUS_EDGES, CANVAS_WIDTH, CANVAS_HEIGHT,
    THEMES, DEFAULT_ANIMATION_DELAY_MS, MIN_ZOOM, MAX_ZOOM, ZOOM_STEP,
)

BASE_NODE_RADIUS = 12
HOVER_HIT_MARGIN = 5


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.theme_name = "light"
        self.theme = THEMES[self.theme_name]

        # ---- build the graph from config.py (unchanged from before) ----
        self.graph = Graph()
        for name, (x, y) in CAMPUS_BUILDINGS.items():
            self.graph.add_vertex(name, x, y)
        for a, b, w in CAMPUS_EDGES:
            self.graph.add_edge(a, b, w)

        # ---- view transform state (zoom / pan) ----
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._dragging = False
        self._drag_start = (0, 0)
        self._pan_start = (0, 0)
        self._mouse_xy = (0, 0)
        self.hover_node: Optional[str] = None

        # ---- per-node / per-edge visual state for animation ----
        # values: "default" | "current" | "visited" | "path"
        self.node_state: Dict[str, str] = {name: "default" for name in self.graph.vertex_names()}
        self.edge_state: Dict[Tuple[str, str], str] = {
            self._edge_key(a, b): "normal" for a, b, _ in self.graph.edge_list()
        }

        # ---- map image ----
        self._raw_map_image: Optional[Image.Image] = None
        self._zoomed_photo = None
        self._zoomed_photo_zoom: Optional[float] = None
        self._load_map_image()

        # ---- animation-run state ----
        self.animation_job: Optional[str] = None
        self.animation_paused = False
        self.step_mode = tk.BooleanVar(value=False)
        self.animation_delay_ms = tk.IntVar(value=DEFAULT_ANIMATION_DELAY_MS)
        self.pending_result: Optional[AlgorithmResult] = None
        self.pending_index = 0
        self.last_result: Optional[AlgorithmResult] = None

        self._build_menu()
        self._build_layout()
        self._bind_canvas_events()
        self._bind_shortcuts()
        self._redraw()
        self._pulse_tick()  # starts the continuous gentle-pulse redraw loop

    # =============================================================== menu ===
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Traversal to TXT  (Ctrl+E)", command=self._export_txt)
        file_menu.add_separator()
        file_menu.add_command(label="Quit  (Ctrl+Q)", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Toggle Dark / Light Mode  (Ctrl+D)", command=self._toggle_theme)
        view_menu.add_command(label="Reset Zoom  (double-click map)", command=self._reset_view)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-d>", lambda e: self._toggle_theme())
        self.root.bind("<Control-D>", lambda e: self._toggle_theme())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-e>", lambda e: self._export_txt())
        self.root.bind("<Return>", lambda e: self._on_find_path())

    # ============================================================= layout ===
    def _build_layout(self) -> None:
        self.root.configure(bg=self.theme["bg"])

        self.toolbar = tk.Frame(self.root, bg=self.theme["panel_bg"], height=48)
        self.toolbar.pack(side="top", fill="x")
        tk.Label(
            self.toolbar, text="Pulchowk Smart Campus Navigation System",
            bg=self.theme["panel_bg"], fg=self.theme["text"],
            font=("Segoe UI", 13, "bold"), padx=14, pady=10,
        ).pack(side="left")
        self.theme_btn = tk.Button(
            self.toolbar, text="Dark Mode", command=self._toggle_theme,
            relief="flat", bg=self.theme["accent"], fg="white",
            font=("Segoe UI", 9, "bold"), padx=10,
        )
        self.theme_btn.pack(side="right", padx=10, pady=8)

        body = tk.Frame(self.root, bg=self.theme["bg"])
        body.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(
            body, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
            bg=self.theme["panel_bg"], highlightthickness=0,
        )
        self.canvas.pack(side="left", padx=12, pady=12)

        self.sidebar = tk.Frame(body, bg=self.theme["bg"], width=300)
        self.sidebar.pack(side="right", fill="y", padx=(0, 12), pady=12)

        self._build_route_card()
        self._build_animation_card()
        self._build_results_card()
        self._build_legend_card()
        self._build_chart_card()

        self.status_var = tk.StringVar(value="Ready.  Scroll to zoom, drag to pan, double-click to reset.")
        self.status_bar = tk.Label(
            self.root, textvariable=self.status_var, anchor="w",
            bg=self.theme["panel_bg"], fg=self.theme["muted_text"],
            font=("Segoe UI", 9), padx=10, pady=4,
        )
        self.status_bar.pack(side="bottom", fill="x")

    def _card(self, title: str) -> tk.Frame:
        outer = tk.Frame(self.sidebar, bg=self.theme["panel_bg"],
                          highlightbackground=self.theme["edge_normal"], highlightthickness=1)
        outer.pack(fill="x", pady=(0, 10))
        tk.Label(
            outer, text=title, bg=self.theme["panel_bg"], fg=self.theme["text"],
            font=("Segoe UI", 10, "bold"), anchor="w",
        ).pack(fill="x", padx=10, pady=(8, 2))
        return outer

    def _build_route_card(self) -> None:
        card = self._card("Route Finder")
        names = sorted(self.graph.vertex_names())

        tk.Label(card, text="Start:", bg=self.theme["panel_bg"], fg=self.theme["muted_text"]).pack(anchor="w", padx=10)
        self.start_var = tk.StringVar(value=names[0])
        ttk.Combobox(card, textvariable=self.start_var, values=names, state="readonly").pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(card, text="End:", bg=self.theme["panel_bg"], fg=self.theme["muted_text"]).pack(anchor="w", padx=10)
        self.end_var = tk.StringVar(value=names[-1])
        ttk.Combobox(card, textvariable=self.end_var, values=names, state="readonly").pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(card, text="Algorithm:", bg=self.theme["panel_bg"], fg=self.theme["muted_text"]).pack(anchor="w", padx=10)
        self.algo_var = tk.StringVar(value="Dijkstra")
        ttk.Combobox(card, textvariable=self.algo_var, values=list(ALGORITHMS.keys()), state="readonly").pack(fill="x", padx=10, pady=(0, 8))

        tk.Button(
            card, text="Find Path", command=self._on_find_path,
            bg=self.theme["edge_visited"], fg="white", relief="flat",
            font=("Segoe UI", 10, "bold"), pady=6,
        ).pack(fill="x", padx=10, pady=(0, 10))

    def _build_animation_card(self) -> None:
        card = self._card("Animation Controls")

        btn_row = tk.Frame(card, bg=self.theme["panel_bg"])
        btn_row.pack(fill="x", padx=10, pady=(0, 6))
        tk.Button(btn_row, text="Pause", command=self._pause_animation, relief="flat").pack(side="left", expand=True, fill="x", padx=(0, 3))
        tk.Button(btn_row, text="Resume", command=self._resume_animation, relief="flat").pack(side="left", expand=True, fill="x", padx=(3, 0))

        tk.Checkbutton(
            card, text="Step-by-step mode", variable=self.step_mode,
            bg=self.theme["panel_bg"], fg=self.theme["text"],
            selectcolor=self.theme["panel_bg"], anchor="w",
        ).pack(fill="x", padx=8)

        tk.Button(card, text="Next Step", command=self._advance_one_step, relief="flat").pack(fill="x", padx=10, pady=(2, 6))

        tk.Label(card, text="Animation speed:", bg=self.theme["panel_bg"], fg=self.theme["muted_text"]).pack(anchor="w", padx=10)
        tk.Scale(
            card, from_=100, to=1500, orient="horizontal", variable=self.animation_delay_ms,
            bg=self.theme["panel_bg"], fg=self.theme["muted_text"], highlightthickness=0,
            troughcolor=self.theme["bg"],
        ).pack(fill="x", padx=10, pady=(0, 10))

    def _build_results_card(self) -> None:
        card = self._card("Results")
        self.results_text = tk.Label(
            card, text="Run an algorithm to see results here.",
            bg=self.theme["panel_bg"], fg=self.theme["text"],
            justify="left", anchor="w", wraplength=260, font=("Segoe UI", 9),
        )
        self.results_text.pack(fill="x", padx=10, pady=(0, 10))

    def _build_legend_card(self) -> None:
        card = self._card("Legend")

        node_items = [
            ("node_fill", "Location"),
            ("node_selected", "Selected (start / end)"),
        ]
        for color_key, label in node_items:
            row = tk.Frame(card, bg=self.theme["panel_bg"])
            row.pack(fill="x", padx=10, pady=2)
            swatch = tk.Canvas(row, width=14, height=14, bg=self.theme["panel_bg"], highlightthickness=0)
            swatch.create_oval(1, 1, 13, 13, fill=self.theme[color_key], outline="")
            swatch.pack(side="left", padx=(0, 6))
            tk.Label(row, text=label, bg=self.theme["panel_bg"], fg=self.theme["muted_text"], font=("Segoe UI", 8)).pack(side="left")

        edge_items = [
            ("edge_normal", "Normal edge"),
            ("edge_relaxing", "Current relaxation"),
            ("edge_visited", "Visited traversal edge"),
            ("edge_path", "Final shortest path"),
        ]
        for color_key, label in edge_items:
            row = tk.Frame(card, bg=self.theme["panel_bg"])
            row.pack(fill="x", padx=10, pady=2)
            swatch = tk.Canvas(row, width=14, height=14, bg=self.theme["panel_bg"], highlightthickness=0)
            swatch.create_line(1, 7, 13, 7, fill=self.theme[color_key], width=3)
            swatch.pack(side="left", padx=(0, 6))
            tk.Label(row, text=label, bg=self.theme["panel_bg"], fg=self.theme["muted_text"], font=("Segoe UI", 8)).pack(side="left")

    def _build_chart_card(self) -> None:
        card = self._card("Execution Time Comparison")
        self.chart = ExecutionChart(card, self.theme)
        self.chart.pack(fill="both", expand=True)

    # ========================================================= map image ===
    def _load_map_image(self) -> None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(script_dir, "assets", "campus_map.png")

        if os.path.exists(map_path):
            try:
                self._raw_map_image = Image.open(map_path).convert("RGBA")
                print(f"[pulchowk_nav] Loaded map image from: {map_path} "
                      f"({self._raw_map_image.width}x{self._raw_map_image.height})")
                return
            except Exception as e:
                print(f"[pulchowk_nav] Found map at {map_path} but failed to open it: {e}")
        else:
            print(f"[pulchowk_nav] No map image found at: {map_path} - using blank background.")
        self._raw_map_image = None

    def _get_map_photo(self):
        """Return a PhotoImage of the map resized for the current zoom, caching
        across pan-only redraws so we don't re-resize the image on every
        mouse-drag tick (only when the zoom level actually changes)."""
        if self._raw_map_image is None:
            return None
        if self._zoomed_photo is None or self._zoomed_photo_zoom != self.zoom:
            w = max(1, int(self._raw_map_image.width * self.zoom))
            h = max(1, int(self._raw_map_image.height * self.zoom))
            resized = self._raw_map_image.resize((w, h))
            self._zoomed_photo = ImageTk.PhotoImage(resized)
            self._zoomed_photo_zoom = self.zoom
        return self._zoomed_photo

    # ======================================================== transforms ===
    def _world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        return x * self.zoom + self.pan_x, y * self.zoom + self.pan_y

    def _screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        return (sx - self.pan_x) / self.zoom, (sy - self.pan_y) / self.zoom

    def _scaled_radius(self) -> float:
        return max(5.0, BASE_NODE_RADIUS * self.zoom)

    @staticmethod
    def _edge_key(a: str, b: str) -> Tuple[str, str]:
        return tuple(sorted((a, b)))

    def _node_at_screen(self, sx: float, sy: float) -> Optional[str]:
        r = self._scaled_radius() + HOVER_HIT_MARGIN
        for name in self.graph.vertex_names():
            v = self.graph.get_vertex(name)
            nx, ny = self._world_to_screen(v.x, v.y)
            if (nx - sx) ** 2 + (ny - sy) ** 2 <= r ** 2:
                return name
        return None

    # ============================================================= redraw ===
    def _redraw(self) -> None:
        self.canvas.delete("all")

        # ---- layer 1: campus aerial image ----
        photo = self._get_map_photo()
        if photo is not None:
            self.canvas.create_image(self.pan_x, self.pan_y, anchor="nw", image=photo)
        else:
            for x in range(0, CANVAS_WIDTH, 50):
                sx0, sy0 = self._world_to_screen(x, 0)
                sx1, sy1 = self._world_to_screen(x, CANVAS_HEIGHT)
                self.canvas.create_line(sx0, sy0, sx1, sy1, fill=self.theme["edge_normal"])
            for y in range(0, CANVAS_HEIGHT, 50):
                sx0, sy0 = self._world_to_screen(0, y)
                sx1, sy1 = self._world_to_screen(CANVAS_WIDTH, y)
                self.canvas.create_line(sx0, sy0, sx1, sy1, fill=self.theme["edge_normal"])

        # ---- layer 2: edges ----
        edge_colors = {
            "normal": self.theme["edge_normal"],
            "relaxing": self.theme["edge_relaxing"],
            "visited": self.theme["edge_visited"],
            "path": self.theme["edge_path"],
        }
        edge_widths = {"normal": 2, "relaxing": 3, "visited": 3, "path": 4}

        for a, b, weight in self.graph.edge_list():
            key = self._edge_key(a, b)
            state = self.edge_state.get(key, "normal")
            va, vb = self.graph.get_vertex(a), self.graph.get_vertex(b)
            sax, say = self._world_to_screen(va.x, va.y)
            sbx, sby = self._world_to_screen(vb.x, vb.y)
            self.canvas.create_line(
                sax, say, sbx, sby,
                fill=edge_colors[state], width=edge_widths[state],
            )
            mx, my = (sax + sbx) / 2, (say + sby) / 2
            self.canvas.create_text(
                mx, my, text=f"{weight:.0f}m", fill=self.theme["muted_text"],
                font=("Segoe UI", max(6, int(8 * self.zoom))),
            )

        # ---- layer 3 + 4: nodes (default color, or animation state) ----
        node_fill_by_state = {
            "default": self.theme["node_fill"],
            "current": self.theme["edge_relaxing"],
            "visited": self.theme["edge_visited"],
            "path": self.theme["edge_path"],
        }
        pulse = 2.0 * abs(math.sin(time.time() * 3.0))

        for name in self.graph.vertex_names():
            v = self.graph.get_vertex(name)
            sx, sy = self._world_to_screen(v.x, v.y)
            r = self._scaled_radius()

            is_selected = name in (self.start_var.get(), self.end_var.get())
            is_hovered = name == self.hover_node

            draw_r = r + (pulse if is_selected else 0) + (3 if is_hovered else 0)

            # soft shadow
            self.canvas.create_oval(
                sx - draw_r + 2, sy - draw_r + 3, sx + draw_r + 2, sy + draw_r + 3,
                fill=self.theme["node_shadow"], outline="",
            )

            # hover glow ring
            if is_hovered:
                self.canvas.create_oval(
                    sx - draw_r - 6, sy - draw_r - 6, sx + draw_r + 6, sy + draw_r + 6,
                    fill="", outline=self.theme["accent"], width=2,
                )

            fill = self.theme["node_selected"] if is_selected else node_fill_by_state[self.node_state.get(name, "default")]
            self.canvas.create_oval(
                sx - draw_r, sy - draw_r, sx + draw_r, sy + draw_r,
                fill=fill, outline=self.theme["node_border"], width=2,
            )

        # ---- layer 5: labels ----
        for name in self.graph.vertex_names():
            v = self.graph.get_vertex(name)
            sx, sy = self._world_to_screen(v.x, v.y)
            r = self._scaled_radius()
            self.canvas.create_text(
                sx, sy - r - 10, text=name, fill=self.theme["text"],
                font=("Segoe UI", max(7, int(9 * self.zoom)), "bold"),
            )

        # ---- layer 6: tooltip (always drawn last -> always on top) ----
        if self.hover_node is not None:
            self._draw_tooltip(self.hover_node)

    def _draw_tooltip(self, name: str) -> None:
        neighbors = self.graph.get_neighbors(name)
        text = name + ("\n" + ", ".join(f"{n} ({w:.0f}m)" for n, w in neighbors) if neighbors else "")
        mx, my = self._mouse_xy
        padding = 6
        # rough size estimate so the box comfortably fits the text
        lines = text.split("\n")
        w = max(len(line) for line in lines) * 6 + padding * 2
        h = len(lines) * 14 + padding * 2
        x0, y0 = mx + 14, my + 14
        self.canvas.create_rectangle(
            x0, y0, x0 + w, y0 + h,
            fill=self.theme["tooltip_bg"], outline="",
        )
        self.canvas.create_text(
            x0 + padding, y0 + padding, text=text, fill=self.theme["tooltip_text"],
            font=("Segoe UI", 8), anchor="nw", justify="left",
        )

    # ============================================================= events ===
    def _bind_canvas_events(self) -> None:
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Double-Button-1>", lambda e: self._reset_view())
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)       # Windows / macOS
        self.canvas.bind("<Button-4>", lambda e: self._zoom_at(e.x, e.y, ZOOM_STEP))    # Linux scroll up
        self.canvas.bind("<Button-5>", lambda e: self._zoom_at(e.x, e.y, 1 / ZOOM_STEP))  # Linux scroll down

    def _on_canvas_motion(self, event) -> None:
        self._mouse_xy = (event.x, event.y)
        if self._dragging:
            return
        node = self._node_at_screen(event.x, event.y)
        if node != self.hover_node:
            self.hover_node = node
            if node:
                neighbors = ", ".join(f"{n} ({w:.0f}m)" for n, w in self.graph.get_neighbors(node))
                self.status_var.set(f"{node} - connects to: {neighbors}" if neighbors else node)
            else:
                self.status_var.set("Ready.  Scroll to zoom, drag to pan, double-click to reset.")
            self._redraw()

    def _on_canvas_press(self, event) -> None:
        node = self._node_at_screen(event.x, event.y)
        if node is not None:
            self._on_node_click(node)
        else:
            self._dragging = True
            self._drag_start = (event.x, event.y)
            self._pan_start = (self.pan_x, self.pan_y)

    def _on_canvas_drag(self, event) -> None:
        if not self._dragging:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self.pan_x = self._pan_start[0] + dx
        self.pan_y = self._pan_start[1] + dy
        self._redraw()

    def _on_canvas_release(self, event) -> None:
        self._dragging = False

    def _on_mousewheel(self, event) -> None:
        factor = ZOOM_STEP if event.delta > 0 else 1 / ZOOM_STEP
        self._zoom_at(event.x, event.y, factor)

    def _zoom_at(self, sx: float, sy: float, factor: float) -> None:
        world_x, world_y = self._screen_to_world(sx, sy)
        new_zoom = min(MAX_ZOOM, max(MIN_ZOOM, self.zoom * factor))
        self.zoom = new_zoom
        self.pan_x = sx - world_x * new_zoom
        self.pan_y = sy - world_y * new_zoom
        self._redraw()

    def _reset_view(self) -> None:
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._redraw()

    def _on_node_click(self, name: str) -> None:
        if name == self.start_var.get():
            self.status_var.set(f"{name} is already set as the start location.")
            return
        self.end_var.set(name)
        self.status_var.set(f"Set as destination: {name}")
        self._redraw()

    def _pulse_tick(self) -> None:
        """Continuous lightweight redraw loop so selected-node pulsing and
        hover glow stay smooth without being tied to algorithm animation."""
        self._redraw()
        self.root.after(120, self._pulse_tick)

    # ========================================================= algorithm ===
    def _on_find_path(self) -> None:
        start, end = self.start_var.get(), self.end_var.get()
        algo_name = self.algo_var.get()

        if start == end:
            messagebox.showwarning("Invalid selection", "Start and End must be different locations.")
            return

        self._cancel_animation()
        self._reset_graph_state()

        result = ALGORITHMS[algo_name](self.graph, start, end)
        self.last_result = result
        self.chart.record(algo_name, result.exec_time_s)

        if not result.found:
            self.status_var.set(f"{algo_name}: no path found between {start} and {end}.")
            self.results_text.config(text=f"No path found between {start} and {end}.")
            return

        self.pending_result = result
        self.pending_index = 0
        self.animation_paused = False
        self.status_var.set(f"Animating {algo_name}...")

        if self.step_mode.get():
            self._advance_one_step()
        else:
            self._animate_next_step()

    def _reset_graph_state(self) -> None:
        self.node_state = {name: "default" for name in self.graph.vertex_names()}
        self.edge_state = {self._edge_key(a, b): "normal" for a, b, _ in self.graph.edge_list()}
        self._redraw()

    def _infer_edge_to(self, current: str, already_visited: list) -> Optional[Tuple[str, str]]:
        """
        Best-effort guess at which edge led to `current`, using only data
        already returned by algorithms.py (visit_order) - no changes to
        algorithms.py itself. We look for the most recently visited node
        that is an actual neighbor of `current`.
        """
        neighbor_names = {n for n, _ in self.graph.get_neighbors(current)}
        for prior in reversed(already_visited):
            if prior in neighbor_names:
                return self._edge_key(current, prior)
        return None

    def _animate_next_step(self) -> None:
        if self.animation_paused or self.pending_result is None:
            return

        result = self.pending_result
        if self.pending_index < len(result.visit_order):
            self._apply_step(result, self.pending_index)
            self.pending_index += 1
            self._redraw()
            self.animation_job = self.root.after(self.animation_delay_ms.get(), self._animate_next_step)
        else:
            self._finish_animation(result)

    def _advance_one_step(self) -> None:
        if self.pending_result is None:
            return
        result = self.pending_result
        if self.pending_index < len(result.visit_order):
            self._apply_step(result, self.pending_index)
            node = result.visit_order[self.pending_index]
            self.status_var.set(f"Visiting: {node}  (step {self.pending_index + 1}/{len(result.visit_order)})")
            self.pending_index += 1
            self._redraw()
        else:
            self._finish_animation(result)

    def _apply_step(self, result: AlgorithmResult, index: int) -> None:
        already_visited = result.visit_order[:index]
        current = result.visit_order[index]

        # demote the previous "current" node/edge down to "visited"
        if index > 0:
            prev_node = result.visit_order[index - 1]
            self.node_state[prev_node] = "visited"
            prev_edge = self._infer_edge_to(prev_node, already_visited[:-1])
            if prev_edge:
                self.edge_state[prev_edge] = "visited"

        self.node_state[current] = "current"
        edge = self._infer_edge_to(current, already_visited)
        if edge:
            self.edge_state[edge] = "relaxing"

    def _finish_animation(self, result: AlgorithmResult) -> None:
        for name in result.path:
            self.node_state[name] = "path"
        for i in range(len(result.path) - 1):
            key = self._edge_key(result.path[i], result.path[i + 1])
            self.edge_state[key] = "path"
        self._redraw()

        unit_note = "meters (real distance)" if result.algorithm == "Dijkstra" else "edges (hop count)"
        self.results_text.config(text=(
            f"Algorithm: {result.algorithm}\n"
            f"Path: {' -> '.join(result.path)}\n\n"
            f"Distance: {result.distance_m:.1f} m\n"
            f"Estimated walking time: {result.walking_time_s:.1f} s\n"
            f"Execution time: {result.exec_time_s * 1000:.4f} ms"
        ))
        self.status_var.set(f"{result.algorithm} finished.")
        self.pending_result = None

    def _pause_animation(self) -> None:
        self.animation_paused = True
        self.status_var.set("Animation paused.")

    def _resume_animation(self) -> None:
        if self.pending_result is None:
            return
        self.animation_paused = False
        self.status_var.set("Animation resumed.")
        if not self.step_mode.get():
            self._animate_next_step()

    def _cancel_animation(self) -> None:
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None
        self.pending_result = None
        self.pending_index = 0
        self.animation_paused = False

    # ================================================================ misc ===
    def _export_txt(self) -> None:
        if self.last_result is None:
            messagebox.showinfo("Nothing to export", "Run an algorithm first.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return

        r = self.last_result
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Algorithm: {r.algorithm}\n")
            f.write(f"Visit order: {' -> '.join(r.visit_order)}\n")
            f.write(f"Final path: {' -> '.join(r.path)}\n")
            f.write(f"Distance: {r.distance_m:.1f} m\n")
            f.write(f"Walking time: {r.walking_time_s:.1f} s\n")
            f.write(f"Execution time: {r.exec_time_s * 1000:.4f} ms\n")

        self.status_var.set(f"Exported traversal to {path}")

    def _toggle_theme(self) -> None:
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.theme = THEMES[self.theme_name]
        self.theme_btn.config(text="Light Mode" if self.theme_name == "dark" else "Dark Mode")

        for widget in self.root.winfo_children():
            widget.destroy()
        self._build_menu()
        self._build_layout()
        self._redraw()

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About",
            "Pulchowk Smart Campus Navigation System\n\n"
            "A DSA demonstration project implementing, entirely from "
            "scratch: a singly linked list, queue, stack, binary min-heap, "
            "an undirected weighted graph, and BFS, DFS, and Dijkstra's "
            "algorithm - overlaid on a real aerial image of Pulchowk Campus.\n\n"
            "Built with Python, Tkinter, and Pillow.",
        )
