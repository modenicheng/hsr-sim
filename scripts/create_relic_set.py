"""CLI tool to create relic set config files.

Default directory looks like:
CONFIGS_DIR/
    <version>/
        relics/
            <set_name>/
            head.json / hands.json / ...
            <set_name>_2_pc.py
            <set_name>_4_pc.py
"""

from argparse import ArgumentParser, Namespace
import json
from pathlib import Path
import re
import shutil

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.enums import RelicSlot
from hsr_sim.models.schemas.passive import PassiveSkillConfig
from hsr_sim.models.schemas.relics import RelicConfig
from hsr_sim.models.schemas.relics import RelicSetConfig


def _validate_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_]+", value):
        raise ValueError("Relic set name only allows English characters and underscores (_)。")
    return value


def _normalize_version(value: str) -> str:
    matched = re.fullmatch(r"v?(\d+\.\d+)", value)
    if not matched:
        raise ValueError("version format only supports x.x or vx.x (e.g., 1.0 / v1.0).")
    return f"v{matched.group(1)}"


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create relic set config CLI")
    parser.add_argument("name", help="Relic set name (English characters and underscores only)")
    parser.add_argument(
        "--version",
        default="v1.0",
        help="Config version (supports x.x or vx.x, default v1.0)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwriting existing relic set directory.",
    )
    parser.add_argument(
        "-t",
        "--type",
        dest="set_type",
        required=True,
        choices=["relics", "planar_ornaments"],
        help="Set type: relics=outer circle relics, planar_ornaments=planar ornaments.",
    )

    args = parser.parse_args()

    try:
        args.name = _validate_name(args.name)
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


def _slot_list(set_type: str) -> list[RelicSlot]:
    if set_type == "relics":
        return [RelicSlot.HEAD, RelicSlot.HANDS, RelicSlot.TORSO, RelicSlot.FEET]
    return [RelicSlot.PLANAR_SPHERE, RelicSlot.LINK_ROPE]


def _script_template(set_name: str, script_name: str) -> str:
    return (
        f'"""{set_name} {script_name} script."""\n\n'
        "\n"
        "def apply(context):\n"
        "    \"\"\"TODO: implement set bonus behavior.\"\"\"\n"
        "    _ = context\n"
        "\n"
    )


def _build_relic_payload(set_name: str, slot: RelicSlot) -> dict:
    set_bonus_2_pc = PassiveSkillConfig(
        id=0,
        name=f"{set_name}_2_pc",
        description=f"TODO: fill 2-piece bonus for {set_name}",
        script=f"{set_name}_2_pc",
    )
    set_bonus_4_pc = PassiveSkillConfig(
        id=0,
        name=f"{set_name}_4_pc",
        description=f"TODO: fill 4-piece bonus for {set_name}",
        script=f"{set_name}_4_pc",
    )
    relic_set = RelicSetConfig(
        id=0,
        name=set_name,
        passive_2_pc=set_bonus_2_pc,
        passive_4_pc=set_bonus_4_pc,
    )

    relic = RelicConfig(
        id=0,
        name=f"{set_name}_{slot.value}",
        relic_set=relic_set,
        slot=slot,
        story=f"TODO: fill story for {slot.value}",
    )
    return relic.model_dump(mode="json")


def run_create_relic_set(name: str, version: str, set_type: str, force: bool = False) -> None:
    set_dir = CONFIGS_DIR / version / "relics" / name

    if set_dir.exists():
        if force:
            shutil.rmtree(set_dir)
        else:
            raise FileExistsError(
                "Failed to create relic set: the set already exists in the same version.\n"
                f"Set: {name}\n"
                f"Version: {version}\n"
                f"Path: {set_dir}\n"
                "Please change the name / version, or use -f/--force to overwrite."
            )

    set_dir.mkdir(parents=True, exist_ok=True)

    slots = _slot_list(set_type)
    created_files: list[Path] = []

    for slot in slots:
        json_path = set_dir / f"{slot.value}.json"
        _write_json(json_path, _build_relic_payload(name, slot))
        created_files.append(json_path)

    for script_name in ["2_pc", "4_pc"]:
        py_path = set_dir / f"{name}_{script_name}.py"
        _write_text(py_path, _script_template(name, script_name))
        created_files.append(py_path)

    print(f"Created {len(created_files)} files under: {set_dir}")


def main() -> None:
    args = parse_args()
    run_create_relic_set(args.name, args.version, args.set_type, args.force)


if __name__ == "__main__":
    main()