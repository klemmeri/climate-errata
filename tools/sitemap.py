"""Write sitemap.xml and robots.txt for climateerrata.org.

lastmod = today for pages that differ from the last commit (or are new),
otherwise the date of the last commit that touched the page.
"""
import datetime, subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://climateerrata.org"
SKIP = {"report-thanks.html", "google8b07c37c4908ddfe.html"}
TODAY = datetime.date.today().isoformat()


def _git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()


def lastmod(rel):
    if _git("status", "--porcelain", "--", rel):
        return TODAY
    d = _git("log", "-1", "--format=%cs", "--", rel)
    return d or TODAY


def url(rel):
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return f"{BASE}/{rel[:-len('index.html')]}"
    return f"{BASE}/{rel}"


pages = sorted(
    p.relative_to(ROOT).as_posix()
    for p in ROOT.rglob("*.html")
    if not any(part in {".git", "tools", "data", "node_modules"} for part in p.relative_to(ROOT).parts)
    and p.name not in SKIP
)
prio = lambda r: "1.0" if r == "index.html" else "0.8" if r.startswith("entries/") else "0.6"
xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for r in pages:
    xml.append(f"  <url><loc>{url(r)}</loc><lastmod>{lastmod(r)}</lastmod><priority>{prio(r)}</priority></url>")
xml.append("</urlset>")
(ROOT / "sitemap.xml").write_text("\n".join(xml) + "\n")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
print(len(pages), "pages in sitemap.xml")


# Page list for stats.html (path -> page title), regenerated on every build
import json, html as _html
_sp = []
for rel in pages:
    t = (ROOT / rel).read_text(errors="ignore")
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    title = _html.unescape(m.group(1)).replace(" — Climate Errata", "").strip() if m else rel
    path = "/" if rel == "index.html" else ("/" + rel[:-len("index.html")] if rel.endswith("/index.html") else "/" + rel)
    _sp.append({"path": path, "title": title})
(ROOT / "stats_pages.json").write_text(json.dumps(_sp, ensure_ascii=False, indent=0) + "\n")
