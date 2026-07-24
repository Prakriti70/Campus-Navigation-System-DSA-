"""
ds_stack.py
-----------
A manually implemented LIFO stack, built on top of linked_list.LinkedList.
Used by DFS. Push and pop both operate at the head, so both are O(1).
"""

from __future__ import annotations
from typing import Any
from linked_list import LinkedList


class Stack:
    """LIFO stack: push and pop both happen at the head. Both O(1)."""

    def __init__(self):
        self._items = LinkedList()

    def push(self, data: Any) -> None:
        self._items.prepend(data)

    def pop(self) -> Any:
        if self.is_empty():
            raise IndexError("pop from an empty stack")
        return self._items.pop_head()

    def peek(self) -> Any:
        if self.is_empty():
            raise IndexError("peek from an empty stack")
        return self._items.head.data

    def is_empty(self) -> bool:
        return self._items.is_empty()

    def __len__(self) -> int:
        return len(self._items)
