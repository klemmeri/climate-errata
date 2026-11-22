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
                        summary=summary))
    links = []
    if r.get("link"):
        links.append(f'<a href="{e(r["link"])}">{e(r["link"])}</a>')
    if r.get("doi"):
        links.append(f'<a href="https://doi.org/{e(r["doi"])}">doi:{e(r["doi"])}</a>')
    scores = ""
    if tot is not None:
        scores = (f'<tr><th>Significance</th><td><strong>{cls}</strong> (Size {r["S"]} · Reach {r["R"]} · '
                  f'Consequence {r["C"]} = {tot} of 6)<div class="meta" style="margin-top:4px">Basis: {e(r["basis"])}</div></td></tr>')
    else:
        scores = '<tr><th>Significance</th><td>Not scored (clean check or already-known issue)</td></tr>'
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
<tr><th>Where reported</th><td>{doi_links(e(r['reported']))}{'<br>' + '<br>'.join(links) if links else ''}</td></tr>
<tr><th>Date</th><td>{e(r['date'])}</td></tr>
</table>
<p class="meta">A fuller write-up, with the evidence and reproduction code, will be added to this page. Questions and corrections are welcome below.</p>
{GISCUS}
</div></main>
{FOOT}"""
    (ROOT / "entries" / f"{sid}.html").write_text(page)

entries += CUSTOM
json.dump(entries, open(ROOT / "entries.json", "w"), indent=1, ensure_ascii=False)
print(len(entries), "entries")
