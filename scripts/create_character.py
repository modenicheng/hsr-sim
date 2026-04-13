"""CLI tool to create character config files.

Default directory looks like:
CONFIGS_DIR/
    <version>/
        characters/
            <character_name>/
                <character_name>.json
                skills/
                    <character_name>_basic_atk.py
                    <character_name>_skill.py
                    <character_name>_ultimate.py
                    ...
                eidolon/
                    <character_name>_eidolon_1.py
                    ...
                talent/
                    <character_name>_talent.py
                technique/
                    <character_name>_technique.py
                bonus_ability/
                    <character_name>_bonus_ability_1.py
                    ...
"""

from argparse import ArgumentParser, Namespace
import json
from pathlib import Path
import re
import shutil
from typing import Any

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.character import CharacterConfig
from hsr_sim.models.schemas.eidolon import EidolonConfig
from hsr_sim.models.schemas.passive import PassiveSkillConfig
from hsr_sim.models.schemas.skill import SkillConfig
from hsr_sim.models.schemas.enums import Element, SkillType, StatType

CHARACTER_ID_RANGE = (10000000, 10999999)
BASIC_ATK_ID_RANGE = (11000000, 11999999)
SKILL_ID_RANGE = (12000000, 12999999)
ULTIMATE_ID_RANGE = (13000000, 13999999)
EIDOLON_ID_RANGE = (14000000, 14999999)
TALENT_ID_RANGE = (15000000, 15999999)
TECHNIQUE_ID_RANGE = (16000000, 16999999)
BONUS_ABILITY_ID_RANGE = (17000000, 17999999)


def _validate_character_name(value: str) -> str:
    """Validate character name: only English letters and underscore are allowed."""
    if not re.fullmatch(r"[A-Za-z_]+", value):
        raise ValueError(
            "Character name only allows English characters and underscores (_)."
        )
    return value


def _normalize_version(value: str) -> str:
    """Accept x.x or vx.x and normalize to vx.x."""
    matched = re.fullmatch(r"v?(\d+\.\d+)", value)
    if not matched:
        raise ValueError(
            "version format only supports x.x or vx.x (e.g., 1.0 or v1.0).")
    return f"v{matched.group(1)}"


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create character config CLI")
    parser.add_argument(
        "character_names",
        nargs="+",
        help="One or more character names (English letters and underscores only)",
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
        help="Force overwrite existing character directory in the same version.",
    )

    args = parser.parse_args()

    try:
        args.character_names = [_validate_character_name(name) for name in args.character_names]
        args.version = _normalize_version(args.version)
    except ValueError as exc:
        parser.error(str(exc))

    return args


def _write_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"File already exists: {path}")
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _make_skill_script_template(character_name: str, skill_name: str) -> str:
    return (f'"""{character_name} {skill_name} script."""\n\n'
            "\n"
            "def apply(context):\n"
            "    \"\"\"TODO: implement skill behavior.\"\"\"\n"
            "    _ = context\n"
            "\n")


def _make_empty_script_template(title: str) -> str:
    return (f'"""{title}."""\n\n'
            "\n"
            "def apply(context):\n"
            "    \"\"\"TODO: implement behavior.\"\"\"\n"
            "    _ = context\n"
            "\n")


def _extract_ids(payload: Any) -> list[int]:
    ids: list[int] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "id" and isinstance(value, int):
                ids.append(value)
            ids.extend(_extract_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            ids.extend(_extract_ids(item))
    return ids


def _collect_version_ids(version: str) -> list[int]:
    version_dir = CONFIGS_DIR / version
    if not version_dir.exists():
        return []

    ids: list[int] = []
    for json_path in version_dir.rglob("*.json"):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ids.extend(_extract_ids(payload))
    return ids


def _allocate_ids(version: str, id_range: tuple[int, int], count: int = 1) -> list[int]:
    lower, upper = id_range
    existing = [value for value in _collect_version_ids(version) if lower <= value <= upper]
    start = max(existing, default=lower - 1) + 1
    end = start + count - 1
    if end > upper:
        raise ValueError(f"ID range exhausted: {lower}-{upper}")
    return list(range(start, end + 1))


def run_create_character(
    character_name: str,
    version: str,
    force: bool = False,
) -> None:
    char_dir = CONFIGS_DIR / version / "characters" / character_name

    if char_dir.exists():
        if force:
            shutil.rmtree(char_dir)
        else:
            available_versions = sorted(
                [p.name for p in CONFIGS_DIR.iterdir() if p.is_dir()]
            )
            version_hint = (
                f"Available versions: {', '.join(available_versions)}"
                if available_versions
                else "No available version directories detected."
            )
            raise FileExistsError(
                "Same character already exists in the same version.\n"
                f"Character: {character_name}\n"
                f"Version: {version}\n"
                f"Path: {char_dir}\n"
                f"{version_hint}\n"
                "Please change the --version or character name and try again; or use -f/--force to overwrite."
            )

    skills_dir = char_dir / "skills"
    eidolons_dir = char_dir / "eidolons"
    talent_dir = char_dir / "talent"
    technique_dir = char_dir / "technique"
    bonus_ability_dir = char_dir / "bonus_ability"

    for folder in [
            skills_dir,
            eidolons_dir,
            talent_dir,
            technique_dir,
            bonus_ability_dir,
    ]:
        folder.mkdir(parents=True, exist_ok=True)

    planned_files: list[Path] = [
        char_dir / f"{character_name}.json",
        skills_dir / f"{character_name}_basic_atk.py",
        skills_dir / f"{character_name}_skill.py",
        skills_dir / f"{character_name}_ultimate.py",
        talent_dir / f"{character_name}_talent.py",
        technique_dir / f"{character_name}_technique.py",
        bonus_ability_dir / f"{character_name}_bonus_ability_1.py",
    ]
    planned_files.extend([eidolons_dir / f"{character_name}_eidolon_{i}.py" for i in range(1, 7)])

    existing_files = [str(path) for path in planned_files if path.exists()]
    if existing_files:
        raise FileExistsError(
            "Target files already exist, aborting to avoid partial overwrite:\n"
            + "\n".join(existing_files))

    created_files: list[Path] = []

    character_id = _allocate_ids(version, CHARACTER_ID_RANGE, 1)[0]
    basic_atk_id = _allocate_ids(version, BASIC_ATK_ID_RANGE, 1)[0]
    skill_id = _allocate_ids(version, SKILL_ID_RANGE, 1)[0]
    ultimate_id = _allocate_ids(version, ULTIMATE_ID_RANGE, 1)[0]
    eidolon_ids = _allocate_ids(version, EIDOLON_ID_RANGE, 6)
    talent_id = _allocate_ids(version, TALENT_ID_RANGE, 1)[0]
    technique_id = _allocate_ids(version, TECHNIQUE_ID_RANGE, 1)[0]
    bonus_ability_ids = _allocate_ids(version, BONUS_ABILITY_ID_RANGE, 3)

    character_json_path = char_dir / f"{character_name}.json"
    basic_atk_skill = SkillConfig(
        id=basic_atk_id,
        name=f"{character_name}_{SkillType.BASIC.value}",
        type=SkillType.BASIC,
        description="TODO: fill description",
        target_type="single_target",
        energy_gain=0,
        script=f"skills/{character_name}_basic_atk",
    )
    skill = SkillConfig(
        id=skill_id,
        name=f"{character_name}_{SkillType.SKILL.value}",
        type=SkillType.SKILL,
        description="TODO: fill description",
        target_type="single_target",
        energy_gain=0,
        script=f"skills/{character_name}_skill",
    )
    ultimate = SkillConfig(
        id=ultimate_id,
        name=f"{character_name}_{SkillType.ULTIMATE.value}",
        type=SkillType.ULTIMATE,
        description="TODO: fill description",
        target_type="single_target",
        energy_gain=0,
        script=f"skills/{character_name}_ultimate",
    )

    eidolons: list[EidolonConfig] = []
    for i in range(1, 7):
        eidolons.append(
            EidolonConfig(
                id=eidolon_ids[i - 1],
                index=i,
                name=f"{character_name}_eidolon_{i}",
                describe="TODO: fill eidolon describe",
                script=f"eidolons/{character_name}_eidolon_{i}",
            ))

    character = CharacterConfig(
        id=character_id,
        name=character_name,
        rarity=5,
        element=Element.QUANTUM,
        base_hp=1000,
        base_atk=500,
        base_def=500,
        base_spd=100,
        basic_atk=basic_atk_skill,
        skill=skill,
        ultimate=ultimate,
        eidolons=eidolons,
        talents=[
            PassiveSkillConfig(
                id=talent_id,
                name=f"{character_name}_talent",
                description="TODO: fill talent description",
                script=f"talent/{character_name}_talent",
            )
        ],
        technique=PassiveSkillConfig(
            id=technique_id,
            name=f"{character_name}_technique",
            description="TODO: fill technique description",
            script=f"technique/{character_name}_technique",
        ),
        bonus_abilities=[
            PassiveSkillConfig(
                id=bonus_ability_ids[i - 1],
                name=f"{character_name}_bonus_ability_{i}",
                description="TODO: fill bonus ability description",
                script=f"bonus_ability/{character_name}_bonus_ability_{i}",
            )
            for i in range(1, 4)
        ],
        stat_bonus={StatType.ATK_PERCENT: 0.0},
    )

    _write_json(character_json_path, character.model_dump(mode="json"))
    created_files.append(character_json_path)

    skill_file_stems = ["basic_atk", "skill", "ultimate"]
    for file_stem in skill_file_stems:
        py_path = skills_dir / f"{character_name}_{file_stem}.py"
        _write_text(
            py_path,
            _make_skill_script_template(character_name, file_stem),
        )
        created_files.append(py_path)

    for i in range(1, 7):
        eidolon_py = eidolons_dir / f"{character_name}_eidolon_{i}.py"
        _write_text(
            eidolon_py,
            _make_empty_script_template(
                f"{character_name} eidolon {i} script"),
        )
        created_files.append(eidolon_py)

    talent_py = talent_dir / f"{character_name}_talent.py"
    _write_text(
        talent_py,
        _make_empty_script_template(f"{character_name} talent script"),
    )
    created_files.append(talent_py)

    technique_py = technique_dir / f"{character_name}_technique.py"
    _write_text(
        technique_py,
        _make_empty_script_template(f"{character_name} technique script"),
    )
    created_files.append(technique_py)

    for i in range(1, 4):
        bonus_py = bonus_ability_dir / f"{character_name}_bonus_ability_{i}.py"
        _write_text(
            bonus_py,
            _make_empty_script_template(
                f"{character_name} bonus ability {i} script", ),
        )
        created_files.append(bonus_py)

    print(f"Created {len(created_files)} files under: {char_dir}")


def main() -> None:
    args = parse_args()
    failures: list[tuple[str, str]] = []
    for character_name in args.character_names:
        try:
            run_create_character(character_name, args.version, args.force)
        except Exception as exc:  # noqa: BLE001
            failures.append((character_name, str(exc)))

    if failures:
        lines = ["Batch creation finished with errors:"]
        lines.extend([f"- {name}: {message}" for name, message in failures])
        raise RuntimeError("\n".join(lines))


if __name__ == "__main__":
    main()
