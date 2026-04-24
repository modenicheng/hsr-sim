"""seele eidolon 6: 离析 — 终结技攻击后使目标陷入【乱蝶】状态，持续1回合。"""

from hsr_sim.skills.script_loader import BaseSkill


class SeeleEidolon6(BaseSkill):
    def activate(self):
        # TODO: 监听 SKILL_EXECUTED (ultimate)，为目标附加乱蝶 debuff
        # 乱蝶效果：目标受到攻击时，额外受到一次量子属性附加伤害
        pass

    def deactivate(self):
        pass
