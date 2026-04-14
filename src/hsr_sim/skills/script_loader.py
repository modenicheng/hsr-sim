from __future__ import annotations

import importlib
import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

from hsr_sim.core.config import PROJECT_ROOT
from hsr_sim.core.exceptions import SkillClassNotFoundError
from hsr_sim.core.exceptions import SkillLoaderError
from hsr_sim.core.exceptions import SkillModuleNotFoundError
from hsr_sim.core.exceptions import SkillTypeMismatchError
from hsr_sim.models.db.user_characters import UserCharacter
from hsr_sim.models.schemas.character import CharacterConfig
from hsr_sim.services.config_loader import ConfigLoader


@dataclass(slots=True)
class SkillContext:
    """技能上下文依赖容器。"""

    world: Any = None
    event_bus: Any = None
    hook_chain: Any = None
    config_loader: ConfigLoader | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSkill:
    """技能脚本基类（可选）。"""

    def __init__(self, context: SkillContext):
        self.context = context


def _snake_to_camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _normalize_script_name(script: str) -> str:
    value = script.strip().replace("\\", "/")
    if value.endswith(".py"):
        value = value[:-3]
    return value


def _normalize_version_token(version: str) -> str:
    """将版本号标准化为可用于模块路径的 token（v1.0 -> v1_0）。"""
    return version.replace(".", "_")


def _denormalize_version_token(version_token: str) -> str:
    """将模块路径中的版本 token 还原为目录名（v1_0 -> v1.0）。"""
    return re.sub(r"^v(\d+)_(\d+)$", r"v\1.\2", version_token)


class DynamicClassLoader:
    """底层通用动态加载器：按模块路径导入并提取类对象。"""

    def __init__(self) -> None:
        self._class_cache: dict[str, type[Any]] = {}
        self._module_cache: dict[str, ModuleType] = {}

    def clear_cache(self) -> None:
        self._class_cache.clear()
        self._module_cache.clear()

    def load_module(self, module_path: str) -> ModuleType:
        if module_path in self._module_cache:
            return self._module_cache[module_path]

        module = self._import_as_module(module_path)
        self._module_cache[module_path] = module
        return module

    def load_class(
        self,
        module_path: str,
        class_name: str | None = None,
        expected_base_class: type[Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> type[Any]:
        cache_key = f"{module_path}:{class_name or ''}:{expected_base_class}"
        if cache_key in self._class_cache:
            return self._class_cache[cache_key]

        module = self.load_module(module_path)
        expected_name = class_name or _snake_to_camel(module_path.split(".")[-1])

        if not hasattr(module, expected_name):
            raise SkillClassNotFoundError(
                self._format_error(
                    f"Class '{expected_name}' not found in module '{module_path}'.",
                    context,
                )
            )

        cls = getattr(module, expected_name)
        if not isinstance(cls, type):
            raise SkillClassNotFoundError(
                self._format_error(
                    f"Attribute '{expected_name}' in '{module_path}' is not a class.",
                    context,
                )
            )

        if expected_base_class is not None and not issubclass(cls, expected_base_class):
            raise SkillTypeMismatchError(
                self._format_error(
                    (
                        f"Class '{expected_name}' in '{module_path}' does not inherit "
                        f"from '{expected_base_class.__name__}'."
                    ),
                    context,
                )
            )

        self._class_cache[cache_key] = cls
        return cls

    def _import_as_module(self, module_path: str) -> ModuleType:
        try:
            return importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            path = self._module_path_to_file(module_path)
            if path is None or not path.exists():
                raise SkillModuleNotFoundError(
                    f"Module '{module_path}' not found and resolved file does not exist."
                ) from exc

            spec = importlib.util.spec_from_file_location(module_path, path)
            if spec is None or spec.loader is None:
                raise SkillModuleNotFoundError(
                    f"Cannot create import spec for '{module_path}' from '{path}'."
                ) from exc

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    def _module_path_to_file(self, module_path: str) -> Path | None:
        parts = module_path.split(".")
        if not parts:
            return None

        if parts[0] == "configs" and len(parts) >= 2:
            parts = ["configs", _denormalize_version_token(parts[1]), *parts[2:]]

        return PROJECT_ROOT.joinpath(*parts).with_suffix(".py")

    @staticmethod
    def _format_error(message: str, context: dict[str, Any] | None) -> str:
        if not context:
            return message
        context_text = ", ".join(f"{k}={v}" for k, v in sorted(context.items()))
        return f"{message} (context: {context_text})"


class SkillScriptLoader:
    """中层加载器：基于版本与脚本名返回可执行技能对象。"""

    def __init__(
        self,
        dynamic_loader: DynamicClassLoader | None = None,
    ):
        self.dynamic_loader = dynamic_loader or DynamicClassLoader()

    def clear_cache(self) -> None:
        self.dynamic_loader.clear_cache()

    def load_skill(
        self,
        *,
        version: str,
        char_name: str,
        script: str,
        context: SkillContext,
        expected_base_class: type[Any] | None = BaseSkill,
        skill_type: str,
    ) -> Any:
        script_name = _normalize_script_name(script)
        module_path = self._build_module_path(
            version=version,
            char_name=char_name,
            script_name=script_name,
        )

        error_context = {
            "version": version,
            "char_name": char_name,
            "skill_type": skill_type,
            "script": script_name,
            "module": module_path,
        }

        cls = self.dynamic_loader.load_class(
            module_path,
            expected_base_class=expected_base_class,
            context=error_context,
        )
        return cls(context)

    @staticmethod
    def _build_module_path(*, version: str, char_name: str, script_name: str) -> str:
        version_token = _normalize_version_token(version)
        if "/" in script_name:
            script_module = script_name.replace("/", ".")
        else:
            script_module = f"skills.{script_name}"
        return f"configs.{version_token}.characters.{char_name}.{script_module}"


@dataclass(slots=True)
class CharacterSkillBundle:
    """角色技能集合，按类型聚合。"""

    active: list[Any] = field(default_factory=list)
    talents: list[Any] = field(default_factory=list)
    eidolons: list[Any] = field(default_factory=list)
    bonus_abilities: list[Any] = field(default_factory=list)
    technique: list[Any] = field(default_factory=list)

    @property
    def passive(self) -> list[Any]:
        return [*self.talents, *self.eidolons, *self.bonus_abilities]

    @property
    def all(self) -> list[Any]:
        return [*self.active, *self.passive, *self.technique]


class CharacterSkillLoader:
    """上层加载器：以角色实例为输入，聚合加载全部可用技能。"""

    def __init__(
        self,
        config_loader: ConfigLoader,
        script_loader: SkillScriptLoader | None = None,
    ):
        self.config_loader = config_loader
        self.script_loader = script_loader or SkillScriptLoader()

    def load_for_character(
        self,
        character: UserCharacter,
        context: SkillContext,
        *,
        activated_bonus_ability_ids: set[int] | None = None,
    ) -> CharacterSkillBundle:
        payload = self.config_loader.get_character_by_id(
            character.char_config_id,
            version=character.version,
        )
        if payload is None or not isinstance(payload.get("config"), CharacterConfig):
            raise SkillLoaderError(
                (
                    "Character config not found "
                    f"(char_config_id={character.char_config_id}, version={character.version})."
                )
            )

        char_config = payload["config"]
        bundle = CharacterSkillBundle()

        for skill_name, skill_cfg in (
            ("basic_atk", char_config.basic_atk),
            ("skill", char_config.skill),
            ("ultimate", char_config.ultimate),
        ):
            bundle.active.append(
                self.script_loader.load_skill(
                    version=character.version,
                    char_name=char_config.name,
                    script=skill_cfg.script,
                    context=context,
                    skill_type=skill_name,
                )
            )

        for talent in char_config.talents:
            script_obj = self.script_loader.load_skill(
                version=character.version,
                char_name=char_config.name,
                script=talent.script,
                context=context,
                skill_type="talent",
            )
            self._try_activate(script_obj)
            bundle.talents.append(script_obj)

        for eidolon in sorted(char_config.eidolons, key=lambda x: x.index):
            if eidolon.index > character.eidolon_level:
                continue
            script_obj = self.script_loader.load_skill(
                version=character.version,
                char_name=char_config.name,
                script=eidolon.script,
                context=context,
                skill_type="eidolon",
            )
            self._try_activate(script_obj)
            bundle.eidolons.append(script_obj)

        for bonus_ability in char_config.bonus_abilities:
            if (
                activated_bonus_ability_ids is not None
                and bonus_ability.id not in activated_bonus_ability_ids
            ):
                continue
            script_obj = self.script_loader.load_skill(
                version=character.version,
                char_name=char_config.name,
                script=bonus_ability.script,
                context=context,
                skill_type="bonus_ability",
            )
            self._try_activate(script_obj)
            bundle.bonus_abilities.append(script_obj)

        if char_config.technique and char_config.technique.script:
            script_obj = self.script_loader.load_skill(
                version=character.version,
                char_name=char_config.name,
                script=char_config.technique.script,
                context=context,
                skill_type="technique",
            )
            bundle.technique.append(script_obj)

        return bundle

    @staticmethod
    def deactivate_passive_skills(bundle: CharacterSkillBundle) -> None:
        for script_obj in bundle.passive:
            deactivate = getattr(script_obj, "deactivate", None)
            if callable(deactivate):
                deactivate()

    @staticmethod
    def _try_activate(script_obj: Any) -> None:
        activate = getattr(script_obj, "activate", None)
        if callable(activate):
            activate()


def load_script(script_path: str) -> ModuleType | None:
    """历史兼容：动态加载脚本模块。

    Args:
        script_path: 脚本路径，如 ``skills/seele_basic_atk`` 或模块路径。

    Returns:
        成功时返回模块对象；失败时返回 ``None``。
    """
    normalized = _normalize_script_name(script_path)
    module_path = normalized.replace("/", ".")

    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        try:
            return DynamicClassLoader().load_module(module_path)
        except SkillLoaderError:
            return None
