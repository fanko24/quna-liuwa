"""由同一份方案数据生成 Markdown、示意图、分享长图与 PDF。"""
import json, math, re, html
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'秋天/赏红叶'
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)
(OUT/'pdf').mkdir(exist_ok=True)
DATA=json.loads((ROOT/'docs/赏秋方案数据.json').read_text())
DIMS=DATA['dimensions']
PLANS=DATA['plans']
for p in PLANS:
    p['total']=round(sum(s*w/5 for s,(_,w) in zip(p['scores'],DIMS)),1)
PLANS.sort(key=lambda p:-p['total'])
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
pdfmetrics.registerFont(TTFont('CN',FONT))
INK='#243D35'; ORANGE='#AF4829'; GOLD='#C79335'; PAPER='#FBF8EF'; PALE='#EAECDD'

def score_table(p):
    lines=['| 维度 | 0-5分 | 权重 | 换算得分 | 理由 |','|---|---:|---:|---:|---|']
    for (n,w),s,r in zip(DIMS,p['scores'],p['reasons']):
        lines.append(f'| {n} | {s:.1f} | {w} | {s*w/5:.1f} | {r} |')
    return '\n'.join(lines)+f'\n\n**总分：{p["total"]:.1f}/100。** 主观规划分，不是景区评级；见[评分规则](README.md#评分规则)。'

def route_svg(p):
    labels=p['nodes']; xs=[24+i*185 for i in range(len(labels))]
    s=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="210" viewBox="0 0 960 210">',f'<rect width="960" height="210" fill="{PAPER}"/>',f'<text x="25" y="30" font-size="20" fill="{INK}" font-family="sans-serif">{html.escape(p["name"])} · 路线节点示意</text>']
    for i,(x,t) in enumerate(zip(xs,labels)):
        if i<4:s.append(f'<path d="M{x+152} 96 H{x+181}" stroke="{GOLD}" stroke-width="3"/><path d="M{x+174} 90 L{x+181} 96 L{x+174} 102" fill="none" stroke="{GOLD}" stroke-width="3"/>')
        s.append(f'<rect x="{x}" y="60" width="155" height="78" rx="12" fill="{INK}"/>')
        chunks=[t[j:j+8] for j in range(0,len(t),8)]
        for j,txt in enumerate(chunks):s.append(f'<text x="{x+77}" y="{93+j*23}" text-anchor="middle" font-size="16" fill="white" font-family="sans-serif">{html.escape(txt)}</text>')
    s.append(f'<text x="25" y="180" font-size="16" fill="{ORANGE}" font-family="sans-serif">不按比例 · 不代表方位或GPS轨迹 · 节点连接、开放状态以现场导览和工作人员为准</text></svg>')
    (BASE/'assets'/f'{p["id"]}-route.svg').write_text('\n'.join(s))

def make_md():
    for i,p in enumerate(PLANS,1):
        route_svg(p)
        s=f'# {p["name"]}：一日攻略\n\n> {p["tag"]}｜本轮排名 {i}｜资料整理：2026-10-26｜基准周末：10月31日至11月1日。8-9岁多孩小队，山林徒步优先。未实地踩线、未电话预订。\n\n'
        s+='## 怎么选与评分\n\n'+score_table(p)+'\n\n'
        s+='## 路线、景色与体力\n\n'+p['walk']+'\n\n'+f'![路线节点示意](assets/{p["id"]}-route.svg)\n\n'+' → '.join(p['nodes'])+'。\n\n'+p['extra']+'\n\n'
        s+='**打卡点**\n\n'+'\n'.join('- '+v for v in p['spots'])+'\n\n**今年时机：**'+p['season']+'\n\n'
        s+='## 一天怎么安排\n\n时间为组织建议，不是实测到达时间；每段按最慢孩子调整，取消后半段也算完成。\n\n| 时间 | 安排 |\n|---|---|\n'+'\n'.join('| '+t+' | '+v+' |' for t,v in p['day'])+'\n\n'
        for title,key in [('自驾与停车','drive'),('公共交通','transit'),('午饭怎么解决','food'),('厕所、补水与休息','facilities'),('门票、开放与预约','ticket'),('家庭预算','budget'),('缩短路线、天气与撤退','retreat'),('给孩子的任务','game')]:
            s+=f'## {title}\n\n{p[key]}\n\n'
        if p['id']=='beigong':s+='![北宫山林历史实景](assets/beigong-view-20101107.jpg)\n\n照片：www.manun.cn，2010-11-07原始上传，CC BY 3.0；仅作历史景观参考，不是2026叶色情况。完整来源见[图片署名](assets/README.md)。\n\n'
        if p['id']=='tanzhe':s+='![潭柘寺门楼历史实景](assets/tanzhe-gate-20251109.jpg)\n\n照片：N509FZ，2025-11-09，CC BY-SA 4.0；历史实拍，不是本周实况，不把门口银杏当帝王树定位图。完整来源见[图片署名](assets/README.md)。\n\n'
        s+='## 资料、近期经验与未知项\n\n'+p['ugc']+'\n\n'+'\n'.join(f'- [{n}]({u})' for n,u in p['sources'])+'\n\n小红书仅采用作者公开经验，里程与停车费未经独立实测；原帖可能要求登录。未复制全文或把旧照片当今年现场。图片原帖可点来源查看，未取得转载许可的不打包进仓库。\n\n'
        if p['id']=='tanzhe':s+='**广慧寺能不能一起走？** 本轮补读两步路、Beijing Hikers及近期小红书后，仍不把整条环穿接在寺内游览后；[广慧寺专项](09-广慧寺短线研究.md)区分了短往返与7-8公里环线，并说明古树树龄争议。\n\n'
        if p['id']=='gudao':s+='**“京西古道”不是唯一一条线。** 冯村、万桑段、定都阁和水峪嘴不是同一起点。请另看[定都阁专项](10-定都阁与冯村短线研究.md)，不混用停车、里程和照片。\n\n'
        s+='[返回总览与评分](README.md) · [天气与队伍准备](出行准备与安全.md)\n'
        (BASE/p['file']).write_text(s)
    intro='# 北京赏红叶与银杏：亲子山林一日游 TOP 7\n\n> 2026-10-26整理；按10月31日至11月1日、8-9岁孩子组队、市区西部出发评估。以正规山林步道为主，不收城市公园，不凑十条。每一项是一整天独立方案，不是一天连赶七处。\n\n'
    intro+='**先做决定：**有车且重视彩林与轻登山的平衡，选北宫；各家地铁集合、首次组队选百望山；想看大片红叶而不追顶，选西山低位短线。千灵山适合石窟与山路结合。古道偏历史探索。红螺寺车程与台阶更多。潭柘寺保留为银杏专项，运动量较少。\n\n'
    intro+='## 总分排序\n\n| 排名 | 方案 | 秋色25 | 儿童25 | 交通15 | 舒适15 | 人流10 | 确定性10 | 总分 |\n|---|---|---:|---:|---:|---:|---:|---:|---:|\n'
    for i,p in enumerate(PLANS,1):
        intro+=f'| {i} | [{p["name"]}]({p["file"]}) | '+' | '.join(f'{s*w/5:.1f}' for s,(_,w) in zip(p['scores'],DIMS))+f' | **{p["total"]:.1f}** |\n'
    intro+='\n## 评分规则\n\n每项先评0-5分，可用0.5分刻度；换算得分=分项分÷5×权重，总分相加，保留一位小数。它是对“本次具体走法”的主观规划判断，不是可复现的景区质量测量。小于3分的分差不代表明显优劣；有无车、叶色与最弱孩子体力可以改变选择。\n\n'
    intro+='| 维度 | 权重 | 判断依据 |\n|---|---:|---|\n| 秋色 | 25 | 红叶/银杏特色、规模、目标日期预计状态 |\n| 儿童适配 | 25 | 步行、坡阶、安全、趣味、撤退；登山兴趣也纳入 |\n| 交通 | 15 | 市区西部往返、地铁接驳、停车与拥堵 |\n| 行程舒适 | 15 | 正餐、厕所、补给、休息和全天节奏 |\n| 人流体验 | 10 | 热点集中程度、排队和小队活动空间 |\n| 执行确定性 | 10 | 官方与近期实走、路线清楚程度、未知项 |\n\n5分表示很适合；4分适合且有少量限制；3分可用但有明显取舍；2分限制较大；1分不适合；0分无法形成可执行方案。开放、安全与合法进入是独立门槛，不能靠其他高分抵消。未经确认的路段不纳入确定推荐。\n\n'
    intro+='## 路线强度与选法\n\n| 方案 | 本次基本版 | 这次不做 |\n|---|---|---|\n'
    for p in PLANS:intro+=f'| {p["name"]} | {p["walk"]} | {p["extra"]} |\n'
    intro+='\n以上“控制公里数”是给队伍设的上限目标，不是实测。除有来源明确的官方长度/作者记录外，不编累计爬升；停车接近与地铁步行须另计。所有路线图是节点示意，不能用于山路导航。\n\n'
    intro+='## 定都阁、广慧寺与戒台寺怎么处理\n\n- [广慧寺短线研究](09-广慧寺短线研究.md)：补齐近期原帖和多渠道对照，保留短往返的条件方案，未核开放和轨迹前不进确定排名。\n- [定都阁与冯村短线研究](10-定都阁与冯村短线研究.md)：12公里/600米完整环线不作儿童默认线；取消AAA不等于闭园，但近期修缮反馈也不能忽略。\n- [戒台寺轻松备选](04-戒台寺慢游.md)：适合古树古建慢游，按本次登山偏好降权；不擅接寺外未知环穿。\n- 香山、八大处、坡峰岭：可赏秋，但热门节点人流与车程降低本次多孩队优先级；不是说不值得去。\n- 灵山、百花山高处：风寒、车程和强度不匹配这次低难度目标。\n\n'
    intro+='## 近期攻略如何改变方案\n\n本轮实际读取小红书原帖正文，分别写进各方案：西山市集不保证座位；北宫黄栌与其他树变色不同步；百望山东门主路与北门陡阶不是同线；千灵山停车接近路不能漏；古道近9公里铁轨环线不能冒充景区短线；红螺寺完整台阶线要裁剪；潭柘寺门口素餐需确认不辣；广慧寺7公里/500米不能只读“轻松”标签。\n\n去年资料与今年分开：2025官方秋季资料用于景观和历史窗口对照；只有实际读到的原帖才称已读。部分目的地未取得2025小红书完整原帖，已在单页披露，不宣称全部渠道全覆盖。未打电话、未订餐、未买票、不保证停车位。\n\n'
    intro+='## 分享文件\n\n- [精简长图](../../output/北京赏红叶与银杏_TOP7_长图_20261026.png)\n- [PDF一日游简版](../../output/pdf/北京赏红叶与银杏_TOP7_一日游_20261026.pdf)\n- [图片署名与许可](assets/README.md)\n- [天气、安全与队伍组织](出行准备与安全.md)\n\n出发前查北京气象台预警、山地风力、空气质量和园方封闭公告；有大风、雨雪或明显湿滑就取消爬山，不用一张提前数日的晴天预报兜底。每30-40分钟休息一次，按最弱孩子调节，14:00左右收队。\n'
    (BASE/'README.md').write_text(intro)

def escape(t):return html.escape(t).replace('\n','<br/>')
ST=ParagraphStyle('body',fontName='CN',fontSize=9,leading=14,textColor=HexColor(INK),wordWrap='CJK',spaceAfter=5)
def para(c,t,x,y,w,size=9,color=INK):
    st=ParagraphStyle('p',parent=ST,fontSize=size,leading=size*1.55,textColor=HexColor(color))
    p=Paragraph(t,st); _,h=p.wrap(w,10000);p.drawOn(c,x,y-h);return y-h-6
def text(c,t,x,y,size=10,color=INK):c.setFillColor(HexColor(color));c.setFont('CN',size);c.drawString(x,y,t)
def route_pdf(c,p,y):
    labels=p['nodes'];x0=34;gap=6;w=(595-68-4*gap)/5
    for i,t in enumerate(labels):
        x=x0+i*(w+gap);c.setFillColor(HexColor(INK));c.roundRect(x,y-43,w,40,6,fill=1,stroke=0)
        para(c,escape(t),x+7,y-7,w-14,9,'#FFFFFF')
        if i<4:text(c,'›',x+w+1,y-27,12,GOLD)
    text(c,'路线节点示意，不按比例、不表示方位，不作GPS导航。',34,y-57,7.5,ORANGE)
    return y-72
def footer(c,num):
    c.setStrokeColor(HexColor('#DCD9CD'));c.line(34,39,561,39)
    text(c,'去哪遛娃  /  8-9岁亲子山林一日游  /  2026.10.26',34,25,7)
    text(c,str(num),548,25,8)
def make_pdf():
    dest=OUT/'pdf/北京赏红叶与银杏_TOP7_一日游_20261026.pdf'
    c=canvas.Canvas(str(dest),pagesize=(595,842));c.setTitle('北京赏红叶与银杏：亲子山林一日游 TOP 7')
    c.setAuthor('去哪遛娃')
    c.setFillColor(HexColor(PAPER));c.rect(0,0,595,842,fill=1,stroke=0)
    text(c,'去哪遛娃  /  AUTUMN 2026',34,800,11,ORANGE)
    text(c,'北京赏红叶与银杏',34,759,29)
    text(c,'亲子山林一日游 · TOP 7',34,725,20)
    y=para(c,'10月31日至11月1日参考｜8-9岁小队｜户外登山优先<br/>每页一处、独立成行；不连赶景点，不以登顶为完成标准。',34,701,527,10)
    img=BASE/'assets/tanzhe-gate-20251109.jpg'
    c.drawImage(str(img),34,451,width=527,height=210,preserveAspectRatio=True,anchor='c',mask='auto')
    text(c,'潭柘寺门楼 · N509FZ · 2025-11-09 · CC BY-SA 4.0 · 历史实景，非本周叶色',34,439,7)
    c.linkURL('https://commons.wikimedia.org/wiki/File:Entrance_gatetower_of_Tanzhe_Temple_(20251109144630).jpg',(34,432,561,448))
    y=412
    for i,p in enumerate(PLANS,1):
        text(c,f'{i:02d}  {p["name"]}',34,y,12)
        text(c,f'{p["total"]:.1f}',509,y,13,ORANGE)
        para(c,escape(p['tag']),62,y-9,430,8.5)
        y-=39
    y=para(c,'评分：秋色25、儿童25、交通15、舒适15、人流10、确定性10。分项0-5分按权重换算；主观规划分，细小分差不代表明显优劣。开放、安全、合法进入独立验收。',34,y-2,527,8)
    y=para(c,'条件备选：广慧寺短往返待核轨迹和开放；定都阁近期有修缮反馈。冯村完整记录12公里/600米，广慧寺近期环线7公里/500米，不作本队默认线。详见GitHub单页。',34,y,527,8,ORANGE)
    if y<49:raise RuntimeError('封面超高')
    footer(c,1);c.showPage()
    for i,p in enumerate(PLANS,1):
        c.setFillColor(HexColor(PAPER));c.rect(0,0,595,842,fill=1,stroke=0)
        text(c,f'{i:02d}  {p["name"]}',34,801,22)
        text(c,f'{p["total"]:.1f}/100',452,802,15,ORANGE)
        text(c,p['tag'],34,776,11,ORANGE)
        score='  '.join(f'{n}{s*w/5:g}/{w}' for s,(n,w) in zip(p['scores'],DIMS))
        text(c,score,34,754,8.2)
        y=route_pdf(c,p,739)
        y=para(c,'<b>步行与强度</b>  '+escape(p['walk']),34,y,527,10)
        y=para(c,'<b>秋色与打卡</b>  '+escape('；'.join(p['spots'])+'。'+p['season']),34,y,527,10)
        top=y-5; cw=250; left=34; right=311
        yl=para(c,'<b>一日安排</b>',left,top,cw,11,ORANGE)
        for t,v in p['day']:yl=para(c,f'<b>{escape(t)}</b>  {escape(v)}',left,yl,cw,10)
        yl=para(c,'<b>儿童任务</b>  '+escape(p['game']),left,yl-3,cw,10)
        yl=para(c,'<b>缩短与撤退</b>  '+escape(p['retreat']),left,yl,cw,10,ORANGE)
        yr=top
        for title,key in [('自驾停车','drive'),('公共交通','transit'),('午饭','food'),('厕所补给','facilities'),('门票预约','ticket'),('预算','budget')]:
            yr=para(c,f'<b>{title}</b>  '+escape(p[key]),right,yr,cw,10)
        by=min(yl,yr)-4
        by=para(c,'<b>来源与范围</b> '+escape(p['ugc']),34,by,527,8.5)
        links=[]
        for k,(n,u) in enumerate(p['sources'],1):links.append(f'<a href="{html.escape(u,quote=True)}" color="#AF4829">[{k}] {escape(n)}</a>')
        by=para(c,' · '.join(links),34,by,527,8)
        if by<47:raise RuntimeError(f'{p["name"]}页面超高 {by}')
        footer(c,i+1);c.showPage()
    c.setFillColor(HexColor(PAPER));c.rect(0,0,595,842,fill=1,stroke=0)
    text(c,'补查：定都阁与广慧寺',34,797,23)
    y=para(c,'条件研究，不加入确定排名。两地有吸引力，但“亲子初级”“难度低”标签不能代替里程、爬升与合法开放核验。',34,768,527,10)
    for title,body in [
      ('广慧寺短往返 · 预评分62.0/100','当季旅游推荐肯定古银杏与万桑古道价值。近期小红书原帖记录的完整环线是7公里、爬升500米，包含短陡坡；评论说明照片拍于发布前一周，不能当当天叶色。2023官方旅游游记另一线约8公里/400米，也不能混为同一条。<br/><b>可研究路线：</b>潭柘寺镇桑峪村合法停车点 → 确认开放的正规步道 → 广慧寺 → 原路返。请熟路朋友先给近期同线轨迹、入口、爬升与撤退；不加定都阁、天坑，不从后山入潭柘寺。<br/><b>条件落实后：</b>08:00出发，09:30核路与厕所，10:00-12:30短走返回，12:30午饭，14:00返程。山上按无补给准备；林荫小院咖啡的主食、营业与座位未核，不作正餐保障。'),
      ('冯村—定都阁 · 预评分56.5/100','两步路2025亲子实走虽标初级，正文实际12公里、爬升600米、7小时，不作本队默认线。区文旅局2026-09-18取消AAA，理由为设施与服务未达标准；这不等于闭园令。近期游客仍报定都阁修缮暂不开放，不能预设能入阁。<br/><b>可研究路线：</b>核实开放的冯村正规栈道入口 → 开放观景段 → 原路返，不追阁、不接不老泉。未取得同线轨迹，不编短线公里数。<br/><b>条件落实后：</b>08:30出发，09:30停车核路，10:00-12:30短走返回，回门头沟城区正规餐馆午饭，14:00返程。提前确认儿童不辣主食、座位和厕所；备可直接吃的午饭。不绕锁门、不停无合法车位的路边。')]:
        y=para(c,'<b>'+title+'</b>',34,y-8,527,13,ORANGE)
        y=para(c,body,34,y,527,10)
    y=para(c,'预评分分项（0-5分，依次为秋色/儿童/交通/舒适/人流/确定性）：广慧寺4/3/3/2/4/2；冯村短返3.5/2.5/3.5/2/3.5/1.5。安全和合法进入是门槛，条件未满足，即使有总分也不能据此出发。',34,y-5,527,9)
    urls=[('门头沟取消AAA公告','https://www.bjmtg.gov.cn/bjmtg/zwxx/zwgg/202609/d530bf90933445d2b5fda12dcd6b40e8.shtml'),('两步路：冯村12公里实走','https://www.2bulu.com/community/gotohuatinfo.htm?id=UQ30N68rQSzVf3tcNf0S8A%3D%3D&type=1'),('小红书：万桑段近期实走','https://www.xiaohongshu.com/explore/6adb6887000000002a0124a1'),('Beijing Hikers 2026实走','https://www.beijinghikers.com/photos-and-news/through-the-hills-to-dingdu-pavilion-and-tanzhe-temple-2026-03-07/'),('GitHub完整攻略与逐项评分','https://github.com/fanko24/quna-liuwa')]
    y=para(c,' · '.join(f'<a href="{html.escape(u,quote=True)}" color="#AF4829">{escape(n)}</a>' for n,u in urls),34,y,527,9)
    if y<47:raise RuntimeError('补查页超高')
    footer(c,9);c.showPage();c.save()
    return dest

def make_poster():
    W=1200;H=3660
    im=Image.new('RGB',(W,H),PAPER); d=ImageDraw.Draw(im)
    fonts={s:ImageFont.truetype(FONT,s) for s in [20,22,24,26,28,30,34,40,48,62]}
    def txt(t,x,y,size=26,color=INK):d.text((x,y),t,font=fonts[size],fill=color)
    def wrap(t,x,y,width,size=26,color=INK):
        line=''
        for ch in t:
            if ch=='\n' or d.textlength(line+ch,font=fonts[size])>width:
                txt(line,x,y,size,color);y+=int(size*1.5);line='' if ch=='\n' else ch
            else:line+=ch
        if line:txt(line,x,y,size,color);y+=int(size*1.5)
        return y
    txt('去哪遛娃  /  AUTUMN 2026',54,35,24,ORANGE)
    txt('北京赏红叶与银杏',54,79,62)
    txt('亲子山林一日游 TOP 7',54,165,40)
    txt('8-9岁小队  ·  10/31-11/01参考  ·  每处独立玩一天',54,232,24)
    photo=Image.open(BASE/'assets/tanzhe-gate-20251109.jpg').convert('RGB')
    photo.thumbnail((1092,325));im.paste(photo,((W-photo.width)//2,282))
    txt('潭柘寺历史实拍 / N509FZ / 2025-11-09 / CC BY-SA 4.0 / 非今年叶色',54,614,20)
    y=664
    short={
      'beigong':('3-4km控制目标｜有车优选','南门 → 小江南 → 正规彩林步道 → 原路返','09:00进园；12:00午饭；14:00返程。狼坡顶选做。','自带主食兜底；南门停车接近路另计。'),
      'baiwang':('3-4km控制目标｜地铁优选','东门 → 一号主路 → 观京台 → 原路返','09:00马连洼集合；半山折返；东门午饭。','地铁往返另走约1.4-2km；不抄北门陡阶捷径。'),
      'xishan':('3-4km控制目标｜赏红优选','东门 → 花溪水景 → 峡谷方向短走 → 折返','09:00进园；11:30回低位午饭；14:00离园。','不登鬼笑石；近期市集缺座位，自带午饭更稳。'),
      'qianling':('官方约3.7km｜孩子留3-3.5h','南门 → 七星沟 → 开放洞窟区 → 仙人谷 → 南门','09:10到园；10:30加餐；13:00南门午饭。','停车接近路另计；不接极乐峰与悬崖栈道。'),
      'gudao':('景区参考2.1km｜历史探秘','水峪嘴入口 → 马蹄窝 → 关城方向 → 原路返','上午正规古道；下山午饭；下午故居或村内慢走。','石板雨后滑；不走铁轨、隧道及成人近9km环线。'),
      'hongluo':('3-4km控制目标｜台阶较多','御竹林 → 古银杏 → 正规山路短走 → 折返','07:30出发；上午赏树与短上坡；14:00返城。','怀柔车程更长；不追中天门，带好午饭与温水。'),
      'tanzhe':('2-3km控制目标｜银杏专项','山门 → 古银杏 → 开放上层院落 → 原路返','09:30入寺；12:00素面或自带饭；14:00返程。','10/25官方仅称开始黄；不接后山环穿，运动量少。')}
    for i,p in enumerate(PLANS,1):
        d.rounded_rectangle((38,y,1162,y+330),radius=20,fill='#FFFFFF',outline='#E2DFD2',width=2)
        txt(f'{i:02d}',60,y+16,48,ORANGE);txt(p['name'],150,y+24,34)
        txt(f'{p["total"]:.1f}分',980,y+25,34,ORANGE)
        a,b,c,e=short[p['id']]
        yy=wrap(a,150,y+80,940,26,ORANGE)
        yy=wrap('路线｜'+b,65,yy+7,1060,26)
        yy=wrap('一天｜'+c,65,yy+4,1060,24)
        yy=wrap('注意｜'+e,65,yy+5,1060,24)
        vals=' · '.join(f'{n}{s*w/5:g}' for s,(n,w) in zip(p['scores'],DIMS))
        txt(vals,65,y+287,20,'#657269')
        if yy>y+283:raise RuntimeError('长图卡片溢出 '+p['id'])
        y+=349
    y=wrap('评分权重｜秋色25 + 儿童25 + 交通15 + 舒适15 + 人流10 + 确定性10。按具体短线评分，0-5分换算；不是景区评级。',54,y+4,1092,22)
    y=wrap('定都阁 / 广慧寺：另附专项研究，近期有修缮、陡坡及7-12km环线记录。先核开放和短线轨迹，不因“亲子初级”就跟走。',54,y+9,1092,22,ORANGE)
    y=wrap('先查预警与封山｜每30-40分钟休息｜按最弱孩子调整｜不走野路、不点火、不食银杏果。路线为节点示意，不是GPS轨迹；票价、座位与停车临期确认。',54,y+9,1092,22)
    txt('2026.10.26整理 · 详细交通/午饭/来源/备选见PDF与GitHub',54,y+12,22)
    if y>H-55:raise RuntimeError('长图底部溢出')
    im=im.crop((0,0,W,min(H,y+80)))
    dest=OUT/'北京赏红叶与银杏_TOP7_长图_20261026.png';im.save(dest)
    return dest

if __name__=='__main__':
    make_md()
    p=make_pdf();img=make_poster()
    print(json.dumps({'ranking':[(p['name'],p['total']) for p in PLANS],'pdf':str(p),'poster':str(img)},ensure_ascii=False,indent=2))
