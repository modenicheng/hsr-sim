import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest

from hsr_sim.models.schemas.enums import StatType
from hsr_sim.models.schemas.relics import MAIN_STAT_GROWTH_MAP, SUBSIDARY_STATS


class _DummySessionContext:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def stat_calculator_module(monkeypatch):
    fake_repo_module = ModuleType("src.hsr_sim.repositories.relic_repo")

    class _PlaceholderRelicRepository:
        def __init__(self, _db):
            pass

        def get(self, _relic_id):
            return None

    fake_repo_module.RelicRepository = _PlaceholderRelicRepository

    fake_utils_module = ModuleType("hsr_sim.utils")
    fake_utils_module.SessionLocal = lambda: _DummySessionContext()

    monkeypatch.setitem(
        sys.modules, "src.hsr_sim.repositories.relic_repo", fake_repo_module
    )
    monkeypatch.setitem(sys.modules, "hsr_sim.utils", fake_utils_module)

    sys.modules.pop("hsr_sim.services.stat_calculator", None)
    return importlib.import_module("hsr_sim.services.stat_calculator")


def _patch_relic_dependencies(monkeypatch, module, relic_map):
    monkeypatch.setattr(module, "SessionLocal", lambda: _DummySessionContext())

    class _FakeRelicRepository:
        def __init__(self, _db):
            self._relic_map = relic_map

        def get(self, relic_id):
            return self._relic_map.get(relic_id)

    monkeypatch.setattr(module, "RelicRepository", _FakeRelicRepository)


def test_calculate_relic_stats_accumulates_main_and_sub_stats(
    monkeypatch, stat_calculator_module
):
    relics = {
        1: SimpleNamespace(
            main_stat_type=StatType.ATK_PERCENT.value,
            rarity=5,
            level=12,
            sub_stats=[
                {"type": StatType.CRIT_RATE.value, "roll": 2},
                {"type": StatType.SPEED.value, "roll": 0},
            ],
        ),
        2: SimpleNamespace(
            main_stat_type=StatType.HP.value,
            rarity=4,
            level=6,
            sub_stats=[
                {"type": StatType.CRIT_RATE.value, "roll": 1},
                {"type": StatType.HP_PERCENT.value, "roll": 2},
            ],
        ),
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    result = stat_calculator_module.calculate_relic_stats([1, 2])

    main_atk_percent = (
        MAIN_STAT_GROWTH_MAP[StatType.ATK_PERCENT][5].base_value
        + MAIN_STAT_GROWTH_MAP[StatType.ATK_PERCENT][5].growth_per_level * 12
    )
    main_hp = (
        MAIN_STAT_GROWTH_MAP[StatType.HP][4].base_value
        + MAIN_STAT_GROWTH_MAP[StatType.HP][4].growth_per_level * 6
    )
    crit_rate_total = (
        SUBSIDARY_STATS[5][StatType.CRIT_RATE][2]
        + SUBSIDARY_STATS[4][StatType.CRIT_RATE][1]
    )

    assert result[StatType.ATK_PERCENT] == pytest.approx(main_atk_percent)
    assert result[StatType.HP] == pytest.approx(main_hp)
    assert result[StatType.CRIT_RATE] == pytest.approx(crit_rate_total)
    assert result[StatType.SPEED] == pytest.approx(
        SUBSIDARY_STATS[5][StatType.SPEED][0]
    )
    assert result[StatType.HP_PERCENT] == pytest.approx(
        SUBSIDARY_STATS[4][StatType.HP_PERCENT][2]
    )


def test_calculate_relic_stats_supports_fixed_and_percent_sub_stats(
    monkeypatch, stat_calculator_module
):
    relics = {
        10: SimpleNamespace(
            main_stat_type=StatType.DEF_PERCENT.value,
            rarity=5,
            level=3,
            sub_stats=[
                {"type": StatType.DEF.value, "roll": 0},
                {"type": StatType.DEF_PERCENT.value, "roll": 1},
                {"type": StatType.ATK.value, "roll": 2},
            ],
        )
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    result = stat_calculator_module.calculate_relic_stats([10])

    expected_main_def_percent = (
        MAIN_STAT_GROWTH_MAP[StatType.DEF_PERCENT][5].base_value
        + MAIN_STAT_GROWTH_MAP[StatType.DEF_PERCENT][5].growth_per_level * 3
    )

    assert result[StatType.DEF_PERCENT] == pytest.approx(
        expected_main_def_percent + SUBSIDARY_STATS[5][StatType.DEF_PERCENT][1]
    )
    assert result[StatType.DEF] == pytest.approx(
        SUBSIDARY_STATS[5][StatType.DEF][0]
    )
    assert result[StatType.ATK] == pytest.approx(
        SUBSIDARY_STATS[5][StatType.ATK][2]
    )


def test_calculate_relic_stats_skips_missing_relic_and_logs_warning(
    monkeypatch, caplog, stat_calculator_module
):
    relics = {
        7: SimpleNamespace(
            main_stat_type=StatType.SPEED.value,
            rarity=3,
            level=5,
            sub_stats=[],
        )
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    with caplog.at_level("WARNING", logger=stat_calculator_module.logger.name):
        result = stat_calculator_module.calculate_relic_stats([404, 7])

    expected_speed = (
        MAIN_STAT_GROWTH_MAP[StatType.SPEED][3].base_value
        + MAIN_STAT_GROWTH_MAP[StatType.SPEED][3].growth_per_level * 5
    )
    assert result[StatType.SPEED] == pytest.approx(expected_speed)
    assert "Relic with id 404 not found in database." in caplog.text


@pytest.mark.parametrize(
    "rarity,level",
    [
        (2, 0),
        (2, 9),
        (3, 5),
        (3, 15),
        (4, 10),
        (4, 20),
        (5, 0),
        (5, 15),
    ],
)
def test_calculate_relic_stats_main_stat_across_rarities(
    monkeypatch, stat_calculator_module, rarity, level
):
    relics = {
        100: SimpleNamespace(
            main_stat_type=StatType.HP.value,
            rarity=rarity,
            level=level,
            sub_stats=[],
        )
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    result = stat_calculator_module.calculate_relic_stats([100])

    expected_hp = (
        MAIN_STAT_GROWTH_MAP[StatType.HP][rarity].base_value
        + MAIN_STAT_GROWTH_MAP[StatType.HP][rarity].growth_per_level * level
    )

    assert result[StatType.HP] == pytest.approx(expected_hp)
    assert len(result) == 1


@pytest.mark.parametrize(
    "roll_combo",
    [
        ((0, 1, 2), "high_roll_on_crit"),
        ((0, 0, 0), "all_low_rolls"),
        ((2, 2, 2), "all_high_rolls"),
        ((1, 1), "all_med_rolls"),
    ],
)
def test_calculate_relic_stats_sub_stat_rolls(
    monkeypatch, stat_calculator_module, roll_combo
):
    rolls, _ = roll_combo
    rarity = 5
    sub_stats = [
        {"type": StatType.CRIT_RATE.value, "roll": rolls[0]},
        {"type": StatType.CRIT_DAMAGE.value, "roll": rolls[1]},
    ]
    if len(rolls) > 2:
        sub_stats.append({"type": StatType.SPEED.value, "roll": rolls[2]})

    relics = {
        200: SimpleNamespace(
            main_stat_type=StatType.ATK_PERCENT.value,
            rarity=rarity,
            level=0,
            sub_stats=sub_stats,
        )
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    result = stat_calculator_module.calculate_relic_stats([200])

    expected_crit_rate = SUBSIDARY_STATS[rarity][StatType.CRIT_RATE][rolls[0]]
    expected_crit_dmg = SUBSIDARY_STATS[rarity][StatType.CRIT_DAMAGE][rolls[1]]

    assert result[StatType.CRIT_RATE] == pytest.approx(expected_crit_rate)
    assert result[StatType.CRIT_DAMAGE] == pytest.approx(expected_crit_dmg)
    if len(rolls) > 2:
        expected_speed = SUBSIDARY_STATS[rarity][StatType.SPEED][rolls[2]]
        assert result[StatType.SPEED] == pytest.approx(expected_speed)


@pytest.mark.parametrize(
    "main_stat_type",
    [
        StatType.HP,
        StatType.ATK,
        StatType.HP_PERCENT,
        StatType.ATK_PERCENT,
        StatType.DEF_PERCENT,
        StatType.SPEED,
        StatType.CRIT_RATE,
        StatType.CRIT_DAMAGE,
    ],
)
def test_calculate_relic_stats_various_main_stats(
    monkeypatch, stat_calculator_module, main_stat_type
):
    relics = {
        300: SimpleNamespace(
            main_stat_type=main_stat_type.value,
            rarity=5,
            level=6,
            sub_stats=[],
        )
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    result = stat_calculator_module.calculate_relic_stats([300])

    expected_value = (
        MAIN_STAT_GROWTH_MAP[main_stat_type][5].base_value
        + MAIN_STAT_GROWTH_MAP[main_stat_type][5].growth_per_level * 6
    )

    assert main_stat_type in result
    assert result[main_stat_type] == pytest.approx(expected_value)


@pytest.mark.parametrize(
    "rarity,num_sub_stats",
    [
        (5, 4),
        (4, 4),
        (3, 3),
        (2, 2),
    ],
)
def test_calculate_relic_stats_multiple_relics_different_rarities(
    monkeypatch, stat_calculator_module, rarity, num_sub_stats
):
    sub_stats = []
    for i in range(num_sub_stats):
        roll = min(i % 3, 2)
        stat_types = [
            StatType.HP,
            StatType.ATK,
            StatType.SPEED,
            StatType.CRIT_RATE,
        ]
        sub_stats.append({"type": stat_types[i].value, "roll": roll})

    relics = {
        400: SimpleNamespace(
            main_stat_type=StatType.HP_PERCENT.value,
            rarity=rarity,
            level=12,
            sub_stats=sub_stats,
        )
    }
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, relics)

    result = stat_calculator_module.calculate_relic_stats([400])

    expected_main = (
        MAIN_STAT_GROWTH_MAP[StatType.HP_PERCENT][rarity].base_value
        + MAIN_STAT_GROWTH_MAP[StatType.HP_PERCENT][rarity].growth_per_level
        * 12
    )

    assert result[StatType.HP_PERCENT] == pytest.approx(expected_main)
    assert len(result) == num_sub_stats + 1


def test_calculate_relic_stats_empty_list_returns_empty_dict(
    monkeypatch, stat_calculator_module
):
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, {})

    result = stat_calculator_module.calculate_relic_stats([])

    assert result == {}


def test_calculate_relic_stats_all_missing_ids_returns_empty(
    monkeypatch, caplog, stat_calculator_module
):
    _patch_relic_dependencies(monkeypatch, stat_calculator_module, {})

    with caplog.at_level("WARNING", logger=stat_calculator_module.logger.name):
        result = stat_calculator_module.calculate_relic_stats([999, 888, 777])

    assert result == {}
    assert caplog.text.count("not found in database") == 3
