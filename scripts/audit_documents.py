"""Check canonical-content completeness and portable document navigation."""
from pathlib import Path
import argparse
import json
import re
import zipfile
from lxml import etree
import fitz

ROOT = Path(__file__).resolve().parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def plain_tokens(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return " ".join(re.findall(r"\w+", text.casefold()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, default=ROOT/"downloads/Escape-Room-Network-Business-Plan.docx")
    parser.add_argument("--pdf", type=Path, default=ROOT/"downloads/Escape-Room-Network-Business-Plan.pdf")
    parser.add_argument("--pagination-out", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT/"content/document-audit.json")
    args = parser.parse_args()
    plan = json.loads((ROOT/"content/plan.json").read_text(encoding="utf-8"))
    sources = json.loads((ROOT/"content/sources.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(args.docx) as z:
        xml = etree.fromstring(z.read("word/document.xml"))
    all_text = " ".join(xml.xpath("//w:t/text()", namespaces=NS))
    tokens = plain_tokens(all_text)
    missing = []
    for c in plan["chapters"]:
        if plain_tokens(c["lead"]) not in tokens:
            missing.append(c["slug"]+" lead")
        for s in c["sections"]:
            if plain_tokens(s["body"]) not in tokens:
                missing.append(c["slug"]+" / "+s["title"])
    bookmarks = xml.xpath("//w:bookmarkStart/@w:name", namespaces=NS)
    internal = xml.xpath("//w:hyperlink/@w:anchor", namespaces=NS)
    missing_targets = sorted(set(internal)-set(bookmarks))
    ids = [e["id"] for key in ("documents", "links", "research") for e in sources.get(key, [])]
    missing_sources = [i for i in ids if "source_"+i not in bookmarks]
    doc = fitz.open(args.pdf)
    pdf_text = ' '.join(re.sub(r'ROUND ONE\s*\|\s*Escape Room Team Building\s*\|\s*Luke Nathan Hayes\s*\d+\s*', '', p.get_text()) for p in doc)
    pdf_tokens = plain_tokens(pdf_text)
    pdf_missing = []
    for c in plan['chapters']:
        if plain_tokens(c['lead']) not in pdf_tokens:
            pdf_missing.append(c['slug']+' lead')
        for s in c['sections']:
            for block in re.split(r'\n\s*\n', s['body']):
                lines = block.splitlines() if block.lstrip().startswith(('|','- ')) else [block]
                for line in lines:
                    if re.fullmatch(r'[\s|:\-]+',line):
                        continue
                    if plain_tokens(line) not in pdf_tokens:
                        pdf_missing.append(c['slug']+' / '+s['title']+': '+line[:65])
    toc = {title: page for level,title,page in doc.get_toc() if level == 1}
    pagination = {"chapter_"+re.sub(r"\W", "_", c["slug"]):toc.get("EXECUTIVE SUMMARY" if i == 0 else c["title"]) for i,c in enumerate(plan["chapters"])}
    pagination.update({"source_register": toc.get("Sources and project inventory"), "rights": toc.get("Rights and provenance"), "licence": toc.get("Strange But True Public Source Licence")})
    if args.pagination_out:
        args.pagination_out.parent.mkdir(parents=True, exist_ok=True)
        args.pagination_out.write_text(json.dumps(pagination, indent=2)+"\n")
    outside = []
    for i,p in enumerate(doc):
        for word in p.get_text("words"):
            if word[0] < 20 or word[2] > p.rect.width-20 or word[1] < 12 or word[3] > p.rect.height-8:
                outside.append({"page": i+1, "word": word[4], "rect": list(word[:4])})
    report = {
        "pages": len(doc),
        "chapters": len(plan["chapters"]),
        "sections": sum(len(c["sections"]) for c in plan["chapters"]),
        "source_entries": len(ids),
        "missing_manuscript_sections": missing,
        "missing_pdf_manuscript_sections": pdf_missing,
        "missing_source_entries": missing_sources,
        "unresolved_internal_links": missing_targets,
        "duplicate_bookmarks": len(bookmarks)-len(set(bookmarks)),
        "em_dashes_in_document_text": all_text.count("\u2014"),
        "pdf_links": sum(len(p.get_links()) for p in doc),
        "words_outside_page_safe_area": outside,
        "contents_page_numbers": pagination,
        "visual_review": "Pending inspection of every rendered page"
    }
    args.report.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))
    if missing or pdf_missing or missing_targets or missing_sources or outside or len(bookmarks) != len(set(bookmarks)) or any(x is None for x in pagination.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
