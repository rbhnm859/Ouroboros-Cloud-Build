"""Offline smoke tests; no imports outside stdlib."""
import unittest
from route import classify, task_key

class RouteTests(unittest.TestCase):
    def test_intents(self):
        for text, expected in [
            ("解釋 harmonic 模型", "RESEARCH"),
            ("查詢 GitHub Actions 工作狀態", "GITHUB_AUDIT"),
            ("分析 V74 勝率與 MeanR", "QUANT"),
            ("修復 cBot 的 C# 編譯錯誤", "CODE_TASK"),
            ("稽核 PR 獨立驗收", "VALIDATION"),
            ("部署正式環境", "CONTROLLED_CHANGE"),
            ("修改程式並部署", "CONTROLLED_CHANGE"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(classify(text).primary, expected)
    def test_no_false_dispatch(self):
        self.assertFalse(classify("使用 codex 修復程式").dispatchable)
    def test_task_dedup(self):
        sha = "a" * 40
        self.assertEqual(task_key("repo", "branch", sha, "修復  錯誤"), task_key("repo", "branch", sha, "修復 錯誤"))
        with self.assertRaises(ValueError):
            task_key("repo", "branch", "bad", "obj")

if __name__ == "__main__":
    unittest.main()
