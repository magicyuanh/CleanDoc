# -*- coding: utf-8 -*-
"""project_kb 建库：读 data/ 资料 → 500 字符切片（决策⑨）→ BGE 嵌入存 chroma + jieba 建 BM25。

零拷贝、零下载、零修改 KG_Test：
- 复用 KG_Test 的 SystemConfig（embedding_model_path 自动指向母体 models/）
- 库文件全部落在 CleanDoc 自身（CLEANDOC_ROOT/project_kb）
- 路径全部取自 clean_config 环境变量（🔴1）
"""
import glob
import os
import pickle
import sys

import chromadb
import jieba
import torch

import clean_config as cc

# --- 🔴1 指向母体 KG_Test，复用 SystemConfig / BGE 嵌入（原位，零下载）---
sys.path.insert(0, cc.KG_TEST_ROOT)
from config import SystemConfig                       # noqa: E402
from sentence_transformers import SentenceTransformer  # noqa: E402
from rank_bm25 import BM25Okapi                        # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MAX_CHUNK_CHARS = 500   # 决策⑨：对齐 BGE 512 token 硬约束（约 500 字符）


def _split_para(para: str, limit: int = MAX_CHUNK_CHARS):
    """段落超长时按 500 字符切分，返回多段（避免 BGE 编码截断）。"""
    para = para.strip()
    if len(para) <= limit:
        return [para]
    return [para[i:i + limit] for i in range(0, len(para), limit)]


def _read_chunks(data_dir):
    """读取 data/ 下所有 .md/.txt，按空行分段 + 超长按 500 字符截断（决策⑨）。"""
    chunks = []
    for fp in glob.glob(os.path.join(data_dir, "**/*"), recursive=True):
        if not fp.endswith((".md", ".txt")):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()
        idx = 0
        for para in (p.strip() for p in text.split("\n\n") if p.strip()):
            for seg in _split_para(para):
                chunks.append({
                    "content": seg,
                    "metadata": {"source_file": os.path.basename(fp), "chunk_idx": idx},
                })
                idx += 1
    return chunks


def build():
    cfg = SystemConfig()   # base_dir 自动锁 KG_Test，embedding_model_path 指向其 BGE
    chunks = _read_chunks(cc.DATA_DIR)
    if not chunks:
        print(f"[BUILD] data/ 为空（{cc.DATA_DIR}），跳过。")
        return 0

    # 1) 向量路：复用母体 BGE 编码 → 存 chroma（重建时先清旧集合）
    embed_model = SentenceTransformer(cfg.embedding_model_path, device=DEVICE)
    client = chromadb.PersistentClient(path=cc.CHROMA_DIR)
    if cc.COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(cc.COLLECTION_NAME)
    col = client.get_or_create_collection(cc.COLLECTION_NAME)

    contents = [c["content"] for c in chunks]
    embeddings = embed_model.encode(contents, normalize_embeddings=True).tolist()
    col.add(
        ids=[f"p{i}" for i in range(len(chunks))],
        documents=contents,
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in chunks],
    )

    # 2) BM25 路：jieba 分词建索引 → pickle 落盘（结构同 KG_Test: {"bm25","chunks"}）
    tokenized = [list(jieba.cut(c["content"])) for c in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(cc.BM25_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)

    print(f"[BUILD] 完成：{len(chunks)} 条 → chroma({cc.COLLECTION_NAME}) + bm25.pkl @ {cc.CHROMA_DIR}")
    return len(chunks)


if __name__ == "__main__":
    n = build()
    sys.exit(0 if n > 0 else 1)
