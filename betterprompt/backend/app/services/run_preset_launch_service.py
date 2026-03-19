from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_asset_version import PromptAssetVersion
from app.models.run_preset import RunPreset
from app.models.workflow_recipe_version import WorkflowRecipeVersion
from app.schemas.prompt_agent import (
    ContinuePromptRequest,
    DebugPromptRequest,
    EvaluatePromptRequest,
    GeneratePromptRequest,
)
from app.schemas.workflow_asset import RunPresetLaunchRequest
from app.services.prompt_agent.errors import PromptAgentRequestError


def _load_json_dict(raw_value: str | None) -> dict[str, Any]:
    if not raw_value:
        return {}
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class RunPresetLaunchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_launch_request(
        self,
        run_preset_id: str,
        request: RunPresetLaunchRequest,
    ) -> tuple[str, GeneratePromptRequest | DebugPromptRequest | EvaluatePromptRequest | ContinuePromptRequest]:
        preset = await self._require_preset(run_preset_id)
        definition = _load_json_dict(preset.definition_json)
        run_settings = definition.get('run_settings', {})
        if not isinstance(run_settings, dict):
            raise PromptAgentRequestError(
                'RUN_PRESET_LAUNCH_INVALID',
                'run_settings must be an object',
            )
        overrides = request.run_settings_override or {}
        launch_mode = await self._resolve_launch_mode(request.mode_override, definition)
        effective_settings = {**run_settings, **overrides}
        source_prompt = await self._resolve_source_prompt(definition.get('prompt_asset_version_id'))

        common = {
            'session_id': request.session_id or self._as_str(effective_settings.get('session_id')),
            'domain_workspace_id': request.domain_workspace_id,
            'subject_id': request.subject_id,
            'source_asset_version_id': definition.get('prompt_asset_version_id'),
            'context_pack_version_ids': self._as_str_list(definition.get('context_pack_version_ids')),
            'evaluation_profile_version_id': self._as_str(definition.get('evaluation_profile_version_id')),
            'workflow_recipe_version_id': self._as_str(definition.get('workflow_recipe_version_id')),
            'run_preset_id': preset.id,
        }

        try:
            if launch_mode == 'generate':
                user_input = (
                    request.user_input_override
                    or self._as_str(effective_settings.get('user_input'))
                    or source_prompt
                )
                if not user_input:
                    raise PromptAgentRequestError(
                        'RUN_PRESET_LAUNCH_INVALID',
                        'generate launch requires user_input or prompt asset content',
                    )
                return launch_mode, GeneratePromptRequest(
                    user_input=user_input,
                    show_diagnosis=self._as_bool(effective_settings.get('show_diagnosis'), default=True),
                    output_preference=self._as_str(effective_settings.get('output_preference')) or 'balanced',
                    artifact_type=self._as_str(effective_settings.get('artifact_type')) or 'task_prompt',
                    prompt_only=self._as_bool(effective_settings.get('prompt_only'), default=False),
                    context_notes=self._as_str(effective_settings.get('context_notes')),
                    **common,
                )

            if launch_mode == 'debug':
                original_task = (
                    self._as_str(effective_settings.get('original_task'))
                    or request.user_input_override
                )
                current_prompt = (
                    self._as_str(effective_settings.get('current_prompt'))
                    or source_prompt
                )
                current_output = self._as_str(effective_settings.get('current_output'))
                if not original_task or not current_prompt or not current_output:
                    raise PromptAgentRequestError(
                        'RUN_PRESET_LAUNCH_INVALID',
                        'debug launch requires original_task, current_prompt, and current_output',
                    )
                return launch_mode, DebugPromptRequest(
                    original_task=original_task,
                    current_prompt=current_prompt,
                    current_output=current_output,
                    output_preference=self._as_str(effective_settings.get('output_preference')) or 'balanced',
                    **common,
                )

            if launch_mode == 'evaluate':
                target_text = (
                    request.user_input_override
                    or self._as_str(effective_settings.get('target_text'))
                    or source_prompt
                )
                if not target_text:
                    raise PromptAgentRequestError(
                        'RUN_PRESET_LAUNCH_INVALID',
                        'evaluate launch requires target_text or prompt asset content',
                    )
                target_type = self._as_str(effective_settings.get('target_type'))
                if not target_type:
                    target_type = 'prompt' if source_prompt and target_text == source_prompt else 'output'
                return launch_mode, EvaluatePromptRequest(
                    target_text=target_text,
                    target_type=target_type,
                    **common,
                )

            previous_result = (
                self._as_str(effective_settings.get('previous_result'))
                or request.user_input_override
            )
            optimization_goal = self._as_str(effective_settings.get('optimization_goal'))
            source_mode = self._as_str(effective_settings.get('source_mode')) or 'generate'
            if not previous_result or not optimization_goal:
                raise PromptAgentRequestError(
                    'RUN_PRESET_LAUNCH_INVALID',
                    'continue launch requires previous_result and optimization_goal',
                )
            return launch_mode, ContinuePromptRequest(
                previous_result=previous_result,
                optimization_goal=optimization_goal,
                mode=source_mode,
                context_notes=self._as_str(effective_settings.get('context_notes')),
                parent_iteration_id=(
                    request.parent_iteration_id
                    or self._as_str(effective_settings.get('parent_iteration_id'))
                ),
                **common,
            )
        except ValidationError as exc:
            raise PromptAgentRequestError(
                'RUN_PRESET_LAUNCH_INVALID',
                f'invalid preset launch payload: {exc.errors()}',
            ) from exc

    async def mark_used(self, run_preset_id: str) -> None:
        preset = await self._require_preset(run_preset_id)
        preset.last_used_at = _utcnow()
        await self.db.commit()

    async def _resolve_launch_mode(self, mode_override: str | None, definition: dict[str, Any]) -> str:
        if mode_override:
            return mode_override
        definition_mode = self._as_str(definition.get('mode'))
        if definition_mode:
            return definition_mode
        workflow_recipe_version_id = self._as_str(definition.get('workflow_recipe_version_id'))
        if not workflow_recipe_version_id:
            return 'generate'
        recipe_version = await self.db.get(WorkflowRecipeVersion, workflow_recipe_version_id)
        if recipe_version is None:
            raise PromptAgentRequestError(
                'WORKFLOW_RECIPE_VERSION_NOT_FOUND',
                'workflow recipe version does not exist',
                status_code=404,
            )
        recipe_definition = _load_json_dict(recipe_version.definition_json)
        steps = recipe_definition.get('steps', [])
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict):
                    mode = self._as_str(step.get('mode'))
                    if mode:
                        return mode
        return 'generate'

    async def _resolve_source_prompt(self, prompt_asset_version_id: Any) -> str | None:
        version_id = self._as_str(prompt_asset_version_id)
        if not version_id:
            return None
        version = await self.db.get(PromptAssetVersion, version_id)
        if version is None:
            raise PromptAgentRequestError(
                'PROMPT_ASSET_VERSION_NOT_FOUND',
                'prompt asset version does not exist',
                status_code=404,
            )
        content = version.content.strip()
        return content or None

    async def _require_preset(self, run_preset_id: str) -> RunPreset:
        preset = await self.db.get(RunPreset, run_preset_id)
        if preset is None:
            raise PromptAgentRequestError(
                'RUN_PRESET_NOT_FOUND',
                'run preset does not exist',
                status_code=404,
            )
        return preset

    def _as_str(self, value: Any) -> str | None:
        return value if isinstance(value, str) and value.strip() else None

    def _as_str_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str) and item.strip()]

    def _as_bool(self, value: Any, *, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        return default
