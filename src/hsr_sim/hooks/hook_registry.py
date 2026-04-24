from __future__ import annotations

from collections.abc import Callable
from typing import Any

from hsr_sim.hooks.hook_chain import HookChain, HookHandle
from hsr_sim.hooks.hook_points import HookPoint
from hsr_sim.hooks.hook_protocol import HookResult


class HookRegistry:
    """全局 Hook 注册中心。"""

    def __init__(self):
        self._chains: dict[HookPoint, HookChain] = {}

    def _get_chain(self, hook_point: HookPoint) -> HookChain:
        chain = self._chains.get(hook_point)
        if chain is None:
            chain = HookChain()
            self._chains[hook_point] = chain
        return chain

    def register(
        self,
        hook_point: HookPoint,
        callback: Callable[..., Any],
        priority: int = 0,
        owner: str | None = None,
    ) -> HookHandle:
        return self._get_chain(hook_point).register(
            callback=callback,
            priority=priority,
            owner=owner,
        )

    def unregister(self, hook_point: HookPoint, handle: HookHandle) -> bool:
        chain = self._chains.get(hook_point)
        if chain is None:
            return False
        removed = chain.unregister(handle)
        if removed and not chain.callbacks:
            self._chains.pop(hook_point, None)
        return removed

    def unregister_owner(self, owner: str) -> int:
        removed = 0
        empty_points: list[HookPoint] = []
        for hook_point, chain in self._chains.items():
            removed += chain.unregister_owner(owner)
            if not chain.callbacks:
                empty_points.append(hook_point)

        for hook_point in empty_points:
            self._chains.pop(hook_point, None)

        return removed

    def trigger(
        self,
        hook_point: HookPoint,
        current_value: Any = None,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> HookResult:
        chain = self._chains.get(hook_point)
        if chain is None:
            return HookResult(value=current_value)
        return chain.trigger(current_value, *args, **kwargs)

    def clear(self) -> None:
        self._chains.clear()
