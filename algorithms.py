"""
algorithms.py
-------------
BFS, DFS, and Dijkstra over a Graph instance. Every algorithm uses only
the manually implemented data structures from this project:
    - BFS      -> ds_queue.Queue
    - DFS      -> ds_stack.Stack (iterative, not recursive)
    - Dijkstra -> min_heap.MinHeap

Each function returns an AlgorithmResult carrying everything the GUI needs
to both display the final answer and animate the search: the visit order
(for animation), the final path, distance, and execution time.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from graph import Graph
from ds_queue import Queue
from ds_stack import Stack
from min_heap import MinHeap
from config import WALKING_SPEED_M_PER_S


@dataclass
class AlgorithmResult:
    algorithm: str = ""
    path: List[str] = field(default_factory=list)
    visit_order: List[str] = field(default_factory=list)
    distance_m: float = 0.0          # meaningful for Dijkstra
    edge_count: int = 0              # meaningful for BFS/DFS
    exec_time_s: float = 0.0
    found: bool = False

    @property
    def walking_time_s(self) -> float:
        return self.distance_m / WALKING_SPEED_M_PER_S if self.distance_m else 0.0


def _reconstruct_path(previous: Dict[str, Optional[str]], start: str, end: str) -> List[str]:
    if end not in previous and end != start:
        return []
    path = []
    node: Optional[str] = end
    while node is not None:
        path.append(node)
        node = previous.get(node)
    path.reverse()
    return path if path and path[0] == start else []


def bfs(graph: Graph, start: str, end: str) -> AlgorithmResult:
    """
    Breadth-first search: finds the path with the fewest edges (hops),
    ignoring edge weights entirely. Uses the manual Queue as its frontier.
    Time complexity: O(V + E). Space complexity: O(V).
    """
    t0 = time.perf_counter()
    result = AlgorithmResult(algorithm="BFS")

    if not graph.has_vertex(start) or not graph.has_vertex(end):
        result.exec_time_s = time.perf_counter() - t0
        return result

    visited = {start}
    previous: Dict[str, Optional[str]] = {start: None}

    frontier = Queue()
    frontier.enqueue(start)

    while not frontier.is_empty():
        current = frontier.dequeue()
        result.visit_order.append(current)

        if current == end:
            break

        for neighbor, _weight in graph.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                previous[neighbor] = current
                frontier.enqueue(neighbor)

    path = _reconstruct_path(previous, start, end)
    result.exec_time_s = time.perf_counter() - t0

    if path:
        result.path = path
        result.edge_count = len(path) - 1
        result.found = True
        # report the real-world distance of the path it found, for comparison
        result.distance_m = _path_distance(graph, path)

    return result


def dfs(graph: Graph, start: str, end: str) -> AlgorithmResult:
    """
    Depth-first search (iterative, using the manual Stack): explores as
    deep as possible before backtracking. Does NOT guarantee a shortest
    path - included specifically to contrast against BFS/Dijkstra.
    Time complexity: O(V + E). Space complexity: O(V).
    """
    t0 = time.perf_counter()
    result = AlgorithmResult(algorithm="DFS")

    if not graph.has_vertex(start) or not graph.has_vertex(end):
        result.exec_time_s = time.perf_counter() - t0
        return result

    visited = set()
    previous: Dict[str, Optional[str]] = {start: None}

    stack = Stack()
    stack.push(start)

    while not stack.is_empty():
        current = stack.pop()

        if current in visited:
            continue
        visited.add(current)
        result.visit_order.append(current)

        if current == end:
            break

        # push neighbors in reverse so traversal order matches the order
        # they appear in the adjacency list (purely cosmetic, for
        # consistent/deterministic animation)
        neighbors = graph.get_neighbors(current)
        for neighbor, _weight in reversed(neighbors):
            if neighbor not in visited:
                if neighbor not in previous:
                    previous[neighbor] = current
                stack.push(neighbor)

    path = _reconstruct_path(previous, start, end)
    result.exec_time_s = time.perf_counter() - t0

    if path:
        result.path = path
        result.edge_count = len(path) - 1
        result.found = True
        result.distance_m = _path_distance(graph, path)

    return result


def dijkstra(graph: Graph, start: str, end: str) -> AlgorithmResult:
    """
    Dijkstra's algorithm using the manual MinHeap as its priority queue.
    Finds the path that minimizes total edge weight (real walking distance).
    Time complexity: O((V + E) log V) with a binary heap.
    Space complexity: O(V).
    """
    t0 = time.perf_counter()
    result = AlgorithmResult(algorithm="Dijkstra")

    if not graph.has_vertex(start) or not graph.has_vertex(end):
        result.exec_time_s = time.perf_counter() - t0
        return result

    distances: Dict[str, float] = {name: float("inf") for name in graph.vertex_names()}
    previous: Dict[str, Optional[str]] = {name: None for name in graph.vertex_names()}
    distances[start] = 0.0
    finalized = set()

    heap = MinHeap()
    heap.push(0.0, start)

    while not heap.is_empty():
        dist, current = heap.pop_min()

        if current in finalized:
            continue  # stale entry left over from a decrease-key push
        finalized.add(current)
        result.visit_order.append(current)

        if current == end:
            break

        for neighbor, weight in graph.get_neighbors(current):
            if neighbor in finalized:
                continue
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heap.push(new_dist, neighbor)  # lazy decrease-key

    result.exec_time_s = time.perf_counter() - t0

    if distances.get(end, float("inf")) != float("inf"):
        path = _reconstruct_path(previous, start, end)
        result.path = path
        result.edge_count = len(path) - 1
        result.distance_m = distances[end]
        result.found = True

    return result


def _path_distance(graph: Graph, path: List[str]) -> float:
    """Sum the real edge weights along a path (used to report BFS/DFS distance too)."""
    total = 0.0
    for i in range(len(path) - 1):
        for neighbor, weight in graph.get_neighbors(path[i]):
            if neighbor == path[i + 1]:
                total += weight
                break
    return total


ALGORITHMS = {
    "Dijkstra": dijkstra,
    "BFS": bfs,
    "DFS": dfs,
}
