# src/hsr_sim/utils/import_utils.py
import importlib
from typing import Any


def import_class(module_path: str) -> Any:
    """从模块路径导入类（约定类名为文件名驼峰形式）"""
    module_name, class_name = module_path.rsplit(".", 1)
    # 将文件名转为驼峰类名，例如 seele_basic_atk -> SeeleBasicAtk
    class_name = "".join(word.capitalize() for word in class_name.split("_"))
    module = importlib.import_module(module_name)
    return getattr(module, class_name)
