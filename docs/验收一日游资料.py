"""核对唯一数据、单页、总览、PDF的名称/评分/特点/时间一致。"""
import json,re
from pathlib import Path
from pypdf import PdfReader
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'秋天/赏红叶';d=json.loads((ROOT/'docs/赏秋方案数据.json').read_text())
plans=d['plans'];dims=d['dimensions'];assert len(plans)==8
scores=[round(sum(v*w/5 for v,(_,w) in zip(p['scores'],dims)),1) for p in plans]
assert scores==sorted(scores,reverse=True)
pdf=PdfReader(ROOT/'output/pdf/北京赏红叶与银杏_一日游方案_20261026_v3.pdf')
assert len(pdf.pages)==2*len(plans)+2
overview=(BASE/'README.md').read_text()
for i,p in enumerate(plans,1):
 md=(BASE/p['file']).read_text();page=pdf.pages[2*i-1].extract_text()+pdf.pages[2*i].extract_text()
 for t in [p['name'],p['feature'],p['feature_summary'],f'{scores[i-1]:.1f}']:
  assert t in md,(p['id'],'单页',t)
  assert t in overview,(p['id'],'总览',t)
  assert t.replace(' ','') in page.replace(' ',''),(p['id'],'PDF',t)
 for t,v in p['day']:
  assert t in md and t in page,(p['id'],'时间',t)
  assert v in md,(p['id'],'日程',v)
 first_time=re.search(r'\d\d:\d\d',p['meeting']).group()
 assert first_time in p['card_day'],(p['id'],'长图集合时刻')
 for t in re.findall(r'\d\d:\d\d',p['finish']):assert t in p['card_day'],(p['id'],'长图结束时刻',t)
 assert (BASE/'assets'/f'{p["id"]}-route.svg').exists()
 assert (BASE/'assets'/f'{p["id"]}-plan.png').exists()
 assert len(p['photos'])>=2
 for ph in p['photos']:
  assert ph['file'] in md and ph['source_url'] in md
  assert (BASE/ph['file']).exists()
 assert '路线规划图' in md
bad=[]
for f in ROOT.rglob('*.md'):
 if '.git' in f.parts:continue
 txt=f.read_text()
 for u in re.findall(r'\]\(([^)\n]+)\)',txt):
  if u.startswith(('http:','https:','#','mailto:')):continue
  if not (f.parent/u.split('#')[0]).exists():bad.append((str(f),u))
 assert 'xsec_token' not in txt,str(f)
assert not bad,bad
assert not (BASE/'01-千灵山亲子线.md').exists()
for f in [BASE/'README.md',ROOT/'README.md']:
 assert 'TOP7' not in f.read_text() and '基础版' not in f.read_text()
im=Image.open(ROOT/'output/北京赏红叶与银杏_一日游长图_20261026_v3.png');assert im.width==1200;im.verify()
print('PASS：8条路线；评分排序、特点、PDF/Markdown日程、长图时刻字段一致；18页PDF；节点图齐全；本地链接及旧文件检查通过。')
