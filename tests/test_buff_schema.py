from pydantic import ValidationError

from hsr_sim.models.schemas.buff import BuffConfig, BuffScope


def test_buff_config_defaults_and_optional_fields():
    cfg = BuffConfig.model_validate(
        {
            "id": 50000001,
            "name": "speed_up",
        }
    )

    assert cfg.id == 50000001
    assert cfg.name == "speed_up"
    assert cfg.scope == BuffScope.GLOBAL
    assert cfg.max_stacks == 1
    assert cfg.default_duration is None
    assert cfg.dispelable is False
    assert cfg.params == {}


def test_buff_config_validates_stack_and_duration():
    try:
        BuffConfig.model_validate(
            {
                "id": 50000002,
                "name": "bad_buff",
                "max_stacks": 0,
            }
        )
    except ValidationError as exc:
        assert "max_stacks" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for max_stacks")

    try:
        BuffConfig.model_validate(
            {
                "id": 50000003,
                "name": "bad_buff_2",
                "default_duration": -1,
            }
        )
    except ValidationError as exc:
        assert "default_duration" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for default_duration")
