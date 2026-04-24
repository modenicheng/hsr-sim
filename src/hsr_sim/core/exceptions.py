class SkillLoaderError(Exception):
    """技能加载基础异常。"""


class SkillModuleNotFoundError(SkillLoaderError):
    """技能模块不存在。"""


class SkillClassNotFoundError(SkillLoaderError):
    """技能脚本模块中未找到约定类。"""


class SkillTypeMismatchError(SkillLoaderError):
    """技能脚本类不符合预期类型。"""
