import json

import pytest
from pydantic import ValidationError

from hsr_sim.models.schemas.enums import RelicSlot
from hsr_sim.models.schemas.passive import PassiveSkillConfig
from hsr_sim.models.schemas.relics import RelicConfig, RelicSetConfig


@pytest.fixture()
def normal_relic_set_config() -> RelicSetConfig:
    return RelicSetConfig(
        id=2001,
        name="Amphoreus, The Eternal Land",
        passive_2_pc=PassiveSkillConfig(
            id=3001,
            name="Set Bonus",
            description="Example 2-piece passive.",
            script="return { crit_rate = 0.08 }",
        ),
    )


@pytest.fixture()
def normal_relic_config(normal_relic_set_config: RelicSetConfig) -> RelicConfig:
    return RelicConfig(
        id=1001,
        name="Amphoreus, The Eternal Land - Link Rope",
        relic_set=normal_relic_set_config,
        slot=RelicSlot.LINK_ROPE,
        story="A relic from Amphoreus.",
    )


def test_relic_config_model_dump_json_roundtrip(
    normal_relic_config: RelicConfig,
):
    dumped = normal_relic_config.model_dump(mode="json")

    assert dumped == {
        "id": 1001,
        "name": "Amphoreus, The Eternal Land - Link Rope",
        "relic_set": {
            "id": 2001,
            "name": "Amphoreus, The Eternal Land",
            "passive_2_pc": {
                "id": 3001,
                "name": "Set Bonus",
                "description": "Example 2-piece passive.",
                "script": "return { crit_rate = 0.08 }",
            },
            "passive_4_pc": None,
        },
        "slot": "link_rope",
        "story": "A relic from Amphoreus.",
    }

    reloaded = RelicConfig.model_validate_json(json.dumps(dumped))
    assert reloaded == normal_relic_config


def test_relic_config_requires_relic_set():
    with pytest.raises(ValidationError, match="Field required"):
        RelicConfig.model_validate(
            {
                "id": 1,
                "name": "Bad relic",
                "slot": RelicSlot.HEAD,
                "story": "bad",
            }
        )
