from hsr_sim.hooks import HookPoint, HookRegistry, HookResult


def test_hook_result_is_pydantic_model():
    result = HookResult(stop=True, value=123)

    assert result.stop is True
    assert result.value == 123


def test_hook_chain_orders_by_priority_and_can_stop():
    registry = HookRegistry()
    calls: list[str] = []

    def low_priority(value, *_args, **_kwargs):
        calls.append(f"low:{value}")
        return value + 1

    def high_priority(value, *_args, **_kwargs):
        calls.append(f"high:{value}")
        return HookResult(stop=True, value=value * 2)

    registry.register(
        HookPoint.BEFORE_DAMAGE_CALCULATION, low_priority, priority=10
    )
    registry.register(
        HookPoint.BEFORE_DAMAGE_CALCULATION, high_priority, priority=100
    )

    result = registry.trigger(HookPoint.BEFORE_DAMAGE_CALCULATION, 5)

    assert calls == ["high:5"]
    assert result.stop is True
    assert result.value == 10


def test_hook_registry_unregister_owner():
    registry = HookRegistry()
    calls: list[int] = []

    def handler(value, *_args, **_kwargs):
        calls.append(value)
        return value + 1

    registry.register(HookPoint.ON_TURN_START, handler, owner="buff_a")
    registry.register(HookPoint.ON_TURN_START, handler, owner="buff_b")

    removed = registry.unregister_owner("buff_a")
    result = registry.trigger(HookPoint.ON_TURN_START, 1)

    assert removed == 1
    assert calls == [1]
    assert result.value == 2
