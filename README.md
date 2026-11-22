# Climate Errata

Independent, reproducible checks of climate papers, datasets and code.

- Site: published with Netlify from this repository (static HTML; no build step).
- `entries.json`: the register (one object per entry).
- `entries/<id>.html`: one page per entry, with a comment thread (giscus, backed by this repository's Discussions).
- `about.html`: how the register works (contact first, statuses, significance, rules).

Content: CC BY 4.0. Code: MIT. See LICENSE.md.

Maintained by Mark L. Morrissey, Ph.D., Professor Emeritus of Meteorology, School of Meteorology, University of Oklahoma.

## Discussion, search and private reports (added 22 Nov 2026)
- `doi.html?doi=10.xxxx/...` — a discussion page for any paper or dataset DOI. Metadata from Crossref, falling back to DataCite; register entries that mention the DOI; a giscus thread keyed to `doi:<doi>` (one shared thread per DOI).
- `search.html?q=...` — searches `entries.json` and `discussions.json` (keywords or a DOI).
- `discussions.json` is refreshed by `.github/workflows/export-discussions.yml` (on every discussion or comment, every 6 h, or by hand: Actions → "Export discussions for site search" → Run workflow).
- `report.html` — Netlify form `contact` for questions, private error reports and author responses. Submissions: Netlify → Forms (form detection must be enabled once in the Netlify project settings).
- Posting policy: about.html#posting. New, unreported error claims go to the responsible party first; such comments may be hidden until that has happened.
- Optional per row in `data/register_rows.json`: `target_doi` (the paper's or dataset's own DOI) links the entry to its DOI discussion page.
- Dataset pages (added 22 Nov 2026): curated facts in `data/datasets.json` (check against the producer's pages; update `checked`). `python3 tools/build_datasets.py` writes `datasets/*.html`, `datasets/index.html`, per-dataset RSS `datasets/<id>.xml`, `datasets/datasets.json` and the site feed `feed.xml`. The discussions workflow reruns it, so thread lists and feeds stay current. To add a dataset: add a block to `data/datasets.json` (keywords decide which discussions are listed; `entries` lists register entry ids) and run the script.
- "Papers that use the affected data" (added 22 Nov 2026): curated in `data/affected.json`, rendered on entry pages by `assets/affected.js`. List a paper only when its abstract or text shows it uses the affected data for the affected region and a period that spans the problem; mark the effect as not assessed. Never list a paper the maintainer is screening or has contacted until its contact window has closed. Candidate review happens privately (not in this repo).
- Site updates (added 22 Nov 2026): changes to the website itself go in `data/site_updates.json` (newest first); `python3 tools/build.py` writes `updates.html` and `site-updates.xml`. Errata changes do not go here.
