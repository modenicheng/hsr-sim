from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.models.db.user_light_cones import UserLightCone
from hsr_sim.repositories.light_cone_repo import LightConeRepository


class LightConeService:

    def __init__(self, light_cone_repo: LightConeRepository):
        self.light_cone_repo = light_cone_repo

    def create_light_cone(
        self,
        config_id: int,
        version: str = "v1.0",
        level: int = 80,
        superimpose: int = 1,
        locked: bool = False,
        equipped_to_character_id: int | None = None,
    ) -> UserLightCone:
        """创建并持久化一个用户光锥实例，可选装备给指定角色。"""
        character: UserCharacter | None = None
        if equipped_to_character_id is not None:
            character = self.light_cone_repo.db.get(UserCharacter,
                                                    equipped_to_character_id)
            if character is None:
                raise ValueError(
                    f"UserCharacter with id={equipped_to_character_id} not found"
                )

        new_light_cone = UserLightCone(
            config_id=config_id,
            version=version,
            level=level,
            superimpose=superimpose,
            locked=locked,
        )
        self.light_cone_repo.add(new_light_cone)
        self.light_cone_repo.db.flush()

        if character is not None:
            character.equipped_light_cone_id = new_light_cone.id

        self.light_cone_repo.db.commit()
        self.light_cone_repo.db.refresh(new_light_cone)
        return new_light_cone
