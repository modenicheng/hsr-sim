from pydantic import BaseModel, Field


class CharacterConfig(BaseModel):
    id: int
    name: str
    base_hp: float = Field(gt=0)
    base_atk: float = Field(gt=0)
    base_def: float = Field(gt=0)
    speed: float = Field(gt=0)
    rarity: int = Field(default=5, ge=4, le=5)
    element: str = "physical"
    skill_ids: list[int] = []
