#!/usr/bin/env python3
"""Tests for forge_sol_S43_netbatch_v5_20261027.py with the SYNTHETIC toolchain (fake_toolchain_s43.py).
Env: FORGE_S43_TMP scratch dir; FORGE_S43_TOOL overrides the tool (mutation check). No real compiler or engine runs."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = Path(os.environ.get("FORGE_S43_TOOL", HERE / "forge_sol_S43_netbatch_v5_20261027.py"))
FAKE = HERE / "fake_toolchain_s43.py"
SCRATCH = Path(os.environ.get("FORGE_S43_TMP", tempfile.gettempdir())) / f"s43_tests_{os.getpid()}"
SCRATCH.mkdir(parents=True, exist_ok=False)
PY = sys.executable
sys.path.insert(0, str(HERE))
from fake_toolchain_s43 import bench_nodes  # noqa: E402

DEPTHS = (11, 13, 16, 20, 22)
_N = [0]


def new(tag):
    _N[0] += 1
    p = SCRATCH / f"{_N[0]:03d}_{tag}"; return p


def fake_base(root, net_bytes):
    for d in ("src", "include", "tests"):
        (root / d).mkdir(parents=True)
    for s in ("bitboard", "board", "book", "eval", "eval_params", "nnue", "search", "uci"):
        (root / "src" / f"{s}.cpp").write_text(f"// {s}\n")
    (root / "include" / "forge.hpp").write_text("// h\n"); (root / "tests" / "tests.cpp").write_text("// t\n")
    (root / "src" / "nnue_weights.inc").write_bytes(net_bytes)
    (root / "CMakeLists.txt").write_text("project(fake)\n")                       # must survive the private copy
    (root / "build_release").mkdir(); (root / "build_release" / "stale.exe").write_text("stale")  # must not
    return root


def refs_for(path, nets, wrong=None):
    d = {"schema": "forge-s26-bench-refs-v1", "nets": {}}
    for i, n in enumerate(nets):
        sha = hashlib.sha256(Path(n).read_bytes()).hexdigest()
        bench = {str(dd): bench_nodes(sha, dd) for dd in DEPTHS}
        if wrong is not None and i == 0:
            bench[str(wrong)] += 1
        d["nets"][sha] = {"id": f"net{i}", "bench": bench}
    Path(path).write_text(json.dumps(d), encoding="utf-8")


def toolchain_args():
    return ["--gpp", json.dumps([PY, "-I", "-B", str(FAKE), "gpp"]), "--objdump", json.dumps([PY, "-I", "-B", str(FAKE), "objdump"]),
            "--launcher", json.dumps([PY, "-I", "-B"]), "--min-free-ram-gib", "0.5"]


def run(args, cwd):
    p = subprocess.run([PY, "-I", "-B", str(TOOL), *map(str, args)], cwd=str(cwd), capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def tree_files(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(root).rglob("*")) if p.is_file()}


class NetBatchV5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = new("work"); cls.work.mkdir()
        cls.base = fake_base(cls.work / "base tree", b"base-net")           # a path with a space
        (cls.work / "nets").mkdir()
        cls.n1 = cls.work / "nets" / "a.inc"; cls.n1.write_bytes(b"net-A" * 50)
        cls.n2 = cls.work / "nets" / "b.inc"; cls.n2.write_bytes(b"net-B" * 70)
        cls.refs = cls.work / "refs.json"; refs_for(cls.refs, [cls.n1, cls.n2])

    def test_1_relative_from_other_cwd_equals_absolute(self):
        before = tree_files(self.base)
        rel = run(["--base", "base tree", "--net", "nets/a.inc", "--net", "nets/b.inc", "--bench-ref", "refs.json",
                   "--out", "out_rel", *toolchain_args()], self.work)                       # cwd = work, relative paths
        other = new("othercwd"); other.mkdir()
        ab = run(["--base", self.base, "--net", self.n1, "--net", self.n2, "--bench-ref", self.refs,
                  "--out", self.work / "out_abs", *toolchain_args()], other)                # another cwd, absolute paths
        self.assertEqual(rel[0], 0, rel[1] + rel[2]); self.assertEqual(ab[0], 0, ab[1] + ab[2])
        r1 = json.loads((self.work / "out_rel" / "netbatch_result.json").read_text())
        r2 = json.loads((self.work / "out_abs" / "netbatch_result.json").read_text())
        self.assertEqual([n["bench"] for n in r1["nets"]], [n["bench"] for n in r2["nets"]])
        self.assertEqual([n["bench_status"] for n in r1["nets"]], ["PASS", "PASS"])
        self.assertNotEqual(r1["cwd_at_start"], r2["cwd_at_start"])
        self.assertEqual(r1["tool_sha256"], r2["tool_sha256"])
        for r in (r1, r2):                                                                   # absolute paths everywhere
            res = r["arguments_resolved"]
            for p in [res["base"], res["bench_ref"], res["out"], *res["net"]]:
                self.assertTrue(Path(p).is_absolute(), p)
            for n in r["nets"]:
                for k in ("net", "job_dir", "private_tree", "exe"):
                    self.assertTrue(Path(n[k]).is_absolute(), n[k])
            for s in r["steps"]:
                self.assertTrue(Path(s["cwd"]).is_absolute()); self.assertTrue(Path(s["stdout"]).is_absolute())
                self.assertTrue(all(Path(x).is_absolute() for x in s["argv"] if x.endswith((".exe", ".inc", ".json"))))
        self.assertEqual(tree_files(self.base), before)                                      # base never modified
        self.assertTrue(r1["base_unchanged"])

    def test_2_new_base_no_tool_edits(self):
        base2 = fake_base(new("base2"), b"other-net")
        nd = new("nets3"); nd.mkdir(); n3 = nd / "c.inc"; n3.write_bytes(b"net-C" * 33)
        refs2 = new("refs2.json"); refs_for(refs2, [n3])
        sha_before = hashlib.sha256(TOOL.read_bytes()).hexdigest()
        rc, so, se = run(["--base", base2, "--net", n3, "--bench-ref", refs2, "--out", new("out2"), *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 0, so + se)
        self.assertEqual(hashlib.sha256(TOOL.read_bytes()).hexdigest(), sha_before)

    def test_3_pin_mismatch_and_no_reference(self):
        bad = new("bad_refs.json"); refs_for(bad, [self.n1], wrong=22)
        o = new("out_bad")
        rc, so, se = run(["--base", self.base, "--net", self.n1, "--bench-ref", bad, "--out", o, *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1)
        r = json.loads((o / "netbatch_result.json").read_text())
        self.assertEqual(r["nets"][0]["bench_status"], "PIN_MISMATCH"); self.assertIn("MISMATCH", r["nets"][0]["bench_cmp"]["22"])
        self.assertEqual(r["nets"][0]["bench_cmp"]["11"], "MATCH")
        o2 = new("out_noref")
        rc, so, se = run(["--base", self.base, "--net", self.n2, "--bench-ref", bad, "--out", o2, *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1)
        self.assertEqual(json.loads((o2 / "netbatch_result.json").read_text())["nets"][0]["bench_status"], "NO_REFERENCE")

    def test_4_fma_detected(self):
        o = new("out_fma")
        rc, so, se = run(["--base", self.base, "--net", self.n1, "--bench-ref", self.refs, "--out", o, "--extra-flag=-DFAKE_FMA", *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1)
        r = json.loads((o / "netbatch_result.json").read_text())["nets"][0]
        self.assertGreater(r["fma_count"], 0); self.assertEqual(r["status"], "FAIL")

    def test_5_refusals(self):
        o = new("nonempty"); o.mkdir(); (o / "x").write_text("x")
        rc, so, se = run(["--base", self.base, "--net", self.n1, "--bench-ref", self.refs, "--out", o, *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1); self.assertIn("not empty", se)
        rc, so, se = run(["--base", self.base, "--net", self.n1, "--bench-ref", self.refs, "--out", self.base / "inside", *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1); self.assertIn("inside an input", se); self.assertFalse((self.base / "inside").exists())
        rc, so, se = run(["--base", self.work / "nets", "--net", self.n1, "--bench-ref", self.refs, "--out", new("x"), *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1); self.assertIn("not a Forge source tree", se)
        wrong = new("wrong_schema.json"); wrong.write_text('{"nets": {}}')
        rc, so, se = run(["--base", self.base, "--net", self.n1, "--bench-ref", wrong, "--out", new("y"), *toolchain_args()], SCRATCH)
        self.assertEqual(rc, 1); self.assertIn("schema", se)

    def test_6_ctest_allowlist_classifier(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("s43tool", TOOL); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        allow = json.loads((HERE / "forge_sol_S43_allowlist_AL1_20261027.json").read_text(encoding="utf-8"))
        junit = new("junit.xml")
        junit.write_text('<testsuite><testcase name="forge_tests" status="fail"><failure message="x"/></testcase>'
                         '<testcase name="forge_perft" status="run"/></testsuite>', encoding="utf-8")
        known = ("FAIL: WAC 001 expected g3g6 got f6h5\nFAIL: WAC 001 score 623 below 31997\n"
                 "FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion\n"
                 "FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion\n")
        self.assertEqual(m.check_ctest_output(known, junit, allow, allow["test_source_sha256"][0])["status"], "PASS")
        self.assertEqual(m.check_ctest_output(known.replace("623", "661"), junit, allow, "x")["status"], "FAIL")      # wrong net score
        self.assertEqual(m.check_ctest_output(known + "FAIL: something new\n", junit, allow, "x")["status"], "FAIL")
        self.assertEqual(m.check_ctest_output(known + "FAIL: WAC 001 expected g3g6 got f6h5\n", junit, allow, "x")["status"], "FAIL")  # over max
        twice = "FAIL: WAC 001 expected g3g6 got f6h5\nFAIL: WAC 001 expected g3g6 got f6h5\nFAIL: WAC 001 score 623 below 31997\n"
        r = m.check_ctest_output(twice, junit, allow, "x")                                  # 3 lines <= max_total, one rule twice
        self.assertEqual(r["status"], "FAIL"); self.assertTrue(r["over_max"])
        junit2 = new("junit2.xml")
        junit2.write_text('<testsuite><testcase name="forge_perft" status="fail"><failure message="x"/></testcase></testsuite>', encoding="utf-8")
        self.assertEqual(m.check_ctest_output("", junit2, allow, "x")["status"], "FAIL")                               # other test failed

    def test_7_ctest_with_absolute_paths_from_other_cwd(self):
        cm = json.dumps([PY, "-I", "-B", str(FAKE), "cmake"]); ct = json.dumps([PY, "-I", "-B", str(FAKE), "ctest"])
        other = new("cwd7"); other.mkdir(); o = self.work / "out_ctest"
        rc, so, se = run(["--base", "base tree", "--net", "nets/a.inc", "--bench-ref", "refs.json", "--out", "out_ctest", "--ctest",
                          "--allowlist", HERE / "forge_sol_S43_allowlist_AL1_20261027.json", "--cmake", cm, "--ctest-exe", ct,
                          *toolchain_args()], self.work)
        self.assertEqual(rc, 0, so + se)
        r = json.loads((o / "netbatch_result.json").read_text())["nets"][0]
        self.assertEqual(r["ctest"]["status"], "PASS"); self.assertTrue(r["ctest"]["junit_exists"])
        self.assertTrue(Path(r["ctest"]["junit"]).is_absolute()); self.assertEqual(r["ctest"]["returncode"], 8)
        self.assertEqual(r["ctest"]["failed_tests"], ["forge_tests"])
        tree = Path(r["private_tree"])
        self.assertTrue((tree / "CMakeLists.txt").is_file()); self.assertFalse((tree / "build_release").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
