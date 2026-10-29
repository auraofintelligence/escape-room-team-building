# Escape Room Team Building

Business plan by Luke Nathan Hayes for an Australian escape-room network connecting immersive experiences, tourism, paid local work and whole-of-life skill development.

ROUND ONE is exploratory market research, evidence, itemised cost options and worked calculations for Luke Nathan Hayes to review. The executive summary and one-sentence proposition open the plan. Language research and learning sit in the middle. Source facts, model assumptions and founder decisions remain separate. No commercial format, price, premises, timetable, technology, contractor arrangement or agent suite is selected by this edition.

## Read the plan

- [Website](https://auraofintelligence.github.io/escape-room-team-building/)
- [PDF business plan](downloads/Escape-Room-Network-Business-Plan.pdf)
- [Editable Word business plan](downloads/Escape-Room-Network-Business-Plan.docx)
- [Canonical manuscript](content/plan.json)
- [Portable Markdown](content/plan.md)
- [Financial inputs](content/finance.json)
- [Sources](content/sources.json)

## Build

Python 3 and Pillow are required for the static site generator. The full manuscript is kept in `content/plan.json`. Source registers, financial assumptions and artwork provenance are separate structured files. The source register records observation dates, recheck status and quotation dates where available. No requested supplier quotations are recorded in ROUND ONE.

```sh
python scripts/check_finance.py
python scripts/build.py --check --require-assets
```

The repository's existing GitHub Pages publication serves the generated static files from the main branch. Run the checks above before publishing an update. Publication does not run an operating business agent, contact anyone, purchase anything or create a business schedule.

## Rights

[Strange But True Public Source Licence](LICENCE.md). Commercial and corporate rights remain with Luke Nathan Hayes. The style and navigation follow [Installing the Missing Middle](https://auraofintelligence.github.io/installing-the-missing-middle/). Original reference documents retain their original rights and wording.

## Portable editions

The Word builder uses python-docx, Pillow and ReportLab. The PDF builder uses the same canonical manuscript with independent pagination. Its default embedded-font paths target Windows Arial; pass suitable local font files when adapting the builder to another host.

```sh
python scripts/build_documents.py
python scripts/build_pdf.py
python scripts/audit_documents.py
```

The document audit also uses PyMuPDF and lxml. ROUND ONE's PDF received a full visual review. Word content and navigation were checked; Word pagination remains visually unverified because a compatible native renderer was unavailable on the authoring device.

The generated favicon and its full generation prompt are recorded in [content/favicon.json](content/favicon.json).
