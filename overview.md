# CleanDoc 洁净室技术交底 MVP — 冒烟测试报告

> 归档时间：2026-07-31 21:20 ｜ 状态：✅ 冒烟全部通过

## 一、本次完成

**阶段 5（冒烟测试）全项通过**，CleanDoc MVP 从"代码就绪"推进到"可演示"。

| 冒烟项 | 结果 | 关键数据 |
|---|---|---|
| ① 容器+Neo4j 连通 | ✅ | cleandoc Up，`bolt://host.docker.internal:7687` ping OK |
| ② 探库 | ✅ | 478 节点 / 417 关系，HVACR 本体（Component/Parameter/Action/Space…） |
| ③ build_index | ✅ | 2 份示例资料 → 26 条 500 字符切片 → chroma + bm25.pkl |
| ④ 双路检索+生成 | ✅ | 规范路 8 条 + 项目路 8 条，融合生成 2335~2526 字交底 |
| ⑤ 指标自评 | ✅ | 见 §四 |

## 二、冒烟中修复的 3 个坑（重要）

### 坑 1：DualRouteResult 字段顺序（dataclass 报错）
`query_project`、`disclosure_markdown` 两个无默认值字段排在带默认值字段之后 → `TypeError`。
**修**：无默认值字段提到最前。

### 坑 2：ResponseGenerator 签名不匹配
adapter 传了 `(cfg, monitor)`，母体只收 `config`（内部自己建 MonitoringManager）。
**修**：改传 `cfg`（monitor_dir 已被覆写，内部自然用可写路径）。

### 坑 3：母体 chroma_db 只读（Vector 路降级）
`/app` 是 `:ro` 挂载，`PersistentClient` 打开母体库要写元数据 → `readonly database` → Vector 路静默降级。
**修**：adapter 覆写 `cfg.chroma_db_path` → `/clean_doc/chroma_db`（可写副本，`_mirror_chroma_db()` 复制母体 sqlite）。**这是本次最关键的一处修复**，否则规范检索只剩 BM25+Graph 两路。

## 三、容器部署（最终形态）

```
docker run -d --name cleandoc --gpus all -p 8502:8501 \
  -e KG_TEST_ROOT=/app \
  -e CLEANDOC_ROOT=/clean_doc \
  -e DEEPSEEK_API_KEY=<from .env> \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USER=<from .env> \
  -e NEO4J_PASSWORD=<from .env> \
  -v /d/KG_Test:/app:ro \
  -v "/d/clean doc":/clean_doc:rw \
  kg_test-archrag-app:latest \
  streamlit run /clean_doc/app.py --server.port 8501 --server.address 0.0.0.0
```

⚠️ **环境变量必须 6 个全注入**（3 个路径 + DEEPSEEK + 2 个 Neo4j），且 `NEO4J_URI` 在容器内必须改写为 `host.docker.internal`（.env 里的 `localhost` 会指向容器自身）。
⚠️ **挂载路径**：`/d/clean doc`（带空格），不是 `/d/CleanDoc`。

## 四、指标自评（对照 PRD §10）

| 指标 | 目标 | 实测 | 判定 |
|---|---|---|---|
| ① 检索速度 | 双路 < 5s | 模型常驻后双路检索 < 2s（DeepSeek 融合段 0.24~0.30s） | ✅ |
| ② 证据可追溯 | 每段带来源 | 正文带 `[1]`~`[7]` 引用 + query₁/query₂ 原文展示 + 项目背景独立成段 | ✅ |
| ③ 生成质量 | 六章节完整 | 工程概况/施工准备/操作工艺/质量标准/安全事项/验收要求 全齐，参数冲突显式提示（"表单参数为 20±2℃，以设计图纸为准，需项目总工核定"） | ✅ |

**首轮总耗时 120s**（模型懒加载：BGE 嵌入 + BGE-Reranker + 图检索装配）；**二次调用 93s**（模型常驻后更快）。

## 五、遗留事项

1. **output/ 未入 git**（运行时产物，.gitignore 已覆盖），首次演示产物保留在 `D:\clean doc\output\示例药厂洁净厂房_净化空调_技术交底.md`。
2. `src/tests/` 仅占位（PRD 后期阶段补测试）。
3. **真实项目资料待用户补**：`project_kb/data/` 目前只有 2 份示例（决策㉑ AI 起草占位）。
4. 表单参数 vs 项目资料参数冲突时，当前策略是"显式提示需总工核定"——符合 PRD 定位，若需"表单绝对优先"可后续调 prompt。
5. **下次启动**：`docker start cleandoc archrag-neo4j`（archrag-core 已停，省 7.6G 显存/内存）。

## 六、文件清单

```
D:\clean doc\
├── 洁净室技术交底MVP_PRD.md   # PRD v2（23 决策）
├── clean_config.py            # CleanDoc 自身配置（环境变量解析，不叫 config 防撞名）
├── app.py                     # Streamlit 入口（表单+证据链+溯源+下载）
├── src/
│   ├── adapter/kg_test_adapter.py   # 唯一 import KG_Test 的层（monitor/chroma 覆写 + FILE 解析）
│   ├── domain/                      # schema / project_types / 两套提示词
│   ├── project_kb/                  # build_index(500切片) + project_retriever(向量+BM25+RRF+溯源)
│   └── service/disclosure_service.py# 双路编排 + 溯源汇入 + list_projects
├── project_kb/data/           # 示例资料 2 份（真实资料后补）
├── scripts/                   # trace_verify.py + e2e_trace_verify.py（溯源回归）
├── output/                    # 演示产物（gitignore）
└── README.md / requirements.txt / .gitignore
```

## 七、引用溯源功能（2026-07-31 追加）

### 需求
交底正文的 `[n]` 引用标记无可追溯来源 → 要求"可溯源到出处/链接"。

### 拍板（用户）
1. 项目路溯源到「文件名+段落」；2. UI 正文内 `[n]` 可点击 + 正文下方溯源表，两者都要。

### 实现（零改母体）
| 文件 | 改动 |
|---|---|
| `project_retriever.py` | chroma 取 metadatas、BM25 用自带 metadata，按文本映射回填 `UnifiedContext.metadata={source_file, chunk_idx, source_type}` |
| `kg_test_adapter.py` | `search_normative` 解析 content `FILE:` 前缀→metadata（正文剥净噪声）；Graph 流透出实体关系 |
| `disclosure_schema.py` | `DualRouteResult` 增 `normative_sources` / `project_sources`（idx/type/file/chunk/relation/preview） |
| `disclosure_service.py` | 两侧 metadata 汇入溯源字段 |
| `app.py` | `_linkify_refs()` 把正文 `[n]`→`<a href="#src-n">` 锚点链接；`_source_table()` 渲染双段溯源表（规范库/图谱 + 项目资料），表行带 `id="src-n"` 锚点 |

### 编号映射原理（可靠）
母体 `generator.generate_async` 把 ctx 列表按 `[i+1] (source) content` 编号传入 LLM（`/app/rag/generator.py:51-59`）→ **交底 `[n]` = ctx1[n-1]**（含 Vector/BM25/Graph 混排）。溯源表按此映射。

### 验证
- 单测：规范路 5 条 `file=test.pdf` + 无 FILE 前缀；项目路 5 条 `文件名.md + chunk` 精确回填 ✅
- 端到端：8+8 溯源条目、正文 28 处引用链接化、编号 `[1..5]`、锚点 id 正确 ✅
- 容器 health 200，Streamlit 热加载新代码 ✅

### 局限
- 规范库（KG_Test）侧母体只存聚合文件名 `test.pdf`，溯源到**文件级**（母体数据限制，MVP 接受）
- 项目库侧可到**文件+段落**（符合拍板①）
