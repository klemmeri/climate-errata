"""Export the repo's GitHub Discussions to discussions.json for the site search page.

Run by .github/workflows/export-discussions.yml (needs GITHUB_TOKEN with discussions: read).
Keeps the old 'generated' stamp when nothing changed, so the workflow commits only real changes.
"""
import json, os, re, pathlib, urllib.request, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
OWNER, NAME = os.environ.get("REPO", "klemmeri/climate-errata").split("/")
TOKEN = os.environ["GITHUB_TOKEN"]
SITE = "https://climateerrata.org"

Q = """query($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){
 discussions(first:50,after:$after,orderBy:{field:UPDATED_AT,direction:DESC}){pageInfo{hasNextPage endCursor}
  nodes{number title url body createdAt updatedAt category{name} author{login} isAnswered
   comments(first:100){nodes{body createdAt isAnswer author{login}
    replies(first:50){nodes{body createdAt author{login}}}}}}}}}"""

def gql(variables):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": Q, "variables": variables}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req, timeout=60))
    if "errors" in out:
        raise SystemExit(out["errors"])
    return out["data"]["repository"]["discussions"]

def clean(t, n=4000):
    t = re.sub(r"<!--.*?-->", " ", t or "", flags=re.S)
    t = re.sub(r"https://(climate-errata\.netlify\.app|(www\.)?climateerrata\.org)\S*", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:n]

entries = {e["id"]: e["title"] for e in json.load(open(ROOT / "entries.json"))}
datasets = {d["id"]: d["name"] for d in json.load(open(ROOT / "data/datasets.json"))["datasets"]}
items, after = [], None
while True:
    d = gql({"owner": OWNER, "name": NAME, "after": after})
    for n in d["nodes"]:
        title = n["title"].strip()
        rec = {"number": n["number"], "title": title, "url": n["url"], "category": n["category"]["name"],
               "author": (n["author"] or {}).get("login"), "created": n["createdAt"], "updated": n["updatedAt"],
               "answered": n["isAnswered"], "body": clean(n["body"])}
        m = re.match(r"^doi:(10\.\S+)$", title, re.I)
        p = re.match(r"^/?(entries/([a-z0-9-]+)\.html)$", title)
        q = re.match(r"^/?(datasets/([a-z0-9-]+)\.html)$", title)
        if m:
            rec["doi"] = m.group(1).lower()
            rec["page"] = f"/doi.html?doi={rec['doi']}"
            rec["label"] = f"Discussion of doi:{rec['doi']}"
        elif p:
            rec["page"] = "/" + p.group(1)
            rec["label"] = "Discussion: " + entries.get(p.group(2), p.group(2))
        elif q:
            rec["page"] = "/" + q.group(1)
            rec["label"] = "Questions about " + datasets.get(q.group(2), q.group(2))
        comments = []
        for c in n["comments"]["nodes"]:
            comments.append({"author": (c["author"] or {}).get("login"), "created": c["createdAt"],
                             "answer": c["isAnswer"], "body": clean(c["body"], 2000)})
            for r in c["replies"]["nodes"]:
                comments.append({"author": (r["author"] or {}).get("login"), "created": r["createdAt"],
                                 "body": clean(r["body"], 2000)})
        rec["comments"] = comments
        items.append(rec)
    if not d["pageInfo"]["hasNextPage"]:
        break
    after = d["pageInfo"]["endCursor"]

path = ROOT / "discussions.json"
old = json.load(open(path)) if path.exists() else {}
stamp = old.get("generated") if old.get("discussions") == items else \
    datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump({"generated": stamp, "discussions": items}, open(path, "w"), indent=1, ensure_ascii=False)
print(len(items), "discussions;", "unchanged" if stamp == old.get("generated") else "updated")
