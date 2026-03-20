# 项目上下文恢复文档

> 本文档用于帮助接手程序员在 15 分钟内恢复完整项目上下文。
> 最后更新：2026-03-20

---

## 一句话概述

**autopilot-agent** 是一个基于 LangGraph 的多 Agent 协作系统，将 [dev-autopilot-skill v2](../dev-autopilot-skill.md) 从纯 Prompt 协议升级为可执行的 Agent 框架。用户输入一句话需求，系统自动驱动 6 个阶段完成全周期软件开发。

---

## 项目完成状态

### 已完成 ✅

| 模块 | 文件数 | 状态 | 说明 |
|------|--------|------|------|
| 项目基础设施 | 2 | ✅ 完成 | `pyproject.toml`, `__init__.py` 包结构 |
| 配置层 | 1 | ✅ 完成 | `settings.py` — 6 个 Pydantic 配置模型 |
| 状态层 | 4 | ✅ 完成 | `database.py`, `models.py`(8 表 ORM), `schema.py`(LangGraph State), `queries.py`(CRUD) |
| 提示词层 | 7 | ✅ 完成 | 7 个 Agent 的 system prompt，含 Bug-Driven Evolution 硬约束注入 |
| Agent 实现 | 8 | ✅ 完成 | `base.py` + 7 个 Agent（requirement, architect, spike, decomposer, coder, reviewer, checkpoint） |
| 核心机制 | 6 | ✅ 完成 | circuit_breaker, scope_lock, backtrack, change_request, heartbeat, bug_driven_evolution |
| 编排层 | 3 | ✅ 完成 | `main_graph.py`(6 阶段 DAG), `phase_graphs.py`(阶段子图), `parallel.py`(fan-out 并行) |
| 工具层 | 2 | ✅ 完成 | `file_manager.py`, `code_writer.py`(含 PROGRESS.md/DECISIONS.md 同步) |
| CLI 入口 | 1 | ✅ 完成 | 8 个命令：start, resume, status, decisions, backtrack, skip, pause, change-request |
| 测试 | 2 | ✅ 完成 | 33 个测试全部通过（10 state + 23 mechanisms） |
| 文档 | 3 | ✅ 完成 | README.md(941 行), PROGRESS.md, DECISIONS.md |
| 技术探针 | 1 | ✅ 完成 | `spike_test.py` — LangGraph fan-out + SQLite WAL 并发验证 |

### 已知未完成项 ⚠️

| 项目 | 优先级 | 说明 |
|------|--------|------|
| PROGRESS.md 未同步最终状态 | 中 | 文件中的"已完成 MDU"仍为 0%，需更新为实际完成状态（40/40 MDU 100%） |
| .gitignore 缺少 .venv | 高 | `.venv/` 目录被提交到了 git，应添加到 `.gitignore` |
| 端到端集成测试 | 中 | 当前只有 state 和 mechanisms 的单元测试，缺少 Agent+Orchestrator 的集成测试（需要 mock LLM） |
| `__init__.py` 导出 | 低 | 各子包的 `__init__.py` 为空，可选择性地添加公共 API 导出 |
| 错误恢复测试 | 低 | backtrack 和 change-request 的完整流程尚未有自动化测试 |

---

## 技术栈速查

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | 3.11+ | `TypedDict` + `Annotated` 特性依赖 |
| 编排 | LangGraph | ≥0.2.0 | DAG 工作流 + fan-out/fan-in + checkpointing |
| LLM | LangChain Core | ≥0.3.0 | 多 provider 抽象（OpenAI/Anthropic/Ollama） |
| 持久化 | SQLite + SQLAlchemy 2.0 | ≥2.0.0 | WAL 模式 + 8 表 ORM |
| CLI | Typer + Rich | ≥0.12.0 | 类型安全命令行 + 格式化输出 |
| 检查点 | langgraph-checkpoint-sqlite | ≥3.0.0 | 图状态序列化/恢复 |
| 包管理 | pyproject.toml + pip | — | `pip install -e .` 可用 |

---

## 架构核心决策（7 个 ADR）

快速理解"为什么这样设计"——详情见 `DECISIONS.md`：

1. **ADR-001 LangGraph** — 选它因为 DAG 编排 + fan-out 并行 + checkpointing + human-in-the-loop 四项全覆盖。探针已验证。
2. **ADR-002 LangChain Core** — 与 LangGraph 同生态零摩擦，多 provider 切换。
3. **ADR-003 SQLite + WAL** — 零部署，5 并发写入 ×20 次探针通过。极端并发时考虑升级 PostgreSQL。
4. **ADR-004 Typer** — CLI 框架，最佳开发体验。
5. **ADR-005 asyncio fan-out, 默认 3 并行** — semaphore 控制，可配置 1-5。
6. **ADR-006 pyproject.toml** — 现代 Python 包管理标准。
7. **ADR-007 8 表数据模型** — 完整覆盖 v2 协议所有实体关系。

---

## 关键代码入口

接手后先读这 5 个文件，即可理解整体架构：

### 1. `src/orchestrator/main_graph.py` — 系统骨架

```
START → requirement_phase → architecture_phase → spike_phase
      → decomposition_phase → execution_phase → wrapup_phase → END

特殊节点：
  human_gate        — 暂停等待用户输入
  backtrack_router   — 跳转回早期阶段
```

每个阶段通过 `route_phase_transition()` 决定下一步：继续、暂停(human_gate)、或回溯(backtrack_router)。

### 2. `src/state/schema.py` — 状态定义

`AutopilotState(TypedDict)` 是全局状态，在所有 Agent 之间传递。关键字段：

- `current_phase` / `current_step` — 当前位置
- `locked_requirement` — 冻结的需求
- `execution_plan` — MDU DAG + 批次调度
- `mdu_results: Annotated[list, add]` — fan-in reducer，并行结果自动聚合
- `waiting_for_human` / `human_prompt` — 人机交互控制

### 3. `src/agents/base.py` — Agent 基类

所有 Agent 共享的 LLM 调用能力：
- `invoke_llm()` — 带重试 + 指数退避的 LLM 调用
- `invoke_llm_json()` — 自动 JSON 解析（处理 markdown fence）
- 支持 OpenAI / Anthropic / Ollama 三种 provider

### 4. `src/orchestrator/parallel.py` — 并行执行核心

`execute_batch()` 函数：
- asyncio.Semaphore 控制并发数
- 对每个 MDU：Coder 编码 → Scope 检查 → Reviewer 审查（最多 3 轮）
- fan-in 收集结果，触发 heartbeat

### 5. `src/mechanisms/bug_driven_evolution.py` — 硬约束

**这是必须理解的硬约束**：每个 bug 必须三层下钻：
1. 修复 bug
2. 分析根因（6 类：prompt_deficiency / flow_omission / mechanism_blind_spot / data_model_defect / dependency_gap / acceptance_gap）
3. 双向回写（dev-autopilot-skill.md + agent 代码）

`enforce_at_phase_boundary()` 在阶段边界**强制阻断**，不允许跳过。

---

## 数据流示意

```
用户需求 (一句话)
    │
    ▼
RequirementAgent ─── locked_requirement
    │
    ▼
ArchitectAgent ───── decisions[] + spike_candidates[]
    │
    ▼
SpikeAgent ────────── validated_decisions[] (或 backtrack)
    │
    ▼
DecomposerAgent ──── execution_plan { mdus[], batches[], dependencies }
    │                    ↑ CircuitBreaker 限制: depth≤4, MDU≤60, sub≤8
    ▼
┌─── Parallel Executor (semaphore=3) ───┐
│  CoderAgent → ScopeLock → Reviewer    │  ← 每个 MDU
│  (最多 3 轮审查)                       │
└───────────────────────────────────────┘
    │  mdu_results[] (fan-in)
    ▼
CheckpointAgent ── evolution_gate ── WrapupAgent
```

---

## 数据库表关系

```
projects (1)
  ├── decisions (N) ........... ADR 记录
  ├── phases (N)
  │     └── tasks (N)
  │           └── mdus (N)
  │                 └── mdu_dependencies (N:N) ... DAG 边
  ├── backtrack_log (N) ...... 回溯历史
  └── change_log (N) ......... 变更日志
```

两个数据库文件：
- `autopilot.db` — 主状态（8 表）
- `autopilot_checkpoint.db` — LangGraph 检查点（会话恢复用）

---

## 6 个工程机制速查

| 机制 | 文件 | 触发条件 | 作用 |
|------|------|----------|------|
| **熔断器** | `circuit_breaker.py` | 拆解深度>4 / MDU>60 / 子项>8 | 停止拆解，使用当前树 |
| **范围锁** | `scope_lock.py` | 每个 MDU 编码时自动注入 | 防止 AI 超范围编码 |
| **回溯** | `backtrack.py` | 上游问题/审查死循环/用户命令 | 5 类根因 → 5 个回溯目标 |
| **变更请求** | `change_request.py` | 用户 `/change-request` | 影响分析 + 风险评估 |
| **心跳** | `heartbeat.py` | 每 10% 完成度或阶段切换 | 进度报告 |
| **Bug 进化** | `bug_driven_evolution.py` | 发现任何 bug | **硬约束**：三层下钻 + 阶段阻断 |

---

## 人机交互点（9 个）

系统在以下节点暂停，等待用户输入（通过 `human_gate` 节点实现）：

| 节点 | 阶段 | 用户操作 |
|------|------|----------|
| 需求追问 | Step 3 | 回答 3-5 个选择题 |
| 架构确认 | Step 4 | 确认/调整架构方案 |
| 探针失败 | Step 6 | 确认替代方案 |
| 执行计划确认 | Step 9 | 确认 MDU 数量和关键路径 |
| 阶段验收 | Phase 边界 | 本地运行代码并反馈 |
| 回溯确认 | Backtrack | 确认回溯目标 |
| 变更确认 | Change Request | 确认变更方案 |
| 审查死循环 | 异常 C | 确认根因和处理方向 |
| 进化阻断 | Phase 边界 | 完成待回写的 bug 进化 |

---

## 快速运行指南

```bash
# 1. 环境准备
cd autopilot-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

# 2. 配置 API Key
export OPENAI_API_KEY="sk-..."

# 3. 运行测试（验证环境）
pip install -e ".[dev]"
python -m pytest tests/ -v    # 期望 33 passed

# 4. 运行技术探针（验证核心依赖）
python spike_test.py          # 期望 2/2 PASSED

# 5. 启动项目
autopilot start "你的需求" --dir ./target-project
```

---

## 关键约定和规则

### 不可违反的硬约束

1. **Bug-Driven Evolution** — 每个 bug 必须三层下钻，不可跳过第二层和第三层
2. **范围锁** — MDU 编码不可超出描述范围
3. **熔断器** — 拆解超限时立即停止
4. **阶段验收 Evolution Gate** — 有待回写 bug 时阻断阶段推进

### 代码约定

- 所有文件开头 `from __future__ import annotations`
- Agent 操作全部 async
- 配置全部 Pydantic
- ORM 使用 SQLAlchemy 2.0 `mapped_column` 风格
- 状态通过 `AutopilotState(TypedDict)` 在节点间传递

### 文件约定

- `PROGRESS.md` — 由 `code_writer.py` 从 DB 自动生成，不要手动编辑
- `DECISIONS.md` — 同上
- `autopilot.db` — 不要手动修改，所有变更通过 `queries.py`
- `dev-autopilot-skill.md` — 框架协议文档，Bug 进化时需要同步更新

---

## 开发历史摘要

| 时间 | 里程碑 |
|------|--------|
| 2026-03-20 Phase 1 | 需求理解与锁定完成 |
| 2026-03-20 Phase 2 | 架构设计确认，7 个 ADR 固化 |
| 2026-03-20 Phase 3 | 技术探针 2/2 通过（LangGraph fan-out + SQLite WAL） |
| 2026-03-20 Phase 4 | 任务拆解：9 组任务 → 40 MDU → 20 批次 |
| 2026-03-20 Phase 5 | 40/40 MDU 全部实现 |
| 2026-03-20 硬约束 | Bug-Driven Evolution 协议注入框架 + 代码 |
| 2026-03-20 Phase 6 | 33/33 测试通过，README 完成 |

---

## 如果要继续开发

### 优先级最高的改进

1. **添加 `.gitignore` 规则** — 排除 `.venv/`、`*.db`、`__pycache__/`
2. **更新 `PROGRESS.md`** — 同步为实际完成状态
3. **添加集成测试** — mock LLM 后测试完整 Agent 链路
4. **添加 `orchestrator/__init__.py` 导出** — 简化 import 路径

### 可选增强

- 支持 streaming 输出（LLM token 流式显示）
- 添加 Web UI（FastAPI + 前端）替代纯 CLI
- 支持多项目管理（当前假设单项目单 DB）
- 添加 cost tracking（LLM API 调用费用追踪）
- 集成真实代码执行环境（sandbox）做自动化测试

---

## 联系与参考

- **框架协议文档**：[dev-autopilot-skill.md](../dev-autopilot-skill.md)（955 行，v2 完整规范）
- **项目 README**：[README.md](./README.md)（941 行，详细使用说明）
- **GitHub**：[Better-Prompt](https://github.com/1055373165/Better-Prompt)
