export type PromptAgentMode = 'generate' | 'debug' | 'evaluate';
export type PromptAgentResponseMode = PromptAgentMode | 'continue';
export type PromptArtifactType = 'system_prompt' | 'task_prompt' | 'analysis_workflow' | 'conversation_prompt';
export type GenerateOutputPreference = 'balanced' | 'depth' | 'execution' | 'natural';
export type EvaluateTargetType = 'prompt' | 'output';

export interface GenerateDraft {
  userInput: string;
  showDiagnosis: boolean;
  promptOnly: boolean;
  artifactType: PromptArtifactType;
  outputPreference: GenerateOutputPreference;
}

export interface DebugDraft {
  originalTask: string;
  currentPrompt: string;
  currentOutput: string;
}

export interface EvaluateDraft {
  targetText: string;
  targetType: EvaluateTargetType;
}

export interface PromptDiagnosis {
  task_type: string;
  output_type: string;
  quality_target: string;
  failure_modes: string[];
}

export interface PromptIterationRef {
  session_id: string | null;
  iteration_id: string | null;
}

export interface WorkflowAssetVersionSummary {
  id: string;
  version_number: number;
  change_summary: string | null;
  created_at: string;
}

export interface ContextPackVersionDetail extends WorkflowAssetVersionSummary {
  payload: Record<string, unknown>;
  source_iteration_id: string | null;
}

export interface ContextPackSummary {
  id: string;
  name: string;
  description: string | null;
  tags: string[];
  current_version: WorkflowAssetVersionSummary | null;
  updated_at: string;
}

export interface ContextPackDetail extends ContextPackSummary {
  current_version: ContextPackVersionDetail | null;
  created_at: string;
  archived_at: string | null;
}

export interface EvaluationProfileVersionDetail extends WorkflowAssetVersionSummary {
  rules: Record<string, unknown>;
}

export interface EvaluationProfileSummary {
  id: string;
  name: string;
  description: string | null;
  current_version: WorkflowAssetVersionSummary | null;
  updated_at: string;
}

export interface EvaluationProfileDetail extends EvaluationProfileSummary {
  current_version: EvaluationProfileVersionDetail | null;
  created_at: string;
  archived_at: string | null;
}

export interface WorkflowRecipeVersionDetail extends WorkflowAssetVersionSummary {
  definition: Record<string, unknown>;
  source_iteration_id: string | null;
}

export interface WorkflowRecipeSummary {
  id: string;
  name: string;
  description: string | null;
  domain_hint: string | null;
  current_version: WorkflowAssetVersionSummary | null;
  updated_at: string;
}

export interface WorkflowRecipeDetail extends WorkflowRecipeSummary {
  current_version: WorkflowRecipeVersionDetail | null;
  created_at: string;
  archived_at: string | null;
}

export interface RunPresetSummary {
  id: string;
  name: string;
  description: string | null;
  last_used_at: string | null;
  updated_at: string;
}

export interface RunPresetDetail extends RunPresetSummary {
  definition: Record<string, unknown>;
  created_at: string;
  archived_at: string | null;
}

export interface WorkflowRefSelection {
  context_pack_version_ids: string[];
  evaluation_profile_version_id: string | null;
  workflow_recipe_version_id: string | null;
  run_preset_id: string | null;
}

export interface WorkspaceScopeSelection {
  domain_workspace_id: string | null;
  subject_id: string | null;
  domain_workspace_label: string | null;
  subject_label: string | null;
}

export interface RunContextSnapshot {
  launch_label: string;
  refs: WorkflowRefSelection;
  workspace_scope: WorkspaceScopeSelection | null;
  workflow_recipe_label: string | null;
  evaluation_profile_label: string | null;
  context_pack_labels: string[];
  run_preset_label: string | null;
}

export interface DomainWorkspaceSummary {
  id: string;
  workspace_type: string;
  name: string;
  description: string | null;
  status: string;
  updated_at: string;
}

export interface DomainWorkspaceDetail extends DomainWorkspaceSummary {
  config: Record<string, unknown>;
  subject_count: number;
  source_count: number;
  report_count: number;
  created_at: string;
  archived_at: string | null;
}

export interface WorkspaceSubjectSummary {
  id: string;
  workspace_id: string;
  subject_type: string;
  external_key: string | null;
  display_name: string;
  status: string;
  updated_at: string;
}

export interface WorkspaceSubjectDetail extends WorkspaceSubjectSummary {
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ResearchSourceSummary {
  id: string;
  workspace_id: string;
  subject_id: string | null;
  source_type: string;
  canonical_uri: string | null;
  title: string | null;
  source_timestamp: string | null;
  ingest_status: string;
  updated_at: string;
}

export interface ResearchSourceDetail extends ResearchSourceSummary {
  content: Record<string, unknown>;
  created_at: string;
}

export interface ResearchReportVersionSummary {
  id: string;
  version_number: number;
  summary_text: string | null;
  confidence_score: number | null;
  created_at: string;
}

export interface ResearchReportVersionDetail extends ResearchReportVersionSummary {
  content: Record<string, unknown>;
  source_session_id: string | null;
  source_iteration_id: string | null;
}

export interface ResearchReportSummary {
  id: string;
  workspace_id: string;
  subject_id: string | null;
  report_type: string;
  title: string;
  status: string;
  latest_version: ResearchReportVersionSummary | null;
  updated_at: string;
}

export interface ResearchReportDetail extends ResearchReportSummary {
  latest_version: ResearchReportVersionDetail | null;
  created_at: string;
  archived_at: string | null;
}

export interface GeneratePromptResponse {
  mode: 'generate';
  iteration: PromptIterationRef;
  diagnosis: PromptDiagnosis | null;
  final_prompt: string;
  artifact_type: PromptArtifactType;
  applied_modules: string[];
  optimization_strategy: string;
  optimized_input: string;
  prompt_only: boolean;
  diagnosis_visible: boolean;
  generation_backend: 'llm' | 'template';
  generation_model: string | null;
}

export interface DebugPromptResponse {
  mode: 'debug';
  iteration: PromptIterationRef;
  strengths: string[];
  weaknesses: string[];
  top_failure_mode: string;
  missing_control_layers: string[];
  minimal_fix: string[];
  fixed_prompt: string;
}

export interface EvaluateScoreBreakdown {
  problem_fit: number;
  constraint_awareness: number;
  information_density: number;
  judgment_strength: number;
  executability: number;
  natural_style: number;
  overall_stability: number;
}

export interface EvaluatePromptResponse {
  mode: 'evaluate';
  iteration: PromptIterationRef;
  score_breakdown: EvaluateScoreBreakdown;
  total_score: number;
  total_interpretation: string;
  top_issue: string;
  suggested_fix_layer: string;
}

export interface ContinuePromptResponse {
  mode: 'continue';
  iteration: PromptIterationRef;
  source_mode: PromptAgentMode;
  optimization_goal: string;
  refined_result: string;
  result_label: string;
  suggested_next_actions: string[];
  generation_backend: 'llm' | 'template';
  generation_model: string | null;
}

export type RunPresetLaunchResponse =
  | GeneratePromptResponse
  | DebugPromptResponse
  | EvaluatePromptResponse
  | ContinuePromptResponse;
