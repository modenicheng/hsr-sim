from pydantic import BaseModel, Field, model_validator


class StandardEnergyComponent(BaseModel):
    energy: float = Field(ge=0)
    max_energy: float = Field(gt=0)

    @model_validator(mode="after")
    def check_energy(self):
        if (
            self.energy is not None
            and self.max_energy is not None
            and self.energy > self.max_energy
        ):
            raise ValueError("energy cannot be greater than max_energy")
        return self


class SpecialEnergyComponent(BaseModel):
    name: str
    energy: float = Field(ge=0)
    max_energy: float = Field(gt=0)

    @model_validator(mode="after")
    def check_energy(self):
        if (
            self.energy is not None
            and self.max_energy is not None
            and self.energy > self.max_energy
        ):
            raise ValueError("energy cannot be greater than max_energy")
        return self
