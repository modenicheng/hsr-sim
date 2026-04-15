from collections.abc import Callable
from typing import Any, Protocol, TypeAlias, runtime_checkable

from pydantic import BaseModel, Field


class HookResult(BaseModel):
    """Hook 执行结果。"""

    stop: bool = Field(default=False)
    value: Any | None = None


HookReturn: TypeAlias = HookResult | Any | None


@runtime_checkable
class HookCallback(Protocol):
    """Hook 回调协议。"""

    def __call__(
        self,
        current_value: Any,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> HookReturn:
        """执行 hook 回调。"""


HookCallable: TypeAlias = Callable[..., HookReturn]
