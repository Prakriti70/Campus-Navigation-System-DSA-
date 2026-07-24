"""
vertex.py
---------
Represents a single campus location (building). Holds its name and
canvas coordinates. Coordinates are set from config.py, never hardcoded
inside algorithm or GUI logic.
"""

from __future__ import annotations


class Vertex:
    def __init__(self, name: str, x: int, y: int):
        self.name: str = name
        self.x: int = x
        self.y: int = y

    def __repr__(self) -> str:
        return f"Vertex({self.name!r}, x={self.x}, y={self.y})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Vertex) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)
