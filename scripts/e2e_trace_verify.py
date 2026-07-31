# -*- coding: utf-8 -*-
"""端到端验证：generate_disclosure 溯源字段 + 正文链接化（含 LLM 融合段）。"""
import sys, json, re, time
sys.path.insert(0, '/clean_doc')
from src.domain.disclosure_schema import DisclosureRequest
from src.service.disclosure_service import generate_disclosure
from app import _linkify_refs, _source_table

req = DisclosureRequest(
    project='示例药厂洁净厂房',
    project_type='净化空调',
    location='洁净生产区（万级）',
    params='洁净度 10000级(0.5μm≤3500个/m³)、温度 20±2℃、相对湿度 45%-60%、正压差 ≥5Pa、新风比 ≥15%',
)
t0 = time.time()
r = generate_disclosure(req)
print('总耗时 %.1fs' % (time.time() - t0))

print('\n=== 溯源字段 ===')
print('规范路 normative_sources 条数:', len(r.normative_sources))
for s in r.normative_sources[:3]:
    print(f'  [{s["idx"]}] {s["source_type"]} | {s["file"]} | {s["preview"][:40]}')
print('项目路 project_sources 条数:', len(r.project_sources))
for s in r.project_sources[:3]:
    print(f'  [{s["idx"]}] {s["source_type"]} | {s["file"]} | 段{s.get("chunk_idx",0)+1} | {s["preview"][:40]}')

print('\n=== 正文 [n] 链接化 ===')
linked = _linkify_refs(r.disclosure_markdown)
links = re.findall(r'<a href="#src-(\d+)"', linked)
print('链接化后的 [n] 引用数:', len(links), '| 去重编号:', sorted(set(int(x) for x in links)))
sample = [l for l in re.findall(r'.{0,30}<a href="#src-\d+">\[\d+\]</a>.{0,20}', linked)]
print('样例:', sample[:2] if sample else '（正文可能未引用编号）')
print('原始 markdown 是否保留 [n]:', '[3]' in r.disclosure_markdown)

print('\n=== 溯源表 HTML ===')
tbl = _source_table(r.normative_sources)
print('规范溯源表行数:', tbl.count('\n') - 1, '| 含锚点:', 'src-1' in tbl)

# 存结果供 UI 对照
with open('/tmp/e2e_trace.json', 'w', encoding='utf-8') as f:
    json.dump({
        'md_head': r.disclosure_markdown[:200],
        'norm_src': r.normative_sources,
        'proj_src': r.project_sources,
    }, f, ensure_ascii=False, indent=1)
print('\n已存 /tmp/e2e_trace.json')
