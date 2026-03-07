"""Integration test: run the full Palace pipeline (三省六部) with Gemini model."""
import json
import os
import shutil
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from palace.llm import GEMINI_DEFAULT_MODEL
from palace.agents import run_agent, SANSHENG, LIUBU
from palace.renderer import build_markdown

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "_test_output_gemini")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestGeminiIssuePipeline(unittest.TestCase):
    """End-to-end test: issue.json → 三省 → 六部 → Markdown."""

    @classmethod
    def setUpClass(cls):
        cls.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not cls.api_key:
            raise unittest.SkipTest("GEMINI_API_KEY not set")
        cls.model = GEMINI_DEFAULT_MODEL
        cls.issue = _load_json(os.path.join(FIXTURES_DIR, "issue.json"))
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR, ignore_errors=True)

    def _dump(self, name, data):
        path = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---- 三省 ----

    def test_01_zhongshu_draft(self):
        """中书省: issue → draft (should return dict with drafts/options)."""
        result = run_agent("zhongshu.md", self.issue, self.model, self.api_key)
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0, "Draft should not be empty")
        self._dump("01_zhongshu", result)
        self.__class__._draft = result

    def test_02_menxia_review(self):
        """门下省: draft → review (should contain risks or suggestions)."""
        draft = getattr(self.__class__, "_draft", None)
        if draft is None:
            self.skipTest("Draft not available (test_01 failed)")
        result = run_agent("menxia.md", draft, self.model, self.api_key)
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0, "Review should not be empty")
        self._dump("02_menxia", result)
        self.__class__._review = result

    def test_03_shangshu_final(self):
        """尚书省: (draft, review) → final decision."""
        draft = getattr(self.__class__, "_draft", None)
        review = getattr(self.__class__, "_review", None)
        if draft is None or review is None:
            self.skipTest("Draft or Review not available")
        combined = {"Draft": draft, "Review": review}
        result = run_agent("shangshu.md", combined, self.model, self.api_key)
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0, "Final decision should not be empty")
        self._dump("03_shangshu", result)
        self.__class__._final = result

    # ---- 六部 ----

    def test_04_liubu_all(self):
        """六部: final → 6 ministry outputs, all valid dicts."""
        final = getattr(self.__class__, "_final", None)
        if final is None:
            self.skipTest("Final decision not available")
        liubu = {}
        for dept in LIUBU:
            with self.subTest(dept=dept["label"]):
                result = run_agent(dept["file"], final, self.model, self.api_key)
                self.assertIsInstance(result, dict, f"{dept['label']} should return dict")
                self.assertTrue(len(result) > 0, f"{dept['label']} should not be empty")
                self._dump(f"{dept['seq']:02d}_{dept['key']}", result)
                liubu[dept["key"]] = result
        self.__class__._liubu = liubu

    # ---- Markdown 渲染 ----

    def test_05_render_markdown(self):
        """Build markdown from all pipeline outputs."""
        final = getattr(self.__class__, "_final", None)
        liubu = getattr(self.__class__, "_liubu", None)
        draft = getattr(self.__class__, "_draft", None)
        review = getattr(self.__class__, "_review", None)
        if not all([draft, review, final, liubu]):
            self.skipTest("Pipeline outputs incomplete")

        exec_plan = {
            "issue_id": final.get("issue_id", self.issue.get("id", "")),
            "liubu": liubu,
        }
        md = build_markdown(self.issue, draft, review, final, exec_plan)
        self.assertIsInstance(md, str)
        self.assertGreater(len(md), 100, "Markdown should have substantial content")
        self.assertIn("中书省", md)
        self.assertIn("门下省", md)
        self.assertIn("尚书省", md)

        md_path = os.path.join(OUTPUT_DIR, "decision.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"\n  Markdown written to {md_path} ({len(md)} chars)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
