from pydantic import BaseModel, Field, model_validator


class HealthComponent(BaseModel):
    value: float = Field(gt=0)
    max_value: float = Field(gt=0)

    @model_validator(mode="after")
    def check_hp(self):
        if (
            self.value is not None
            and self.max_value is not None
            and self.value > self.max_value
        ):
            raise ValueError("Health value cannot be greater than max_value")
        return self


class AttackComponent(BaseModel):
    value: float = Field(gt=0)


class DefenseComponent(BaseModel):
    value: float = Field(gt=0)


class SpeedComponent(BaseModel):
    base_speed: float = Field(gt=0)
    speed_bonus: float = Field(default=0.0)
    speed_fix: float = Field(default=0.0)

    @property
    def final_speed(self) -> float:
        return self.base_speed * (1 + self.speed_bonus) + self.speed_fix

    @property
    def action_value(self) -> float:
        TRACK_LENGTH = 10000.0
        return TRACK_LENGTH / self.final_speed


class ActionValueComponent(BaseModel):
    value: float = Field(gt=0)


class ShieldComponent(BaseModel):
    value: float = Field(ge=0)


class CritRateComponent(BaseModel):
    value: float = Field(ge=0, le=1)


class CritDamageComponent(BaseModel):
    value: float = Field(ge=0)


class SkillPointComponent(BaseModel):
    current: int = Field(ge=0)
    max_value: int = Field(gt=0)
