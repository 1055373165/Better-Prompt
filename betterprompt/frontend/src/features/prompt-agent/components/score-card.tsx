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
    <Card className="rounded-[1.7rem] border-[var(--bp-line)] bg-[rgba(255,252,247,0.78)] shadow-[var(--bp-shadow-soft)]">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-[var(--bp-ink)]">评估结果</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-[1.5rem] border border-[rgba(31,36,45,0.16)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] px-5 py-5 text-[#f8f3eb]">
          <div className="bp-overline text-[#d8c8ba]">Total Score</div>
          <div className="mt-3 text-4xl font-semibold tracking-tight tabular-nums">{totalScore}</div>
          <div className="mt-2 text-sm leading-6 text-[#d4d8df]">总分由 7 个维度累计，单项满分 5 分。</div>
        </div>
        <div className="space-y-2 text-sm">
          {Object.entries(scoreBreakdown).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between rounded-[1.15rem] border border-[var(--bp-line)] bg-[rgba(255,255,255,0.66)] px-4 py-3">
              <span className="text-[var(--bp-ink-soft)]">{SCORE_LABELS[key as keyof EvaluateScoreBreakdown] ?? key}</span>
              <span className="font-semibold tabular-nums text-[var(--bp-ink)]">{value}/5</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
