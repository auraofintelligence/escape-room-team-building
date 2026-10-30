# Escape Room Team Building

ROUND ONE business-development research by Luke Nathan Hayes for an Australian escape-room network. The opening contains sourced capacities, competitor prices and editable throughput/turnover comparisons. Later chapters cover design, tourism, recorded learning, paid work, costs and renewal.

- [Website and summary calculator](https://auraofintelligence.github.io/escape-room-team-building/)
- [PDF](downloads/Escape-Room-Network-Business-Plan.pdf) and [Word](downloads/Escape-Room-Network-Business-Plan.docx)
- [Canonical manuscript](content/plan.json), [Markdown](content/plan.md), [source register](content/sources.json)
- [Cost benchmarks and formulas](content/finance.json), [venue data](content/market-data.json), [revision record](content/revision-notes.json)

Recording is part of the core design with a clear opt-out. AI supports research and computation; commercial choices remain with Luke. Numbers are sourced observations or labelled comparison inputs. Unknown cost inputs stay blank. Unsupported installation hours and their totals have been removed.

## Build and check

The site uses Python and Pillow. Portable editions also use python-docx and ReportLab; the audit uses PyMuPDF and lxml. Node runs the independent calculator fixtures. Embedded PDF fonts default to Windows Arial paths.

```sh
python scripts/check_finance.py
node scripts/check_calculators.cjs
python scripts/build_documents.py
python scripts/build_pdf.py
python scripts/build.py --check --require-assets
python scripts/audit_documents.py
```

The seven calculators run locally in the browser without network calls or saved inputs. Only the summary starts with explicitly labelled comparison values. Its source price, group tier and arithmetic are checked against the portable edition. Document calculator links open the corresponding website section.

The PDF is visually reviewed. Word content and navigation are checked; native Word pagination remains unverified because the packaged renderer requires LibreOffice, unavailable on this device. The editions share a manuscript and have independent layouts.

## Rights

[Strange But True Public Source Licence](LICENCE.md). Original source files and licence terms are preserved. Generated favicon artwork and prompt: [provenance](content/favicon.json).
