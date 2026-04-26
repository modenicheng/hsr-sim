# AGENTS.md — hsr-sim

## Quick start

```sh
uv sync                    # install deps
uv run -m hsr_sim          # run the app (src layout — use -m, not a script entrypoint)
uv run pytest              # all tests
uv run pytest tests/test_xxx.py        # single test file
uv run pytest tests/test_xxx.py::test_yyy  # single test
```

## Code quality

```sh
prek run --all-files       # run all pre-commit hooks (ruff check + format, etc.)
```

Note: `prek` is **not** in `uv sync`. Install separately: `uv tool install prek` or `winget install --id j178.Prek`.
`prek install -f --prepare-hooks` to set up git hooks.

Ruff config (pyproject.toml): line-length 80, target py313, rules E/W/F/D (pydocstyle google convention).
Ignores: E501, W191, D100–D105, D107, D415.

Hooks enforce conventional commits (feat, fix, chore, etc.) and block commits to `main`/`master`.

## Architecture summary

- **ECS** (esper): core simulation engine. `ECSWorld` wraps an esper world + event bus + hook registry. ECS systems in `src/hsr_sim/ecs/systems/`. Components in `ecs/components/`. esper uses global named worlds; `ECSWorld.activate()` calls `esper.switch_world()`.
- **Events** (eventure): `GameEventBus` wraps `eventure.EventBus` + `EventLog`. Publishes typed game events (`damage_dealt`, `character_knocked_down`, `turn_started`, etc.). Handlers subscribe with priority; fanout per event type.
- **Hooks** (`HookRegistry` / `HookChain`): priority-ordered callbacks that receive and return a value through the chain. Hooks can **modify** values and **short-circuit** (stop). Used mid-calculation (e.g. `BEFORE_CRIT_DETERMINATION`, `BEFORE_DAMAGE_CALCULATION`).
- **Config loader** (`src/hsr_sim/services/config_loader.py`): version-aware, caches all configs at startup. Character-specific buffs override global buffs on ID conflict.
- **Database**: SQLite (`data/hsr.db`) via SQLAlchemy + Alembic. `src/hsr_sim/models/db/` contains ORM models. `src/hsr_sim/repositories/base.py` provides generic CRUD.
- **UI**: textual TUI in `src/hsr_sim/ui/`. Entry point: `HSRSimApp` in `ui/app.py`.
- **Skill scripts**: Python modules loaded dynamically. Each skill is a class inheriting `BaseSkill`/`BaseDamageSkill` with `execute`. Filename snake_case → class name CamelCase (e.g. `seele_basic_atk` → `SeeleBasicAtk`, `seele_eidolon_1` → `SeeleEidolon1`).

### Hook vs Event — when to use which

| Mechanism | Use when | Signature |
|-----------|----------|-----------|
| **Hook** (`HookRegistry` / `context.trigger_hook`) | You need to **modify a value** mid-calculation or **stop** further processing | `callback(current_value, **kwargs) → HookResult \| new_value \| None` |
| **Event** (`GameEventBus` / `context.publish_event`) | You need to **broadcast that something happened**; fire-and-forget | `handler(event: Event)` with `event.data` dict |

Critical: hooks return the value through the chain (registered via `context.hook_chain`), events do not return values (subscribed via `context.event_bus`). Events carry data in `event.data` as a dict.

## Directory map

| Dir | Purpose |
|-----|---------|
| `src/hsr_sim/ecs/` | Entity-Component-System (esper-based): components, systems, world, factories |
| `src/hsr_sim/battle/` | Battle session orchestration |
| `src/hsr_sim/skills/` | Skill base classes (`BaseSkill`, `BaseDamageSkill`, `SkillContext`), script loader, types |
| `src/hsr_sim/hooks/` | Hook system (registry, chain, protocol, points) |
| `src/hsr_sim/events/` | Event bus wrapper, types (`EventType`), models (`GameEvent`) |
| `src/hsr_sim/models/schemas/` | Pydantic config schemas (character, relic, buff, light_cone, enemy, etc.) |
| `src/hsr_sim/models/db/` | SQLAlchemy ORM models |
| `src/hsr_sim/models/` | Battle state and character status enums/models |
| `src/hsr_sim/repositories/` | Data access layer (generic BaseRepository + specific repos) |
| `src/hsr_sim/services/` | Business logic (config_loader, stat_calculator, relic_generator, etc.) |
| `src/hsr_sim/utils/` | Utilities (db_session, id_generator, import_utils) |
| `src/hsr_sim/core/` | Core config (PROJECT_ROOT, CONFIGS_DIR, exceptions) |
| `src/hsr_sim/logger/` | Rich-based logging |
| `configs/v1.0/` | Versioned game data: characters, relics, light_cones, buffs, enemies |
| `scripts/` | Scaffolding + migration + validation scripts |
| `tests/` | pytest test suite |
| `alembic/` | Database migrations |
| `docs/` | Design docs (`design.md`, `event系统用法.md`, `速度系统.md`, etc.) |

## Import conventions

Use `from hsr_sim.xxx` — the dominant pattern (works because `uv` installs the `src`-layout package).
Some older ECS system files use `from src.hsr_sim.xxx`. Both work, but prefer `hsr_sim.xxx`.

## Skill programming model

### Skill lifecycle

- **`activate()`** — called on load for passives (talents, eidolons, bonus abilities). Register hooks/event handlers here. Return the handle to enable cleanup in `deactivate()`.
- **`execute(caster, targets)`** — called when the skill is used in battle. Active skills only.
- **`deactivate()`** — called on bundle removal. Use saved handles to unregister hooks/events.

### SkillContext (available as `self.context`)

- `context.trigger_hook(hook_point, initial_value, **kwargs)` — run hook chain, return modified value
- `context.publish_event(event_type, **kwargs)` — broadcast event (auto-attaches `caster_id`, `target_ids`)
- `context.get_component(entity_id, ComponentClass)` — shortcut for `esper.try_component`
- `context.event_bus` — for direct subscription (`self.context.event_bus.subscribe(...)`)
- `context.hook_chain` — for direct hook registration (`self.context.hook_chain.register(...)`)
- `context.caster` / `context.targets` — set before `execute()` is called

### Running damage from a script

Two paths, don't mix them:
1. **Inherit `BaseDamageSkill`** — call `super().execute(caster, targets)`. It publishes `damage_dealt` events → picked up by `HealthSystem`.
2. **Call `DamageSystem.calculate_and_apply_damage()`** directly — does full formula + crit + hooks + publishes result. Preferred for complex effects.

### Entity identity pattern

Never hardcode `entity_id`. Use `CharacterIdentityComponent.config_id` to identify a character:

```python
identity = esper.try_component(entity_id, CharacterIdentityComponent)
if identity and identity.config_id == 10000000:  # Seele
    ...
```

### Static utility methods for scripts

- `EnergySystem.recover_energy(entity_id, amount)` — static, safe to call from any script
- `esper.try_component(entity_id, ComponentClass)` — read a component
- `esper.add_component(entity_id, component)` / `esper.remove_component(entity_id, ComponentClass)` — add/remove

## Component quick reference

| Component | Key fields | Notes |
|-----------|-----------|-------|
| `SpeedComponent` | `base_speed`, `speed_bonus`, `speed_fix` | `final_speed = base_speed * (1 + speed_bonus) + speed_fix`; `action_value = 10000 / final_speed` |
| `CritRateComponent` | `value` (0–1) | Default 0.05 if absent |
| `CritDamageComponent` | `value` (float multiplier) | Default 0.50 if absent; crit damage = `base * (1 + value)` |
| `HealthComponent` | `value`, `max_value` | `value <= 0` triggers `CHARACTER_KNOCKED_DOWN` |
| `StandardEnergyComponent` | `energy`, `max_energy` | Clamped to [0, max_energy] |
| `CharacterIdentityComponent` | `config_id`, `config_name`, `version` | Use `config_id` to identify character type |
| `CharacterStatusComponent` | `status` (`ALIVE`/`KNOCKED_DOWN`) | Check before applying effects to a defeated entity |
| `StackComponent` | `stack_type` (str), `current`, `max` | For custom buff stacks (e.g. Seele SPD boost uses `stack_type="seele_spd_boost"`) |
| `AttackComponent` | `value` | Flat ATK stat |
| `DefenseComponent` | `value` | Flat DEF stat |

## Eidolon conventions

- Eidolon scripts live in `configs/<v>/characters/<name>/eidolons/`.
- Script naming: `{char_name}_eidolon_{n}.py` → class `{CharName}Eidolon{N}`.
- E3/E5 (talent level boosts) are typically stubs — their effects depend on skill level → multiplier mappings.
- Passive skills (talents, eidolons, bonus abilities) load conditionally: eidolons filter by `eidolon.index <= character.eidolon_level`.

## Config loading and versioning

- `ConfigLoader` scans `configs/` for version dirs matching `vX.Y` and loads everything on init.
- `config_loader.get_character(name, version)` returns a dict with `"config": CharacterConfig`.
- `config_loader.get_character_by_id(id, version)` looks up by numeric ID.
- When version is omitted, the latest version is used.
- Character buffs in `configs/<v>/characters/<name>/buffs/` take priority over global buffs in `configs/<v>/buffs/`.

## ID conventions

Character: `10xx xxxx`, Relic sets: `20xx xxxx`, Light Cones: `30xx xxxx`, Enemies: `40xx xxxx`, Global Buffs: `50xx xxxx`, Character Buffs: `51xx xxxx`.

Sub-ranges: basic atk `11xx`, skill `12xx`, ultimate `13xx`, eidolon `14xx`, talent `15xx`, technique `16xx`, bonus ability `17xx`. Relic piece `21xx`, 2pc set `22xx`, 4pc set `23xx`. Light cone passive `31xx`. Enemy skill `41xx`, enemy passive `42xx`.

## Database notes

- Tables use `__tablename__` naming (plural), e.g. `user_characters`, `user_relics`, `user_light_cones`.
- `JSONText` type decorator handles JSON serialization via `orjson`.
- `UserCharacter.equipped_light_cone_id` has a UNIQUE constraint (one-to-one).
- Alembic uses `render_as_batch=True` and `sqlite:///./data/hsr.db`.
- Tests that need a fresh DB should use `:memory:` or temporary files — check `test_db_session.py` for patterns.

## Skill script conventions

- Configs reference scripts by path (e.g. `skills/seele_basic`). The loader resolves this to `configs.<version_token>.characters.<char_name>.skills.<script_name>`.
- The Python file must contain a class whose name is the CamelCase of the filename's final component.
- The class must inherit `BaseSkill` (or the `expected_base_class`) and implement `execute`.
- Validated by `scripts/validate_configs.py`.
- Check `docs/event系统用法.md` and `docs/design.md` before adding game mechanics.

## Testing notes

- Common patterns: `mock_db` fixture (MagicMock), `monkeypatch` for patching module-level singletons like `config_loader`.
- Some integration tests write to real `configs/` on disk (e.g. `test_character_config_load.py`, `test_config_loader_integration.py`).
- `test_script_generators_loadable.py` runs the scaffolding scripts and verifies the generated skill scripts are importable.
