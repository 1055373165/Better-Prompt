from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt_asset import PromptAsset
from app.models.prompt_asset_version import PromptAssetVersion
from app.models.prompt_category import PromptCategory
from app.services.prompt_agent.generate_engine import PromptGenerateEngine
from app.services.prompt_agent.optimization_layer import PROMPT_BRIEF_HEADER

DEFAULT_PROMPT_CATEGORY_NAME = '默认提示词'
DEFAULT_IMPORT_CHANGE_SUMMARY = '默认导入：项目历史生成提示词模板'


@dataclass(frozen=True)
class DefaultPromptAssetSeed:
    name: str
    description: str
    content: str
    tags: tuple[str, ...]
    is_favorite: bool = False


def _build_generate_input_template() -> str:
    lines = [
        PROMPT_BRIEF_HEADER,
        '',
        '目标产物：{{artifact_target}}',
        '推断任务类型：{{task_type}}',
        '质量偏好：{{quality_target}}',
        '补充原则：',
        '- 默认交付最终 Prompt，不要产出元 Prompt。',
        '- 把用户输入视为待优化的原始 Prompt 或原始任务描述，目标是重写得更强，而不是偏离用户真正要完成的任务。',
        '- 角色设定必须服务于真实业务任务，不要把执行模型写成 Prompt Agent 或 Prompt Compiler，除非用户明确要求。',
        '- 优先补足输入约束、成功标准、输出格式、失效边界和回退规则。',
        '- 除非用户明确要求，不要额外增加“先分析摘要、先解释思路、先输出计划、先自我介绍”等中间步骤。',
        '- 正文保持自然、清晰、信息密度高，避免模板腔和空泛表述。',
        '- 最终产物不要包裹在 Markdown 代码块中，也不要为了举例再插入 fenced code block。',
        '',
        '任务专用提醒：',
        '{{task_specific_hints_optional}}',
        '',
        '用户原始描述：',
        '{{user_input}}',
        '',
        '补充上下文：',
        '{{context_notes_optional}}',
    ]
    return '\n'.join(lines)


def build_default_prompt_asset_seeds() -> list[DefaultPromptAssetSeed]:
    generate_engine = PromptGenerateEngine()
    base_context_placeholder = '{{base_context}}'

    return [
        DefaultPromptAssetSeed(
            name='原始生成系统提示词',
            description='Prompt Generate 链路发给模型的原始 system prompt。',
            content=generate_engine.system_prompt,
            tags=('默认', '生成', 'system'),
            is_favorite=True,
        ),
        DefaultPromptAssetSeed(
            name='原始输入优化模板',
            description='生成链路在真正拼装 Prompt 前，对用户输入做结构化重写时使用的模板。',
            content=_build_generate_input_template(),
            tags=('默认', '生成', 'input-brief'),
            is_favorite=True,
        ),
        DefaultPromptAssetSeed(
            name='原始任务 Prompt 模板',
            description='输出最终可直接发送任务 Prompt 时使用的原始模板。',
            content=generate_engine._build_task_prompt_template(base_context_placeholder, 'general_deep_analysis'),
            tags=('默认', '生成', 'task-prompt'),
        ),
        DefaultPromptAssetSeed(
            name='原始 System Prompt 模板',
            description='输出长期复用的 system prompt 时使用的原始模板。',
            content=generate_engine._build_system_prompt_template(base_context_placeholder, 'general_deep_analysis'),
            tags=('默认', '生成', 'system-template'),
        ),
        DefaultPromptAssetSeed(
            name='原始分析工作流模板',
            description='输出 analysis workflow prompt 时使用的原始模板。',
            content=generate_engine._build_analysis_workflow_template(base_context_placeholder, 'general_deep_analysis'),
            tags=('默认', '生成', 'analysis-workflow'),
        ),
        DefaultPromptAssetSeed(
            name='原始多轮对话模板',
            description='输出 conversation prompt 时使用的原始模板。',
            content=generate_engine._build_conversation_prompt_template(base_context_placeholder, 'general_deep_analysis'),
            tags=('默认', '生成', 'conversation'),
        ),
    ]


async def seed_default_prompt_library(db: AsyncSession) -> None:
    category = await _get_or_create_default_category(db)

    existing_result = await db.execute(
        select(PromptAsset).where(
            PromptAsset.category_id == category.id,
            PromptAsset.archived_at.is_(None),
        )
    )
    existing_assets = {
        asset.name: asset
        for asset in existing_result.scalars().all()
    }

    base_time = datetime.utcnow()
    created_any = False

    for index, seed in enumerate(build_default_prompt_asset_seeds()):
        if seed.name in existing_assets:
            continue

        timestamp = base_time + timedelta(seconds=index)
        asset_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())

        asset = PromptAsset(
            id=asset_id,
            user_id=None,
            category_id=category.id,
            name=seed.name,
            description=seed.description,
            is_favorite=seed.is_favorite,
            current_version_id=version_id,
            tags_json=json.dumps(list(seed.tags), ensure_ascii=False),
            created_at=timestamp,
            updated_at=timestamp,
        )
        version = PromptAssetVersion(
            id=version_id,
            asset_id=asset_id,
            version_number=1,
            content=seed.content,
            source_iteration_id=None,
            source_asset_version_id=None,
            change_summary=DEFAULT_IMPORT_CHANGE_SUMMARY,
            created_at=timestamp,
        )
        db.add(asset)
        db.add(version)
        created_any = True

    if created_any:
        await db.commit()


async def _get_or_create_default_category(db: AsyncSession) -> PromptCategory:
    result = await db.execute(
        select(PromptCategory).where(
            PromptCategory.name == DEFAULT_PROMPT_CATEGORY_NAME,
            PromptCategory.parent_id.is_(None),
        )
    )
    category = result.scalar_one_or_none()
    if category is not None:
        return category

    now = datetime.utcnow()
    category = PromptCategory(
        id=str(uuid.uuid4()),
        user_id=None,
        parent_id=None,
        name=DEFAULT_PROMPT_CATEGORY_NAME,
        path=DEFAULT_PROMPT_CATEGORY_NAME,
        depth=0,
        sort_order=0,
        created_at=now,
        updated_at=now,
    )
    db.add(category)
    await db.flush()
    return category
