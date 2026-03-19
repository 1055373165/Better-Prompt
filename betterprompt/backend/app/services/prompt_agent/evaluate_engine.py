import re
from typing import Any

from app.schemas.prompt_agent import EvaluateScoreBreakdown


# 5-level rubric anchors for each dimension
RUBRIC: dict[str, dict[int, str]] = {
    'problem_fit': {
        1: '完全没有定义任务目标或问题范围',
        2: '仅有模糊的目标描述，缺少具体约束',
        3: '任务目标基本清晰，但边界或对象不够明确',
        4: '任务目标和对象清晰，包含核心约束条件',
        5: '任务目标、对象、范围和约束完整且精准',
    },
    'constraint_awareness': {
        1: '完全没有提及约束、限制或前提条件',
        2: '仅有泛泛的约束提及，缺乏具体说明',
        3: '包含部分约束但不完整，或缺少边界定义',
        4: '关键约束和前提条件明确，覆盖主要场景',
        5: '约束、前提、边界和失效条件完整且相互关联',
    },
    'information_density': {
        1: '内容空洞，大量重复或无效信息',
        2: '信息稀疏，存在明显空话或冗余段落',
        3: '信息量适中，但仍有可压缩的冗余',
        4: '信息密集，每段都有新的判断或洞察',
        5: '信息密度极高，无冗余，每句话都不可删除',
    },
    'judgment_strength': {
        1: '没有任何判断或优先级区分',
        2: '仅有表面判断，缺少依据或优先级',
        3: '包含基本判断但缺少深度推理或权衡',
        4: '关键判断清晰，有推理依据和优先级排序',
        5: '判断深刻、有层次，包含权衡和决策框架',
    },
    'executability': {
        1: '完全没有可执行的步骤或标准',
        2: '提到了"执行"但缺少具体步骤或标准',
        3: '有基本执行步骤但缺少验证方式或成功标准',
        4: '执行步骤清晰，包含验证方式和成功标准',
        5: '执行路径完整，包含步骤、验证、回退和成功标准',
    },
    'natural_style': {
        1: '充斥"首先/其次/最后"等模板结构，AI味浓重',
        2: '模板化倾向明显，表达生硬',
        3: '部分段落自然但仍有模板痕迹',
        4: '整体流畅自然，极少模板表达',
        5: '完全自然流畅，像专家在认真讨论问题',
    },
    'overall_stability': {
        1: '结构混乱，输出质量不可预测',
        2: '有基本结构但稳定性差，容易跑偏',
        3: '结构尚可，但部分维度明显薄弱',
        4: '各维度均衡，整体稳定可靠',
        5: '各维度均强，结构稳健，可直接投入使用',
    },
}

# Score interpretation thresholds
SCORE_INTERPRETATIONS = [
    (30, 35, '可直接使用：Prompt 质量优秀，各维度均衡稳健，可直接投入生产场景。'),
    (24, 29, '建议精修：Prompt 整体可用，但部分维度有提升空间，建议围绕最弱项做一轮定向优化。'),
    (18, 23, '建议调试：Prompt 基础框架存在，但多个维度不达标，建议使用 Debug 模式进行系统性修复。'),
    (0, 17, '建议重构：Prompt 质量不足以产生稳定输出，建议使用 Generate 模式重新生成。'),
]


class PromptEvaluateEngine:
    def evaluate(
        self,
        target_text: str,
        *,
        target_type: str = 'prompt',
        profile_rules: dict[str, Any] | None = None,
        recipe_definition: dict[str, Any] | None = None,
    ) -> tuple[EvaluateScoreBreakdown, int, str, str, str]:
        text = target_text.strip()
        lower_text = text.lower()

        problem_fit = self._score_problem_fit(text, lower_text)
        constraint_awareness = self._score_constraint_awareness(text, lower_text)
        information_density = self._score_information_density(text, lower_text)
        judgment_strength = self._score_judgment_strength(text, lower_text)
        executability = self._score_executability(text, lower_text)
        natural_style = self._score_natural_style(text, lower_text)
        overall_stability = self._score_overall_stability(
            problem_fit, constraint_awareness, information_density,
            judgment_strength, executability, natural_style,
        )

        breakdown = EvaluateScoreBreakdown(
            problem_fit=problem_fit,
            constraint_awareness=constraint_awareness,
            information_density=information_density,
            judgment_strength=judgment_strength,
            executability=executability,
            natural_style=natural_style,
            overall_stability=overall_stability,
        )
        breakdown = self._apply_target_type_adjustments(breakdown, lower_text, target_type)
        breakdown = self._apply_profile_adjustments(breakdown, lower_text, profile_rules or {})
        breakdown = self._apply_recipe_adjustments(breakdown, lower_text, recipe_definition or {})

        score_map = breakdown.model_dump()
        weakest_key = min(score_map, key=score_map.get)
        total = sum(score_map.values())

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

        interpretation = self._interpret_total(total, profile_rules or {})

        return breakdown, total, interpretation, top_issue, suggested_fix_layer

    def _apply_target_type_adjustments(
        self,
        breakdown: EvaluateScoreBreakdown,
        lower_text: str,
        target_type: str,
    ) -> EvaluateScoreBreakdown:
        if target_type != 'output':
            return breakdown

        updated = breakdown.model_copy(deep=True)
        if any(keyword in lower_text for keyword in ['结论', '建议', '风险', 'evidence', 'recommend']):
            updated.judgment_strength = min(updated.judgment_strength + 1, 5)
        else:
            updated.judgment_strength = max(updated.judgment_strength - 1, 1)

        if any(keyword in lower_text for keyword in ['步骤', '行动', 'next step', '执行', '建议']):
            updated.executability = min(updated.executability + 1, 5)

        updated.overall_stability = self._score_overall_stability(
            updated.problem_fit,
            updated.constraint_awareness,
            updated.information_density,
            updated.judgment_strength,
            updated.executability,
            updated.natural_style,
        )
        return updated

    def _apply_profile_adjustments(
        self,
        breakdown: EvaluateScoreBreakdown,
        lower_text: str,
        profile_rules: dict[str, Any],
    ) -> EvaluateScoreBreakdown:
        if not profile_rules:
            return breakdown

        updated = breakdown.model_copy(deep=True)
        criteria = profile_rules.get('criteria', [])
        if isinstance(criteria, list):
            missing_hits = 0
            for item in criteria:
                if not isinstance(item, str):
                    continue
                tokens = [token.strip().lower() for token in re.split(r'[\s,;/]+', item) if token.strip()]
                if tokens and not any(token in lower_text for token in tokens):
                    missing_hits += 1
            if missing_hits >= 1:
                updated.constraint_awareness = max(updated.constraint_awareness - 1, 1)
            if missing_hits >= 2:
                updated.judgment_strength = max(updated.judgment_strength - 1, 1)

        strictness = profile_rules.get('strictness')
        if strictness == 'strict':
            updated.information_density = max(updated.information_density - 1, 1)
            updated.executability = max(updated.executability - 1, 1)

        output_requirements = profile_rules.get('output_requirements')
        if isinstance(output_requirements, dict) and output_requirements:
            if not any(keyword in lower_text for keyword in ['格式', '结构', '输出', 'format', 'structure']):
                updated.executability = max(updated.executability - 1, 1)

        updated.overall_stability = self._score_overall_stability(
            updated.problem_fit,
            updated.constraint_awareness,
            updated.information_density,
            updated.judgment_strength,
            updated.executability,
            updated.natural_style,
        )
        return updated

    def _apply_recipe_adjustments(
        self,
        breakdown: EvaluateScoreBreakdown,
        lower_text: str,
        recipe_definition: dict[str, Any],
    ) -> EvaluateScoreBreakdown:
        if not recipe_definition:
            return breakdown

        updated = breakdown.model_copy(deep=True)
        required_inputs = recipe_definition.get('required_inputs', [])
        if isinstance(required_inputs, list) and required_inputs:
            if not any(isinstance(item, str) and item.lower() in lower_text for item in required_inputs):
                updated.constraint_awareness = max(updated.constraint_awareness - 1, 1)

        default_output_schema = recipe_definition.get('default_output_schema')
        if isinstance(default_output_schema, dict) and default_output_schema:
            if not any(keyword in lower_text for keyword in ['格式', '结构', 'schema', '字段', 'output']):
                updated.executability = max(updated.executability - 1, 1)

        supports_continue = recipe_definition.get('supports_continue')
        if supports_continue is True and not any(keyword in lower_text for keyword in ['继续', '优化', '迭代', 'continue']):
            updated.overall_stability = max(updated.overall_stability - 1, 1)

        updated.overall_stability = self._score_overall_stability(
            updated.problem_fit,
            updated.constraint_awareness,
            updated.information_density,
            updated.judgment_strength,
            updated.executability,
            updated.natural_style,
        )
        return updated

    def _score_problem_fit(self, text: str, lower_text: str) -> int:
        signals = 0
        task_keywords = ['任务', '目标', '问题', '需求', 'task', 'goal', 'objective']
        scope_keywords = ['范围', '对象', '场景', '领域', 'scope']
        constraint_keywords = ['约束', '限制', '条件', '要求', 'constraint']

        task_hits = sum(1 for k in task_keywords if k in lower_text)
        scope_hits = sum(1 for k in scope_keywords if k in lower_text)
        constraint_hits = sum(1 for k in constraint_keywords if k in lower_text)

        signals = min(task_hits, 3) + min(scope_hits, 2) + min(constraint_hits, 2)

        if signals >= 5:
            return 5
        elif signals >= 3:
            return 4
        elif signals >= 2:
            return 3
        elif signals >= 1:
            return 2
        return 1

    def _score_constraint_awareness(self, text: str, lower_text: str) -> int:
        keywords = ['约束', '限制', '边界', '前提', '失效', '条件', '不得', '禁止', '必须', '不要',
                     'constraint', 'boundary', 'limitation', 'prerequisite']
        hits = sum(1 for k in keywords if k in lower_text)

        if hits >= 5:
            return 5
        elif hits >= 3:
            return 4
        elif hits >= 2:
            return 3
        elif hits >= 1:
            return 2
        return 1

    def _score_information_density(self, text: str, lower_text: str) -> int:
        length = len(text)
        # Count meaningful paragraphs (non-empty lines)
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        para_count = len(paragraphs)

        # Detect filler phrases
        filler_phrases = ['总而言之', '综上所述', '总结来说', '需要注意的是', '值得一提的是', '众所周知']
        filler_count = sum(1 for f in filler_phrases if f in text)

        # Base score from length
        if length >= 600:
            score = 4
        elif length >= 300:
            score = 3
        else:
            score = 2

        # Adjust for density ratio (length per paragraph)
        if para_count > 0:
            avg_para_len = length / para_count
            if avg_para_len >= 60:
                score = min(score + 1, 5)
            elif avg_para_len < 30:
                score = max(score - 1, 1)

        # Penalize filler
        score = max(score - filler_count, 1)

        return min(score, 5)

    def _score_judgment_strength(self, text: str, lower_text: str) -> int:
        strong_judgment = ['关键', '本质', '优先', '风险', '判断', '核心', '根本', '决定性',
                           '最重要', '权衡', '取舍', 'critical', 'essential', 'priority']
        reasoning = ['因为', '所以', '由于', '导致', '意味着', '原因', 'because', 'therefore']

        j_hits = sum(1 for k in strong_judgment if k in lower_text)
        r_hits = sum(1 for k in reasoning if k in lower_text)
        total_hits = j_hits + r_hits

        if total_hits >= 6:
            return 5
        elif total_hits >= 4:
            return 4
        elif total_hits >= 2:
            return 3
        elif total_hits >= 1:
            return 2
        return 1

    def _score_executability(self, text: str, lower_text: str) -> int:
        action_keywords = ['下一步', '执行', '验证', '标准', '步骤', '操作', '实现', '具体',
                           'step', 'execute', 'verify', 'action', 'implement']
        structure_keywords = ['输出格式', '格式', '结构', '模板', 'format', 'template']

        a_hits = sum(1 for k in action_keywords if k in lower_text)
        s_hits = sum(1 for k in structure_keywords if k in lower_text)
        total_hits = a_hits + s_hits

        # Check for numbered steps pattern
        numbered_steps = len(re.findall(r'(?:^|\n)\s*\d+[\.\、]', text))
        total_hits += min(numbered_steps, 3)

        if total_hits >= 5:
            return 5
        elif total_hits >= 3:
            return 4
        elif total_hits >= 2:
            return 3
        elif total_hits >= 1:
            return 2
        return 1

    def _score_natural_style(self, text: str, lower_text: str) -> int:
        template_markers = ['首先', '其次', '最后', '第一', '第二', '第三',
                            '总之', '综上', 'firstly', 'secondly', 'lastly']
        ai_filler = ['希望以上', '如果您还有', '请随时', '供您参考', '祝您']

        t_hits = sum(1 for k in template_markers if k in text)
        a_hits = sum(1 for k in ai_filler if k in text)

        penalty = t_hits + a_hits * 2

        if penalty == 0:
            return 5
        elif penalty <= 1:
            return 4
        elif penalty <= 3:
            return 3
        elif penalty <= 5:
            return 2
        return 1

    def _score_overall_stability(self, *dimension_scores: int) -> int:
        scores = list(dimension_scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)

        # Overall stability is dragged down by the weakest dimension
        if min_score >= 4 and avg_score >= 4.0:
            return 5
        elif min_score >= 3 and avg_score >= 3.5:
            return 4
        elif min_score >= 2 and avg_score >= 3.0:
            return 3
        elif min_score >= 2:
            return 2
        return 1

    def _interpret_total(self, total: int, profile_rules: dict[str, Any]) -> str:
        suffix = ''
        pass_threshold = profile_rules.get('pass_threshold')
        if isinstance(pass_threshold, (int, float)):
            max_score = 35
            actual_ratio = total / max_score
            status_text = '达到' if actual_ratio >= float(pass_threshold) else '未达到'
            suffix = f' 当前结果{status_text} profile 设定的通过阈值。'
        for low, high, interpretation in SCORE_INTERPRETATIONS:
            if low <= total <= high:
                return interpretation + suffix
        return SCORE_INTERPRETATIONS[-1][2] + suffix
