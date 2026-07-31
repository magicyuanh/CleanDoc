# CleanDoc — 洁净室施工技术交底自动生成 MVP

> 状态：MVP · 辅助起草，需人工复核签字后生效（PRD v2，2026-07-31）。

## 是什么
输入「项目 + 分项工程 + 部位 + 关键参数」，双路检索（KG_Test 规范路 + CleanDoc 项目背景路）→ 融合生成**结构化技术交底草稿**。

## 核心原则
- **零拷贝、零修改 `D:\KG_Test`**：仅 `import` 复用其检索/生成/模型/知识库资产（原位引用）。
- 规范（通用）存 KG_Test；项目背景（特定）存 CleanDoc `project_kb`，物理隔离。

## 运行
见 PRD §4.10.1（方案 A：新建独立容器，复用 `kg_test-archrag-app:latest` 镜像）。

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
  -e DEEPSEEK_API_KEY=<key> \
  kg_test-archrag-app:latest \
  streamlit run /clean_doc/app.py --server.port=8501 --server.address=0.0.0.0
```

浏览器访问 `http://localhost:8502`。

## 目录
- `src/adapter/` — 唯一 import KG_Test 的层
- `src/domain/` — 交底结构、分项元数据、提示词
- `src/project_kb/` — 项目背景库建库/检索
- `src/service/` — 双路编排与融合生成
- `project_kb/data/` — 项目背景原始资料（脱敏/示例）

## 诚实性
MVP 输出为 AI 辅助起草，须经项目技术负责人复核签字后生效。简历表述为「施工文书自动生成 MVP / 辅助起草」。
