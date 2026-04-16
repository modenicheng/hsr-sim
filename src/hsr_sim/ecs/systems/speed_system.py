from esper import Processor

class SpeedSystem(Processor):
    """已降级：行动值管理现已由 TurnSystem 负责。

    本 System 保留以保持向后兼容性，但不再执行任何操作。
    """

    def process(self):
        # 行动值管理由 TurnSystem 完全接管，此处不再操作
        pass
