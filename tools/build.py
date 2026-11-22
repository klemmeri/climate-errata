"""Build Climate Errata entry pages and entries.json from data/register_rows.json.

Hand-written pages listed in CUSTOM are kept as they are; only their entries.json record is merged in.
Run from the repository root:  python3 tools/build.py
"""
import json, re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = json.load(open(ROOT / "data/register_rows.json"))
CUSTOM = json.load(open(ROOT / "data/custom_entries.json"))

TYPE = {"Code": "code", "Observing data": "dataset", "Paper": "paper"}

def status(r):
    o, v = r["outcome"], r["verdict"]
    if o == "n/a":
        return ("known", "Already known") if "known" in v.lower() else ("clean", "No error found")
    if o.startswith("Fixed"):
        return "fixed", o
    if o in ("Confirmed", "Acknowledged", "Resolved"):
        return "acknowledged", o
    if o == "Published":
        return "reported", "Published (preprint)"
    if o == "Public comment":
        return "reported", "Public comment"
    return "reported", "Reported (open)"

def sig(r):
    if r.get("S") is None:
        return "Not scored", None
    t = r["S"] + r["R"] + r["C"]
    return ("High" if t >= 5 else "Medium" if t >= 3 else "Low"), t

def slug(s):
    s = re.sub(r"\(.*?\)", "", s).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return "-".join(s.split("-")[:6])

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,;()\[\]<>\"']+")

def find_dois(r):
    """All DOIs mentioned in a row: the target's own DOI (optional 'target_doi'), our notes, links."""
    text = " ".join(str(r.get(k) or "") for k in ("target_doi", "doi", "target", "found", "reported", "link", "verdict"))
    out = []
    for d in DOI_RE.findall(text):
        d = d.rstrip(".").lower()
        if d not in out:
            out.append(d)
    return out

def fix_rows(f):
    if not f:
        return ""
    return (f'<tr><th>Fixed on</th><td>{e(f["date"])}</td></tr>'
            f'<tr><th>Fixed in</th><td><a href="{e(f["fixed_in_url"])}">{e(f["fixed_in"])}</a></td></tr>'
            f'<tr><th>Affected versions</th><td>{e(f["affected"])}</td></tr>'
            f'<tr><th>Is the fix retroactive?</th><td>{e(f["scope"])}</td></tr>')

def doi_links(text):
    return re.sub(r"10\.5281/zenodo\.(\d+)", r'<a href="https://doi.org/10.5281/zenodo.\1">10.5281/zenodo.\1</a>', text)

e = html.escape
HEAD = open(ROOT / "tools/head.html").read()
FOOT = open(ROOT / "tools/foot.html").read()
GISCUS = open(ROOT / "tools/giscus.html").read()

entries, seen = [], set()
for r in rows:
    sid = slug(r["target"])
    while sid in seen:
        sid += "-2"
    seen.add(sid)
    st, label = status(r)
    cls, tot = sig(r)
    summary = r["found"]
    entries.append(dict(id=sid, title=r["target"], target=r["target"], type=TYPE[r["area"]], status=st,
                        status_label=label, significance=cls, reported=r["sd"], updated="2026-11-22",
                        summary=summary, fixed=(r.get("fix") or {}).get("date", ""), target_doi=(r.get("target_doi") or "").lower(), dois=find_dois(r)))
    links = []
    if r.get("link"):
        links.append(f'<a href="{e(r["link"])}">{e(r["link"])}</a>')
    if r.get("target_doi"):
        links.append(f'Discuss this DOI: <a href="/doi.html?doi={e(r["target_doi"])}">doi:{e(r["target_doi"])}</a>')
    if r.get("doi"):
        links.append(f'<a href="https://doi.org/{e(r["doi"])}">doi:{e(r["doi"])}</a>')
    scores = ""
    if tot is not None:
        scores = (f'<tr><th>Significance</th><td><strong>{cls}</strong> (Size {r["S"]} · Reach {r["R"]} · '
                  f'Consequence {r["C"]} = {tot} of 6)<div class="meta" style="margin-top:4px">Basis: {e(r["basis"])}</div></td></tr>')
    else:
        scores = '<tr><th>Significance</th><td>Not scored (clean check or already-known issue)</td></tr>'
    fixrows = fix_rows(r.get("fix"))
    wf = ROOT / "data/writeups" / f"{sid}.html"
    writeup = (wf.read_text() if wf.exists() else
               '<p class="meta">A fuller write-up, with the evidence and reproduction code, will be added to this page. Questions and corrections are welcome below.</p>')
    page = f"""{HEAD.replace('%TITLE%', e(r['target']) + ' — Climate Errata').replace('%DESC%', e(summary[:150]))}
<main><div class="wrap">
<p class="meta"><a href="/">← Register</a></p>
<h1>{e(r['target'])}</h1>
<div class="meta"><span class="pill st-{st}">{e(label)}</span><span class="pill type">{TYPE[r['area']]}</span><span class="pill sig">Significance: {cls}</span></div>
<h2>Finding</h2>
<p>{e(r['found'])}</p>
<table class="facts">
<tr><th>Verdict</th><td>{e(r['verdict'])}</td></tr>
{scores}
<tr><th>Outcome</th><td>{e(r['outcome'] if r['outcome'] != 'n/a' else label)}</td></tr>
{fixrows}
<tr><th>Where reported</th><td>{doi_links(e(r['reported']))}{'<br>' + '<br>'.join(links) if links else ''}</td></tr>
<tr><th>Date</th><td>{e(r['date'])}</td></tr>
</table>
{writeup}
<section id="affected" data-entry="{sid}"></section><script src="/assets/affected.js" defer></script>
{GISCUS}
</div></main>
{FOOT}"""
    (ROOT / "entries" / f"{sid}.html").write_text(page)

for c in CUSTOM:
    c["fixed"] = (c.get("fix") or {}).get("date", "")
    c.setdefault("target_doi", "")
    c.setdefault("dois", [c["target_doi"]] if c["target_doi"] else [])
entries += CUSTOM
json.dump(entries, open(ROOT / "entries.json", "w"), indent=1, ensure_ascii=False)
print(len(entries), "entries")


# ---- Site updates page and feed (changes to the site itself, not errata) ----
from email.utils import format_datetime as _fd
from datetime import datetime as _dt, timezone as _tz
UP = json.load(open(ROOT / "data/site_updates.json"))["updates"]
items = "".join(
    f'<article class="entry" id="u{i}"><h3>{e(u["title"])}</h3><div class="meta"><span>{e(u["date"])}</span></div>'
    f'<p style="margin:8px 0 0">{e(u["text"])}</p></article>' for i, u in enumerate(UP))
body = f"""<h1>Site updates</h1>
<p class="lede">Changes to the Climate Errata website itself: new features, new pages and changes to how it works. Updates to the errata are in the <a href="/">register</a> and its <a href="/feed.xml">feed</a>.</p>
<p class="meta" style="display:block"><a href="/site-updates.xml">RSS feed of site updates</a> · Suggestions for the site are welcome through <a href="/report.html?kind=comment">Write to us</a>.</p>
{items}"""
(ROOT / "updates.html").write_text(
    HEAD.replace("%TITLE%", "Site updates — Climate Errata").replace("%DESC%", "Changes to the Climate Errata website itself.")
    + "\n<main><div class=\"wrap\">\n" + body + "\n</div></main>\n" + FOOT)
SITE = "https://climateerrata.org"
rss = ['<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Climate Errata: site updates</title>'
       f'<link>{SITE}/updates.html</link><description>Changes to the Climate Errata website itself</description><language>en</language>']
for i, u in enumerate(UP):
    d = _fd(_dt.fromisoformat(u["date"] + "T00:00:00+00:00").astimezone(_tz.utc))
    rss.append(f'<item><title>{e(u["title"])}</title><link>{SITE}/updates.html#u{i}</link><guid isPermaLink="false">site:{e(u["date"])}:{e(u["title"])}</guid>'
               f'<pubDate>{d}</pubDate><description>{e(u["text"])}</description></item>')
rss.append("</channel></rss>\n")
(ROOT / "site-updates.xml").write_text("".join(rss))
print(len(UP), "site updates")
