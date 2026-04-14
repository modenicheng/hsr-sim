from pydantic import BaseModel, Field, model_validator
from src.hsr_sim.models.schemas.enums import Element, Path, StatType


class HealthComponent(BaseModel):
    hp: float = Field(gt=0)
    max_hp: float = Field(gt=0)

    @model_validator(mode="after")
    def check_hp(self):
        hp = self.hp
        max_value = self.max_hp
        if hp is not None and max_value is not None and hp > max_value:
            raise ValueError("hp cannot be greater than max_value")
        return self


class AttackComponent(BaseModel):
    atk: float = Field(gt=0)


class DefenseComponent(BaseModel):
    defense: float = Field(gt=0)


class SpeedComponent(BaseModel):
    spd: float = Field(gt=0)

class StandardEnergyComponent(BaseModel):
    energy: float = Field(ge=0)
    # 可能使用脚本直接控制比较灵活
    # throttle: float = Field(ge=0)  # 释放大招的能量阈值。通常与max_energy相同，但也可以设置为更小的值以实现特殊机制（如银枝的两段大招）
    max_energy: float = Field(gt=0)

    @model_validator(mode="after")
    def check_energy(self):
        energy = self.energy
        max_value = self.max_energy
        if energy is not None and max_value is not None and energy > max_value:
            raise ValueError("energy cannot be greater than max_energy")
        return self

class SpecialEnergyComponent(BaseModel):
    name: str  # 能量类型名称（如「飞黄」-飞霄）
    energy: float = Field(ge=0)
    max_energy: float = Field(gt=0)

    @model_validator(mode="after")
    def check_energy(self):
        energy = self.energy
        max_value = self.max_energy
        if energy is not None and max_value is not None and energy > max_value:
            raise ValueError("energy cannot be greater than max_energy")
        return self

class CharacterIdentityComponent(BaseModel):
    config_id: int
    config_name: str
    version: str
