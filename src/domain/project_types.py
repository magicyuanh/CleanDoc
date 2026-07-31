# -*- coding: utf-8 -*-
"""分项工程类型枚举 + 默认参数（domain 层，纯业务、零 KG_Test 依赖）。

决策⑦：6 类全枚举，MVP 实测 4 类（围护结构/净化空调/工艺管道/电气）。
决策⑧：技术交底 + 安全交底两种模板变体。
"""
from dataclasses import dataclass, field
from typing import Dict

# 6 类分项工程（决策⑦）
PROJECT_TYPES = ["围护结构", "净化空调", "工艺管道", "电气", "地面", "调试"]
# 实测优先 4 类（对齐指标①「≥4 类」）
DEMO_TYPES = ["围护结构", "净化空调", "工艺管道", "电气"]

# 交底类型（决策⑧）
DISCLOSURE_TYPES = ["技术交底", "安全交底"]


@dataclass
class ProjectTypeMeta:
    """分项工程的默认检索/生成配置。"""
    name: str
    # 第一路 query 模板（指向规范）
    query_normative_template: str = "洁净室 {ptype} 施工规范要点 / 质量标准 / 安全要求"
    # 第二路 query 模板（指向项目背景）
    query_project_template: str = "{ptype} 施工 项目背景 实际参数 特殊要求"
    # 默认关键参数提示（UI 预填，可改）
    default_params: str = ""
    # 是否 MVP 实测（决策⑦）
    demo: bool = False


# 6 类元数据表
PROJECT_TYPE_META: Dict[str, ProjectTypeMeta] = {
    "围护结构": ProjectTypeMeta(
        "围护结构", demo=True,
        default_params="洁净度 ISO 7 级、压差 +10Pa、墙体岩棉夹芯板、密封胶条"),
    "净化空调": ProjectTypeMeta(
        "净化空调", demo=True,
        default_params="洁净度 ISO 7 级、温度 22±2℃、湿度 55±5%、新风量、风管严密性"),
    "工艺管道": ProjectTypeMeta(
        "工艺管道", demo=True,
        default_params="管材 316L、氩弧焊、坡度、酸洗钝化、试压 1.5 倍工作压力"),
    "电气": ProjectTypeMeta(
        "电气", demo=True,
        default_params="照度 ≥300lx、接地电阻 ≤1Ω、防静电、桥架、电缆敷设"),
    "地面": ProjectTypeMeta(
        "地面", default_params="环氧自流平、平整度 2m 靠尺 ≤2mm、防静电、伸缩缝"),
    "调试": ProjectTypeMeta(
        "调试", default_params="风量平衡、压差调试、洁净度检测、自控联调"),
}
