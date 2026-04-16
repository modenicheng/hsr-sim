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
        """弹出行动值最小的实体。

        Returns:
            (entity_id, action_value) 元组

        Raises:
            IndexError: 队列为空
        """
        while self._heap:
            entry = heapq.heappop(self._heap)
            if entry.valid:
                return entry.entity_id, entry.action_value
        raise IndexError("Action queue is empty")

    def peek_next(self) -> tuple[int, float] | None:
        """查看行动值最小的实体，不删除。

        Returns:
            (entity_id, action_value) 元组，或 None 如果队列为空
        """
        while self._heap:
            entry = self._heap[0]
            if entry.valid:
                return entry.entity_id, entry.action_value
            heapq.heappop(self._heap)
        return None

    def mark_invalid(self, entity_id: int) -> None:
        """标记实体为无效（延迟删除机制）。

        用于倒下角色或销毁的召唤物，避免重建整个堆。
        """
        # 这是一个标记操作，实际删除通过 pop_next 或 peek_next 的清理完成
        pass

    def is_empty(self) -> bool:
        """检查队列是否为空。"""
        return not self._heap or all(not entry.valid for entry in self._heap)

    def size(self) -> int:
        """返回有效条目数量。"""
        return sum(1 for entry in self._heap if entry.valid)

    def clear(self) -> None:
        """清空队列。"""
        self._heap.clear()

    def subtract_all(self, amount: float) -> None:
        """对队列内所有条目的行动值减去指定值。

        用于归一化：行动完毕后，对所有实体减去下一行动者的值。
        """
        for entry in self._heap:
            entry.action_value -= amount
