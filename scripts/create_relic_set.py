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
from pathlib import Path
import shutil

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.enums import RelicSlot
from hsr_sim.models.schemas.passive import PassiveSkillConfig
from hsr_sim.models.schemas.relics import RelicConfig
from hsr_sim.models.schemas.relics import RelicSetConfig

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

RELIC_SET_ID_RANGE = (20000000, 20999999)
RELIC_ITEM_ID_RANGE = (21000000, 21999999)
RELIC_2PC_PASSIVE_ID_RANGE = (22000000, 22999999)
RELIC_4PC_PASSIVE_ID_RANGE = (23000000, 23999999)


def _validate_name(value: str) -> str:
    return validate_name(value, label="Relic set name")


def _normalize_version(value: str) -> str:
    return normalize_version(value)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create relic set config CLI")
    parser.add_argument(
        "names",
        nargs="+",
        help="One or more relic set names (English characters and underscores only)",
    )
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
        args.names = [_validate_name(name) for name in args.names]
        args.version = _normalize_version(args.version)
    except ValueError as exc:
        parser.error(str(exc))

    return args


def _slot_list(set_type: str) -> list[RelicSlot]:
    if set_type == "relics":
        return [
            RelicSlot.HEAD,
            RelicSlot.HANDS,
            RelicSlot.TORSO,
            RelicSlot.FEET,
        ]
    return [RelicSlot.PLANAR_SPHERE, RelicSlot.LINK_ROPE]


def _script_template(set_name: str, script_name: str) -> str:
    module_stem = f"{set_name}_{script_name}"
    return make_loadable_script_template(
        module_stem=module_stem,
        title=f"{set_name} {script_name} script",
        execute_todo="TODO: implement set bonus behavior.",
        class_doc="Auto-generated relic set script class.",
    )


def _allocate_ids(
    version: str, id_range: tuple[int, int], count: int = 1
) -> list[int]:
    return allocate_ids(
        configs_dir=CONFIGS_DIR,
        version=version,
        id_range=id_range,
        count=count,
    )


def _build_relic_payload(
    set_name: str,
    slot: RelicSlot,
    relic_id: int,
    relic_set: RelicSetConfig,
) -> dict:
    relic = RelicConfig(
        id=relic_id,
        name=f"{set_name}_{slot.value}",
        relic_set=relic_set,
        slot=slot,
        story=f"TODO: fill story for {slot.value}",
    )
    return relic.model_dump(mode="json")


def run_create_relic_set(
    name: str, version: str, set_type: str, force: bool = False
) -> None:
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

    relic_set_id = _allocate_ids(version, RELIC_SET_ID_RANGE, 1)[0]
    passive_2_pc_id = _allocate_ids(version, RELIC_2PC_PASSIVE_ID_RANGE, 1)[0]
    passive_4_pc_id = _allocate_ids(version, RELIC_4PC_PASSIVE_ID_RANGE, 1)[0]
    relic_item_ids = _allocate_ids(version, RELIC_ITEM_ID_RANGE, len(slots))

    set_bonus_2_pc = PassiveSkillConfig(
        id=passive_2_pc_id,
        name=f"{name}_2_pc",
        description=f"TODO: fill 2-piece bonus for {name}",
        script=f"{name}_2_pc",
    )
    set_bonus_4_pc = PassiveSkillConfig(
        id=passive_4_pc_id,
        name=f"{name}_4_pc",
        description=f"TODO: fill 4-piece bonus for {name}",
        script=f"{name}_4_pc",
    )
    relic_set = RelicSetConfig(
        id=relic_set_id,
        name=name,
        passive_2_pc=set_bonus_2_pc,
        passive_4_pc=set_bonus_4_pc,
    )

    for idx, slot in enumerate(slots):
        json_path = set_dir / f"{slot.value}.json"
        write_json(
            json_path,
            _build_relic_payload(name, slot, relic_item_ids[idx], relic_set),
        )
        created_files.append(json_path)

    for script_name in ["2_pc", "4_pc"]:
        py_path = set_dir / f"{name}_{script_name}.py"
        write_text(py_path, _script_template(name, script_name))
        created_files.append(py_path)

    print(f"Created {len(created_files)} files under: {set_dir}")


def main() -> None:
    args = parse_args()
    failures: list[tuple[str, str]] = []
    for name in args.names:
        try:
            run_create_relic_set(name, args.version, args.set_type, args.force)
        except Exception as exc:  # noqa: BLE001
            failures.append((name, str(exc)))

    if failures:
        lines = ["Batch creation finished with errors:"]
        lines.extend([f"- {name}: {message}" for name, message in failures])
        raise RuntimeError("\n".join(lines))


if __name__ == "__main__":
    main()
