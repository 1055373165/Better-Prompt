# 《BetterPrompt 数据库 Migration 规划 v1》

## 1. 文档目标

本文定义 `BetterPrompt` 在产品化过程中数据库 schema 的分批迁移策略，目标是：

- **降低一次性建模风险**
- **确保 Sprint 节奏可落地**
- **让后端工程和数据模型同步推进**
- **避免早期过度设计导致返工**

本文适合作为 Alembic migration 的实施顺序依据。

# 2. 迁移设计原则

- **先主干，后扩展**
- **先过程，后资产**
- **先可运行，后复杂化**
- **先低耦合表，后高阶能力表**
- **尽量保证每一批 migration 都可单独上线**

# 3. 总体迁移批次

建议分为 4 批。

- **Migration Batch 1**
  - 用户与 Prompt 会话主链路

- **Migration Batch 2**
  - Prompt 资产沉淀能力

- **Migration Batch 3**
  - 模板体系

- **Migration Batch 4**
  - 使用统计、成本、评估增强

# 4. Batch 1：主链路建模

## 4.1 目标

支撑以下最小能力：

- 创建用户
- 创建 session
- 创建 iteration
- 支持 generate/debug/evaluate/continue 的结果落库
- 支持 session 详情与历史查询

## 4.2 包含表

- `users`
- `prompt_sessions`
- `prompt_iterations`

## 4.3 建议顺序

### Step 1

创建 `users`

### Step 2

创建 `prompt_sessions`

### Step 3

创建 `prompt_iterations`

### Step 4

补充索引

## 4.4 关键字段检查

### `users`

必须具备：

- `id`
- `email`
- `name`
- `status`
- `created_at`
- `updated_at`

### `prompt_sessions`

必须具备：

- `id`
- `user_id`
- `title`
- `entry_mode`
- `status`
- `latest_iteration_id`（可先 nullable）
- `metadata_json`
- `created_at`
- `updated_at`

### `prompt_iterations`

必须具备：

- `id`
- `session_id`
- `parent_iteration_id`（nullable）
- `mode`
- `status`
- `input_payload_json`
- `output_payload_json`
- `provider`
- `model`
- `tokens_input`
- `tokens_output`
- `latency_ms`
- `error_code`
- `error_message`
- `created_at`

## 4.5 索引建议

- `idx_prompt_sessions_user_id_created_at`
- `idx_prompt_sessions_user_id_updated_at`
- `idx_prompt_iterations_session_id_created_at`
- `idx_prompt_iterations_parent_iteration_id`
- `idx_prompt_iterations_mode`
- `idx_prompt_iterations_status`

## 4.6 验收标准

- migration 成功执行
- session 与 iteration 可写入
- session 详情可按时间顺序取 iteration
- continue 链路可通过 `parent_iteration_id` 表达

# 5. Batch 2：资产沉淀能力

## 5.1 目标

支撑以下能力：

- 将某次 iteration 保存为 Prompt 资产
- 支持资产版本管理
- 支持收藏与标签

## 5.2 包含表

- `prompt_assets`
- `prompt_asset_versions`

## 5.3 建议顺序

### Step 1

创建 `prompt_assets`

### Step 2

创建 `prompt_asset_versions`

### Step 3

为 `prompt_sessions.pinned_asset_id` 或相关外键补齐引用

## 5.4 关键字段检查

### `prompt_assets`

必须具备：

- `id`
- `user_id`
- `source_session_id`
- `name`
- `artifact_type`
- `current_version_id`（可后补）
- `is_favorite`
- `visibility`
- `tags_json`
- `created_at`
- `updated_at`

### `prompt_asset_versions`

必须具备：

- `id`
- `asset_id`
- `version_number`
- `content`
- `source_iteration_id`
- `created_at`

## 5.5 索引建议

- `idx_prompt_assets_user_id_updated_at`
- `idx_prompt_assets_user_id_is_favorite`
- `uq_prompt_asset_versions_asset_id_version_number`

## 5.6 验收标准

- 用户可从 iteration 创建 asset
- asset 可追加 version
- 可正确查出 current version

# 6. Batch 3：模板体系

## 6.1 目标

支撑以下能力：

- 官方模板
- 用户模板
- 模板版本管理
- 模板分类

## 6.2 包含表

- `templates`
- `template_versions`

## 6.3 建议顺序

### Step 1

创建 `templates`

### Step 2

创建 `template_versions`

## 6.4 验收标准

- 模板可创建
- 模板可版本化
- 模板可按 owner_type / category 查询

# 7. Batch 4：使用统计与增强能力

## 7.1 目标

支撑以下能力：

- token 与成本统计
- quota 预留
- 评估记录拆分
- 更精细分析与报表

## 7.2 包含表

- `usage_records`
- 可选 `evaluation_records`

## 7.3 验收标准

- 每次 iteration 可追踪 usage
- 成本可按用户与时间聚合统计

# 8. Alembic 组织建议

建议每一批 migration 对应 1-2 个 revision，而不是把所有表放进一个 revision。

推荐命名方式：

- `001_create_users`
- `002_create_prompt_sessions`
- `003_create_prompt_iterations`
- `004_create_prompt_assets`
- `005_create_prompt_asset_versions`
- `006_create_templates`
- `007_create_template_versions`
- `008_create_usage_records`

# 9. 回滚策略建议

- Batch 1 必须保证可独立回滚
- Batch 2 起要谨慎处理有数据依赖的外键回滚
- 不建议在同一个 migration 中做过多数据修复逻辑
- schema 迁移与数据回填尽量拆分

# 10. Sprint 对应关系

- **Sprint 1**
  - 完成 Batch 1

- **Sprint 2**
  - 衔接 Batch 2，并完成 session 主流程落库

- **Sprint 3**
  - 视产品优先级推进 Batch 3

- **Sprint 4+**
  - 推进 Batch 4

# 11. 风险提示

- 不要一开始就把所有表全部建完
- 不要在 Batch 1 引入团队/角色/复杂标签系统
- 不要把模板和资产混成同一张表
- 不要省略 `parent_iteration_id`，否则 continue 链路后续会返工

# 12. 最终结论

数据库迁移应以 `users -> prompt_sessions -> prompt_iterations` 为主线先跑通过程闭环，再逐步补充 `prompt_assets`、`templates`、`usage_records`。这能最大化减少早期返工，并和当前产品化路线保持一致。
