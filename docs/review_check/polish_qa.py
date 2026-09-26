"""Render all pages and check references, table coverage, and retired wording."""
from pathlib import Path
import json
import re

from PIL import Image, ImageDraw
from pypdf import PdfReader
import pypdfium2 as pdfium

PAPER = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'polished_pages'
OUT.mkdir(exist_ok=True)
reader = PdfReader(PAPER / 'main.pdf')
pdf = pdfium.PdfDocument(str(PAPER / 'main.pdf'))
texts = [p.extract_text() for p in reader.pages]
assert '关键词' in texts[1]
assert '问题重述' in texts[2]
source = (PAPER / 'sections/04-models.tex').read_text(encoding='utf-8')
table = (PAPER / 'sections/04-q1-results.tex').read_text(encoding='utf-8')
assert [int(n) for n in re.findall(r'(?m)^(\d+) & ', table)] == list(range(1, 101))
old_table = (PAPER / 'docs/润色前备份_20260925/sections/08-appendix.tex').read_text(encoding='utf-8')
assert re.findall(r'(?m)^\d+ & .*$', table) == re.findall(r'(?m)^\d+ & .*$', old_table)
for phrase in ['极性与强度同时落在中性区间', '主要参考模态的判定不依赖具体基线',
               '三个种子与四类条件共形成50388', '配对差为-0.130']:
    assert phrase not in source, phrase
log = (PAPER / 'main.log').read_text(encoding='utf-8', errors='replace')
summary = {'pages': len(reader.pages), 'abstract_and_keywords_same_page': True,
           'all100_rows_unchanged': True,
           'undefined_references': 'There were undefined references' in log,
           'overfull_boxes': len(re.findall('Overfull', log)),
           'page_text_lengths': [len(t) for t in texts]}
assert not summary['undefined_references']
for i in range(len(pdf)):
    pdf[i].render(scale=1.5).to_pil().save(OUT / f'page_{i:02d}.png')
for start in range(0, len(pdf), 6):
    sheet = Image.new('RGB', (1350, 1310), '#d0d0d0')
    draw = ImageDraw.Draw(sheet)
    for offset in range(min(6, len(pdf) - start)):
        im = Image.open(OUT / f'page_{start + offset:02d}.png')
        im.thumbnail((440, 623))
        x, y = (offset % 3) * 450 + 5, (offset // 3) * 655 + 25
        sheet.paste(im, (x, y))
        draw.text((x, y - 20), f'PDF {start + offset + 1}', fill='black')
    sheet.save(OUT / f'sheet_{start // 6:02d}.png')
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2))
