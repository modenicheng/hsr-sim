import json

import pytest

from hsr_sim.models.schemas.enums import RelicSlot, StatType
from hsr_sim.models.schemas.passive import PassiveSkillConfig
from hsr_sim.models.schemas.relics import RelicConfig


@pytest.fixture()
def normal_relic_config() -> RelicConfig:
    return RelicConfig(
        id=1001,
        name="Amphoreus, The Eternal Land",
        relic_set_id=2001,
        slot=RelicSlot.LINK_ROPE,
        rarity=5,
        story="A relic from Amphoreus.",
        main_stat={StatType.HP_PERCENT: 0.432},
        sub_stats={
            StatType.DEF: 21,
            StatType.CRIT_DAMAGE: 0.246,
            StatType.EFFECT_HIT_RATE: 0.077,
            StatType.EFFECT_RES: 0.073,
        },
        passive_2_pc=PassiveSkillConfig(
            id=3001,
            name="Set Bonus",
            description="Example 2-piece passive.",
            script="return { crit_rate = 0.08 }",
        ),
    )


def test_relic_config_model_dump_json_roundtrip(normal_relic_config: RelicConfig):
    dumped = normal_relic_config.model_dump(mode="json")

    assert dumped == {
        "id": 1001,
        "name": "Amphoreus, The Eternal Land",
        "relic_set_id": 2001,
        "slot": "link_rope",
        "rarity": 5,
        "story": "A relic from Amphoreus.",
        "main_stat": {"hp_percent": 0.432},
        "sub_stats": {
            "def": 21,
            "crit_damage": 0.246,
            "effect_hit_rate": 0.077,
            "effect_res": 0.073,
        },
        "passive_2_pc": {
            "id": 3001,
            "name": "Set Bonus",
            "description": "Example 2-piece passive.",
            "script": "return { crit_rate = 0.08 }",
        },
        "passive_4_pc": None,
    }

    reloaded = RelicConfig.model_validate_json(json.dumps(dumped))
    assert reloaded == normal_relic_config


@pytest.mark.parametrize(
    ("slot", "main_stat"),
    [
        (RelicSlot.HEAD, {StatType.HP_PERCENT: 0.432}),
        (RelicSlot.LINK_ROPE, {StatType.ATK: 56.448}),
    ],
)
def test_relic_config_rejects_invalid_main_stat_for_slot(slot, main_stat):
    with pytest.raises(ValueError, match="Invalid main_stat"):
        RelicConfig(
            id=1,
            name="Bad relic",
            relic_set_id=1,
            slot=slot,
            rarity=5,
            story="bad",
            main_stat=main_stat,
        )


@pytest.mark.parametrize(
    "main_stat",
    [
        {StatType.HP_PERCENT: 0.05},
        {StatType.HP_PERCENT: 0.5},
    ],
)
def test_relic_config_rejects_main_stat_out_of_range(main_stat):
    with pytest.raises(ValueError, match="(exceeds max value|is less than min value)"):
        RelicConfig(
            id=2,
            name="Bad relic",
            relic_set_id=1,
            slot=RelicSlot.LINK_ROPE,
            rarity=5,
            story="bad",
            main_stat=main_stat,
        )


def test_relic_config_rejects_too_many_sub_stats_for_two_star():
    with pytest.raises(ValueError, match="2-star relics can have at most 2 sub-stats"):
        RelicConfig(
            id=3,
            name="Bad relic",
            relic_set_id=1,
            slot=RelicSlot.HEAD,
            rarity=2,
            story="bad",
            main_stat={StatType.HP: 45.1584},
            sub_stats={
                StatType.ATK: 6.774,
                StatType.DEF: 6.774,
                StatType.CRIT_RATE: 0.010368,
            },
        )


def test_relic_config_rejects_duplicate_main_stat_in_sub_stats():
    with pytest.raises(ValueError, match="Sub-stats cannot duplicate the main stat"):
        RelicConfig(
            id=4,
            name="Bad relic",
            relic_set_id=1,
            slot=RelicSlot.LINK_ROPE,
            rarity=5,
            story="bad",
            main_stat={StatType.HP_PERCENT: 0.432},
            sub_stats={
                StatType.HP_PERCENT: 0.03456,
                StatType.CRIT_RATE: 0.02592,
            },
        )
