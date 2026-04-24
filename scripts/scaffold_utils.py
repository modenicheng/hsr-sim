from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


def validate_name(value: str, label: str = "Name") -> str:
    """Validate that a scaffold name contains only letters/underscore."""
    if not re.fullmatch(r"[A-Za-z_]+", value):
        raise ValueError(
            f"{label} only allows English characters and underscores (_)."
        )
    return value


def normalize_version(value: str) -> str:
    """Accept x.x or vx.x and normalize to vx.x."""
    matched = re.fullmatch(r"v?(\d+\.\d+)", value)
    if not matched:
        raise ValueError(
            "version format only supports x.x or vx.x (e.g., 1.0 or v1.0)."
        )
    return f"v{matched.group(1)}"


def write_text(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"File already exists: {path}")
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def snake_to_camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def make_loadable_script_template(
    *,
    module_stem: str,
    title: str,
    execute_todo: str,
    class_doc: str,
) -> str:
    """Generate a class-based script template for dynamic class loading."""
    class_name = snake_to_camel(module_stem)
    return (
        f'"""{title}."""\n\n'
        "from hsr_sim.skills.script_loader import BaseSkill\n\n\n"
        f"class {class_name}(BaseSkill):\n"
        f'    """{class_doc}"""\n\n'
        "    def execute(self, *args, **kwargs):\n"
        f'        """{execute_todo}"""\n'
        "        _ = args, kwargs\n"
        "        return None\n\n\n"
    )


def extract_ids(payload: Any) -> list[int]:
    ids: list[int] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "id" and isinstance(value, int):
                ids.append(value)
            ids.extend(extract_ids(value))
    elif isinstance(payload, list):
        for item in payload:
            ids.extend(extract_ids(item))
    return ids


def collect_version_ids(*, configs_dir: Path, version: str) -> list[int]:
    version_dir = configs_dir / version
    if not version_dir.exists():
        return []

    ids: list[int] = []
    for json_path in version_dir.rglob("*.json"):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ids.extend(extract_ids(payload))
    return ids


def allocate_ids(
    *,
    configs_dir: Path,
    version: str,
    id_range: tuple[int, int],
    count: int = 1,
) -> list[int]:
    lower, upper = id_range
    existing = [
        value
        for value in collect_version_ids(
            configs_dir=configs_dir, version=version
        )
        if lower <= value <= upper
    ]
    start = max(existing, default=lower - 1) + 1
    end = start + count - 1
    if end > upper:
        raise ValueError(f"ID range exhausted: {lower}-{upper}")
    return list(range(start, end + 1))
