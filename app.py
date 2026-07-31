# -*- coding: utf-8 -*-
"""CleanDoc Streamlit 入口 —— 极简表单 + 分步证据链渲染（决策⑪/⑤/⑯/⑰）。

表单：项目（动态扫描 data/，决策⑥）/ 分项（6 类枚举，决策⑦）/ 技术·安全切换（决策⑧）
     / 部位 / 参数 → 「生成交底」按钮
展示：分步 —— ① 规范要点 A → ② 项目背景 B → ③ 最终交底（+ 复制 Markdown 按钮，决策⑯）
溯源：正文内 [n] 可点击（锚点跳转）+ 正文下方引用溯源表（决策⑮b）
标注：MVP · 辅助起草，需人工复核签字。
"""
import re

import streamlit as st

import clean_config as cc
from src.domain.disclosure_schema import DisclosureRequest
from src.domain.project_types import PROJECT_TYPES, DISCLOSURE_TYPES
from src.service.disclosure_service import generate_disclosure, list_projects

st.set_page_config(page_title="CleanDoc · 洁净室技术交底", layout="wide")

st.title("🏭 CleanDoc — 洁净室施工技术交底（MVP）")
st.caption("辅助起草 · 需项目技术负责人复核签字后生效")

# ---------- 表单 ----------
with st.form("disclosure_form"):
    col1, col2 = st.columns(2)
    with col1:
        project = st.selectbox("项目", list_projects() or ["示例药厂洁净厂房"])
        project_type = st.selectbox("分项工程", PROJECT_TYPES)
        location = st.text_input("部位", "洁净车间隔墙")
    with col2:
        disclosure_type = st.selectbox("交底类型", DISCLOSURE_TYPES)  # 决策⑧
        params = st.text_input("关键参数", "洁净度 ISO 7 级、压差 +10Pa")
    submitted = st.form_submit_button("生成交底", type="primary")


def _linkify_refs(markdown: str) -> str:
    """把正文里的 [n] 引用编号转成可点击锚点链接（跳到下方溯源表对应行）。

    仅转换独立引用标记（前后非数字/字母/]，避免误伤 [4][5] 连续引用后的边界）。
    """
    # [n] 或 [n][m] → 逐个转 <a href="#src-n">[n]</a>
    def _rep(m):
        n = m.group(1)
        return f'<a href="#src-{n}" style="text-decoration:none;color:#c7254e;">[{n}]</a>'
    # 先保护已存在的 HTML 标签（理论无，兜底）
    return re.sub(r"\[(\d+)\]", _rep, markdown)


def _source_table(sources: list) -> str:
    """渲染引用溯源表（编号 | 来源 | 文件 | 片段预览）。"""
    if not sources:
        return "_（无命中来源）_"
    rows = ["| 编号 | 来源 | 文件 / 图谱 | 片段预览 |", "|---|---|---|---|"]
    for s in sources:
        n = s["idx"]
        # 来源类型徽标
        stype = s.get("source_type", "")
        badge = {"规范库": "📘", "知识图谱": "🕸️", "项目资料": "📄"}.get(stype, "📎")
        # 文件列：规范库=文件名；图谱=实体关系；项目资料=文件名
        if s.get("relation"):
            file_cell = f"{s.get('source_entity','')} → {s.get('relation')}"
        else:
            file_cell = f"{s.get('file','')}" + (f" · 段{s.get('chunk_idx',0)+1}" if s.get("chunk_idx") is not None else "")
        # 片段预览（脱敏 HTML 特殊字符）
        prev = (s.get("preview") or "").replace("|", "\\|").replace("\n", " ")
        rows.append(f'| <a id="src-{n}"></a>**[{n}]** | {badge} {stype} | {file_cell} | {prev} |')
    return "\n".join(rows)


# ---------- 生成 ----------
if submitted:
    req = DisclosureRequest(
        project=project,
        project_type=project_type,
        location=location,
        params=params,
        disclosure_type=disclosure_type,
    )
    with st.spinner("双路检索 + 融合生成中…"):
        result = generate_disclosure(req)

    # ---- 证据链：分步展示（决策⑪）----
    with st.expander("① 规范要点 A（来源：KG_Test 规范库）", expanded=True):
        st.caption(f"query₁：{result.query_normative}")
        st.markdown(result.normative_points)
    with st.expander("② 项目背景 B（来源：project_kb 项目库）", expanded=True):
        st.caption(f"query₂：{result.query_project}")
        st.markdown(result.project_background)

    # ---- 最终交底（决策⑯ 复制按钮 + ⑮b 溯源）----
    st.divider()
    st.markdown("### ③ 技术交底（草稿）")
    st.markdown(_linkify_refs(result.disclosure_markdown), unsafe_allow_html=True)
    st.download_button(
        "📋 复制 Markdown（下载）",
        result.disclosure_markdown,
        file_name=f"{req.project}_{req.project_type}_{req.disclosure_type}.md",
        mime="text/markdown",
    )

    # ---- 引用溯源表（决策⑮b）----
    st.markdown("### 📎 引用溯源")
    st.caption("点击正文中 [n] 编号可跳转到对应来源行；片段为该编号命中的原文开头。")
    st.markdown("**规范要点引用**（KG_Test 规范库 / 知识图谱）")
    st.markdown(_source_table(result.normative_sources), unsafe_allow_html=True)
    st.markdown("**项目背景引用**（project_kb 项目资料）")
    st.markdown(_source_table(result.project_sources), unsafe_allow_html=True)
    st.caption("⚠️ MVP · 辅助起草，须经项目技术负责人复核签字后生效。")
