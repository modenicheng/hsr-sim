"""Migrate character config JSON files safely.

核心策略：
- 只补齐缺失字段（尤其是新增 schema 字段）
- 不覆盖任何已存在值（即使该值不是默认值）
- 默认 dry-run，需显式传入 --write 才会写回文件
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
import copy
import json
from pathlib import Path
import re

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.character import CharacterConfig

DEFAULT_CHARACTER_PATCH: dict = {
    "energy": {
        "energy_type": "standard",
        "max_energy": 120,
    }
}


def _normalize_version(value: str) -> str:
    matched = re.fullmatch(r"v?(\d+\.\d+)", value)
    if not matched:
        raise ValueError("version format only supports x.x or vx.x")
    return f"v{matched.group(1)}"


def _deep_fill_missing(target: dict, defaults: dict) -> dict:
    """Recursively fill missing keys from defaults, never overwrite existing values."""
    for key, default_value in defaults.items():
        if key not in target:
            target[key] = copy.deepcopy(default_value)
            continue

        current_value = target[key]
        if isinstance(current_value, dict) and isinstance(default_value, dict):
            _deep_fill_missing(current_value, default_value)

    return target


def _iter_versions(version: str | None) -> list[str]:
    if version:
        return [_normalize_version(version)]

    pattern = re.compile(r"^v(\d+)\.(\d+)$")
    versions = [
        p.name
        for p in CONFIGS_DIR.iterdir()
        if p.is_dir() and pattern.match(p.name)
    ]
    return sorted(versions)


def _iter_character_json_files(version: str) -> list[Path]:
    chars_root = CONFIGS_DIR / version / "characters"
    if not chars_root.exists():
        return []

    files: list[Path] = []
    for char_dir in chars_root.iterdir():
        if not char_dir.is_dir():
            continue
        json_path = char_dir / f"{char_dir.name}.json"
        if json_path.exists():
            files.append(json_path)
    return files


def migrate_character_configs(
    version: str | None = None, write: bool = False
) -> dict[str, int]:
    stats = {
        "scanned": 0,
        "updated": 0,
        "validated": 0,
        "errors": 0,
    }

    for ver in _iter_versions(version):
        for json_path in _iter_character_json_files(ver):
            stats["scanned"] += 1
            try:
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                migrated = _deep_fill_missing(
                    copy.deepcopy(payload), DEFAULT_CHARACTER_PATCH
                )

                # 迁移后必须可通过 schema 校验
                CharacterConfig.model_validate(migrated)
                stats["validated"] += 1

                if migrated != payload:
                    if write:
                        with json_path.open(
                            "w", encoding="utf-8", newline="\n"
                        ) as f:
                            f.write(
                                json.dumps(
                                    migrated, ensure_ascii=False, indent=2
                                )
                                + "\n"
                            )
                    stats["updated"] += 1
            except Exception as exc:  # noqa: BLE001
                stats["errors"] += 1
                print(f"[ERROR] {json_path}: {exc}")

    return stats


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description="Migrate character configs with safe default filling"
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Target version (x.x or vx.x). Default: all",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write changes to files. Without this flag, runs in dry-run mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stats = migrate_character_configs(version=args.version, write=args.write)

    mode = "WRITE" if args.write else "DRY-RUN"
    print(
        f"[{mode}] scanned={stats['scanned']} validated={stats['validated']} "
        f"updated={stats['updated']} errors={stats['errors']}"
    )


if __name__ == "__main__":
    main()
