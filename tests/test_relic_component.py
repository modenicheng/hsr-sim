import pytest

from hsr_sim.ecs.components.relics import RelicComponent
from hsr_sim.models.schemas.enums import StatType, RelicSlot


class TestRelicComponent:
    def test_valid_relic_creation(self):
        comp = RelicComponent(
            set_id=1,
            slot=RelicSlot.HEAD,
            relic_set_id=1,
            level=15,
            rarity=5,
            main_stat={StatType.HP: 200.0},
            sub_stats=[],
        )
        assert comp.set_id == 1
        assert comp.level == 15

    def test_valid_relic_with_sub_stats(self):
        comp = RelicComponent(
            set_id=1,
            slot=RelicSlot.TORSO,
            relic_set_id=1,
            level=20,
            rarity=5,
            main_stat={StatType.CRIT_DAMAGE: 0.5},
            sub_stats=[
                {StatType.CRIT_RATE: 0.05},
                {StatType.ATK: 50.0},
            ],
        )
        assert len(comp.sub_stats) == 2

    def test_invalid_main_stat_not_dict(self):
        with pytest.raises(Exception):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=5,
                main_stat=StatType.HP,
                sub_stats=[],
            )

    def test_invalid_main_stat_multiple_keys(self):
        with pytest.raises(ValueError, match="main_stat must be a dict"):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=5,
                main_stat={StatType.HP: 200, StatType.ATK: 50},
                sub_stats=[],
            )

    def test_invalid_main_stat_for_slot(self):
        with pytest.raises(ValueError, match="Invalid main_stat"):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=5,
                main_stat={StatType.ATK: 100},
                sub_stats=[],
            )

    def test_invalid_main_stat_exceeds_max(self):
        with pytest.raises(ValueError, match="exceeds max value"):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=5,
                main_stat={StatType.HP: 10000},
                sub_stats=[],
            )

    def test_two_star_max_two_substats(self):
        with pytest.raises(
            ValueError, match="2-star relics can have at most 2 sub-stats"
        ):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=2,
                main_stat={StatType.HP: 50},
                sub_stats=[{}, {}, {}],
            )

    def test_five_star_max_four_substats(self):
        with pytest.raises(ValueError, match="can have at most 4 sub-stats"):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=5,
                main_stat={StatType.HP: 200},
                sub_stats=[{}, {}, {}, {}, {}],
            )

    def test_substat_duplicate_main_stat(self):
        with pytest.raises(
            ValueError, match="Sub-stats cannot duplicate the main stat"
        ):
            RelicComponent(
                set_id=1,
                slot=RelicSlot.HEAD,
                relic_set_id=1,
                level=0,
                rarity=5,
                main_stat={StatType.HP: 200},
                sub_stats=[{StatType.HP: 10}],
            )
