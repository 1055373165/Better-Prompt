# 架构决策记录

## ADR-001：Agent 框架选型 — LangGraph

- 状态：已验证（探针通过）
- 日期：2026-03-20
- 背景：需要一个支持 DAG 编排、并行分支、human-in-the-loop、状态持久化的 Agent 框架
- 候选方案：
  - LangGraph 0.2+：DAG 原生支持、fan-out/fan-in 并行、内置 checkpointing、human-in-the-loop 成熟
  - CrewAI：API 简洁但编排灵活性不足，不支持细粒度 DAG 控制
  - AutoGen：擅长多 Agent 对话，不适合 DAG 式工作流
  - 纯自研：最大控制力，但开发成本高 3-5 倍
- 最终决定：LangGraph 0.2+。DAG 编排 + 并行 + checkpointing + human-in-the-loop 四项核心需求全覆盖
- 代价与妥协：回溯到任意历史节点的原生支持有限，需自行实现；框架版本迭代较快，存在 API 变动风险
- 推翻条件：如果 LangGraph 的并行 fan-out 在实际使用中无法稳定支持 3+ 并发 LLM 调用，或 checkpointing 不支持 SQLite 对接
- 影响范围：orchestrator/、agents/、state/ 全部模块
- 探针验证：已通过 — 3 并行节点 fan-out + SqliteSaver checkpointing 正常工作，状态可恢复

## ADR-002：LLM 抽象层 — LangChain Core

- 状态：已决定
- 日期：2026-03-20
- 背景：需要支持多 LLM 提供商（OpenAI / Anthropic / Ollama）切换，且与 LangGraph 集成
- 候选方案：
  - LangChain Core：与 LangGraph 同生态，多 provider 支持成熟
  - LiteLLM：更轻量的统一接口，但与 LangGraph 集成需额外适配
  - 直接调用各 provider SDK：无抽象层开销，但切换 provider 需改代码
- 最终决定：LangChain Core。与 LangGraph 同生态零摩擦集成
- 代价与妥协：引入 LangChain 依赖链较重；部分 provider 的高级功能可能被抽象层屏蔽
- 推翻条件：如果 LangChain 的抽象层导致 token streaming 或 tool calling 功能缺失
- 影响范围：agents/ 全部模块、config/settings.py
- 探针验证：不需要 — LangChain + LangGraph 集成是官方推荐路径

## ADR-003：状态持久化 — SQLite + SQLAlchemy 2.0

- 状态：已验证（探针通过）
- 日期：2026-03-20
- 背景：需要事务安全的状态持久化，支持并发 Agent 读写，同时支持 LangGraph checkpointing
- 候选方案：
  - SQLite + SQLAlchemy：零部署、事务支持、ORM 便利、LangGraph 有 SqliteSaver
  - PostgreSQL：更强并发，但需要额外部署
  - 纯文件（JSON/Markdown）：最简单，但无事务、无并发安全
- 最终决定：SQLite + SQLAlchemy 2.0。单机场景足够，零部署，LangGraph SqliteSaver 原生支持
- 代价与妥协：SQLite WAL 模式下并发写入有限（单写多读），极端并发场景可能需升级
- 推翻条件：如果并行 MDU 执行时出现数据库锁竞争导致超时
- 影响范围：state/ 全部模块、orchestrator/ checkpoint 配置
- 探针验证：已通过 — 5 并发写入 ×20 次，0 错误，100/100 行写入，耗时 0.25s

## ADR-004：CLI 框架 — Typer

- 状态：已决定
- 日期：2026-03-20
- 背景：需要一个类型安全、支持异步、自动生成帮助文档的 CLI 框架
- 候选方案：
  - Typer：基于 Click，类型安全，自动帮助文档，async 支持
  - Click：更底层，灵活但样板代码多
  - argparse：标准库，无额外依赖，但 DX 差
- 最终决定：Typer。最佳 DX + 类型安全
- 代价与妥协：额外依赖
- 推翻条件：无合理推翻条件
- 影响范围：cli/main.py
- 探针验证：不需要

## ADR-005：并发策略 — asyncio + LangGraph fan-out，默认 3 并发

- 状态：已验证（探针通过）
- 日期：2026-03-20
- 背景：需要真自动并行执行无依赖的 MDU，同时受 LLM API rate limit 约束
- 候选方案：
  - asyncio + fan-out（默认 3）：原生异步，LangGraph 直接支持
  - multiprocessing：真并行但进程间通信复杂，与 LangGraph 不兼容
  - threading + ThreadPoolExecutor：GIL 限制，对 I/O 密集型可行但不如 asyncio 优雅
- 最终决定：asyncio + LangGraph fan-out，`max_parallel_mdus=3`，可配置上限 5
- 代价与妥协：受 API rate limit 约束；并行 Agent 之间如果产生冲突（修改同文件）需要额外冲突检测
- 推翻条件：如果 LangGraph 的 fan-out 不支持动态调整并发数
- 影响范围：orchestrator/parallel.py、config/settings.py
- 探针验证：已通过 — 与 ADR-001 合并验证，fan-out 并行 + 并发 DB 写入均正常

## ADR-006：包管理 — uv + pyproject.toml

- 状态：已决定
- 日期：2026-03-20
- 背景：需要现代化的 Python 包管理，快速解析依赖
- 候选方案：
  - uv：极快的依赖解析，兼容 pip 接口
  - Poetry：成熟但依赖解析慢
  - pip + requirements.txt：最基础，无锁文件
- 最终决定：uv + pyproject.toml
- 代价与妥协：uv 相对较新，用户可能需要额外安装
- 推翻条件：无合理推翻条件
- 影响范围：项目根目录
- 探针验证：不需要

## ADR-007：数据模型设计 — 8 表结构

- 状态：已决定
- 日期：2026-03-20
- 背景：需要完整覆盖 v2 协议的所有状态（项目、ADR、阶段、任务、MDU、依赖、回溯、变更）
- 候选方案：
  - 8 表结构（projects, decisions, phases, tasks, mdus, mdu_dependencies, backtrack_log, change_log）：完整覆盖
  - 3 表精简结构（projects, mdus, logs）：更简单但丢失关系
- 最终决定：8 表结构，完整覆盖
- 代价与妥协：表数量较多，查询可能需要多表 JOIN
- 推翻条件：如果实际开发中发现表之间的关联查询严重影响性能
- 影响范围：state/ 全部模块
- 探针验证：不需要
