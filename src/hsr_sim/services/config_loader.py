import json
import re
from pathlib import Path
from typing import Any

from hsr_sim.core.config import CONFIGS_DIR
from hsr_sim.models.schemas.buff import BuffConfig
from hsr_sim.models.schemas.character import CharacterConfig
from hsr_sim.models.schemas.light_cone import LightConeConfig
from hsr_sim.models.schemas.relics import RelicConfig
from hsr_sim.models.schemas.relics import RelicSetConfig
from pydantic import ValidationError


def _normalize_version_token(version: str) -> str:
    return version.replace(".", "_")


class ConfigLoader:
    def __init__(self):
        self._cache: dict[str, dict[str, dict[str, dict[str, Any]]]] = {
            "characters": {},
            "light_cones": {},
            "relics": {},
            "buffs": {},
        }
        self._id_cache: dict[str, dict[int, dict[str, dict[str, Any]]]] = {
            "characters": {},
            "light_cones": {},
            "relics": {},
            "buffs": {},
        }
        self._character_buff_cache: dict[
            int, dict[str, dict[str, dict[str, Any]]]
        ] = {}
        self._character_buff_id_cache: dict[
            int, dict[int, dict[str, dict[str, Any]]]
        ] = {}
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
        self._load_character_buffs(version, version_path / "characters")
        self._load_light_cones(version, version_path / "light_cones")
        self._load_relics(version, version_path / "relics")
        self._load_buffs(version, version_path / "buffs")

    def _build_module_path(self, version: str, path: Path) -> str:
        relative_parts = list(
            path.with_suffix("").relative_to(CONFIGS_DIR / version).parts
        )
        return ".".join(
            ["configs", _normalize_version_token(version), *relative_parts]
        )

    def _put_cache(
        self,
        dataset: str,
        name: str,
        version: str,
        payload: dict[str, Any],
        entity_id: int | None = None,
    ) -> None:
        if name not in self._cache[dataset]:
            self._cache[dataset][name] = {}
        self._cache[dataset][name][version] = payload

        if entity_id is not None:
            if entity_id not in self._id_cache[dataset]:
                self._id_cache[dataset][entity_id] = {}
            self._id_cache[dataset][entity_id][version] = payload

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
            try:
                char_config = CharacterConfig.model_validate(data)
            except ValidationError:
                continue

            scripts_info = self._collect_character_scripts(
                version, char_dir, char_name
            )

            self._put_cache(
                dataset="characters",
                name=char_name,
                version=version,
                payload={
                    "config": char_config,
                    "scripts": scripts_info,
                },
                entity_id=char_config.id,
            )

    def _load_character_buffs(self, version: str, chars_root: Path) -> None:
        if not chars_root.exists():
            return

        for char_dir in chars_root.iterdir():
            if not char_dir.is_dir():
                continue
            char_dataset = self._cache["characters"].get(char_dir.name, {})
            char_payload = char_dataset.get(version)
            if not char_payload:
                continue
            char_config = char_payload.get("config")
            if not isinstance(char_config, CharacterConfig):
                continue
            self._load_buffs(
                version, char_dir / "buffs", character_id=char_config.id
            )

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
                scripts["skills"][skill_name] = (
                    f"{base_package}.skills.{skill_name}"
                )

        talent_dir = char_dir / "talent"
        if talent_dir.exists():
            for talent_file in talent_dir.glob("*.py"):
                scripts["talent"] = f"{base_package}.talent.{talent_file.stem}"

        tech_dir = char_dir / "technique"
        if tech_dir.exists():
            for tech_file in tech_dir.glob("*.py"):
                scripts["technique"] = (
                    f"{base_package}.technique.{tech_file.stem}"
                )

        eidolon_dir = char_dir / "eidolons"
        if eidolon_dir.exists():
            eidolon_files = sorted(eidolon_dir.glob("*.py"))
            scripts["eidolons"] = [
                f"{base_package}.eidolons.{f.stem}" for f in eidolon_files
            ]

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
            try:
                lc_config = LightConeConfig.model_validate(data)
            except ValidationError:
                continue

            script_module = None
            if py_file.exists():
                script_module = (
                    f"configs.{version}.light_cones.{lc_name}.{lc_name}"
                )

            self._put_cache(
                dataset="light_cones",
                name=lc_name,
                version=version,
                payload={
                    "config": lc_config,
                    "script": script_module,
                },
                entity_id=lc_config.id,
            )

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
                try:
                    piece_config = RelicConfig.model_validate(payload)
                except ValidationError:
                    continue
                pieces[piece_file.stem] = piece_config
                if set_config is None:
                    set_config = piece_config.relic_set

            scripts: dict[str, str] = {}
            for script_file in set_dir.glob("*.py"):
                key = script_file.stem
                scripts[key] = f"configs.{version}.relics.{set_name}.{key}"

            self._put_cache(
                dataset="relics",
                name=set_name,
                version=version,
                payload={
                    "config": set_config,
                    "pieces": pieces,
                    "scripts": scripts,
                },
                entity_id=set_config.id if set_config else None,
            )

    def _load_buffs(
        self,
        version: str,
        buffs_root: Path,
        character_id: int | None = None,
    ) -> None:
        if not buffs_root.exists():
            return

        for json_file in sorted(buffs_root.rglob("*.json")):
            payload = self._load_json(json_file)
            if payload is None:
                continue
            try:
                buff_config = BuffConfig.model_validate(payload)
            except ValidationError:
                continue

            buff_name = json_file.stem
            scripts: dict[str, str] = {}
            for script_file in sorted(json_file.parent.glob("*.py")):
                scripts[script_file.stem] = self._build_module_path(
                    version, script_file
                )

            cache_payload = {"config": buff_config, "scripts": scripts}
            if character_id is None:
                self._put_cache(
                    dataset="buffs",
                    name=buff_name,
                    version=version,
                    payload=cache_payload,
                    entity_id=buff_config.id,
                )
            else:
                self._put_character_buff_cache(
                    character_id=character_id,
                    name=buff_name,
                    version=version,
                    payload=cache_payload,
                    entity_id=buff_config.id,
                )

    def _put_character_buff_cache(
        self,
        *,
        character_id: int,
        name: str,
        version: str,
        payload: dict[str, Any],
        entity_id: int | None = None,
    ) -> None:
        if character_id not in self._character_buff_cache:
            self._character_buff_cache[character_id] = {}
        if name not in self._character_buff_cache[character_id]:
            self._character_buff_cache[character_id][name] = {}
        self._character_buff_cache[character_id][name][version] = payload

        if entity_id is not None:
            if character_id not in self._character_buff_id_cache:
                self._character_buff_id_cache[character_id] = {}
            if entity_id not in self._character_buff_id_cache[character_id]:
                self._character_buff_id_cache[character_id][entity_id] = {}
            self._character_buff_id_cache[character_id][entity_id][version] = (
                payload
            )

    def _load_json(self, path: Path) -> dict[str, Any] | None:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (OSError, json.JSONDecodeError):
            return None
        return None

    def _get_latest(
        self, dataset: dict[str, dict[str, Any]], version: str | None
    ) -> dict[str, Any] | None:
        if not dataset:
            return None
        if version:
            return dataset.get(version)
        latest_ver = max(dataset.keys(), key=self._parse_version)
        return dataset[latest_ver]

    def get_character(
        self, name: str, version: str | None = None
    ) -> dict[str, Any] | None:
        return self._get_latest(
            self._cache["characters"].get(name, {}), version
        )

    def get_character_versions(self, name: str) -> list[str]:
        return sorted(
            self._cache["characters"].get(name, {}).keys(),
            key=self._parse_version,
        )

    def get_all_characters(self) -> list[CharacterConfig]:
        """返回所有角色配置（最新版本）"""
        all_characters: list[CharacterConfig] = []
        for name in sorted(self._cache["characters"].keys()):
            latest = self._get_latest(self._cache["characters"][name], None)
            if latest and isinstance(latest.get("config"), CharacterConfig):
                all_characters.append(latest["config"])
        return all_characters

    def get_light_cone(
        self, name: str, version: str | None = None
    ) -> dict[str, Any] | None:
        return self._get_latest(
            self._cache["light_cones"].get(name, {}), version
        )

    def get_light_cone_versions(self, name: str) -> list[str]:
        return sorted(
            self._cache["light_cones"].get(name, {}).keys(),
            key=self._parse_version,
        )

    def get_relic_set(
        self, name: str, version: str | None = None
    ) -> dict[str, Any] | None:
        return self._get_latest(self._cache["relics"].get(name, {}), version)

    def get_relic_set_versions(self, name: str) -> list[str]:
        return sorted(
            self._cache["relics"].get(name, {}).keys(), key=self._parse_version
        )

    def get_all_light_cones(self) -> list[LightConeConfig]:
        all_light_cones: list[LightConeConfig] = []
        for name in sorted(self._cache["light_cones"].keys()):
            latest = self._get_latest(self._cache["light_cones"][name], None)
            if latest and isinstance(latest.get("config"), LightConeConfig):
                all_light_cones.append(latest["config"])
        return all_light_cones

    def get_all_relic_sets(self) -> list[RelicSetConfig]:
        all_relic_sets: list[RelicSetConfig] = []
        for name in sorted(self._cache["relics"].keys()):
            latest = self._get_latest(self._cache["relics"][name], None)
            if latest and isinstance(latest.get("config"), RelicSetConfig):
                all_relic_sets.append(latest["config"])
        return all_relic_sets

    def get_character_by_id(
        self,
        character_id: int,
        version: str | None = None,
    ) -> dict[str, Any] | None:
        return self._get_latest(
            self._id_cache["characters"].get(character_id, {}), version
        )

    def get_light_cone_by_id(
        self,
        light_cone_id: int,
        version: str | None = None,
    ) -> dict[str, Any] | None:
        return self._get_latest(
            self._id_cache["light_cones"].get(light_cone_id, {}), version
        )

    def get_relic_set_by_id(
        self,
        set_id: int,
        version: str | None = None,
    ) -> dict[str, Any] | None:
        return self._get_latest(
            self._id_cache["relics"].get(set_id, {}), version
        )

    def get_buff(
        self,
        name: str,
        version: str | None = None,
        character_id: int | None = None,
    ) -> dict[str, Any] | None:
        if character_id is not None:
            character_dataset = self._character_buff_cache.get(
                character_id, {}
            ).get(name, {})
            if version:
                latest = character_dataset.get(version)
                if latest is not None:
                    return latest
            else:
                latest = self._get_latest(character_dataset, None)
                if latest is not None:
                    return latest
        return self._get_latest(self._cache["buffs"].get(name, {}), version)

    def get_buff_by_id(
        self,
        buff_id: int,
        version: str | None = None,
        character_id: int | None = None,
    ) -> dict[str, Any] | None:
        if character_id is not None:
            character_dataset = self._character_buff_id_cache.get(
                character_id, {}
            ).get(buff_id, {})
            if version:
                latest = character_dataset.get(version)
                if latest is not None:
                    return latest
            else:
                latest = self._get_latest(character_dataset, None)
                if latest is not None:
                    return latest
        return self._get_latest(
            self._id_cache["buffs"].get(buff_id, {}), version
        )

    def get_buff_versions(
        self,
        name: str,
        character_id: int | None = None,
    ) -> list[str]:
        if character_id is not None:
            dataset = self._character_buff_cache.get(character_id, {}).get(name)
            if dataset:
                return sorted(dataset.keys(), key=self._parse_version)
        return sorted(
            self._cache["buffs"].get(name, {}).keys(), key=self._parse_version
        )

    def get_all_buffs(
        self, character_id: int | None = None
    ) -> list[BuffConfig]:
        if character_id is not None:
            all_buffs: list[BuffConfig] = []
            character_dataset = self._character_buff_cache.get(character_id, {})
            for name in sorted(character_dataset.keys()):
                latest = self._get_latest(character_dataset[name], None)
                if latest and isinstance(latest.get("config"), BuffConfig):
                    all_buffs.append(latest["config"])
            return all_buffs

        all_buffs: list[BuffConfig] = []
        for name in sorted(self._cache["buffs"].keys()):
            latest = self._get_latest(self._cache["buffs"][name], None)
            if latest and isinstance(latest.get("config"), BuffConfig):
                all_buffs.append(latest["config"])
        return all_buffs

    def reload(self) -> None:
        self._cache = {
            "characters": {},
            "light_cones": {},
            "relics": {},
            "buffs": {},
        }
        self._id_cache = {
            "characters": {},
            "light_cones": {},
            "relics": {},
            "buffs": {},
        }
        self._character_buff_cache = {}
        self._character_buff_id_cache = {}
        self._scan_versions()
        self._load_all()


config_loader = ConfigLoader()
