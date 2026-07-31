# -*- coding: utf-8 -*-
"""溯源回归验证：metadata 回填 + 编号映射（不调 LLM）。"""
import sys, io, contextlib, json
sys.path.insert(0, '/clean_doc')
from src.adapter.kg_test_adapter import get_adapter
a = get_adapter()
from src.project_kb.project_retriever import ProjectRetriever
r = ProjectRetriever(a.cfg)

print('=== 规范路溯源（search_normative 后 metadata）===')
with contextlib.redirect_stdout(io.StringIO()):
    ctx1 = a.search_normative('洁净室 净化空调 施工规范要点 质量标准 安全要求', top_k=5)
for i, c in enumerate(ctx1):
    meta = c.metadata
    print(f'  [{i+1}] type={meta.get("source_type")} | file={meta.get("source_file")} | relation={meta.get("relation")} | 无FILE前缀={"FILE:" not in c.content}')

print()
print('=== 项目路溯源（project_retriever search 后 metadata）===')
ctx2 = r.search('净化空调 施工 项目背景 实际参数 特殊要求', top_k=5)
for i, c in enumerate(ctx2):
    meta = c.metadata
    print(f'  [{i+1}] type={meta.get("source_type")} | file={meta.get("source_file")} | chunk={meta.get("chunk_idx")}')

out = {
    'normative': [
        {'idx': i+1, 'type': c.metadata.get('source_type'), 'file': c.metadata.get('source_file'),
         'relation': c.metadata.get('relation'), 'preview': c.content[:50]}
        for i, c in enumerate(ctx1)
    ],
    'project': [
        {'idx': i+1, 'file': c.metadata.get('source_file'), 'chunk': c.metadata.get('chunk_idx'),
         'preview': c.content[:50]}
        for i, c in enumerate(ctx2)
    ],
}
with open('/tmp/trace_verify.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print()
print('已存 /tmp/trace_verify.json')
