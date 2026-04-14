from pydantic import BaseModel

class BuffComponent(BaseModel):
    buff_id: int
    source: str | None = None
    duration: float | None = None  # 持续回合

class BuffContainerComponent(BaseModel):
    buff_ids: list[int] = []


class StackComponent(BaseModel):
    stack_type: str
    current: int = 0
    max: int = 10
