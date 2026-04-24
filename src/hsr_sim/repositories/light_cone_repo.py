from sqlalchemy import and_

from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.models.db.user_light_cones import UserLightCone

from .base import BaseRepository


class UserLightConeRepository(BaseRepository[UserLightCone]):
    def __init__(self, db):
        super().__init__(UserLightCone, db)

    def list_by_config_id(self, config_id: int) -> list[UserLightCone]:
        return self.list_by_filters(config_id=config_id)

    def get_equipped_by_character(
        self,
        character_id: int,
    ) -> UserLightCone | None:
        return (
            self.db.query(UserLightCone)
            .join(
                UserCharacter,
                and_(
                    UserCharacter.equipped_light_cone_id == UserLightCone.id,
                    UserCharacter.id == character_id,
                ),
            )
            .one_or_none()
        )

    def list_unequipped(self) -> list[UserLightCone]:
        return (
            self.db.query(UserLightCone)
            .outerjoin(
                UserCharacter,
                UserCharacter.equipped_light_cone_id == UserLightCone.id,
            )
            .filter(UserCharacter.id.is_(None))
            .all()
        )


class LightConeRepository(UserLightConeRepository):
    """兼容旧命名。"""

    def __init__(self, db):
        super().__init__(db)
