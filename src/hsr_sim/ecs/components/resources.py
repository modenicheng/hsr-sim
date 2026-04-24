from pydantic import BaseModel, Field


class BaseResourceComponent(BaseModel):
    """叠层/增益/减益状态的基础组件，包含公共属性"""

    id: int
    stack: int = 0
    max_stack: int = Field(
        gt=0, default=1
    )  # 默认不可叠层。1 即为不可叠层；0为无限叠层
    countdown: float = (
        0  # 可以是小数，单位为轮次（暂时按照角色行动值计算失效时间）
    )
