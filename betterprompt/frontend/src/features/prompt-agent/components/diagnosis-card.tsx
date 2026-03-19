import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { PromptDiagnosis } from '../types';

const TASK_TYPE_LABELS: Record<string, string> = {
  algorithm_analysis: '算法分析',
  source_code_analysis: '源码分析',
  architecture_spec: '架构方案',
  business_insight: '商业洞察',
  product_design: '产品设计',
  data_analysis: '数据分析',
  education_learning: '教学学习',
  creative_marketing: '创意营销',
  document_translation: '文档翻译',
  general_deep_analysis: '通用深度分析',
  writing_generation: '写作生成',
  other: '其他',
};

const OUTPUT_TYPE_LABELS: Record<string, string> = {
  system_prompt: '系统提示词',
  task_prompt: '任务 Prompt',
  analysis_workflow: '分析工作流 Prompt',
  conversation_prompt: '对话协作 Prompt',
};

const QUALITY_TARGET_LABELS: Record<string, string> = {
  balanced: '平衡',
  depth: '深度',
  execution: '可执行性',
  natural: '自然表达',
};

const FAILURE_MODE_LABELS: Record<string, string> = {
  surface_restatement: '停留在表层复述',
  template_tone: '模板腔过重',
  correct_but_empty: '正确但空洞',
  pseudo_depth: '伪深度',
  uncritical_praise: '缺少批判性',
  no_priority_judgment: '缺少优先级判断',
  not_executable: '不可执行',
  style_instability: '风格不稳定',
};

export function DiagnosisCard({ diagnosis }: { diagnosis: PromptDiagnosis }) {
  return (
    <Card className="rounded-[1.7rem] border-[var(--bp-line)] bg-[rgba(255,252,247,0.78)] shadow-[var(--bp-shadow-soft)]">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-[var(--bp-ink)]">诊断摘要</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm md:grid-cols-2">
        <div className="bp-meta-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">任务类型</div>
          <div className="mt-2 font-semibold text-[var(--bp-ink)]">{TASK_TYPE_LABELS[diagnosis.task_type] ?? diagnosis.task_type}</div>
        </div>
        <div className="bp-meta-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">输出产物</div>
          <div className="mt-2 font-semibold text-[var(--bp-ink)]">{OUTPUT_TYPE_LABELS[diagnosis.output_type] ?? diagnosis.output_type}</div>
        </div>
        <div className="bp-meta-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">质量目标</div>
          <div className="mt-2 font-semibold text-[var(--bp-ink)]">{QUALITY_TARGET_LABELS[diagnosis.quality_target] ?? diagnosis.quality_target}</div>
        </div>
        <div className="bp-meta-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-ink-soft)]">高风险失败模式</div>
          <div className="mt-2 text-sm leading-6 text-[var(--bp-ink-soft)]">
            {diagnosis.failure_modes.map((mode) => FAILURE_MODE_LABELS[mode] ?? mode).join(' / ') || '—'}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
