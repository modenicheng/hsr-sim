from enum import Enum


class HookPoint(str, Enum):
    """钩子点"""
    BEFORE_DAMAGE_CALCULATION = "before_damage_calculation"  # 伤害计算前
    AFTER_DAMAGE_CALCULATION = "after_damage_calculation"  # 伤害计算后
    BEFORE_SKILL_EXECUTION = "before_skill_execution"  # 技能执行前
    AFTER_SKILL_EXECUTION = "after_skill_execution"  # 技能执行后
    BEFORE_BUFF_APPLICATION = "before_buff_application"  # Buff应用前
    AFTER_BUFF_APPLICATION = "after_buff_application"  # Buff应用后
    BEFORE_HEALING_CALCULATION = "before_healing_calculation"  # 治疗计算前
    AFTER_HEALING_CALCULATION = "after_healing_calculation"  # 治疗计算后
    ON_TURN_START = "on_turn_start"  # 回合开始
    ON_TURN_END = "on_turn_end"  # 回合结束
    ON_CHARACTER_DEFEAT = "on_character_defeat"  # 角色被击败
    ON_CHARACTER_REVIVE = "on_character_revive"  # 角色复活
    ON_ENEMY_DEFEAT = "on_enemy_defeat"  # 敌人被击败
    ON_BUFF_EXPIRE = "on_buff_expire"  # Buff失效
    ON_BUFF_STACK_CHANGE = "on_buff_stack_change"  # Buff层数变化
    ON_ENERGY_CHANGE = "on_energy_change"  # 能量变化
