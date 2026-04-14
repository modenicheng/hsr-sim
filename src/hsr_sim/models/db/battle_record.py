from typing import Any

from .base import Base
from .user_characters import UserCharacter
from .types import JSONText
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[int] = mapped_column(Integer, nullable=False)  # 战斗发生的时间戳

    records: Mapped[list["BattleRecord"]] = relationship(
        "BattleRecord",
        back_populates="battle",
        passive_deletes=True,
        overlaps="battles,user_characters",
    )
    user_characters: Mapped[list[UserCharacter]] = relationship(
        "UserCharacter",
        secondary="battle_records",
        back_populates="battles",
        viewonly=True,
        overlaps="records,battle_records,battle,user_character",
    )


class BattleRecord(Base):
    __tablename__ = "battle_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    battle_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("battles.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_characters.id", ondelete="CASCADE"),
        nullable=False,
    )
    record_data: Mapped[dict[str, Any]] = mapped_column(
        JSONText, nullable=False)  # 存储战斗记录的JSON数据

    battle: Mapped[Battle | None] = relationship(
        "Battle",
        back_populates="records",
        overlaps="battles,user_characters",
    )
    user_character: Mapped[UserCharacter] = relationship(
        "UserCharacter",
        back_populates="battle_records",
        overlaps="battles,user_characters",
    )
