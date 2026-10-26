"""从同一数据生成图文Markdown和唯一PDF；不再生成长图。"""
import html,json,re
from pathlib import Path
from urllib.parse import quote
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'秋天/赏红叶';OUT=ROOT/'output/pdf'
OUT.mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'docs/赏秋方案数据.json').read_text());P=D['plans'];DIM=D['dimensions'];VERSION=D['version']
for p in P:p['total']=round(sum(v*w/5 for v,(_,w) in zip(p['scores'],DIM)),1)
P.sort(key=lambda p:-p['total']);N=len(P)
PDF=OUT/'北京赏红叶与银杏_亲子图文攻略_20261026.pdf'
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf';pdfmetrics.registerFont(TTFont('CN',FONT))
INK='#233F34';RED='#AC482B';GOLD='#B78E42';PAPER='#FBF8F0';MUTED='#667268'
TRANSPORT='各家庭从西城、海淀、朝阳等实际地址分别出发，在约定的景区入口集合。先查本家当天导航，再倒推出门时刻；另留停车、进出站和步行20-30分钟。下列交通范围仅为排程宽预算，不是各行政区固定车程。'
RULE='六项0-5分，按秋色25、儿童适配25、交通15、时间舒适15、人流10、执行确定性10换算，总计100分。分数为规划比较，3分以内差距不宜过度解读。入口与合法通行是成行前提，不能用景色得分抵消。'
esc=html.escape

def score(p):return ' · '.join(f'{n}{v*w/5:g}/{w}' for v,(n,w) in zip(p['scores'],DIM))
def credit(ph):
 t=ph.get('credit','')
 if '@' in t or 'sky' in t or 'N509FZ' in t or '乐天' in t:return t
 return ph['source_name']+'；逐图署名见原文及素材说明'
def pic(ph,heading=False):
 s=('### '+ph['alt']+'\n\n') if heading else ''
 return s+f'![{ph["alt"]}]({ph["file"]})\n\n'+f'{ph["date_note"]}。[{ph["source_name"]}]({ph["source_url"]})。署名：{credit(ph)}。\n\n'
def fact_table(p):
 rows=[('核心特点',p['feature']+'。'+p['feature_summary']),('适合谁','8-9岁小学生家庭，能随队走山路、按最慢孩子调整'),('步行与强度',p['walk']),('集合',p['meeting']),('结束',p['finish']),('午饭',p['lunch_time']+'；'+({'baiwang':'东门艺园简餐，自带午餐备份','beigong':'南门区域简餐或自带午餐','gudao':'入口餐馆或自带午餐'}.get(p['id'],'自带午餐为主'))),('成行前提',p['conditions'])]
 return '| 项目 | 本次安排 |\n|---|---|\n'+''.join(f'| {k} | {v} |\n' for k,v in rows)+'\n'
def make_md():
 for i,p in enumerate(P,1):
  m=p['map']
  s=f'# {p["name"]}｜一日攻略\n\n> 排名 {i}/{N} · {p["total"]:.1f}/100 · 适合8-9岁 · {VERSION}\n\n'
  s+=f'**{p["feature"]}**\n\n{p["feature_summary"]}\n\n'+pic(p['photos'][0])
  s+='## 先看是否适合这次组队\n\n'+fact_table(p)
  s+='## 路线图与走法\n\n'+f'![{m["kind"]}]({m["file"]})\n\n'
  s+=f'**地图来源**：[{m["source_name"]}]({m["source_url"]})；{m["date_note"]}。\n\n**本次怎么走**：{m["reading"]}\n\n'
  s+='**游览顺序**：'+' → '.join(p['nodes'])+'。\n\n'+p['extra']+'\n\n'
  s+='## 沿路最值得看的景色\n\n'+'\n'.join('- '+x for x in p['spots'])+'\n\n'
  for ph in p['photos'][1:]:s+=pic(ph,True)
  s+='**赏秋时机**：'+p['season']+'\n\n'
  s+='## 一天怎么安排\n\n时间是儿童小队的组织安排，包含加餐、午饭、休息和拍照。现场按最慢孩子调整。\n\n| 时间 | 地点与安排 |\n|---|---|\n'+''.join(f'| {t} | {v} |\n' for t,v in p['day'])+'\n'
  s+='## 交通与集合\n\n**集合**：'+p['meeting']+'。\n\n**结束**：'+p['finish']+'。\n\n'+TRANSPORT+'\n\n'+p['travel_budget']+'\n\n**自驾**：'+p['drive']+'\n\n**公共交通**：'+p['transit']+'\n\n'
  s+=f'[打开高德地图搜索集合区域](https://www.amap.com/search?query={quote(p["map_query"])})。认准正文约定的入口，地名搜索结果不是精确轨迹。\n\n'
  for title,key in [('午饭怎么解决','food'),('厕所、补水与休息','facilities'),('门票与预算','ticket'),('一家一小预算参考','budget'),('折返与特别提醒','retreat'),('给孩子的观察任务','game')]:s+=f'## {title}\n\n{p[key]}\n\n'
  s+='## 分项评分与理由\n\n| 维度 | 0-5分 | 换算分 | 理由 |\n|---|---:|---:|---|\n'
  for (n,w),v,reason in zip(DIM,p['scores'],p['reasons']):s+=f'| {n}（权重{w}） | {v:.1f} | {v*w/5:.1f} | {reason} |\n'
  s+=f'\n**总分**：{p["total"]:.1f}/100。[统一评分说明](README.md#评分与排序)。\n\n'
  s+='## 资料依据\n\n'+p['ugc']+'\n\n'+'\n'.join(f'- [{n}]({u})' for n,u in p['sources'])+'\n\n'
  s+='照片只说明景观特点，历史图片不代表本周叶色。地图按来源标注，地区底图不是已验证的同线轨迹；当天开放、票务和公交以官方信息为准。共同装备与集合规则见[行前准备](出行准备与安全.md)。\n\n[返回总览](README.md) · [图片与地图署名](assets/README.md)\n'
  (BASE/p['file']).write_text(s)
 # 总览先比较，再看照片，避免连续大图把评分埋到页底。
 s=f'# 北京赏红叶与银杏｜{N}条亲子一日路线\n\n> {VERSION} · 8-9岁 · 西城、海淀、朝阳等分别出发 · 当天往返\n\n'
 s+='想轻松组队、地铁会合，先看百望山；想兼顾湖景彩林与爬山，看北宫；专注红叶看西山；愿意用完整一天走古道加古银杏，看广慧寺。冯村需熟路领队先核入口和通行。\n\n## 评分与排序\n\n'+RULE+'\n\n'
 s+='| 排名 | 方案 | 秋色25 | 儿童25 | 交通15 | 舒适15 | 人流10 | 确定性10 | 总分 | 核心特点 |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---|\n'
 for i,p in enumerate(P,1):s+=f'| {i} | [{p["name"]}]({p["file"]}) | '+' | '.join(f'{v*w/5:.1f}' for v,(_,w) in zip(p['scores'],DIM))+f' | **{p["total"]:.1f}** | {p["feature"]} |\n'
 s+='\n## 看图选路线\n\n'
 for i,p in enumerate(P,1):
  s+=f'### {i}. [{p["name"]}]({p["file"]}) · {p["total"]:.1f}分\n\n**{p["feature"]}**\n\n{p["feature_summary"]}\n\n'+pic(p['photos'][0])
  s+=f'**一天安排**：{p["meeting"]}；{p["lunch_time"]}午饭；{p["finish"]}结束。\n\n**步行**：{p["walk"]}\n\n'
 s+='## 集合与交通\n\n'+TRANSPORT+'\n\n'
 s+='| 方案 | 集合 | 结束 | 成行前提 |\n|---|---|---|---|\n'+''.join(f'| {p["name"]} | {p["meeting"]} | {p["finish"]} | {p["conditions"]} |\n' for p in P)+'\n'
 s+='## 地图与资料怎么读\n\n六处使用实际景区导览图或导览牌实拍；广慧寺和冯村采用有来源的地区地图，标明步行段、车行衔接与核验边界。不要把完整景区长环线、成人用时或山峰海拔当作本次儿童队实测。各页注明图源和拍摄时段，不把旧图当实时秋色。\n\n'
 s+=f'## 唯一分享文件\n\n[下载最新完整PDF](../../output/pdf/{PDF.name})：首页评分总表，每条路线包含照片、地图与主要攻略。旧长图不再保留。\n\n[出行准备](出行准备与安全.md) · [素材署名](assets/README.md)\n'
 (BASE/'README.md').write_text(s)
 s='# 去哪遛娃\n\n北京四季亲子出游方案库。按孩子体力、季节、交通、吃饭和撤返来规划。\n\n| 春 | 夏 | 秋 | 冬 |\n|---|---|---|---|\n| [春天](春天/README.md) | [夏天](夏天/README.md) | [秋天](秋天/README.md) | [冬天](冬天/README.md) |\n\n## 北京赏红叶与银杏\n\n8条当天往返的亲子路线：逐项评分、主要景色照片、真实导览图、一日时间表与交通用餐安排。\n\n'
 s+='![北宫湖畔彩林](秋天/赏红叶/assets/beigong-scene-1.jpg)\n\n图片来源与资料时段见[北宫攻略](秋天/赏红叶/02-北宫山林赏秋.md)。\n\n'
 s+='- [总览：评分、特点、看图选路线](秋天/赏红叶/README.md)\n'+''.join(f'- [{i}. {p["name"]}](秋天/赏红叶/{p["file"]})\n' for i,p in enumerate(P,1))
 s+=f'- [下载最新完整PDF](output/pdf/{PDF.name})\n\n所有方案均需按当日开放和孩子体力执行。照片不承诺本周叶色；地图来源与适用范围逐条注明。\n'
 (ROOT/'README.md').write_text(s)
 (ROOT/'秋天/README.md').write_text('# 秋天\n\n[北京赏红叶与银杏：8条亲子一日路线](赏红叶/README.md)\n\n图文攻略、分项评分、实际导览图和最新PDF集中在同一主题。\n\n[返回四季首页](../README.md)\n')
 s='# 图片与地图来源\n\n所有原图均保留既有署名与水印，不改叶色、不把春季资料说成秋季实况。照片权利归原作者；第三方图片不因在官方综合稿中出现而变成开放许可。\n\n'
 for p in P:
  s+='## '+p['name']+'\n\n'
  for ph in p['photos']:s+=f'- `{Path(ph["file"]).name}`：{ph["alt"]}。[{ph["source_name"]}]({ph["source_url"]})；{ph["date_note"]}；{ph["credit"]}。\n'
  m=p['map'];s+=f'- 地图 `{Path(m["file"]).name}`：[{m["source_name"]}]({m["source_url"]})；{m["date_note"]}。{m.get("rights_note", "原图著作权归原制作者；仅标明本次游览区域，不作实时通行证明。")}\n\n'
 s+='CC BY-SA照片按[CC BY-SA 4.0许可](https://creativecommons.org/licenses/by-sa/4.0/)署名；OpenStreetMap底图署名© OpenStreetMap contributors，地理数据ODbL，见 https://www.openstreetmap.org/copyright 。地图标记仅表示可核对地标，不据POI直线拼接徒步轨迹。\n'
 (BASE/'assets/README.md').write_text(s)

def para(c,t,x,y,w,size=10,draw=True,color=INK,leading=1.48):
 st=ParagraphStyle('p',fontName='CN',fontSize=size,leading=size*leading,textColor=HexColor(color),wordWrap='CJK')
 q=Paragraph(t,st);_,h=q.wrap(w,10000)
 if draw:q.drawOn(c,x,y-h)
 return y-h-6

def tx(c,t,x,y,size=10,color=INK):c.setFont('CN',size);c.setFillColor(HexColor(color));c.drawString(x,y,t)
def bg(c):c.setFillColor(HexColor(PAPER));c.rect(0,0,595,842,fill=1,stroke=0)
def foot(c,n):
 c.setStrokeColor(HexColor('#DAD8CA'));c.line(30,37,565,37);tx(c,f'去哪遛娃 · {VERSION} · 北京赏红叶与银杏',30,23,7.5,MUTED);tx(c,str(n),550,23,8,MUTED)
def image_fit(c,path,x,y,w,h,back=True):
 im=Image.open(path);iw,ih=im.size;scale=min(w/iw,h/ih);ww,hh=iw*scale,ih*scale
 if back:c.setFillColor(HexColor('#EFE9DA'));c.rect(x,y,w,h,fill=1,stroke=0)
 dest=Path(path)
 if dest.suffix.lower()!='.jpg' or max(iw,ih)>1800:
  cache=ROOT/'tmp/pdf-assets';cache.mkdir(parents=True,exist_ok=True);dest=cache/(Path(path).stem+'.jpg')
  rgb=im.convert('RGB');rgb.thumbnail((1800,1800));rgb.save(dest,quality=91)
 c.drawImage(str(dest),x+(w-ww)/2,y+(h-hh)/2,ww,hh,mask='auto')
def header(c,p,i,label):
 bg(c);tx(c,f'{i:02d} {p["name"]}',30,801,21);tx(c,f'{p["total"]:.1f}/100',472,801,13,RED)
 return para(c,esc(p['feature'])+' · '+label,30,781,535,10,color=RED)
def caption(c,ph,x,y,w,size=7.7):
 y=para(c,esc(ph['alt']),x,y,w,size+0.6)
 who=credit(ph)
 if len(who)>70:who=ph['source_name']+'；完整署名见素材说明'
 date=ph['date_note']
 if w<300:
  who=ph['source_name']
  date=('2025春季资料，非秋色' if '春' in date else ('2025往年资料' if '2025' in date else '资料图，拍摄日期见来源'))
 return para(c,f'<a href="{esc(ph["source_url"])}" color="{RED}">{esc(who)}</a> · '+esc(date),x,y,w,size,color=MUTED)
def detail_body(c,p,top,size,draw=True):
 left=para(c,'<b>一日时间表</b>',30,top,255,size+1,draw,RED)
 for t,v in p['day']:left=para(c,f'<b>{esc(t)}</b> {esc(v)}',30,left,255,size,draw)
 left=para(c,'<b>折返与特别提醒</b> '+esc(p['retreat']),30,left-4,255,size,draw,RED)
 left=para(c,'<b>给孩子的任务</b> '+esc(p['game']),30,left,255,size,draw)
 right=top
 for title,key in [('自驾停车','drive'),('公共交通','transit'),('午饭','food'),('厕所补给','facilities'),('门票','ticket'),('预算','budget')]:right=para(c,f'<b>{title}</b> '+esc(p[key]),310,right,255,size,draw)
 y=min(left,right)-5
 y=para(c,'<b>赏秋时机</b> '+esc(p['season']),30,y,535,size-0.6,draw)
 links=' · '.join(f'<a href="{esc(u)}" color="{RED}">[{j}] {esc(n)}</a>' for j,(n,u) in enumerate(p['sources'],1))
 return para(c,links,30,y,535,max(7.2,size-1.4),draw)

def make_pdf():
 c=canvas.Canvas(str(PDF),pagesize=(595,842));c.setTitle('北京赏红叶与银杏｜8条亲子图文攻略');c.setAuthor('去哪遛娃')
 bg(c);tx(c,'北京赏红叶与银杏',30,797,28);tx(c,'8条亲子一日路线 · 评分与特点',30,762,17,RED)
 y=para(c,'适合8-9岁小学生。各家庭从西城、海淀、朝阳等分别出发，在目的地会合，当天往返。先看总表，再按照片和地图选择。',30,739,535,10)
 widths=[21,111,32,32,32,32,32,32,35,176];scale=535/sum(widths);widths=[v*scale for v in widths]
 heads=['序','方案','秋色25','儿童25','交通15','舒适15','人流10','确定10','总分','核心特点']
 x=30;top=y-8
 for v,w in zip(heads,widths):c.setFillColor(HexColor(INK));c.rect(x,top-36,w,36,fill=1,stroke=0);para(c,v,x+3,top-10,w-6,7.1,color='#FFFFFF');x+=w
 top-=36
 for i,p in enumerate(P,1):
  vals=[str(i),p['name']]+[f'{v*w/5:.1f}' for v,(_,w) in zip(p['scores'],DIM)]+[f'{p["total"]:.1f}',p['feature']]
  x=30
  for v,w in zip(vals,widths):
   c.setFillColor(HexColor('#FFFFFF' if i%2 else '#F0EBDD'));c.rect(x,top-56,w,56,fill=1,stroke=0);para(c,esc(v),x+3,top-11,w-6,7.9 if w>45 else 7.2);x+=w
  c.linkRect('',f'plan-{p["id"]}',(30,top-56,565,top),relative=0,thickness=0)
  top-=56
 y=para(c,esc(RULE),30,top-17,535,9)
 y=para(c,'<b>怎么选</b>：地铁会合看百望山；彩林湖景看北宫；红叶山林看西山；完整一天古道加古银杏看广慧寺。冯村需熟路领队确认入口和通行后再成行。',30,y-2,535,9.5)
 y=para(c,'每条三页：景色精选、路线导览、一日攻略。旧长图已停止保留；拍摄日期和地图来源逐图注明。',30,y-2,535,9)
 assert y>45,y;foot(c,1);c.showPage()
 for i,p in enumerate(P,1):
  # 1 / 景色：一张主图+三至四张互补照片。
  c.bookmarkPage(f'plan-{p["id"]}');c.addOutlineEntry(f'{i}. {p["name"]}',f'plan-{p["id"]}',level=0,closed=False)
  y=header(c,p,i,'景色精选');y=para(c,esc(p['feature_summary']),30,y,535,10.3)
  photos=p['photos'][:5];hero=photos[0];w0,h0=Image.open(BASE/hero['file']).size
  if h0>w0*1.15 and len(photos)==5:
   # 竖幅古树/古寺用双主图，不把竖照缩成一条夹在大片空框中。
   for j,ph in enumerate(photos[:2]):
    x=30+j*273;image_fit(c,BASE/ph['file'],x,420,262,300,back=False);caption(c,ph,x,414,262,7.0)
   for j,ph in enumerate(photos[2:]):
    x=30+j*181;image_fit(c,BASE/ph['file'],x,130,173,230,back=False);caption(c,ph,x,124,173,7.0)
  else:
   image_fit(c,BASE/hero['file'],30,405,535,315,back=False);caption(c,hero,30,399,535,7.6)
   others=photos[1:]
   if len(others)==3:
    for j,ph in enumerate(others):
     x=30+j*181;image_fit(c,BASE/ph['file'],x,130,173,190,back=False);caption(c,ph,x,124,173,7.0)
   else:
    for j,ph in enumerate(others):
     x=30+(j%2)*273;yy=240-(j//2)*152;image_fit(c,BASE/ph['file'],x,yy,262,110,back=False);caption(c,ph,x,yy-5,262,7.0)
  # 图注已经包含年份，避免把任何历史照片当实时叶色。
  foot(c,3*i-1);c.showPage()
  # 2 / 地图：真实底图独立展示，地图文字优先于装饰。
  y=header(c,p,i,'路线导览');m=p['map']
  y=para(c,'<b>本次怎么走</b> '+esc(m['reading']),30,y,535,9.7)
  map_top=y-5;bottom=133;image_fit(c,BASE/m['file'],30,bottom,535,map_top-bottom,back=False)
  y=para(c,f'<a href="{esc(m["source_url"])}" color="{RED}">地图来源：{esc(m["source_name"])}</a> · '+esc(m['date_note']),30,122,535,7.8)
  y=para(c,'<b>游览顺序</b> '+esc(' → '.join(p['nodes']))+'。',30,y,535,9)
  y=para(c,esc(p['conditions'])+'。完整地图长线并非本次必走线路；以当天正规开放路牌为准。',30,y,535,8.5,color=RED)
  assert y>42,(p['id'],'map caption',y);foot(c,3*i);c.showPage()
  # 3 / 主要攻略：照片地图与日程相互对应，字不能因固定两页而越缩越小。
  y=header(c,p,i,'一日攻略')
  y=para(c,'<b>集合</b> '+esc(p['meeting'])+'；<b>结束</b> '+esc(p['finish']),30,y,535,9.7)
  y=para(c,'<b>步行</b> '+esc(p['walk']),30,y,535,9.5)
  top=y-5;size=9.5
  while size>=8.7 and detail_body(c,p,top,size,False)<47:size-=0.2
  assert size>=8.7,(p['id'],'body does not fit',size)
  last=detail_body(c,p,top,size,True);assert last>43,(p['id'],last)
  foot(c,3*i+1);c.showPage()
 bg(c);tx(c,'出发前，把这几件事约好',30,799,24)
 y=para(c,esc(TRANSPORT),30,761,535,11)
 items=[('前一天家长群','准确入口定位、人数、车辆与公交方案、预计抵达时刻、午饭；公交家庭先查返程和末班。迟到由成人在入口会合，不让儿童独自追队。'),('共同装备','防滑鞋、分层保暖、替换汗湿内层、温水、午饭与加餐、个人药品、垃圾袋；成人备离线地图、充电宝、应急头灯与急救包。'),('运动节奏','8-9岁小队按最慢孩子走，上坡能交谈，不比赛下坡；每45-60分钟短休。下午不临时加陌生山路，不依靠夜行赶完计划。'),('天气与开放','前一天及当天出门前查降雨、大风、空气质量和景区公告；湿叶打滑、临时封闭或孩子不适就缩短或取消山路。'),('两条山野线','广慧寺与冯村须由熟路领队核具体入口、同线地图及当日通行；区域地理图不是原帖7公里/300米实测轨迹，不能据图跨入围挡或野径。'),('照片与权利','资料图注明年份、作者和来源，旧叶色不等于今年实况。OpenStreetMap底图© OpenStreetMap contributors，地理数据ODbL；其他图片权利归原制作者。')]
 for title,t in items:y=para(c,f'<b>{title}</b> '+esc(t),30,y-9,535,10.5)
 y=para(c,'<a href="https://github.com/fanko24/quna-liuwa" color="#AC482B">GitHub最新图文攻略、逐项评分理由与完整素材署名</a>',30,y-12,535,11)
 assert y>45,y;foot(c,3*N+2);c.showPage();c.save()

def main():
 assert all(p.get('map',{}).get('file') for p in P),'缺少真实地图，禁止用流程图占位交付'
 make_md();make_pdf()
 print(json.dumps({'version':VERSION,'plans':N,'photos':sum(len(p['photos']) for p in P),'pages':3*N+2,'pdf':str(PDF)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
