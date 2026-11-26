"""Build Climate Errata entry pages and entries.json from data/register_rows.json.

Hand-written pages listed in CUSTOM are kept as they are; only their entries.json record is merged in.
Run from the repository root:  python3 tools/build.py
"""
import json, re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = json.load(open(ROOT / "data/register_rows.json"))
CUSTOM = json.load(open(ROOT / "data/custom_entries.json"))
ABOUT = json.load(open(ROOT / "data/about.json"))

TYPE = {"Code": "code", "Observing data": "dataset", "Paper": "paper"}

def status(r):
    o, v = r["outcome"], r["verdict"]
    if o == "n/a":
        return ("known", "Already known") if "known" in v.lower() else ("clean", "No error found")
    if o.startswith("Fixed"):
        return "fixed", o
    if o in ("Confirmed", "Acknowledged", "Resolved"):
        return "acknowledged", o
    if o == "Disputed":
        return "disputed", "Disputed"
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
from urllib.parse import quote as _q
def respond_box(target):
    url = "/report.html?kind=response&entry=" + _q(target, safe="")
    return ('<section class="respond" id="respond"><h2>Authors and producers: respond or object</h2>'
            '<p>If you are an author, data producer or developer of this work and you disagree with this finding, '
            'or think we have misread something, <a href="' + url + '">send us your response</a>. '
            'We review every response promptly. If it shows our finding is wrong, we correct or withdraw the entry openly '
            '(see <a href="/policies.html#corrections">Corrections</a>). If you would like your response shown on this page, '
            'it is published unedited, with or without your name as you prefer, and never without your permission. '
            'You can also reply publicly in the discussion below.</p></section>')

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
                        summary=summary, verdict=r.get("verdict", ""), about=ABOUT.get(str(r["row"]), ""), fixed=(r.get("fix") or {}).get("date", ""), target_doi=(r.get("target_doi") or "").lower(), dois=find_dois(r)))
    links = []
    if r.get("link"):
        links.append(f'<a href="{e(r["link"])}">{e(r["link"])}</a>')
    if r.get("target_doi"):
        links.append(f'Discuss this DOI: <a href="/doi.html?doi={e(r["target_doi"])}">doi:{e(r["target_doi"])}</a>')
    if r.get("doi"):
        dlabel = "Our write-up on Zenodo (latest version)" if r["doi"].startswith("10.5281/zenodo.") else "DOI"
        links.append(f'{dlabel}: <a href="https://doi.org/{e(r["doi"])}">doi:{e(r["doi"])}</a>')
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
<div class="meta"><span class="pill st-{st}">{e(label)}</span><span class="pill type">{TYPE[r['area']]}</span><a class="pill sig" href="/about.html#significance" title="How significance is scored">Significance: {cls}</a></div>
{('<h2>What it is</h2>' + chr(10) + '<p>' + e(ABOUT[str(r["row"])]) + '</p>') if str(r["row"]) in ABOUT else ''}
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
{respond_box(r["target"])}
{GISCUS}
</div></main>
{FOOT}"""
    (ROOT / "entries" / f"{sid}.html").write_text(page)

for c in CUSTOM:
    c["fixed"] = (c.get("fix") or {}).get("date", "")
    c.setdefault("about", ABOUT.get(c["id"], ""))
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


# ---- What we checked (papers by side; datasets; code) ----
CK = json.load(open(ROOT / "data/checked.json"))
OUT = {"clean": "No error found", "nomaterial": "No material error found", "reviewed": "Method reviewed, not rerun; no material error found", "inprint": "Already known, corrected or challenged in print",
       "flagged": "Error found (see register)", "withauthors": "Finding sent to the authors", "inprogress": "Check not finished"}
SIDE = {"mainstream": "Mainstream findings", "questioning": "Papers questioning mainstream findings"}
def _cnt(items, outs, side=None):
    return sum(p.get("count", 1) for p in items if p["outcome"] in outs and (side is None or p.get("side") == side))
def _li(p):
    link = f'<a href="https://doi.org/{e(p["doi"])}">{e(p["cite"])}</a>' if p.get("doi") else (f'<a href="{e(p["entry"])}">{e(p["cite"])}</a>' if p.get("entry") else e(p["cite"]))
    return (f'<li>{link}: {e(p["topic"])}. <strong>{OUT[p["outcome"]]}</strong>'
            f'{(". " + e(p["note"])) if p.get("note") else ""}</li>')
HDR = '<tr><th></th><th>Checked</th><th>No error / no material error</th><th>Already known or in print</th><th>Error found or sent to authors</th><th>Not finished</th></tr>'
def _row(label, items, side=None):
    return (f'<tr><th>{label}</th><td>{_cnt(items, ["clean","nomaterial","reviewed","inprint","flagged","withauthors"], side)}</td>'
            f'<td>{_cnt(items, ["clean","nomaterial","reviewed"], side)}</td><td>{_cnt(items, ["inprint"], side)}</td>'
            f'<td>{_cnt(items, ["flagged","withauthors"], side)}</td><td>{_cnt(items, ["inprogress"], side)}</td></tr>')
# flagged datasets and code that are public: from the register
def _flagged(area, ctype):
    out = []
    for ent, r in zip(entries[:len(rows)], rows):
        if r["area"] == area and str(r.get("verdict", "")).startswith("Real"):
            out.append({"cite": ent["title"], "topic": ent["status_label"], "outcome": "flagged", "entry": f"/entries/{ent['id']}.html"})
    for c in CUSTOM:
        if c.get("type") == ctype:
            out.append({"cite": c["title"], "topic": c.get("status_label", c.get("status", "")), "outcome": "flagged", "entry": f"/entries/{c['id']}.html"})
    return out
DS = _flagged("Observing data", "dataset") + CK["datasets"]
CO = _flagged("Code", "code") + CK["code"]
papers = CK["papers"]
def _section(items, title):
    named = [p for p in items if "cite" in p]
    s = ""
    fl = [p for p in named if p["outcome"] == "flagged"]
    ok = [p for p in named if p["outcome"] != "flagged"]
    if ok:
        s += f"<h3>{title}: no error, no material error, or already known</h3><ul>" + "".join(_li(p) for p in ok) + "</ul>"
    if fl:
        s += f"<h3>{title}: errors found (register entries, with current status)</h3><ul>" + "".join(
            f'<li><a href="{e(p["entry"])}">{e(p["cite"])}</a> &mdash; {e(p["topic"])}</li>' for p in fl) + "</ul>"
    return s
plis = ""
for sd in SIDE:
    ps = [p for p in papers if "cite" in p and p.get("side") == sd]
    if ps:
        plis += f"<h3>{SIDE[sd]}</h3><ul>" + "".join(_li(p) for p in ps) + "</ul>"
body = f"""<h1>What we checked</h1>
<p class="lede">Every paper, dataset and piece of code we have checked, with the outcome, whether or not we found an error. What we choose to check, and why, is explained on the <a href="/about.html#selection">How it works</a> page.</p>
<p class="meta" style="display:block">When we find a possible error, the authors, data producers or developers hear about it first. Until they reply or three weeks pass, such items are counted here but not named; then they are added by name with a link to their register entry. <a href="#papers">Papers</a> · <a href="#datasets">Datasets</a> · <a href="#code">Code</a></p>
<h2 id="papers">Papers</h2>
<p>Papers taken up in our systematic screening since 22 November 2026. Papers questioning mainstream climate findings are tested with the same methods and standards as the rest. The numbers are small, so the proportions say little yet. "Method reviewed, not rerun" means we read the methods and found nothing that called for a rerun; it is a lighter check than "no error found", which means we reproduced or tested the result.</p>
<table class="facts">{HDR}{_row(SIDE["mainstream"], papers, "mainstream")}{_row(SIDE["questioning"], papers, "questioning")}</table>
{plis}
<h2 id="datasets">Datasets</h2>
<p>Observing and gridded datasets checked since our audits began in {e(CK["other_since"])}. These checks were not a random sample: we went looking where errors are most likely, such as instrument changes and sudden changes in the number of reporting stations. The share with errors therefore says nothing about how often datasets in general contain errors.</p>
<table class="facts">{HDR}{_row("Datasets", DS)}</table>
{_section(DS, "Datasets")}
<h2 id="code">Code</h2>
<p>Climate software checked since our audits began in {e(CK["other_since"])}. A line may cover several related packages checked together. These checks were not a random sample either: we chose the most widely used packages and the parts of them most likely to go wrong, such as statistical defaults, edge cases and recently changed code. The share with errors therefore says nothing about how often climate software in general contains errors.</p>
<table class="facts">{HDR}{_row("Code", CO)}</table>
{_section(CO, "Code")}"""
(ROOT / "checked.html").write_text(
    HEAD.replace("%TITLE%", "What we checked — Climate Errata").replace("%DESC%", "Every paper, dataset and piece of code checked, with the outcome, including those with no error.")
    + "\n<main><div class=\"wrap\">\n" + body + "\n</div></main>\n" + FOOT)
print(len(DS), "datasets,", len(CO), "code lines on checked.html")

# ---------------------------------------------------------------- one-line activity summary (home page)
def _activity_line():
    import json as _j
    reg = _j.loads((ROOT / "data" / "register_rows.json").read_text())
    ck = _j.loads((ROOT / "data" / "checked.json").read_text())
    n = lambda xs: sum(int(x.get("count", 1)) for x in xs)
    checks = n(ck["papers"]) + n(ck["datasets"]) + n(ck["code"]) + len(reg)
    fixed = sum(1 for r in reg if str(r.get("outcome", "")).startswith(("Fixed", "Resolved")))
    return (f'<!--ACTIVITY--><p class="note activity">Since November 2026 we have recorded {checks} checks of papers, '
            f'datasets and code (<a href="/checked.html">what we checked</a>). {len(reg)} problems are on the register, '
            f'{fixed} of them since fixed by the developers or producers.</p><!--/ACTIVITY-->')

import re as _re
_idx = ROOT / "index.html"
_t = _idx.read_text()
_line = _activity_line()
if "<!--ACTIVITY-->" in _t:
    _t = _re.sub(r"<!--ACTIVITY-->.*?<!--/ACTIVITY-->", lambda m: _line, _t, flags=_re.S)
else:
    _t = _t.replace('<div class="stats" id="stats"></div>', _line + '\n<div class="stats" id="stats"></div>', 1)
_idx.write_text(_t)
