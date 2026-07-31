# -*- coding: utf-8 -*-
"""CleanDoc 自身配置。

🔴1 修正：路径全部由环境变量解析，不硬编码。
- 容器（方案 A）：KG_TEST_ROOT=/app、CLEANDOC_ROOT=/clean_doc
- 本机（开发）：缺省回退 D:/KG_Test、D:/clean doc

⚠️ 本模块刻意不叫 config.py，避免与 KG_Test 的 config.py 在 sys.path 撞名。
"""
import os

# --- 路径（环境变量优先，缺省回退本机路径）---
KG_TEST_ROOT = os.getenv("KG_TEST_ROOT", r"D:\KG_Test")        # 母体 KG_Test 根
CLEANDOC_ROOT = os.getenv("CLEANDOC_ROOT", r"D:\clean doc")    # CleanDoc 根

# --- 子路径（全部由 CLEANDOC_ROOT 派生，容器/本机自动正确）---
PROJECT_KB_DIR = os.path.join(CLEANDOC_ROOT, "project_kb")     # 项目背景库运行时目录
DATA_DIR = os.path.join(PROJECT_KB_DIR, "data")                # 项目原始资料
CHROMA_DIR = PROJECT_KB_DIR                                    # chroma 持久化目录
BM25_PATH = os.path.join(PROJECT_KB_DIR, "bm25.pkl")           # BM25 索引
COLLECTION_NAME = "project_kb"                                 # chroma collection 名

# --- 监控目录（🟡3：指向可写目录，避免写 KG_Test 只读 /app/monitor）---
MONITOR_DIR = os.getenv("CLEANDOC_MONITOR_DIR",
                        os.path.join(CLEANDOC_ROOT, "monitor"))

# --- 母体 chroma_db 的可写副本（🟡3b：/app 只读，PersistentClient 无法打开只读库，
#     复制一份到可写目录供 HybridRetriever 的 Vector 路读取）---
CHROMA_DB_WRITABLE = os.getenv("CLEANDOC_CHROMA_DB",
                               os.path.join(CLEANDOC_ROOT, "chroma_db"))

# --- 检索/生成参数（决策⑩/⑧）---
TOP_K = 8            # 两路统一 top_k（决策⑩）
RECALL_MULT = 5      # 宽召回倍数（与 HybridRetriever 一致）
TEMPERATURE = 0.3    # 融合段温度（PRD §4.5）

# --- 分项工程（6 类全枚举，决策⑦；MVP 实测 4 类）---
PROJECT_TYPES = ["围护结构", "净化空调", "工艺管道", "电气", "地面", "调试"]
DEMO_TYPES = ["围护结构", "净化空调", "工艺管道", "电气"]  # 实测优先 4 类

# --- 启用交底类型（决策⑧：技术 + 安全）---
DISCLOSURE_TYPES = ["技术交底", "安全交底"]
