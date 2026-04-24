from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user_characters import UserCharacter


user_team_characters = Table(
    "user_team_characters",
    Base.metadata,
    Column(
        "user_team_id",
        Integer,
        ForeignKey("user_teams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_character_id",
        Integer,
        ForeignKey("user_characters.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class UserTeam(Base):
    __tablename__ = "user_teams"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    team_name: Mapped[str] = mapped_column(String(100))
    characters: Mapped[list["UserCharacter"]] = relationship(
        "UserCharacter",
        secondary=user_team_characters,
        back_populates="teams",
    )
