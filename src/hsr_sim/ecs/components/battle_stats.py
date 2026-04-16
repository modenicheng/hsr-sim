from pydantic import BaseModel, Field, model_validator


class HealthComponent(BaseModel):
    value: float = Field(gt=0)
    max_value: float = Field(gt=0)

    @model_validator(mode="after")
    def check_hp(self):
        if (self.value is not None and self.max_value is not None
                and self.value > self.max_value):
            raise ValueError("Health value cannot be greater than max_value")
        return self


class AttackComponent(BaseModel):
    value: float = Field(gt=0)


class DefenseComponent(BaseModel):
    value: float = Field(gt=0)


class SpeedComponent(BaseModel):
    value: float = Field(gt=0)


class ActionValueComponent(BaseModel):
    value: float = Field(gt=0)
