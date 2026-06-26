#!/usr/bin/env python3
import json,sys,os,re,ssl,time,hashlib,urllib.request
ctx=ssl._create_unverified_context()
urls=json.load(open("_img_urls.json",encoding="utf-8"))
start,end,outmap=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]
def localname(u):
    ext=re.search(r"\.(jpg|jpeg|png|gif|webp)$",u.lower())
    ext="."+(ext.group(1) if ext else "jpg")
    return "images/activities/"+hashlib.md5(u.encode()).hexdigest()[:14]+ext
def dl(u):
    out=localname(u)
    if os.path.exists(out) and os.path.getsize(out)>500: return out
    wb=f"https://web.archive.org/web/im_/{u}"
    for a in range(4):
        try:
            req=urllib.request.Request(wb,headers={"User-Agent":"Mozilla/5.0"})
            data=urllib.request.urlopen(req,timeout=50,context=ctx).read()
            if data[:2]==b'\xff\xd8' or data[:4]==b'\x89PNG' or data[:4]==b'GIF8' or data[:4]==b'RIFF':
                open(out,"wb").write(data); return out
            return None
        except Exception:
            time.sleep(2*(a+1))
    return None
m={}
chunk=urls[start:end]
for n,u in enumerate(chunk,1):
    r=dl(u)
    if r: m[u]=r
    time.sleep(0.25)
    if n%25==0: print(f"[{outmap}] {n}/{len(chunk)} ok={len(m)}",flush=True)
json.dump(m,open(outmap,"w",encoding="utf-8"),ensure_ascii=False)
print(f"[{outmap}] DONE {len(m)}/{len(chunk)}",flush=True)
