#!/usr/bin/env python3
"""Tests for forge_sol_S45_rebase_ready.py: real `git apply` / GNU `patch` on a tiny tree, decision logic, an
end-to-end `run` with fake build/bench functions, and the void-gate classification on fixture manifests.

  python -I -B test_forge_sol_S45_rebase_ready.py      (S45_TOOL=<path> tests another copy; used by the mutation check)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

TOOL = Path(os.environ.get("S45_TOOL", Path(__file__).resolve().parent / "forge_sol_S45_rebase_ready.py"))
spec = importlib.util.spec_from_file_location("s45", TOOL)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

BASE_FILE = "".join(f"line {i}\n" for i in range(1, 41))


def make_tree(root: Path, body: str = BASE_FILE) -> Path:
    for part in ("src", "include", "tests", "bench", "tools"):
        (root / part).mkdir(parents=True, exist_ok=True)
    (root / "src" / "a.cpp").write_text(body, encoding="utf-8", newline="\n")
    (root / "src" / "nnue_weights.inc").write_text("// net A\n", encoding="utf-8", newline="\n")
    (root / "CMakeLists.txt").write_text("project(x)\n", encoding="utf-8", newline="\n")
    return root


def patch_text(old_line: str, new_line: str, ctx_before: list[str], ctx_after: list[str], start: int, path="src/a.cpp") -> str:
    n = len(ctx_before) + 1 + len(ctx_after)
    hunk = [f"@@ -{start},{n} +{start},{n} @@"] + [" " + c for c in ctx_before] + ["-" + old_line, "+" + new_line] + \
           [" " + c for c in ctx_after]
    return f"--- a/{path}\n+++ b/{path}\n" + "\n".join(hunk) + "\n"


GOOD = patch_text("line 20", "line 20 changed", ["line 17", "line 18", "line 19"], ["line 21", "line 22", "line 23"], 17)
# Same change but the hunk header says line 12: both tools find it 5 lines later (offset, no fuzz).
OFFSET = patch_text("line 20", "line 20 changed", ["line 17", "line 18", "line 19"], ["line 21", "line 22", "line 23"], 12)
# One context line does not match: needs fuzz 1 -> git refuses, GNU patch -F0 refuses.
FUZZY = patch_text("line 20", "line 20 changed", ["line 17", "line 18", "line 19 DIFFERENT"], ["line 21", "line 22", "line 23"], 17)
# Only the OUTERMOST context line differs: GNU patch with fuzz >= 1 would apply it; -F0 and git must refuse.
FUZZ_OUTER = patch_text("line 20", "line 20 changed", ["line 17 DIFFERENT", "line 18", "line 19"], ["line 21", "line 22", "line 23"], 17)
CONFLICT = patch_text("line 99", "line 99 changed", ["line 96", "line 97", "line 98"], ["line 100"], 96)
NET = patch_text("// net A", "// net B", [], [], 1, path="src/nnue_weights.inc")


class PatchChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, text: str, name: str) -> dict:
        tree = make_tree(self.root / name / "tree")
        p = self.root / name / "x.patch"
        p.write_text(text, encoding="utf-8", newline="\n")
        before = (tree / "src" / "a.cpp").read_text(encoding="utf-8")
        r = S.check_patch(tree, p)
        self.assertEqual((tree / "src" / "a.cpp").read_text(encoding="utf-8"), before, "checks must not modify the tree")
        return r

    def test_good_patch_passes_both(self):
        r = self.check(GOOD, "good")
        self.assertTrue(r["git_apply_check"])
        self.assertTrue(r["gnu_patch_dry_run"])
        self.assertEqual(r["gnu_offset_hunks"], 0)
        self.assertEqual(r["files"], ["src/a.cpp"])

    def test_offset_is_reported_but_passes(self):
        r = self.check(OFFSET, "offset")
        self.assertTrue(r["git_apply_check"])
        self.assertTrue(r["gnu_patch_dry_run"])
        self.assertGreaterEqual(r["gnu_offset_hunks"], 1)

    def test_fuzz_is_refused_by_both(self):
        r = self.check(FUZZY, "fuzzy")
        self.assertFalse(r["git_apply_check"])
        self.assertFalse(r["gnu_patch_dry_run"])

    def test_outer_context_fuzz_is_refused(self):
        r = self.check(FUZZ_OUTER, "fuzz_outer")
        self.assertFalse(r["git_apply_check"])
        self.assertFalse(r["gnu_patch_dry_run"], "patch -F0 must not apply a hunk that needs fuzz")

    def test_conflict_fails_both(self):
        r = self.check(CONFLICT, "conflict")
        self.assertFalse(r["git_apply_check"])
        self.assertFalse(r["gnu_patch_dry_run"])

    def test_apply_changes_the_tree(self):
        tree = make_tree(self.root / "apply" / "tree")
        p = self.root / "apply" / "x.patch"
        p.write_text(GOOD, encoding="utf-8", newline="\n")
        S.apply_patch(tree, p, use_git=True)
        self.assertIn("line 20 changed\n", (tree / "src" / "a.cpp").read_text(encoding="utf-8"))
        tree2 = make_tree(self.root / "apply2" / "tree")
        S.apply_patch(tree2, p, use_git=False)
        self.assertIn("line 20 changed\n", (tree2 / "src" / "a.cpp").read_text(encoding="utf-8"))


class Decisions(unittest.TestCase):
    BASE = {11: 100, 16: 300, 20: 500}

    def test_tunable(self):
        self.assertTrue(S.on_check("tunable", {16: 300}, {16: 301}, self.BASE, 16)[0])
        ok, text = S.on_check("tunable", {16: 300}, {16: 300}, self.BASE, 16)
        self.assertFalse(ok)
        self.assertIn("INERT", text)
        self.assertFalse(S.on_check("tunable", {16: 300}, None, self.BASE, 16)[0])

    def test_node_exact(self):
        self.assertTrue(S.on_check("node_exact", {}, dict(self.BASE), self.BASE, 16)[0])
        self.assertFalse(S.on_check("node_exact", {}, {11: 100, 16: 300, 20: 501}, self.BASE, 16)[0])

    def test_fixed_depth_inert(self):
        self.assertTrue(S.on_check("fixed_depth_inert", {16: 300}, {16: 300}, self.BASE, 16)[0])
        self.assertFalse(S.on_check("fixed_depth_inert", {16: 300}, {16: 299}, self.BASE, 16)[0])

    def test_not_applicable_kinds(self):
        self.assertIsNone(S.on_check("bugfix_node_identical", {}, None, self.BASE, 16)[0])
        self.assertIsNone(S.on_check("none", {}, None, self.BASE, 16)[0])

    def good_row(self) -> dict:
        return {"kind": "tunable", "git_apply_check": True, "gnu_patch_dry_run": True, "net_touched": False,
                "patch_sha256_mismatch": False, "build_off": {"ok": True, "fma": 0}, "off_equals_base": True,
                "on_pass": True, "on_text": "", "option_errors": []}

    def test_verdict_ready_only_when_everything_passes(self):
        self.assertEqual(S.verdict(self.good_row()), "READY")
        for key, value in (("git_apply_check", False), ("gnu_patch_dry_run", False), ("net_touched", True),
                           ("patch_sha256_mismatch", True), ("off_equals_base", False), ("on_pass", False),
                           ("option_errors", ["info string invalid value"])):
            row = self.good_row()
            row[key] = value
            self.assertTrue(S.verdict(row).startswith("NOT READY"), key)
        row = self.good_row()
        row["build_off"] = {"ok": True, "fma": 3}
        self.assertTrue(S.verdict(row).startswith("NOT READY"))
        row["build_off"] = {"ok": False, "fma": None}
        self.assertTrue(S.verdict(row).startswith("NOT READY"))
        self.assertEqual(S.verdict({"kind": "none"}), "N/A")


class RunEndToEnd(unittest.TestCase):
    """cmd_run with fake build/bench: nodes are a function of (candidate dir, exe, options)."""

    def test_run(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            base = make_tree(root / "basetree")
            pdir = root / "cfg" / "patches"
            pdir.mkdir(parents=True)
            (pdir / "good.patch").write_text(GOOD, encoding="utf-8", newline="\n")
            (pdir / "conflict.patch").write_text(CONFLICT, encoding="utf-8", newline="\n")
            (pdir / "net.patch").write_text(NET, encoding="utf-8", newline="\n")
            cfg = {"candidates": [
                {"name": "tun_ok", "kind": "tunable", "patch": "patches/good.patch", "on_options": {"X": "1"}},
                {"name": "tun_inert", "kind": "tunable", "patch": "patches/good.patch", "on_options": {"X": "1"}},
                {"name": "exact_ok", "kind": "node_exact", "patch": "patches/good.patch", "on_build_flags": ["-DS=1"]},
                {"name": "exact_bad", "kind": "node_exact", "patch": "patches/good.patch", "on_options": {"Y": "true"}},
                {"name": "off_drift", "kind": "bugfix_node_identical", "patch": "patches/good.patch"},
                {"name": "conflict", "kind": "tunable", "patch": "patches/conflict.patch", "on_options": {"X": "1"}},
                {"name": "net_changer", "kind": "bugfix_node_identical", "patch": "patches/net.patch"},
                {"name": "nothing", "kind": "none", "note": "already in the lock"},
                {"name": "bad_sha", "kind": "bugfix_node_identical", "patch": "patches/good.patch", "patch_sha256": "0" * 64}]}
            cfgp = root / "cfg" / "c.json"
            cfgp.write_text(json.dumps(cfg), encoding="utf-8")
            depths = [11, 16]
            base_nodes = {11: 1000, 16: 5000}

            def fake_build(tree, exe, flags, script, log):
                exe.write_text("fake " + " ".join(flags), encoding="utf-8")
                return {"ok": True, "sha256": "f" * 64, "fma": 0, "warnings": 0, "flags": flags}

            def fake_bench(exe, ds, options=None):
                cand = exe.parent.name
                options = options or {}
                nodes = {d: base_nodes[d] for d in ds}
                if cand == "off_drift":
                    nodes = {d: base_nodes[d] + 1 for d in ds}
                if cand == "tun_ok" and options:
                    nodes = {d: base_nodes[d] + 7 for d in ds}
                if cand == "exact_bad" and options:
                    nodes = {d: base_nodes[d] - 3 if d == 16 else base_nodes[d] for d in ds}
                return {"nodes": nodes, "nps": {d: 1 for d in ds}, "option_errors": [], "unadvertised_options": []}

            a = argparse.Namespace(work=str(root / "work"), out_json=str(root / "r.json"), out_md=str(root / "r.md"),
                                   depths="11,16", precheck_depth=16, config=str(cfgp), only=None, base_tree=str(base),
                                   net=None, base_name="T", base_ref="1000,5000", build_script="unused")
            self.assertEqual(S.cmd_run(a, build_fn=fake_build, bench_fn=fake_bench), 0)
            rep = json.loads(Path(a.out_json).read_text(encoding="utf-8"))
            v = {r["name"]: r["verdict"] for r in rep["rows"]}
            self.assertTrue(rep["base_identity"])
            self.assertEqual(v["tun_ok"], "READY")
            self.assertTrue(v["tun_inert"].startswith("NOT READY") and "INERT" in v["tun_inert"])
            self.assertEqual(v["exact_ok"], "READY")
            self.assertTrue(v["exact_bad"].startswith("NOT READY"))
            self.assertTrue(v["off_drift"].startswith("NOT READY") and "OFF bench != base" in v["off_drift"])
            self.assertTrue(v["conflict"].startswith("NOT READY") and "git apply --check fails" in v["conflict"])
            self.assertTrue(v["net_changer"].startswith("NOT READY") and "changes the net" in v["net_changer"])
            self.assertEqual(v["nothing"], "N/A")
            self.assertTrue(v["bad_sha"].startswith("NOT READY") and "sha256" in v["bad_sha"])
            self.assertTrue((root / "work" / "exact_ok" / "forge_on.exe").exists(), "ON build made for build flags")
            self.assertIn("| tun_ok | tunable |", Path(a.out_md).read_text(encoding="utf-8"))
            with self.assertRaises(SystemExit):           # outputs must be new
                S.cmd_run(a, build_fn=fake_build, bench_fn=fake_bench)


def gate(gid, tag, exe, base_override=None, **kw):
    g = {"gate": gid, "tag": tag, "exe": exe, "ok": kw.pop("ok", "CR_PASS_x.ok"), "options": [], "srand": 1}
    if base_override:
        g["base_override"] = base_override
    g.update(kw)
    return g


LOCK = {"name": "base_AUTOLOCK_1_gate120_e32f003rec_s198", "exe": "forge_h256_s198.exe", "sha256": "833C47F3AB", "options": []}
OLD = {"name": "base_h256_e12", "exe": "forge_h256_e12.exe", "sha256": "456743D9CD", "options": []}
EP10 = {"name": "base_nnue_ep10", "exe": "forge_nnue_ep10.exe", "sha256": "42D387C6EF", "options": []}
COMBINE_NOTE = "vs h256_e12 (lock moved to AUTOLOCK_1 ...; keeps old opponent; an H1 goes to COMBINE_LIST). "


class Voids(unittest.TestCase):
    def classify(self, g, done=frozenset(), lock="AUTOLOCK_1_gate120_e32f003rec_s198", sha=None):
        return S.classify_gate(g, set(done), EP10, lock, sha)

    def test_states_and_classes(self):
        self.assertEqual(self.classify(gate("10", "t", "forge_x_AL1.exe", LOCK), done={"10"})["class"], "DONE")
        self.assertEqual(self.classify(gate("18", "t", "forge_packa_epa.exe", ok="DROPPED_post_lock_h256.ok"))["class"], "DROPPED")
        self.assertEqual(self.classify(gate("55", "t", "forge_h256_e20i_AL1.exe", LOCK))["class"], "VALID")
        self.assertEqual(self.classify(gate("121", "t", "forge_p23b_h256e12.exe", OLD, notes=COMBINE_NOTE))["class"],
                         "OLD_OPPONENT_COMBINE")
        self.assertEqual(self.classify(gate("40", "t", "forge_packb_h256.exe", OLD))["class"], "VOID_OPPONENT")
        held = self.classify(gate("e32c", "t", "forge_h256_e32f003.exe", OLD, status="HELD_NEEDS_DRIVER_CAP3000"))
        self.assertEqual((held["state"], held["class"]), ("HELD", "VOID_OPPONENT"))
        self.assertEqual(self.classify(gate("17", "t", "forge_timepack.exe"))["class"], "VOID_OPPONENT")  # manifest base (ep10)

    def test_superseded_policy_in_old_note_is_ignored(self):
        g = gate("55", "t", "forge_h256_e20i_AL1.exe", LOCK, notes="REBUILT on AL1 ... opponent AL1. Old note: " + COMBINE_NOTE)
        self.assertEqual(self.classify(g)["class"], "VALID")
        self.assertEqual(self.classify(g, lock="e48f006")["class"], "VOID_OPPONENT")

    def test_new_lock_voids_gates_against_the_old_lock(self):
        g = gate("55", "t", "forge_h256_e20i_AL1.exe", LOCK)
        self.assertEqual(self.classify(g, lock="e48f006")["class"], "VOID_OPPONENT")
        # matching by sha (any case) also counts as the lock
        self.assertEqual(self.classify(g, lock="renamed", sha="833c47f3ab")["class"], "VALID")

    def test_candidate_base(self):
        self.assertEqual(S.candidate_base({"exe": "forge_h256_f015_AL1.exe"}), "AL1 tree (exe suffix _AL1)")
        self.assertEqual(S.candidate_base({"exe": "forge_x.exe", "ag_rebuilt_on": "AUTOLOCK_1"}), "AUTOLOCK_1")
        self.assertIn("net-only", S.candidate_base({"exe": "forge_h256_f006.exe"}))
        self.assertEqual(S.candidate_base({"exe": "forge_p23b_refutlmr_h256e12.exe"}), "h256_e12 tree (exe name)")
        self.assertEqual(S.candidate_base({"exe": "forge_omni_s_h256v2.exe"}), "h256_e12 tree (exe name)")
        self.assertEqual(S.candidate_base({"exe": "forge_packa_epa.exe"}), "ep10 (exe name)")
        self.assertEqual(S.candidate_base({"exe": "forge_mystery.exe"}), "unknown")

    def test_cmd_voids_reads_bom_manifest_and_results(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            man = {"base": EP10, "gates": [gate("1", "a", "forge_h256_x_AL1.exe", LOCK), gate("2", "b", "forge_y_h256.exe", OLD),
                                           gate("3", "c", "forge_z_AL1.exe", LOCK)]}
            mp = root / "m.json"
            mp.write_bytes(b"\xef\xbb\xbf" + json.dumps(man).encode("utf-8"))
            rp = root / "r.csv"
            rp.write_bytes(b"\xef\xbb\xbfgate,tag,verdict\n3,c,H1\n")
            a = argparse.Namespace(manifest=str(mp), results=str(rp), lock_name="AUTOLOCK_1_gate120_e32f003rec_s198",
                                   lock_sha=None, label="t", out_json=str(root / "v.json"), out_md=str(root / "v.md"))
            self.assertEqual(S.cmd_voids(a), 0)
            v = json.loads((root / "v.json").read_text(encoding="utf-8"))
            self.assertEqual(v["counts"], {"VALID": 1, "VOID_OPPONENT": 1, "DONE": 1})
            md = (root / "v.md").read_text(encoding="utf-8")
            self.assertIn("| 2 | b |", md)
            self.assertNotIn("| 3 | c |", md)          # done gates are not listed as queued


class Safety(unittest.TestCase):
    def test_refuses_protected_outputs(self):
        for bad in (r"D:\grok-pc-data\forge_push\x", r"D:\grok-pc-data\selfplay_out\y", r"F:\forge_nnue_train\z",
                    r"C:\Users\Administrator\grok-pc\w"):
            with self.assertRaises(SystemExit):
                S.refuse_protected(Path(bad), "t")


if __name__ == "__main__":
    unittest.main(verbosity=2)
