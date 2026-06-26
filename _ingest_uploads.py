#!/usr/bin/env python3
# ヘテムル原本の wp-content/uploads フォルダを取り込み、全記事の画像をローカル化して再生成する。
# 使い方:  python3 _ingest_uploads.py <uploadsフォルダのパス>
#   <uploadsフォルダ> は wp-content/uploads（年月フォルダ 2019.. が並ぶ階層）か、その親でもOK。
import sys, os, re, json, shutil, importlib.util

def find_uploads(root):
    # 与えられたパス配下で「uploads」ディレクトリ（中に 20xx 年フォルダ）を探す
    if os.path.basename(root.rstrip("/")) == "uploads":
        return root
    for dp, dns, fn in os.walk(root):
        if os.path.basename(dp) == "uploads" and any(re.match(r"20\d\d$", d) for d in dns):
            return dp
    return None

def main():
    if len(sys.argv) < 2:
        print("使い方: python3 _ingest_uploads.py <uploadsフォルダ or WPルート>"); return
    up = find_uploads(sys.argv[1])
    if not up:
        print("uploadsフォルダが見つかりません:", sys.argv[1]); return
    dest = "images/uploads"
    print("コピー:", up, "→", dest)
    if os.path.exists(dest): shutil.rmtree(dest)
    shutil.copytree(up, dest)
    have = set()
    for dp, _, fns in os.walk(dest):
        for f in fns:
            have.add(os.path.relpath(os.path.join(dp, f), dest))
    print("取り込んだ画像:", len(have), "ファイル")

    acts = json.load(open("activities.json", encoding="utf-8"))
    hit = miss = 0
    def localize(url):
        nonlocal hit, miss
        m = re.search(r"/wp-content/uploads/(.+)$", url)
        if not m:
            miss += 1; return None
        rel = m.group(1)
        cands = [rel, re.sub(r"-\d+x\d+(?=\.\w+$)", "", rel)]  # サイズ付き→原寸も試す
        for c in cands:
            if c in have:
                hit += 1; return f"{dest}/{c}"
        miss += 1; return None
    for r in acts:
        newimgs = []
        for u in r["images"]:
            lp = localize(u)
            if lp: newimgs.append(lp)
        r["images"] = newimgs
    json.dump(acts, open("activities.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"画像のローカル化: 一致 {hit} / 不一致 {miss}")

    # 再生成
    spec = importlib.util.spec_from_file_location("b", "_build_activities.py")
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    os.makedirs("news", exist_ok=True)
    for r in acts:
        open(f"news/{r['slug']}.html", "w", encoding="utf-8").write(b.gen_article(r))
    open("news.html", "w", encoding="utf-8").write(b.gen_index(acts))
    withimg = sum(1 for r in acts if r["images"])
    print(f"再生成完了: {len(acts)}記事 / 画像あり {withimg}記事")

if __name__ == "__main__":
    main()
