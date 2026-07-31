# -*- coding: utf-8 -*-
"""project_kb 检索：向量 + BM25 双路 → FusionLayer(RRF) → 归一 UnifiedContext。

🔴2（拍板）：**跳过 RerankModel**（省 6.3GB 显存 + 加载时间），仅向量+BM25+RRF，
对小型项目库质量无损（PRD §4.6 末段 / §10.2）。
🔴1：路径全部取自 clean_config 环境变量。
复用母体：FusionLayer / SystemConfig / UnifiedContext（零重造轮子）。
"""
import os
import pickle
import sys
from typing import List

import chromadb
import jieba
import torch

import clean_config as cc

# --- 🔴1 指向母体 KG_Test，复用 FusionLayer / SystemConfig / UnifiedContext ---
sys.path.insert(0, cc.KG_TEST_ROOT)
from config import SystemConfig                       # noqa: E402
from rag.fusion import FusionLayer                    # noqa: E402
from core.models import UnifiedContext                # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class ProjectRetriever:
    """CleanDoc 项目背景库检索：向量 + BM25 → FusionLayer(RRF) → UnifiedContext（🔴2 无 RerankModel）。"""

    def __init__(self, config: SystemConfig = None):
        self.cfg = config or SystemConfig()   # 复用母体配置，base_dir 锁 KG_Test
        self.client = chromadb.PersistentClient(path=cc.CHROMA_DIR)
        self.collection = self.client.get_collection(cc.COLLECTION_NAME)
        self.embed_model = SentenceTransformer(self.cfg.embedding_model_path, device=DEVICE)

        with open(cc.BM25_PATH, "rb") as f:
            bm25_data = pickle.load(f)
        self.bm25 = bm25_data["bm25"]
        self.bm25_chunks = bm25_data["chunks"]

        self.fusion = FusionLayer(rrf_k=60)
        # 🔴2 拍板：不加载 RerankModel（省 6.3GB 显存）；小型项目库 RRF 融合已足够

    def search(self, query: str, top_k: int = 8) -> List[UnifiedContext]:
        recall_n = top_k * 5

        # A. 向量路
        q_vec = self.embed_model.encode(query, normalize_embeddings=True).tolist()
        res = self.collection.query(query_embeddings=[q_vec], n_results=recall_n)
        vector_texts = res["documents"][0] if res.get("documents") else []
        # 🆕 溯源：chroma 命中自带 metadatas（source_file/chunk_idx），按文本建索引
        vector_meta = {}
        if res.get("metadatas") and res["metadatas"][0]:
            for txt, meta in zip(vector_texts, res["metadatas"][0]):
                vector_meta[txt] = meta or {}

        # B. BM25 路（chunks 自带 metadata，直接映射）
        tokens = list(jieba.cut(query))
        bm25_texts = self.bm25.get_top_n(
            tokens, [c["content"] for c in self.bm25_chunks], n=recall_n
        )
        bm25_meta = {c["content"]: c.get("metadata", {}) for c in self.bm25_chunks}

        # 阶段2: RRF 文本流融合（与 HybridRetriever 一致的调用约定）
        fused_texts = self.fusion.fuse(
            {"Vector": vector_texts, "BM25": bm25_texts}, top_k=recall_n
        )

        # 阶段3: 归一化为 UnifiedContext（标记来源 Vector / BM25）→ 直接取 top_k（🔴2 无重排）
        set_vec, set_bm25 = set(vector_texts), set(bm25_texts)
        candidates: List[UnifiedContext] = []
        for text in fused_texts:
            src = []
            if text in set_vec:
                src.append("Vector")
            if text in set_bm25:
                src.append("BM25")
            # 🆕 溯源：合并两路 metadata（BM25 优先完整，Vector 兜底），标记来源类型
            meta = bm25_meta.get(text) or vector_meta.get(text) or {}
            meta = dict(meta)  # 浅拷贝，避免污染 bm25_chunks 原始数据
            meta.setdefault("source_type", "项目资料")
            candidates.append(
                UnifiedContext(
                    content=text,
                    source="+".join(src) or "Text",
                    score=0.0,
                    metadata=meta,
                )
            )
        return candidates[:top_k]
