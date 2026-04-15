"""CLI tool to create enemy config files.

Default directory looks like:
CONFIGS_DIR/
    <version>/
        enemies/
            <enemy_name>/
                <enemy_name>.json
                skills/
                    <enemy_name>_skill.py
                passives/
                    <enemy_name>_passive.py
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
import shutil

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.enemy import EnemyConfig
from hsr_sim.models.schemas.enums import Element
from hsr_sim.models.schemas.passive import PassiveSkillConfig
from hsr_sim.models.schemas.skill import EnemySkillConfig

try:
    from scripts.scaffold_utils import allocate_ids
    from scripts.scaffold_utils import make_loadable_script_template
    from scripts.scaffold_utils import normalize_version
    from scripts.scaffold_utils import validate_name
    from scripts.scaffold_utils import write_json
    from scripts.scaffold_utils import write_text
except ModuleNotFoundError:
    from scaffold_utils import allocate_ids
    from scaffold_utils import make_loadable_script_template
    from scaffold_utils import normalize_version
    from scaffold_utils import validate_name
    from scaffold_utils import write_json
    from scaffold_utils import write_text

ENEMY_ID_RANGE = (40000000, 40999999)
ENEMY_SKILL_ID_RANGE = (41000000, 41999999)
ENEMY_PASSIVE_ID_RANGE = (42000000, 42999999)


def _validate_enemy_name(value: str) -> str:
    """Validate enemy name: only English letters and underscore are allowed."""
    return validate_name(value, label="Enemy name")


def _normalize_version(value: str) -> str:
    """Accept x.x or vx.x and normalize to vx.x."""
    return normalize_version(value)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create enemy config CLI")
    parser.add_argument(
        "enemy_names",
        nargs="+",
        help="One or more enemy names (English letters and underscores only)",
    )
    parser.add_argument(
        "--version",
        default="v1.0",
        help="Configuration version (supports x.x or vx.x, default v1.0)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite existing enemy directory in the same version.",
    )

    args = parser.parse_args()

    try:
        args.enemy_names = [
            _validate_enemy_name(name) for name in args.enemy_names
        ]
        args.version = _normalize_version(args.version)
    except ValueError as exc:
        parser.error(str(exc))

    return args


def _make_loadable_script_template(
    *,
    module_stem: str,
    title: str,
    execute_todo: str,
    class_doc: str,
) -> str:
    return make_loadable_script_template(
        module_stem=module_stem,
        title=title,
        execute_todo=execute_todo,
        class_doc=class_doc,
    )


def _make_enemy_skill_script_template(enemy_name: str) -> str:
    module_stem = f"{enemy_name}_skill"
    return _make_loadable_script_template(
        module_stem=module_stem,
        title=f"{enemy_name} skill script",
        execute_todo="TODO: implement enemy skill behavior.",
        class_doc="Auto-generated enemy skill script class.",
    )


def _make_enemy_passive_script_template(enemy_name: str) -> str:
    module_stem = f"{enemy_name}_passive"
    return _make_loadable_script_template(
        module_stem=module_stem,
        title=f"{enemy_name} passive script",
        execute_todo="TODO: implement enemy passive behavior.",
        class_doc="Auto-generated enemy passive script class.",
    )


def _allocate_ids(version: str,
                  id_range: tuple[int, int],
                  count: int = 1) -> list[int]:
    return allocate_ids(
        configs_dir=CONFIGS_DIR,
        version=version,
        id_range=id_range,
        count=count,
    )


def run_create_enemy(
    enemy_name: str,
    version: str,
    force: bool = False,
) -> None:
    enemy_dir = CONFIGS_DIR / version / "enemies" / enemy_name

    if enemy_dir.exists():
        if force:
            shutil.rmtree(enemy_dir)
        else:
            available_versions = sorted(
                [p.name for p in CONFIGS_DIR.iterdir() if p.is_dir()])
            version_hint = (
                f"Available versions: {', '.join(available_versions)}"
                if available_versions else
                "No available version directories detected.")
            raise FileExistsError(
                "Same enemy already exists in the same version.\n"
                f"Enemy: {enemy_name}\n"
                f"Version: {version}\n"
                f"Path: {enemy_dir}\n"
                f"{version_hint}\n"
                "Please change the --version or enemy name and try again; or use -f/--force to overwrite."
            )

    skills_dir = enemy_dir / "skills"
    passives_dir = enemy_dir / "passives"

    for folder in [skills_dir, passives_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    planned_files: list[Path] = [
        enemy_dir / f"{enemy_name}.json",
        skills_dir / f"{enemy_name}_skill.py",
        passives_dir / f"{enemy_name}_passive.py",
    ]

    existing_files = [str(path) for path in planned_files if path.exists()]
    if existing_files:
        raise FileExistsError(
            "Target files already exist, aborting to avoid partial overwrite:\n"
            + "\n".join(existing_files))

    created_files: list[Path] = []

    enemy_id = _allocate_ids(version, ENEMY_ID_RANGE, 1)[0]
    skill_id = _allocate_ids(version, ENEMY_SKILL_ID_RANGE, 1)[0]
    passive_id = _allocate_ids(version, ENEMY_PASSIVE_ID_RANGE, 1)[0]

    enemy_json_path = enemy_dir / f"{enemy_name}.json"
    enemy_skill = EnemySkillConfig(
        id=skill_id,
        name=f"{enemy_name}_skill",
        description="TODO: fill skill description",
        target_type="single_target",
        script=f"skills/{enemy_name}_skill",
    )
    enemy_passive = PassiveSkillConfig(
        id=passive_id,
        name=f"{enemy_name}_passive",
        description="TODO: fill passive description",
        script=f"passives/{enemy_name}_passive",
    )

    enemy = EnemyConfig(
        id=enemy_id,
        name=enemy_name,
        base_hp=1000,
        base_atk=500,
        base_def=500,
        base_spd=100,
        base_weakness=[Element.PHYSICAL],
        toughness=60,
        skills=[enemy_skill],
        passives=[enemy_passive],
    )

    write_json(enemy_json_path, enemy.model_dump(mode="json"))
    created_files.append(enemy_json_path)

    skill_py = skills_dir / f"{enemy_name}_skill.py"
    write_text(skill_py, _make_enemy_skill_script_template(enemy_name))
    created_files.append(skill_py)

    passive_py = passives_dir / f"{enemy_name}_passive.py"
    write_text(passive_py, _make_enemy_passive_script_template(enemy_name))
    created_files.append(passive_py)

    print(f"Created {len(created_files)} files under: {enemy_dir}")


def main() -> None:
    args = parse_args()
    failures: list[tuple[str, str]] = []
    for enemy_name in args.enemy_names:
        try:
            run_create_enemy(enemy_name, args.version, args.force)
        except Exception as exc:  # noqa: BLE001
            failures.append((enemy_name, str(exc)))

    if failures:
        lines = ["Batch creation finished with errors:"]
        lines.extend([f"- {name}: {message}" for name, message in failures])
        raise RuntimeError("\n".join(lines))


if __name__ == "__main__":
    main()
