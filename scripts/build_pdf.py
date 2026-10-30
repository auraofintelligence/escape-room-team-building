"""Build a PDF edition from the canonical manuscript when a Word renderer is unavailable.

Uses ReportLab with embedded fonts, linked source IDs and complete source entries.
The Word and PDF editions share content; pagination is independent.
"""
from pathlib import Path
import hashlib
import json
import re
from html import escape
from urllib.parse import quote
from source_metadata import source_date
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak, CondPageBreak, KeepTogether, Image
from reportlab.platypus.tableofcontents import TableOfContents

ROOT=Path(__file__).resolve().parents[1]
BASE='https://auraofintelligence.github.io/escape-room-team-building/'
W,H=A4
MARGIN=44
WIDTH=W-2*MARGIN
NAVY=colors.HexColor('#203b4c')
SAGE=colors.HexColor('#edf2ee')
GRAY=colors.HexColor('#526568')
FONTDIR=Path('C:/Windows/Fonts')
for face,file in [('Plan','arial.ttf'),('Plan-Bold','arialbd.ttf'),('Plan-Italic','ariali.ttf'),('Plan-BoldItalic','arialbi.ttf')]:
    pdfmetrics.registerFont(TTFont(face,str(FONTDIR/file)))
pdfmetrics.registerFontFamily('Plan',normal='Plan',bold='Plan-Bold',italic='Plan-Italic',boldItalic='Plan-BoldItalic')
styles=getSampleStyleSheet()
for name in ['BodyText','Normal']:
    styles[name].fontName='Plan'
    styles[name].fontSize=10.5
    styles[name].leading=14.3
    styles[name].spaceAfter=7
for name,size in [('Title',22),('Heading1',21),('Heading2',14),('Heading3',11.8)]:
    styles[name].fontName='Plan-Bold'
    styles[name].fontSize=size
    styles[name].leading=size*1.18
    styles[name].textColor=colors.black
    styles[name].spaceAfter=9
    styles[name].spaceBefore=12 if name!='Title' else 0
    styles[name].keepWithNext=True
styles.add(ParagraphStyle('Lead',parent=styles['BodyText'],fontSize=13.4,leading=18,spaceAfter=12))
styles.add(ParagraphStyle('SourceNote',parent=styles['BodyText'],fontSize=8.6,leading=11.5,textColor=GRAY,spaceAfter=7))
styles.add(ParagraphStyle('Basis',parent=styles['SourceNote'],keepWithNext=True))
styles.add(ParagraphStyle('Cell',parent=styles['BodyText'],fontSize=8.7,leading=11.1,spaceAfter=0,splitLongWords=True))
styles.add(ParagraphStyle('CellHead',parent=styles['Cell'],fontName='Plan-Bold',textColor=colors.white))
styles.add(ParagraphStyle('SourceTitle',parent=styles['Heading3'],spaceBefore=11,spaceAfter=5))
styles.add(ParagraphStyle('Register',parent=styles['BodyText'],fontSize=9.1,leading=12,spaceAfter=5))
styles.add(ParagraphStyle('ContentsEntry',fontName='Plan',fontSize=11,leading=17,leftIndent=0,firstLineIndent=0,spaceBefore=6,textColor=colors.black))

plan=json.loads((ROOT/'content/plan.json').read_text(encoding='utf-8'))
sources=json.loads((ROOT/'content/sources.json').read_text(encoding='utf-8'))
refs={e['id']:e for key in ('documents','links','research') for e in sources.get(key,[])}

def rich(text):
    held=[]
    def hold(value):
        held.append(value)
        return '@@LINK'+str(len(held)-1)+'@@'
    def link(m):
        url=m[2]
        if not url.startswith(('http:','https:','#')):url=BASE+url
        return hold('<a color="#275e67" href="'+escape(url,quote=True)+'">'+escape(m[1])+'</a>')
    text=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',link,str(text))
    text=escape(text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<i>\1</i>',text)
    text=re.sub(r'`([^`]+)`',r'\1',text)
    text=re.sub(r'\b([DPMR]\d{2,3})\b',lambda m:hold('<a color="#275e67" href="#source_'+m[1]+'">'+m[1]+'</a>') if m[1] in refs else m[1],text)
    for i,item in enumerate(held):text=text.replace('@@LINK'+str(i)+'@@',item)
    return text

def table(headers,rows):
    # Match the established portable edition's deliberate column proportions.
    from build_documents import widths_for
    inches,_=widths_for(headers,rows)
    widths=[x/sum(inches)*WIDTH for x in inches]
    data=[[Paragraph(rich(v),styles['CellHead' if r==0 else 'Cell']) for v in row] for r,row in enumerate([headers]+rows)]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#cbd8d2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,SAGE])]))
    return [Spacer(1,5),t,Spacer(1,10)]

def markdown(text,style='BodyText'):
    lines=str(text).strip().splitlines()
    out=[]
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if '|' in line and i+1<len(lines) and re.fullmatch(r'[\s|:\-]+',lines[i+1]):
            cells=lambda s:[v.strip() for v in s.strip().strip('|').split('|')]
            headers=cells(line);rows=[];i+=2
            while i<len(lines) and '|' in lines[i] and lines[i].strip():
                rows.append(cells(lines[i]));i+=1
            out.extend(table(headers,rows));continue
        if line.startswith('### '):out.append(Paragraph(rich(line[4:]),styles['Heading3']));i+=1;continue
        if line.startswith('## '):out.append(Paragraph(rich(line[3:]),styles['Heading2']));i+=1;continue
        if line.startswith('# '):i+=1;continue
        if re.match(r'^[-*] ',line):
            out.append(Paragraph(rich(line[2:]),styles[style],bulletText='•'));i+=1;continue
        chunk=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('### ','## ','- ','* ')):
            if '|' in lines[i] and i+1<len(lines) and re.fullmatch(r'[\s|:\-]+',lines[i+1]):break
            chunk.append(lines[i].strip());i+=1
        out.append(Paragraph(rich(' '.join(chunk)),styles[style]))
    return out

class PlanDoc(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,topMargin=40,bottomMargin=40,title=plan['title']+' ROUND ONE',author=plan['author'])
        self.addPageTemplates(PageTemplate(id='main',frames=[Frame(MARGIN,40,WIDTH,H-80,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.footer))
    def footer(self,canvas,doc):
        canvas.setFont('Plan',8)
        canvas.setFillColor(GRAY)
        canvas.drawString(MARGIN,23,'ROUND ONE  |  Escape Room Team Building  |  Luke Nathan Hayes')
        canvas.drawRightString(W-MARGIN,23,str(doc.page))
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and hasattr(f,'bookmark_key'):
            self.canv.bookmarkHorizontalAbsolute(f.bookmark_key,self.frame._y+f.height+f.getSpaceAfter())
            self.canv.addOutlineEntry(f.getPlainText(),f.bookmark_key,0,False)
            self.notify('TOCEntry',(0,f.getPlainText(),self.page,f.bookmark_key))

def heading(text,key):
    p=Paragraph(escape(text),styles['Heading1']);p.bookmark_key=key;return p

story=[]
story.append(Paragraph(escape(plan['title']),styles['Title']))
story.append(Paragraph(escape(plan['subtitle']),styles['BodyText']))
story.append(Paragraph(escape(plan['author']+' | '+plan['date']+' | '+plan['edition']),styles['SourceNote']))
for idx,c in enumerate(plan['chapters']):
    if idx:
        if idx==1:
            story.append(PageBreak());story.append(Paragraph('Contents',styles['Heading1']))
            toc=TableOfContents();toc.levelStyles=[styles['ContentsEntry']];story.append(toc)
        story.append(CondPageBreak(180) if c['slug'] in {'renewal','partnerships','roadmap'} else PageBreak())
    story.append(heading('EXECUTIVE SUMMARY' if idx==0 else c['title'],'chapter_'+re.sub(r'\W','_',c['slug'])))
    story.append(Paragraph(rich(c['lead']),styles['Lead']))
    for s in c['sections']:
        opening=[Paragraph(escape(s['title']),styles['Heading2'])]
        if s.get('basis'):opening.append(Paragraph(escape(s['basis']),styles['Basis']))
        flows=markdown(s['body'])
        first=0
        while first<len(flows):
            opening.append(flows[first]);first+=1
            if isinstance(flows[first-1],(Paragraph,Table)):break
        story.append(KeepTogether(opening))
        story.extend(flows[first:])
        if s.get('refs'):story.append(Paragraph('Sources: '+rich(', '.join(s['refs'])),styles['SourceNote']))
        if s.get('calculator'):
            sid=s.get('id') or re.sub(r'[^a-z0-9]+','-',s['title'].lower()).strip('-')
            story.append(Paragraph(rich('[Change inputs in the online calculator]('+BASE+c['slug']+'.html#'+sid+')'),styles['SourceNote']))
    if idx==0:
        image=ROOT/'assets/heroes/index.webp'
        if image.exists():
            from PIL import Image as PILImage
            w,h=PILImage.open(image).size
            art=Image(str(image),width=310,height=310*h/w)
            story.append(KeepTogether([art,Spacer(1,5),Paragraph('Original AI-generated concept artwork. An illustration, not a selected premises.',styles['SourceNote'])]))
story.append(PageBreak());story.append(heading('Sources and project inventory','source_register'))
story.append(Paragraph('Dates record source checks. Prices are advertised observations; no supplier quotations were requested. Original documents and full notes are linked.',styles['BodyText']))
for group,label in [('documents','Original documents'),('links','Connected projects and websites'),('research','Market and cost sources')]:
    story.append(CondPageBreak(95))
    story.append(Paragraph(label,styles['Heading2']))
    for e in sources.get(group,[]):
        start=len(story)
        story.append(Paragraph('<a name="source_'+e['id']+'"/>'+escape(e['id']+' '+e['title']),styles['SourceTitle']))
        if group=='research' and e.get('verification_note')!='Unverified inherited reference.':story.extend(markdown(e.get('verification_note',''),'Register'))
        if e.get('checked'):story.append(Paragraph(source_date(e),styles['SourceNote']))
        url=(BASE+quote(e['path'],safe='/')) if group=='documents' and e.get('path') and (ROOT/e['path']).is_file() else e.get('url') or BASE+'sources.html#'+e['id']
        story.append(Paragraph('<a color="#275e67" href="'+escape(url,quote=True)+'">Open source</a>',styles['SourceNote']))
        for link in e.get('product_links',[]):story.append(Paragraph(rich('['+link['item']+']('+link['url']+')'),styles['SourceNote']))
        story[start:]=[KeepTogether(story[start:])]
for file,title,key in [('RIGHTS.md','Rights and provenance','rights'),('LICENCE.md','Strange But True Public Source Licence','licence')]:
    story.append(PageBreak());story.append(heading(title,key));story.extend(markdown((ROOT/file).read_text(encoding='utf-8')))
output=ROOT/'downloads/Escape-Room-Network-Business-Plan.pdf'
PlanDoc(output).multiBuild(story)
report={'method':'ReportLab from canonical manuscript; independent pagination from Word','canonical_plan_sha256':hashlib.sha256((ROOT/'content/plan.json').read_bytes()).hexdigest(),'source_register_sha256':hashlib.sha256((ROOT/'content/sources.json').read_bytes()).hexdigest(),'pdf':str(output.relative_to(ROOT))}
(ROOT/'content/pdf-build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Built PDF with canonical chapters, complete source register, links and contents')
