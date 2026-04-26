"""战斗会话：统一管理战斗生命周期、ECS 系统和状态机。"""

from typing import Optional

import esper
from hsr_sim.services import config_loader
from hsr_sim.skills.script_loader import SkillContext as LoaderSkillContext
from hsr_sim.skills.script_loader import SkillScriptLoader

from hsr_sim.ecs.world import ECSWorld
from hsr_sim.ecs.systems import (
    TurnSystem,
    DamageSystem,
    HealingSystem,
    HealthSystem,
    EnergySystem,
    BuffSystem,
)
from hsr_sim.ecs.components import (
    BuffContainerComponent,
    CharacterStatusComponent,
    CharacterIdentityComponent,
)
from hsr_sim.models.character_status import CharacterStatus
from hsr_sim.models.battle_state import BattleState, ActionInput


class BattleSession:
    """战斗会话：统一管理 ECS 上下文、系统、状态机和战斗循环。

    职责：
    - 创建/销毁 ECS 世界
    - 管理系统的注册和执行顺序
    - 维护战斗状态和逻辑帧
    - 实现主循环和状态转移
    - 接收玩家/AI 的行动输入
    - 判定战斗胜负
    """

    def __init__(self, config_version: str):
        self.config_version = config_version
        self.state = BattleState.IDLE
        self.current_tick = 0
        self.current_turn = 0

        # 创建独立的 ECS 世界
        self.world = ECSWorld(config_version)
        esper.switch_world(self.world.world_name)

        # 初始化系统
        self.turn_system = TurnSystem(self.world.event_stream)
        self.damage_system = DamageSystem(
            self.world.event_stream,
            self.world.hook_registry,
            lambda: self.current_tick,
        )
        self.healing_system = HealingSystem(
            self.world.event_stream,
            self.world.hook_registry,
            lambda: self.current_tick,
        )
        self.health_system = HealthSystem(
            self.world.event_stream, self.world.hook_registry
        )
        self.energy_system = EnergySystem(self.world.event_stream)
        self.buff_system = BuffSystem(
            self.world.event_stream, self.world.hook_registry
        )

        # 系统注册顺序很重要
        self.world.systems = [
            self.turn_system,
            self.damage_system,
            self.healing_system,
            self.health_system,
            self.energy_system,
            self.buff_system,
        ]

        # 订阅事件
        self.health_system.subscribe_to_events()
        self.energy_system.subscribe_to_events()
        self.buff_system.subscribe_to_events()

        # 状态
        self._current_actor_id: int | None = None
        self._team_ids: set[int] = set()
        self._enemy_ids: set[int] = set()
        self._skill_loader = SkillScriptLoader()
        self._skill_instance_cache: dict[tuple[int, int], object] = {}

    def start(self, team_ids: list[int], enemy_ids: list[int]):
        """初始化战斗，生成实体并启动主循环。"""
        self.world.activate()

        self._team_ids = set(team_ids)
        self._enemy_ids = set(enemy_ids)
        self._prepare_participants(self._team_ids | self._enemy_ids)

        # 为所有参战实体初始化（应该已在 factories 中做好）
        # 这里假设实体已经存在于 world 中

        # 初始化 TurnSystem 的行动队列
        self.turn_system.initialize()

        self.state = BattleState.PREPARING
        self.current_turn = 0
        self.current_tick = 0

        # 启动主循环
        self._run_loop()

    def _run_loop(self):
        """主循环：持续推进直到战斗结束或等待玩家输入。"""
        if self.state in (BattleState.IDLE, BattleState.PREPARING):
            self.state = BattleState.TURN_START

        while self.state not in (
            BattleState.FINISHED,
            BattleState.WAITING_ACTION,
        ):
            self.current_tick += 1
            self.turn_system.set_current_tick(self.current_tick)

            # 处理主状态转移
            if self.state == BattleState.TURN_START:
                self._advance_to_next_actor()
            elif self.state == BattleState.EXECUTING_ACTION:
                # 行动执行在 submit_action 中完成
                pass
            elif self.state == BattleState.TURN_END:
                self.current_turn += 1
                self.state = BattleState.TURN_START

            # 检查胜负条件
            if self._check_victory_condition():
                self.state = BattleState.FINISHED
                break

    def _advance_to_next_actor(self):
        """推进到下一个行动者。"""
        if self.turn_system.get_current_actor() is not None:
            self._current_actor_id = self.turn_system.get_current_actor()
            self.state = BattleState.WAITING_ACTION
        else:
            # 队列为空，战斗结束
            self.state = BattleState.FINISHED

    def submit_action(self, action_input: ActionInput) -> bool:
        """接收玩家或 AI 提交的行动。

        Args:
            action_input: 行动输入

        Returns:
            是否成功提交
        """
        # 校验当前状态
        if self.state != BattleState.WAITING_ACTION:
            return False

        # 校验行动者
        if action_input.actor_id != self._current_actor_id:
            return False

        # 执行行动（简化版：暂不处理技能执行）
        self.state = BattleState.EXECUTING_ACTION

        if not self._execute_action(action_input):
            self.state = BattleState.WAITING_ACTION
            return False

        # 标记行动完成
        self.turn_system.on_action_finished()

        # 返回主循环
        self.state = BattleState.TURN_END
        self._run_loop()

        return True

    def _prepare_participants(self, entity_ids: set[int]):
        """为参战实体补齐最小战斗组件。"""
        for entity_id in entity_ids:
            if not esper.entity_exists(entity_id):
                continue

            if esper.try_component(entity_id, CharacterStatusComponent) is None:
                esper.add_component(
                    entity_id,
                    CharacterStatusComponent(status=CharacterStatus.ALIVE),
                )

            if esper.try_component(entity_id, BuffContainerComponent) is None:
                esper.add_component(entity_id, BuffContainerComponent())

    def _execute_action(self, action_input: ActionInput) -> bool:
        """执行行动输入（MVP：基础攻击/技能伤害 + 治疗）。"""
        actor_id = action_input.actor_id
        if not esper.entity_exists(actor_id):
            return False

        valid_targets = [
            tid for tid in action_input.targets if esper.entity_exists(tid)
        ]
        if not valid_targets:
            return False

        action_type = action_input.action_type.lower()
        params = action_input.params or {}

        skill_name_for_event = action_input.action_type
        script_result = self._execute_skill_script(actor_id, action_input)
        if script_result is not None:
            resolved_name = script_result.get("skill_name")
            if isinstance(resolved_name, str) and resolved_name.strip():
                skill_name_for_event = resolved_name
            if self._apply_script_effect(
                actor_id, valid_targets, script_result
            ):
                self.world.event_stream.publish_skill_executed_event(
                    tick=self.current_tick,
                    skill_name=skill_name_for_event,
                    source_id=actor_id,
                    target_id=valid_targets[0],
                )
                return True

        if action_type in {"basic", "basic_atk", "skill"}:
            base_damage = float(params.get("base_damage", 100.0))
            damage_type = params.get("damage_type")
            for target_id in valid_targets:
                self.damage_system.calculate_and_apply_damage(
                    attacker_id=actor_id,
                    defender_id=target_id,
                    base_damage=base_damage,
                    damage_type=damage_type,
                )

        elif action_type in {"heal", "healing"}:
            base_healing = float(params.get("base_healing", 100.0))
            for target_id in valid_targets:
                self.healing_system.calculate_and_apply_healing(
                    healer_id=actor_id,
                    target_id=target_id,
                    base_healing=base_healing,
                )
        else:
            return False

        self.world.event_stream.publish_skill_executed_event(
            tick=self.current_tick,
            skill_name=skill_name_for_event,
            source_id=actor_id,
            target_id=valid_targets[0],
        )
        return True

    def _execute_skill_script(
        self, actor_id: int, action_input: ActionInput
    ) -> dict | None:
        """按 skill_id 解析并执行技能脚本。"""
        params = action_input.params or {}
        skill_id_raw = params.get("skill_id")
        if skill_id_raw is None:
            return None
        try:
            skill_id = int(skill_id_raw)
        except (TypeError, ValueError):
            return None

        identity = esper.try_component(actor_id, CharacterIdentityComponent)
        if identity is None:
            return None

        version = identity.version or self.config_version
        payload = config_loader.get_character_by_id(
            identity.config_id, version=version
        )
        if not payload:
            return None

        char_config = payload.get("config")
        if char_config is None:
            return None

        skill_config = self._find_skill_config_by_id(char_config, skill_id)
        if skill_config is None:
            return None

        cache_key = (actor_id, skill_id)
        skill_obj = self._skill_instance_cache.get(cache_key)
        if skill_obj is None:
            context = LoaderSkillContext(
                world=self.world,
                event_bus=self.world.event_stream,
                hook_chain=self.world.hook_registry,
                config_loader=config_loader,
            )
            skill_obj = self._skill_loader.load_skill(
                version=version,
                char_name=char_config.name,
                script=skill_config.script,
                context=context,
                skill_type=getattr(
                    skill_config.type, "value", str(skill_config.type)
                ),
            )
            self._skill_instance_cache[cache_key] = skill_obj

        execute = getattr(skill_obj, "execute", None)
        if not callable(execute):
            return {
                "skill_name": skill_config.name,
            }

        try:
            result = execute(actor_id, action_input.targets)
        except Exception:
            return None

        if isinstance(result, dict):
            if "skill_name" not in result:
                result["skill_name"] = skill_config.name
            return result

        return {
            "skill_name": skill_config.name,
        }

    @staticmethod
    def _find_skill_config_by_id(char_config, skill_id: int):
        """在角色主动技能中按 id 查找技能配置。"""
        for cfg in (
            char_config.basic_atk,
            char_config.skill,
            char_config.ultimate,
        ):
            if cfg.id == skill_id:
                return cfg
        return None

    def _apply_script_effect(
        self, actor_id: int, target_ids: list[int], script_result: dict
    ) -> bool:
        """将脚本返回效果应用到系统。"""
        effect = str(script_result.get("effect", "")).lower()

        if effect == "damage":
            base_damage = float(script_result.get("base_damage", 100.0))
            damage_type = script_result.get("damage_type")
            for target_id in target_ids:
                self.damage_system.calculate_and_apply_damage(
                    attacker_id=actor_id,
                    defender_id=target_id,
                    base_damage=base_damage,
                    damage_type=damage_type,
                )
            return True

        if effect in {"healing", "heal"}:
            base_healing = float(script_result.get("base_healing", 100.0))
            for target_id in target_ids:
                self.healing_system.calculate_and_apply_healing(
                    healer_id=actor_id,
                    target_id=target_id,
                    base_healing=base_healing,
                )
            return True

        return False

    def _check_victory_condition(self) -> bool:
        """检查战斗是否应该结束。

        Returns:
            战斗是否已结束
        """
        if not self._team_ids or not self._enemy_ids:
            return False

        alive_team = sum(
            1
            for entity_id in self._team_ids
            if esper.entity_exists(entity_id)
            and (
                status := esper.try_component(
                    entity_id, CharacterStatusComponent
                )
            )
            and status.status == CharacterStatus.ALIVE
        )
        alive_enemy = sum(
            1
            for entity_id in self._enemy_ids
            if esper.entity_exists(entity_id)
            and (
                status := esper.try_component(
                    entity_id, CharacterStatusComponent
                )
            )
            and status.status == CharacterStatus.ALIVE
        )

        # 任意一方全灭，战斗结束
        return alive_team == 0 or alive_enemy == 0

    def get_current_actor(self) -> Optional[int]:
        """获取当前行动者 ID。"""
        return self.turn_system.get_current_actor()

    def save_snapshot(self) -> dict:
        """生成战斗快照（MVP 版本：仅返回占位符）。"""
        return {
            "state": self.state.value,
            "turn": self.current_turn,
            "tick": self.current_tick,
        }

    def restore_from_snapshot(self, snapshot: dict):
        """从快照恢复战斗状态（MVP 版本：仅占位符）。"""
        pass

    def cleanup(self):
        """清理战斗资源。"""
        self.world.deactivate()
        # 必须先切换到其他世界，再删除当前世界
        try:
            esper.switch_world("default")
        except (KeyError, ValueError):
            pass

        try:
            esper.delete_world(self.world.world_name)
        except (PermissionError, KeyError, ValueError):
            # 如果已删除、无法删除或不存在，忽略错误
            pass
