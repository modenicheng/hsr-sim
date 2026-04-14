from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.logger import get_logger

logger = get_logger(__name__)


def create_character_instance(db,
                              char_config_id: int,
                              version: str = "v1.0",
                              level: int = 80,
                              eidolon_level: int = 0) -> UserCharacter:
    """创建一个新的 UserCharacter 实例并保存到数据库中。

    :param db: 数据库会话
    :param char_config_id: 角色配置 ID
    :param version: 版本信息
    :param level: 角色等级，默认为 80
    :param eidolon_level: 角色命星等级，默认为 0
    :return: 创建的 UserCharacter 实例
    """
    new_character = UserCharacter(
        char_config_id=char_config_id,
        version=version,
        level=level,
        eidolon_level=eidolon_level,
    )
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    logger.info(f"Created new character instance with ID {new_character.id}")
    return new_character
