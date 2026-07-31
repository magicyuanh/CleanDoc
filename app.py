# -*- coding: utf-8 -*-
"""CleanDoc Streamlit 入口 —— 极简表单 + 分步证据链渲染（决策⑪/⑤/⑯/⑰）。

表单：项目（动态扫描 data/，决策⑥）/ 分项（6 类枚举，决策⑦）/ 技术·安全切换（决策⑧）
     / 部位 / 参数 → 「生成交底」按钮
展示：分步 —— ① 规范要点 A → ② 项目背景 B → ③ 最终交底（+ 复制 Markdown 按钮，决策⑯）
标注：MVP · 辅助起草，需人工复核签字。
"""
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

    # ---- 最终交底（决策⑯ 复制按钮）----
    st.divider()
    st.markdown("### ③ 技术交底（草稿）")
    st.markdown(result.disclosure_markdown)
    st.download_button(
        "📋 复制 Markdown（下载）",
        result.disclosure_markdown,
        file_name=f"{req.project}_{req.project_type}_{req.disclosure_type}.md",
        mime="text/markdown",
    )
    st.caption("⚠️ MVP · 辅助起草，须经项目技术负责人复核签字后生效。")
