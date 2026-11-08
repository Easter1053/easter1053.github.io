#!/usr/bin/env python3
"""THE MIHAK Daily site builder.

Usage:
  python3 tools/build.py issues/YYYY-MM-DD/issue.json            # build site pages
  python3 tools/build.py issues/YYYY-MM-DD/issue.json --artifact OUT.html
      # also write a single self-contained page (fonts as data URIs) for the claude.ai artifact

Writes issues/<iso>/index.html, index.html (latest issue), archive/index.html, issues/issues.json.
issue.json keys: iso, weekday, no, label(optional), read{h,buzz,lede,bx[str],ba[str],points[[k,v]],card}, picks[{cat,type,h,why}],
cats[{en,ko,items[{side,type,h,s,src,links[[name,url]],week?}],note?}], memo[str].
"""
import base64, html, json, os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://themihak.com"
IG = "https://www.instagram.com/mihak.branding/"
CONSULT = "https://forms.gle/mGsi1SWmPyqKrdEK9"
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&display=swap">'
e = html.escape


def date_label(d):
    s = d["iso"].replace("-", ".") + f' ({d["weekday"]}) · {d["no"]}'
    if d.get("label"):
        s += " " + d["label"]
    return s


def body(d):
    cats = d["cats"]
    toc = "".join(
        f'<a class="toc-item" href="#c{i+1}"><span class="toc-en">{c["en"]}</span><span class="toc-ko">{c["ko"]} <b>{len(c["items"])}</b></span></a>'
        for i, c in enumerate(cats))
    picks = "".join(
        f'<li class="pick"><span class="pick-no">{i+1:02d}</span><div class="pick-body"><span class="chip">{e(p["cat"])} · {e(p["type"])}</span><p class="pick-h">{e(p["h"])}</p><p class="pick-why">{e(p["why"])}</p></div></li>'
        for i, p in enumerate(d["picks"]))
    sec = ""
    for i, c in enumerate(cats):
        items = ""
        for j, it in enumerate(c["items"]):
            links = '<span class="sep">/</span>'.join(
                f'<a href="{e(u)}" target="_blank" rel="noopener">{e(n)} <span class="arr">→</span></a>' for n, u in it["links"])
            dom = it["side"] == "국내"
            side = f'<span class="side {"dom" if dom else "glo"}">{"DOMESTIC" if dom else "INTERNATIONAL"}</span>'
            wid = '<span class="wid">◆ 1주일 화제</span>' if it.get("week") else ""
            items += (f'<article class="item"><span class="item-no">{j+1:02d}</span><div class="item-body"><div class="item-meta">{side}'
                      f'<span class="type">{e(it["type"])}</span>{wid}</div><h3 class="item-h">{e(it["h"])}</h3><p class="item-s">{e(it["s"])}</p>'
                      f'<div class="item-src"><span>{e(it["src"])}</span><span class="links">{links}</span></div></div></article>')
        n = len(c["items"])
        sub = f"{n} STORIES" + (" · 5개 미만" if n < 5 else "")
        note = f'<div class="note"><p class="note-k">EDITOR\'S NOTE</p><p>{e(c["note"])}</p></div>' if c.get("note") else ""
        sec += (f'<section class="cat" id="c{i+1}"><div class="wrap"><header class="cat-head"><span class="cat-idx">{i+1:02d}</span><div>'
                f'<span class="cat-en">{c["en"]}</span><span class="cat-sub"><b>{c["ko"]}</b>{sub}</span></div></header>{items}{note}</div></section>')
    r = d["read"]
    buzz = f'<p class="buzz">◆ 선정 이유 · {e(r["buzz"])}</p>' if r.get("buzz") else ""
    bx = (f'<div class="ba bx"><p class="ba-k">LIVE BX</p>' + "".join(f"<p>{e(x)}</p>" for x in r["bx"]) + '</div>') if r.get("bx") else ""
    ba = (f'<div class="ba"><p class="ba-k">BRANDING AESTHETICS</p>' + "".join(f"<p>{e(x)}</p>" for x in r["ba"]) + '</div>') if r.get("ba") else ""
    pts = "".join(f"<li><b>{e(a)}</b> {e(b)}</li>" for a, b in r["points"])
    memo = "".join(f"<li>{e(m)}</li>" for m in d["memo"])
    total = sum(len(c["items"]) for c in cats)
    return f'''<header class="mast"><div class="wrap">
<div class="folio"><span class="cap">Aesthetic Branding Magazine</span><a href="{IG}" target="_blank" rel="noopener">@mihak.branding</a></div>
<p class="date"><i>|</i>{e(date_label(d))}<i>|</i></p>
<div class="logo"><span class="the">THE</span><span class="mk">MIHAK</span></div>
<p class="tagline">아트디렉터의 미학 브랜딩 매거진 · Daily</p>
</div></header>
<nav class="toc" aria-label="카테고리"><div class="wrap">{toc}</div></nav>
<section class="read"><div class="wrap">
<p class="kick">THE READ · 오늘의 해석</p>
<h2>{e(r["h"])}</h2>
{buzz}<p class="lab">WHAT HAPPENED</p>
<p class="lede">{e(r["lede"])}</p>
{bx}{ba}<ol>{pts}</ol>
<p class="card">{e(r["card"])}</p>
</div></section>
<section class="picks"><div class="wrap">
<div class="sec-head"><p class="bar">EDITOR'S SELECTION</p><h2>Today's <em>Picks</em></h2><p>오늘 가장 이슈가 된 브랜딩 뉴스 다섯</p></div>
<ol>{picks}</ol>
</div></section>
<div class="band"><div class="wrap"><div class="b-t">The <em>Briefing</em></div><span class="cap">{total} stories · five categories</span></div></div>
{sec}
<section class="memo"><div class="wrap"><span class="cap">Editor's Memo</span><p class="m-t">Before you go</p><ul>{memo}</ul></div></section>
{footer()}'''


def footer():
    return f'''<footer class="foot"><div class="wrap">
<div class="logo"><span class="the">THE</span><span class="mk">MIHAK</span></div>
<p class="tagline">브랜딩은 미학에서 시작된다</p>
<div class="rule"></div>
<a class="ig" href="{IG}" target="_blank" rel="noopener">@mihak.branding</a>
<p class="small">모든 소식은 원문 기사의 날짜와 내용을 확인해 정리했습니다.<br>원문 링크는 각 항목 아래에 있습니다.</p>
</div></footer>'''


def topnav(prefix):
    return f'''<div class="topnav"><div class="wrap"><a class="brand" href="{prefix}">THE MIHAK</a><nav>
<a href="{prefix}">Daily</a><a href="{prefix}archive/">Archive</a><a href="{CONSULT}" target="_blank" rel="noopener">상담 신청</a><a href="{IG}" target="_blank" rel="noopener">Instagram</a></nav></div></div>'''


def page(title, desc, inner, prefix):
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:site_name" content="THE MIHAK">
{FONTS}
<style>@font-face{{font-family:'Pretendard';src:url('{prefix}assets/fonts/PretendardVariable.woff2') format('woff2');font-weight:45 920;font-display:swap}}</style>
<link rel="stylesheet" href="{prefix}assets/mihak.css">
</head>
<body>
{topnav(prefix)}
{inner}
</body>
</html>
'''


def all_issues():
    out = []
    for p in glob.glob(os.path.join(ROOT, "issues", "*", "issue.json")):
        d = json.load(open(p, encoding="utf-8"))
        out.append(d)
    return sorted(out, key=lambda x: x["iso"], reverse=True)


def build(issue_path, artifact=None):
    d = json.load(open(issue_path, encoding="utf-8"))
    title = f'더 미학 데일리 {d["iso"].replace("-", ".")}'
    desc = "THE READ · " + d["read"]["h"]
    inner = body(d)
    os.makedirs(os.path.join(ROOT, "issues", d["iso"]), exist_ok=True)
    open(os.path.join(ROOT, "issues", d["iso"], "index.html"), "w", encoding="utf-8").write(page(title, desc, inner, "../../"))
    issues = all_issues()
    latest = issues[0]
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(
        page("THE MIHAK — 더 미학 데일리", "아트디렉터의 미학 브랜딩 매거진. 매일 아침 패션·뷰티·엔터·아트·미식 브랜딩 뉴스와 THE READ.", body(latest), ""))
    rows = "".join(
        f'<li><a href="../issues/{x["iso"]}/"><span class="d">{x["iso"].replace("-", ".")}<br>{e(x["no"])}</span>'
        f'<span class="t">{e(x["read"]["h"])}<span class="s">{" · ".join(e(p["h"]) for p in x["picks"][:3])}</span></span></a></li>'
        for x in issues)
    arch = f'<section class="arch"><div class="wrap"><h1>Archive</h1><p class="lead">지난 데일리 뉴스와 THE READ</p><ul>{rows}</ul></div></section>{footer()}'
    os.makedirs(os.path.join(ROOT, "archive"), exist_ok=True)
    open(os.path.join(ROOT, "archive", "index.html"), "w", encoding="utf-8").write(page("Archive — THE MIHAK", "더 미학 데일리 지난호", arch, "../"))
    json.dump([{"iso": x["iso"], "no": x["no"], "read": x["read"]["h"]} for x in issues],
              open(os.path.join(ROOT, "issues", "issues.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if artifact:
        font = base64.b64encode(open(os.path.join(ROOT, "assets", "fonts", "PretendardVariable.woff2"), "rb").read()).decode()
        css = open(os.path.join(ROOT, "assets", "mihak.css"), encoding="utf-8").read()
        out = (f'<title>더 미학 데일리</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{FONTS}\n<style>\n'
               f"@font-face{{font-family:'Pretendard';src:url(data:font/woff2;base64,{font}) format('woff2');font-weight:45 920;font-display:swap}}\n"
               f'{css}\n</style>\n{inner}\n')
        open(artifact, "w", encoding="utf-8").write(out)
    print("built", d["iso"], "issues:", len(issues))


if __name__ == "__main__":
    a = sys.argv[1:]
    art = a[a.index("--artifact") + 1] if "--artifact" in a else None
    build(a[0], art)
