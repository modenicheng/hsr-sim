import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.character import CharacterConfig
from hsr_sim.models.schemas.light_cone import LightConeConfig
from hsr_sim.models.schemas.relics import RelicConfig
from hsr_sim.models.schemas.relics import RelicSetConfig


class ConfigLoader:
    def __init__(self):
        self._cache: dict[str, dict[str, dict[str, dict[str, Any]]]] = {
            "characters": defaultdict(dict),
            "light_cones": defaultdict(dict),
            "relics": defaultdict(dict),
        }
        self._versions: list[str] = []
        self._scan_versions()
        self._load_all()

    def _scan_versions(self) -> None:
        version_pattern = re.compile(r"^v(\d+)\.(\d+)$")
        versions: list[str] = []
        for item in CONFIGS_DIR.iterdir():
            if item.is_dir() and version_pattern.match(item.name):
                versions.append(item.name)
        self._versions = sorted(versions, key=self._parse_version)

    def _parse_version(self, version_str: str) -> tuple[int, int]:
        match = re.match(r"v(\d+)\.(\d+)", version_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0

    def _load_all(self) -> None:
        for version in self._versions:
            self._load_version(version)

    def _load_version(self, version: str) -> None:
        version_path = CONFIGS_DIR / version
        self._load_characters(version, version_path / "characters")
        self._load_light_cones(version, version_path / "light_cones")
        self._load_relics(version, version_path / "relics")

    def _load_characters(self, version: str, chars_root: Path) -> None:
        if not chars_root.exists():
            return

        for char_dir in chars_root.iterdir():
            if not char_dir.is_dir():
                continue

            char_name = char_dir.name
            json_file = char_dir / f"{char_name}.json"
            if not json_file.exists():
                continue

            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            char_config = CharacterConfig.model_validate(data)

            scripts_info = self._collect_character_scripts(version, char_dir, char_name)

            self._cache["characters"][char_name][version] = {
                "config": char_config,
                "scripts": scripts_info,
            }

    def _collect_character_scripts(
        self,
        version: str,
        char_dir: Path,
        char_name: str,
    ) -> dict[str, Any]:
        base_package = f"configs.{version}.characters.{char_name}"
        scripts: dict[str, Any] = {}

        skills_dir = char_dir / "skills"
        if skills_dir.exists():
            scripts["skills"] = {}
            for skill_file in skills_dir.glob("*.py"):
                skill_name = skill_file.stem
                scripts["skills"][skill_name] = f"{base_package}.skills.{skill_name}"

        talent_dir = char_dir / "talent"
        if talent_dir.exists():
            for talent_file in talent_dir.glob("*.py"):
                scripts["talent"] = f"{base_package}.talent.{talent_file.stem}"

        tech_dir = char_dir / "technique"
        if tech_dir.exists():
            for tech_file in tech_dir.glob("*.py"):
                scripts["technique"] = f"{base_package}.technique.{tech_file.stem}"

        eidolon_dir = char_dir / "eidolons"
        if eidolon_dir.exists():
            eidolon_files = sorted(eidolon_dir.glob("*.py"))
            scripts["eidolons"] = [f"{base_package}.eidolons.{f.stem}" for f in eidolon_files]

        bonus_dir = char_dir / "bonus_ability"
        if bonus_dir.exists():
            bonus_files = sorted(bonus_dir.glob("*.py"))
            scripts["bonus_abilities"] = [
                f"{base_package}.bonus_ability.{f.stem}" for f in bonus_files
            ]

        return scripts

    def _load_light_cones(self, version: str, lc_root: Path) -> None:
        if not lc_root.exists():
            return

        for lc_dir in lc_root.iterdir():
            if not lc_dir.is_dir():
                continue

            lc_name = lc_dir.name
            json_file = lc_dir / f"{lc_name}.json"
            py_file = lc_dir / f"{lc_name}.py"
            if not json_file.exists():
                continue

            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            lc_config = LightConeConfig.model_validate(data)

            script_module = None
            if py_file.exists():
                script_module = f"configs.{version}.light_cones.{lc_name}.{lc_name}"

            self._cache["light_cones"][lc_name][version] = {
                "config": lc_config,
                "script": script_module,
            }

    def _load_relics(self, version: str, relics_root: Path) -> None:
        if not relics_root.exists():
            return

        for set_dir in relics_root.iterdir():
            if not set_dir.is_dir():
                continue

            set_name = set_dir.name
            pieces: dict[str, RelicConfig] = {}
            set_config: RelicSetConfig | None = None

            for piece_file in set_dir.glob("*.json"):
                with piece_file.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                piece_config = RelicConfig.model_validate(payload)
                pieces[piece_file.stem] = piece_config
                if set_config is None:
                    set_config = piece_config.relic_set

            scripts: dict[str, str] = {}
            for script_file in set_dir.glob("*.py"):
                key = script_file.stem
                scripts[key] = f"configs.{version}.relics.{set_name}.{key}"

            self._cache["relics"][set_name][version] = {
                "config": set_config,
                "pieces": pieces,
                "scripts": scripts,
            }

    def _get_latest(self, dataset: dict[str, dict[str, Any]], version: str | None) -> dict[str, Any] | None:
        if not dataset:
            return None
        if version:
            return dataset.get(version)
        latest_ver = max(dataset.keys(), key=self._parse_version)
        return dataset[latest_ver]

    def get_character(self, name: str, version: str | None = None) -> dict[str, Any] | None:
        return self._get_latest(self._cache["characters"].get(name, {}), version)

    def get_character_versions(self, name: str) -> list[str]:
        return sorted(self._cache["characters"].get(name, {}).keys(), key=self._parse_version)

    def get_light_cone(self, name: str, version: str | None = None) -> dict[str, Any] | None:
        return self._get_latest(self._cache["light_cones"].get(name, {}), version)

    def get_light_cone_versions(self, name: str) -> list[str]:
        return sorted(self._cache["light_cones"].get(name, {}).keys(), key=self._parse_version)

    def get_relic_set(self, name: str, version: str | None = None) -> dict[str, Any] | None:
        return self._get_latest(self._cache["relics"].get(name, {}), version)

    def get_relic_set_versions(self, name: str) -> list[str]:
        return sorted(self._cache["relics"].get(name, {}).keys(), key=self._parse_version)