---
description: 一键启动全周期 AI 辅助开发流程，从一句需求到完整项目交付
---

# Dev Autopilot v2 — 全周期开发自动驾驶

用户输入一句需求后，按照 `dev-autopilot-skill.md` 中定义的 v2 执行协议，自动驱动工具链完成从需求锁定到项目交付的全流程。

## 启动流程

1. 读取 `dev-autopilot-skill.md` 获取完整执行协议
2. 确认用户输入了需求（格式：`我的需求是：【一句话】`）
3. 按照执行协议的六个阶段顺序执行：
   - 第一阶段：需求理解与锁定（AI 直接展开 → Requirement Decomposer 交互式锁定，⚠️ 需用户参与决策）
   - 第二阶段：架构设计与决策固化（Cognitive Architecture Injector → Architecture Decision Recorder → DECISIONS.md，⚠️ 需用户确认架构）
   - 第三阶段：技术探针（验证高风险技术决策，可跳过，⚠️ 探针失败需用户确认替代方案）
   - 第四阶段：任务拆解（Task Decomposition Engine → 递归拆解至 MDU（最大 4 层、上限 60 个）→ 依赖分析 → PROGRESS.md，⚠️ 需用户确认执行计划）
   - 第五阶段：执行循环（对每个 MDU：Prompt Generator + Self-Auditor → 编码 → Code Review Protocol（最多 3 轮）；每个阶段结束：Milestone Checkpoint Validator（含用户本地验证）→ Progress Tracker → 更新 PROGRESS.md）
   - 第六阶段：全局收尾（Self-Auditor 全局审查 → 最终进度快照 → 项目交付摘要）
4. 全程自动注入范围锁，发现上游问题触发回溯协议而非 workaround
5. 每 10% 完成度或阶段切换时输出进度心跳

## 用户交互点

执行过程中仅在以下节点暂停等待用户：

- 需求追问（Step 3）：回答选择题确认需求边界
- 架构确认（Step 4）：确认或调整架构方案
- 探针失败（Step 6）：确认替代方案
- 执行计划确认（Step 9）：确认 MDU 总量和关键路径后启动开发
- 阶段验收（Phase_Checkpoint）：在本地运行代码并反馈验证结果
- 回溯确认（回溯协议）：确认回溯目标和影响范围
- 需求变更确认（变更协议）：确认变更方案和额外工作量

## 异常处理

- 会话中断 → `/dev-autopilot-resume`（从中断 MDU 重头开始，不续写半成品）
- 进度迷失 → `/dev-autopilot-status`
- 代码审查死循环（>3 次）→ 根因分析后触发回溯协议
- 阶段验收阻断 → 修复项拆解为新 MDU 后重新验收
- 需求变更 → `/dev-autopilot-change-request`（影响评估 + 用户确认）
- 任意回溯 → `/dev-autopilot-backtrack`（任意 MDU 执行中可触发）
