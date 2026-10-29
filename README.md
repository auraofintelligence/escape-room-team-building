# Escape Room Team Building

Business plan by Luke Nathan Hayes for an Australian escape-room network connecting immersive experiences, tourism, paid local work and whole-of-life skill development.

The plan opens with the business proposition, market and operating model. Language analysis and learning sit within the full commercial plan. The proposed AI agent organisation is documented for Luke's approval and is not activated by this repository.

## Read the plan

- [Website](https://auraofintelligence.github.io/escape-room-team-building/)
- [PDF business plan](downloads/Escape-Room-Network-Business-Plan.pdf)
- [Editable Word business plan](downloads/Escape-Room-Network-Business-Plan.docx)
- [Canonical manuscript](content/plan.json)
- [Portable Markdown](content/plan.md)
- [Financial inputs](content/finance.json)
- [Sources](content/sources.json)

## Build

Python 3 and Pillow are required for the static site generator. The full manuscript is kept in `content/plan.json`. Source registers, financial assumptions and artwork provenance are separate structured files.

```sh
python scripts/check_finance.py
python scripts/build.py --check --require-assets
```

The repository's existing GitHub Pages publication serves the generated static files from the main branch. Run the checks above before publishing an update. Publication does not run an operating business agent, contact anyone, purchase anything or create a business schedule.

## Rights

[Strange But True Public Source Licence](LICENCE.md). Commercial and corporate rights remain with Luke Nathan Hayes. The style and navigation follow [Installing the Missing Middle](https://auraofintelligence.github.io/installing-the-missing-middle/). Original reference documents retain their original rights and wording.
