from hsr_sim.models.db.user_characters import UserCharacter
from sqlalchemy.orm import selectinload

from .base import BaseRepository


class UserCharacterRepository(BaseRepository[UserCharacter]):
    def __init__(self, db):
        super().__init__(UserCharacter, db)

    def list_by_config_id(self, char_config_id: int) -> list[UserCharacter]:
        return self.list_by_filters(char_config_id=char_config_id)

    def list_by_version(self, version: str) -> list[UserCharacter]:
        return self.list_by_filters(version=version)

    def get_with_equipment(self, character_id: int) -> UserCharacter | None:
        return (
            self.db.query(UserCharacter)
            .options(
                selectinload(UserCharacter.equipped_light_cone),
                selectinload(UserCharacter.equipped_relics),
            )
            .filter(UserCharacter.id == character_id)
            .one_or_none()
        )

    def get_by_equipped_light_cone(
        self,
        light_cone_id: int,
    ) -> UserCharacter | None:
        return self.get_one_by_filters(equipped_light_cone_id=light_cone_id)


class CharacterRepository(UserCharacterRepository):
    """兼容旧命名。"""

    def __init__(self, db):
        super().__init__(db)
