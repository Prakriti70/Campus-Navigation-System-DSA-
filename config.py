"""
config.py
---------
Single source of truth for the campus graph's layout. Add a new building
by adding a coordinate to CAMPUS_BUILDINGS and at least one entry in
CAMPUS_EDGE_TOPOLOGY - no other file needs to change, and no algorithm
code (graph.py, algorithms.py) ever reads pixel coordinates.

Coordinates below were derived directly from assets/campus_map.png
(850x790px), matched against the labeled pins visible in that image:

    DoECE          -> "Department of Electrical..." pin (top-left)
    ICTC Building  -> "ICTC Building" pin
    Library        -> "Pulchowk Campus Library" pin
    Robotics Club  -> "Robotics Club" pin
    Dean Office    -> mapped to the "Institute of Engineering" pin
                      (the small building directly behind Robotics Club),
                      per explicit instruction - there is no separate
                      "Dean Office" pin in the source image
    Main Entry     -> mapped to the midpoint of the lane/gate between
                      ICTC Building and the "Pulchowk Campus ICT Tower"
                      pin, since no distinct gate pin exists in the image

Canteen has been intentionally removed - it is not part of the graph.
"""

import math
from typing import Dict, List, Tuple

CANVAS_WIDTH = 850
CANVAS_HEIGHT = 790

# name -> (x, y) pixel position on assets/campus_map.png
CAMPUS_BUILDINGS: Dict[str, Tuple[int, int]] = {
    "Main Entry":     (595, 193),
    "Library":         (651, 401),
    "ICTC Building":    (511, 144),
    "DoECE":             (46, 50),
    "Robotics Club":      (411, 527),
    "Dean Office":         (46, 770),
}

# Topology only - which buildings are directly walkable to one another
# without passing another campus building in between. Weights are
# derived automatically from pixel distance (see below), NOT hardcoded,
# so moving a building in CAMPUS_BUILDINGS keeps edge weights consistent.
CAMPUS_EDGE_TOPOLOGY: List[Tuple[str, str]] = [
    ("Main Entry", "ICTC Building"),
    ("Main Entry", "Library"),
    ("ICTC Building", "DoECE"),
    ("ICTC Building", "Robotics Club"),
    ("Library", "Robotics Club"),
    ("Robotics Club", "Dean Office"),
    ("DoECE", "Dean Office"),
]

# PLACEHOLDER calibration factor converting pixel distance to real-world
# meters. Derived to produce plausible walking distances (15m-110m) for
# this crop of campus - replace with a real measurement (e.g. compare one
# known real distance against its pixel distance here) once available.
SCALE_METERS_PER_PIXEL = 0.15


def _pixel_distance(a: str, b: str) -> float:
    ax, ay = CAMPUS_BUILDINGS[a]
    bx, by = CAMPUS_BUILDINGS[b]
    return math.hypot(ax - bx, ay - by)


# (vertex_a, vertex_b, weight_in_meters) - computed once at import time
CAMPUS_EDGES: List[Tuple[str, str, float]] = [
    (a, b, round(_pixel_distance(a, b) * SCALE_METERS_PER_PIXEL, 1))
    for a, b in CAMPUS_EDGE_TOPOLOGY
]

# average adult walking speed, used to convert distance -> walking time
WALKING_SPEED_M_PER_S = 1.4

# animation timing (milliseconds between animation steps)
DEFAULT_ANIMATION_DELAY_MS = 500

# zoom limits for the map canvas
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0
ZOOM_STEP = 1.1

# colors (used by both light and dark themes)
THEMES = {
    "light": {
        "bg": "#F4F3F1",
        "panel_bg": "#FFFFFF",
        "text": "#1F1E1C",
        "muted_text": "#5F5E5A",
        "accent": "#378ADD",
        "node_fill": "#378ADD",
        "node_border": "#FFFFFF",
        "node_shadow": "#8A8A86",
        "node_selected": "#D85A30",
        "edge_normal": "#9A9992",
        "edge_relaxing": "#F0B429",
        "edge_visited": "#5AA65A",
        "edge_path": "#1B3A6B",
        "tooltip_bg": "#1F1E1C",
        "tooltip_text": "#FFFFFF",
    },
    "dark": {
        "bg": "#1E1E1E",
        "panel_bg": "#2A2A2A",
        "text": "#F4F3F1",
        "muted_text": "#A8A7A3",
        "accent": "#5AA6F0",
        "node_fill": "#5AA6F0",
        "node_border": "#EDEDED",
        "node_shadow": "#0A0A0A",
        "node_selected": "#FF7A54",
        "edge_normal": "#5A5A5A",
        "edge_relaxing": "#F0B429",
        "edge_visited": "#7BC94C",
        "edge_path": "#7FB2E5",
        "tooltip_bg": "#F4F3F1",
        "tooltip_text": "#1F1E1C",
    },
}
