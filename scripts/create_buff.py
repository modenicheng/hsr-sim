"""CLI tool to create buff config files.

Usage:

- `create_buff <buff_name>`
- `create_buff overload <character_name> <buff_name>`

Default directory looks like:
CONFIGS_DIR/
    <version>/
        buffs/
            <buff_name>/
                <buff_name>.json
                <buff_name>.py
        characters/
            <character_name>/
                buffs/
                    <buff_name>/
                        <buff_name>.json
                        <buff_name>.py
"""

from argparse import ArgumentParser, Namespace
import shutil

from hsr_sim.core.config import CONFIGS_DIR

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

GLOBAL_BUFF_ID_RANGE = (50000000, 50999999)
CHARACTER_BUFF_ID_RANGE = (51000000, 51999999)


def _validate_name(value: str) -> str:
    return validate_name(value, label="Name")


def _normalize_version(value: str) -> str:
    return normalize_version(value)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create buff config CLI")
    parser.add_argument(
        "parts",
        nargs="+",
        help="`<buff_name>` or `overload <character_name> <buff_name>`.",
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
        help="Force overwriting existing buff directory.",
    )

    args = parser.parse_args()

    try:
        args.version = _normalize_version(args.version)

        if args.parts[0] == "overload":
            if len(args.parts) != 3:
                raise ValueError(
                    "overload mode requires: overload <character_name> <buff_name>"
                )
            args.mode = "character"
            args.character_name = _validate_name(args.parts[1])
            args.buff_name = _validate_name(args.parts[2])
        else:
            if len(args.parts) != 1:
                raise ValueError("global mode requires: <buff_name>")
            args.mode = "global"
            args.character_name = None
            args.buff_name = _validate_name(args.parts[0])
    except ValueError as exc:
        parser.error(str(exc))

    return args


def _make_buff_script_template(*, module_stem: str, title: str) -> str:
    return make_loadable_script_template(
        module_stem=module_stem,
        title=title,
        execute_todo="TODO: implement buff behavior.",
        class_doc="Auto-generated buff script class.",
    )


def _build_buff_payload(
    *,
    buff_name: str,
    buff_id: int,
    script_path: str,
    mode: str,
    character_name: str | None,
) -> dict:
    payload = {
        "id": buff_id,
        "name": buff_name,
        "description": f"TODO: fill description for {buff_name}",
        "scope": mode,
        "max_stacks": 1,
        "default_duration": 1,
        "dispelable": False,
        "script": script_path,
        "params": {},
    }
    if character_name is not None:
        payload["character_name"] = character_name
    return payload


def run_create_buff(
    buff_name: str,
    version: str,
    *,
    character_name: str | None = None,
    force: bool = False,
) -> None:
    if character_name is None:
        buff_dir = CONFIGS_DIR / version / "buffs" / buff_name
        buff_id = allocate_ids(
            configs_dir=CONFIGS_DIR,
            version=version,
            id_range=GLOBAL_BUFF_ID_RANGE,
            count=1,
        )[0]
        script_path = f"buffs/{buff_name}/{buff_name}"
    else:
        buff_dir = CONFIGS_DIR / version / "characters" / character_name / "buffs" / buff_name
        buff_id = allocate_ids(
            configs_dir=CONFIGS_DIR,
            version=version,
            id_range=CHARACTER_BUFF_ID_RANGE,
            count=1,
        )[0]
        script_path = f"characters/{character_name}/buffs/{buff_name}/{buff_name}"

    if buff_dir.exists():
        if force:
            shutil.rmtree(buff_dir)
        else:
            scope = character_name or "global"
            raise FileExistsError(
                "Failed to create buff: the buff already exists in the same version.\n"
                f"Buff: {buff_name}\n"
                f"Scope: {scope}\n"
                f"Version: {version}\n"
                f"Path: {buff_dir}\n"
                "Please change the name / version, or use -f/--force to overwrite."
            )

    buff_dir.mkdir(parents=True, exist_ok=True)

    json_path = buff_dir / f"{buff_name}.json"
    py_path = buff_dir / f"{buff_name}.py"

    write_json(
        json_path,
        _build_buff_payload(
            buff_name=buff_name,
            buff_id=buff_id,
            script_path=script_path,
            mode="character" if character_name else "global",
            character_name=character_name,
        ),
    )
    write_text(
        py_path,
        _make_buff_script_template(
            module_stem=buff_name,
            title=f"{buff_name} buff script",
        ),
    )

    print(f"Created 2 files under: {buff_dir}")


def main() -> None:
    args = parse_args()
    try:
        run_create_buff(
            args.buff_name,
            args.version,
            character_name=args.character_name,
            force=args.force,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(str(exc)) from exc


if __name__ == "__main__":
    main()
