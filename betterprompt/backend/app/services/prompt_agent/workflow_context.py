from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.context_pack_version import ContextPackVersion
from app.models.evaluation_profile_version import EvaluationProfileVersion
from app.models.prompt_asset_version import PromptAssetVersion
from app.models.run_preset import RunPreset
from app.models.workflow_recipe_version import WorkflowRecipeVersion
from app.services.prompt_agent.errors import PromptAgentRequestError


def _load_json_dict(raw_value: str | None) -> dict[str, Any]:
    if not raw_value:
        return {}
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_json_list(raw_value: str | None) -> list[Any]:
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _dump_pretty_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _merge_ref_field(
    request,
    field_name: str,
    preset_definition: dict[str, Any],
    preset_key: str,
) -> Any:
    if field_name in request.model_fields_set:
        return getattr(request, field_name)
    return preset_definition.get(preset_key)


@dataclass
class ResolvedWorkflowContext:
    run_preset: RunPreset | None = None
    preset_definition: dict[str, Any] = field(default_factory=dict)
    source_asset_version: PromptAssetVersion | None = None
    context_pack_versions: list[ContextPackVersion] = field(default_factory=list)
    evaluation_profile_version: EvaluationProfileVersion | None = None
    workflow_recipe_version: WorkflowRecipeVersion | None = None

    def ref_payload(self) -> dict[str, Any]:
        return {
            'run_preset_id': self.run_preset.id if self.run_preset else None,
            'prompt_asset_version_id': self.source_asset_version.id if self.source_asset_version else None,
            'context_pack_version_ids': [item.id for item in self.context_pack_versions],
            'evaluation_profile_version_id': (
                self.evaluation_profile_version.id if self.evaluation_profile_version else None
            ),
            'workflow_recipe_version_id': self.workflow_recipe_version.id if self.workflow_recipe_version else None,
        }

    def recipe_definition(self) -> dict[str, Any]:
        if self.workflow_recipe_version is None:
            return {}
        return _load_json_dict(self.workflow_recipe_version.definition_json)

    def evaluation_rules(self) -> dict[str, Any]:
        if self.evaluation_profile_version is None:
            return {}
        return _load_json_dict(self.evaluation_profile_version.rules_json)

    def infer_mode(self, mode_override: str | None = None) -> str:
        if mode_override:
            return mode_override
        recipe_definition = self.recipe_definition()
        steps = recipe_definition.get('steps', [])
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict) and isinstance(step.get('mode'), str):
                    return step['mode']
        return 'generate'

    def source_prompt_content(self) -> str | None:
        if self.source_asset_version is None:
            return None
        content = self.source_asset_version.content.strip()
        return content or None

    def build_generate_context_notes(self, base_context_notes: str | None) -> str | None:
        return self._merge_blocks(
            base_context_notes,
            include_source_prompt=True,
            include_context_packs=True,
            include_evaluation_profile=True,
            include_workflow_recipe=True,
        )

    def build_continue_context_notes(self, base_context_notes: str | None) -> str | None:
        return self._merge_blocks(
            base_context_notes,
            include_source_prompt=True,
            include_context_packs=True,
            include_evaluation_profile=True,
            include_workflow_recipe=True,
        )

    def build_debug_guidance(self) -> str | None:
        return self._merge_blocks(
            None,
            include_source_prompt=True,
            include_context_packs=True,
            include_evaluation_profile=True,
            include_workflow_recipe=True,
        )

    def _merge_blocks(
        self,
        base_text: str | None,
        *,
        include_source_prompt: bool,
        include_context_packs: bool,
        include_evaluation_profile: bool,
        include_workflow_recipe: bool,
    ) -> str | None:
        blocks: list[str] = []
        if base_text and base_text.strip():
            blocks.append(f'用户补充上下文：\n{base_text.strip()}')
        if include_source_prompt and self.source_asset_version is not None:
            source_prompt = self.source_prompt_content()
            if source_prompt:
                blocks.append(
                    '参考起始 Prompt 版本：\n'
                    '以下内容表示本次运行引用的 Prompt 资产版本，应吸收其中有价值的结构和约束，而不是机械复述。\n'
                    f'{source_prompt}'
                )
        if include_context_packs and self.context_pack_versions:
            pack_blocks = []
            for index, version in enumerate(self.context_pack_versions, start=1):
                payload = _load_json_dict(version.payload_json)
                pack_blocks.append(
                    f'Context Pack {index} (version_id={version.id}, version_number={version.version_number})\n'
                    f'{_dump_pretty_json(payload)}'
                )
            blocks.append(
                '运行上下文包：\n'
                '以下内容是本次运行显式绑定的长期上下文，应作为硬上下文约束被吸收进结果。\n'
                + '\n\n'.join(pack_blocks)
            )
        if include_evaluation_profile and self.evaluation_profile_version is not None:
            blocks.append(
                '质量评估标准：\n'
                '以下标准代表本次运行绑定的 Evaluation Profile，结果应尽量主动满足这些质量要求。\n'
                f'{_dump_pretty_json(self.evaluation_rules())}'
            )
        if include_workflow_recipe and self.workflow_recipe_version is not None:
            blocks.append(
                '运行方法模板：\n'
                '以下 Workflow Recipe 定义代表本次运行的推荐方法和顺序，可用于约束输出结构与行为方式。\n'
                f'{_dump_pretty_json(self.recipe_definition())}'
            )

        merged = '\n\n'.join(blocks).strip()
        return merged or None


class PromptWorkflowContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_request(self, request) -> tuple[object, ResolvedWorkflowContext]:
        run_preset: RunPreset | None = None
        preset_definition: dict[str, Any] = {}
        if request.run_preset_id:
            run_preset = await self._require_run_preset(request.run_preset_id)
            preset_definition = _load_json_dict(run_preset.definition_json)

        merged_refs = {
            'source_asset_version_id': _merge_ref_field(
                request,
                'source_asset_version_id',
                preset_definition,
                'prompt_asset_version_id',
            ),
            'context_pack_version_ids': _merge_ref_field(
                request,
                'context_pack_version_ids',
                preset_definition,
                'context_pack_version_ids',
            )
            or [],
            'evaluation_profile_version_id': _merge_ref_field(
                request,
                'evaluation_profile_version_id',
                preset_definition,
                'evaluation_profile_version_id',
            ),
            'workflow_recipe_version_id': _merge_ref_field(
                request,
                'workflow_recipe_version_id',
                preset_definition,
                'workflow_recipe_version_id',
            ),
            'run_preset_id': request.run_preset_id,
        }
        effective_request = request.model_copy(update=merged_refs)
        resolved = ResolvedWorkflowContext(
            run_preset=run_preset,
            preset_definition=preset_definition,
            source_asset_version=await self._resolve_prompt_asset_version(effective_request.source_asset_version_id),
            context_pack_versions=await self._resolve_context_pack_versions(effective_request.context_pack_version_ids),
            evaluation_profile_version=await self._resolve_evaluation_profile_version(
                effective_request.evaluation_profile_version_id
            ),
            workflow_recipe_version=await self._resolve_workflow_recipe_version(
                effective_request.workflow_recipe_version_id
            ),
        )
        return effective_request, resolved

    async def _require_run_preset(self, run_preset_id: str) -> RunPreset:
        preset = await self.db.get(RunPreset, run_preset_id)
        if preset is None:
            raise PromptAgentRequestError(
                'RUN_PRESET_NOT_FOUND',
                'run preset does not exist',
                status_code=404,
            )
        return preset

    async def _resolve_prompt_asset_version(self, version_id: str | None) -> PromptAssetVersion | None:
        if not version_id:
            return None
        version = await self.db.get(PromptAssetVersion, version_id)
        if version is None:
            raise PromptAgentRequestError(
                'PROMPT_ASSET_VERSION_NOT_FOUND',
                'prompt asset version does not exist',
                status_code=404,
            )
        return version

    async def _resolve_context_pack_versions(self, version_ids: list[str]) -> list[ContextPackVersion]:
        resolved_versions: list[ContextPackVersion] = []
        seen_ids: set[str] = set()
        for version_id in version_ids:
            if version_id in seen_ids:
                continue
            version = await self.db.get(ContextPackVersion, version_id)
            if version is None:
                raise PromptAgentRequestError(
                    'CONTEXT_PACK_VERSION_NOT_FOUND',
                    'context pack version does not exist',
                    status_code=404,
                )
            resolved_versions.append(version)
            seen_ids.add(version_id)
        return resolved_versions

    async def _resolve_evaluation_profile_version(
        self,
        version_id: str | None,
    ) -> EvaluationProfileVersion | None:
        if not version_id:
            return None
        version = await self.db.get(EvaluationProfileVersion, version_id)
        if version is None:
            raise PromptAgentRequestError(
                'EVALUATION_PROFILE_VERSION_NOT_FOUND',
                'evaluation profile version does not exist',
                status_code=404,
            )
        return version

    async def _resolve_workflow_recipe_version(self, version_id: str | None) -> WorkflowRecipeVersion | None:
        if not version_id:
            return None
        version = await self.db.get(WorkflowRecipeVersion, version_id)
        if version is None:
            raise PromptAgentRequestError(
                'WORKFLOW_RECIPE_VERSION_NOT_FOUND',
                'workflow recipe version does not exist',
                status_code=404,
            )
        return version
