"""scripts/find-awesomeclaude.py: offline fixture (sitemap + 2 pages + 1 failing page), cache reuse, no network."""
import contextlib
import http.server
import importlib.util
import io
import os
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "awesomeclaude"
spec = importlib.util.spec_from_file_location("find_awesomeclaude", ROOT / "scripts" / "find-awesomeclaude.py")
fac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fac)


class FakeNet:
    """Serves the fixture files by URL path; a missing file raises like a network error."""

    def __init__(self):
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        path = urlparse(url).path.strip("/")
        f = FIX / (path if path.endswith(".xml") else path.replace("/", "__") + ".html")
        if not f.exists():
            raise TimeoutError(url)
        return f.read_text()


class FindAwesomeClaudeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = self.tmp.name
        self.net = FakeNet()
        self.real_fetch, fac.fetch = fac.fetch, self.net

    def tearDown(self):
        fac.fetch = self.real_fetch
        self.tmp.cleanup()

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = fac.main([*args, "--cache-dir", self.cache])
        return code, out.getvalue()

    def test_searches_every_sitemap_page_not_only_matching_urls(self):
        code, out = self.run_cli("postgres")
        self.assertEqual(code, 0)
        self.assertIn("2 of 4 pages searched, 1 match postgres", out)
        self.assertIn("https://awesomeclaude.ai/mcp/databases", out)
        self.assertIn("-> crystaldba/postgres-mcp", out)
        self.assertNotIn("webfuse-com/awesome-claude", out)  # site header link is not next to a match
        self.assertNotIn("qdrant", out)
        self.assertIn("skipped: https://awesomeclaude.ai/broken-page (TimeoutError)", out)
        self.assertIn("skipped: file:///etc/passwd (not on https://awesomeclaude.ai/)", out)
        self.assertEqual(len(self.net.calls), 4)  # sitemap + 3 site pages, one request each; never the file URL

    def test_script_and_style_text_are_not_searched(self):
        code, out = self.run_cli("calendar")
        self.assertIn("1 match calendar", out)
        self.assertNotIn("mcp/databases", out)
        self.assertIn("-> takumi0706/google-calendar-mcp", out)
        self.assertNotIn("Postgres and calendar", out)  # <title> is stripped with <head>

    def test_repo_is_credited_only_to_its_own_card(self):
        code, out = self.run_cli("calendar")
        rows = {ln.strip().split("  -> ")[0]: ln for ln in out.splitlines() if ln.startswith("   ")}
        # link at the end of the card (how-to layout), single quotes, www. and .git
        self.assertIn("-> takumi0706/google-calendar-mcp", rows["Google Calendar MCP server for events and availability."])
        self.assertIn("-> takumi0706/google-calendar-mcp", rows["Find free calendar slots"])
        self.assertNotIn("next-card-repo", out)
        code, out = self.run_cli("tip")
        line = next(ln for ln in out.splitlines() if "no link of its own" in ln)
        self.assertNotIn("->", line)

    def test_heading_line_gets_its_card_repo(self):
        code, out = self.run_cli("crystaldba")
        self.assertIn("crystaldba/postgres-mcp  -> crystaldba/postgres-mcp", out)

    def test_card_layouts_from_the_review(self):
        wrapped = ('<header><a href="https://github.com/webfuse-com/awesome-claude">GitHub</a></header>'
                   '<a href="https://github.com/a/one"><div><h3>One</h3><p>postgres one</p></div></a>'
                   '<a href="https://github.com/b/two"><div><h3>Two</h3><p>postgres two</p></div></a>')
        listed = ('<h2>Databases</h2><ul><li><a href="https://github.com/x/y">y</a> - postgres tool</li>'
                  '<li><a href="https://github.com/z/w">w</a> - postgres other</li></ul>')
        icon = ('<div><h3>Alpha</h3><p>alpha postgres tool</p><a href="https://github.com/a/alpha"><svg></svg></a></div>'
                '<div><h3>Beta</h3><p>beta postgres tool</p></div>')
        spoof = "<h3>Diff</h3><pre>@@ -1 +1 @@ postgres\n##\n\x00H postgres</pre>"
        for doc, want in [(wrapped, [("postgres one", "a/one"), ("postgres two", "b/two")]),
                          (listed, [("- postgres tool", "x/y"), ("- postgres other", "z/w")]),
                          (icon, [("alpha postgres tool", "a/alpha"), ("beta postgres tool", "")]),
                          (spoof, [("@@ -1 +1 @@ postgres", ""), ("H postgres", "")])]:
            _, _, hits = fac.search(fac.page_lines(doc), ["postgres"])
            self.assertEqual([(ln, repo) for ln, repo in hits], want)

    def test_offline_stays_offline_after_a_cache_hit(self):
        calls = []
        locs = "".join(f"<loc>https://awesomeclaude.ai/p{i}</loc>" for i in range(8))
        # seed the cache with the sitemap and p3 only, then take the site down
        fac.fetch = lambda url: f"<urlset>{locs}</urlset>" if url.endswith(".xml") else "<p>p3</p>"
        fac.cached("https://awesomeclaude.ai/p3", Path(self.cache), True, time.time())
        fac.cached(fac.SITEMAP, Path(self.cache), True, time.time())

        def down(url):
            calls.append(url)
            raise TimeoutError(url)
        fac.fetch = down
        self.run_cli("x")
        self.assertEqual(calls, [f"https://awesomeclaude.ai/p{i}" for i in range(3)])

    def test_cache_hits_between_failures_do_not_reset_the_count(self):
        calls = []
        locs = "".join(f"<loc>https://awesomeclaude.ai/p{i}</loc>" for i in range(10))
        fac.fetch = lambda url: f"<urlset>{locs}</urlset>" if url.endswith(".xml") else "<p>cached</p>"
        for i in (1, 3, 5):
            fac.cached(f"https://awesomeclaude.ai/p{i}", Path(self.cache), True, time.time())
        fac.cached(fac.SITEMAP, Path(self.cache), True, time.time())

        def down(url):
            calls.append(url)
            raise TimeoutError(url)
        fac.fetch = down
        self.run_cli("x")
        self.assertEqual(calls, [f"https://awesomeclaude.ai/p{i}" for i in (0, 2, 4)])

    def test_site_failing_reads_every_cached_page(self):
        self.run_cli("postgres")
        old = time.time() - fac.MAX_AGE - 60
        for f in Path(self.cache).rglob("*.txt"):
            os.utime(f, (old, old))
        fac.fetch = lambda url: (_ for _ in ()).throw(TimeoutError(url))
        code, out = self.run_cli("postgres")
        self.assertIn("-> crystaldba/postgres-mcp", out)
        self.assertIn("2 of 4 pages searched", out)

    def test_pages_with_more_distinct_keywords_rank_first(self):
        code, out = self.run_cli("postgres", "mcp")
        self.assertIn("2 match postgres mcp", out)
        pages = [ln.split()[0] for ln in out.splitlines() if ln.startswith("https://")]
        self.assertEqual(pages, ["https://awesomeclaude.ai/mcp/databases",
                                 "https://awesomeclaude.ai/how-to/manage-calendar-with-claude"])
        self.assertIn("2/2 keywords", out)

    def test_second_run_uses_cache_and_refresh_refetches(self):
        self.run_cli("qdrant")
        first = len(self.net.calls)
        self.run_cli("qdrant")
        self.assertEqual(len(self.net.calls), first + 1)  # only the failing page is retried
        self.run_cli("qdrant", "--refresh")
        self.assertEqual(len(self.net.calls), first * 2 + 1)

    def test_stale_cache_is_refetched(self):
        self.run_cli("qdrant")
        old = time.time() - fac.MAX_AGE - 60
        for f in Path(self.cache).rglob("*.txt"):
            os.utime(f, (old, old))
        before = len(self.net.calls)
        self.run_cli("qdrant")
        self.assertEqual(len(self.net.calls), before + 4)

    def test_failed_refetch_uses_old_copy_and_says_so(self):
        self.run_cli("postgres")
        fac.fetch = lambda url: (_ for _ in ()).throw(TimeoutError(url))
        code, out = self.run_cli("postgres", "--refresh")
        self.assertIn("-> crystaldba/postgres-mcp", out)
        self.assertIn("old copy: sitemap (stale (TimeoutError))", out)
        self.assertIn("old copy: https://awesomeclaude.ai/mcp/databases (stale (site failing))", out)

    def test_sitemap_failure_exits_1(self):
        fac.fetch = lambda url: (_ for _ in ()).throw(TimeoutError(url))
        code, out = self.run_cli("postgres")
        self.assertEqual(code, 1)
        self.assertIn("sitemap failed (TimeoutError)", out)

    def test_stops_after_three_failures_in_a_row(self):
        calls = []
        locs = "".join(f"<loc>https://awesomeclaude.ai/p{i}</loc>" for i in range(6))

        def down(url):
            calls.append(url)
            if url.endswith(".xml"):
                return f"<urlset>{locs}</urlset>"
            raise TimeoutError(url)
        fac.fetch = down
        code, out = self.run_cli("x")
        self.assertEqual(len(calls), 1 + fac.MAX_FAILS)
        self.assertEqual(out.count("(site failing)"), 6 - fac.MAX_FAILS)
        self.assertIn("0 of 6 pages searched", out)

    def test_redirect_off_site_is_not_followed(self):
        hits = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                if self.path == "/site/page":
                    self.send_response(302)
                    self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/secret")
                    self.end_headers()
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"secret calendar")

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        old_site = fac.SITE
        fac.SITE = f"http://127.0.0.1:{srv.server_port}/site/"
        try:
            with self.assertRaises(urllib.error.URLError):
                self.real_fetch(fac.SITE + "page")
            with self.assertRaises(ValueError):
                self.real_fetch(f"http://127.0.0.1:{srv.server_port}/secret")
        finally:
            fac.SITE = old_site
            srv.shutdown()
            srv.server_close()
        self.assertEqual(hits, ["/site/page"])

    def test_oversized_page_is_a_failure(self):
        class Big:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

            def read(self, n):
                return b"x" * n
        old = fac.OPENER
        fac.OPENER = type("O", (), {"open": lambda self, req, timeout: Big()})()
        try:
            with self.assertRaises(ValueError):
                self.real_fetch(fac.SITE + "big")
        finally:
            fac.OPENER = old

    def test_no_keywords_prints_usage(self):
        code, out = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("usage:", out)


if __name__ == "__main__":
    unittest.main()
