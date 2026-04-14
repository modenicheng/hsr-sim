from pydantic import BaseModel, Field, model_validator


class HealthComponent(BaseModel):
    hp: float = Field(gt=0)
    max_hp: float = Field(gt=0)

    @model_validator(mode="after")
    def check_hp(self):
        if (self.hp is not None and self.max_hp is not None
                and self.hp > self.max_hp):
            raise ValueError("hp cannot be greater than max_hp")
        return self


class AttackComponent(BaseModel):
    atk: float = Field(gt=0)


class DefenseComponent(BaseModel):
    defense: float = Field(gt=0)


class SpeedComponent(BaseModel):
    spd: float = Field(gt=0)
