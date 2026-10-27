#!/usr/bin/env python3
"""Tests for forge_sol_S36_samediff_verify_20261027.py (stdlib; run: python -I -B test_forge_sol_S36.py)."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s36", HERE / "forge_sol_S36_samediff_verify_20261027.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

# Two trees get the same doc line at different places, plus the same test change.
DIFF_L = """--- a/README.md\t2026-10-25 08:00:00.000000000 +0100
+++ b/README.md\t2026-10-25 11:00:00.000000000 +0100
@@ -10,3 +10,5 @@
 line ten
 line eleven
 line twelve
+
+New doc line.
--- a/tests/tests.cpp
+++ b/tests/tests.cpp
@@ -1,3 +1,3 @@
 int a;
-int b = 1;
+int b = 2;
 int c;
"""
DIFF_B = """diff -ruN a/README.md b/README.md
--- a/README.md\t2026-10-25 08:00:00.000000000 +0100
+++ b/README.md\t2026-10-25 11:00:00.000000000 +0100
@@ -3,2 +3,4 @@
 intro
+New doc line.
+
 ## buffix section
--- a/tests/tests.cpp
+++ b/tests/tests.cpp
@@ -40,3 +40,3 @@
 int a;
-int b = 1;
+int b = 2;
 int c;
"""
APPROVED_1 = """--- a/tests/tests.cpp
+++ b/tests/tests.cpp
@@ -1,3 +1,3 @@
 int a;
-int b = 1;
+int b = 5;
 int c;
"""
APPROVED_2 = """--- a/tests/tests.cpp
+++ b/tests/tests.cpp
@@ -1,3 +1,3 @@
 int a;
-int b = 5;
+int b = 2;
 int c;
--- a/README.md
+++ b/README.md
@@ -1,0 +2,2 @@
+New doc line.
+
"""
PLANT_TEST = """--- a/tests/tests.cpp
+++ b/tests/tests.cpp
@@ -5,0 +6,1 @@
+// planted extra line
"""
PLANT_SRC = """--- a/src/search.cpp
+++ b/src/search.cpp
@@ -10,0 +11,1 @@
+// planted
"""
NEW_FILE = """--- /dev/null
+++ b/tools/new_tool.py
@@ -0,0 +1,2 @@
+print('x')
+print('y')
\\ No newline at end of file
"""


class Verifier(unittest.TestCase):
    def run_tool(self, a, b, approved=(), extra=()):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.diff").write_text(a, encoding="utf-8")
            (tmp / "b.diff").write_text(b, encoding="utf-8")
            paths = []
            for i, text in enumerate(approved):
                p = tmp / f"ap{i}.patch"
                p.write_text(text, encoding="utf-8")
                paths.append(str(p))
            out = tmp / "r.json"
            args = ["--a", f"L={tmp / 'a.diff'}", "--b", f"B={tmp / 'b.diff'}", "--json", str(out), *extra]
            if paths:
                args += ["--approved", *paths]
            rc = tool.main(args)
            return rc, json.loads(out.read_text(encoding="utf-8"))

    def test_same_change_set_with_different_placement(self):
        rc, r = self.run_tool(DIFF_L, DIFF_B, [APPROVED_1, APPROVED_2])
        self.assertEqual((rc, r["verdict"]), (0, "SAME_CHANGE_SET"))
        self.assertTrue(any("README.md" in n for n in r["notes"]) or all(f["a_equals_b_blocks"] for f in r["files"]))

    def test_sequential_approved_patches_compose(self):
        rc, r = self.run_tool(DIFF_L, DIFF_L, [APPROVED_1, APPROVED_2])
        self.assertEqual(rc, 0)
        rc, r = self.run_tool(DIFF_L, DIFF_L, [APPROVED_1])
        self.assertEqual(rc, 1)                                  # README change and b=2 are not covered by patch 1

    def test_planted_one_line_extra_change_is_flagged(self):
        rc, r = self.run_tool(DIFF_L, DIFF_B + PLANT_TEST, [APPROVED_1, APPROVED_2])
        self.assertEqual((rc, r["verdict"]), (1, "DIFFERENT"))
        self.assertTrue(any("tests/tests.cpp: B differs from the approved" in x for x in r["reasons"]))
        row = [f for f in r["files"] if f["file"] == "tests/tests.cpp"][0]
        self.assertIn({"line": "// planted extra line", "a": 1, "b": 0}, row["b_vs_approved"])

    def test_protected_source_change_is_flagged_even_if_both_trees_have_it(self):
        rc, r = self.run_tool(DIFF_L + PLANT_SRC, DIFF_B + PLANT_SRC, [APPROVED_1, APPROVED_2, PLANT_SRC])
        self.assertEqual(rc, 1)
        self.assertTrue(any("protected forge source changed" in x for x in r["reasons"]))

    def test_path_outside_allow_and_new_files(self):
        rc, r = self.run_tool(NEW_FILE, NEW_FILE, [NEW_FILE])
        self.assertEqual(rc, 0)                                  # tools/ is allowed; new file parsed with no-EOL marker
        rc, r = self.run_tool(NEW_FILE, NEW_FILE, [NEW_FILE], extra=["--allow", "tests/"])
        self.assertTrue(any("outside the allowed paths" in x for x in r["reasons"]))

    def test_deterministic(self):
        a = self.run_tool(DIFF_L, DIFF_B, [APPROVED_1, APPROVED_2])[1]
        b = self.run_tool(DIFF_L, DIFF_B, [APPROVED_1, APPROVED_2])[1]
        for r in (a, b):
            r.pop("inputs")                                      # temp paths differ
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_malformed_hunk_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.diff"
            p.write_text("--- a/x\n+++ b/x\n@@ -1,1 +1,1 @@\n?bad\n", encoding="utf-8")
            self.assertEqual(tool.main(["--a", f"L={p}", "--b", f"B={p}"]), 2)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONHASHSEED", "0")
    unittest.main(verbosity=2)
