"""CLI tool to create light cone config files.

Default directory looks like:
CONFIGS_DIR/
    <version>/
        light_cones/
            <name>.json
            <name>.py
"""

from argparse import ArgumentParser, Namespace
import shutil

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.enums import Path as GamePath
from hsr_sim.models.schemas.light_cone import LightConeConfig
from hsr_sim.models.schemas.passive import PassiveSkillConfig

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

LIGHT_CONE_ID_RANGE = (30000000, 30999999)
LIGHT_CONE_PASSIVE_ID_RANGE = (31000000, 31999999)


def _validate_name(value: str) -> str:
    return validate_name(value, label="name")


def _normalize_version(value: str) -> str:
    return normalize_version(value)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create light cone config CLI")
    parser.add_argument(
        "names",
        nargs="+",
        help=
        "One or more light cone names (English characters and underscores only)",
    )
    parser.add_argument(
        "--version",
        "-v",
        default="v1.0",
        help="Config version (supports x.x or vx.x, default v1.0)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwriting existing light cone directory.",
    )

    args = parser.parse_args()

    try:
        args.names = [_validate_name(name) for name in args.names]
        args.version = _normalize_version(args.version)
    except ValueError as exc:
        parser.error(str(exc))

    return args


def _script_template(name: str) -> str:
    return make_loadable_script_template(
        module_stem=name,
        title=f"{name} light cone script",
        execute_todo="TODO: implement light cone behavior.",
        class_doc="Auto-generated light cone script class.",
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


def _build_light_cone_payload(name: str, light_cone_id: int,
                              passive_id: int) -> dict:
    light_cone = LightConeConfig(
        id=light_cone_id,
        name=name,
        rarity=5,
        path=GamePath.HUNT,
        story=f"TODO: fill story for {name}",
        passive_skill=PassiveSkillConfig(
            id=passive_id,
            name=f"{name}_passive",
            description=f"TODO: fill passive skill for {name}",
            script=f"light_cones/{name}",
        ),
    )
    return light_cone.model_dump(mode="json")


def run_create_light_cone(name: str,
                          version: str,
                          force: bool = False) -> None:
    cone_dir = CONFIGS_DIR / version / "light_cones" / name

    if cone_dir.exists():
        if force:
            shutil.rmtree(cone_dir)
        else:
            raise FileExistsError(
                "Failed to create light cone: the cone already exists in the same version.\n"
                f"Light Cone: {name}\n"
                f"Version: {version}\n"
                f"Path: {cone_dir}\n"
                "Please change the name / version, or use -f/--force to overwrite."
            )

    cone_dir.mkdir(parents=True, exist_ok=True)

    light_cone_id = _allocate_ids(version, LIGHT_CONE_ID_RANGE, 1)[0]
    passive_id = _allocate_ids(version, LIGHT_CONE_PASSIVE_ID_RANGE, 1)[0]

    json_path = cone_dir / f"{name}.json"
    py_path = cone_dir / f"{name}.py"

    write_json(json_path,
               _build_light_cone_payload(name, light_cone_id, passive_id))
    write_text(py_path, _script_template(name))

    print(f"Created 2 files under: {cone_dir}")


def main() -> None:
    args = parse_args()
    failures: list[tuple[str, str]] = []
    for name in args.names:
        try:
            run_create_light_cone(name, args.version, args.force)
        except Exception as exc:  # noqa: BLE001
            failures.append((name, str(exc)))

    if failures:
        lines = ["Batch creation finished with errors:"]
        lines.extend([f"- {name}: {message}" for name, message in failures])
        raise RuntimeError("\n".join(lines))


if __name__ == "__main__":
    main()
