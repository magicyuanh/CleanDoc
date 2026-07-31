# -*- coding: utf-8 -*-
"""adapter —— CleanDoc 唯一 import KG_Test 的层（零修改母体）。

职责：
1. sys.path 指向 KG_TEST_ROOT（环境变量解析，🔴1）。
2. 构造 SystemConfig 后**覆写 monitor_dir 为可写目录**（🟡3 修正：/app 是 :ro 只读，
   SystemConfig.__post_init__ 会尝试 mkdir /app/monitor → 只读挂载下抛错，必须绕开）。
3. 封装 HybridRetriever（图谱默认启用+自动降级，决策①，无需开关）、
   ResponseGenerator（第一路规范要点）、LLMClient（融合段，绕过写死台本）。
4. 检索日志静音（决策⑰：contextlib.redirect_stdout 包检索调用，演示 UI 干净）。
"""
import os
import sys
import io
import asyncio
import contextlib

import nest_asyncio
nest_asyncio.apply()  # ⚠️ Streamlit 异步兼容，入口必调一次

import clean_config as cc

# --- 🔴1 指向母体 KG_Test（容器=/app，本机=D:/KG_Test），不复制、不写死 ---
sys.path.insert(0, cc.KG_TEST_ROOT)

from config import SystemConfig                    # noqa: E402  base_dir 自动锁 KG_Test
from rag.retriever import HybridRetriever          # noqa: E402  图谱默认启用+自动降级
from rag.generator import ResponseGenerator        # noqa: E402  第一路规范要点（问答台本原样用）
from core.llm_client import LLMClient              # noqa: E402  融合段生成（绕过写死台本）
from core.monitoring import MonitoringManager      # noqa: E402  构造 LLMClient 依赖
from core.models import UnifiedContext             # noqa: E402  检索↔生成数据契约


class CleanDocAdapter:
    """CleanDoc 侧封装：装配 KG_Test 组件 + 提供双路所需调用。"""

    def __init__(self):
        # 构造 SystemConfig（base_dir 自动锁 KG_Test；.env 从挂载 /app/.env 读 key）
        self.cfg = SystemConfig()

        # 🟡3 覆写 monitor_dir → 可写目录（/app 是 :ro，原 /app/monitor 会写失败）
        self.cfg.monitor_dir = cc.MONITOR_DIR
        os.makedirs(cc.MONITOR_DIR, exist_ok=True)
        self.monitor = MonitoringManager(cc.MONITOR_DIR)

        # 🟡3b 覆写 chroma_db_path → 可写目录：PersistentClient 打开母体库会写元数据，
        #      /app 只读 → 抛 "readonly database"。指向 /clean_doc/chroma_db 的持久副本：
        #      → 先在可写处建一个 PersistentClient（复制母体 sqlite），再让母体读取它。
        self.cfg.chroma_db_path = cc.CHROMA_DB_WRITABLE
        os.makedirs(cc.CHROMA_DB_WRITABLE, exist_ok=True)
        self._mirror_chroma_db()

        # 装配检索器与生成器（构造时加载模型，占用显存）
        self.retriever = HybridRetriever(self.cfg)
        self.generator = ResponseGenerator(self.cfg)

    def _mirror_chroma_db(self):
        """把母体 /app/chroma_db 的 sqlite 复制到可写目录，作为读取源。

        母体库本身只读（:ro 挂载），PersistentClient 打不开；
        复制出可写副本后，母体 HybridRetriever 就能正常读 Vector 路。
        """
        import shutil
        src = os.path.join(cc.KG_TEST_ROOT, "chroma_db")
        dst = cc.CHROMA_DB_WRITABLE
        if not os.path.isdir(src):
            return
        # 只复制 sqlite 主文件与目录结构（uuid 子目录内是分片数据，一并拷）
        if not os.path.exists(os.path.join(dst, "chroma.sqlite3")):
            shutil.copytree(src, dst, dirs_exist_ok=True)

    # ------------------------------------------------------------------
    # 第一路：规范要点（KG_Test 原位检索 + 问答台本提取）
    # ------------------------------------------------------------------
    def search_normative(self, query: str, top_k: int = cc.TOP_K):
        """第一路检索：HybridRetriever.search（含图谱，默认启用+自动降级）。"""
        with contextlib.redirect_stdout(io.StringIO()):   # 决策⑰ 日志静音
            return self.retriever.search(query, top_k=top_k)

    def extract_normative_points(self, query: str, ctx_list) -> str:
        """第一路生成：用 KG_Test 问答台本把上下文整理成「规范要点 A」文本。"""
        with contextlib.redirect_stdout(io.StringIO()):
            return self.generator.generate_sync(query, ctx_list)

    # ------------------------------------------------------------------
    # 融合段：直调底层 LLMClient，注入 CleanDoc 自有交底台本（绕过写死 system prompt）
    # ------------------------------------------------------------------
    def call_llm_fusion(self, prompt: str, temperature: float = cc.TEMPERATURE) -> str:
        """同步驱动 LLMClient.call_llm（Streamlit 内 nest_asyncio 已就绪）。"""
        async def _run():
            async with LLMClient(self.cfg, self.monitor) as llm:
                return await llm.call_llm(prompt, self.cfg.model_name, temperature=temperature)

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_run())


# 模块级单例（进程内复用组件，避免重复加载模型）
_adapter = None


def get_adapter() -> CleanDocAdapter:
    global _adapter
    if _adapter is None:
        _adapter = CleanDocAdapter()
    return _adapter
