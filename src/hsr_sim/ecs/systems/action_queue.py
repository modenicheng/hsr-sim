"""行动值优先队列工具，基于最小堆实现。"""

import heapq
from dataclasses import dataclass, field


@dataclass(order=True)
class ActionEntry:
    """行动队列中的条目，按行动值升序排列。"""

    action_value: float
    entity_id: int = field(compare=False)
    valid: bool = field(default=True, compare=False)


class ActionQueue:
    """行动值优先队列，支持高效插入、删除和获取最小值。"""

    def __init__(self):
        self._heap: list[ActionEntry] = []

    def push(self, entity_id: int, action_value: float) -> None:
        """将实体和行动值插入队列。"""
        heapq.heappush(self._heap, ActionEntry(action_value, entity_id))

    def pop_next(self) -> tuple[int, float]:
        self._clean_invalid()
        if not self._heap:
            raise IndexError("Action queue is empty")
        entry = heapq.heappop(self._heap)
        return entry.entity_id, entry.action_value

    def peek_next(self) -> tuple[int, float] | None:
        self._clean_invalid()
        if not self._heap:
            return None
        return self._heap[0].entity_id, self._heap[0].action_value

    def mark_invalid(self, entity_id: int) -> None:
        for entry in self._heap:
            if entry.entity_id == entity_id:
                entry.valid = False

    def reinsert(self, entity_id: int, new_action_value: float) -> None:
        self.mark_invalid(entity_id)
        self.push(entity_id, new_action_value)

    def _clean_invalid(self) -> None:
        self._heap = [e for e in self._heap if e.valid]

    def is_empty(self) -> bool:
        self._clean_invalid()
        return not self._heap

    def size(self) -> int:
        self._clean_invalid()
        return len(self._heap)

    def clear(self) -> None:
        """清空队列。"""
        self._heap.clear()

    def subtract_all(self, amount: float) -> None:
        """对队列内所有条目的行动值减去指定值。

        用于归一化：行动完毕后，对所有实体减去下一行动者的值。
        """
        for entry in self._heap:
            entry.action_value -= amount

    def sorted_entries(self) -> list[tuple[int, float]]:
        self._clean_invalid()
        return sorted(
            [(e.entity_id, e.action_value) for e in self._heap],
            key=lambda x: x[1],
        )
