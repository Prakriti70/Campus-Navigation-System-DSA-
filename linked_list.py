"""
linked_list.py
--------------
A manually implemented singly linked list. This is the foundation used by:
    - Graph adjacency lists (each vertex's neighbors are stored in one of these)
    - Queue (enqueue at tail, dequeue at head)
    - Stack (push/pop at head)

No built-in Python containers (list, deque) are used to store the actual
chain of elements - only Node objects linked via `.next`.
"""

from __future__ import annotations
from typing import Any, Optional, Iterator


class Node:
    """A single node in the linked list, holding arbitrary data."""

    def __init__(self, data: Any):
        self.data: Any = data
        self.next: Optional["Node"] = None


class LinkedList:
    """Singly linked list with O(1) append (tail-tracked) and O(n) search/remove."""

    def __init__(self):
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._size: int = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    def append(self, data: Any) -> Node:
        """Add a new node at the tail. Returns the created node."""
        node = Node(data)
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1
        return node

    def prepend(self, data: Any) -> Node:
        """Add a new node at the head. Returns the created node."""
        node = Node(data)
        node.next = self.head
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1
        return node

    def pop_head(self) -> Any:
        """Remove and return the data at the head. Raises if empty."""
        if self.head is None:
            raise IndexError("pop_head from an empty linked list")
        node = self.head
        self.head = node.next
        if self.head is None:
            self.tail = None
        self._size -= 1
        return node.data

    def remove_by_predicate(self, predicate) -> bool:
        """
        Remove the first node whose data satisfies predicate(data) == True.
        Returns True if something was removed.
        """
        prev = None
        current = self.head
        while current is not None:
            if predicate(current.data):
                if prev is None:
                    self.head = current.next
                else:
                    prev.next = current.next
                if current is self.tail:
                    self.tail = prev
                self._size -= 1
                return True
            prev = current
            current = current.next
        return False

    def __iter__(self) -> Iterator[Any]:
        current = self.head
        while current is not None:
            yield current.data
            current = current.next

    def to_list(self) -> list:
        return list(iter(self))

    def __repr__(self) -> str:
        return f"LinkedList({self.to_list()})"
