import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { PromptAgentPageShell } from '@/features/prompt-agent/page-shell';

const basename = import.meta.env.BASE_URL || '/';

export function AppRouter() {
  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route path="/" element={<PromptAgentPageShell />} />
        <Route path="/prompt-agent" element={<PromptAgentPageShell />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
