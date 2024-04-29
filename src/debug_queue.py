"""
Debug queue

Allows for reading current queue state

Is much less efficient than a normal queue
in regard to both time and space
"""

from queue import Queue as StockQueue
from typing import Generic, TypeVar

T = TypeVar("T")

class Queue(Generic[T]):
    """A queue that has a readable debug state"""
    def __init__(self) -> None:
        self.queue: StockQueue[T] = StockQueue()
        self.items: list[T] = []

    def put(self, item: T, block: bool = True, timeout: float | None = None) -> None:
        """Add an item to the queue"""
        self.queue.put(item, block, timeout)
        self.items.append(item)

    def get(self, block: bool = True, timeout: float | None = None) -> T:
        """Get an item from the queue"""
        if len(self.items) > 0:
            self.items.pop(0)
        return self.queue.get(block, timeout)

    def empty(self) -> bool:
        """Return True if the queue is empty"""
        return self.queue.empty()

    def get_items(self) -> list[T]:
        """Get internal list of items from the queue"""
        return self.items
