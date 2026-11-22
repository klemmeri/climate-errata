# Climate Errata

Independent, reproducible checks of climate papers, datasets and code.

- Site: published with Netlify from this repository (static HTML; no build step).
- `entries.json`: the register (one object per entry).
- `entries/<id>.html`: one page per entry, with a comment thread (giscus, backed by this repository's Discussions).
- `about.html`: how the register works (contact first, statuses, significance, rules).

Content: CC BY 4.0. Code: MIT. See LICENSE.md.

Maintained by Mark L. Morrissey, Ph.D., Professor Emeritus of Meteorology.

## Discussion, search and private reports (added 22 Nov 2026)
- `doi.html?doi=10.xxxx/...` — a discussion page for any paper or dataset DOI. Metadata from Crossref, falling back to DataCite; register entries that mention the DOI; a giscus thread keyed to `doi:<doi>` (one shared thread per DOI).
- `search.html?q=...` — searches `entries.json` and `discussions.json` (keywords or a DOI).
- `discussions.json` is refreshed by `.github/workflows/export-discussions.yml` (on every discussion or comment, every 6 h, or by hand: Actions → "Export discussions for site search" → Run workflow).
- `report.html` — Netlify form `contact` for questions, private error reports and author responses. Submissions: Netlify → Forms (form detection must be enabled once in the Netlify project settings).
- Posting policy: about.html#posting. New, unreported error claims go to the responsible party first; such comments may be hidden until that has happened.
- Optional per row in `data/register_rows.json`: `target_doi` (the paper's or dataset's own DOI) links the entry to its DOI discussion page.
