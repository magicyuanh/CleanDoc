# CleanDoc — 洁净室施工技术交底自动生成 MVP

> 状态：✅ MVP 已跑通。辅助起草交底文件，需人工复核签字后生效。

## 是什么
输入「项目 + 分项工程 + 部位 + 关键参数」，双路检索（KG_Test 规范路 + CleanDoc 项目背景路）→ 融合生成**结构化技术交底草稿**，附**引用溯源**（正文 `[n]` 可点击 → 溯源表显示来源文件/图谱实体/段落）。

## 核心原则
- **零拷贝、零修改 `HVAC-KG-RAG`**：仅 `import` 复用其检索/生成/模型/知识库资产（原位引用）。
- 规范（通用）存 HVAC-KG-RAG；项目背景（特定）存 CleanDoc `project_kb`，物理隔离、互不污染。
- 双路不对称：规范路走问答台本提炼「要点 A」；项目路保留原文「背景 B」。编号映射可靠（`[n]` ≡ `ctx₁[n-1]`）。

## 运行
**前置**：`archrag-neo4j` 容器保持运行（图谱路依赖，决策①）；`kg_test-archrag-app:latest` 镜像存在。

```bash
docker run -d --name cleandoc --gpus all -p 8502:8501 \
  -e KG_TEST_ROOT=/app \
  -e CLEANDOC_ROOT=/clean_doc \
  -e DEEPSEEK_API_KEY=<your-key> \
  -e NEO4J_URI="bolt://host.docker.internal:7687" \
  -e NEO4J_USER=<neo4j-user> \
  -e NEO4J_PASSWORD=<neo4j-pass> \
  -v /d/KG_Test:/app:ro \
  -v "/d/clean doc":/clean_doc:rw \
  kg_test-archrag-app:latest \
  streamlit run /clean_doc/app.py --server.port 8501 --server.address 0.0.0.0
```

⚠️ **3 个坑**：
1. 环境变量**必须 6 个全注入**（3 路径 + DeepSeek + 2 Neo4j），`.env` 里的 `NEO4J_URI=localhost` 在容器内须改写为 `host.docker.internal`（否则指向容器自身）。
2. 挂载路径：`/d/clean doc` **带空格**。
3. 首次生成约 120s（模型懒加载 BGE+重排），之后常驻约 90s/次。

浏览器访问 `http://localhost:8502`。

## 数据流
```
表单(项目/分项/部位/参数/类型)
 ├─ 第一路 query₁ → HybridRetriever(Vector+BM25+Graph→RRF→Rerank) → ResponseGenerator → 规范要点 A
 ├─ 第二路 query₂ → ProjectRetriever(Vector+BM25→RRF，无Rerank) → 项目背景 B（带文件/段落 metadata）
 └─ 融合段：交底模板 + A + B + 表单参数 → LLMClient(DeepSeek) → 交底 Markdown + 引用溯源表
```

## 目录
- `src/adapter/` — 唯一 import KG_Test 的层（monitor/chroma 覆写 + FILE 解析）
- `src/domain/` — 交底结构、分项元数据、提示词
- `src/project_kb/` — 项目背景库建库/检索（500 字符切片 + 溯源 metadata）
- `src/service/` — 双路编排与融合生成
- `project_kb/data/` — 项目背景原始资料（脱敏/示例）
- `scripts/` — 溯源回归验证脚本（trace_verify / e2e_trace_verify）
- `output/` — 演示产物（交底成品，gitignore）

## 诚实性
MVP 输出为 AI 辅助起草，须经项目技术负责人复核签字后生效。规范路溯源到文件级（母体 `test.pdf` 聚合，母体数据限制）；项目路溯源到文件名+段落。
