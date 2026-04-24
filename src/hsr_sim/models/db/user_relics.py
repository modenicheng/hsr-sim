# models/db/user_relic.py
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index, String
from .base import Base
from hsr_sim.models.db.types import JSONText

if TYPE_CHECKING:
    from .user_characters import UserCharacter


class UserRelic(Base):
    __tablename__ = "user_relics"
    __table_args__ = (Index("idx_user_relics_equipped_by", "equipped_by"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(
        String(10), default="v1.0"
    )  # 遗器配置版本
    set_id: Mapped[int]  # 无须外键，直接绑定到遗器套装配置 ID
    slot: Mapped[str]  # RelicSlot 的字符串值
    level: Mapped[int] = mapped_column(default=0)
    rarity: Mapped[int] = mapped_column(default=5)
    main_stat_type: Mapped[str]  # StatType 的字符串值
    # 副词条列表：每个元素为 {"type": str, "roll": int}
    # roll 取值 0=low, 1=med, 2=high
    sub_stats: Mapped[list[dict]] = mapped_column(JSONText, default=list)
    equipped_by: Mapped[int | None] = mapped_column(
        ForeignKey("user_characters.id", ondelete="SET NULL"), nullable=True
    )  # 关联的角色 ID，可以为 null
    character: Mapped["UserCharacter | None"] = relationship(
        "UserCharacter", back_populates="equipped_relics"
    )
