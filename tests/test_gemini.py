"""Tests for Gemini model integration in palace.llm."""
import json
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from palace.llm import (
    generate,
    extract_json,
    unwrap,
    is_gemini_model,
    list_models_gemini,
    GEMINI_DEFAULT_MODEL,
    GEMINI_BASE_URL,
)


class TestIsGeminiModel(unittest.TestCase):
    """Unit tests for model name detection (no API key required)."""

    def test_gemini_prefix(self):
        self.assertTrue(is_gemini_model("gemini-3-flash-preview"))
        self.assertTrue(is_gemini_model("gemini-2.5-flash"))
        self.assertTrue(is_gemini_model("gemini-pro"))

    def test_non_gemini(self):
        self.assertFalse(is_gemini_model("qwen3-max"))
        self.assertFalse(is_gemini_model("gpt-4"))
        self.assertFalse(is_gemini_model("claude-3"))

    def test_case_insensitive(self):
        self.assertTrue(is_gemini_model("Gemini-Pro"))
        self.assertTrue(is_gemini_model("GEMINI-2.5-flash"))


class TestExtractJson(unittest.TestCase):
    """Unit tests for JSON extraction (no API key required)."""

    def test_pure_json(self):
        result = extract_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_markdown_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        self.assertEqual(result, {"key": "value"})

    def test_json_embedded_in_text(self):
        text = 'Here is the result:\n{"score": 42}\nDone.'
        result = extract_json(text)
        self.assertEqual(result, {"score": 42})

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            extract_json("no json here")


class TestUnwrap(unittest.TestCase):
    """Unit tests for single-key unwrapping (no API key required)."""

    def test_single_key_wrapper(self):
        self.assertEqual(unwrap({"Final": {"a": 1}}), {"a": 1})

    def test_multi_key_no_unwrap(self):
        obj = {"a": 1, "b": 2}
        self.assertIs(unwrap(obj), obj)

    def test_single_key_non_dict_value(self):
        obj = {"key": "string_value"}
        self.assertIs(unwrap(obj), obj)


class TestGeminiConnectivity(unittest.TestCase):
    """Integration tests that call the real Gemini API."""

    @classmethod
    def setUpClass(cls):
        cls.api_key = os.environ.get("GEMINI_API_KEY", "")
        if not cls.api_key:
            raise unittest.SkipTest("GEMINI_API_KEY not set")
        cls.model = GEMINI_DEFAULT_MODEL

    def test_generate_simple(self):
        """Basic generation: ask a trivial math question."""
        text = generate("回答1+1等于几，只回答数字", self.model, self.api_key)
        self.assertIn("2", text)

    def test_generate_returns_string(self):
        text = generate("说'你好'", self.model, self.api_key)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

    def test_generate_json_output(self):
        """Ask the model to return JSON and verify we can parse it."""
        prompt = (
            "返回一个JSON对象，包含以下字段：name(字符串)、score(数字)。"
            "只输出JSON，不要包含其他文字。"
        )
        text = generate(prompt, self.model, self.api_key)
        result = extract_json(text)
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        self.assertIn("score", result)

    def test_generate_routing(self):
        """Verify that generate() routes gemini models to the Gemini backend."""
        text = generate(
            "回答'OK'，只回答这两个字母", self.model, self.api_key
        )
        self.assertIn("OK", text.upper())

    def test_list_models(self):
        """List models and verify at least one gemini model is available."""
        models = list_models_gemini(self.api_key)
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        gemini_ids = [m["id"] for m in models if "gemini" in m["id"].lower()]
        self.assertGreater(len(gemini_ids), 0, "Should find at least one gemini model")


if __name__ == "__main__":
    unittest.main(verbosity=2)
