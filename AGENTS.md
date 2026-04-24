# AGENTS.md — hsr-sim

## Quick start

```sh
uv sync                    # install deps
uv run -m hsr_sim          # run the app (src layout — use -m, not a script entrypoint)
uv run pytest              # all 119 tests
uv run pytest tests/test_xxx.py        # single test file
uv run pytest tests/test_xxx.py::test_yyy  # single test
```

## Code quality

```sh
prek run --all-files       # run all pre-commit hooks (ruff check + format, trailing whitespace, etc.)
```

Ruff config: line-length 80, target py313, rules E/W/F/D (pydocstyle google convention).
Ignores: E501, W191, D100–D105, D107, D415.

Hooks enforce conventional commits (feat, fix, chore, etc.) and block commits to `main`/`master`.

## Architecture summary

- **ECS** (esper): core simulation engine. `ECSWorld` wraps an esper world + event bus + hook registry. ECS systems live in `src/hsr_sim/ecs/systems/`. Components in `ecs/components/`.
- **Events** (eventure): `GameEventBus` publishes typed game events (damage, turn, buff, energy, etc.). `HookRegistry` chains priority-ordered callbacks that can short-circuit calculations.
- **Config loader** (`src/hsr_sim/services/config_loader.py`): version-aware, caches all configs at startup. Character-specific buffs override global buffs on ID conflict.
- **Database**: SQLite (`data/hsr.db`) via SQLAlchemy + Alembic. `src/hsr_sim/models/db/` contains ORM models. `src/hsr_sim/repositories/base.py` provides generic CRUD.
- **UI**: textual TUI in `src/hsr_sim/ui/`. Entry point: `HSRSimApp` in `ui/app.py`.
- **Skill scripts**: Python modules loaded dynamically via `DynamicClassLoader`/`SkillScriptLoader`. Each skill is a class inheriting `BaseSkill` with an `execute` method. The class name is `snake_to_camel` of the module's final component.

## Directory map

| Dir | Purpose |
|-----|---------|
| `src/hsr_sim/ecs/` | Entity-Component-System (esper-based) |
| `src/hsr_sim/battle/` | Battle session orchestration |
| `src/hsr_sim/skills/` | Skill base classes and dynamic script loader |
| `src/hsr_sim/hooks/` | Hook system (registry, chain, protocol, points) |
| `src/hsr_sim/events/` | Event bus, types, and models |
| `src/hsr_sim/models/schemas/` | Pydantic config schemas (character, relic, buff, etc.) |
| `src/hsr_sim/models/db/` | SQLAlchemy ORM models |
| `src/hsr_sim/repositories/` | Data access layer (generic BaseRepository + specific repos) |
| `src/hsr_sim/services/` | Business logic (config_loader, stat_calculator, relic_generator, etc.) |
| `src/hsr_sim/utils/` | Utilities (db_session, id_generator, import_utils) |
| `src/hsr_sim/core/` | Core config (PROJECT_ROOT, CONFIGS_DIR, exceptions) |
| `src/hsr_sim/logger/` | Rich-based logging |
| `configs/v1.0/` | Versioned game data: characters, relics, light_cones, buffs, enemies |
| `scripts/` | Scaffolding + migration scripts |
| `tests/` | pytest test suite |
| `alembic/` | Database migrations |
| `docs/` | Design docs (`design.md`, event system usage, 角色配置版本化策略) |

## Import conventions

Use `from hsr_sim.xxx` — this is the dominant pattern (used in tests, repositories, services, hooks, events, the UI layer) and works because `uv` installs the `src`-layout package.

Some older ECS system files use `from src.hsr_sim.xxx`. Both work, but prefer `hsr_sim.xxx` for consistency.

## Config loading and versioning

- `ConfigLoader` scans `configs/` for version dirs matching `vX.Y` and loads everything on init.
- `config_loader.get_character(name, version)` returns a dict with `"config": CharacterConfig`.
- `config_loader.get_character_by_id(id, version)` looks up by numeric ID.
- When version is omitted, the latest version is used.
- Character buffs in `configs/<v>/characters/<name>/buffs/` take priority over global buffs in `configs/<v>/buffs/`.

## ID conventions

Character: `10xx xxxx`, Relic sets: `20xx xxxx`, Light Cones: `30xx xxxx`, Enemies: `40xx xxxx`, Global Buffs: `50xx xxxx`, Character Buffs: `51xx xxxx`.

## Database notes

- Tables use `__tablename__` naming (plural), e.g. `user_characters`, `user_relics`, `user_light_cones`.
- `JSONText` type decorator handles JSON serialization via `orjson`.
- `UserCharacter.equipped_light_cone_id` has a UNIQUE constraint (one-to-one).
- Alembic uses `render_as_batch=True` and `sqlite:///./data/hsr.db`.
- Tests that need a fresh DB should use `:memory:` or temporary files — check `test_db_session.py` for patterns.

## Skill script conventions

- Configs reference scripts by path (e.g. `skills/seele_basic`). The loader resolves this to `configs.<version_token>.characters.<char_name>.skills.<script_name>`.
- The Python file must contain a class whose name is the CamelCase of the filename (e.g. `seele_basic` → `SeeleBasic`).
- The class must inherit `BaseSkill` (or the `expected_base_class`) and implement `execute`.
- Validated by `scripts/validate_configs.py`.
- Check `docs/event系统用法.md` and `docs/design.md` before adding game mechanics.

## Testing notes

- 119 tests, all passing.
- Common patterns: `mock_db` fixture (MagicMock), `monkeypatch` for patching module-level singletons like `config_loader`.
- Some integration tests write to real `configs/` on disk (e.g. `test_character_config_load.py`, `test_config_loader_integration.py`).
- `test_script_generators_loadable.py` runs the scaffolding scripts and verifies the generated skill scripts are importable.
