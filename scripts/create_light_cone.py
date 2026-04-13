"""CLI tool to create light cone config files.

Default directory looks like:
CONFIGS_DIR/
    <version>/
        light_cones/
            <name>.json
            <name>.py
"""

from argparse import ArgumentParser, Namespace
import json
from pathlib import Path
import re
import shutil
from typing import Any

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.enums import Path as GamePath
from hsr_sim.models.schemas.light_cone import LightConeConfig
from hsr_sim.models.schemas.passive import PassiveSkillConfig

LIGHT_CONE_ID_RANGE = (30000000, 30999999)
LIGHT_CONE_PASSIVE_ID_RANGE = (31000000, 31999999)


def _validate_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_]+", value):
        raise ValueError("name only allows English characters and underscores (_).")
    return value


def _normalize_version(value: str) -> str:
    matched = re.fullmatch(r"v?(\d+\.\d+)", value)
    if not matched:
        raise ValueError("version 格式仅支持 x.x 或 vx.x（如 1.0 / v1.0）。")
    return f"v{matched.group(1)}"


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Create light cone config CLI")
    parser.add_argument(
        "names",
        nargs="+",
        help="One or more light cone names (English characters and underscores only)",
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


def _write_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"File already exists: {path}")
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _script_template(name: str) -> str:
    return (f'"""{name} light cone script."""\n\n'
            "\n"
            "def apply(context):\n"
            "    \"\"\"TODO: implement light cone behavior.\"\"\"\n"
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


def _build_light_cone_payload(name: str, light_cone_id: int, passive_id: int) -> dict:
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

    _write_json(json_path, _build_light_cone_payload(name, light_cone_id, passive_id))
    _write_text(py_path, _script_template(name))

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
