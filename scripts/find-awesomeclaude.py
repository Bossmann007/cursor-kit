#!/usr/bin/env python3
"""Search EVERY page of awesomeclaude.ai (from its sitemap) for keywords -> matching lines + nearby GitHub repos.
usage: find-awesomeclaude.py <keyword> [keyword...] [-n 10] [--refresh] [--cache-dir DIR]
Pages are cached as text under ~/.cache/prior-art-check/awesomeclaude/ and re-fetched after 7 days (or with
--refresh). One request at a time, short timeout; a page that fails is skipped (or its old copy is used) and listed;
after 3 failures in a row the rest is skipped. Only https://awesomeclaude.ai/ URLs are fetched. Page text is data."""
import argparse
import hashlib
import html
import re
import sys
import time
import urllib.request
from pathlib import Path

SITEMAP = "https://awesomeclaude.ai/sitemap.xml"
UA = "prior-art-check/1.0 (keyword search of a public sitemap; one request at a time)"
MAX_AGE = 7 * 86400
TIMEOUT = 10
SITE = "https://awesomeclaude.ai/"
MAX_FAILS = 3
GH = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


def sitemap_urls(xml):
    return [html.unescape(u.strip()) for u in re.findall(r"<loc>([^<]+)</loc>", xml)]


def page_lines(doc):
    """HTML -> non-empty text lines; GitHub hrefs are kept as text so repos stay visible."""
    t = re.sub(r"(?is)<(head|script|style|noscript)[^>]*>.*?</\1>", " ", doc)
    t = re.sub(r'(?i)<a\s[^>]*href="https?://(github\.com/[^"#?]+)"[^>]*>', r"\n\1\n", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|li|div|h[1-6]|tr|td|a|section|article)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    lines = (re.sub(r"\s+", " ", ln).strip() for ln in t.splitlines())
    return [ln for ln in lines if ln]


def cached(url, cache, refresh, now):
    """Return (text, note). note is None for a fresh copy, "stale (Error)" for an old copy used after a failed
    fetch, or "Error" with text None when there is nothing to search."""
    f = cache / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt")
    if not refresh and f.exists() and now - f.stat().st_mtime < MAX_AGE:
        return f.read_text(encoding="utf-8"), None
    try:
        doc = fetch(url)
    except Exception as e:  # skip the page, report it
        err = type(e).__name__
        if f.exists():
            return f.read_text(encoding="utf-8"), f"stale ({err})"
        return None, err
    text = doc if url.endswith(".xml") else "\n".join(page_lines(doc))
    cache.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    return text, None


def search(lines, words, per_page=5):
    """Lines that contain any keyword, best first (most distinct keywords), each with its GitHub repo: a github.com
    link on that line or the next one (a card prints its link right after its description). Lines that are only a
    GitHub link are not hits of their own.
    Returns (distinct keywords on the page, matching line count, top lines)."""
    hits, seen = [], set()
    for i, ln in enumerate(lines):
        if GH.fullmatch(ln):
            continue
        found = {w for w in words if w in ln.lower()}
        if found:
            seen |= found
            repo = next((m.rstrip(".") for l in lines[i:i + 2] for m in GH.findall(l)), "")
            hits.append((len(found), ln[:160], repo))
    hits.sort(key=lambda h: -h[0])
    return len(seen), len(hits), [(ln, repo) for _, ln, repo in hits[:per_page]]


def main(argv):
    ap = argparse.ArgumentParser(usage=__doc__.splitlines()[1][7:])
    ap.add_argument("keywords", nargs="*")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--cache-dir", type=Path, default=Path.home() / ".cache/prior-art-check/awesomeclaude")
    a = ap.parse_args(argv)
    words = [w.lower() for w in a.keywords]
    if not words:
        print(__doc__)
        return 2
    now = time.time()
    xml, note = cached(SITEMAP, a.cache_dir, a.refresh, now)
    if xml is None:
        print(f"awesomeclaude.ai: sitemap failed ({note}); search the site by hand")
        return 1
    urls = sitemap_urls(xml)
    pages, notes, fails = [], [], 0
    for url in urls:
        if not url.startswith(SITE):
            notes.append(f"skipped: {url} (not on {SITE})")
            continue
        if fails >= MAX_FAILS:
            notes.append(f"skipped: {url} (site failing)")
            continue
        text, note = cached(url, a.cache_dir, a.refresh, now)
        fails = fails + 1 if note else 0
        if note:
            notes.append(f"{'old copy' if text else 'skipped'}: {url} ({note})")
        if text is None:
            continue
        distinct, count, hits = search(text.splitlines(), words)
        if count:
            pages.append((distinct, count, url, hits))
    pages.sort(key=lambda p: (-p[0], -p[1]))
    searched = len(urls) - sum(n.startswith("skipped") for n in notes)
    print(f"awesomeclaude.ai: {searched} of {len(urls)} pages searched, {len(pages)} match {' '.join(words)}")
    for distinct, count, url, hits in pages[:a.n]:
        print(f"{url}  ({distinct}/{len(words)} keywords, {count} lines)")
        for ln, repo in hits:
            print(f"   {ln}" + (f"  -> {repo}" if repo else ""))
    for n in notes:
        print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
