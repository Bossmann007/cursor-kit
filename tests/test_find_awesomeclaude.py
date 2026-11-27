"""scripts/find-awesomeclaude.py: offline fixture (sitemap + 2 pages + 1 failing page), cache reuse, no network."""
import contextlib
import importlib.util
import io
import os
import tempfile
import time
import unittest
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
        self.assertIn("takumi0706/google-calendar-mcp", out)

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
        for f in Path(self.cache).iterdir():
            os.utime(f, (old, old))
        before = len(self.net.calls)
        self.run_cli("qdrant")
        self.assertEqual(len(self.net.calls), before + 4)

    def test_failed_refetch_uses_old_copy_and_says_so(self):
        self.run_cli("postgres")
        fac.fetch = lambda url: (_ for _ in ()).throw(TimeoutError(url))
        code, out = self.run_cli("postgres", "--refresh")
        self.assertIn("-> crystaldba/postgres-mcp", out)
        self.assertIn("old copy: https://awesomeclaude.ai/mcp/databases (stale (TimeoutError))", out)

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

    def test_no_keywords_prints_usage(self):
        code, out = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("usage:", out)


if __name__ == "__main__":
    unittest.main()
