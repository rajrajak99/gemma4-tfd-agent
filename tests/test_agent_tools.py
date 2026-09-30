"""
Unit tests for TFD-Agent tools and Verifier Engine using standard library unittest.
"""
import os
import shutil
import tempfile
import unittest
from src.agent.tools.file_tools import view_file, edit_file_replace
from src.agent.tools.search_tools import find_files, search_code
from src.agent.verifier import TracebackParser, VerifierEngine

class TestTFDAgentTools(unittest.TestCase):
    def setUp(self):
        self.temp_workspace = tempfile.mkdtemp()
        self.sample_file = os.path.join(self.temp_workspace, "sample.py")
        with open(self.sample_file, "w") as f:
            f.write("def foo():\n    return 42\n")

    def tearDown(self):
        shutil.rmtree(self.temp_workspace)

    def test_file_view_and_edit(self):
        view_res = view_file(self.sample_file)
        self.assertIn("42", view_res["content"])
        self.assertEqual(view_res["total_lines"], 2)

        # Test surgical edit
        edit_res = edit_file_replace(self.sample_file, "return 42", "return 100")
        self.assertTrue(edit_res.get("success"))

        # Confirm change
        updated_view = view_file(self.sample_file)
        self.assertIn("return 100", updated_view["content"])

    def test_search_and_find(self):
        files = find_files(self.temp_workspace, "*.py")
        self.assertIn("sample.py", files["files"])

        matches = search_code(self.temp_workspace, "def foo")
        self.assertGreaterEqual(matches["total_matches"], 1)
        self.assertEqual(matches["matches"][0]["line"], 1)

    def test_traceback_parser(self):
        sample_stderr = """
Traceback (most recent call last):
  File "calculator.py", line 18, in divide
    return a / b
ZeroDivisionError: division by zero
"""
        diag = TracebackParser.parse(sample_stderr)
        self.assertTrue(diag["has_traceback"])
        self.assertIn("ZeroDivisionError", diag["error_summary"])
        self.assertEqual(diag["primary_culprit"]["file"], "calculator.py")
        self.assertEqual(diag["primary_culprit"]["line"], 18)

if __name__ == "__main__":
    unittest.main()
