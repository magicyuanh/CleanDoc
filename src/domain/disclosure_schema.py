# -*- coding: utf-8 -*-
"""交底输出结构（domain 层，纯业务、零 KG_Test 依赖）。"""
from dataclasses import dataclass, field
from typing import List, Optional

# 技术交底固定章节（PRD §5 输出示例）
TECH_SECTIONS = ["工程概况", "施工准备", "操作工艺", "质量标准", "安全事项", "验收要求"]

# 安全交底固定章节（变体，决策⑧）
SAFETY_SECTIONS = ["工程概况", "危险源辨识", "安全措施", "应急处置", "作业要求"]


@dataclass
class DisclosureRequest:
    """一次交底生成的入参（表单 → service）。"""
    project: str                                   # 项目名（来自 project_kb/data 文件名）
    project_type: str                              # 分项工程（6 类枚举）
    location: str                                  # 部位
    params: str                                    # 关键参数（洁净度/温湿度/压差等）
    disclosure_type: str = "技术交底"              # 技术交底 / 安全交底（决策⑧）


@dataclass
class DualRouteResult:
    """双路检索的中间结果（证据链面板用，决策⑤/⑪）。"""
    query_normative: str                           # query₁
    query_project: str                             # query₂
    disclosure_markdown: str = ""                  # 最终交底 Markdown
    normative_texts: List[str] = field(default_factory=list)   # 第一路命中的原文（来源 KG_Test）
    normative_points: str = ""                     # 规范要点 A（问答台本整理后）
    project_texts: List[str] = field(default_factory=list)     # 第二路命中的原文（来源 project_kb）
    project_background: str = ""                   # 项目背景 B（拼接）
