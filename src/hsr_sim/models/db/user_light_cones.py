from typing import TYPE_CHECKING

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

if TYPE_CHECKING:
    from .user_characters import UserCharacter


class UserLightCone(Base):
    __tablename__ = "user_light_cones"
    __table_args__ = (Index("idx_light_cones_config_id", "config_id"), )

    id: Mapped[int] = mapped_column(primary_key=True)
    config_id: Mapped[int]
    version: Mapped[str] = mapped_column(String(10), default="v1.0")
    level: Mapped[int] = mapped_column(default=80)
    superimpose: Mapped[int] = mapped_column(default=1)
    locked: Mapped[bool] = mapped_column(default=False)
    character: Mapped["UserCharacter | None"] = relationship(
        "UserCharacter",
        back_populates="equipped_light_cone",
        foreign_keys="UserCharacter.equipped_light_cone_id",
        uselist=False,
    )
