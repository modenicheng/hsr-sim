# src/hsr_sim/ecs/factories.py
import esper
from hsr_sim.services import config_loader
from .components import (
    HealthComponent,
    AttackComponent,
    DefenseComponent,
    SpeedComponent,
    StandardEnergyComponent,
    SpecialEnergyComponent,
    CharacterIdentityComponent,
)


def create_character_from_config(char_name: str, version: str) -> int:
    """根据角色名和版本创建角色实体，返回实体ID.

    :param char_name: 角色配置名
    :param version: 版本号
    :return: 创建的实体ID
    """
    char_data = config_loader.get_character(char_name, version)
    if not char_data:
        raise ValueError(f"角色 '{char_name}' 在版本 '{version}' 下未找到。")

    char_config = char_data["config"]

    # 创建一个空实体
    entity = esper.create_entity()

    # 挂载基础战斗属性组件
    esper.add_component(
        entity,
        HealthComponent(
            value=char_config.base_hp, max_value=char_config.base_hp
        ),
    )
    esper.add_component(entity, AttackComponent(value=char_config.base_atk))
    esper.add_component(entity, DefenseComponent(value=char_config.base_def))
    esper.add_component(entity, SpeedComponent(base_speed=char_config.base_spd))

    # 根据角色配置的能量类型挂载能量组件
    if char_config.energy.energy_type == "standard":
        esper.add_component(
            entity,
            StandardEnergyComponent(
                energy=0, max_energy=char_config.energy.max_energy
            ),
        )
    else:
        esper.add_component(
            entity,
            SpecialEnergyComponent(
                name=char_config.energy.energy_type,
                energy=0,
                max_energy=char_config.energy.max_energy,
            ),
        )

    # 挂载身份组件，记录其来源
    esper.add_component(
        entity,
        CharacterIdentityComponent(
            config_id=char_config.id,
            config_name=char_config.name,
            version=version,
        ),
    )

    return entity


def load_character_from_db(user_character):
    """根据数据库中的用户角色数据创建角色实体，返回实体ID.

    :param user_character: 数据库中的用户角色对象
    :return: 创建的实体ID
    """
    # 这里的实现会根据数据库模型的具体结构而有所不同
    # 需要从user_character中提取必要的信息，如角色配置ID、版本等
    # 然后调用create_character_from_config或类似的方法来创建实体
    pass  # 具体实现待定
