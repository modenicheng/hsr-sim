from pydantic import BaseModel, Field


class BaseResourceComponent(BaseModel):
    """叠层/增益/减益状态的基础组件，包含公共属性"""

    id: int
    name: str
    describe: str
    stack: int = 0
    max_stack: int = Field(gt=0, default=1)
    countdown: float = 0
