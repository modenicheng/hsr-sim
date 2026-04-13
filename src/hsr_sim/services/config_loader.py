import json
import importlib
from pathlib import Path
from typing import TypeVar
from pydantic import BaseModel
from src.hsr_sim.core.config import CONFIGS_DIR

T = TypeVar("T", bound=BaseModel)


class ConfigLoader:
    _instance = None
    _cache: dict[str, dict[int, BaseModel]] = {
    }  # {"characters": {1001: CharacterConfig}}

    def _scan_configs(self) -> list[str]:
        config_files = CONFIGS_DIR.glob("*.json")
        return [f.stem for f in config_files]


# 单例实例
config_loader = ConfigLoader()
