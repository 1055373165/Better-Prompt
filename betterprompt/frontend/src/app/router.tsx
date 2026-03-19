import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { PromptAgentPageShell } from '@/features/prompt-agent/page-shell';
import { SessionHistoryPageShell } from '@/features/session-history/page-shell';
import { WorkspaceShellPageShell } from '@/features/workspace-shell/page-shell';
import { WorkflowLibraryPageShell } from '@/features/workflow-library/page-shell';

const basename = import.meta.env.BASE_URL || '/';

export function AppRouter() {
  return (
    <BrowserRouter
      basename={basename}
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/prompt-agent" replace />} />
        <Route path="/prompt-agent" element={<PromptAgentPageShell />} />
        <Route path="/workspaces" element={<WorkspaceShellPageShell />} />
        <Route path="/library" element={<WorkflowLibraryPageShell />} />
        <Route path="/sessions" element={<SessionHistoryPageShell />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
