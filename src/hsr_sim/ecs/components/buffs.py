from pydantic import BaseModel


class BuffContainerComponent(BaseModel):
    buff_ids: list[int] = []


class StackComponent(BaseModel):
    stack_type: str
    current: int = 0
    max: int = 10
