#!/usr/bin/env python3
# activities_p*.json をマージ → activities.json / news.html / news/<slug>.html 群 / _redirects.json を生成
# パスは %P% プレースホルダ（記事=../ / index=空）。画像は Wayback の最寄りスナップショット形式。
import json, glob, re, html as H, os, urllib.parse

BASE = "https://www.gps-run.com"

def merge():
    allr = []
    for f in sorted(glob.glob("activities_p*.json")):
        allr += json.load(open(f, encoding="utf-8"))
    seen, acts = set(), []
    for r in sorted(allr, key=lambda x: x["date"], reverse=True):
        if r["oldUrl"] in seen: continue
        seen.add(r["oldUrl"]); acts.append(r)
    used = {}
    for i, r in enumerate(acts):
        s = r.get("slug") or f"act-{i}"
        if s in used:
            used[s] += 1; s = f"{s}-{used[s]}"
        else:
            used[s] = 0
        r["slug"] = s
    json.dump(acts, open("activities.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return acts

def imgurl(img):
    return f"https://web.archive.org/web/im_/{img}"

NAV = '''  <header id="header">
    <a href="%P%index.html" class="logo"><img src="%P%3131553a-7a69-4460-b31b-8082b39b5b1c.jpeg" alt="NAOKI SHIMIZU" class="logo-img"><div class="logo-text">GPS <span>RUNNER</span></div></a>
    <nav>
      <a href="%P%index.html">HOME</a>
      <a href="%P%works.html">WORKS</a>
      <a href="%P%cases.html">CASE</a>
      <a href="%P%news.html"%NEWSACT%>NEWS</a>
      <a href="%P%profile.html">PROFILE</a>
      <a href="%P%offer.html">OFFER</a>
      <a href="%P%contact.html">CONTACT</a>
      <a href="%P%support.html" class="nav-cta">SUPPORT</a>
    </nav>
    <button class="hamburger" id="hamburger"><span></span><span></span><span></span></button>
  </header>
  <div class="mobile-nav" id="mobileNav">
    <a href="%P%index.html">HOME</a><a href="%P%works.html">WORKS</a><a href="%P%cases.html">CASE</a>
    <a href="%P%news.html">NEWS</a><a href="%P%profile.html">PROFILE</a><a href="%P%global.html">GLOBAL</a>
    <a href="%P%offer.html">OFFER</a><a href="%P%special.html">PROJECT</a><a href="%P%contact.html">CONTACT</a><a href="%P%support.html">SUPPORT</a>
  </div>'''

FOOT = '''  <footer><p><a href="%P%index.html">GPS RUNNER</a> &middot; &copy; 2026 Naoki Shimizu. &middot; <a href="%P%tokushoho.html">特定商取引法に基づく表記</a> &middot; <a href="%P%privacy.html">プライバシーポリシー</a></p></footer>
  <script>
    window.addEventListener('scroll',function(){document.getElementById('header').classList.toggle('scrolled',window.scrollY>50)});
    document.getElementById('hamburger').addEventListener('click',function(){this.classList.toggle('active');document.getElementById('mobileNav').classList.toggle('active')});
  </script>
  <script src="%P%chatbot.js" data-knowledge="%P%knowledge.json" data-primary-color="#FFE500" data-greeting="こんにちは！GPS RUNNER 志水直樹へのご質問はお気軽にどうぞ"></script>\n  <script src="/theme.js"></script>'''

IMGERR = "this.closest('figure,a').style.display='none'"

def paragraphs(body):
    sents = re.split(r'(?<=[。！？!?])\s+', body)
    paras, buf = [], ""
    for s in sents:
        buf += s
        if len(buf) > 55:
            paras.append(buf); buf = ""
    if buf.strip(): paras.append(buf)
    return "".join(f"<p>{H.escape(p)}</p>" for p in paras) or f"<p>{H.escape(body)}</p>"

def gen_article(r):
    P = "../"
    canon = f"{BASE}/news/{r['slug']}.html"
    desc = H.escape((r["excerpt"] or r["title"])[:150])
    ttl = H.escape(r["title"])
    og_img = f"{BASE}/{r['images'][0]}" if r["images"] else f"{BASE}/images/ogp.jpg"
    gallery = ""
    if r["images"]:
        cells = "".join(
            f'<a href="%P%{im}" target="_blank" rel="noopener"><img src="%P%{im}" alt="{ttl} 写真{i+1}" loading="lazy" onerror="{IMGERR}"></a>'
            for i, im in enumerate(r["images"]))
        gallery = f'<div class="article-gallery">{cells}</div>'
    videos = ""
    if r.get("videos"):
        vs = "".join(f'<div class="article-video"><iframe src="https://www.youtube.com/embed/{v}" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>' for v in r["videos"])
        videos = f'<p class="video-label">▶ 動画</p>{vs}'
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": r["title"],
          "datePublished": r["date"], "inLanguage": "ja", "articleSection": r["category"],
          "author": {"@type": "Person", "@id": f"{BASE}/#person", "name": "志水直樹"},
          "publisher": {"@type": "Person", "name": "志水直樹"}, "mainEntityOfPage": canon}
    if r["images"]: ld["image"] = og_img
    bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "HOME", "item": f"{BASE}/"},
        {"@type": "ListItem", "position": 2, "name": "NEWS・活動", "item": f"{BASE}/news.html"},
        {"@type": "ListItem", "position": 3, "name": r["title"]}]}
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{ttl} | GPS RUNNER 志水直樹</title>
  <meta name="description" content="{desc}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="%P%archive.css">\n  <script>try{{if(localStorage.getItem("gpsrun-theme")==="light")document.documentElement.setAttribute("data-theme","light")}}catch(e){{}}</script>\n  <link rel="stylesheet" href="/theme.css">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="GPS RUNNER 志水直樹">
  <meta property="og:title" content="{ttl}">
  <meta property="og:description" content="{desc}">
  <meta property="og:url" content="{canon}">
  <meta property="og:image" content="{og_img}">
  <meta property="og:locale" content="ja_JP">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{ttl}">
  <meta name="twitter:image" content="{og_img}">
  <link rel="canonical" href="{canon}">
  <link rel="icon" href="%P%favicon.svg" type="image/svg+xml">
  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
  <script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>
</head>
<body>
{NAV.replace("%NEWSACT%", ' class="active"')}
  <div class="page-hero">
    <div class="breadcrumb"><a href="%P%index.html">HOME</a> / <a href="%P%news.html">NEWS・活動</a> / {r["category"]}</div>
    <div class="a-meta"><span class="a-tag">{r["category"]}</span><span class="a-date">{r["date"].replace("-",".")}</span></div>
    <h1>{ttl}</h1>
  </div>
  <section>
    <article class="article">
      <div class="article-body">{paragraphs(r["body"]) if r["body"] else "<p>（本文は移行準備中です）</p>"}</div>
      {videos}
      {gallery}
      <div class="backrow">
        <a href="%P%news.html" class="btn btn-outline">← NEWS・活動一覧へ</a>
        <a href="%P%contact.html" class="btn btn-primary">お問い合せ</a>
      </div>
    </article>
  </section>
{FOOT}
</body>
</html>'''
    return html.replace("%P%", P)

def gen_index(acts):
    P = ""
    slim = [{"d": r["date"], "t": r["title"], "c": r["category"], "e": r["excerpt"][:90],
             "s": r["slug"], "img": (r["images"][0] if r["images"] else "")} for r in acts]
    cats = ["すべて", "企業コラボ", "講演・教育", "メディア", "イベント", "海外プロジェクト", "震災復興", "お知らせ"]
    years = sorted({r["date"][:4] for r in acts}, reverse=True)
    chips_c = "".join(f'<button class="chip cat{" active" if c=="すべて" else ""}" data-c="{c}">{c}</button>' for c in cats)
    chips_y = '<button class="chip yr active" data-y="all">全期間</button>' + "".join(f'<button class="chip yr" data-y="{y}">{y}</button>' for y in years)
    data_js = json.dumps(slim, ensure_ascii=False)
    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NEWS・活動アーカイブ | GPS RUNNER 志水直樹</title>
  <meta name="description" content="GPSランナー志水直樹の活動アーカイブ。企業コラボ・学校/自治体講演・イベント・メディア出演・海外プロジェクトなど、2019年からの全活動を年・カテゴリで絞り込んで閲覧できます。">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="%P%archive.css">\n  <script>try{{if(localStorage.getItem("gpsrun-theme")==="light")document.documentElement.setAttribute("data-theme","light")}}catch(e){{}}</script>\n  <link rel="stylesheet" href="/theme.css">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="GPS RUNNER 志水直樹">
  <meta property="og:title" content="NEWS・活動アーカイブ | GPS RUNNER 志水直樹">
  <meta property="og:description" content="2019年からの全活動を年・カテゴリで絞り込んで閲覧。企業コラボ・講演・イベント・メディア出演など。">
  <meta property="og:url" content="{BASE}/news.html">
  <meta property="og:image" content="{BASE}/images/ogp.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{BASE}/news.html">
  <link rel="icon" href="%P%favicon.svg" type="image/svg+xml">
</head>
<body>
{NAV.replace("%NEWSACT%", ' class="active"')}
  <div class="page-hero">
    <div class="breadcrumb"><a href="%P%index.html">HOME</a> / NEWS・活動</div>
    <p class="section-label">NEWS / ACTIVITIES</p>
    <h1>活動アーカイブ</h1>
    <p>2019年からの活動を、年・カテゴリ・キーワードで絞り込んで閲覧できます。</p>
  </div>
  <section>
    <div class="filters">
      <div class="filter-row" id="catRow">{chips_c}</div>
      <div class="filter-row" id="yrRow">{chips_y}</div>
      <div class="filter-row"><input type="search" class="search-box" id="q" placeholder="キーワードで検索（例：講演、コープ、ペルー、神戸新聞…）"></div>
    </div>
    <div class="result-count" id="count"></div>
    <div class="container"><div class="grid" id="grid"></div></div>
    <button class="loadmore" id="more" style="display:none">もっと見る</button>
  </section>
{FOOT}
  <script>
    const ACTS={data_js};
    let fc="すべて",fy="all",fq="",shown=0,STEP=24,filtered=[];
    const grid=document.getElementById('grid'),count=document.getElementById('count'),more=document.getElementById('more');
    function card(a){{
      const img=a.img?`<img src="${{a.img}}" alt="${{a.t}}" loading="lazy" onerror="this.parentNode.innerHTML='<div class=\\'card-noimg\\'>GPS RUNNER</div>'">`:`<div class="card-noimg">GPS RUNNER</div>`;
      return `<a class="card" href="news/${{a.s}}.html"><div class="card-img">${{img}}</div><div class="card-body"><div class="card-meta"><span class="card-tag">${{a.c}}</span><span class="card-date">${{a.d.replace(/-/g,'.')}}</span></div><h3>${{a.t}}</h3><p>${{a.e}}</p></div></a>`;
    }}
    function apply(){{
      filtered=ACTS.filter(a=>(fc==="すべて"||a.c===fc)&&(fy==="all"||a.d.startsWith(fy))&&(!fq||(a.t+a.e+a.c).toLowerCase().includes(fq)));
      shown=0;grid.innerHTML='';count.textContent=`${{filtered.length}} 件`;render();
    }}
    function render(){{
      const next=filtered.slice(shown,shown+STEP);
      grid.insertAdjacentHTML('beforeend',next.map(card).join(''));
      shown+=next.length;more.style.display=shown<filtered.length?'block':'none';
    }}
    document.getElementById('catRow').onclick=e=>{{if(e.target.dataset.c){{fc=e.target.dataset.c;document.querySelectorAll('.cat').forEach(b=>b.classList.toggle('active',b===e.target));apply();}}}};
    document.getElementById('yrRow').onclick=e=>{{if(e.target.dataset.y){{fy=e.target.dataset.y;document.querySelectorAll('.yr').forEach(b=>b.classList.toggle('active',b===e.target));apply();}}}};
    document.getElementById('q').oninput=e=>{{fq=e.target.value.toLowerCase().trim();apply();}};
    more.onclick=render;apply();
  </script>
</body>
</html>'''
    return html.replace("%P%", P)

def main():
    acts = merge()
    os.makedirs("news", exist_ok=True)
    for r in acts:
        open(f"news/{r['slug']}.html", "w", encoding="utf-8").write(gen_article(r))
    open("news.html", "w", encoding="utf-8").write(gen_index(acts))
    redirects = [{"source": urllib.parse.urlparse(r["oldUrl"]).path.rstrip("/"),
                  "destination": f"/news/{r['slug']}.html", "permanent": True} for r in acts]
    json.dump(redirects, open("_redirects.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"生成完了: 個別{len(acts)}ページ + news.html + 301マップ{len(redirects)}件")

if __name__ == "__main__":
    main()
