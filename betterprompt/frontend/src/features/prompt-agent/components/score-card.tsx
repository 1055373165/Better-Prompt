import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { EvaluateScoreBreakdown } from '../types';

const SCORE_LABELS: Record<keyof EvaluateScoreBreakdown, string> = {
  problem_fit: '问题拟合度',
  constraint_awareness: '约束意识',
  information_density: '信息密度',
  judgment_strength: '判断强度',
  executability: '可执行性',
  natural_style: '自然表达',
  overall_stability: '整体稳定性',
};

export function ScoreCard({ scoreBreakdown, totalScore }: { scoreBreakdown: EvaluateScoreBreakdown; totalScore: number }) {
  return (
    <Card className="rounded-[1.75rem] border-white/70 bg-white/75 shadow-[0_20px_70px_-42px_rgba(15,23,42,0.22)] backdrop-blur-xl">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-slate-900">评估结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="rounded-[1.5rem] border border-slate-200/80 bg-[linear-gradient(135deg,#0f172a,#1e293b)] px-5 py-4 text-white">
          <div className="text-3xl font-semibold tracking-tight">{totalScore}</div>
          <div className="mt-1 text-xs text-slate-300">总分由 7 个维度累计，单项满分 5 分。</div>
        </div>
        <div className="space-y-2 text-sm text-slate-500">
          {Object.entries(scoreBreakdown).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between rounded-2xl border border-slate-200/80 bg-slate-50/80 px-4 py-3">
              <span>{SCORE_LABELS[key as keyof EvaluateScoreBreakdown] ?? key}</span>
              <span className="font-medium text-slate-900">{value}/5</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
