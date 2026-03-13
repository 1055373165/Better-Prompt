# BetterPrompt 项目设计与实现分析

更新日期：2026-03-13

## 1. 项目定位

当前 `betterprompt/` 是从主项目中拆出的 Prompt Agent 独立工作区，目标是把 Prompt 的生成、调试、评估与继续优化流程沉淀成一个可单独运行的产品骨架。

从现有实现看，它还处于“功能骨架已成型、产品化打磨尚未收口”的阶段：

- 前端已经具备完整的 Prompt Agent 工作台组件、API 调用链路和视觉方向。
- 后端已经具备 FastAPI 接口、请求模型、编排层和一组规则引擎。
- 文档层已经有较多规划文档，但运行链路和交付方式仍有一些“抽离中”的痕迹。

## 2. 当前实现结构

### 2.1 前端

前端位于 `betterprompt/frontend/`，技术栈为：

- React 18
- Vite 5
- TypeScript
- Tailwind CSS 3
- TanStack Query
- Axios

主链路如下：

1. `src/main.tsx`
   负责挂载 React 应用并引入全局样式 `src/styles/globals.css`。
2. `src/app/App.tsx`
   注入 QueryClient 等全局 Provider。
3. `src/app/router.tsx`
   使用 `BrowserRouter` 将 `/` 和 `/prompt-agent` 指向 Prompt Agent 页面。
4. `src/features/prompt-agent/index.tsx`
   是实际的页面编排层，负责：
   - 顶部品牌区与快速入口
   - 模式切换
   - Generate / Debug / Evaluate 三类结构化面板
   - 结果面板与继续优化动作
5. `src/features/prompt-agent/hooks/*`
   分别封装 generate / debug / evaluate / continue 四条 API 调用。

从职责划分看，前端架构是清晰的：页面编排、基础 UI、业务组件、请求 Hook 已经分层完成。

### 2.2 后端

后端位于 `betterprompt/backend/`，技术栈为：

- FastAPI
- Pydantic
- SQLAlchemy Async
- SQLite

主链路如下：

1. `app/main.py`
   初始化 FastAPI、CORS 和数据库启动逻辑。
2. `app/api/v1/prompt_agent.py`
   暴露 `/generate`、`/debug`、`/evaluate`、`/continue` 四个核心接口。
3. `app/services/prompt_agent_service.py`
   作为服务层薄封装，将请求转交给编排器。
4. `app/services/prompt_agent/orchestrator.py`
   是核心业务编排层，负责串联：
   - 任务理解
   - Prompt 诊断
   - 模块路由
   - 优化层
   - Generate / Debug / Evaluate / Continue 各子引擎

当前后端更像“规则驱动的 Prompt 工程流水线”，而不是单一的大模型调用代理。这一层次设计是合理的，也方便未来替换或扩展具体策略。

## 3. 这次排查到的前端问题

### 3.1 现象

页面并不是 Tailwind 整体失效，而是呈现为：

- 顶部 Hero 和 Quick Start 区块样式正常；
- 页面主体左侧出现大面积空白；
- 工作流看起来像“样式没渲染完整”或“页面还没搭完”。

通过浏览器快照和代码对照，问题根因不在 CSS 入口，而在“页面编排缺失 + 设计 token 缺口”。

### 3.2 根因 1：主工作流面板没有挂载

`src/features/prompt-agent/components/` 中已经存在：

- `mode-selector.tsx`
- `generate-panel.tsx`
- `debug-panel.tsx`
- `evaluate-panel.tsx`

但在 `src/features/prompt-agent/index.tsx` 中，主布局左列实际是空的：

- 结果区在右列正常渲染；
- 左列只留下一个空的 `div`；
- 直接导致页面主体视觉失衡，用户会误以为前端样式没有正确渲染。

这是本次最核心的显示问题。

### 3.3 根因 2：Quick Start 的交互与页面结构不匹配

Quick Start 会根据输入内容推荐模式，但原实现中：

- 识别到 `debug` / `evaluate` 相关输入时，只会切换 `mode`；
- 页面又没有渲染对应的结构化面板；
- 因此用户点击后没有获得完整工作流入口，体验上像“页面没反应”。

这进一步放大了“样式/界面异常”的感受。

### 3.4 根因 3：Tailwind 自定义 token 缺失

前端样式中引用了若干自定义工具类或语义 token，例如：

- `shadow-apple-sm`
- `shadow-card-hover`
- `stock-up`
- `stock-down`
- `stock-neutral`

这些值在原始 `tailwind.config.ts` 中没有补齐，导致：

- 某些卡片阴影无法生效；
- 金额涨跌类语义色无法正常映射；
- 组件能显示，但细节视觉不完整。

这不是整站失效的唯一根因，但会让页面更像“样式没吃全”。

## 4. 本次已完成修复

### 4.1 恢复页面主工作流

已在 `src/features/prompt-agent/index.tsx` 中重新挂载：

- `ModeSelector`
- `GeneratePanel`
- `DebugPanel`
- `EvaluatePanel`

这样页面恢复为“左侧输入工作流 + 右侧结果面板”的完整工作台结构。

### 4.2 修正 Quick Start 行为

已将顶部区域调整为“快速入口”而不是“万能提交器”：

- 生成类输入仍可直接提交；
- 若识别为调试或评估类需求，则切换模式并滚动到下方结构化面板；
- 避免用户点击后没有明确反馈。

### 4.3 补齐 Tailwind 设计 token

已在 `tailwind.config.ts` 与 `globals.css` 中补齐：

- 阴影 token：`shadow-apple-sm`、`shadow-card-hover`
- 语义价格色：`stock-up`、`stock-down`、`stock-neutral`

这样现有 UI 组件和全局工具类的引用关系重新闭环。

## 5. 验证结果

本次修复后已完成：

- `npm run build` 构建通过
- 本地浏览器预览验证通过
- 修复前后页面快照比对，确认左侧工作流区域已恢复渲染

## 6. 当前剩余风险

### 6.1 前后端仍是分离运行状态

当前后端 `app/main.py` 只提供 API，并没有挂载前端静态资源。  
这意味着项目仍依赖独立的前端开发服务器或静态预览方式启动。

### 6.2 Vite 构建产物默认使用根路径资源

当前构建产物 `dist/index.html` 中的资源路径仍是 `/assets/...`。  
如果未来不是部署在站点根路径，而是放在子路径或直接打开静态文件，CSS/JS 资源可能仍会加载失败。

这不是本次“页面主体显示异常”的直接根因，但确实是后续部署阶段需要优先处理的风险点。

## 7. 结论

当前 BetterPrompt 的整体架构方向是对的：

- 前端已经具备工作台化的交互骨架；
- 后端已经具备可扩展的编排式 Prompt 引擎结构；
- 主要问题不在架构失真，而在抽离过程中有一段页面编排没有收口。

本次修复解决的是“前端看起来像样式没渲染好”的主要成因：

- 主工作流左列缺失
- Quick Start 与模式流转脱节
- 设计 token 未闭环

修复后，当前页面已经恢复为可以正常使用、结构完整的 Prompt Agent 工作台。
