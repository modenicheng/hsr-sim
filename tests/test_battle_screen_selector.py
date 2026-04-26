"""Tests for enemy target selector behavior in BattleScreen."""

from hsr_sim.ui.battle_controller import BattleSnapshot
from hsr_sim.ui.screens.battle import BattleScreen
from hsr_sim.ui.widgets.selector_rules import SingleTargetRule, TargetInfo


def test_enable_target_selection_removes_dead_targets(monkeypatch):
    """Should only keep alive enemies in selector targets."""
    screen = BattleScreen()
    captured: dict = {}

    def _capture_setup_target_selector(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(screen, "setup_target_selector", _capture_setup_target_selector)

    snapshot = BattleSnapshot(
        enemy_targets=[
            TargetInfo(entity_id=101, label="Enemy #1", is_enemy=True, is_alive=False),
            TargetInfo(entity_id=202, label="Enemy #2", is_enemy=True, is_alive=True),
        ]
    )

    screen._enable_target_selection(snapshot)

    assert [t.entity_id for t in captured["targets"]] == [202]
    assert captured["primary_id"] == 202
    assert isinstance(captured["rule"], SingleTargetRule)


def test_enable_target_selection_with_no_enemy_targets_does_nothing(monkeypatch):
    """Should not call selector setup when no enemy targets are present."""
    screen = BattleScreen()
    called = False

    def _capture_setup_target_selector(**kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(screen, "setup_target_selector", _capture_setup_target_selector)

    screen._enable_target_selection(BattleSnapshot(enemy_targets=[]))

    assert called is False


def test_enable_target_selection_with_all_dead_targets_does_nothing(
    monkeypatch,
):
    """Should not set selector when all enemy targets are dead."""
    screen = BattleScreen()
    called = False

    def _capture_setup_target_selector(**kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(screen, "setup_target_selector", _capture_setup_target_selector)

    snapshot = BattleSnapshot(
        enemy_targets=[
            TargetInfo(
                entity_id=101,
                label="Enemy #1",
                is_enemy=True,
                is_alive=False,
            ),
        ]
    )
    screen._enable_target_selection(snapshot)

    assert called is False
