import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  {
    to: '/prompt-agent',
    label: 'Prompt Agent',
    description: 'Workbench',
  },
  {
    to: '/workspaces',
    label: 'Workspaces',
    description: 'V3 Shell',
  },
  {
    to: '/library',
    label: 'Workflow Library',
    description: 'V2 Assets',
  },
  {
    to: '/sessions',
    label: 'Sessions',
    description: 'Runs History',
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-[var(--bp-line)] bg-[rgba(251,247,241,0.84)] backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-[92rem] flex-col gap-4 px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="bp-overline">BetterPrompt</div>
            <div className="mt-2 flex items-center gap-3">
              <div className="text-xl font-semibold tracking-tight text-[var(--bp-ink)]">Prompt Operating Surface</div>
              <div className="hidden rounded-full border border-[rgba(162,74,53,0.18)] bg-[rgba(162,74,53,0.1)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--bp-clay)] md:inline-flex">
                V2 live · V3 shell
              </div>
            </div>
          </div>

          <nav className="flex flex-wrap gap-2">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => `rounded-[1.2rem] border px-4 py-3 transition ${
                  isActive
                    ? 'border-[rgba(31,36,45,0.18)] bg-[linear-gradient(135deg,rgba(30,38,52,0.98),rgba(55,65,78,0.98))] text-[#f8f3eb] shadow-[0_18px_42px_-28px_rgba(24,25,27,0.5)]'
                    : 'border-[var(--bp-line)] bg-[rgba(255,255,255,0.72)] text-[var(--bp-ink)] hover:border-[var(--bp-line-strong)] hover:bg-[rgba(255,255,255,0.9)]'
                }`}
              >
                <div className="text-sm font-semibold">{item.label}</div>
                <div className={`mt-1 text-xs ${item.to === '/library' ? 'tracking-[0.12em]' : ''}`}>{item.description}</div>
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>{children}</main>
    </div>
  );
}
