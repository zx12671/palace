"""Offline tests that do NOT require any API key."""
import json
import os
import unittest
from unittest.mock import patch

from palace.llm import extract_json, unwrap, deep_get, pick_strongest_model
from palace.agents import SANSHENG, LIUBU, run_agent
from palace.renderer import build_markdown
from palace.session import DecisionSession, STATE_DRAFT

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "agent_prompts")


class TestExtractJson(unittest.TestCase):
    def test_clean_json(self):
        result = extract_json('{"a": 1}')
        self.assertEqual(result, {"a": 1})

    def test_json_with_markdown_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        self.assertEqual(result, {"key": "value"})

    def test_json_with_surrounding_text(self):
        text = 'Here is the result:\n{"x": 42}\nDone.'
        result = extract_json(text)
        self.assertEqual(result, {"x": 42})

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            extract_json("not json at all")


class TestUnwrap(unittest.TestCase):
    def test_single_key_wrapper(self):
        self.assertEqual(unwrap({"Draft": {"a": 1}}), {"a": 1})

    def test_multi_key_passthrough(self):
        data = {"a": 1, "b": 2}
        self.assertIs(unwrap(data), data)

    def test_non_dict_inner_passthrough(self):
        data = {"key": [1, 2, 3]}
        self.assertIs(unwrap(data), data)


class TestDeepGet(unittest.TestCase):
    def test_first_key_found(self):
        self.assertEqual(deep_get({"a": 1, "b": 2}, "a", "b"), 1)

    def test_fallback_key(self):
        self.assertEqual(deep_get({"b": 2}, "a", "b"), 2)

    def test_default(self):
        self.assertEqual(deep_get({"c": 3}, "a", "b", default="x"), "x")


class TestPickStrongestModel(unittest.TestCase):
    def test_prefers_max(self):
        models = [
            {"id": "qwen2-turbo"},
            {"id": "qwen3-max"},
            {"id": "qwen3-plus"},
        ]
        self.assertEqual(pick_strongest_model(models), "qwen3-max")

    def test_empty_list(self):
        self.assertIsNone(pick_strongest_model([]))

    def test_no_qwen(self):
        self.assertIsNone(pick_strongest_model([{"id": "gpt-4"}]))


class TestAgentConfig(unittest.TestCase):
    def test_sansheng_count(self):
        self.assertEqual(len(SANSHENG), 3)

    def test_liubu_count(self):
        self.assertEqual(len(LIUBU), 6)

    def test_all_prompt_files_exist(self):
        for dept in SANSHENG + LIUBU:
            path = os.path.join(PROMPTS_DIR, dept["file"])
            self.assertTrue(os.path.isfile(path), f"Missing prompt: {path}")

    def test_prompt_templates_non_empty(self):
        for dept in SANSHENG + LIUBU:
            path = os.path.join(PROMPTS_DIR, dept["file"])
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertGreater(len(content), 50, f"{dept['file']} is too short")


class TestFixtures(unittest.TestCase):
    def test_all_fixtures_valid_json(self):
        for fname in os.listdir(FIXTURES_DIR):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(FIXTURES_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("title", data, f"{fname} missing 'title'")
            self.assertIn("domain", data, f"{fname} missing 'domain'")


class TestRenderer(unittest.TestCase):
    def test_build_markdown_minimal(self):
        issue = {"title": "Test", "background": "bg"}
        draft = {"drafts": [{"name": "A", "summary": "s", "pros": ["p"], "cons": ["c"], "rough_steps": ["s1"]}]}
        review = {"risks": ["r1"], "revision_suggestions": ["s1"]}
        final = {"imperial_choice": {"name": "A", "reasoning": "r"}, "alternative": {"name": "B", "reasoning": "r2"}}
        exec_plan = {"liubu": {"libu": {"roles": ["dev"]}, "hubu": {"budget": "0"}}}
        md = build_markdown(issue, draft, review, final, exec_plan)
        self.assertIn("# Test", md)
        self.assertIn("中书省", md)
        self.assertIn("门下省", md)
        self.assertIn("尚书省", md)


class TestRunAgentMocked(unittest.TestCase):
    @patch("palace.agents.generate")
    def test_run_agent_returns_parsed_json(self, mock_gen):
        mock_gen.return_value = '{"drafts": [{"name": "Plan A"}]}'
        result = run_agent("zhongshu.md", {"title": "test"}, "qwen3-max", "fake-key")
        self.assertIn("drafts", result)
        mock_gen.assert_called_once()


class TestSessionInit(unittest.TestCase):
    def test_initial_state(self):
        issue = {"title": "t", "domain": "test"}
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            s = DecisionSession(issue, "qwen3-max", "fake", d)
            self.assertEqual(s.state, STATE_DRAFT)
            self.assertIsNone(s.draft)
            self.assertEqual(s.dept_index, 0)


if __name__ == "__main__":
    unittest.main()
