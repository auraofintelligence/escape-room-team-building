"""Build the static business-plan site from content/plan.json."""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import quote, urlsplit, unquote
import argparse, hashlib, json, re, zipfile
from calculator_markup import calculator_markup
from source_metadata import source_date

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://auraofintelligence.github.io/escape-room-team-building/'
REPO = 'https://github.com/auraofintelligence/escape-room-team-building'
UTILITIES = [('sources', 'Sources and projects'), ('downloads', 'Downloads'), ('licence', 'Licence'), ('sitemap', 'All pages'), ('presentation', 'Presentation')]
PLAN = json.loads((ROOT/'content/plan.json').read_text(encoding="utf-8"))
CHAPTERS = PLAN['chapters']
SOURCES = json.loads((ROOT/'content/sources.json').read_text(encoding="utf-8"))
DOCS = SOURCES.get('documents', [])
PROJECTS = SOURCES.get('links', [])
RESEARCH = SOURCES.get('research', [])
REFS = {x['id']: x for x in DOCS+PROJECTS+RESEARCH}
ART = {x['slug']: x for x in json.loads((ROOT/'content/artwork.json').read_text(encoding="utf-8"))} if (ROOT/'content/artwork.json').exists() else {}
NAV = [(x['slug'], x.get('nav_title', x['title'])) for x in CHAPTERS] + UTILITIES
TITLE = PLAN.get('title', 'Escape Room Team Building')
DATE = PLAN.get('date', '29 October 2026')
EDITION = PLAN.get('edition', 'Business plan 1.0')
FINANCE = json.loads((ROOT/'content/finance.json').read_text(encoding='utf-8'))

def write(path, text):
    p = ROOT/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def anchor(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def inline(text):
    s = escape(str(text))
    held = []
    def link(m):
        label, url = m.group(1), unescape(m.group(2))
        if not (url.startswith(('https://', 'http://', '#')) or not urlsplit(url).scheme):
            return label
        attr = ' target="_blank" rel="noopener noreferrer"' if url.startswith(('https://', 'http://')) else ''
        held.append(f'<a href="{escape(url, quote=True)}"{attr}>{label}</a>')
        return f'@@LINK{len(held)-1}@@'
    s = re.sub(r'\[([^\]]+)\]\(([^\s]+)\)', link, s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\b([DPMR]\d{2,3})\b', lambda m: f'<a href="sources.html#{m[1]}" class="ref" title="{escape(REFS[m[1]].get("title",m[1]),quote=True)}">{m[1]}</a>' if m[1] in REFS else m[1], s)
    for i, item in enumerate(held):
        s = s.replace(f'@@LINK{i}@@', item)
    return s

def markdown(text):
    lines = str(text).strip().splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if '|' in line and i+1 < len(lines) and re.fullmatch(r'[\s|:\-]+', lines[i+1]) and '-' in lines[i+1]:
            cells = lambda x: [c.strip() for c in x.strip().strip('|').split('|')]
            headers = cells(line)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip() and '|' in lines[i]:
                row = cells(lines[i])
                row += [''] * (len(headers)-len(row))
                rows.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>')
                i += 1
            out.append('<div class="table-scroll" tabindex="0" role="region" aria-label="Data table"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>')
            continue
        if re.match(r'^[-*] ', line) or re.match(r'^\d+[.)] ', line):
            ordered = bool(re.match(r'^\d+[.)] ', line))
            tag = 'ol' if ordered else 'ul'
            items = []
            pattern = r'^\d+[.)] ' if ordered else r'^[-*] '
            while i < len(lines) and re.match(pattern, lines[i].strip()):
                item = re.sub(pattern, '', lines[i].strip())
                i += 1
                while i < len(lines) and lines[i].startswith('  ') and not re.match(r'^\s*[-*] |^\s*\d+[.)] ', lines[i]):
                    item += ' ' + lines[i].strip()
                    i += 1
                items.append('<li>'+inline(item)+'</li>')
            out.append('<'+tag+'>'+''.join(items)+'</'+tag+'>')
            continue
        if line.startswith('> '):
            out.append('<blockquote><p>'+inline(line[2:])+'</p></blockquote>')
            i += 1
            continue
        if line.startswith('### '):
            out.append('<h3>'+inline(line[4:])+'</h3>')
            i += 1
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^\s*(?:[-*] |\d+[.)] |### |> )', lines[i]):
            if '|' in lines[i] and i+1 < len(lines) and re.fullmatch(r'[\s|:\-]+', lines[i+1]):
                break
            para.append(lines[i].strip())
            i += 1
        out.append('<p>'+inline(' '.join(para))+'</p>')
    return ''.join(out)

def reference_chips(ids):
    ids = list(dict.fromkeys(ids))
    return '<div class="source-chips">'+''.join(f'<a class="chip" href="sources.html#{x}">{escape(x)} · {escape(REFS[x].get("title",x))}</a>' for x in ids if x in REFS)+'</div>' if ids else ''

def hero(slug):
    a = ART.get(slug)
    if not a or not a.get('path') or not (ROOT/a['path']).exists():
        return ''
    from PIL import Image
    w,h = Image.open(ROOT/a['path']).size
    return f'<figure class="hero"><img src="{escape(a["path"],quote=True)}" alt="{escape(a.get("alt","Generated concept artwork"),quote=True)}" width="{w}" height="{h}" fetchpriority="high"><figcaption>{escape(a.get("caption","Original AI-generated concept artwork for this business plan."))}</figcaption></figure>'

def shell(slug, title, lead, body, *, art=True, section='Business plan', canonical=None, base_tag=False):
    names = [x[0] for x in NAV]
    pos = names.index(slug) if slug in names else 0
    prev, nxt = NAV[(pos-1)%len(NAV)], NAV[(pos+1)%len(NAV)]
    if base_tag:
        prev, nxt = ('sources', 'Sources and projects'), ('index', 'Executive summary')
    nav = ''.join(f'<a href="{u}.html"'+(' aria-current="page"' if u==slug else '')+f'>{escape(n)}</a>' for u,n in NAV)
    actions = '<div class="actions"><a class="button" href="downloads/Escape-Room-Network-Business-Plan.pdf">Read the full PDF</a><a class="button secondary" href="downloads/Escape-Room-Network-Business-Plan.docx">Editable Word plan</a><a class="button secondary" href="presentation.html">Presentation view</a></div>' if slug=='index' else ''
    url = canonical or BASE+('' if slug=='index' else slug+'.html')
    base = '<base href="../../">' if base_tag else ''
    skip_href = 'documents/readers/'+slug+'.html#main' if base_tag else '#main'
    return f'''<!doctype html><html lang="en-AU"><head>{base}<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | {escape(TITLE)}</title><meta name="description" content="{escape(lead,quote=True)}"><meta name="theme-color" content="#203b4c"><link rel="canonical" href="{escape(url,quote=True)}"><meta property="og:type" content="website"><meta property="og:title" content="{escape(title,quote=True)}"><meta property="og:description" content="{escape(lead,quote=True)}"><meta property="og:url" content="{escape(url,quote=True)}"><link rel="icon" href="assets/favicon.ico?v=round-one" sizes="any"><link rel="icon" href="assets/favicon-32.png?v=round-one" type="image/png" sizes="32x32"><link rel="icon" href="assets/favicon-16.png?v=round-one" type="image/png" sizes="16x16"><link rel="apple-touch-icon" href="assets/apple-touch-icon.png"><link rel="stylesheet" href="assets/site.css"><link rel="stylesheet" href="assets/refinements.css"><script defer src="assets/site.js"></script><link rel="describedby" href="llms.txt"></head><body id="top"><a class="skip" href="{skip_href}">Skip to content</a><header class="header"><div class="wrap header-inner"><a class="brand" href="index.html"><img class="brand-mark" src="assets/favicon-192.png" width="48" height="48" alt=""><span>Escape Room<br>Team Building</span></a><nav class="main-nav" aria-label="Main navigation"><a href="index.html">The business</a><a href="network-tourism.html">The network</a><a href="sources.html">Sources</a><button class="menu-button" data-menu aria-expanded="false" aria-controls="all-nav">All chapters</button></nav></div><nav class="all-nav" id="all-nav" aria-label="All chapters" hidden><div class="wrap nav-grid">{nav}</div></nav></header><main id="main"><div class="wrap intro"><p class="eyebrow">ROUND ONE · {escape(section)}</p><h1>{escape(title)}</h1><p class="lead">{escape(lead)}</p>{actions}</div>{hero(slug) if art else ''}{body}</main><footer class="footer"><div class="wrap route-nav"><a href="{prev[0]}.html">Previous<strong>← {escape(prev[1])}</strong></a><a href="{nxt[0]}.html">Next<strong>{escape(nxt[1])} →</strong></a></div><div class="wrap footer-base"><p>© 2026 Luke Nathan Hayes · Strange But True Public Source Licence.<br>{escape(EDITION)} · {escape(DATE)}</p><div class="footer-links"><a href="sitemap.html">All pages</a><a href="downloads.html">PDF &amp; Word</a><a href="licence.html">Licence</a><a href="{REPO}" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div></div></footer><button class="top" data-top aria-label="Return to top">↑</button></body></html>'''

def build_chapters():
    for i,c in enumerate(CHAPTERS):
        used = set()
        blocks, anchors = [], []
        for s in c['sections']:
            sid = s.get('id') or anchor(s['title'])
            if sid in used:
                raise ValueError(f'Duplicate section anchor {c["slug"]}#{sid}')
            used.add(sid)
            anchors.append((sid,s['title']))
            basis = '<p class="scenario-basis">'+escape(s['basis'])+'</p>' if s.get('basis') else ''
            calc = calculator_markup(s['calculator'], FINANCE) if s.get('calculator') else ''
            blocks.append(f'<section id="{sid}"><h2>{escape(s["title"])}</h2>{basis}{markdown(s["body"])}{reference_chips(s.get("refs",[]))}{calc}</section>')
        metrics = c.get('metrics', [])
        metric = '<div class="metrics">'+''.join(f'<div class="metric"><strong>{escape(str(m["value"]))}</strong><span>{escape(m["label"])}</span></div>' for m in metrics)+'</div>' if metrics else ''
        aside = '<aside class="aside"><h2>On this page</h2>'+''.join(f'<a href="#{a}">{escape(t)}</a>' for a,t in anchors)+'</aside>'
        body = '<div class="wrap">'+metric+'<div class="content-layout"><article class="reading">'+''.join(blocks)+reference_chips(c.get('refs',[]))+'</article>'+aside+'</div></div>'
        if any(s.get('calculator') for s in c['sections']):
            data=json.dumps({'benchmarks':FINANCE['benchmarks'],'verified_rates':FINANCE['verified_rates']},ensure_ascii=False).replace('<','\\u003c')
            body += '<script type="application/json" id="calculator-data">'+data+'</script><script defer src="assets/calculator-engine.js"></script><script defer src="assets/calculators.js"></script>'
        page=shell(c['slug'],c['title'],c['lead'],body,section=f'{i+1:02} · '+c.get('nav_title',c['title']))
        if any(s.get('calculator') for s in c['sections']):page=page.replace('</head>','<link rel="stylesheet" href="assets/calculators.css"></head>')
        write(c['slug']+'.html',page)
    manuscript = '# '+TITLE+'\n\n'+PLAN.get('subtitle','')+'\n\n'+PLAN.get('author','Luke Nathan Hayes')+' | '+DATE+' | '+EDITION+'\n\n'
    for c in CHAPTERS:
        manuscript += '## '+c['title']+'\n\n'+c['lead']+'\n\n'
        for s in c['sections']:
            manuscript += '### '+s['title']+'\n\n'+(s['basis']+'\n\n' if s.get('basis') else '')+s['body'].strip()+'\n\n'
            if s.get('refs'): manuscript += 'Sources: '+', '.join(s['refs'])+'\n\n'
        if c.get('refs'): manuscript += 'Chapter sources: '+', '.join(c['refs'])+'\n\n'
    manuscript += '## Source register\n\nAdvertised observations, not requested quotations. Full source notes are linked.\n\n'
    for ref in DOCS+PROJECTS+RESEARCH:
        url = ref.get('url') or ref.get('source_url') or BASE+'sources.html#'+ref['id']
        manuscript += ref['id']+' ['+ref['title']+']('+url+')\n\n'
        if ref.get('verification_note'):manuscript += ref['verification_note']+'\n\n'
        if source_date(ref):manuscript += source_date(ref)+'.\n\n'
    write('content/plan.md',manuscript)

def build_sources():
    cards=[]
    for d in DOCS:
        exists=(ROOT/d.get('path','')).is_file()
        reader=(ROOT/'documents/readers'/f'{d["id"]}.html').is_file()
        actions = f'<div class="actions"><a class="button secondary" href="{quote(d["path"],safe="/")}">Original {Path(d["path"]).suffix[1:].upper()}</a>'+ (f'<a href="documents/readers/{d["id"]}.html">Read online</a>' if reader else '')+'</div>' if exists else '<p>The reference register identifies this document. The exact original is unavailable in the inherited archive.</p>'
        note = d.get('application', d.get('note',''))
        cards.append(f'<article class="card" id="{d["id"]}" data-search="{escape(d["id"]+" "+d["title"]+" "+note,quote=True)}"><p class="tag">{d["id"]} · Original document</p><h3>{escape(d["title"])}</h3><p>{inline(note)}</p>{actions}<details><summary>Original-file verification</summary><p class="hash">SHA-256<br>{d.get("sha256") or "Exact file not available"}</p></details></article>')
    for kind,items in [('Connected project',PROJECTS),('Market and operating source',RESEARCH)]:
        for x in items:
            purpose = x.get('application',x.get('purpose',x.get('note','')))
            checked = '<p class="metadata">'+escape(source_date(x))+'</p>' if source_date(x) else ''
            if x.get('verification_note') and x['verification_note'] != purpose:
                checked += '<p class="metadata">'+escape(x['verification_note'])+'</p>'
            if x.get('product_links'):
                checked += '<p>'+ ' · '.join('<a href="'+escape(link['url'],quote=True)+'" target="_blank" rel="noopener noreferrer">'+escape(link['item'])+'</a>' for link in x['product_links'])+'</p>'
            cards.append(f'<article class="card" id="{x["id"]}" data-search="{escape(x["id"]+" "+x["title"]+" "+purpose,quote=True)}"><p class="tag">{x["id"]} · {kind}</p><h3><a href="{escape(x["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(x["title"])} ↗</a></h3><p>{inline(purpose)}</p>{checked}</article>')
    controls=f'<div class="filter"><label class="sr-only" for="source-search">Search sources and projects</label><input id="source-search" data-filter type="search" placeholder="Find a source, project or topic"></div><p data-count aria-live="polite">{len(cards)} entries</p><p data-empty class="empty" hidden>No matches. Try a broader term.</p>'
    intro='<p>Market and cost evidence alongside the original <a href="https://auraofintelligence.github.io/installing-the-missing-middle/" target="_blank" rel="noopener noreferrer">Installing the Missing Middle</a> collection. Dates are source checks. Prices are advertised observations; no supplier quotations were requested. Unverified entries are identified. Original documents retain their wording and rights.</p>'
    body='<section class="wrap wide-section">'+intro+controls+'<div class="card-grid">'+''.join(cards)+'</div><div class="notice"><p><a href="content/embedded-links.json">Embedded links from the source documents</a> preserve the wider reference trail. <a href="content/sources.json">Download the source register</a>.</p></div></section>'
    write('sources.html',shell('sources','Sources and project connections','The market research, original documents and connected projects behind the business plan.',body,section='Reference library'))

def build_utilities():
    body='''<section class="wrap wide-section"><div class="card-grid"><article class="card"><h2>The complete business plan</h2><p>Matching ROUND ONE research editions covering the opportunity, market evidence, design, tourism, costs, learning, paid work and renewal.</p><div class="actions"><a class="button" href="downloads/Escape-Room-Network-Business-Plan.pdf">PDF plan</a><a class="button secondary" href="downloads/Escape-Room-Network-Business-Plan.docx">Editable Word plan</a></div></article><article class="card"><h2>Manuscript and model inputs</h2><p><a href="content/plan.md">Markdown manuscript</a> · <a href="content/plan.json">Structured manuscript</a> · <a href="content/finance.json">Financial inputs and calculations</a></p><p><a href="presentation.html">Open the chapter presentation</a> for a concise view of the whole plan.</p></article><article class="card"><h2>Original source collection</h2><p>Unchanged source documents, the source register and embedded links from Installing the Missing Middle, with additions for this business.</p><div class="actions"><a class="button secondary" href="downloads/Escape-Room-Network-Source-Pack.zip">Download source pack</a><a href="sources.html">Browse the source library</a></div></article><article class="card"><h2>Research and founder decisions</h2><p>Research and computation support a review of the alternatives. Commercial and operating choices remain open.</p><p><a href="agent-roles.html">Research and paid work</a> · <a href="briefs/approval-register.md">Research decision register</a> · <a href="AGENTS.md">Authoring instructions</a></p></article></div></section>'''
    write('downloads.html',shell('downloads','Read and develop the full plan','PDF, editable Word, the manuscript, model inputs and original source collection.',body,section='Downloads'))
    licence=(ROOT/'LICENCE.md').read_text(encoding="utf-8")
    blocks=[]
    for b in licence.split('\n\n'):
        if b.startswith('# '):continue
        if b.startswith('## '):blocks.append('<section><h2>'+escape(b[3:])+'</h2></section>')
        else:blocks.append(markdown(b))
    body='<div class="wrap content-layout"><article class="reading">'+''.join(blocks)+'<p><a href="LICENCE.md">Licence file</a> · <a href="RIGHTS.md">Rights and provenance</a></p></article></div>'
    write('licence.html',shell('licence','Strange But True Public Source Licence','The established public-source terms, with commercial rights held by Luke Nathan Hayes.',body,section='Rights and attribution'))
    toc='<ol class="toc-list">'+''.join(f'<li><a href="{s}.html"><strong>{escape(t)}</strong>{escape(next((c["lead"] for c in CHAPTERS if c["slug"]==s),""))}</a></li>' for s,t in NAV)+'</ol>'
    write('sitemap.html',shell('sitemap','Explore the complete business plan','Every chapter, the full source collection and downloadable editions.','<section class="wrap wide-section">'+toc+'</section>',section='All pages'))
    controls='<div class="presentation-controls"><button data-present>Start presentation</button><button data-prev aria-label="Previous slide">← Previous</button><span data-slide-count aria-live="polite"></span><button data-next aria-label="Next slide">Next →</button></div><p>Use the arrow keys in presentation mode. Escape returns to the outline.</p>'
    slides=''.join(f'<section class="presentation-card" id="slide-{i+1}"><p>{i+1:02} / {len(CHAPTERS)}</p><h2>{escape(c["title"])}</h2><p>{escape(c["lead"])}</p>{markdown(c.get("presentation",c["sections"][0]["body"]))}<a href="{c["slug"]}.html">Read this chapter →</a></section>' for i,c in enumerate(CHAPTERS))
    write('presentation.html',shell('presentation',TITLE,PLAN.get('subtitle','An Australian network of shared adventures and useful skills.'),'<section class="wrap wide-section">'+controls+slides+'</section>',section='Presentation'))
    write('404.html',shell('404','Find your next chapter','The business plan and source library are here.','<section class="wrap wide-section"><a class="button" href="index.html">Executive summary</a> <a href="sitemap.html">All pages</a></section>',art=False,section='Page not found'))
    write('.nojekyll','')
    write('robots.txt','# Discovery does not grant rights beyond LICENCE.md.\nSitemap: '+BASE+'sitemap.xml\n')
    llm='# '+TITLE+'\n\n'+PLAN.get('subtitle','')+'\n\nBy Luke Nathan Hayes. '+EDITION+', '+DATE+'.\n\nRead the business plan and current direction before interpreting archive sources. ROUND ONE is exploratory research. Source observations, model assumptions and founder decisions are separate. Numerical scenarios are worked illustrations. No prices, premises, room counts, calendars, technologies, contractor arrangements, agent teams or financial commitments are chosen by this edition. AI extends research and computation. Source entries distinguish observation dates, verification status and supplier quotation dates. Room capacity follows installed rooms, session timetables and demand. No population-per-node calculation applies. C-Hour is non-monetary. Personal Auras and data belong to their people. The Strange But True Public Source Licence applies.\n\n'+'\n'.join(f'- [{t}]({BASE+s+".html"})' for s,t in NAV)+'\n\n- [Full manuscript]('+BASE+'content/plan.md)\n- [Source register]('+BASE+'content/sources.json)\n- [Licence]('+BASE+'LICENCE.md)\n'
    write('llms.txt',llm)
    urls=[BASE+('' if s=='index' else s+'.html') for s,_ in NAV]
    write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(u)+'</loc></url>' for u in urls)+'</urlset>')

def update_readers():
    for d in DOCS:
        p=ROOT/'documents/readers'/f'{d["id"]}.html'
        if not p.exists():continue
        old=p.read_text(encoding="utf-8")
        m=re.search(r'<article class="reader">(.*?)</article>',old,re.S)
        if m:
            content=m[1]
        else:
            original=re.search(r'<main[^>]*>(.*?)</main>',old,re.S)
            if not original:continue
            content=re.sub(r'<h1[^>]*>.*?</h1>','',original[1],count=1,flags=re.S)
            if d.get('path') and (ROOT/d['path']).is_file():
                content='<p><a href="'+quote(d['path'],safe='/')+'">Open this unchanged source file</a></p>'+content
        body='<div class="wrap"><article class="reader">'+content+'</article></div>'
        p.write_text(shell(d['id'],d['title'],'Unchanged source text in a searchable reading copy.',body,art=False,section='Original document',canonical=BASE+'documents/readers/'+d['id']+'.html',base_tag=True),encoding='utf-8')

def source_pack():
    p=ROOT/'downloads/Escape-Room-Network-Source-Pack.zip'
    temporary=p.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for d in DOCS:
            f=ROOT/d.get('path','')
            if f.is_file():z.write(f,f.relative_to(ROOT))
        for f in ['content/sources.json','content/embedded-links.json','LICENCE.md','RIGHTS.md']:
            if (ROOT/f).is_file():z.write(ROOT/f,f)
    temporary.replace(p)

class Links(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=[];self.images=[];self.h1=0;self.base=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='base':self.base=a.get('href')
        if 'id' in a:self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        for k in ['href','src']:
            if tag!='base' and k in a:self.refs.append(a[k])
        if tag=='img':self.images.append(a)

def checks(require_assets=False):
    errors=[];parsed={}
    main_pages=[ROOT/(s+'.html') for s,_ in NAV]
    readers=sorted((ROOT/'documents/readers').glob('*.html'))
    def parse(p):
        if p not in parsed:
            parser=Links();parser.feed(p.read_text(encoding="utf-8"));parsed[p]=parser
        return parsed[p]
    for p in main_pages+readers+[ROOT/'404.html']:
        if not p.is_file():
            errors.append(f'Missing page {p.relative_to(ROOT)}');continue
        parser=parse(p)
        if parser.h1!=1:errors.append(f'{p.name}: expected one h1')
        if len(parser.ids)!=len(set(parser.ids)):errors.append(f'{p.name}: duplicate HTML ids')
        if require_assets and p in main_pages and sum('assets/heroes/' in a.get('src','') for a in parser.images)!=1:errors.append(f'{p.name}: expected one hero image')
        for a in parser.images:
            if 'alt' not in a:errors.append(f'{p.name}: image without alt text')
        for ref in parser.refs:
            u=urlsplit(unescape(ref))
            if u.scheme or u.netloc:continue
            base=(p.parent/parser.base).resolve() if parser.base else p.parent
            target=(base/unquote(u.path)).resolve() if u.path else (base if parser.base else p)
            if target.is_dir():target=target/'index.html'
            if not target.is_file():
                errors.append(f'{p.relative_to(ROOT)}: missing {ref}');continue
            if u.fragment and target.suffix=='.html' and unquote(u.fragment) not in parse(target).ids:
                errors.append(f'{p.relative_to(ROOT)}: missing anchor {ref}')
    raw=json.dumps(PLAN,ensure_ascii=False)
    if '\u2014' in raw:errors.append('Authored manuscript contains an em dash')
    if re.search(r'\b(?:Megan|Meghan|Brad)\b',raw):errors.append('Authored manuscript contains an inherited family role')
    for c in CHAPTERS:
        ids=set(c.get('refs',[]))
        for s in c['sections']:
            ids.update(s.get('refs',[]))
            ids.update(re.findall(r'\b[DPMR]\d{2,3}\b',s['body']))
        for sid in sorted(ids-set(REFS)):
            errors.append(f'{c["slug"]}: unknown source {sid}')
    if require_assets:
        from PIL import Image
        hashes={}
        for s,_ in NAV:
            a=ART.get(s,{})
            if not a.get('path') or not (ROOT/a['path']).is_file():
                errors.append(f'{s}: missing hero asset');continue
            image_path=ROOT/a['path']
            digest=hashlib.sha256(image_path.read_bytes()).hexdigest()
            if digest in hashes:errors.append(f'Hero reused by {s} and {hashes[digest]}')
            hashes[digest]=s
            if a.get('sha256')!=digest:errors.append(f'{s}: hero differs from provenance hash')
            try:
                with Image.open(image_path) as im:im.verify()
            except Exception as exc:errors.append(f'{s}: unreadable hero ({type(exc).__name__})')
        for name in ['Escape-Room-Network-Business-Plan.docx','Escape-Room-Network-Source-Pack.zip']:
            p=ROOT/'downloads'/name
            try:
                with zipfile.ZipFile(p) as z:
                    if z.testzip():errors.append(f'{name}: archive checksum failed')
                    if p.suffix=='.docx' and not {'[Content_Types].xml','word/document.xml'}<=set(z.namelist()):
                        errors.append(f'{name}: required Word document parts missing')
            except (OSError,zipfile.BadZipFile):errors.append(f'{name}: unreadable archive')
        pdf=ROOT/'downloads/Escape-Room-Network-Business-Plan.pdf'
        if pdf.is_file():
            data=pdf.read_bytes()
            if not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:
                errors.append(f'{pdf.name}: invalid PDF header or end marker')
        else:errors.append(f'{pdf.name}: missing PDF')
    report={'pages':len(main_pages),'chapters':len(CHAPTERS),'heroes':sum(bool(ART.get(s)) for s,_ in NAV),'source_readers':len(readers),'source_entries':len(REFS),'original_documents':sum((ROOT/d.get('path','')).is_file() for d in DOCS),'errors':errors}
    write('content/build-report.json',json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--require-assets',action='store_true');p.add_argument('--no-source-pack',action='store_true');args=p.parse_args()
    build_chapters();build_sources();build_utilities();update_readers()
    if not args.no_source_pack:source_pack()
    if args.check:checks(args.require_assets)
