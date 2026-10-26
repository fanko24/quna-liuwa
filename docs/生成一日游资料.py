"""唯一方案数据 -> GitHub文档、节点示意、长图、PDF。"""
import json,html,re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'秋天/赏红叶';OUT=ROOT/'output'
(OUT/'pdf').mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'docs/赏秋方案数据.json').read_text());P=D['plans'];DIM=D['dimensions']
for p in P:p['total']=round(sum(v*w/5 for v,(_,w) in zip(p['scores'],DIM)),1)
P.sort(key=lambda p:-p['total'])
N=len(P);VERSION=D['version']
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
pdfmetrics.registerFont(TTFont('CN',FONT))
INK='#243D35';RED='#AE4B2B';PAPER='#FBF8EF';GOLD='#BD903D'
PDF=OUT/'pdf/北京赏红叶与银杏_一日游方案_20261026_v2.pdf'
PNG=OUT/'北京赏红叶与银杏_一日游长图_20261026_v2.png'
TRANSPORT='各家庭从西城、海淀、朝阳等实际地址分别出发，在景区入口集合，不先绕到一个市区点。出门时刻=集合时刻-本家当日路线预计耗时-停车/步行20至30分钟。各方案的分钟数只是跨城排程宽预算，不是导航实测；不能把行政区当成一个固定起点。'
RETURN='普通线路约14:30至15:30点名解散，广慧寺两寺一阁约15:45至16:00结束；各家按实际交通回城，不承诺相同到家时间。10月底日落约17:13，山谷会更早暗，山路以16:00前结束为目标。公交家庭必须在周五核去返班次、末班和末段接驳，不能靠下山临时叫车。'
RULE='评分为主观规划比较：秋色25、儿童25、交通15、舒适15、人流10、确定性10；每项0-5分，换算=分项/5×权重。约7公里、爬升300米是用户认可的参考，不表示12公里600米也等强度；同名路线须核同一轨迹。'
def esc(t):return html.escape(t)
def score(p):return ' / '.join(f'{n}{v*w/5:g}/{w}' for v,(n,w) in zip(p['scores'],DIM))
def svg(p):
 a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="205"><rect width="1100" height="205" fill="{PAPER}"/>',f'<text x="24" y="30" font-family="sans-serif" font-size="20" fill="{INK}">{esc(p["name"])} · 节点示意</text>']
 for i,t in enumerate(p['nodes']):
  x=24+i*214;a.append(f'<rect x="{x}" y="55" width="195" height="80" rx="12" fill="{INK}"/>')
  for j in range(0,len(t),10):a.append(f'<text x="{x+98}" y="{87+j//10*23}" text-anchor="middle" font-family="sans-serif" font-size="16" fill="white">{esc(t[j:j+10])}</text>')
  if i<4:a.append(f'<text x="{x+199}" y="99" font-size="21" fill="{GOLD}">›</text>')
 a.append(f'<text x="24" y="179" font-size="16" font-family="sans-serif" fill="{RED}">不按比例、不表示方位、不作GPS导航；开放连接段以现场导览与熟路成人核验为准。</text></svg>')
 (BASE/'assets'/f'{p["id"]}-route.svg').write_text('\n'.join(a))
def make_md():
 for i,p in enumerate(P,1):
  svg(p)
  s=f'# {p["name"]}：一日攻略\n\n> {p["tag"]}｜排名{i}/{N}｜{VERSION}｜8-9岁孩子｜基准周末10月31日至11月1日。各城区出发，当天往返；未实地踩线或电话预订。\n\n'
  s+=f'**特点：{p["feature"]}。{p["feature_summary"]}**\n\n'
  s+='## 评分\n\n| 维度 | 0-5分 | 换算分 | 理由 |\n|---|---:|---:|---|\n'
  for (n,w),v,reason in zip(DIM,p['scores'],p['reasons']):s+=f'| {n}（{w}） | {v:.1f} | {v*w/5:.1f} | {reason} |\n'
  s+=f'\n**总分{p["total"]:.1f}/100。** [统一评分说明](README.md#评分与排序)。\n\n'
  s+='## 从全市各处怎么会合\n\n**集合：**'+p['meeting']+'。\n\n**结束：**'+p['finish']+'。\n\n'+TRANSPORT+'\n\n'+p['travel_budget']+'\n\n**自驾：**'+p['drive']+'\n\n**公共交通：**'+p['transit']+'\n\n**迟到：**出发前30分钟在家长群报预计抵达时刻；缓冲窗口内集合，超过窗口由领队决定全队等候还是安排成人陪迟到家庭在入口会合。不得让儿童独自在山路追队。\n\n'
  s+='## 路线与景色\n\n'+p['walk']+'\n\n'+f'![路线节点示意](assets/{p["id"]}-route.svg)\n\n'+' → '.join(p['nodes'])+'。\n\n'+p['extra']+'\n\n**打卡点**\n\n'+'\n'.join('- '+x for x in p['spots'])+'\n\n**赏秋时机：**'+p['season']+'\n\n'
  s+='## 一天怎么安排\n\n各时间为组织建议，不是节点实测。吃饭、拍照、休息和停车接近均算进一天；能当天往返不等于必须把所有加量段走完。\n\n| 时间 | 安排 |\n|---|---|\n'+'\n'.join(f'| {t} | {v} |' for t,v in p['day'])+'\n\n'
  for title,key in [('吃饭与备用午餐','food'),('厕所、补水与休息','facilities'),('门票、开放与预约','ticket'),('家庭预算','budget'),('缩短路线与撤退','retreat'),('给孩子的观察任务','game')]:s+=f'## {title}\n\n{p[key]}\n\n'
  if p['id']=='tanzhe':s+='![潭柘寺门楼历史实景](assets/tanzhe-gate-20251109.jpg)\n\nN509FZ，2025-11-09，CC BY-SA 4.0；不是本周叶色，也不是帝王树定位图。[完整署名](assets/README.md)。\n\n'
  s+='## 资料与仍待确认\n\n'+p['ugc']+'\n\n'+'\n'.join(f'- [{name}]({url})' for name,url in p['sources'])+'\n\n旧照片、成人轨迹、官方稳定规则和本周开放分开看。停车费、门票优惠、餐馆营业、接驳均须临期核实。未授权原图不打包，原帖可要求登录。\n\n[返回方案总览](README.md) · [行前准备](出行准备与安全.md)\n'
  (BASE/p['file']).write_text(s)
 intro=f'# 北京赏红叶与银杏：{N}个亲子一日选择\n\n> {VERSION}｜北京西城、海淀、朝阳等各城区分别出发｜8-9岁小队｜自驾或公共交通当天往返｜参考强度约7公里、爬升300米，可安排完整一天。千灵山和不再推荐的独立旧页已移除。\n\n'
 intro+='## 每处有什么特点\n\n| 地点 | 一句话特点 |\n|---|---|\n'
 for p in P:intro+=f'| [{p["name"]}]({p["file"]}) | **{p["feature"]}**：{p["feature_summary"]} |\n'
 intro+='\n地铁会合优先百望山；彩林与登山结合选北宫、西山；全天山林加古银杏选广慧寺两寺一阁；冯村推荐栈道往返与远眺。每处一个推荐行程，特殊情况写备注。\n\n'
 intro+='## 评分与排序\n\n'+RULE+' 小于3分的差距不表示显著优劣。安全、合法进入和回程时间是独立门槛，不能靠景色高分抵消。\n\n| 排名 | 方案 | 秋色25 | 儿童25 | 交通15 | 舒适15 | 人流10 | 确定性10 | 总分 |\n|---|---|---:|---:|---:|---:|---:|---:|---:|\n'
 for i,p in enumerate(P,1):intro+=f'| {i} | [{p["name"]}]({p["file"]}) | '+' | '.join(f'{v*w/5:.1f}' for v,(_,w) in zip(p['scores'],DIM))+f' | **{p["total"]:.1f}** |\n'
 intro+='\n交通评分已按全市分散出发调整；不再因“靠近市区西部”给所有家庭同样的通勤优势。行政区范围很大，无法仅凭“海淀”给一个准确车程。\n\n## 集合与返程\n\n'+TRANSPORT+'\n\n'+RETURN+'\n\n| 方案 | 集合地点与时刻 | 结束窗口 | 排程用交通预算（非导航实测） |\n|---|---|---|---|\n'
 for p in P:intro+=f'| {p["name"]} | {p["meeting"]} | {p["finish"]} | {p["travel_budget"]} |\n'
 intro+='\n**举例：**09:30集合，如果某家导航90分钟，停车步行另留25分钟，则约07:35出门；另一家导航50分钟，同样缓冲则约08:15出门。这个例子不代表西城或朝阳固定车程。公交家庭先核回程，再决定去程；约好景区入口，不在市区绕路集合。\n\n## 路线强度与全天内容\n\n| 方案 | 步行与强度 | 取舍 |\n|---|---|---|\n'
 for p in P:intro+=f'| {p["name"]} | {p["walk"]} | {p["extra"]} |\n'
 intro+='\n## 特殊备注\n\n已读[sky原帖](https://www.xiaohongshu.com/explore/69192d0f0000000007021a68)：2025-11-16编辑，记录11月14日，约7公里/300米/成人3.5小时。按认可强度推荐全天两寺一阁：先走山林，回村后乘车到潭柘寺正式入口购票参观。不照抄成人用时、15分钟打车、免费停车、巨石拍照或后山入寺。2026另帖7公里500米是另一版本，不能拼接。\n\n冯村旧完整线12公里/600米/7小时，强度更高且有旧锁门绕行提示。本次只推荐正规栈道原路往返，远眺定都阁，不伪造到阁轻松闭环。节点图不按比例，不作GPS导航；公里控制目标不等于实测。\n\n'
 intro+='## 分享文件\n\n- [新版精简长图](../../output/'+PNG.name+')\n- [新版PDF一日游攻略](../../output/pdf/'+PDF.name+')\n- [图片署名](assets/README.md)\n- [行前准备](出行准备与安全.md)\n\n资料来源分别列在各方案。没有实地踩线、电话订餐、买票或承诺有停车位。部分2025小红书原帖未取得正文，使用去年官方秋季资料对照，不宣称全渠道覆盖。\n'
 (BASE/'README.md').write_text(intro)
 root='# 去哪遛娃\n\n北京四季亲子出游方案库。按孩子体力、季节、实际交通、吃饭与撤返规划。\n\n| 季节 | 入口 |\n|---|---|\n| 春天 | [春天](春天/README.md) |\n| 夏天 | [夏天](夏天/README.md) |\n| 秋天 | [秋天](秋天/README.md) |\n| 冬天 | [冬天](冬天/README.md) |\n\n## 当前主题：北京赏红叶与银杏\n\n'+f'{N}个当天往返选择，{VERSION}。各城区分别出发、在景区集合；接受约7公里300米强度，每处一个推荐行程，特殊情况简短备注。\n\n'
 root+='- [总览、评分、全市出发安排](秋天/赏红叶/README.md)\n'+'\n'.join(f'- [{i}. {p["name"]}](秋天/赏红叶/{p["file"]})' for i,p in enumerate(P,1))+'\n\n'
 root+=f'- [群分享长图](output/{PNG.name})\n- [PDF一日攻略](output/pdf/{PDF.name})\n\n图为节点示意，不作GPS导航；开放、交通、票价和用餐临期核对。实景图片按来源许可署名，未授权原图不收录。仓库不保存儿童姓名、家庭地址、证件、会话令牌等私人信息。\n'
 (ROOT/'README.md').write_text(root)
 (ROOT/'秋天/README.md').write_text(f'# 秋天\n\n[北京赏红叶与银杏：{N}个一日选择](赏红叶/README.md)\n\n{VERSION}，各城区当天往返，独立评分、一日攻略、路线图、交通与吃饭同步更新。\n\n[返回四季首页](../README.md)\n')

def para(c,t,x,y,w,size=9.2,draw=True,color=INK):
 st=ParagraphStyle('p',fontName='CN',fontSize=size,leading=size*1.5,textColor=HexColor(color),wordWrap='CJK')
 q=Paragraph(t,st);_,h=q.wrap(w,10000)
 if draw:q.drawOn(c,x,y-h)
 return y-h-6
def tx(c,t,x,y,size=10,color=INK):c.setFont('CN',size);c.setFillColor(HexColor(color));c.drawString(x,y,t)
def bg(c):c.setFillColor(HexColor(PAPER));c.rect(0,0,595,842,fill=1,stroke=0)
def foot(c,n):
 c.setStrokeColor(HexColor('#DDD9CD'));c.line(32,38,563,38)
 tx(c,f'去哪遛娃 / {VERSION} / 各城区当天往返',32,24,7);tx(c,str(n),550,24,8)
def diagram(c,p,y):
 for i,t in enumerate(p['nodes']):
  x=32+i*107;c.setFillColor(HexColor(INK));c.roundRect(x,y-48,99,44,5,fill=1,stroke=0)
  para(c,esc(t),x+5,y-10,89,8.3,color='#FFFFFF')
  if i<4:tx(c,'›',x+100,y-33,13,GOLD)
 tx(c,'节点示意，不按比例、不表示方位，不作GPS导航。',32,y-62,7.5,RED)
 return y-77
def page_body(c,p,size,draw=True):
 top=603
 left=para(c,'<b>一日时间表</b>',32,top,250,size+1,draw,RED)
 for t,v in p['day']:left=para(c,f'<b>{esc(t)}</b> {esc(v)}',32,left,250,size,draw)
 left=para(c,'<b>缩短与撤退</b> '+esc(p['retreat']),32,left,250,size,draw,RED)
 right=top
 for title,key in [('自驾停车','drive'),('公共交通','transit'),('午饭','food'),('厕所补给','facilities'),('门票预约','ticket'),('预算','budget')]:right=para(c,f'<b>{title}</b> '+esc(p[key]),310,right,253,size,draw)
 y=min(left,right)-3
 y=para(c,'<b>秋色与打卡</b> '+esc('；'.join(p['spots'])+'。'+p['season']),32,y,531,size-0.4,draw)
 y=para(c,'<b>依据与版本</b> '+esc(p['ugc']),32,y,531,size-0.8,draw)
 links=' · '.join(f'<a href="{esc(u)}" color="#AE4B2B">[{i}] {esc(n)}</a>' for i,(n,u) in enumerate(p['sources'],1))
 return para(c,links,32,y,531,size-1.1,draw)
def make_pdf():
 c=canvas.Canvas(str(PDF),pagesize=(595,842));c.setTitle(f'北京赏红叶与银杏：{N}个一日选择');c.setAuthor('去哪遛娃')
 bg(c);tx(c,'去哪遛娃 / AUTUMN 2026',32,802,11,RED);tx(c,'北京赏红叶与银杏',32,765,28)
 tx(c,f'{N}个亲子一日选择',32,730,21)
 para(c,'各城区分别出发，当天自驾或公共交通往返<br/>8-9岁小队；认可约7公里/300米强度；每处一个推荐行程。',32,710,531,10)
 c.drawImage(str(BASE/'assets/tanzhe-gate-20251109.jpg'),160,473,width=275,height=183,mask='auto')
 tx(c,'潭柘寺历史实拍 / N509FZ / 2025-11-09 / CC BY-SA 4.0 / 非今年叶色',32,461,7)
 c.linkURL('https://commons.wikimedia.org/wiki/File:Entrance_gatetower_of_Tanzhe_Temple_(20251109144630).jpg',(32,454,563,468))
 y=432
 for i,p in enumerate(P,1):
  tx(c,f'{i:02d} {p["name"]}',32,y,12);tx(c,f'{p["total"]:.1f}',514,y,13,RED)
  para(c,esc(p['tag']),57,y-8,445,8.5);y-=37
 y=para(c,esc(RULE),32,y,531,8)
 y=para(c,'广慧寺回村后转潭柘寺；冯村推荐栈道往返与远眺，不承诺入阁。各页集合、饭点与结束时刻和GitHub、长图一致。',32,y,531,8,True,RED)
 assert y>45,y
 foot(c,1);c.showPage()
 for i,p in enumerate(P,1):
  bg(c);tx(c,f'{i:02d} {p["name"]}',32,801,21);tx(c,f'{p["total"]:.1f}/100',461,801,14,RED)
  tx(c,p['feature']+'｜'+p['feature_summary'],32,777,9.2,RED);tx(c,score(p),32,756,7.8)
  y=diagram(c,p,744)
  y=para(c,'<b>步行与强度</b> '+esc(p['walk']),32,y,531,9)
  if y<606: # 长线说明较长时压缩该段字体，保持正文共同起点。
   # 本段在首次绘制后不叠印：长文本由更小字号重新整页绘制。
   c.setFillColor(HexColor(PAPER));c.rect(30,605,535,65,fill=1,stroke=0)
   y=para(c,'<b>步行与强度</b> '+esc(p['walk']),32,667,531,8)
  assert y>604,(p['id'],y)
  size=9.4
  while size>=7.8 and page_body(c,p,size,False)<48:size-=0.2
  assert size>=7.8,(p['id'],size)
  last=page_body(c,p,size,True);assert last>45,(p['id'],last)
  foot(c,i+1);c.showPage()
 bg(c);tx(c,'各城区会合与行前核对',32,799,23)
 y=para(c,esc(TRANSPORT),32,765,531,11)
 y=para(c,'<b>倒推出门时刻</b><br/>例如09:30集合：本家导航90分钟、停车步行25分钟，约07:35出门；另一家导航50分钟，同样缓冲，则约08:15出门。这是算例，不是某个区的固定车程。',32,y-6,531,11)
 y=para(c,esc(RETURN),32,y-6,531,11)
 for p in P:
  y=para(c,f'<b>{esc(p["name"])}</b>：{esc(p["meeting"])}；结束{esc(p["finish"])}。',32,y,531,9)
 y=para(c,'<b>出发前一天</b>：家长群确认人数、车辆/公交方案、准确入口定位、去返路线、午饭、天气预警、当日开放和儿童票。熟路成人核同一轨迹与退出点。普通游线允许弹性调整，封闭、锁门、施工区不绕入。',32,y-6,531,10,True,RED)
 y=para(c,'<a href="https://github.com/fanko24/quna-liuwa" color="#AE4B2B">GitHub最新总览与每条攻略</a> · <a href="https://www.timeanddate.com/sun/china/beijing?month=10&amp;year=2026" color="#AE4B2B">北京10月日落参考</a>',32,y,531,9)
 assert y>45,y
 foot(c,N+2);c.showPage();c.save()
def make_long():
 W=1200;H=1180+N*450
 im=Image.new('RGB',(W,H),PAPER);dr=ImageDraw.Draw(im)
 fonts={s:ImageFont.truetype(FONT,s) for s in [20,22,24,26,28,30,34,40,54]}
 def text(t,x,y,s=26,col=INK):dr.text((x,y),t,font=fonts[s],fill=col)
 def wrap(t,x,y,w,s=26,col=INK,show=True):
  line=''
  for ch in t:
   if ch=='\n' or dr.textlength(line+ch,font=fonts[s])>w:
    if show:text(line,x,y,s,col)
    y+=int(s*1.45);line='' if ch=='\n' else ch
   else:line+=ch
  if line:
   if show:text(line,x,y,s,col)
   y+=int(s*1.45)
  return y
 text('去哪遛娃 / '+VERSION,48,30,24,RED);text('北京赏红叶与银杏',48,78,54)
 text(f'{N}个亲子一日选择',48,158,40)
 text('西城·海淀·朝阳等分别出发｜景区集合｜当天往返',48,223,24)
 photo=Image.open(BASE/'assets/tanzhe-gate-20251109.jpg');photo.thumbnail((1000,250));im.paste(photo,((W-photo.width)//2,274))
 text('潭柘寺历史实拍 / N509FZ / 2025-11-09 / CC BY-SA 4.0 / 非今年叶色',48,535,20)
 y=580
 for i,p in enumerate(P,1):
  rows=[(p['feature']+'｜'+p['feature_summary'],24,RED),(p['card_walk'],22,INK),('路线｜'+' → '.join(p['nodes']),24,INK),('一天｜'+p['card_day'],24,INK),('注意｜'+p['card_note'],22,INK)]
  yy=y+72
  for value,size,color in rows:yy=wrap(value,54,yy+4,1092,size,color,False)
  height=yy-y+58
  dr.rounded_rectangle((30,y,1170,y+height),radius=18,fill='white',outline='#DFDDCF',width=2)
  text(f'{i:02d}',50,y+15,40,RED);text(p['name'],135,y+20,30)
  text(f'{p["total"]:.1f}分',1005,y+20,30,RED)
  yy=y+72
  for value,size,color in rows:yy=wrap(value,54,yy+4,1092,size,color)
  text(score(p),54,yy+15,20,'#647268')
  y+=height+18
 y=wrap('接受约7km/300m的全天活动；成人用时另加儿童休息与饭点。广慧寺回村后转潭柘寺；冯村推荐栈道往返，不混入旧12km/600m环线。',48,y+8,1104,24)
 y=wrap('出门时刻＝本方案集合时刻－本家实际导航耗时－停车步行20至30分钟。公共交通先核回程末班和末段接驳，各家分别返城。',48,y+8,1104,24)
 y=wrap('评分权重：秋色25、儿童25、交通15、舒适15、人流10、确定性10。路线是节点示意，不是GPS；开放、票务、餐饮与停车临期确认。',48,y+8,1104,22)
 text('详细攻略、评分理由与来源见同版PDF/GitHub；不走封闭路段、不绕锁门。',48,y+12,22)
 assert y+75<H,(y,H)
 im=im.crop((0,0,W,y+75));im.save(PNG)
def main():
 make_md();make_pdf();make_long()
 print(json.dumps({'version':VERSION,'count':N,'ranking':[(p['name'],p['total']) for p in P],'pdf':str(PDF),'long':str(PNG)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
