from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BuffScope(str, Enum):
    GLOBAL = "global"
    CHARACTER = "character"


class BuffConfig(BaseModel):
    id: int
    name: str
    description: str = ""
    scope: BuffScope = BuffScope.GLOBAL
    max_stacks: int = Field(default=1, ge=1)  # 此值仅为默认，运行时可能更改
    default_duration: int | None = Field(default=None, ge=0)
    dispelable: bool = False
    script: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    character_id: int | None = None
