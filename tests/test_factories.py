from types import SimpleNamespace

from hsr_sim.ecs import factories
from hsr_sim.ecs.components import CharacterIdentityComponent
from hsr_sim.ecs.components import SpecialEnergyComponent
from hsr_sim.ecs.components import StandardEnergyComponent


def test_create_character_from_config_mounts_standard_energy(monkeypatch):
    char_config = SimpleNamespace(
        id=1001,
        name="seele",
        base_hp=1000.0,
        base_atk=500.0,
        base_def=500.0,
        base_spd=100.0,
        energy=SimpleNamespace(energy_type="standard", max_energy=120),
    )

    monkeypatch.setattr(
        factories.config_loader,
        "get_character",
        lambda name, version: {"config": char_config},
    )

    calls = []
    monkeypatch.setattr(factories.esper, "create_entity", lambda: 1)
    monkeypatch.setattr(
        factories.esper,
        "add_component",
        lambda entity, component: calls.append(component),
    )

    entity = factories.create_character_from_config("seele", "v1.0")

    assert entity == 1
    assert any(isinstance(c, StandardEnergyComponent) for c in calls)
    assert not any(isinstance(c, SpecialEnergyComponent) for c in calls)
    assert any(isinstance(c, CharacterIdentityComponent) for c in calls)


def test_create_character_from_config_mounts_special_energy(monkeypatch):
    char_config = SimpleNamespace(
        id=2001,
        name="aglaea",
        base_hp=1200.0,
        base_atk=600.0,
        base_def=550.0,
        base_spd=102.0,
        energy=SimpleNamespace(energy_type="special_flux", max_energy=8),
    )

    monkeypatch.setattr(
        factories.config_loader,
        "get_character",
        lambda name, version: {"config": char_config},
    )

    calls = []
    monkeypatch.setattr(factories.esper, "create_entity", lambda: 2)
    monkeypatch.setattr(
        factories.esper,
        "add_component",
        lambda entity, component: calls.append(component),
    )

    entity = factories.create_character_from_config("aglaea", "v1.0")

    assert entity == 2
    assert any(isinstance(c, SpecialEnergyComponent) for c in calls)
    assert not any(isinstance(c, StandardEnergyComponent) for c in calls)
