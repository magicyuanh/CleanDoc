# 洁净室施工技术交底自动生成 MVP — PRD（CleanDoc）

> 目标：基于你已有的 ArchRAG（HVAC-KG-RAG，位于 `D:\KG_Test`）混合检索系统，在其之上**独立衍生**一个「洁净室施工技术交底自动生成」MVP，代号 **CleanDoc**，作为简历中「施工文书自动生成」的真实落地案例。
> 核心原则：**CleanDoc 是独立项目，零拷贝、零修改 `D:\KG_Test`**——所有检索/生成/模型/知识库资产均原位引用（`import`），不改 KG_Test 一行代码。
> 状态：**v2 拍板版（2026-07-31）**。6 项决策 + 2 项🔴修正已拍板并入文（见 §10 追加）；仅 PRD 修订，未写程序代码。

---

## 1. 背景与目标
- JD 职责③要求落地「施工文书自动生成」类 AI 场景。你的知识库已含洁净室规范（GB 50073 / GMP 等），技术交底是最契合 RAG 能力（检索规范条文 + 生成结构化文书）的施工文书类型，且洁净室是高门槛细分，生成有真实规范兜底、面试可信度高。
- MVP 目标：输入「项目 + 分项工程 + 部位 + 关键参数」→ **双路检索**（规范路复用 KG_Test + 项目背景路 CleanDoc 自建库）→ 融合生成**结构化技术交底草稿**。
- 非目标：不是全量施工资料系统，不替代人工复核签字。

## 2. 现有资产盘点（全部原位引用，不重建、不拷贝）
| 资产 | 位置（`D:\KG_Test` 内） | 复用方式 |
|---|---|---|
| 混合检索（向量+BM25+图谱→RRF→Reranker） | `rag/retriever.py` | 经 CleanDoc `adapter` 层 `import` 调用，不改 |
| 生成器（DeepSeek） | `rag/generator.py` | 经 `adapter` 调用其生成接口；交底提示词由 CleanDoc 提供，不改 KG_Test |
| 洁净室规范 KB | `jsonl/structured_chunks.jsonl`、`graph/neo4j_nodes.csv`、`table_full_coverage.jsonl`、`Global_HVACR_Ontology_Policy` | 已索引，原位被检索命中 |
| 嵌入/重排模型 | `models/bge-large-zh-v1.5`、`models/bge-reranker-large` | 原位加载，不重训、不复制 |
| DeepSeek | API（`DEEPSEEK_API_KEY`） | 经 KG_Test 配置调用 |

> 关键机制：`config.py` 的 `base_dir = os.path.dirname(os.path.abspath(__file__))`，即**锁定在 KG_Test 自身目录**。因此 CleanDoc 只要把 `D:\KG_Test` 加入 `sys.path` 再 `import` 其模块，`base_dir` 自动解析为 KG_Test，chroma_db / bm25 / models / jsonl / policy / Neo4j 全部自动指向 KG_Test 原位资产——**无需任何拷贝**。

## 3. 范围边界（关键，决定诚实性）
### IN（MVP 内）
- 领域：**洁净室（cleanroom）建筑施工**，作为首个落地场景。
- 文书类型：**技术交底**（含「安全交底」作为同模板的变体选项，更贴 JD 的"安全"关键词）。**决策⑧：安全交底做**——UI 加「技术/安全」切换 + 写 `safety_disclosure.md` 并接入；前置：先冒烟验证 KG_Test 能检索出安全类条文，搜不到则降级为「模板占位不接入」。
- 输入：分项工程类型（围护结构 / 净化空调 / 工艺管道 / 电气 / 地面 / 调试）、部位、关键参数（洁净度等级、温湿度、压差等）。**决策⑦：6 类全枚举，MVP 实测 4 类（围护 / 净化空调 / 工艺管道 / 电气），对齐指标①「≥4 类」**。
- 输出：结构化技术交底草稿——工程概况 / 施工准备 / 操作工艺 / 质量标准 / 安全事项 / 验收要求。
- 检索：**双路**。规范路 = 复用 KG_Test 现有混合检索（**含图谱分支，决策①**）；项目背景路 = CleanDoc 自建轻量向量库（见 4.6）。
- **项目背景库**：CleanDoc 内自建轻量向量库，存放项目实际背景资料（如脱敏后的金茂广场 / 三一南方总部参数、本项目特定要求），与规范库解耦，增删项目不碰 KG_Test。**资料形态：md/txt 手写脱敏（决策⑮）**，不经 MinerU 解析（MVP 资料量小，手写最稳、不增依赖）。
- 标注：UI 明确标注「MVP · 辅助起草，需人工复核签字」。

### OUT（MVP 外，明确不做）
- ❌ 修改 `D:\KG_Test` 任何源码（adapter 仅 `import`，不改）。
- ❌ 拷贝 KB / 模型 / 向量库 / 图谱到 `D:\clean doc`（原位引用即可）。
- ❌ 全量施工资料系统（检验批、隐蔽工程记录、竣工图等）。
- ❌ 洁净室以外的建筑类型（架构支持扩展，但 MVP 只做洁净室）。
- ❌ 模型训练 / 微调（纯提示词 + 检索，不碰 BGE/DeepSeek 权重）。
- ❌ 修改 KG_Test 的知识库 / 模型 / 向量库（规范 KB 保持原位；项目背景库在 CleanDoc 自建，见 4.6）。
- ❌ 用户系统 / 多租户 / 生成结果持久化（MVP = 会话内输出，可复制/导出）。

## 4. 技术方案
### 4.1 双路融合链路（运行在 CleanDoc，规范资产取自 KG_Test，项目背景库在 CleanDoc 自建）
```
用户输入(项目 + 分项/部位/参数)  [CleanDoc app.py 表单]
│
├─ 第一路：规范要点（KG_Test 原位，零改动）
│    query₁ = 「洁净室 {分项} 施工规范要点 / 质量标准 / 安全要求」
│    → adapter 调 KG_Test HybridRetriever.search(query₁)        # 原位混合检索
│    → adapter 调 KG_Test ResponseGenerator.generate_sync(query₁, ctx₁)  # 用 KG_Test 自带问答台本生成规范要点文本 A
│
├─ 第二路：项目背景（CleanDoc 自建向量库）
│    query₂ = 「{分项} 施工 项目背景 实际参数」
│    → CleanDoc 自建 project_kb 检索（复用 KG_Test 的 BGE 嵌入，库文件存 D:\clean doc\project_kb，不碰 KG_Test）
│    → 返回项目背景文本 B（脱敏后的本项目特定要求）
│
└─ 融合生成（CleanDoc，最终交底）
     prompt = 技术交底模板系统提示词 + "规范要点:" + A + "项目背景:" + B + 表单参数
     → CleanDoc 调 KG_Test 底层 LLMClient.call_llm(prompt, temperature≈0.2)   # 绕过写死的 ResponseGenerator
     → 结构化 Markdown 交底 + 证据链面板   [CleanDoc app.py 渲染]
```

### 4.2 CleanDoc 分层文件结构（D:\clean doc）
```
D:\clean doc\
│
├── .env                      # 密钥：DEEPSEEK_API_KEY / NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD
├── .gitignore
├── README.md                 # 项目说明、运行步骤、依赖
├── requirements.txt          # 版本锁定清单：方案 A 零补装；保留为记录（从镜像 freeze 一份，决策⑫）
├── clean_config.py           # ⚠️ CleanDoc 自身配置（KG_Test 路径、启用交底类型）
│                              #    特意不叫 config.py，避免与 KG_Test 的 config.py 重名冲突
│
├── app.py                    # 【表现层】Streamlit 入口：表单 + 调 service + 渲染结果
│
└── src\                      # 【核心代码层】
    ├── __init__.py
    │
    ├── adapter\              # 【适配层】唯一 import KG_Test 的地方
    │   ├── __init__.py
    │   └── kg_test_adapter.py   # sys.path 指向 D:/KG_Test，import HybridRetriever / ResponseGenerator / LLMClient / SystemConfig
    │
    ├── domain\              # 【领域层】纯逻辑，零 KG_Test 依赖
    │   ├── __init__.py
    │   ├── disclosure_schema.py   # 交底输出结构（施工准备/操作工艺/质量标准/安全事项）
    │   ├── project_types.py       # 分项工程类型枚举 + 默认参数（6 类全枚举，MVP 实测 4 类，决策⑦）
    │   └── prompts\               # 提示词模板分层存放，便于维护
    │       ├── __init__.py
    │       ├── technical_disclosure.md   # 技术交底提示词
    │       └── safety_disclosure.md      # 安全交底变体（决策⑧：做并接入）
    │
    ├── project_kb\          # 【项目背景库·代码层】仅放代码；运行时数据在 src 外（见下方 project_kb\ 运行时目录）
    │   ├── __init__.py
    │   ├── build_index.py      # 入库：读 D:\clean doc\project_kb\data\ 资料切片（~500 字符，决策⑨）→ 复用 KG_Test 的 BGE 嵌入存 chroma + jieba 建 BM25（库落 D:\clean doc\project_kb）
    │   └── project_retriever.py # 混合检索(向量+BM25)：复用 KG_Test 的 FusionLayer(RRF)，返回项目背景文本 B（🔴2 无 RerankModel）
    │
    └── service\             # 【应用/生成层】编排：双路检索 → 融合生成
        ├── __init__.py
        └── disclosure_service.py   # 入参(project, project_type, location, params)
                                    #   → 第一路 adapter(KG_Test search+generate) → 规范要点 A
                                    #   → 第二路 project_kb 检索 → 项目背景 B
                                    #   → 拼交底模板+AB → LLMClient.call_llm → 结构化交底
│
├── project_kb\             # 【项目背景库·运行时数据，src 外】由 build_index.py 生成；不进版本库（见 .gitignore）
│   ├── data\               # 项目背景原始资料（脱敏后的金茂/三一参数、本项目要求等）← 你提供，不编造；MVP 先用「示例」占位资料跑通（决策③）
│   │   └── *.md / *.txt
│   ├── (chroma 持久化文件，由 chromadb.PersistentClient(path="D:/clean doc/project_kb") 自动生成，collection=project_kb)
│   └── bm25.pkl            # BM25 索引（pickle 落盘，结构同 KG_Test：{"bm25","chunks"}）
│
└── tests\                   # 【测试层】MVP 拍板为**不写正式 pytest**（决策④），测试层仅作可选项保留，功能验收靠 §6 冒烟验证兜底
    └── test_disclosure.py
```
**各层职责**
- **adapter**：唯一接触 KG_Test 的层；从 `clean_config.KG_TEST_ROOT` 取路径后 `sys.path.insert` 再 `import` 检索/生成模块（不写死 `D:/KG_Test`，🔴1）。换母体时只改这一层。
- **domain**：交底结构、分项工程元数据、提示词模板——纯业务，可单独测试，不依赖 KG_Test。
- **service**：把表单输入翻译成"检索 query + 交底提示词"并串联 adapter，是 MVP 大脑。
- **app（表现层）**：只收表单、调 service、显示，不含业务逻辑。证据链面板仅展示「规范要点 A + 项目背景 B」两段文本及各自来源（KG_Test / project_kb），**不展示 score/文件列表**（决策⑤）。**证据链展示时机：分步展示（决策⑪）**——先「规范要点」→ 再「项目背景」→ 最后「交底」，录屏演示体现双路。**项目下拉来源：动态扫描 `project_kb/data/` 文件名（决策⑥）**，增删项目不碰代码。

### 4.3 配置与依赖（坑位清单）
- **`.env` 位置**：`load_dotenv()` 读的是**当前工作目录**的 `.env`。在 `D:\clean doc` 运行，就在此放一份**仅含密钥**的 `.env`（DEEPSEEK_API_KEY / NEO4J_*）；模型路径仍走 KG_Test 默认，不在此配。- **config 命名**：CleanDoc 配置命名为 `clean_config.py`，**不得叫 `config.py`**，否则与 KG_Test 的 `config.py` 在 `sys.path` 上撞名导致 import 混乱。
- **Neo4j 依赖**：图谱检索需 Neo4j 服务运行；**MVP 已拍板启用图谱分支（决策①）**，故 `archrag-neo4j` 容器**必须保持运行**（CleanDoc 运行期间不停）。`NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` 从 KG_Test 挂载 `.env` 继承。
- **⚠️ 严禁在 `D:\clean doc\.env` 设 `ARCHRAG_BASE_DIR`**：`config.py` 的 `base_dir = os.getenv("ARCHRAG_BASE_DIR", os.path.dirname(os.path.abspath(__file__)))`。若 CleanDoc 的 `.env` 设了它，会覆盖 `base_dir` 为 `D:\clean doc\models\...`（不存在）→ 模型加载直接崩溃。正确做法：`.env` **只放 `DEEPSEEK_API_KEY` / `NEO4J_*`**，让 `base_dir` 自然落到 KG_Test（机制详解见 4.8）。
- **代码改动量**：KG_Test 侧 = 0 改动；CleanDoc 侧 = 上述分层文件 + `.env`，均为新建。

### 4.4 生成接口适配（零修改 KG_Test 的关键）
本架构把"生成"拆成两段，恰好规避了 KG_Test `ResponseGenerator.generate_sync` 系统提示词写死的约束：
- **第一路（规范要点）**：直接复用 KG_Test 既有能力——`adapter` 调 `HybridRetriever.search(query₁)` 拿到上下文后，再调 `ResponseGenerator.generate_sync(query₁, ctx₁)`。KG_Test 自带的问答台本此时正好用来"提取规范要点"，**无需改 KG_Test、也无需求改提示词**，产出的规范说明文本 A 作为第二段的原料。**图谱分支（决策①，审核修正）**：源码核对确认 `HybridRetriever` 的图谱**无开关，是默认启用 + 自动降级**——`GraphRetriever()` 无条件构造（`rag/retriever.py:76`），`search()` 无条件调 `query_graph(...)`（`:132`）；Neo4j 连不上时 `is_active=False` 自动降级为「向量+BM25」照常返回。因此 adapter **无需任何"显式启用"动作**，正常 `import` 构造即可；真正前置是 **Neo4j 服务可达**（冒烟加"Neo4j 连通性"检查）。
- **第二路（项目背景）**：CleanDoc 自建 `project_kb` 向量库检索（见 4.6），返回项目特定资料文本 B。
- **融合段（最终交底）**：CleanDoc `service` 把「技术交底模板系统提示词 + 规范要点 A + 项目背景 B + 表单参数」整体拼成 `prompt`，调 KG_Test 底层 `LLMClient.call_llm(prompt, model_name, temperature=0.2)`。此 `call_llm` 的 `prompt` 参数由调用方完全掌控，**彻底绕开写死的问答台本**，自有交底台本得以生效。
- 提示词要点（置于 `domain/prompts/`）：以「洁净室施工技术专家」身份，严格基于【规范要点】与【项目背景】按固定模板生成；关键条款标 `[1][2]` 引用；上下文未收录内容明确写「需项目总工核定」，禁止编造。

### 4.5 参数默认值
- `top_k` **8**（决策⑩，两路统一；比 QA 略高，保证规范条款覆盖；BGE 512 token 限制内安全）。
- `temperature` 0.3（事实性与可读性平衡，仍强制引用防幻觉）。
- **切片策略：按 ~500 字符切 chunk（决策⑨）**——对齐 BGE 512 token 硬约束（`build_index.py` 的 `_read_chunks` 不再仅按空行分段，改为空行分段 + 超长截断/合并到 ≤500 字符）。
- 不新增 KG_Test 环境变量、不改其 `config.py`、不碰 `models/`。

### 4.6 项目背景库（CleanDoc 自建 · 混合检索，解耦规范库）
- **定位**：规范（通用、静态）存于 KG_Test 原位；项目背景（特定、动态）存于 CleanDoc 自建库 `D:\clean doc\project_kb`，二者解耦。CleanDoc 增删项目只动自身库，绝不触碰 KG_Test。本库采用与 KG_Test 一致的**混合检索（向量 + BM25）**，仅省略图谱路（项目库无 Neo4j）。
- **构建**（`src/project_kb/build_index.py`）：
  1. 读取 `D:\clean doc\project_kb\data\` 下脱敏项目资料（金茂广场 / 三一南方总部参数、本项目特定要求等）→ 切片（该目录在 src 外，与 4.2 树一致）。
  2. **向量路**：复用 KG_Test 的 `bge-large-zh-v1.5`（`SystemConfig().embedding_model_path`）对切片做嵌入 → 存入 chroma（路径 `D:\clean doc\project_kb`，collection 名如 `project_kb`）。
  3. **BM25 路**：用 `jieba` 对切片做分词 → 以 `rank_bm25.BM25Okapi` 建索引 → pickle 落盘（如 `D:\clean doc\project_kb\bm25.pkl`，结构同 KG_Test：`{"bm25":<obj>, "chunks":[...]}`）。
- **检索**（`src/project_kb/project_retriever.py`）：**不能用 KG_Test 的 `HybridRetriever`**（其 `chroma_db_path` / `bm25_index_path` 在 `config.py` 中写死指向 KG_Test，无法指向 project_kb）。改为在 CleanDoc 内写一个薄 `ProjectRetriever`：
  - 向量路：`chromadb.PersistentClient(path="D:/clean doc/project_kb").get_collection("project_kb")` + `SentenceTransformer(SystemConfig().embedding_model_path)` 编码 query；
  - BM25 路：加载 `bm25.pkl`，`jieba.cut(query)` 后 `bm25.get_top_n(...)`；
  - **融合直接复用 KG_Test 现成模块**：`from rag.fusion import FusionLayer`（RRF，rrf_k=60）融合向量+BM25 → 归一化 `UnifiedContext` 返回项目背景文本 B（**🔴2 拍板：不做 RerankModel 精排**，省 6.3GB 显存，理由见 §10.2）。
  - 即：project_kb 的"建库/检索"是新建的，但**融合算法、嵌入模型全部复用 KG_Test，零重造轮子、零重下模型**（重排按 🔴2 刻意不用）。
- **内容很少时的取舍**：项目资料规模小，BM25 与向量的增益差异有限，混合检索主要价值是**与 KG_Test 架构一致、鲁棒性更好**；若追求极致简洁，project_kb 仅用 chroma 向量检索也成立。**MVP 拍板：项目库仅用「向量 + BM25 + RRF 融合」，跳过 RerankModel（🔴2）**——省 6.3GB 显存与加载时间，对小型项目库质量无损（理由见 §10.2）。
- **诚实性**：`data/` 中资料须为真实脱敏内容或明确标注的"示例项目"；简历写"基于示例项目验证"而非"金茂广场真实应用"，不夸大。

### 4.6.1 建库代码（`src/project_kb/build_index.py`，精确可跑）
> 经源码核对（`D:\KG_Test\rag\fusion.py`、`reranker.py`、`retriever.py`、`core\models.py`）。建库复用 KG_Test 的 `bge-large-zh-v1.5`（`SystemConfig().embedding_model_path` 自动指向母体 `models/`），库文件全部落在 `D:\clean doc\project_kb`，零拷贝、零下载、零修改 KG_Test。
```python
# -*- coding: utf-8 -*-
import os, sys, glob, pickle, jieba
import chromadb
import torch

# 指向母体 KG_Test，复用其 SystemConfig / 嵌入模型（原位，零下载、零修改）
# 🔴1：路径取自环境变量（容器 /app、/clean_doc；本机 D:/KG_Test、D:/clean doc），不写死
sys.path.insert(0, os.getenv("KG_TEST_ROOT", r"D:\KG_Test"))
from config import SystemConfig
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

BASE = os.getenv("CLEANDOC_ROOT", r"D:\clean doc")       # 🔴1 环境变量解析
DATA_DIR = os.path.join(BASE, "project_kb", "data")
CHROMA_DIR = os.path.join(BASE, "project_kb")      # chroma 持久化目录（CleanDoc 自身）
BM25_PATH = os.path.join(BASE, "project_kb", "bm25.pkl")
COLLECTION = "project_kb"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_CHUNK_CHARS = 500   # 决策⑨：对齐 BGE 512 token 硬约束（约 500 字符）


def _split_para(para: str, limit: int = MAX_CHUNK_CHARS):
    """段落超长时按 500 字符切分，返回多段（避免 BGE 编码截断）。"""
    para = para.strip()
    if len(para) <= limit:
        return [para]
    out = []
    for i in range(0, len(para), limit):
        out.append(para[i:i + limit])
    return out


def _read_chunks(data_dir):
    """读取 data/ 下所有 .md/.txt，按空行分段 + 超长按 500 字符截断（决策⑨）。"""
    chunks = []
    for fp in glob.glob(os.path.join(data_dir, "**/*"), recursive=True):
        if not fp.endswith((".md", ".txt")):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()
        idx = 0
        for para in (p.strip() for p in text.split("\n\n") if p.strip()):
            for seg in _split_para(para):
                chunks.append({"content": seg,
                               "metadata": {"source_file": os.path.basename(fp), "chunk_idx": idx}})
                idx += 1
    return chunks


def build():
    cfg = SystemConfig()                       # base_dir 自动锁 KG_Test，embedding_model_path 指向其 BGE
    chunks = _read_chunks(DATA_DIR)
    if not chunks:
        print("[BUILD] data/ 为空，跳过。")
        return

    # 1) 向量路：复用母体 BGE 编码 → 存 chroma（重建时先清旧集合）
    embed_model = SentenceTransformer(cfg.embedding_model_path, device=DEVICE)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    col = client.get_or_create_collection(COLLECTION)
    contents = [c["content"] for c in chunks]
    embeddings = embed_model.encode(contents, normalize_embeddings=True).tolist()
    col.add(ids=[f"p{i}" for i in range(len(chunks))],
            documents=contents, embeddings=embeddings,
            metadatas=[c["metadata"] for c in chunks])

    # 2) BM25 路：jieba 分词建索引 → pickle 落盘（结构同 KG_Test: {"bm25","chunks"}）
    tokenized = [list(jieba.cut(c["content"])) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(BM25_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)

    print(f"[BUILD] 完成：{len(chunks)} 条 → chroma({COLLECTION}) + bm25.pkl")


if __name__ == "__main__":
    build()
```

### 4.6.2 检索代码（`src/project_kb/project_retriever.py`，精确可跑）
> 薄封装 `ProjectRetriever`，**不复用 `HybridRetriever`**（其 `chroma_db_path`/`bm25_index_path` 写死指向 KG_Test），但融合算法 `FusionLayer`、数据契约 `UnifiedContext`、嵌入 `SystemConfig` **全部复用母体**，调用约定与 `HybridRetriever.search` 一致（见下：向量+BM25 → RRF 融合 → 归一为 UnifiedContext）。
> **🔴2（拍板）**：本项目检索**跳过 `RerankModel`**（仅向量+BM25+RRF，不精排），省 6.3GB 显存与加载时间，对小型项目库质量无损（理由见 §10.2）。
```python
# -*- coding: utf-8 -*-
import os, sys, pickle, jieba
import chromadb
import torch
from typing import List

# 指向母体 KG_Test，复用 FusionLayer / SystemConfig / UnifiedContext
# 🔴1：路径取自 clean_config 环境变量，不写死
sys.path.insert(0, os.getenv("KG_TEST_ROOT", r"D:\KG_Test"))
from config import SystemConfig
from rag.fusion import FusionLayer
from core.models import UnifiedContext
from sentence_transformers import SentenceTransformer

BASE = os.getenv("CLEANDOC_ROOT", r"D:\clean doc")       # 🔴1 环境变量解析
CHROMA_DIR = os.path.join(BASE, "project_kb")
BM25_PATH = os.path.join(BASE, "project_kb", "bm25.pkl")
COLLECTION = "project_kb"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class ProjectRetriever:
    """CleanDoc 项目背景库检索：向量 + BM25 双路 → FusionLayer(RRF) → 归一 UnifiedContext（🔴2 无 RerankModel）。"""
    def __init__(self, config: SystemConfig = None):
        self.cfg = config or SystemConfig()        # 复用母体配置，base_dir 锁 KG_Test
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_collection(COLLECTION)
        self.embed_model = SentenceTransformer(self.cfg.embedding_model_path, device=DEVICE)

        with open(BM25_PATH, "rb") as f:
            bm25_data = pickle.load(f)
        self.bm25 = bm25_data["bm25"]
        self.bm25_chunks = bm25_data["chunks"]

        self.fusion = FusionLayer(rrf_k=60)
        # 🔴2 拍板：不加载 RerankModel（省 6.3GB 显存）；小型项目库 RRF 融合已足够

    def search(self, query: str, top_k: int = 8) -> List[UnifiedContext]:
        recall_n = top_k * 5
        # A. 向量路
        q_vec = self.embed_model.encode(query, normalize_embeddings=True).tolist()
        res = self.collection.query(query_embeddings=[q_vec], n_results=recall_n)
        vector_texts = res["documents"][0] if res.get("documents") else []
        # B. BM25 路
        tokens = list(jieba.cut(query))
        bm25_texts = self.bm25.get_top_n(tokens, [c["content"] for c in self.bm25_chunks], n=recall_n)
        # 阶段2: RRF 文本流融合（与 HybridRetriever 一致的调用约定）
        fused_texts = self.fusion.fuse({"Vector": vector_texts, "BM25": bm25_texts}, top_k=recall_n)
        # 阶段3: 归一化为 UnifiedContext（标记来源 Vector / BM25）→ 直接取 top_k 返回（🔴2 无重排）
        set_vec, set_bm25 = set(vector_texts), set(bm25_texts)
        candidates = []
        for text in fused_texts:
            src = []
            if text in set_vec: src.append("Vector")
            if text in set_bm25: src.append("BM25")
            candidates.append(UnifiedContext(content=text, source="+".join(src) or "Text", score=0.0))
        return candidates[:top_k]
```
- **返回**：`List[UnifiedContext]`（与 KG_Test 检索↔生成数据契约一致），`disclosure_service` 直接取 `.content` 拼进交底 prompt 作为「项目背景 B」。
- **与 KG_Test 的一致性**：向量用 `normalize_embeddings=True`、BM25 用 `jieba.cut`、融合用 `FusionLayer(rrf_k=60).fuse(...)`、重排用 `RerankModel.rank(...)`——与 `HybridRetriever.search`（retriever.py L103–197）逐行对齐，保证两路检索质量口径统一。

### 4.7 调用接口与数据流细节（零修改实现的核心）
本 MVP 能否「零修改 KG_Test」，取决于对调用接口的精确理解。以下均经源码核对（`D:\KG_Test`，只读）。

**A. KG_Test 写死的系统提示词（为何必须绕过 `ResponseGenerator`）**
- 位置：`D:\KG_Test\rag\generator.py` → `class ResponseGenerator` → `async def generate_async(self, query, context_list)` 内局部变量 `system_prompt = """..."""`（第 63–74 行）；第 97 行 `prompt = f"{system_prompt}\n{user_prompt}"` 传入 `llm.call_llm(...)`；`generate_sync(query, context_list)`（第 107 行）仅为同步桥接 `loop.run_until_complete(self.generate_async(...))`。
- 全文（模型实际收到的纯文本，含空行）：
  > 你是一个精通垂直领域的专家助手。请严格基于提供的【参考上下文】回答用户的【问题】。
  >
  > ## 核心原则：
  > 1. **事实优先**：回答内容必须来源于参考上下文。若信息不足，请直接承认知识库未收录，严禁编造。
  > 2. **强制引用**：在陈述关键事实时，必须在句末标注来源编号，格式为 [1], [2]。
  > 3. **逻辑整合**：不要机械罗列。如果【图谱 (Graph)】提供了逻辑关系，请优先结合【文档 (Vector/Text)】的细节进行综合阐述。
  > 4. **结构清晰**：使用 Markdown 格式（标题、列表）组织答案，语言干练，避免废话。
  >
  > ## 回答格式示例：
  > PPO算法的核心优势在于稳定性[1]。图谱显示它与RLHF存在直接关联[2]...
- 关键约束：该 system prompt 是 `generate_async` 内部常量，**`generate_sync` 不暴露任何自定义提示词参数**。因此 CleanDoc 不把「技术交底模板」塞进 `ResponseGenerator`（否则生成的是「问答腔」，不像正式交底文档），而是在融合段直接调更底层的 `LLMClient.call_llm` 注入自有交底台本。第一路仅借用 `ResponseGenerator` 提取「规范要点文本 A」（问答台本无所谓，反正只是原料）。

**B. 精确调用接口清单（`adapter/kg_test_adapter.py` 需 import）**
```python
import os, sys, asyncio, nest_asyncio
from clean_config import KG_TEST_ROOT, MONITOR_DIR   # 🔴1 路径/监控目录取自环境变量
nest_asyncio.apply()                          # ⚠️ Streamlit 异步兼容，入口必调一次
sys.path.insert(0, KG_TEST_ROOT)              # 🔴1 指向母体（容器=/app，本机=D:/KG_Test），不复制、不写死

from config import SystemConfig              # base_dir 自动锁 KG_Test
from rag.retriever import HybridRetriever     # 检索（图谱分支需按签名显式启用，决策①）
from rag.generator import ResponseGenerator   # 第一路规范要点（问答台本原样用）
from core.llm_client import LLMClient         # 融合段生成（绕过写死的 ResponseGenerator）
from core.monitoring import MonitoringManager # LLMClient 构造依赖（传入 MONITOR_DIR 可写目录，🟡3）
from core.models import UnifiedContext       # 检索↔生成的数据契约
```
- `HybridRetriever.search(query, top_k=5)` → `List[UnifiedContext]`（**注意方法名是 `search`，非 `hybrid_retrieve`**）。
- `ResponseGenerator.generate_sync(query, context_list)` → 字符串（第一路用）。
- `LLMClient.call_llm(prompt, model_name, temperature)` → 字符串（融合段用，`prompt` 整段由 CleanDoc 掌控）。
- `LLMClient` 需异步上下文：`async with LLMClient(cfg, monitor) as llm: await llm.call_llm(...)`；Streamlit 内用 `asyncio.get_event_loop().run_until_complete(...)` 驱动。
- 数据契约 `UnifiedContext`：含 `content / source / score / metadata`，是 KG_Test 定义的检索↔生成「货币」，CleanDoc 直接用。

**C. KG_Test ↔ CleanDoc 数据流（仅返回值流动，无共享存储写入）**
- ① 能力引用（启动即固定）：CleanDoc `import` 各模块 → 构造时自动从 `D:\KG_Test` 加载 chroma/bm25/模型/Neo4j/DeepSeek 密钥（只读引用，源头不动）。
- ② 请求级（每次生成走一遍）：
  - 第一路：表单 → 组 `query₁` → `HybridRetriever.search`（从 KG_Test 的 chroma/bm25/neo4j 召回）→ `List[UnifiedContext]` → `ResponseGenerator.generate_sync` → **规范要点文本 A**（返回 CleanDoc）。
  - 第二路：`build_index` 预处理（脱敏项目资料切片 → 复用 KG_Test 的 BGE 嵌入 → 存 `D:\clean doc\project_kb` chroma）→ 运行时 `project_retriever` → **项目背景文本 B**（返回 CleanDoc）。
  - 融合段：拼「交底模板 + A + B + 表单参数」= 整段 prompt → `LLMClient.call_llm` → 最终结构化交底 → UI。
- 关键边界：KG_Test 的 chroma/bm25/neo4j = 规范数据，CleanDoc 永远只读不写；写只发生在 `D:\clean doc\project_kb`。两套库物理隔离、互不污染。

### 4.8 模型复用机制（零下载、零额外模型调用）
- **证据（`D:\KG_Test\config.py`）**：
  - 第 51–53 行：`base_dir = os.getenv("ARCHRAG_BASE_DIR", os.path.dirname(os.path.abspath(__file__)))` → `__file__` 为 `D:\KG_Test\config.py`，故 `base_dir = D:\KG_Test`。
  - 第 121–122 行：`embedding_model_path = os.path.join(base_dir, "models", "bge-large-zh-v1.5")`；`reranker_model_path = os.path.join(base_dir, "models", "bge-reranker-large")`。
- CleanDoc `import SystemConfig` 时上述代码自动执行，embedding/reranker 直接解析到 `D:\KG_Test\models\...`，**无需写任何模型路径、无需下载**。
- **完全复用的模型资产**：
  | 资产 | 路径 | 复用方式 |
  |---|---|---|
  | Embedding | `D:\KG_Test\models\bge-large-zh-v1.5` | `HybridRetriever` 构造时自动加载 |
  | Reranker | `D:\KG_Test\models\bge-reranker-large` | 同上，精排自动用 |
  | LLM | DeepSeek API | 仅从 `.env` 读 key，无权重可下载 |
- **第二路（project_kb）同样复用同一份 BGE**：建库时用同一个 `bge-large-zh-v1.5` 向量化，仅把项目文档的向量存进 `D:\clean doc\project_kb` 的 chroma 目录；两路向量同模型、同空间，天然可比较 / 可融合，检索还能共用同一 reranker。
- **⚠️ 唯一陷阱：禁止在 `D:\clean doc\.env` 设 `ARCHRAG_BASE_DIR`**（详见 4.3 坑位清单）。

### 4.9 内容归属判别：规范 vs 项目背景（规则驱动，非 LLM 意图识别）
- **唯一判别维度**：通用规范（放之四海而皆准的国家 / 行业标准）走 KG_Test；项目特定（仅本项目独有的信息）走 `project_kb`。两者物理隔离，「这条归谁」无模糊地带。
- **判别发生时刻（仅两处，非逐条判断）**：
  1. **建库时刻**（你唯一需主动判别处）：脱敏项目参数 / 部位 / 等级 / 特殊要求 / 金茂三一启示 → 放 `data/` → `project_kb`；**任何 GB 规范条款、通用工艺、通用验收标准 → 不放**（KG_Test 已有，重复放会污染、让两路检索打架）。
  2. **查询时刻**：无需逐条挑。靠 query 意图驱动——`query₁` 带「洁净室 {分项} 规范 质量 安全」指向规范，`query₂` 带「{项目} {分项} 特殊要求 参数」指向项目；RAG 相似度排序自动筛选相关项回来，不相关不会进融合段。
- **实操清单（净化空调交底示例）**：「风管严密性试验按 GB 50243，漏风率不大于 X%」→ 规范→KG_Test；「高效过滤器通用安装工艺」→ 规范→KG_Test；「本项目洁净度 ISO 7 级、压差 +10Pa」→ 项目→project_kb；「本项目过滤器品牌 / 供货要求」→ 项目→project_kb；「金茂类似项目工期 / 成本经验启示」→ 项目（脱敏）→project_kb。
- **全程规则驱动、无 LLM 意图识别**（LLM 只在融合生成登场）：
  | 环节 | 机制 | 规则 / LLM |
  |---|---|---|
  | 内容归属判别 | 你按准则放文件夹 | 规则（人判断） |
  | 建库切片 + 嵌入 | `build_index` 机械切片 → BGE 嵌入 → 存 chroma | 规则（无 LLM） |
  | 路径路由 | 代码写死 `query₁` / `query₂` 两路 | 规则（硬编码） |
  | 路内检索 | 向量 / BM25 / 图谱相似度 | 规则（无 LLM） |
  | 融合生成交底 | `LLMClient.call_llm(prompt)` | **LLM（仅此处）** |
  - 架构好处：边界由结构保证，不依赖模型判断；两路物理隔离，换项目只改 `project_kb`，KG_Test 规范零维护。

### 4.10 环境与依赖（KG_Test 跑在 Docker，锁定冻结版本，禁止装最新）
- **事实修正（用户指出，2026-07-30）**：KG_Test 实际运行在 **Docker 容器**内，本地没有 venv、也没有全局装那套依赖；且项目是去年（约大半年前）的，期间 `chromadb` / `sentence_transformers` / `transformers` / `torch` / `jieba` / `rank_bm25` 等多数依赖都已大版本更新，API 可能已不兼容。
- **核心原则（必须）**：**锁定 Docker 镜像内的冻结版本，绝不 `pip install` 无版本约束的"最新版"**。CleanDoc import 的每一个 KG_Test 依赖都沿用镜像里的老版本，否则去年代码会因库 API 变更直接崩。模型权重不受影响（在 `D:\KG_Test\models\`，与 pip 包无关，见 4.8）。
- **决策（2026-07-30 拍板，⑭修订）**：采用 **方案 A（同容器运行）**。理由：版本 = 镜像冻结版，零漂移、零重装、不崩旧代码，且 KG_Test 仍完全不动（仅被 import + 只读引用）。**备选方案 B' = 异地 Docker 同构跑**（`docker save/load`，仅当容器不可用时切换；原方案 B 本地 venv 因 ABI 风险已废弃，见 4.10.2）。
- **落地方式**：

  - **方案 A（已采用 · 零版本漂移）**：CleanDoc 直接跑在 **KG_Test 所在的同一个 Docker 容器**里。
    - `D:\clean doc` 以 volume 挂进容器（如 `/clean_doc`），`sys.path.insert(0,"/KG_Test")` 指向容器内既有的 KG_Test 源码；KG_Test 本身完全不动（仅被 import + 只读引用）。
    - 补装包（实测 2026-07-30）：只读探针显示 `streamlit` / `nest_asyncio` / `python-dotenv` **均已在镜像内**，CleanDoc 实际**无需补装任何包**。即便日后需补，也仅 additive 低风险包，不影响已有依赖。
    - 启动：`docker exec ... streamlit run /clean_doc/app.py`。依赖版本 = 镜像冻结版，**零漂移、零重下、零重装**。
    - 代价：开发迭代需经容器（改代码在 Windows 本机，volume 实时同步；运行在容器内），比纯本地略重。

  - **方案 B'（异地 Docker 同构跑 · 决策⑭，已替换原方案 B）**：仅当方案 A（容器不可用）时启用——`docker save kg_test-archrag-app:latest -o kg_test.tar` 导出镜像，在目标机 `docker load -i kg_test.tar` 后照 §4.10.1 命令跑。与容器**完全同构、零 ABI 风险**（原方案 B 的「镜像 pip freeze → 本地 Windows venv」因 torch `2.5.1+cu121` 为 Linux wheel、且系统 Python 3.12 为 embeddable 重建无 venv 模块，本地复刻**高 ABI 风险**，已废弃）。
    - 代价：镜像 6.96GB 需跨机搬运；好处：环境 100% 一致，无需重装任何依赖。

  - **❌ 禁止方案 C（踩坑）**：本地新建 venv 后无脑 `pip install chromadb sentence-transformers torch ...`（latest）。大半年前的 KG_Test 代码会因为这些库的 breaking change 崩——正是你担心的点，务必避免。

- **CleanDoc 额外依赖（实测结论）**：探针验证 `streamlit` / `nest_asyncio` / `python-dotenv` 均已在 `kg_test-archrag-app` 镜像内；KG_Test 全套依赖（`chromadb==1.4.0` / `sentence-transformers==3.3.1` / `rank_bm25` / `jieba==0.42.1` / `torch==2.5.1+cu121` / `transformers==4.46.3` 等）也全部就位。**CleanDoc 放进同容器 = 零额外装包、零重装、不升级、不重下模型**。
- **版本锁定记录**：实现第一步先固定版本来源——方案 A 确认镜像 tag；把精确版本号写进 `requirements.txt`（4.2），作为可复现依据（方案 B' 无需 `requirements.lock`——镜像即锁定）。
- **模型权重**：仍由 `config.base_dir` 原位复用 `D:\KG_Test\models\`，与 pip 包、与版本漂移完全无关。

### 4.10.2 为什么废弃原方案 B（本地 venv 复刻）——决策⑭
- **原方案 B**：`docker exec <kg_test_container> pip freeze > requirements.lock` → 本地 Windows venv 照装同版本 → `sys.path` 指向本机 `D:/KG_Test` 运行。
- **废弃理由（依据 `D:\00 Happy Developer` 环境文档 §14/§17 实机事实）**：
  1. **torch `2.5.1+cu121` 是 Linux wheel**：镜像内为 cu121 构建，Windows 本地无同款 wheel（Windows 用 cu118/cu126+），ABI 不兼容 → `import torch` 即崩或重编译，风险高。
  2. **系统 Python 3.12 是 embeddable 重建**：无 stdlib `venv` 模块（建 venv 需 `virtualenv`），且全局仅 11 个基础包，无 torch 等任何 AI 栈 → 复刻成本接近从零装。
  3. **chromadb==1.4.0 / sentence-transformers==3.3.1 等冻结版本在 Windows 的 wheel 可用性未经验证**，属未知风险。
- **方案 B'（替代）**：`docker save` 导出镜像 → 目标机 `docker load` → 照 §4.10.1 命令跑。镜像=完整的冻结环境，**零 ABI 风险、零重装、跨机 100% 同构**；代价仅镜像 6.96GB 搬运。符合「保守策略控风险」。

### 4.10.1 实测结论与具体运行命令（方案 A · 2026-07-30 验证）
- **实测（进入运行中的 `archrag-core` 容器做只读探针）**：python 3.12.12；`base_dir=/app`（KG_Test 容器内根）；`bge-large-zh-v1.5` 与 `bge-reranker-large` 两模型路径均 `exists=True`；关键包 `chromadb` / `sentence_transformers` / `jieba` / `torch` / `rank_bm25` / `nest_asyncio` / `transformers` / `streamlit` **全部已装**；CleanDoc 需 import 的 KG_Test 模块（`rag.retriever` / `rag.generator` / `rag.fusion` / `rag.reranker` / `core.llm_client` / `core.models` / `core.monitoring`）**全部 import 成功**。
- **结论**：KG_Test 当前**正在运行**（容器 `archrag-core` + `archrag-neo4j` 均 Up），依赖为冻结镜像（`requirements.txt` 用 `==` 全锁版本，镜像 6 个月前构建，含 `torch==2.5.1+cu121` 匹配 RTX 3090）。CleanDoc 放进同一容器**零额外装包、零下模型、`base_dir` 自动锁 `/app`=KG_Test**——方案 A 完全成立，且比预期更省（streamlit / nest_asyncio / python-dotenv 本就在镜像内，CleanDoc 实际**无需补装任何包**）。
- **运行命令（不碰 KG_Test 任何文件，新建独立容器复用其镜像 `kg_test-archrag-app:latest`）**：
```bash
docker run -d --name cleandoc --gpus all -p 8502:8501 \
  -v "D:/KG_Test":/app:ro \
  -v "D:/KG_Test/models":/app/models:ro \
  -v "D:/KG_Test/chroma_db":/app/chroma_db:ro \
  -v "D:/KG_Test/jsonl":/app/jsonl:ro \
  -v "D:/KG_Test/graph":/app/graph:ro \
  -v "D:/KG_Test/.env":/app/.env:ro \
  -v "D:/clean doc":/clean_doc \
  -e ARCHRAG_BASE_DIR=/app \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e KG_TEST_ROOT=/app \
  -e CLEANDOC_ROOT=/clean_doc \
  -e DEEPSEEK_API_KEY=<你的key> \
  kg_test-archrag-app:latest \
  streamlit run /clean_doc/app.py --server.port=8501 --server.address=0.0.0.0
```
  - 说明：KG_Test 以 `:ro` 只读挂入（零修改），CleanDoc 源码挂 `/clean_doc`；`ARCHRAG_BASE_DIR=/app` 确保 `base_dir` 锁 KG_Test；`KG_TEST_ROOT=/app` + `CLEANDOC_ROOT=/clean_doc` 供 `clean_config` 路径解析（🔴1）；`DEEPSEEK_API_KEY` 显式注入作保险（🟡6，避免仅依赖 `/app/.env` 单点）；Neo4j 走宿主机 `host.docker.internal:7687`（compose 已把 7687 publish 到宿主机）；端口 8502 避免与 `archrag-core` 的 8501 冲突。`.env` 从 KG_Test 继承 `DEEPSEEK_API_KEY` / `NEO4J_*`，CleanDoc 容器内无需另建 `.env`（若想独立也可在 `D:\clean doc` 放一份，仅含密钥）。**决策②：采用新建独立容器 `cleandoc`（不回用 `archrag-core` 容器），可随时 `docker rm cleandoc` 干净回滚**。
  - 备选（仅当方案 A 容器不可用时启用，决策⑥，已按 ⑭ 修订）：**方案 B' = 异地 Docker 同构跑**——`docker save kg_test-archrag-app:latest -o kg_test.tar` 导出镜像 → 目标机 `docker load -i kg_test.tar` → 照上方命令跑。原方案 B（本地 venv）因 torch Linux wheel + 系统 Python 无 venv 模块的 ABI 风险已废弃（见 4.10.2）。方案 A 正常时不预建 B' 环境。

## 5. 输入 / 输出定义
- **输入示例**：项目=示例药厂洁净厂房（背景取自 project_kb）；分项工程=围护结构；部位=某药厂洁净车间隔墙；参数=洁净度 ISO 7 级、压差 +10Pa。
- **输出示例（结构）**：
  ```
  # 洁净室围护结构施工技术交底（草稿）
  ## 一、工程概况
  ## 二、施工准备（材料/机具/作业条件）
  ## 三、操作工艺（按规范条款 [1][2] 展开）
  ## 四、质量标准（引用 GB 50073 / 验收指标）
  ## 五、安全事项
  ## 六、验收要求
  > ⚠️ 本交底为 AI 辅助起草，须经项目技术负责人复核签字后生效。
  ```

## 6. 验收 / 度量指标（用于简历写实）
| 指标 | 说明 | 目标 |
|---|---|---|
| ① 覆盖洁净室交底类型数 | 能稳定生成几类分项交底 | ≥4 类（围护/净化空调/工艺管道/电气 等） |
| ② 起草工时节省 | 人工 2~3h → MVP 生成 | 节省 ≥80%（约 5~10min 出草稿） |
| ③ 草稿一次可用率 / 人工修改量 | 工程师小幅修改即可用 | 一次通过率 ≥60%（**决策⑬：MVP 用「自评」测 4 类交底并诚实标注「自评」**） |

> 简历写实时需回填上述 ①②③ 真实数字（做完发我，匹配度 82→88）。

## 7. 风险与诚实声明
- 生成质量依赖于 KB 中洁净室条款深度；若某子项 KB 未收录，生成器已强制「未收录即声明」，不编造——面试可如实说明。
- 简历表述严格写为「施工文书（洁净室技术交底）自动生成 MVP / 辅助起草」，**不夸为全量施工资料系统**。
- 录屏用于面试演示，投递时简历不含录屏文件，仅写实 MVP 能力。
- 技术坑：`.env` 位置、`config.py` 重名、Neo4j 是否运行——见 4.3。

## 8. 实施步骤（独立 CleanDoc 项目，预计 ≤3 天）
1. 在 `D:\clean doc` 按 4.2 结构 scaffold 空目录与占位文件（含 `.env` 模板、`clean_config.py`、`project_kb/`）。
2. 写 `adapter/kg_test_adapter.py`：接入 KG_Test 的 `HybridRetriever` / `ResponseGenerator` / 底层 `LLMClient`（按 4.4 双路适配）。
3. 建 `project_kb/`：放入脱敏项目资料到 `D:\clean doc\project_kb\data\`（src 外运行时目录）→ 写 `build_index.py` 切片 + BGE 嵌入 + 存 chroma（库在 `D:\clean doc\project_kb`）→ 写 `project_retriever.py` 轻量检索。
4. 写 `domain/`：交底结构、分项工程元数据、技术交底 + 安全交底提示词模板。
5. 写 `service/disclosure_service.py`：第一路 adapter(KG_Test search+generate)→ 规范要点 A；第二路 project_kb 检索 → 项目背景 B；拼模板+AB → `LLMClient.call_llm` → 结构化交底。
6. 写 `app.py`：Streamlit 表单（项目 `selectbox` **动态扫描 `data/`**、分项 `selectbox`（6 类枚举，决策⑦）、技术/安全切换（决策⑧）、部位/参数 `text_input`、`生成` 按钮）+ **分步证据链渲染（决策⑪）**：规范要点 → 项目背景 → 交底。**加「复制 Markdown」按钮（决策⑯）**（约 10 行，演示直接复制归档）。**检索日志静音（决策⑰）**：用 `contextlib.redirect_stdout` 包检索调用，演示 UI 干净。
7. 启动测试 4 类洁净室交底（围护/净化空调/工艺管道/电气），自评指标 ①②③（决策⑬）。
8. 录屏演示（双路检索 + 融合生成过程 + 证据链）。
9. 把 ①②③ 发我 → 写实进简历（匹配度 82→88）。

## 9. 排期（用户确认）
- **周五~周日（7/31–8/2）**：按本 PRD 实现 CleanDoc + 录屏（约 3 天，基于现有洁净室 KB）。
- **下周一/二（8/3–8/4）**：回填 ①②③ → 更新简历写实 MVP（82→88）→ 投递目标 JD。
- 风险：岗位提前关帖概率低（JD 要求高、难招到合适人）；投前瞄一眼是否仍在线。

## 10. 已拍板决策汇总（无需再确认）
- 命名：**CleanDoc**；独立文件夹 `D:\clean doc`；PRD 与简历/录屏统一用此名。
- 策略：**原位引用 KG_Test，零拷贝、零修改**（满足"不改 KG_Test 内容"要求）。
- 架构：**双路融合**（规范路复用 KG_Test 原位问答 + 项目背景路 CleanDoc 自建向量库，两路结果融合再生成最终交底）；代码分层（adapter / domain / service / ui / project_kb + tests），不平铺。
- 前端：新建极简 Streamlit 表单，**不复制** KG_Test 的 QA 界面。
- 范围：IN=洁净室技术交底（含安全交底变体）；OUT=全量施工资料/其他建筑类型/训练模型/新增KB/多用户/改 KG_Test。
- 调用接口（已源码核对）：`generator.py` 第 63–74 行 system prompt 写死 → 第一路复用 `ResponseGenerator` 取规范要点、融合段绕开它直调 `LLMClient.call_llm` 注入自有交底台本；检索方法名 `HybridRetriever.search`（非 hybrid_retrieve）；入口必调 `nest_asyncio.apply()`；检索↔生成数据契约 `UnifiedContext`。
- 模型复用：CleanDoc RAG 全部原位复用 KG_Test 的 BGE 嵌入 / 重排 / DeepSeek，`config.base_dir` 自动指向母体，**零下载、零额外模型调用**；`.env` 严禁设 `ARCHRAG_BASE_DIR`（陷阱见 4.3 / 4.8）。
- 内容归属：通用规范归 KG_Test / 项目特定归 `project_kb`，判别仅发生在建库时刻；全链路规则驱动，无 LLM 意图识别，LLM 仅在融合生成登场。
- 两者关系：CleanDoc 是 KG_Test 之上的薄应用层，KG_Test 为单一真相源且零修改；两者仅返回值流动，无共享存储写入。
- 环境（2026-07-30 修正，⑭修订）：KG_Test 跑在 Docker 内（冻结版本，去年项目，大半年未更、依赖有漂移风险）；CleanDoc **锁冻结版本、禁止无约束装最新**，已拍板采用 **方案 A（同容器运行，零漂移，KG_Test 仍零修改）**；备选方案 B'（`docker save/load` 异地同构跑）仅在容器不可用时切换；禁止方案 C（装最新）崩溃旧代码；见 4.10 / 4.10.2。
- 诚实性：标 MVP / 辅助起草，不夸全量。

## 10.1 决策记录（2026-07-31 拍板并入文）
| 决策 | 拍板 | 落点 |
|---|---|---|
| ① 第一路规范检索图谱分支 | **启用图谱** | §3 / §4.3 / §4.4；`archrag-neo4j` 必须保持运行；**审核修正：图谱无开关、默认启用+自动降级**（retriever.py:76,132），adapter 无需显式启用，前置=Neo4j 可达 |
| ② CleanDoc 运行方式 | **新建独立容器 `cleandoc`**（复用镜像，KG_Test 挂 `:ro`） | §4.10.1；回滚=`docker rm cleandoc` |
| ③ 项目库资料 | **先用「示例」占位资料跑通全链路**，真实脱敏资料由用户随后替换 | §4.2 `project_kb/data` 注释；代码零改动可换 |
| ④ tests 层 | **不写正式 pytest**，靠 §6 冒烟验证兜底 | §4.2 tests 注释 |
| ⑤ 证据链 UI | **仅展示规范要点 A + 项目背景 B 两段及来源**，不展示 score/文件列表 | §4.2 app 职责 / §8 实施步骤 6 |
| ⑥ 方案 A 失效 fallback | **方案 B' = 异地 Docker 同构跑**（`docker save/load`；原方案 B 本地 venv 因 ABI 风险废弃，决策⑭） | §4.10.1 备选段 / §4.10.2 |

## 10.2 🔴 修正记录（2026-07-31 评审后并入文）
- **🔴1 路径环境变量化**：所有 CleanDoc 代码不再硬编码 `D:/KG_Test` / `D:/clean doc`；`clean_config.py` 用 `KG_TEST_ROOT` / `CLEANDOC_ROOT` 环境变量解析（容器 `/app`、`/clean_doc`；本机 `D:/KG_Test`、`D:/clean doc`），adapter / `build_index.py` / `project_retriever.py` 全部从 `clean_config` 取路径；容器 run 命令补 `-e KG_TEST_ROOT=/app -e CLEANDOC_ROOT=/clean_doc`（见 4.6.1 / 4.6.2 / 4.10.1）。
- **🔴2 第二路跳过 RerankModel**：`ProjectRetriever` 不加载 `RerankModel`（省 6.3GB 显存），仅向量+BM25+RRF 融合后直接取 `top_k` 返回（PRD 4.6 末段原已许可「小库 rerank 增益有限」）。规避与 KG_Test `HybridRetriever` 双加载 6.3GB 重排模型 → 24G 显存峰值风险。

## 10.3 🟡 优化记录（2026-07-31 并入文）
- **MonitoringManager 可写目录**：CleanDoc 构造 `MonitoringManager` 时传入可写目录（`CLEANDOC_ROOT/monitor` 或 `/tmp/cleandoc_monitor`），避免其写只读 `/app/monitor` 报 `[MONITOR_ERROR]` 噪声。
- **演示期容器策略**：`archrag-core` 可 `docker stop`（CleanDoc 独立容器已自带模型）；但 **`archrag-neo4j` 必须保持运行**（决策①图谱依赖）。**MinerU 无需停（决策⑱）**：CleanDoc 流程不调 MinerU，其空闲时实测仅占 978 MiB/24576 MiB（4%）——停 archrag-core 后 CleanDoc 演示显存约 8.9G，余量充足，不必停 MinerU。
- **先冒烟再盖楼**：动手前先跑 `HybridRetriever.search("洁净室 围护结构 施工规范 质量标准")` 确认 chroma `knowledge_base` 集合真有洁净室条文；空库即停，不演示。**冒烟项加「Neo4j 连通性」（决策①图谱前置）**。
- **DEEPSEEK_API_KEY 保险**：run 命令显式 `-e DEEPSEEK_API_KEY=<key>`（§4.10.1），不单点依赖 `/app/.env`。
- **演示 checklist 加两步（决策⑲）**：① 开浏览器前先查 `ProxyEnable`（环境文档 11.5，极光 VPN 的 localhost 陷阱对 8502 同样生效）；② 演示前 `docker stop archrag-core`（省 7.6G，MinerU 不用停）。

## 10.4 决策记录 2（2026-07-31 二轮拍板并入文）
| # | 决策 | 拍板 | 落点 |
|---|---|---|---|
| ⑦ | 分项工程 MVP 范围 | **6 类全枚举，实测 4 类**（围护/净化空调/工艺管道/电气） | §3 / §4.2 project_types / §8 步骤 7 |
| ⑧ | 安全交底变体 | **做并接入**（UI 切换 + `safety_disclosure.md`）；前置：冒烟验证 KB 有安全条文，搜不到降级为占位 | §3 / §4.2 prompts / §8 步骤 6 |
| ⑨ | 切片策略 | **~500 字符切 chunk**（对齐 BGE 512 token 约束） | §4.5 / §4.6.1 `_read_chunks` 已改 |
| ⑩ | top_k | **两路统一 8** | §4.5 |
| ⑥ | 项目下拉来源 | **动态扫描 `project_kb/data/` 文件名** | §4.2 app 职责 / §8 步骤 6 |
| ⑪ | 证据链展示时机 | **分步展示**（规范要点→项目背景→交底） | §4.2 app 职责 / §8 步骤 6 |
| ⑬ | 指标③可用率测量 | **自评 4 类交底，诚实标注「自评」** | §6 表格 |
| ⑫ | requirements.txt | **保留为记录**（方案 A 零补装；从镜像 freeze 一份） | §4.2 注释 |

> 编号说明：⑥ 为二轮审查清单原编号，落点=app 职责动态扫描；⑦⑧⑨⑩⑪⑫⑬ 为二轮新编号。

## 10.5 决策记录 3（2026-07-31 三轮拍板并入文，依据 `D:\00 Happy Developer` 环境文档复核）
| # | 决策 | 拍板 | 落点 |
|---|---|---|---|
| ⑭ | fallback 方案 B 现实性 | **替换为方案 B' = 异地 Docker 同构跑**（`docker save/load` 镜像，零 ABI 风险）；原「镜像 pip freeze → 本地 venv」因 torch Linux wheel + 系统 Python 3.12 embeddable 无 venv 模块的 ABI 风险**已废弃** | §4.10 决策段 / §4.10.1 备选段 / §4.10.2（新增） |
| ⑮ | 项目背景资料形态 | **md/txt 手写脱敏**（不经 MinerU 解析，MVP 资料量小最稳） | §3 IN |
| ⑯ | 交底 UI 加「复制 Markdown」按钮 | **加**（约 10 行，演示直接复制归档） | §8 步骤 6 |
| ⑰ | 检索日志静音 | **静音**（`contextlib.redirect_stdout` 包检索调用，演示 UI 干净；调试可临时开） | §8 步骤 6 |
| ⑱ | 演示期停 MinerU？ | **不停**（CleanDoc 不调 MinerU，其空闲仅占 978MiB/4%；停 archrag-core 后演示显存约 8.9G 充足） | §10.3 🟡4 |
| ⑲ | 演示 checklist | **加两步**：① 开浏览器前查 `ProxyEnable`（极光 VPN localhost 陷阱，对 8502 生效）；② 演示前 `docker stop archrag-core` | §10.3 🟡6 |

## 10.6 环境文档同步项（2026-07-31，改 `D:\00 Happy Developer\本机AI应用开发基础环境信息.md`）
- **§三 Neo4j 定位**：原「CleanDoc 核心链路不依赖 Neo4j…即使 Neo4j 未开仍能跑」→ 更新为「CleanDoc 已拍板启用图谱（决策①），Neo4j 为**演示必备**；`archrag-neo4j` 必须保持运行」。
- **§9 模型选型**：补充「CleanDoc 演示期停 archrag-core、不停 MinerU（决策⑱）」。
- 说明：环境文档整理于拍板前（01:33），Neo4j 定位表述过时，本次同步修正。

## 10.7 决策记录 4（2026-07-31 四轮拍板并入文，审核执行方案后）
| # | 决策 | 拍板 | 落点 |
|---|---|---|---|
| ⑳ | 子 agent 执行顺序 | **两批**：先子 A（适配层）→ 子 B/C 并行 → 子 D 收尾（B/C 依赖 A 的 `clean_config`，避免干等） | 执行方案 §二 |
| ㉑ | 示例占位资料 | **由 AI 起草** 1–2 份（按 §5 输入示例：示例药厂/围护/ISO 7 级/压差 +10Pa），用户审核 | 执行方案 §二 子 A / §八 |
| ㉒ | `D:\clean doc` git init | **init**（配 `.gitignore`，记录版本、简历可贴 repo） | 执行方案 §三 阶段 0 |
| ㉓ | 录屏脚本时机 | **MVP 跑通后再写**（贴合实际流程，避免与实现脱节） | 执行方案 §三 阶段 6 |

## 10.8 执行方案滞后点同步（2026-07-31，执行方案与 PRD 对齐修正）
1. 🟡4「必要时停 MinerU」→ 删（决策⑱：MinerU 不停）。
2. 阶段 5 冒烟**加「Neo4j 连通性」**检查（决策①图谱前置）。
3. 阶段 3（子 C）产出补：复制按钮（⑯）/ 日志静音（⑰）/ 分步展示（⑪）。
4. 子 B 产出补：**500 字符切片**（⑨）。
5. 阶段 6 收口：**自评 4 类**（围护/净化空调/工艺管道/电气）+ 标「自评」（⑬）；**录屏脚本跑通后写**（㉓）。
6. requirements.txt 注释改「记录清单（镜像 freeze）」（⑫）。
