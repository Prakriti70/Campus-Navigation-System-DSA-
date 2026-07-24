"""
ds_queue.py
-----------
A manually implemented FIFO queue, built on top of linked_list.LinkedList.
Used by BFS for its frontier. No collections.deque / queue.Queue used.

(Named ds_queue.py rather than queue.py so it never shadows Python's
built-in `queue` module, which some libraries import internally.)
"""

from __future__ import annotations
from typing import Any
from linked_list import LinkedList


class Queue:
    """FIFO queue: enqueue at the tail, dequeue from the head. Both O(1)."""

    def __init__(self):
        self._items = LinkedList()

    def enqueue(self, data: Any) -> None:
        self._items.append(data)

    def dequeue(self) -> Any:
        if self.is_empty():
            raise IndexError("dequeue from an empty queue")
        return self._items.pop_head()

    def is_empty(self) -> bool:
        return self._items.is_empty()

    def __len__(self) -> int:
        return len(self._items)
