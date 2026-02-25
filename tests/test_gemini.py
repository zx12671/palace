import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from palace.llm import generate

MODEL = "qwen3-max"


class TestDashScopeConnectivity(unittest.TestCase):
    def setUp(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        if not self.api_key:
            self.skipTest("DASHSCOPE_API_KEY not set")

    def test_generate_content(self):
        text = generate("回答1+1等于几，只回答数字", MODEL, self.api_key)
        self.assertIn("2", text)


if __name__ == "__main__":
    unittest.main()
