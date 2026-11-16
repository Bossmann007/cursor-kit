#!/usr/bin/env python3
"""List the NCS tracks on https://ncs.io/ home (title, artist, genre, highlight second, slug, mp3 url) or download one.
   python3 -I ncs.py                 -> table
   python3 -I ncs.py get "<title>" out.mp3
The page lists recent releases; data-preview is the second NCS marks as the strong part (0 = not set)."""
import html, json, re, sys, urllib.request

def tracks():
    req = urllib.request.Request("https://ncs.io/", headers={"User-Agent": "Mozilla/5.0"})
    s = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'data-url="([^"]+)"(.*?)data-genre="([^"]*)"', s, re.S):
        a = m.group(2)
        get = lambda k: html.unescape((re.search(k + r'="([^"]*)"', a) or [None, ""])[1])
        title = html.escape(get("data-track"), quote=False)
        slug = re.search(r'<a href="/([a-z0-9-]+)">(?:(?!<a href=).){0,1500}?<strong>' + re.escape(title) + '</strong>', s, re.S)
        out.append({"title": get("data-track"), "artist": get("data-artistraw"), "genre": m.group(3),
                    "preview": int(get("data-preview") or 0), "slug": slug.group(1) if slug else "", "url": m.group(1)})
    seen, uniq = set(), []
    for t in out:
        if t["url"] not in seen: seen.add(t["url"]); uniq.append(t)
    return uniq

if __name__ == "__main__":
    ts = tracks()
    if len(sys.argv) == 4 and sys.argv[1] == "get":
        t = next((t for t in ts if t["title"].lower() == sys.argv[2].lower()), None)
        if not t: sys.exit("not found: " + sys.argv[2])
        urllib.request.urlretrieve(t["url"], sys.argv[3]); print(json.dumps(t, ensure_ascii=False))
    else:
        for t in ts: print(f'{t["title"]:<36} | {t["artist"]:<28} | {t["genre"]:<18} | {t["preview"]:>3}s | {"ncs.io/" + t["slug"] if t["slug"] else "slug: abrir a faixa no site"}')
