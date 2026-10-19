import importlib.util, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    import token_engine  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False


def load():
    spec = importlib.util.spec_from_file_location("te_filter", ROOT / "hooks" / "te-filter-output.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@unittest.skipUnless(HAVE, "token_engine not installed")
class T(unittest.TestCase):
    def engine(self):
        from token_engine import QualityLevel, TokenEngine
        from token_engine.core.config import EngineConfig
        c = EngineConfig.default(); c.quality_level = QualityLevel("balanced"); c.enable_ccr = False
        return TokenEngine(c)

    def test_repetitive_log_is_compressed_and_errors_kept(self):
        m = load()
        text = "\n".join(f"tests/test_x.py::test_{i} PASSED [{i}%]" for i in range(900)) + "\nE   AssertionError: boom\nFAILED tests/test_x.py::test_9\n"
        r = m.filter_text(text, self.engine())
        self.assertIsNotNone(r)
        out, before, after = r
        self.assertLess(after, before)
        self.assertIn("AssertionError: boom", out)

    def test_short_or_incompressible_output_untouched(self):
        m = load()
        self.assertIsNone(m.filter_text("hello\nworld\n", self.engine()))
        code = "\n".join(f"def f{i}(x):\n    return x * {i} + {i * 7}\n" for i in range(300))
        self.assertIsNone(m.filter_text(code, self.engine()))

    def test_updated_output_keeps_bash_result_shape(self):
        m = load()
        resp = {"stdout": "x", "stderr": "e", "interrupted": False, "isImage": False, "noOutputExpected": False}
        out = m.updated_output(resp, "short")
        self.assertEqual(out["stdout"], "short")
        self.assertEqual({k: v for k, v in out.items() if k != "stdout"}, {k: v for k, v in resp.items() if k != "stdout"})


if __name__ == "__main__":
    unittest.main()
