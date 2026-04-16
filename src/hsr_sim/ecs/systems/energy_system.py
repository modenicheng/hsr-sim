"""能量系统：处理能量扣除和恢复。"""
from esper import Processor
import esper
from eventure import Event

from src.hsr_sim.ecs.components import (
    StandardEnergyComponent,
)
from src.hsr_sim.events.models import GameEvent
from src.hsr_sim.events.types import EventType


class EnergySystem(Processor):
    """能量系统：处理技能能量扣除和恢复。

    职责：
    1. 监听技能释放事件，扣除能量
    2. 监听回合/受击事件，恢复能量
    3. 确保能量在 0 ~ max_energy 范围内
    """

    def __init__(self, event_stream):
        super().__init__()
        self.event_stream = event_stream

    def process(self):
        """系统在这里暂无操作。能量变化由事件驱动。"""
        pass

    def subscribe_to_events(self):
        """订阅能量相关事件。"""
        self.event_stream.subscribe(
            EventType.SKILL_EXECUTED,
            self.on_skill_executed,
            priority=40,
            owner="energy_system",
        )
        self.event_stream.subscribe(
            EventType.TURN_STARTED,
            self.on_turn_started,
            priority=40,
            owner="energy_system",
        )
        self.event_stream.subscribe(
            EventType.DAMAGE_DEALT,
            self.on_damage_dealt,
            priority=40,
            owner="energy_system",
        )

    def on_skill_executed(self, event: Event | GameEvent):
        """处理技能释放事件，扣除能量。"""
        data = self._event_data(event)
        source_id = data.get("source_id")
        energy_cost = data.get("energy_cost", 0)

        if source_id is None or energy_cost <= 0:
            return

        self._consume_energy(source_id, energy_cost)

    def on_turn_started(self, event: Event | GameEvent):
        """处理回合开始事件，恢复能量。"""
        # MVP 版本中，回合开始时给所有存活角色恢复一定能量
        for ent, energy in esper.get_component(StandardEnergyComponent):
            self._recover_energy(ent, energy.max_energy * 0.25)  # 回合开始恢复 25%

    def on_damage_dealt(self, event: Event | GameEvent):
        """处理伤害事件，受击角色恢复能量。"""
        data = self._event_data(event)
        target_id = data.get("target_id")

        if target_id is None:
            return

        # 受击恢复能量（简化版：恢复 5%）
        self._recover_energy(target_id, 5.0)

    def _event_data(self, event: Event | GameEvent) -> dict:
        """兼容 GameEvent / eventure.Event，统一提取 data 字段。"""
        if isinstance(event, GameEvent):
            return event.data
        return dict(getattr(event, "data", {}) or {})

    def _consume_energy(self, entity_id: int, amount: float):
        """消耗能量。"""
        energy = esper.try_component(entity_id, StandardEnergyComponent)
        if not energy:
            return
        
        energy.energy = max(0, energy.energy - amount)

    def _recover_energy(self, entity_id: int, amount: float):
        """恢复能量。"""
        energy = esper.try_component(entity_id, StandardEnergyComponent)
        if not energy:
            return
        
        old_energy = energy.energy
        energy.energy = min(energy.max_energy, energy.energy + amount)
        
        # 如果能量值变化，发布事件
        if energy.energy != old_energy:
            self.event_stream.publish(
                GameEvent(
                    tick=self.event_stream.event_log.current_tick,
                    type=EventType.ENERGY_CHANGED,
                    data={
                        "entity_id": entity_id,
                        "old_energy": old_energy,
                        "new_energy": energy.energy,
                    },
                )
            )
