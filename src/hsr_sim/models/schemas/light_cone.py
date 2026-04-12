from pydantic import BaseModel, Field
from .enums import Path


class LightConeConfig(BaseModel):
    id: int
    name: str
    rarity: int = Field(default=5, ge=1, le=5)
    path: Path
    superimposition: int = Field(default=1, ge=1, le=5)  # 叠影
    passive_skill_id: int
