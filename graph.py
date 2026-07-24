"""
graph.py
--------
The campus map as an undirected weighted graph.

Representation: each vertex maps to a LinkedList of Edge objects (its
adjacency list) - not a Python list or dict of lists. This is what makes
the adjacency list "manual": traversing a vertex's neighbors means walking
a linked list of Edge nodes, not indexing into a built-in container.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from vertex import Vertex
from edge import Edge
from linked_list import LinkedList


class Graph:
    def __init__(self):
        self.vertices: Dict[str, Vertex] = {}
        self.adjacency: Dict[str, LinkedList] = {}

    # ------------------------------------------------------------ mutation ---
    def add_vertex(self, name: str, x: int, y: int) -> None:
        if name in self.vertices:
            return  # already present, no-op
        self.vertices[name] = Vertex(name, x, y)
        self.adjacency[name] = LinkedList()

    def add_edge(self, a: str, b: str, weight: float) -> None:
        """Add an undirected weighted edge between two existing vertices."""
        if a not in self.vertices or b not in self.vertices:
            raise ValueError(f"Both vertices must exist before adding an edge: {a}, {b}")
        if a == b:
            raise ValueError("Cannot connect a vertex to itself")

        self.adjacency[a].append(Edge(b, weight))
        self.adjacency[b].append(Edge(a, weight))

    def remove_edge(self, a: str, b: str) -> None:
        """Remove the undirected edge between a and b, if it exists."""
        if a in self.adjacency:
            self.adjacency[a].remove_by_predicate(lambda edge: edge.to_vertex == b)
        if b in self.adjacency:
            self.adjacency[b].remove_by_predicate(lambda edge: edge.to_vertex == a)

    def remove_vertex(self, name: str) -> None:
        """Remove a vertex and every edge touching it."""
        if name not in self.vertices:
            return

        # remove edges pointing at `name` from every other vertex's list
        for other_name in list(self.adjacency.keys()):
            if other_name != name:
                self.adjacency[other_name].remove_by_predicate(
                    lambda edge: edge.to_vertex == name
                )

        del self.adjacency[name]
        del self.vertices[name]

    # -------------------------------------------------------------- access ---
    def get_neighbors(self, name: str) -> List[Tuple[str, float]]:
        """Return [(neighbor_name, weight), ...] for a given vertex."""
        if name not in self.adjacency:
            return []
        return [(edge.to_vertex, edge.weight) for edge in self.adjacency[name]]

    def get_vertex(self, name: str) -> Optional[Vertex]:
        return self.vertices.get(name)

    def vertex_names(self) -> List[str]:
        return list(self.vertices.keys())

    def has_vertex(self, name: str) -> bool:
        return name in self.vertices

    def edge_list(self) -> List[Tuple[str, str, float]]:
        """Return each undirected edge exactly once as (a, b, weight)."""
        seen = set()
        result = []
        for name, edges in self.adjacency.items():
            for edge in edges:
                key = tuple(sorted((name, edge.to_vertex)))
                if key not in seen:
                    seen.add(key)
                    result.append((key[0], key[1], edge.weight))
        return result

    # ------------------------------------------------------------- display ---
    def display(self) -> str:
        """Human-readable adjacency list representation, e.g. for debugging."""
        lines = []
        for name in self.vertices:
            neighbor_strs = [f"{n}({w})" for n, w in self.get_neighbors(name)]
            lines.append(f"{name}: " + ", ".join(neighbor_strs))
        return "\n".join(lines)
