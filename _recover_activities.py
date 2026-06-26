#!/usr/bin/env python3
# 旧ブログ全記事をWaybackから回収。引数: start end outfile （スライス並列用）
import urllib.request, urllib.parse, re, ssl, json, sys, time, html as H
ctx = ssl._create_unverified_context()

def wb(ts, u):
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(f"http://web.archive.org/web/{ts}id_/{u}",
                                         headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=50, context=ctx).read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise last

def category(title, url):
    t = (title + " " + url).lower()
    def has(*ks): return any(k.lower() in t for k in ks)
    if has("nhk","abc","mbs","ytv","読売","朝日新聞","神戸新聞","日経","産経","毎日新聞","テレビ","ラジオ","出演","掲載","放送","情熱大陸","イッテq","図鑑","新聞","press","efe","共同通信","両丹","高知新聞","ラジオ"):
        return "メディア"
    if has("ペルー","peru","アルパカ","台湾","花蓮","海外","世界最大","シンガポール","ドバイ","南米","環島"):
        return "海外プロジェクト"
    if has("コラボ","企業","コープ","coop","阪急","キューピー","キユーピー","パナホーム","ベアレン","不動産","周年","adidas","アディダス","サッポロ","ニッカ","karhu","カルフ","pets-for-life"):
        return "企業コラボ"
    if has("講演","小学校","中学校","高校","大学","支援学校","授業","教育","学校","生徒","児童","pta","学院","研究集会","教育研究"):
        return "講演・教育"
    if has("復興","震災","気仙沼","東北","3-11","3.11"):
        return "震災復興"
    if has("プロギング","ゴミ拾い","plogging","ウォーク","walk","ラン","run","参加者募集","開催","イベント","体験","アートウォーク","ツアー"):
        return "イベント"
    return "お知らせ"

TRAIL = re.compile(r"言語切り替え|Previous project|Next project|Share\b|Copyright|©|最新情報\s*UPDATES|イチオシ作品|GPS RUNと食|関連記事|コメントを残す|前の記事|次の記事")

def extract(raw):
    m = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = H.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""
    title = re.split(r"\s*[–—\-|]\s*GPS RUN", title)[0].strip()
    txt = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = H.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    if "Search site..." in txt:
        region = txt.split("Search site...")[-1]
    elif title and txt.rfind(title) > 0:
        region = txt[txt.rfind(title):]
    else:
        region = txt
    region = region.strip()
    if title and region.startswith(title):
        region = region[len(title):]
    region = re.sub(r"^\s*[–—\-|][^】！。]*?(?:志水 直樹|-->)\s*", "", region)
    region = re.sub(r"^\s*\d{4}年\d{1,2}月\d{1,2}日\s*", "", region)
    txt = TRAIL.split(region)[0].strip()
    imgs = []
    for i in re.findall(r'(?:src|data-orig-file|data-large-file)="([^"]+)"', raw):
        if "wp-content/uploads" not in i: continue
        i = urllib.parse.urljoin("http://gps-run.com/", i).replace("//wp-content", "/wp-content")
        b = re.sub(r"-\d+x\d+(?=\.\w+$)", "", i)
        if b not in imgs and "logo" not in b.lower() and not b.endswith(".svg"):
            imgs.append(b)
    return title, txt, imgs[:10]

def load_rows():
    rows = []
    for l in open("old_urls.txt", encoding="utf-8"):
        ts, u = l.strip().split("\t")
        p = urllib.parse.urlparse(u).path
        segs = [s for s in p.split("/") if s]
        if not (segs and re.match(r"20\d\d", segs[0])): continue
        m = re.match(r"/(\d{4})/(\d{2})/(\d{2})/", p)
        if not m: continue
        rows.append((ts, u, f"{m.group(1)}-{m.group(2)}-{m.group(3)}", segs[-1]))
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows

def main():
    rows = load_rows()
    start, end, outfile = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    chunk = rows[start:end]
    out = []
    for n, (ts, u, date, slug) in enumerate(chunk, 1):
        try:
            raw = wb(ts, urllib.parse.quote(u, safe=":/%"))
            title, body, imgs = extract(raw)
            if not title:
                title = H.unescape(urllib.parse.unquote(slug)).replace("-", " ")
            slugc = f"act-{date.replace('-','')}-{start + n}"
            out.append({"date": date, "title": title,
                        "category": category(title, body + " " + urllib.parse.unquote(u)),
                        "excerpt": body[:150], "body": body[:2500],
                        "images": imgs, "imgTs": ts, "oldUrl": u, "slug": slugc})
        except Exception as e:
            out.append({"date": date, "title": H.unescape(urllib.parse.unquote(slug)).replace("-", " "),
                        "category": "お知らせ", "excerpt": "", "body": "", "images": [],
                        "imgTs": ts, "oldUrl": u, "slug": "act-" + str(start + n), "error": str(e)[:40]})
        time.sleep(0.4)
        if n % 10 == 0:
            print(f"[{outfile}] {n}/{len(chunk)}", flush=True)
    json.dump(out, open(outfile, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[{outfile}] DONE {len(out)}件 / 本文 {sum(1 for r in out if r.get('body'))}", flush=True)

if __name__ == "__main__":
    main()
