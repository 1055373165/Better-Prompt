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

export interface GeneratePromptResponse {
  mode: 'generate';
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
  score_breakdown: EvaluateScoreBreakdown;
  total_score: number;
  total_interpretation: string;
  top_issue: string;
  suggested_fix_layer: string;
}

export interface ContinuePromptResponse {
  mode: PromptAgentResponseMode;
  source_mode: PromptAgentMode;
  optimization_goal: string;
  refined_result: string;
  result_label: string;
  suggested_next_actions: string[];
  generation_backend: 'llm' | 'template';
  generation_model: string | null;
}
