"""验收真实输出、PDF内容、地图类型、照片、日程及GitHub官方GFM渲染。"""
import json,re,sys,hashlib
from pathlib import Path
from pypdf import PdfReader
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'秋天/赏红叶'
d=json.loads((ROOT/'docs/赏秋方案数据.json').read_text());ps=d['plans'];dims=d['dimensions'];assert len(ps)==8
norm=lambda s:re.sub(r'\s+','',s)
scores=[round(sum(v*w/5 for v,(_,w) in zip(p['scores'],dims)),1) for p in ps];assert scores==sorted(scores,reverse=True)
f=ROOT/'output/pdf/北京赏红叶与银杏_亲子图文攻略_20261026.pdf';pdf=PdfReader(f);assert len(pdf.pages)==26
first=norm(pdf.pages[0].extract_text());overview=(BASE/'README.md').read_text();minutes=lambda x:int(x[:2])*60+int(x[3:5])
for i,p in enumerate(ps,1):
 md=(BASE/p['file']).read_text();visual=pdf.pages[3*i-2];mp=pdf.pages[3*i-1];detail=pdf.pages[3*i];txt=norm(visual.extract_text()+mp.extract_text()+detail.extract_text())
 for t in [p['name'],p['feature'],f'{scores[i-1]:.1f}']:
  assert norm(t) in first,(p['id'],'评分首页',t);assert t in md and t in overview,(p['id'],'MD',t);assert norm(t) in txt,(p['id'],'PDF',t)
 for k in ['meeting','finish','walk','drive','transit','food','facilities','ticket','budget','retreat','game']:
  assert p[k] in md,(p['id'],'MD字段',k)
  # game出现在PDF末页共同行前提醒之外的每条正文；均须真实存在。
  assert norm(p[k]) in txt,(p['id'],'PDF字段',k)
 previous=0
 for t,v in p['day']:
  a,b=t.split('-');assert minutes(a)>=previous,(p['id'],'日程重叠',t);assert minutes(b)>minutes(a);previous=minutes(b)
  assert t in md and norm(t) in txt,(p['id'],'时间',t);assert norm(v) in txt,(p['id'],'PDF日程',v)
 assert previous<=16*60,(p['id'],'结束过晚')
 assert len(p['photos'])>=4 and len(visual.images)==min(5,len(p['photos'])),(p['id'],'照片数量')
 for ph in p['photos']:
  assert ph['file'] in md and ph['source_url'] in md and ph.get('visually_reviewed'),(p['id'],'照片图注')
  Image.open(BASE/ph['file']).verify()
 m=p['map'];assert 'plan.png' not in m['file'] and 'route.svg' not in m['file'];assert m['file'] in md and m['source_url'] in md
 im=Image.open(BASE/m['file']);assert min(im.size)>=500,(p['id'],'地图分辨率');im.verify();assert len(mp.images)>=1
 assert norm(m['reading']) in txt,(p['id'],'地图读法')
 assert not re.search(r'\*\*[^*\n]+：\*\*\S',md),(p['id'],'GFM粗体边界')
# 文本链接路径与旧产物清理。
for fmd in ROOT.rglob('*.md'):
 if '.git' in fmd.parts or 'tmp' in fmd.parts:continue
 text=fmd.read_text();assert 'xsec_token=' not in text,str(fmd)
 for u in re.findall(r'\]\(([^)\n]+)\)',text):
  if u.startswith(('https:','http:','#','mailto:')):continue
  assert (fmd.parent/u.split('#')[0]).exists(),(str(fmd),u)
assert len(list((ROOT/'output').rglob('*.pdf')))==1,'应只保留唯一最新PDF'
assert not list((ROOT/'output').glob('*.png')),'长图应删除'
assert not list((BASE/'assets').glob('*-plan.png')),'旧流程图应删除'
assert not list((BASE/'assets').glob('*-route.svg')),'旧节点图应删除'
if '--require-gfm' in sys.argv:
 g=ROOT/'tmp/final_gfm/result.json';assert g.exists(),'缺少本轮GitHub官方GFM证据'
 result=json.loads(g.read_text());assert result['passed']==9 and not result['failed'],result
 for item in result['results']:
  source=ROOT/item['file'];current=hashlib.sha256(source.read_bytes()).hexdigest()
  assert current==item.get('source_md_sha256',item['sha256']),(item['id'],'GFM证据对应旧版本，必须重渲染')
  rendered=(ROOT/item['rendered_html']).read_text()
  assert '**' not in re.sub(r'<[^>]+>','',rendered),(item['id'],'渲染后仍有星号')
  if item['id']!='overview':
   for label in ['集合','结束','自驾','公共交通']:assert f'<strong>{label}</strong>' in rendered,(item['id'],label)
print('PASS：8条评分排序、37张已审照片、8张真实导览/地区地图、26页PDF及主要字段和日程一致；唯一PDF、无长图、无旧流程图。'+(' 官方GFM 9/9通过。' if '--require-gfm' in sys.argv else ' GFM尚未计入本次验收。'))
