from typing import Any

from pydantic import BaseModel, Field


class ActiveBuffComponent(BaseModel):
    """单个 Buff 实例的运行时状态（仅动态数据）。"""

    buff_id: int
    stacks: int = Field(default=1, ge=0)
    remaining_duration: float | None = Field(default=None, ge=0)
    source_entity_id: int | None = None
    runtime_values: dict[str, Any] = Field(default_factory=dict)


class BuffContainerComponent(BaseModel):
    """实体当前持有的 Buff 运行时实例列表。"""

    buffs: list[ActiveBuffComponent] = Field(default_factory=list)


class StackComponent(BaseModel):
    """通用可叠层运行时状态。"""

    stack_type: str
    current: int = Field(default=0, ge=0)
    max: int = Field(default=10, ge=1)


# 兼容旧命名
BuffComponent = ActiveBuffComponent
