"""Tests for BattleController snapshot shaping for TUI."""

import esper

from hsr_sim.ecs.components import CharacterStatusComponent
from hsr_sim.models.character_status import CharacterStatus
from hsr_sim.ui.battle_controller import BattleController


def test_snapshot_removes_knocked_down_enemies() -> None:
    """Snapshot should only include alive enemies for UI rendering."""
    controller = BattleController(version="v1.0")
    try:
        initial = controller.start_battle(seed=7)
        assert len(initial.enemies) == 2
        assert len(initial.enemy_targets) == 2

        dead_enemy_id = controller.enemy_ids[0]
        alive_enemy_id = controller.enemy_ids[1]

        status = esper.try_component(dead_enemy_id, CharacterStatusComponent)
        assert status is not None
        status.status = CharacterStatus.KNOCKED_DOWN

        snapshot = controller._take_snapshot(needs_input=True)

        assert len(snapshot.enemies) == 1
        assert len(snapshot.enemy_targets) == 1
        assert snapshot.enemy_targets[0].entity_id == alive_enemy_id
        assert snapshot.enemy_targets[0].is_alive is True
    finally:
        controller.cleanup()
