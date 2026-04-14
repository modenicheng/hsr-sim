# models/db/user_character.py
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .battle_record import Battle, BattleRecord
    from .user_light_cones import UserLightCone
    from .user_relics import UserRelic


class UserCharacter(Base):
    __tablename__ = "user_characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    char_config_id: Mapped[int]  # 无须外键，直接绑定到角色配置 ID
    version: Mapped[str] = mapped_column(String(10))
    level: Mapped[int] = mapped_column(default=80)
    eidolon_level: Mapped[int] = mapped_column(default=0)
    equipped_light_cone_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_light_cones.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    equipped_light_cone: Mapped["UserLightCone | None"] = relationship(
        "UserLightCone",
        back_populates="character",
        foreign_keys=[equipped_light_cone_id],
        uselist=False,
    )
    equipped_relics: Mapped[list["UserRelic"]] = relationship(
        "UserRelic", back_populates="character"
    )
    battle_records: Mapped[list["BattleRecord"]] = relationship(
        "BattleRecord",
        back_populates="user_character",
        passive_deletes=True,
        overlaps="battles,user_characters",
    )
    battles: Mapped[list["Battle"]] = relationship(
        "Battle",
        secondary="battle_records",
        back_populates="user_characters",
        viewonly=True,
        overlaps="battle_records,records,battle,user_character",
    )
