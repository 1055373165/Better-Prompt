# BetterPrompt V4 Freshness-Aware Agents PRD v1

## 1. 文档目标

本文定义 `V4 Freshness-Aware Agents` 的产品需求。

V4 不是让 BetterPrompt 变成“会聊天的代理”，而是让它在动态信息场景中提供持续更新能力。

一句话概括：

- `V3` 让用户在工作区里工作
- `V4` 让工作区开始持续感知变化并重新运行

## 2. 产品定位

V4 是 `Agent Layer`，但它必须是：

- 高约束
- 强证据
- 强时效
- 可追溯

不是：

- 黑盒结论生成器
- magic stock picker
- 自治交易机器人

## 3. 核心 JTBD

当用户在动态领域持续研究同一批对象时，他希望：

- 不必每天手工重新跑一遍
- 系统能感知哪些对象值得重新看
- 更新时能明确知道“哪里变了”
- 每条更新都带时间与依据

## 4. V4 核心对象

V4 新增五个一等对象：

1. `Watchlist`
2. `Agent Monitor`
3. `Agent Run`
4. `Agent Alert`
5. `Freshness Record`

定义：

- `Watchlist`：工作区里的关注对象集合
- `Agent Monitor`：定义何时触发 rerun 的规则
- `Agent Run`：一次自动或半自动 rerun 的执行记录
- `Agent Alert`：面向用户的更新提示
- `Freshness Record`：某个 source / subject / report 的时效状态

## 5. 关键用户故事

### 故事 1：创建关注列表

用户应能：

- 在股票工作区创建 watchlist
- 添加若干 ticker

### 故事 2：为关注列表配置 monitor

用户应能：

- 设定按周期 rerun
- 或按事件触发 rerun

### 故事 3：收到变化提醒

系统 rerun 后，用户应能：

- 在更新流中看到 alert
- 看到结论摘要
- 看到变更概述

### 故事 4：查看 diff

用户应能：

- 打开一次 agent run
- 看到哪些输入更新了
- 看到哪些结论变化了
- 看到哪些判断保持不变

### 故事 5：查看 freshness

用户应能在 source、subject、report 层面看到：

- last checked
- data timestamp
- stale / aging / fresh

## 6. 信息架构

```text
Workspace
  ├── Subjects
  ├── Watchlists
  ├── Monitors
  ├── Updates Feed
  ├── Reports
  └── Run Detail / Diff View
```

## 7. 功能范围

### In Scope

- watchlist 管理
- monitor 管理
- rerun 记录
- alert feed
- freshness 标记
- change summary

### NOT In Scope

- 自动下单
- 直接买卖建议
- 开放式自主规划
- 多 vertical 同时展开

## 8. 产品规则

V4 必须满足三条硬规则：

1. 每次更新都显示 recency
2. 每次 rerun 都显示 change summary
3. 每次 alert 都能追到 evidence 与 run

少任何一条，V4 都只是“看起来像 agent”。

## 9. 边缘场景

### 9.1 信息没变

如果 rerun 后无实质变化：

- 可以记录 agent run
- 但不一定生成高优先级 alert

### 9.2 source 过期

如果 source freshness 已过期：

- 需要明确标记 stale
- 不得继续伪装为新鲜结论

### 9.3 trigger 异常

如果 monitor 触发失败：

- 必须留下失败记录
- 不得 silent fail

## 10. 成功指标

- watchlist 创建率
- active monitor 数
- agent-run 成功率
- 产生 alert 的有效比例
- 有 freshness 标记的 report 占比

## 11. 上线验收标准

1. 用户能创建 watchlist
2. 用户能创建 monitor
3. monitor 能产生 agent run 记录
4. 更新流能显示 alert
5. source / subject / report 有 freshness 状态
6. run detail 能显示 diff 摘要

## 12. 最终判断

V4 的价值不在于“自动化”本身，而在于：

- 自动化
- freshness
- diff
- evidence

只有这四者同时出现，BetterPrompt 的 agent 层才会可信。
