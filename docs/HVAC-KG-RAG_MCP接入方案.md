# HVAC-KG-RAG MCP 接入方案

> 状态：方案待确认（2026-08-10）。纯方案、不含代码实现。
> 目标：把 `D:\KG_Test`（HVAC-KG-RAG，ArchRAG V3.41 混合检索终端）接入 WorkBuddy，**替代 Streamlit 网页作为日常交互前端**，同时作为 MCP 架构能力的面试证据（与 MinerU MCP 互补）。

---

## 1. 背景与动机

### 1.1 现状

- **KG_Test 是 Streamlit 单体**（`main_rag.py` 封装 Streamlit 启动 `rag/app.py`），没有 HTTP API 服务层。
- 交互范式 = 开浏览器 → 填表单 → 点按钮 → 等刷新，**僵化、不便追问**。
- 检索核心是干净的 Python 函数（`HybridRetriever.search` / `ResponseGenerator.generate_sync`），可被任意进程 import 复用。
- 数据依赖：Neo4j（图谱 478 节点/417 关系）+ chroma_db + BGE 模型，**全在容器/本机 GPU 环境**。

### 1.2 动机

| 动机 | 说明 |
|------|------|
| 替代 Streamlit 前端 | WorkBuddy 对话界面 = 新前端，不用维护表单页面；AI 自动完成「意图→参数→调用→呈现」 |
| MCP 面试证据 | 与 MinerU MCP 互补成「文档解析 + 知识库检索生成」MCP 全家桶，对口 iTechChoice MCP 岗位叙事 |
| 沉淀服务化能力 | 顺带把 KG_Test 服务化（API 层），为将来对外提供能力打底 |

---

## 2. 架构选型：HTTP 服务层 + 薄壳 MCP 客户端（参照 MinerU 已验证模式）

### 2.1 为什么不用「进程内直接 import」方案 A

上轮讨论提出方案 A（MCP Server 直接 import KG_Test）。结合 MinerU MCP 的实战验证，**方案 B'（HTTP 服务层 + 薄壳客户端）更优**：

| 维度 | A：进程内 import | B'：HTTP 服务层 + 薄壳 MCP（推荐） |
|------|------------------|--------------------------------------|
| 模型加载 | MCP server 每次启动都加载 2×BGE（~6GB+），启动慢、占显存 | 服务层常驻，模型加载一次；MCP 薄壳是轻量 requests 客户端 |
| 环境隔离 | MCP server 需与 KG_Test 同 Python 环境（依赖冲突风险） | 服务层独立环境跑；MCP 端仅需 requests（MinerU 已验证） |
| 故障边界 | 模型崩 = MCP server 崩 = 整个会话不可用 | 服务层崩，MCP 返回 error hint，WorkBuddy 会话不崩 |
| 复用 | 每次接入新客户端都重复加载模型 | 任意客户端（MCP/CLI/网页）都走同一 HTTP 入口 |
| 面试话术 | 「我包了一层 import」 | 「我做了服务化 + MCP 协议适配」——更高级 |

> 结论：**参照 MinerU 已验证的「跨服务 HTTP 纯客户端」模式**（`mcp_server_mineroo.py`），KG_Test 侧新增服务层，MCP 侧做薄壳。

### 2.2 目标架构

```
WorkBuddy 对话界面
      │  自然语言
      ▼
AI 代理（决定调哪个工具、传什么参数）
      │  MCP 协议（stdio 本地）
      ▼
mcp_server_hvac.py（薄壳客户端，仅 requests）
      │  HTTP (127.0.0.1:8510)
      ▼
hvac_service.py（新增服务层：FastAPI/Flask，进程内 import KG_Test）
      │  直接调用（常驻，模型加载一次）
      ▼
HybridRetriever.search / ResponseGenerator.generate_sync（KG_Test 核心，零改动）
```

- **MCP 端**：`mcp_server_hvac.py`，纯客户端（`requests`），与 MinerU MCP 同构。
- **服务端**：`hvac_service.py`，新增 HTTP 服务，进程内 import KG_Test 核心，常驻加载模型。
- **KG_Test 本体**：零改动。

---

## 3. 服务端设计（hvac_service.py）

> 本方案只锁定「要有这样一个服务层」，**具体框架（FastAPI/Flask）留到实现时定**（KG_Test requirements 已有 Flask 3.1.2，但 FastAPI 更适合 async 生成接口——实现时对比后锁定）。

### 3.1 接口清单（3 个）

| 接口 | 方法 | 功能 | 关键设计 |
|------|------|------|----------|
| `/health` | GET | 服务自检（模型/Neo4j/chroma 可达性） | 面试演示先调它，返回各依赖状态 |
| `/search` | POST | 规范/知识库检索，返回 top_k 上下文 | 输入 query + top_k；输出含来源/图谱实体/正文片段 |
| `/generate` | POST | 检索 + 融合生成完整回答/交底 | 输入 query + 可选参数；异步长任务（首轮 120s 模型懒加载） |

### 3.2 关键设计点

1. **长请求超时**：`/generate` 首轮 120s、二次 90s → HTTP 超时设 300s；MCP 端 timeout 同步放大（参照 MinerU `REQUEST_TIMEOUT=600`）。
2. **体积控制**：检索结果/生成结果都做截断预览（参照 MinerU `PREVIEW_CHARS=1500`），避免把大文本倒进 LLM 上下文。
3. **错误不崩溃**：服务不可达/Neo4j 挂 → 返回 `{status:"error", hint:"...启动命令"}`，不抛异常（MinerU 已验证模式）。
4. **环境变量**：复用 CleanDoc 验证过的 6 变量（`KG_TEST_ROOT` / `CLEANDOC_ROOT` / `DEEPSEEK_API_KEY` / `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`），服务层直接读。
5. **常驻模型**：服务进程启动即加载 2×BGE（~6GB，RTX 3090 24G 充足），之后每次请求 <2s。

---

## 4. MCP 端设计（mcp_server_hvac.py）

> 参照 `mcp_server_mineroo.py` 结构，纯客户端薄壳。

### 4.1 工具清单（3 个）

| 工具 | 对应接口 | 功能 | 返回 |
|------|----------|------|------|
| `health_check` | `/health` | 检查 HVAC-KG-RAG 服务是否存活 | `{hvac_service: ok/down, hint}` |
| `search` | `/search` | 规范/知识库检索，返回 top_k 上下文 | 来源 + 图谱实体 + 正文预览（截断） |
| `generate` | `/generate` | 融合生成回答（交底/问答） | Markdown 结果 + 溯源（截断） |

### 4.2 与 MinerU MCP 的差异化定位

| | MinerU MCP | HVAC-KG-RAG MCP |
|---|---|---|
| 能力 | 文档解析（PDF→MD） | 知识库检索 + 融合生成（RAG） |
| 面试叙事 | 文档智能解析 | 知识图谱 + 双路检索 + 生成 |
| 场景 | 输入 PDF 出结构化文本 | 输入问题出带溯源的回答 |
| 合体 | 「MCP 全家桶」：解析 + 检索 + 生成，完整能力链 |

---

## 5. 接入 WorkBuddy（登记 mcp.json）

在 `C:\Users\Administrator\.workbuddy\mcp.json` 追加（与已接入的 mineru 同构）：

```json
{
  "mcpServers": {
    "hvac-kg-rag": {
      "command": "C:/Program Files/Python312/python.exe",
      "args": ["D:/KG_Test/mcp/mcp_server_hvac.py"],
      "disabled": false
    }
  }
}
```

> 注意：`command` 用能访问服务的 Python 即可（薄壳只要 requests）；若服务层独立 venv，MCP 端可指向该 venv 的 python。重启 WorkBuddy 后生效。

---

## 6. 实施步骤（实现阶段，非现在）

| 步骤 | 内容 | 预估 |
|------|------|------|
| 1 | 写 `hvac_service.py`（服务层，FastAPI/Flask 二选一） | 0.5 天 |
| 2 | 写 `mcp_server_hvac.py`（薄壳客户端） | 0.25 天 |
| 3 | 本机起服务层 + 冒烟（health/search/generate 三接口） | 0.5 天 |
| 4 | 登记 mcp.json + 重启 WorkBuddy + 对话实测 | 0.25 天 |
| 5 | 面试话术卡 + 演示 SOP 更新 | 0.25 天 |

**总计约 1.75 天**。建议面试后实施，或面试前时间充裕时做 1-4 步。

---

## 7. 决策点（实现时确认）

| # | 决策项 | 初步倾向 | 原因 |
|---|--------|----------|------|
| 1 | 服务层框架：FastAPI vs Flask | FastAPI | 支持 async 生成接口、自带 OpenAPI 文档（面试可展示） |
| 2 | 服务层运行位置：容器内 vs 本机 | 待定 | 容器内已装依赖但 GPU 共享；本机需配环境——实现时对比 |
| 3 | 服务层端口 | 8510（避开 8501/8502） | 不与 Streamlit/CleanDoc 冲突 |
| 4 | 是否保留 Streamlit | 保留 | 零成本，可作「网页版 vs 对话版」对照演示 |

---

## 8. 与面试准备的联动

- **不挤占主线**：录屏已取消（改 Live 演示），本方案是 MCP 能力证据链的第二块拼图，面试后实施。
- **Live 演示注意点**（替代录屏）：容器活着 + 模型预热（先跑一次）+ VPN 坑规避（`--proxy-bypass-list="<-loopback>"`）+ 服务层 health 先行自检。
- **面试话术**：从「我包了一层 import」升级为「我做服务化 + MCP 协议适配，MinerU 和 HVAC-KG-RAG 走同一模式」。

---

## 附：风险与对策

| 风险 | 对策 |
|------|------|
| 服务层与 KG_Test 依赖冲突 | 服务层独立 venv 或容器，与 MCP 薄壳解耦 |
| 模型加载占显存（~6GB） | 服务层常驻一次加载；演示期已停 archrag-core，显存充足 |
| `/generate` 首轮 120s 卡顿 | 服务层预热（启动即跑一次空检索）；MCP timeout 300s |
| 服务层挂了 WorkBuddy 会话崩 | MCP 端捕获异常返回 hint（MinerU 已验证），会话不崩 |
