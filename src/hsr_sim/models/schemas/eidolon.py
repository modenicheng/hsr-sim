from pydantic import BaseModel, Field


class EidolonConfig(BaseModel):
    id: int
    index: int = Field(default=1, ge=1, le=6)  # 星魂阶数，从1开始
    name: str
    describe: str
    script: str
