# -*- coding: utf-8 -*-
"""disclosure_service —— CleanDoc 双路编排（MVP 大脑）。

流程（PRD §4.1 / §4.7C）：
1. 第一路：组 query₁ → adapter(HybridRetriever.search + ResponseGenerator) → 规范要点 A
2. 第二路：组 query₂ → ProjectRetriever.search → 项目背景 B
3. 融合段：拼「交底模板 + A + B + 表单参数」→ LLMClient.call_llm → 结构化交底
"""
import os
from typing import List

import clean_config as cc
from src.adapter.kg_test_adapter import get_adapter
from src.domain.disclosure_schema import DisclosureRequest, DualRouteResult
from src.domain.project_types import PROJECT_TYPE_META
from src.project_kb.project_retriever import ProjectRetriever

PROMPT_DIR = os.path.join(cc.CLEANDOC_ROOT, "src", "domain", "prompts")


def _load_prompt(disclosure_type: str) -> str:
    """按交底类型加载提示词模板（决策⑧：技术/安全变体）。"""
    fname = "safety_disclosure.md" if disclosure_type == "安全交底" else "technical_disclosure.md"
    with open(os.path.join(PROMPT_DIR, fname), "r", encoding="utf-8") as f:
        return f.read()


def generate_disclosure(req: DisclosureRequest) -> DualRouteResult:
    """执行双路检索 + 融合生成，返回完整中间结果（供证据链渲染，决策⑪分步展示）。"""
    adapter = get_adapter()
    meta = PROJECT_TYPE_META.get(req.project_type)
    if meta is None:
        raise ValueError(f"未知分项工程：{req.project_type}（可选：{list(PROJECT_TYPE_META)}）")

    # ---------- 第一路：规范要点 A ----------
    query1 = meta.query_normative_template.format(ptype=req.project_type)
    ctx1 = adapter.search_normative(query1, top_k=cc.TOP_K)
    normative_texts = [c.content for c in ctx1]
    points_a = adapter.extract_normative_points(query1, ctx1) if ctx1 else (
        "（知识库未检索到相关规范条文，以下内容需项目总工核定）"
    )

    # ---------- 第二路：项目背景 B ----------
    query2 = meta.query_project_template.format(ptype=req.project_type)
    retriever = ProjectRetriever(adapter.cfg)
    ctx2 = retriever.search(query2, top_k=cc.TOP_K)
    project_texts = [c.content for c in ctx2]
    background_b = "\n\n".join(project_texts) if project_texts else (
        f"（项目库未检索到「{req.project}」相关背景资料，请补充 project_kb/data/ 资料）"
    )

    # ---------- 融合段：最终交底 ----------
    prompt_template = _load_prompt(req.disclosure_type)
    prompt = (
        prompt_template
        .replace("{normative_points}", points_a)
        .replace("{project_background}", background_b)
        .replace("{project}", req.project)
        .replace("{project_type}", req.project_type)
        .replace("{location}", req.location)
        .replace("{params}", req.params)
    )
    markdown = adapter.call_llm_fusion(prompt, temperature=cc.TEMPERATURE)

    return DualRouteResult(
        query_normative=query1,
        normative_texts=normative_texts,
        normative_points=points_a,
        query_project=query2,
        project_texts=project_texts,
        project_background=background_b,
        disclosure_markdown=markdown,
    )


def list_projects() -> List[str]:
    """动态扫描 project_kb/data/ 文件名 → 项目下拉选项（决策⑥）。"""
    if not os.path.isdir(cc.DATA_DIR):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(cc.DATA_DIR)
        if f.endswith((".md", ".txt"))
    )
