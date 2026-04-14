from pydantic import ValidationError

from hsr_sim.ecs.components.buffs import ActiveBuffComponent, BuffContainerComponent


def test_active_buff_component_only_runtime_fields():
    buff = ActiveBuffComponent(
        buff_id=50000001,
        stacks=2,
        remaining_duration=1.5,
        source_entity_id=1001,
        runtime_values={"triggered_times": 3},
    )

    assert buff.buff_id == 50000001
    assert buff.stacks == 2
    assert buff.remaining_duration == 1.5
    assert buff.runtime_values["triggered_times"] == 3


def test_buff_container_holds_runtime_instances():
    container = BuffContainerComponent(
        buffs=[
            ActiveBuffComponent(buff_id=1, stacks=1),
            ActiveBuffComponent(buff_id=2, stacks=3, remaining_duration=2),
        ]
    )
    assert len(container.buffs) == 2
    assert container.buffs[1].stacks == 3


def test_active_buff_component_rejects_invalid_runtime_values():
    try:
        ActiveBuffComponent(buff_id=10, stacks=-1)
    except ValidationError as exc:
        assert "stacks" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for negative stacks")

    try:
        ActiveBuffComponent(buff_id=10, remaining_duration=-1)
    except ValidationError as exc:
        assert "remaining_duration" in str(exc)
    else:
        raise AssertionError("Expected ValidationError for negative duration")
