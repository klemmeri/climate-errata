"""Build dataset pages, the dataset index and RSS feeds.

Inputs:  data/datasets.json (curated, facts checked by hand), entries.json, discussions.json
Outputs: datasets/index.html, datasets/<id>.html, datasets/<id>.xml (RSS), datasets/datasets.json,
         feed.xml (all register entries)
Run from anywhere:  python3 tools/build_datasets.py
The output depends only on the inputs (no build timestamps), so the GitHub Action commits only real changes.
"""
import json, re, html, pathlib
from email.utils import format_datetime
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = "https://climateerrata.org"
DS = json.load(open(ROOT / "data/datasets.json"))
ENTRIES = {e["id"]: e for e in json.load(open(ROOT / "entries.json"))}
try:
    DISC = json.load(open(ROOT / "discussions.json")).get("discussions", [])
except FileNotFoundError:
    DISC = []
HEAD = open(ROOT / "tools/head.html").read()
FOOT = open(ROOT / "tools/foot.html").read()
GISCUS = open(ROOT / "tools/giscus.html").read()
e = html.escape
OUT = ROOT / "datasets"
OUT.mkdir(exist_ok=True)


def rfc822(d):
    """'2026-11-20' or ISO timestamp -> RFC 822 date for RSS."""
    if not d:
        return ""
    d = d.replace("Z", "+00:00")
    dt = datetime.fromisoformat(d) if "T" in d else datetime.fromisoformat(d + "T00:00:00+00:00")
    return format_datetime(dt.astimezone(timezone.utc))


def kw_re(words):
    return re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(w) for w in words) + r")(?![A-Za-z0-9])", re.I)


def threads_for(ds):
    page = f"/datasets/{ds['id']}.html"
    rx = kw_re(ds["keywords"])
    entry_pages = {f"/entries/{i}.html" for i in ds["entries"]}
    out = []
    for d in DISC:
        text = " ".join([d.get("title", ""), d.get("body", "")] + [c.get("body", "") for c in d.get("comments", [])])
        if d.get("page") == page or d.get("page") in entry_pages or (d.get("doi") and d["doi"] in ds["dois"]) or rx.search(text):
            out.append(d)
    return sorted(out, key=lambda d: d.get("updated", ""), reverse=True)


def entry_card(x):
    return (f'<article class="entry"><h3><a href="/entries/{e(x["id"])}.html">{e(x["title"])}</a></h3>'
            f'<div class="meta"><span class="pill st-{e(x["status"])}">{e(x["status_label"])}</span>'
            f'<span class="pill type">{e(x["type"])}</span><span class="pill sig">Significance: {e(x["significance"])}</span>'
            f'<span>Reported {e(x["reported"])}</span></div><p style="margin:8px 0 0">{e(x["summary"])}</p></article>')


def thread_card(d):
    n = len(d.get("comments", []))
    label = d.get("label") or d.get("title")
    href = d.get("page") or d.get("url")
    last = (d.get("comments") or [{}])[-1].get("body") or d.get("body", "")
    return (f'<article class="entry"><h3><a href="{e(href)}">{e(label)}</a></h3>'
            f'<div class="meta"><span>{n} comment{"" if n == 1 else "s"}</span><span>updated {e(d.get("updated", "")[:10])}</span>'
            f'<a href="{e(d["url"])}">on GitHub</a></div><p style="margin:8px 0 0">{e(last[:240])}{"…" if len(last) > 240 else ""}</p></article>')


def page(title, desc, body):
    return HEAD.replace("%TITLE%", e(title)).replace("%DESC%", e(desc)) + "\n<main><div class=\"wrap\">\n" + body + "\n</div></main>\n" + FOOT


def rss(title, link, desc, items):
    parts = [f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{e(title)}</title><link>{e(link)}</link>'
             f'<description>{e(desc)}</description><language>en</language>']
    for it in items:
        parts.append(f'<item><title>{e(it["title"])}</title><link>{e(it["link"])}</link><guid isPermaLink="false">{e(it["guid"])}</guid>'
                     f'<pubDate>{rfc822(it["date"])}</pubDate><description>{e(it["desc"])}</description></item>')
    parts.append("</channel></rss>\n")
    return "".join(parts)


def entry_item(x):
    return dict(title=f'[{x["status_label"]}] {x["title"]}', link=f'{SITE}/entries/{x["id"]}.html',
                guid=f'entry:{x["id"]}:{x["status_label"]}', date=x["reported"], desc=x["summary"])


def thread_item(d):
    n = len(d.get("comments", []))
    return dict(title=f'Discussion: {d.get("label") or d["title"]} ({n} comment{"" if n == 1 else "s"})',
                link=SITE + d["page"] if d.get("page") else d["url"], guid=f'disc:{d["number"]}:{n}',
                date=d.get("updated", ""), desc=((d.get("comments") or [{}])[-1].get("body") or d.get("body", ""))[:400])


index_rows, public = [], []
for ds in DS["datasets"]:
    ents = [ENTRIES[i] for i in ds["entries"] if i in ENTRIES]
    thr = threads_for(ds)
    public.append(dict(id=ds["id"], name=ds["name"], full_name=ds["full_name"], kind=ds["kind"], producer=ds["producer"],
                       version=ds["version"], coverage=ds["coverage"], keywords=ds["keywords"], dois=ds["dois"],
                       entries=ds["entries"], threads=len(thr), url=f'/datasets/{ds["id"]}.html'))
    links = "".join(f'<li><a href="{e(u)}">{e(t)}</a></li>' for t, u in ds["links"])
    if ds.get("known_issues"):
        ki = f'<a href="{e(ds["known_issues"])}">{e(ds.get("known_issues_label", "Official known-issues page"))}</a>'
        if ds.get("known_issues_note"):
            ki += f'<div class="meta" style="margin-top:4px">{e(ds["known_issues_note"])}</div>'
    else:
        ki = e(ds.get("known_issues_note", "None found."))
    dois = " ".join(f'<a href="/doi.html?doi={e(d)}">doi:{e(d)}</a>' for d in ds["dois"]) or "—"
    contact = ds["contact"]
    contact_html = (f'<a href="{e(contact)}">{e(contact)}</a>' if contact.startswith("http") else
                    re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', e(contact)))
    body = f"""<p class="meta"><a href="/datasets/">← All datasets</a></p>
<h1>{e(ds['name'])}</h1>
<div class="meta"><span class="pill type">{e(ds['kind'])}</span><span>{e(ds['producer'])}</span></div>
<p class="lede" style="margin-top:12px">{e(ds['full_name'])}. {e(ds['about'])}</p>
<table class="facts">
<tr><th>Current version</th><td>{e(ds['version'])}</td></tr>
<tr><th>Coverage</th><td>{e(ds['coverage'])}</td></tr>
<tr><th>Variables</th><td>{e(ds['variables'])}</td></tr>
<tr><th>Known issues</th><td>{ki}</td></tr>
<tr><th>Official pages</th><td><ul style="margin:0;padding-left:18px">{links}</ul></td></tr>
<tr><th>Dataset DOI</th><td>{dois}</td></tr>
<tr><th>Report a problem to the producer</th><td>{contact_html}</td></tr>
</table>
<p class="meta" style="display:block">Facts checked against the producer's pages on {e(DS['checked'])}. Something out of date? <a href="/report.html?kind=comment&entry={e(ds['name'])}">Tell us</a>. ·
<a href="/datasets/{e(ds['id'])}.xml">RSS feed for this dataset</a> (new entries and discussions)</p>
<h2>In the register ({len(ents)})</h2>
{''.join(entry_card(x) for x in ents) or '<p class="empty">No public register entries for this dataset yet.</p>'}
<h2>Discussions that mention {e(ds['name'])} ({len(thr)})</h2>
{''.join(thread_card(d) for d in thr) or '<p class="empty">No discussions yet. Ask below, or open the page for a specific paper by its <a href="/doi.html">DOI</a>.</p>'}
{GISCUS.replace('<h2>Discussion</h2>', '<h2>Ask about ' + e(ds['name']) + '</h2>')}"""
    (OUT / f"{ds['id']}.html").write_text(page(f"{ds['name']} — Climate Errata", f"{ds['full_name']}: versions, known issues, register entries and discussion.", body))
    items = sorted([entry_item(x) for x in ents] + [thread_item(d) for d in thr], key=lambda i: i["date"], reverse=True)[:50]
    (OUT / f"{ds['id']}.xml").write_text(rss(f"Climate Errata: {ds['name']}", f"{SITE}/datasets/{ds['id']}.html",
                                            f"Register entries and discussions about {ds['full_name']}", items))
    index_rows.append(f'<article class="entry"><h3><a href="/datasets/{e(ds["id"])}.html">{e(ds["name"])}</a></h3>'
                      f'<div class="meta"><span class="pill type">{e(ds["kind"])}</span><span>{e(ds["producer"])}</span></div>'
                      f'<p style="margin:8px 0 0">{e(ds["coverage"])}. Version: {e(ds["version"])}.</p>'
                      f'<div class="meta" style="margin-top:6px"><span>{len(ents)} register entr{"y" if len(ents) == 1 else "ies"}</span>'
                      f'<span>{len(thr)} discussion{"" if len(thr) == 1 else "s"}</span>'
                      f'<span>{"known-issues page linked" if ds.get("known_issues") else "no official known-issues page found"}</span>'
                      f'<a href="/datasets/{e(ds["id"])}.xml">RSS</a></div></article>')

idx = f"""<h1>Datasets</h1>
<p class="lede">One page per widely used climate dataset: current version, the producer's own known-issues page, our register entries, and community discussion. Ask about a dataset on its page, or follow it by RSS to hear about new entries and discussions.</p>
<p class="meta" style="display:block">Missing a dataset you use? <a href="/report.html?kind=comment">Suggest it</a>. Facts checked against producers' pages on {e(DS['checked'])}.</p>
{''.join(index_rows)}"""
(OUT / "index.html").write_text(page("Datasets — Climate Errata", "Pages for widely used climate datasets: versions, known issues, register entries and discussion.", idx))
json.dump(public, open(OUT / "datasets.json", "w"), indent=1, ensure_ascii=False)

all_items = sorted([entry_item(x) for x in ENTRIES.values()], key=lambda i: i["date"], reverse=True)[:100]
(ROOT / "feed.xml").write_text(rss("Climate Errata: register", SITE + "/", "New and updated entries in the Climate Errata register", all_items))
print(len(DS["datasets"]), "dataset pages;", len(DISC), "discussions considered")
