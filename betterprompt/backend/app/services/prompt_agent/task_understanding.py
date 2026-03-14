from app.schemas.prompt_agent import GeneratePromptRequest, PromptDiagnosis, PromptTaskType

# Weighted keyword groups for each task type.
# Each entry is (keyword, weight). Higher weight = stronger signal.
TASK_KEYWORD_MAP: dict[PromptTaskType, list[tuple[str, float]]] = {
    'algorithm_analysis': [
        ('算法', 3), ('题解', 3), ('leetcode', 3), ('时间复杂度', 2), ('空间复杂度', 2),
        ('排序', 1.5), ('搜索', 1), ('动态规划', 2), ('贪心', 1.5), ('递归', 1.5),
        ('数据结构', 2), ('二叉树', 2), ('链表', 1.5), ('图论', 2), ('dfs', 2), ('bfs', 2),
    ],
    'source_code_analysis': [
        ('代码', 2), ('源码', 3), ('函数', 2), ('module', 2), ('code', 2),
        ('重构', 2), ('review', 2), ('bug', 2), ('调试', 1.5), ('debug', 2),
        ('class', 1.5), ('方法', 1), ('接口实现', 2), ('类型', 1), ('编译', 1.5),
    ],
    'architecture_spec': [
        ('架构', 3), ('系统设计', 3), ('技术方案', 3), ('微服务', 2), ('分布式', 2),
        ('高可用', 2), ('扩展性', 2), ('技术选型', 2), ('部署', 1.5), ('基础设施', 2),
        ('api设计', 2), ('数据库设计', 2), ('消息队列', 1.5), ('缓存', 1.5),
    ],
    'business_insight': [
        ('商业', 3), ('行业', 2), ('增长', 2), ('公司', 1.5), ('竞争', 2),
        ('市场', 2), ('营收', 2), ('盈利', 2), ('商业模式', 3), ('投资', 2),
        ('估值', 2), ('a股', 2), ('股票', 2), ('选股', 2), ('财报', 2),
        ('融资', 1.5), ('战略', 2), ('供应链', 1.5),
    ],
    'product_design': [
        ('产品', 2), ('prd', 3), ('需求', 2), ('功能', 1.5), ('用户故事', 3),
        ('原型', 2), ('交互', 2), ('用户体验', 2), ('ux', 2), ('ui', 1.5),
        ('产品设计', 3), ('功能规划', 3), ('用户需求', 3), ('产品经理', 2),
        ('mvp', 2), ('迭代', 1.5), ('需求分析', 3),
    ],
    'data_analysis': [
        ('数据分析', 3), ('报表', 2), ('指标', 2), ('可视化', 2), ('dashboard', 2),
        ('sql', 2), ('留存', 2), ('转化率', 2), ('漏斗', 2), ('ab测试', 2),
        ('数据', 1.5), ('统计', 1.5), ('分析报告', 2), ('埋点', 2), ('数据挖掘', 2),
        ('用户画像', 2), ('cohort', 2),
    ],
    'education_learning': [
        ('教学', 3), ('学习', 2), ('课程', 3), ('解释', 1.5), ('教程', 3),
        ('入门', 2), ('概念', 1.5), ('原理', 1.5), ('知识点', 2), ('培训', 2),
        ('辅导', 2), ('学生', 2), ('老师', 2), ('讲解', 2), ('科普', 2),
    ],
    'creative_marketing': [
        ('营销', 3), ('文案', 3), ('品牌', 3), ('创意', 2), ('策划', 2),
        ('广告', 3), ('slogan', 3), ('推广', 2), ('传播', 2), ('内容运营', 2),
        ('社交媒体', 2), ('种草', 2), ('带货', 2), ('kol', 1.5), ('投放', 2),
    ],
    'writing_generation': [
        ('写作', 3), ('改写', 3), ('润色', 3), ('文章', 2), ('博客', 2),
        ('翻译', 2), ('摘要', 2), ('总结', 1.5), ('邮件', 2), ('报告', 1.5),
        ('小说', 2), ('故事', 1.5), ('作文', 2), ('论文', 2),
    ],
    'general_deep_analysis': [
        ('分析', 1), ('深度', 1), ('研究', 1), ('思考', 1), ('探讨', 1),
    ],
}


class TaskUnderstandingEngine:
    def understand(self, request: GeneratePromptRequest) -> PromptDiagnosis:
        text = request.user_input.lower()
        output_type = request.artifact_type

        scores: dict[PromptTaskType, float] = {}
        for task_type, keywords in TASK_KEYWORD_MAP.items():
            score = 0.0
            for keyword, weight in keywords:
                if keyword in text:
                    score += weight
            scores[task_type] = score

        # Remove the fallback type from competition — it only wins when nothing else matches
        fallback_score = scores.pop('general_deep_analysis', 0.0)
        best_type: PromptTaskType = 'general_deep_analysis'
        best_score = 0.0

        for task_type, score in scores.items():
            if score > best_score:
                best_score = score
                best_type = task_type

        # Use fallback if no type scored above threshold
        if best_score < 2.0:
            best_type = 'general_deep_analysis'

        return PromptDiagnosis(
            task_type=best_type,
            output_type=output_type,
            quality_target=request.output_preference,
            failure_modes=[],
        )
