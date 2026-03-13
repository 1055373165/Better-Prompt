import { Copy, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { DiagnosisCard } from './diagnosis-card';
import { ScoreCard } from './score-card';
import type {
  ContinuePromptResponse,
  DebugPromptResponse,
  EvaluatePromptResponse,
  GeneratePromptResponse,
  PromptAgentMode,
} from '../types';

const ARTIFACT_TYPE_LABELS: Record<string, string> = {
  system_prompt: '系统提示词',
  task_prompt: '一次性任务 Prompt',
  analysis_workflow: '分析工作流 Prompt',
  conversation_prompt: '对话协作 Prompt',
};

const FIX_LAYER_LABELS: Record<string, string> = {
  problem_redefinition: '问题重定义层',
  cognitive_drill_down: '认知下钻层',
  key_point_priority: '关键点优先层',
  criticality: '批判性分析层',
  information_density: '信息密度层',
  boundary_validation: '边界验证层',
  executability: '可执行性层',
  style_control: '风格控制层',
};

interface ResultPanelProps {
  mode: PromptAgentMode;
  generateResult: GeneratePromptResponse | null;
  debugResult: DebugPromptResponse | null;
  evaluateResult: EvaluatePromptResponse | null;
  continueResult: ContinuePromptResponse | null;
  onCopy: (content: string) => void;
}

export function ResultPanel({
  mode,
  generateResult,
  debugResult,
  evaluateResult,
  continueResult,
  onCopy,
}: ResultPanelProps) {
  const continueSourceLabel = continueResult?.source_mode === 'generate'
    ? 'Generate'
    : continueResult?.source_mode === 'debug'
      ? 'Debug'
      : 'Evaluate';

  if (mode === 'generate' && generateResult) {
    return (
      <div className="space-y-4">
        {generateResult.diagnosis_visible && generateResult.diagnosis && (
          <DiagnosisCard diagnosis={generateResult.diagnosis} />
        )}
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">
              生成后的{ARTIFACT_TYPE_LABELS[generateResult.artifact_type] ?? 'Prompt'}
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-slate-100 hover:text-slate-900" onClick={() => onCopy(generateResult.final_prompt)}>
              <Copy className="mr-2 h-4 w-4" />复制
            </Button>
          </CardHeader>
          <CardContent>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-sm leading-7 whitespace-pre-wrap text-slate-800">
              {generateResult.final_prompt}
            </div>
            <div className="mt-4 text-xs text-slate-500">
              优化策略：{generateResult.optimization_strategy}
            </div>
            <div className="mt-2 text-xs text-slate-500">
              产物类型：{ARTIFACT_TYPE_LABELS[generateResult.artifact_type] ?? generateResult.artifact_type}
            </div>
            <div className="mt-2 text-xs text-slate-500">
              生成后端：
              {generateResult.generation_backend === 'llm'
                ? ` LLM${generateResult.generation_model ? ` · ${generateResult.generation_model}` : ''}`
                : ' 模板回退'}
            </div>
            {generateResult.prompt_only && (
              <div className="mt-2 text-xs text-slate-500">
                当前返回按“仅输出 Prompt”模式组织。
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (mode === 'debug' && debugResult) {
    return (
      <div className="space-y-4">
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">调试诊断</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm md:grid-cols-2">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">最高风险失败模式</div>
              <div className="mt-2 font-medium text-slate-900">{debugResult.top_failure_mode}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">优势</div>
              <div className="mt-2 leading-6 text-slate-700">{debugResult.strengths.join(' / ')}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">弱点</div>
              <div className="mt-2 leading-6 text-slate-700">{debugResult.weaknesses.join(' / ')}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">建议补强控制层</div>
              <div className="mt-2 leading-6 text-slate-700">
                {debugResult.missing_control_layers.map((layer) => FIX_LAYER_LABELS[layer] ?? layer).join(' / ') || '—'}
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">修复后 Prompt</CardTitle>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-slate-100 hover:text-slate-900" onClick={() => onCopy(debugResult.fixed_prompt)}>
              <Copy className="mr-2 h-4 w-4" />复制
            </Button>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">最小修复动作</div>
              <div className="mt-2 leading-6 text-slate-700">{debugResult.minimal_fix.join(' / ')}</div>
            </div>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 whitespace-pre-wrap leading-7 text-slate-800">{debugResult.fixed_prompt}</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (mode === 'evaluate' && evaluateResult) {
    return (
      <div className="space-y-4">
        <ScoreCard scoreBreakdown={evaluateResult.score_breakdown} totalScore={evaluateResult.total_score} />
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">评估建议</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">最主要缺陷</div>
              <div className="mt-2 font-medium text-slate-900">{evaluateResult.top_issue}</div>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50/80 p-4">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">建议优先修复层</div>
              <div className="mt-2 font-medium text-slate-900">{FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}</div>
            </div>
            <div className="rounded-[1.5rem] border border-sky-200/80 bg-sky-50/80 p-4 text-slate-600">
              建议先围绕“{FIX_LAYER_LABELS[evaluateResult.suggested_fix_layer] ?? evaluateResult.suggested_fix_layer}”修一轮，再使用 Continue Optimization 继续迭代。
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (continueResult) {
    return (
      <div className="space-y-4">
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-900">结果关系</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-500">
            <div>基础结果来源：{continueSourceLabel}</div>
            <div>当前显示内容：{continueResult.result_label}</div>
            <div>本轮优化目标：{continueResult.optimization_goal}</div>
          </CardContent>
        </Card>
        <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-900">
              <Wand2 className="h-4 w-4" />{continueResult.result_label}
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-slate-600 hover:bg-slate-100 hover:text-slate-900" onClick={() => onCopy(continueResult.refined_result)}>
              <Copy className="mr-2 h-4 w-4" />复制
            </Button>
          </CardHeader>
          <CardContent>
            <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-sm whitespace-pre-wrap leading-7 text-slate-800">
              {continueResult.refined_result}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="rounded-[1.75rem] border border-dashed border-slate-300 bg-white/60 p-10 text-center text-sm text-slate-500 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.16)] backdrop-blur-xl">
      输入你的需求，Prompt Agent 会先帮你理解意图，再返回更高质量的 Prompt 结果。
    </div>
  );
}
