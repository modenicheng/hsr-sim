from pydantic import BaseModel, Field
from .enums import StatType, RelicSlot


class RelicConfig(BaseModel):
    id: int
    name: str
    relic_set_id: int  # 遗器套装 ID
    slot: RelicSlot
    rarity: int = Field(default=5, ge=1, le=5)
    main_stat: dict[StatType, float]  # 主属性，只有一个键值对
    sub_stats: dict[StatType, float] = {}  # 副属性，可以有多个键值对
    passive_2_pc: int | None = None  # 2件套被动
    passive_4_pc: int | None = None  # 4件套被动
