"""
min_heap.py
-----------
A manually implemented binary min-heap (array-based), used as the priority
queue in Dijkstra's algorithm. No `heapq` used.

Supports the classic "lazy deletion" approach to decrease-key: instead of
searching the heap for an existing entry and updating it in place, we simply
push a new (smaller) entry for the same vertex. When popping, Dijkstra
checks whether that vertex has already been finalized and skips stale
entries if so. This is the standard, simplest correct approach and keeps
the heap implementation itself uncomplicated.
"""

from __future__ import annotations
from typing import Any, List, Tuple


class MinHeap:
    """
    Binary min-heap storing (priority, item) pairs, ordered by priority.
    Internally backed by a plain Python list used purely as a fixed-index
    array (index arithmetic only - no list.sort(), no heapq).
    """

    def __init__(self):
        self._data: List[Tuple[float, Any]] = []

    def __len__(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def push(self, priority: float, item: Any) -> None:
        self._data.append((priority, item))
        self._sift_up(len(self._data) - 1)

    def pop_min(self) -> Tuple[float, Any]:
        if self.is_empty():
            raise IndexError("pop_min from an empty heap")

        root = self._data[0]
        last = self._data.pop()  # remove last element

        if self._data:
            self._data[0] = last
            self._sift_down(0)

        return root

    # ---------------------------------------------------------- internals ---
    def _parent(self, i: int) -> int:
        return (i - 1) // 2

    def _left(self, i: int) -> int:
        return 2 * i + 1

    def _right(self, i: int) -> int:
        return 2 * i + 2

    def _swap(self, i: int, j: int) -> None:
        self._data[i], self._data[j] = self._data[j], self._data[i]

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = self._parent(i)
            if self._data[i][0] < self._data[parent][0]:
                self._swap(i, parent)
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        size = len(self._data)
        while True:
            left = self._left(i)
            right = self._right(i)
            smallest = i

            if left < size and self._data[left][0] < self._data[smallest][0]:
                smallest = left
            if right < size and self._data[right][0] < self._data[smallest][0]:
                smallest = right

            if smallest == i:
                break

            self._swap(i, smallest)
            i = smallest
