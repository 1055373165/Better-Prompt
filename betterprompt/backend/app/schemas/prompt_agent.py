from typing import Literal

from pydantic import BaseModel, Field


PromptAgentMode = Literal['generate', 'debug', 'evaluate', 'continue']
PromptOutputPreference = Literal['balanced', 'depth', 'execution', 'natural']
PromptArtifactType = Literal['system_prompt', 'task_prompt', 'analysis_workflow', 'conversation_prompt']
PromptGenerateBackend = Literal['llm', 'template']
PromptTaskType = Literal[
    'algorithm_analysis',
    'source_code_analysis',
    'architecture_spec',
    'business_insight',
    'general_deep_analysis',
    'writing_generation',
    'document_translation',
    'product_design',
    'data_analysis',
    'education_learning',
    'creative_marketing',
]
PromptFailureMode = Literal[
    'surface_restatement',
    'template_tone',
    'correct_but_empty',
    'pseudo_depth',
    'uncritical_praise',
    'no_priority_judgment',
    'not_executable',
    'style_instability',
]
PromptControlModule = Literal[
    'problem_redefinition',
    'cognitive_drill_down',
    'key_point_priority',
    'criticality',
    'information_density',
    'boundary_validation',
    'executability',
    'style_control',
]


class PromptDiagnosis(BaseModel):
    task_type: PromptTaskType
    output_type: str
    quality_target: str
    failure_modes: list[PromptFailureMode] = Field(default_factory=list)


class PromptIterationRef(BaseModel):
    session_id: str | None = None
    iteration_id: str | None = None


class WorkflowAssetRefs(BaseModel):
    session_id: str | None = None
    domain_workspace_id: str | None = None
    subject_id: str | None = None
    agent_monitor_id: str | None = None
    trigger_kind: str | None = Field(default=None, min_length=1, max_length=40)
    source_asset_version_id: str | None = None
    context_pack_version_ids: list[str] = Field(default_factory=list)
    evaluation_profile_version_id: str | None = None
    workflow_recipe_version_id: str | None = None
    run_preset_id: str | None = None


class GeneratePromptRequest(WorkflowAssetRefs):
    user_input: str = Field(..., min_length=1)
    show_diagnosis: bool = True
    output_preference: PromptOutputPreference = 'balanced'
    artifact_type: PromptArtifactType = 'task_prompt'
    prompt_only: bool = False
    context_notes: str | None = None


class GeneratePromptResponse(BaseModel):
    mode: PromptAgentMode = 'generate'
    iteration: PromptIterationRef = Field(default_factory=PromptIterationRef)
    diagnosis: PromptDiagnosis | None = None
    final_prompt: str
    artifact_type: PromptArtifactType = 'task_prompt'
    applied_modules: list[PromptControlModule] = Field(default_factory=list)
    optimization_strategy: str
    optimized_input: str
    prompt_only: bool = False
    diagnosis_visible: bool = True
    generation_backend: PromptGenerateBackend = 'template'
    generation_model: str | None = None


class DebugPromptRequest(WorkflowAssetRefs):
    original_task: str = Field(..., min_length=1)
    current_prompt: str = Field(..., min_length=1)
    current_output: str = Field(..., min_length=1)
    output_preference: PromptOutputPreference = 'balanced'


class DebugPromptResponse(BaseModel):
    mode: PromptAgentMode = 'debug'
    iteration: PromptIterationRef = Field(default_factory=PromptIterationRef)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    top_failure_mode: PromptFailureMode
    missing_control_layers: list[PromptControlModule] = Field(default_factory=list)
    minimal_fix: list[str] = Field(default_factory=list)
    fixed_prompt: str


class EvaluatePromptRequest(WorkflowAssetRefs):
    target_text: str = Field(..., min_length=1)
    target_type: Literal['prompt', 'output']


class EvaluateScoreBreakdown(BaseModel):
    problem_fit: int = Field(..., ge=1, le=5)
    constraint_awareness: int = Field(..., ge=1, le=5)
    information_density: int = Field(..., ge=1, le=5)
    judgment_strength: int = Field(..., ge=1, le=5)
    executability: int = Field(..., ge=1, le=5)
    natural_style: int = Field(..., ge=1, le=5)
    overall_stability: int = Field(..., ge=1, le=5)


class EvaluatePromptResponse(BaseModel):
    mode: PromptAgentMode = 'evaluate'
    iteration: PromptIterationRef = Field(default_factory=PromptIterationRef)
    score_breakdown: EvaluateScoreBreakdown
    total_score: int
    total_interpretation: str
    top_issue: str
    suggested_fix_layer: PromptControlModule


class ContinuePromptRequest(WorkflowAssetRefs):
    parent_iteration_id: str | None = None
    previous_result: str = Field(..., min_length=1)
    optimization_goal: str = Field(..., min_length=1)
    mode: Literal['generate', 'debug', 'evaluate']
    context_notes: str | None = None


class ContinuePromptResponse(BaseModel):
    mode: PromptAgentMode = 'continue'
    iteration: PromptIterationRef = Field(default_factory=PromptIterationRef)
    source_mode: Literal['generate', 'debug', 'evaluate']
    optimization_goal: str
    refined_result: str
    result_label: str = '优化后版本'
    suggested_next_actions: list[str] = Field(default_factory=list)
    generation_backend: PromptGenerateBackend = 'template'
    generation_model: str | None = None
