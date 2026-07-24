"""
edge.py
-------
Represents one directed half of an edge, stored inside a vertex's
adjacency linked list: "from this vertex, you can reach `to_vertex`
at cost `weight`". The Graph class adds both directions for an
undirected edge.
"""

from __future__ import annotations


class Edge:
    def __init__(self, to_vertex: str, weight: float):
        self.to_vertex: str = to_vertex  # name of the neighboring vertex
        self.weight: float = weight       # distance in meters

    def __repr__(self) -> str:
        return f"Edge(to={self.to_vertex!r}, weight={self.weight})"
