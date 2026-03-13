class PromptResultFormatter:
    def continue_actions_for_generate(self) -> list[str]:
        return ['再增强深度', '再提高可执行性', '改成更自然的表达风格']

    def continue_actions_for_debug(self) -> list[str]:
        return ['继续修复结构缺口', '补强边界与约束', '保留原意但增强判断力']

    def continue_actions_for_evaluate(self) -> list[str]:
        return ['自动修复最低分项', '补强整体稳定性', '基于评估重生成一版']
