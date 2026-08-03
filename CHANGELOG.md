# Changelog

CleanDoc 洁净室施工技术交底自动生成 MVP。语义化版本（SemVer）。提交记录见 git log。

## [0.1.0] - 2026-08-04

MVP 首版对外发布（Gitee 私有仓首推）。功能已全部跑通，冒烟 5 项全绿。

### 新增

- 双路检索 + 融合生成管线：规范路（KG_Test：Neo4j 图谱 + ChromaDB 向量 + BM25 + BGE 重排 + DeepSeek）+ 项目路（自建 project_kb：500 字符切片 + 向量/BM25 + RRF）
- 六章节结构化技术交底生成（围护/净化空调/工艺管道/电气 4 类实测）
- 引用溯源：正文 `[n]` 可点击锚点 + 双段溯源表（规范库/知识图谱 + 项目资料），项目路到「文件名+段落」级
- 分步证据链展示（规范要点 A → 项目背景 B → 融合交底）
- 复制 Markdown 按钮；检索日志静音
- 录屏演示物料：口播脚本、OBS 配置清单、录前自检脚本（`scripts/pre_rec_check.py`）
- 简历案例说明（`docs/简历案例说明_压缩版.md`）

### 变更

- 路径全部环境变量化（`KG_TEST_ROOT` / `CLEANDOC_ROOT`），零硬编码
- 项目路去除 RerankModel（省显存，仅向量 + BM25 + RRF）
- 母体 `/app` 只读 → adapter 覆写 `cfg.chroma_db_path` 到可写副本 + `_mirror_chroma_db()` 镜像
- README 重写：6 环境变量验证版运行命令 + 数据流图 + 溯源局限诚实说明

### 修复

- `DualRouteResult` dataclass 无默认值字段顺序（TypeError）
- `ResponseGenerator` 构造签名（只收 config）
- 母体 chroma_db 只读导致 Vector 路静默降级（关键修复）

### 移除

- 无（MVP 首版）

---

## 历史提交里程碑（pre-tag）

| 提交 | 日期 | 内容 |
|------|------|------|
| `c12be20` | 2026-07-31 | MVP 实施 + 冒烟全绿 |
| `d6ce2f7` | 2026-07-31 | 引用溯源功能 |
| `88e04ae` | 2026-07-31 | overview 补章节 + output 入 gitignore |
| `5e34a16` | 2026-07-31 | 数据流图 + PRD/README 同步 |
| `24d2d47` | 2026-07-31 | 录屏准备文档 |
| `a470d96` | 2026-08-04 | 简历案例说明（压缩版）入 docs |
