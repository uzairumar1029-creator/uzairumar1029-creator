#!/usr/bin/env python3
"""Builds PROJECT INDEX (public repos, live from the GitHub API) and HOSTED PROJECTS pages.

* projects/README.md + assets/repos/<name>.svg  <- every PUBLIC repository (private ones can never appear)
* hosted/README.md                              <- hosted/projects.json (empty list = empty state)

hosted/projects.json entry format:
  {"name": "My App", "url": "https://...", "description": "...", "tech": "React · FastAPI",
   "status": "LIVE", "thumbnail": "hosted/thumbs/my-app.png"}   # thumbnail optional (png/jpg/webp)
Only add URLs you have verified are live.
"""
import base64, glob, json, mimetypes, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from common import *  # noqa: F401,F403

ROOT = os.path.join(os.path.dirname(__file__), "..")
CFG = json.load(open(os.path.join(ROOT, "scripts", "config.json")))
USER = os.environ.get("GH_USER") or CFG["user"]
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
LANG = {"Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "C#": "#178600", "Rust": "#dea584", "Go": "#00ADD8",
        "HTML": "#e34c26", "CSS": "#563d7c", "C++": "#f34b7d", "C": "#555555", "Java": "#b07219", "Shell": "#89e051", "TSQL": "#e38c00"}


def api(url):
    h = {"User-Agent": "profile-builder", "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30).read())


def repo_card(r, idx):
    w, h = 420, 196
    name = r["name"]
    desc = r.get("description") or "No description yet."
    lang = r.get("language") or "—"
    tags = [t.upper() for t in (r.get("topics") or [])][:3]
    b = frame(w, h, 16)
    b += T(24, 38, f"{idx:02d}", 12, DM, MONO, 400, "start", 2)
    b += T(w - 24, 38, "PUBLIC", 10, DM, MONO, 400, "end", 2)
    b += T(24, 72, name if len(name) <= 26 else name[:25] + "…", 21, TX, SANS, 700)
    b += f'<rect x="24" y="84" width="38" height="2" rx="1" fill="url(#gA)"/>'
    for i, ln in enumerate(wrap(desc, 46)[:3]):
        b += T(24, 112 + i * 19, ln + ("…" if i == 2 and len(wrap(desc, 46)) > 3 else ""), 13.5, MU)
    b += f'<line x1="24" x2="{w - 24}" y1="158" y2="158" stroke="{BR}"/>'
    b += f'<circle cx="30" cy="177" r="5" fill="{LANG.get(lang, DM)}"/>' + T(42, 181, lang.upper(), 10.5, TX, MONO, 600, "start", 1.6)
    if tags:
        b += T(w - 24, 181, " · ".join(tags), 9.5, CY, MONO, 400, "end", 1.2)
    else:
        b += T(w - 24, 181, "GITHUB ↗", 10.5, DM, MONO, 400, "end", 1.6)
    write(os.path.join(ROOT, "assets", "repos", f"{name}.svg"), svg(w, h, b, "", f"{name} — public repository"))


def scrape_repos():
    """Fallback when the API is rate-limited: read the public repositories tab."""
    import html as H, re
    out, page = [], 1
    while page <= 5:
        req = urllib.request.Request(f"https://github.com/{USER}?tab=repositories&page={page}", headers={"User-Agent": "profile-builder"})
        h = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        blocks = re.split(r'<li class="[^"]*"\s+itemprop="owns"', h)[1:]
        if not blocks:
            break
        for b in blocks:
            m = re.search(r'href="/[^/"]+/([^"]+)"\s+itemprop="name codeRepository"', b)
            if not m:
                continue
            d = re.search(r'itemprop="description">\s*(.*?)\s*</p>', b, re.S)
            l = re.search(r'itemprop="programmingLanguage">([^<]*)<', b)
            out.append({"name": m.group(1), "html_url": f"https://github.com/{USER}/{m.group(1)}", "private": False,
                        "fork": "Forked from" in b, "description": H.unescape(d.group(1)) if d else "",
                        "language": H.unescape(l.group(1)) if l else None, "topics": re.findall(r'topic-tag[^>]*>\s*([^<\s][^<]*?)\s*<', b)})
        if 'rel="next"' not in h:
            break
        page += 1
    return out


def build_index():
    try:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=updated")
    except Exception as ex:  # noqa: BLE001
        print("api unavailable, using HTML fallback:", ex, file=sys.stderr)
        repos = scrape_repos()
    repos = [r for r in repos if not r.get("private") and r["name"] not in CFG["exclude_repos"]
             and (CFG.get("include_forks") or not r.get("fork"))]
    for old in glob.glob(os.path.join(ROOT, "assets", "repos", "*.svg")):
        os.remove(old)
    md = ["# PROJECT INDEX", "",
          f"Every **public** repository by [{USER}](https://github.com/{USER}), updated automatically. "
          "Public repositories and hosted projects are different things: see [hosted projects](../hosted/README.md) for live apps.", ""]
    if repos:
        md += ['<div align="center">', ""]
        for i, r in enumerate(repos, 1):
            repo_card(r, i)
            md.append(f'<a href="{r["html_url"]}"><img src="../assets/repos/{r["name"]}.svg" width="420" alt="{r["name"]} — public repository"></a>')
        md += ["", "</div>"]
    else:
        md += ["_No public repositories to show yet._"]
    md += ["", f"[All repositories on GitHub ↗](https://github.com/{USER}?tab=repositories) · [← Back to profile](../README.md)", ""]
    open(os.path.join(ROOT, "projects", "README.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"project index: {len(repos)} public repos")


def hosted_card(p, idx):
    w, h = 420, 330
    b = frame(w, h, 16) + f'<clipPath id="tc"><rect x="16" y="16" width="{w - 32}" height="150" rx="10"/></clipPath>'
    thumb = p.get("thumbnail")
    path = os.path.join(ROOT, thumb) if thumb else ""
    if path and os.path.exists(path):
        mime = mimetypes.guess_type(path)[0] or "image/png"
        data = base64.b64encode(open(path, "rb").read()).decode()
        b += f'<image x="16" y="16" width="{w - 32}" height="150" preserveAspectRatio="xMidYMid slice" clip-path="url(#tc)" href="data:{mime};base64,{data}"/>'
    else:
        b += f'<rect x="16" y="16" width="{w - 32}" height="150" rx="10" fill="{S1}" stroke="{BR}"/><rect x="16" y="16" width="{w - 32}" height="150" rx="10" fill="url(#gAd)" opacity=".12"/>'
        b += T(w / 2, 98, "PREVIEW", 11, DM, MONO, 400, "middle", 3)
    b += f'<rect x="16" y="16" width="{w - 32}" height="150" rx="10" fill="none" stroke="{BR}"/>'
    b += T(24, 202, p["name"], 21, TX, SANS, 700)
    for i, ln in enumerate(wrap(p.get("description", ""), 46)[:2]):
        b += T(24, 226 + i * 19, ln, 13.5, MU)
    b += T(24, 280, (p.get("tech") or "").upper(), 10, CY, MONO, 400, "start", 1.4)
    b += f'<line x1="24" x2="{w - 24}" y1="292" y2="292" stroke="{BR}"/>'
    b += f'<circle cx="30" cy="311" r="3.5" fill="{GR}"/>' + T(42, 315, (p.get("status") or "LIVE").upper(), 10.5, TX, MONO, 600, "start", 2)
    b += T(w - 24, 315, "VISIT PROJECT →", 10.5, CY, MONO, 600, "end", 1.6)
    slug = "".join(c if c.isalnum() else "-" for c in p["name"].lower()).strip("-")
    write(os.path.join(ROOT, "assets", "hosted", f"{slug}.svg"), svg(w, h, b, "", f"{p['name']} — hosted project"))
    return slug


def build_hosted():
    items = json.load(open(os.path.join(ROOT, "hosted", "projects.json")))
    for old in glob.glob(os.path.join(ROOT, "assets", "hosted", "*.svg")):
        os.remove(old)
    md = ["# HOSTED PROJECTS", ""]
    if not items:
        md += ['<div align="center">', "", '<img src="../assets/hosted-empty.svg" width="640" alt="No hosted projects yet">', "", "</div>", ""]
    else:
        md += ['<div align="center">', ""]
        for i, p in enumerate(items, 1):
            slug = hosted_card(p, i)
            md.append(f'<a href="{p["url"]}"><img src="../assets/hosted/{slug}.svg" width="420" alt="{p["name"]} — visit project"></a>')
        md += ["", "</div>"]
    md += ["", "Hosted projects are live deployments. Public repositories live in the [project index](../projects/README.md). · [← Back to profile](../README.md)", ""]
    open(os.path.join(ROOT, "hosted", "README.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"hosted: {len(items)} projects")


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "assets", "hosted"), exist_ok=True)
    try:
        build_index()
    except Exception as ex:  # noqa: BLE001
        print("project index skipped:", ex, file=sys.stderr)
    build_hosted()
