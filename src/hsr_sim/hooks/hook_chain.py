from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from hsr_sim.hooks.hook_protocol import HookResult


@dataclass(slots=True, frozen=True)
class HookHandle:
    """Hook 注册句柄。"""

    callback_id: int
    owner: str | None = None


@dataclass(slots=True)
class _HookEntry:
    priority: int
    order: int
    callback: Callable[..., Any]
    handle: HookHandle


class HookChain:
    """单个 HookPoint 的回调链。"""

    def __init__(self):
        self._entries: list[_HookEntry] = []
        self._next_callback_id = 1
        self._next_order = 1

    def register(
        self,
        callback: Callable[..., Any],
        priority: int = 0,
        owner: str | None = None,
    ) -> HookHandle:
        handle = HookHandle(callback_id=self._next_callback_id, owner=owner)
        self._next_callback_id += 1
        self._entries.append(
            _HookEntry(
                priority=priority,
                order=self._next_order,
                callback=callback,
                handle=handle,
            )
        )
        self._next_order += 1
        self._entries.sort(key=lambda item: (-item.priority, item.order))
        return handle

    def unregister(self, handle: HookHandle) -> bool:
        before = len(self._entries)
        self._entries = [
            entry for entry in self._entries if entry.handle != handle
        ]
        return len(self._entries) != before

    def unregister_owner(self, owner: str) -> int:
        before = len(self._entries)
        self._entries = [
            entry for entry in self._entries if entry.handle.owner != owner
        ]
        return before - len(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def trigger(
        self, current_value: Any = None, /, *args: Any, **kwargs: Any
    ) -> HookResult:
        result = HookResult(value=current_value)
        current = current_value

        for entry in self._entries:
            returned = entry.callback(current, *args, **kwargs)
            if isinstance(returned, HookResult):
                if returned.value is not None:
                    current = returned.value
                if returned.stop:
                    return HookResult(stop=True, value=current)
                continue

            if returned is not None:
                current = returned

        result.value = current
        return result

    @property
    def callbacks(self) -> tuple[Callable[..., Any], ...]:
        return tuple(entry.callback for entry in self._entries)
