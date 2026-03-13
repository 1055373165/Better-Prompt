from app.schemas.prompt_agent import EvaluateScoreBreakdown


class PromptEvaluateEngine:
    def evaluate(self, target_text: str) -> tuple[EvaluateScoreBreakdown, int, str, str]:
        text = target_text.strip()
        lower_text = text.lower()

        problem_fit = 4 if any(keyword in lower_text for keyword in ['任务', '目标', '问题', '需求']) else 2
        constraint_awareness = 4 if any(keyword in lower_text for keyword in ['约束', '限制', '边界', '前提']) else 2
        information_density = 4 if len(text) >= 300 else 3 if len(text) >= 140 else 2
        judgment_strength = 4 if any(keyword in lower_text for keyword in ['关键', '本质', '优先', '风险', '判断']) else 2
        executability = 4 if any(keyword in lower_text for keyword in ['下一步', '执行', '验证', '标准']) else 2
        natural_style = 4 if not any(keyword in text for keyword in ['首先', '其次', '最后']) else 3
        overall_stability = min(problem_fit, constraint_awareness, executability) + 1
        overall_stability = min(overall_stability, 5)

        breakdown = EvaluateScoreBreakdown(
            problem_fit=problem_fit,
            constraint_awareness=constraint_awareness,
            information_density=information_density,
            judgment_strength=judgment_strength,
            executability=executability,
            natural_style=natural_style,
            overall_stability=overall_stability,
        )

        score_map = breakdown.model_dump()
        weakest_key = min(score_map, key=score_map.get)
        total = sum(breakdown.model_dump().values())
        issue_map = {
            'problem_fit': ('任务定义仍不够清晰，问题拟合度偏弱', 'problem_redefinition'),
            'constraint_awareness': ('约束、边界或前提表达不足', 'boundary_validation'),
            'information_density': ('信息密度不足，存在被空话稀释的风险', 'information_density'),
            'judgment_strength': ('缺少关键判断与优先级区分', 'key_point_priority'),
            'executability': ('缺少可执行步骤、验证方式或成功标准', 'executability'),
            'natural_style': ('表达仍有模板化倾向，自然度不足', 'style_control'),
            'overall_stability': ('整体稳定性不足，输出容易受输入波动影响', 'style_control'),
        }
        top_issue, suggested_fix_layer = issue_map[weakest_key]
        return breakdown, total, top_issue, suggested_fix_layer
