from pydantic import BaseModel


class SkillSlotsComponent(BaseModel):
    basic: int
    skill: int
    ultimate: int
    talent: int | None = None
    technique: int | None = None


class CooldownComponent(BaseModel):
    cooldowns: dict[int, int] = {}
