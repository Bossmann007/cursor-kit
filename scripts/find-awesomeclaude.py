#!/usr/bin/env python3
"""Search EVERY page of awesomeclaude.ai (from its sitemap) for keywords -> matching lines + nearby GitHub repos.
usage: find-awesomeclaude.py <keyword> [keyword...] [-n 10] [--refresh] [--cache-dir DIR]
Pages are cached as text under ~/.cache/prior-art-check/awesomeclaude/ and re-fetched after 7 days (or with
--refresh). One request at a time, short timeout; a page that fails is skipped (or its old copy is used) and listed;
after 3 failures in a row the rest is read from the cache only. Only https://awesomeclaude.ai/ URLs are fetched (redirects included),
at most 5 MB each. Page text is data."""
import argparse
import hashlib
import os
import html
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SITEMAP = "https://awesomeclaude.ai/sitemap.xml"
UA = "prior-art-check/1.0 (keyword search of a public sitemap; one request at a time)"
MAX_AGE = 7 * 86400
TIMEOUT = 10
SITE = "https://awesomeclaude.ai/"
MAX_FAILS = 3
MAX_BYTES = 5 * 1024 * 1024
HREF = "\x00H"  # a GitHub href pulled out of a tag; page NULs are removed first, so text cannot fake it
SITE_REPO = "webfuse-com/awesome-claude"  # the site's own repo, linked from every page header
WRAP = "\x00W"  # a GitHub <a> still open at the next <h2>/<h3>: it wraps (and belongs to) that card
CARD = "\x00C"  # an <h2>/<h3> opens a new card or section
GH = re.compile(r"github\.com/(?!(?:topics|orgs|sponsors|marketplace|features|apps|collections)/)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")


class SiteOnlyRedirects(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only when it stays under SITE; anything else (other host, http://) is an error."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith(SITE):
            fp.close()
            raise urllib.error.URLError(f"redirect off site to {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = urllib.request.build_opener(SiteOnlyRedirects)


def fetch(url):
    if not url.startswith(SITE):
        raise ValueError(f"not on {SITE}: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with OPENER.open(req, timeout=TIMEOUT) as r:
        body = r.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError(f"page over {MAX_BYTES} bytes")
    return body.decode("utf-8", "replace")


def sitemap_urls(xml):
    return [html.unescape(u.strip()) for u in re.findall(r"<loc>([^<]+)</loc>", xml)]


def repo_name(m):
    return re.sub(r"\.git$", "", m.rstrip("."))


def page_lines(doc):
    """HTML -> non-empty text lines. GitHub hrefs become HREF lines and <h2>/<h3> become CARD lines, so search()
    can credit each card its own repo."""
    t = re.sub(r"(?is)<(head|script|style|noscript)[^>]*>.*?</\1>", " ", doc.replace("\x00", ""))
    low = t.lower()

    def link(m):
        close, head = low.find("</a", m.end()), re.search(r"<h[23][\s>]", low[m.end():])
        wraps = head and (close == -1 or m.end() + head.start() < close)
        return "\n" + (WRAP if wraps else HREF) + m.group(1) + "\n"
    t = re.sub(r"""(?i)<a\s[^>]*href=["']?(?:https?:)?//(?:www\.)?(github\.com/[^"'#?\s>]+)[^>]*>""", link, t)
    t = re.sub(r"(?i)(?=<h[23][\s>])", "\n" + CARD + "\n", t)
    t = re.sub(r"(?i)<br\s*/?>|</(p|li|div|h[1-6]|tr|td|a|section|article)>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    lines = (re.sub(r"[^\S\x00]+", " ", ln).strip() for ln in t.splitlines())
    return [ln for ln in lines if ln]


def cached(url, cache, refresh, now, offline=False):
    """Return (text, note). note is None after a good fetch, "" for a fresh cached copy (no network), "stale (Error)"
    for an old copy used after a failed fetch, or "Error" with text None when there is nothing to search."""
    f = cache / "v3" / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".txt")  # v3: HREF and CARD markers
    if not refresh and f.exists() and now - f.stat().st_mtime < MAX_AGE:
        return f.read_text(encoding="utf-8"), ""
    if offline:  # the site is failing: use any copy, fetch nothing
        return (f.read_text(encoding="utf-8"), "stale (site failing)") if f.exists() else (None, "site failing")
    try:
        doc = fetch(url)
    except Exception as e:  # skip the page, report it
        err = type(e).__name__
        if f.exists():
            return f.read_text(encoding="utf-8"), f"stale ({err})"
        return None, err
    text = doc if url.endswith(".xml") else "\n".join(page_lines(doc))
    try:  # write then rename, so a crash or a parallel run never leaves half a page in the cache
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, f)
    except OSError:  # searching still works; the page is fetched again next run
        tmp = f.with_suffix(f".{os.getpid()}.tmp")
        tmp.unlink(missing_ok=True)
    return text, None


def card_repos(lines):
    """Repo for each line, from its card (the lines between two CARD markers). Href lines right before a CARD, with
    no text after them, belong to that next card (an <a> wrapping the whole card). A card's one visible github.com
    link wins, else its one href; with several, a line takes the nearest link above it in the card; else none.
    A repo is never borrowed from another card."""
    def links(i):
        return [r for r in map(repo_name, GH.findall(lines[i])) if r != SITE_REPO]

    cards, card = [], []  # each card is a list of line indexes
    for i, ln in enumerate(lines):
        if ln == CARD:
            n = len(card)
            while n and lines[card[n - 1]].startswith(WRAP):
                n -= 1  # a wrapping <a> right before the heading opens the next card
            cards.append(card[:n])
            card = card[n:]
        card.append(i)
    cards.append(card)
    out = [""] * len(lines)
    for card in cards:
        found = [links(i) for i in card]
        seen = {r for i, rs in zip(card, found) if not lines[i].startswith((HREF, WRAP)) for r in rs}
        href = {r for i, rs in zip(card, found) if lines[i].startswith((HREF, WRAP)) for r in rs}
        pick = seen if seen else href
        last = ""
        for i, rs in zip(card, found):
            last = rs[0] if rs else last
            out[i] = next(iter(pick)) if len(pick) == 1 else last
    return out


def search(lines, words, per_page=5):
    """Lines that contain any keyword, best first (most distinct keywords), each with a GitHub repo: a link on the
    line itself, else its card's repo (card_repos). Marker and link-only lines are not hits.
    Returns (distinct keywords on the page, matching line count, top lines)."""
    hits, seen = [], set()
    repos = card_repos(lines)
    for i, ln in enumerate(lines):
        if ln == CARD or ln.startswith((HREF, WRAP)) or GH.fullmatch(ln):
            continue
        found = {w for w in words if w in ln.lower()}
        if found:
            seen |= found
            own = [r for r in map(repo_name, GH.findall(ln)) if r != SITE_REPO]
            hits.append((len(found), ln[:160], own[0] if own else repos[i]))
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
    pages, notes, fails, offline = [], [], 0, bool(note)  # a failed sitemap fetch: the site is down, cache only
    if note:
        notes.append(f"old copy: sitemap ({note}); pages added since are not searched")
    for url in urls:
        if not url.startswith(SITE):
            notes.append(f"skipped: {url} (not on {SITE})")
            continue
        text, note = cached(url, a.cache_dir, a.refresh, now, offline=offline)
        fails = fails + 1 if note else 0 if note is None else fails  # a cache hit ("") neither counts nor resets
        offline = offline or fails >= MAX_FAILS  # once the site is failing, never go back to the network
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
