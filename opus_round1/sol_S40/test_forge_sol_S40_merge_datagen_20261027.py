#!/usr/bin/env python3
"""Tests for forge_sol_S40_merge_datagen_20261027.py (Opus 5.5, 2026-10-27).

Environment:
  FORGE_S40_FIXTURE   built fixture directory or fixture .tar.gz; default: fixture/forge_sol_S40_fixture_20261027.tar.gz
                      beside this file. Every test process works on its own PRIVATE copy under FORGE_S40_TMP.
  FORGE_S40_TMP       scratch directory for outputs (default: the system temp dir)
  FORGE_S40_TOOL      tool under test (default: the file beside this test; the mutation check points it at mutants)
  FORGE_S40_FEN2BIN   optional fen2bin.exe (PC tools/fen2bin.cpp build): output .pos must equal its bytes
  FORGE_S40_HCE_DUMP  optional hce_dump.exe: the --hce-dump route must equal the --second-hce-dir route
  FORGE_S40_V3B       optional renamed copy of the v3b trainer: its load_set / load_set_mmap must load the output
The expected reasons come from an independent brute-force reference (python-chess FEN parsing, Python sets, the
group rule re-implemented on python-chess values); the tool's binary parser and numpy matching are not reused.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

import chess
import numpy as np

HERE = Path(__file__).resolve().parent
TOOL_PATH = Path(os.environ.get("FORGE_S40_TOOL", HERE / "forge_sol_S40_merge_datagen_20261027.py"))
FIXTURE_SRC = Path(os.environ.get("FORGE_S40_FIXTURE", HERE / "fixture" / "forge_sol_S40_fixture_20261027.tar.gz"))
SCRATCH = Path(os.environ.get("FORGE_S40_TMP", tempfile.gettempdir()))
FEN2BIN = os.environ.get("FORGE_S40_FEN2BIN")
HCE_DUMP = os.environ.get("FORGE_S40_HCE_DUMP")
V3B = os.environ.get("FORGE_S40_V3B")
PRIORITY = ["holdout_position", "holdout_game", "main_game", "dup_main", "dup_second", "kept"]


def load_tool():
    spec = importlib.util.spec_from_file_location("s40tool_under_test", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


TOOL = load_tool()
_RUN = [0]


def fixture_dir():
    """A PRIVATE copy of the fixture for this test process: even a buggy tool (or a mutant) that writes where it must
    not can only pollute this copy, never the source fixture or a later run."""
    root = SCRATCH / f"s40_fixture_private_{os.getpid()}"
    if root.exists():
        raise RuntimeError(f"{root} exists")
    root.mkdir(parents=True)
    if FIXTURE_SRC.is_dir():
        shutil.copytree(FIXTURE_SRC, root / FIXTURE_SRC.name)
    else:
        with tarfile.open(FIXTURE_SRC, "r:gz") as t:
            for m in t.getmembers():
                if m.name.startswith("/") or ".." in Path(m.name).parts or not (m.isfile() or m.isdir()):
                    raise RuntimeError("unsafe member in fixture archive")
            t.extractall(root)
    subs = [p for p in root.iterdir() if p.is_dir()]
    assert len(subs) == 1 and (subs[0] / "fixture_truth.json").exists(), "fixture layout"
    if any(p.is_dir() for p in (subs[0] / "second").iterdir()):  # (Path.glob("*/") also matches files before 3.11)
        raise RuntimeError("fixture source is polluted (a directory inside second/)")
    return subs[0]


F = fixture_dir()
TRUTH = json.loads((F / "fixture_truth.json").read_text(encoding="utf-8"))
MAIN_POS = [str(F / "pos" / f"forge_selfplay_00{k}.pos") for k in (1, 2, 3)]
HOLD_POS = [str(F / "pos" / f"forge_selfplay_00{k}.pos") for k in (4, 5)]


def new_out(tag):
    _RUN[0] += 1
    return SCRATCH / f"s40_test_{os.getpid()}_{_RUN[0]:03d}_{tag}"


def run_tool(*argv):
    out = io.StringIO(); err = io.StringIO()
    old = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        rc = TOOL.main(list(map(str, argv)))
    finally:
        sys.stdout, sys.stderr = old
    return rc, out.getvalue(), err.getvalue()


def merge(tag, *extra, second=None, hce=("--second-hce-dir", None)):
    o = new_out(tag)
    args = ["merge", "--second", *(second or [F / "second"]), "--main", *MAIN_POS, "--holdout", *HOLD_POS, "--out", o]
    if hce[0] == "--second-hce-dir":
        args += ["--second-hce-dir", F / "second_hce"]
    elif hce[0]:
        args += list(hce)
    args += list(extra)
    rc, so, se = run_tool(*args)
    return rc, o, so, se


def ledger(out):
    with gzip.open(out / TOOL.LEDGER, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def summary(out):
    return json.loads((out / TOOL.SUMMARY).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ independent reference (python-chess)
def text_rows(path, limit_lines=None):
    rows = []
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    lines = lines[:-1]  # the last element is the unterminated tail (or b"")
    for raw in lines[:limit_lines]:
        fen, sc, res = [x.strip() for x in raw.decode("ascii").split("|")]
        b = chess.Board(fen)
        rows.append({"ident": (b.board_fen(), b.turn), "score": int(sc), "res": res, "fm": b.fullmove_number,
                     "pcs": len(b.piece_map())})
    return rows


def reference(second_files, main_txt, hold_txt, groups=None, hold_ids=(), main_ids=(), rule="drop-group"):
    """Expected reason, group and first match per second row; label conflicts per reason."""
    hold, main = {}, {}
    for role, files, d in (("holdout", hold_txt, hold), ("main", main_txt, main)):
        for path in files:
            for i, r in enumerate(text_rows(path)):
                d.setdefault(r["ident"], []).append((Path(path).name, i, r["score"], r["res"]))
    S = []
    for path, limit in second_files:
        for i, r in enumerate(text_rows(path, limit)):
            S.append({**r, "src": Path(path).name, "row": i})
    if groups is None:  # Sol's rule on python-chess values, no reset at file boundaries
        g = 0; groups = []
        for i, r in enumerate(S):
            if i and (r["fm"] < S[i - 1]["fm"] or r["pcs"] > S[i - 1]["pcs"] or r["res"] != S[i - 1]["res"]):
                g += 1
            groups.append(g)
        gnames = None
    else:
        names = {}; gnames = groups; groups = [names.setdefault(x, len(names)) for x in groups]
    touch = {groups[i] for i, r in enumerate(S) if r["ident"] in hold} if rule == "drop-group" else set()
    gid_hold = {groups[i] for i in range(len(S)) if gnames and gnames[i] in hold_ids}
    gid_main = {groups[i] for i in range(len(S)) if gnames and gnames[i] in main_ids}
    out = []; seen = {}
    for i, r in enumerate(S):
        g = groups[i]
        if r["ident"] in hold:
            rs = "holdout_position"
        elif g in touch or g in gid_hold:
            rs = "holdout_game"
        elif g in gid_main:
            rs = "main_game"
        elif r["ident"] in main:
            rs = "dup_main"
        elif r["ident"] in seen:
            rs = "dup_second"
        else:
            rs = "kept"; seen[r["ident"]] = i
        match = conflict = None
        if rs == "holdout_position":
            m = hold[r["ident"]]; match = ("holdout",) + m[0][:2]; conflict = any((x[2], x[3]) != (r["score"], r["res"]) for x in m)
        elif rs == "dup_main":
            m = main[r["ident"]]; match = ("main",) + m[0][:2]; conflict = any((x[2], x[3]) != (r["score"], r["res"]) for x in m)
        elif rs == "dup_second":
            j = seen[r["ident"]]; match = ("second", S[j]["src"], S[j]["row"]); conflict = (S[j]["score"], S[j]["res"]) != (r["score"], r["res"])
        out.append({"src": r["src"], "row": r["row"], "group": g, "reason": rs, "match": match, "conflict": conflict})
    return out


MAIN_TXT = [F / "main" / f"forge_selfplay_00{k}.txt" for k in (1, 2, 3)]
HOLD_TXT = [F / "main" / f"forge_selfplay_00{k}.txt" for k in (4, 5)]
SEALED2 = [(F / "second" / "forge_selfplay_001.txt", None), (F / "second" / "forge_selfplay_002.txt", None)]


def assert_matches_reference(tc, out, ref):
    led = ledger(out)
    tc.assertEqual(len(led), len(ref))
    for a, b in zip(led, ref):
        got = (a["source"], int(a["row"]), int(a["group"]), a["reason"])
        exp = (b["src"], b["row"], b["group"], b["reason"])
        tc.assertEqual(got, exp)
        if b["match"] is not None:
            norm = lambda n: n[:-4] if n.endswith((".pos", ".txt")) and not n.endswith(".txt.part") else n
            tc.assertEqual((a["match_role"], norm(a["match_file"]), int(a["match_row"])), (b["match"][0], norm(b["match"][1]), b["match"][2]),
                           f"first match of {got}")
            tc.assertEqual(int(a["label_conflict"]), int(b["conflict"]), f"label conflict of {got}")
    s = summary(out)
    tally = {r: sum(1 for b in ref if b["reason"] == r) for r in PRIORITY}
    tc.assertEqual(s["reasons"], tally)
    tc.assertEqual(s["groups"]["groups"], len({b["group"] for b in ref}))
    conf = {"holdout_position": 0, "dup_main": 0, "dup_second": 0}
    for b in ref:
        if b["reason"] in conf and b["conflict"]:
            conf[b["reason"]] += 1
    tc.assertEqual(s["label_conflicts"], conf)


def rows_of(led, label):
    """Ledger rows of one planted game (the ledger lists the second folder's rows in order)."""
    return [led[i] for i, x in enumerate(TRUTH["second_row_game"]) if x == label and i < len(led)]


class MergeFixture(unittest.TestCase):
    def test_01_fixture_vs_bruteforce_reference(self):
        rc, out, so, se = merge("ref")
        self.assertEqual(rc, 0, se)
        ref = reference(SEALED2, MAIN_TXT, HOLD_TXT)
        assert_matches_reference(self, out, ref)
        # inferred groups == the builder's true games on this fixture
        true = TRUTH["second_row_game"][:len(ref)]
        self.assertEqual(len(set(true)), summary(out)["groups"]["groups"])

    def test_02_planted_cases(self):
        rc, out, so, se = merge("planted", "--include-part", "--seen-db", F / "second_db" / "forge_seen_hashes.sqlite3", hce=("--no-hce",))
        self.assertEqual(rc, 0, se)
        led = ledger(out)
        reasons = lambda label: [r["reason"] for r in rows_of(led, label)]
        self.assertEqual(set(reasons("S_COPY_MAIN")), {"dup_main"})
        pm = reasons("S_PREFIX_MAIN"); self.assertEqual(pm[0], "dup_main"); self.assertIn("kept", pm)
        self.assertEqual(set(reasons("S_COPY_HOLD")), {"holdout_position"})
        self.assertEqual(reasons("S_CASTLE"), ["dup_main"])          # castling ignored by the identity
        self.assertEqual(reasons("S_STMFLIP"), ["kept"])             # side to move is part of the identity
        ih = rows_of(led, "S_IDENT_HOLD"); self.assertEqual({r["reason"] for r in ih}, {"holdout_position"})
        self.assertEqual({r["label_conflict"] for r in ih}, {"0"})
        xf = rows_of(led, "S_XFILE_HOLD")
        self.assertEqual([(r["source"], r["reason"]) for r in xf[:4]], [("forge_selfplay_001.txt", "holdout_game")] * 4)
        self.assertEqual(xf[4]["source"], "forge_selfplay_002.txt"); self.assertEqual(xf[4]["reason"], "holdout_position")
        self.assertEqual(len({r["group"] for r in xf}), 1)            # one game across the file junction
        t1 = reasons("S_TOUCH1_HOLD")
        self.assertEqual(t1.count("holdout_position"), 1); self.assertEqual(set(t1) - {"holdout_position"}, {"holdout_game"})
        ds = rows_of(led, "S_DUP_SECOND")
        self.assertTrue(ds and {r["reason"] for r in ds} == {"dup_second"})
        self.assertEqual({r["match_file"] for r in ds}, {"forge_selfplay_001.txt"})

    def test_03_part_handling(self):
        n_sealed = TRUTH["second_split_rows"][1]
        part = F / "second" / "forge_selfplay_003.txt.part"
        pc = TRUTH["part_committed"]
        rc, out, so, se = merge("nopart")
        self.assertEqual(rc, 0, se); self.assertEqual(summary(out)["second_rows"], n_sealed); self.assertIn("--include-part", se)
        rc, out, so, se = merge("part_all", "--include-part", hce=("--no-hce",))
        self.assertEqual(rc, 0, se)
        s = summary(out); total_complete = TRUTH["second_rows"] - n_sealed
        self.assertEqual(s["second_rows"], n_sealed + total_complete)
        self.assertEqual(s["inputs"]["second"][2]["incomplete_tail_bytes"], TRUTH["part_unterminated_tail_bytes"])
        self.assertTrue(s["inputs"]["second"][2]["committed_offset"].startswith("UNVERIFIED"))
        ref = reference(SEALED2 + [(part, None)], MAIN_TXT, HOLD_TXT)
        assert_matches_reference(self, out, ref)
        rc, out, so, se = merge("part_bytes", "--include-part", "--part-committed-bytes", pc["bytes"], hce=("--no-hce",))
        self.assertEqual(rc, 0, se); self.assertEqual(summary(out)["second_rows"], n_sealed + pc["rows"])
        assert_matches_reference(self, out, reference(SEALED2 + [(part, pc["rows"])], MAIN_TXT, HOLD_TXT))
        rc, out, so, se = merge("part_db", "--include-part", "--seen-db", F / "second_db" / "forge_seen_hashes.sqlite3", hce=("--no-hce",))
        self.assertEqual(rc, 0, se); s = summary(out)
        self.assertEqual(s["second_rows"], n_sealed + pc["rows"]); self.assertEqual(s["inputs"]["second"][2]["committed_offset"], "generator DB copy")
        rc, out, so, se = merge("part_badoff", "--include-part", "--part-committed-bytes", pc["bytes"] - 3, hce=("--no-hce",))
        self.assertEqual(rc, 1); self.assertIn("unterminated", se)
        self.assertTrue((out / "STOPPED.txt").exists()); self.assertFalse((out / TOOL.MANIFEST).exists())
        rc, out, so, se = merge("part_hce", "--include-part")  # a .part has no .hce: --second-hce-dir must refuse
        self.assertEqual(rc, 1); self.assertIn("unsealed", se); self.assertFalse(out.exists())  # refused before any write

    def test_04_deterministic(self):
        rc0, o0, _, se0 = merge("detNoHce", hce=(None,))
        self.assertEqual(rc0, 1); self.assertIn("exactly one of", se0)  # no HCE route chosen: refused
        rc1, o1, _, se1 = merge("detA", "--rows-per-file", "300")
        rc2, o2, _, se2 = merge("detB", "--rows-per-file", "300")
        self.assertEqual((rc1, rc2), (0, 0), se1 + se2)
        f1 = sorted(p.name for p in o1.iterdir()); f2 = sorted(p.name for p in o2.iterdir())
        self.assertEqual(f1, f2)
        self.assertGreater(sum(n.endswith(".pos") for n in f1), 1)  # several output shards
        for n in f1:
            if n in ("run_info.json", "SHA256SUMS"):
                continue
            self.assertEqual((o1 / n).read_bytes(), (o2 / n).read_bytes(), n)

    def test_05_inputs_unchanged_and_no_files_added(self):
        def snap():
            return {str(p.relative_to(F)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
                    for p in sorted(F.rglob("*")) if p.is_file()}
        before = snap()
        rc, out, so, se = merge("unchanged", "--include-part", "--seen-db", F / "second_db" / "forge_seen_hashes.sqlite3",
                                hce=("--hce-dump", HCE_DUMP) if HCE_DUMP else ("--no-hce",))
        self.assertEqual(rc, 0, se)
        self.assertEqual(snap(), before)
        # the fixture's own md5 list (written by the builder) still holds for every builder file
        for rel, md5 in TRUTH["md5"].items():
            self.assertEqual(hashlib.md5((F / rel).read_bytes()).hexdigest(), md5, rel)

    def test_06_out_dir_refusals(self):
        rc, so, se = run_tool("merge", "--second", F / "second", "--main", *MAIN_POS, "--no-hce", "--out", F / "second" / "newdir")
        self.assertEqual(rc, 1); self.assertIn("inside input directory", se); self.assertFalse((F / "second" / "newdir").exists())
        nonempty = new_out("nonempty"); nonempty.mkdir(); (nonempty / "x.txt").write_bytes(b"x")
        rc, so, se = run_tool("merge", "--second", F / "second", "--no-hce", "--out", nonempty)
        self.assertEqual(rc, 1); self.assertIn("not empty", se)
        prot = new_out("prot"); prot.mkdir()
        rc, so, se = run_tool("merge", "--second", F / "second", "--no-hce", "--out", prot / "x", "--protected", prot)
        self.assertEqual(rc, 1); self.assertIn("protected", se)
        rc, so, se = run_tool("merge", "--second", F / "second", "--main", MAIN_POS[0], "--holdout", MAIN_POS[0], "--no-hce", "--out", new_out("both"))
        self.assertEqual(rc, 1); self.assertIn("both main and holdout", se)
        rc, so, se = run_tool("merge", "--second", F / "second", "--include-part", "--seen-db", F / "second" / "forge_selfplay_001.txt",
                                 "--no-hce", "--out", new_out("livedb"))
        self.assertEqual(rc, 1); self.assertIn("COPY outside the second folder", se)

    def test_07_tripwire_fails_closed(self):
        rc, out, so, se = merge("tripwire", second=[F / "interleaved"], hce=("--no-hce",))
        self.assertEqual(rc, 1); self.assertIn("interleaving", se)
        self.assertIn("interleaving", (out / "STOPPED.txt").read_text()); self.assertFalse((out / TOOL.MANIFEST).exists())

    def test_08_explicit_game_ids(self):
        rc, out, so, se = merge("ids", "--game-id-sidecars", "--holdout-game-ids", F / "ids" / "holdout_ids.txt",
                                "--main-game-ids", F / "ids" / "main_ids.txt", second=[F / "second_ids"])
        self.assertEqual(rc, 0, se)
        names = []
        for n in ("forge_selfplay_001.txt", "forge_selfplay_002.txt"):
            names += (F / "second_ids" / (n + ".gameid")).read_text().split()
        ref = reference([(F / "second_ids" / "forge_selfplay_001.txt", None), (F / "second_ids" / "forge_selfplay_002.txt", None)],
                        MAIN_TXT, HOLD_TXT, groups=names, hold_ids={"sp2-s002"}, main_ids={"sp2-s004"})
        assert_matches_reference(self, out, ref)
        s = summary(out); self.assertEqual((s["groups"]["in_holdout_id_list"], s["groups"]["in_main_id_list"]), (1, 1))
        led = ledger(out)
        self.assertTrue({r["reason"] for r, nm in zip(led, names) if nm == "sp2-s004"} == {"main_game"})
        self.assertIn("holdout_game", {r["reason"] for r, nm in zip(led, names) if nm == "sp2-s002"})

    def test_09_gameids_fingerprints_and_rule_off(self):
        lst_dir = new_out("idlist"); lst_dir.mkdir(); lst = lst_dir / "holdout_fingerprint_ids.txt"
        rc, so, se = run_tool("gameids", "--text", *HOLD_TXT, "--out", lst)
        self.assertEqual(rc, 0, se)
        ids = {l for l in lst.read_text().splitlines() if l and not l.startswith("#")}
        rc, out, so, se = merge("rule_off", "--holdout-game-rule", "off", "--holdout-game-ids", lst)
        self.assertEqual(rc, 0, se)
        led = ledger(out); s = summary(out)
        ih = rows_of(led, "S_IDENT_HOLD")
        self.assertIn(ih[0]["game_id"], ids)                         # identical game -> identical fingerprint ID
        self.assertGreaterEqual(s["groups"]["in_holdout_id_list"], 1)
        t1 = [r["reason"] for r in rows_of(led, "S_TOUCH1_HOLD")]
        self.assertEqual(t1.count("holdout_position"), 1); self.assertNotIn("holdout_game", t1)  # rule off: no group drop
        self.assertIn("kept", t1)
        rc, so, se = run_tool("gameids", "--text", *HOLD_TXT, "--out", lst)
        self.assertEqual(rc, 1)                                       # never overwritten

    def test_10_collision_safety(self):
        rc, base, so, se = merge("nocoll")
        self.assertEqual(rc, 0, se)
        real = TOOL.keys64
        TOOL.keys64 = lambda boards, stm: (np.asarray(boards, np.uint64).sum(axis=1) % np.uint64(7)).astype(np.uint64)
        try:
            rc, out, so, se = merge("coll")
        finally:
            TOOL.keys64 = real
        self.assertEqual(rc, 0, se)
        s = summary(out)
        self.assertGreater(s["key_collisions_rejected"]["main"] + s["key_collisions_rejected"]["holdout"], 0)
        self.assertEqual(ledger(out), ledger(base))
        for n in ("forge_s40_merged_001.pos", "forge_s40_merged_001.txt", "forge_s40_merged_001.hce"):
            self.assertEqual((out / n).read_bytes(), (base / n).read_bytes(), n)

    def test_11_verify(self):
        rc, out, so, se = merge("verify")
        self.assertEqual(rc, 0, se)
        rc, so, se = run_tool("verify", out); self.assertEqual(rc, 0, so + se); self.assertIn('"PASS"', so)
        bad = new_out("verify_bad"); shutil.copytree(out, bad)
        p = bad / "forge_s40_merged_001.pos"; data = bytearray(p.read_bytes()); data[100] ^= 1
        with open(p, "r+b") as f:
            f.write(bytes(data))
        rc, so, se = run_tool("verify", bad); self.assertEqual(rc, 1); self.assertIn("md5 mismatch", so)

    def test_12_output_rows_equal_source_rows(self):
        """Every output row (txt, pos, hce) equals its source row; checked through the ledger, independent of the tool."""
        rc, out, so, se = merge("rows", "--rows-per-file", "250")
        self.assertEqual(rc, 0, se)
        led = ledger(out); src_lines = {}; src_hce = {}
        for n in ("forge_selfplay_001.txt", "forge_selfplay_002.txt"):
            src_lines[n] = (F / "second" / n).read_bytes().split(b"\n")[:-1]
            src_hce[n] = np.fromfile(F / "second_hce" / n.replace(".txt", ".hce"), "<i2", offset=16)
        kept = [r for r in led if r["reason"] == "kept"]
        by_file = {}
        for r in kept:
            by_file.setdefault(r["out_file"], []).append(r)
        for stem, rows in by_file.items():
            lines = (out / f"{stem}.txt").read_bytes().split(b"\n")[:-1]
            hce = np.fromfile(out / f"{stem}.hce", "<i2", offset=16)
            pos = (out / f"{stem}.pos").read_bytes(); n = len(rows)
            self.assertEqual(pos[:16], b"FPOS" + (1).to_bytes(4, "little") + n.to_bytes(8, "little"))
            meta = np.frombuffer(pos, np.uint8, n, 16 + 34 * n)
            for r in rows:
                i = int(r["out_row"]); line = src_lines[r["source"]][int(r["row"])]
                self.assertEqual(lines[i], line)
                self.assertEqual(int(hce[i]), int(src_hce[r["source"]][int(r["row"])]))
                b = chess.Board(line.decode().split("|")[0])
                exp_meta = (0 if b.turn else 1) | ({"0.0": 0, "0.5": 1, "1.0": 2}[line.decode().split("|")[2].strip()] << 1)
                self.assertEqual(int(meta[i]), exp_meta)

    def test_16_reference_in_two_formats_first_match_wins(self):
        """001 as .pos AND as .txt (a TextRef): same decisions; the first listed reference is the recorded match."""
        o = new_out("tworef")
        rc, so, se = run_tool("merge", "--second", F / "second", "--main", MAIN_POS[0], F / "main" / "forge_selfplay_001.txt",
                              *MAIN_POS[1:], "--holdout", *HOLD_POS, "--second-hce-dir", F / "second_hce", "--out", o)
        self.assertEqual(rc, 0, se)
        assert_matches_reference(self, o, reference(SEALED2, MAIN_TXT, HOLD_TXT))
        s = summary(o); m = {x["name"]: x for x in s["inputs"]["main"]}
        self.assertEqual(m["forge_selfplay_001.txt"]["rows"], m["forge_selfplay_001.pos"]["rows"])
        self.assertEqual(m["forge_selfplay_001.txt"]["matched_pairs"], m["forge_selfplay_001.pos"]["matched_pairs"])
        self.assertGreater(m["forge_selfplay_001.pos"]["matched_pairs"], 0)
        self.assertNotIn("forge_selfplay_001.txt", {r["match_file"] for r in ledger(o) if r["match_role"] == "main"})

    def test_17_bad_lines_fail_closed_like_fen2bin(self):
        src = (F / "second" / "forge_selfplay_001.txt").read_bytes().split(b"\n")
        good, alt = src[0], src[1]          # variants are built from the 2nd line, so an accepted variant is no duplicate
        fen, sc, res = alt.split(b" | ")
        f0 = fen.split(b" "); f0[0] = f0[0].replace(b"k", b"1", 1)
        lines = {"no_black_king": b" ".join(f0) + b" | " + sc + b" | " + res,
                 "two_white_kings": b"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBKKBNR w - - 0 5 | 1 | 0.5",
                 "33_pieces": b"rnbqkbnr/pppppppp/8/8/8/7P/PPPPPPPP/RNBQKBNR w - - 0 5 | 1 | 0.5",
                 "score_out_of_range": fen + b" | 40000 | " + res, "result_2": fen + b" | " + sc + b" | 2.0",
                 "no_bar": fen + b" " + sc + b" " + res, "bad_stm": fen.replace(b" w ", b" x ").replace(b" b ", b" x ") + b" | " + sc + b" | " + res}
        accepted = {"plus_sign_score": fen + b" | +" + sc.lstrip(b"+-") + b" | " + res, "result_1_00": fen + b" | " + sc + b" | 1.00",
                    "extra_spaces": fen + b" |   " + sc + b"   |  " + res}
        for name, line in {**lines, **accepted}.items():
            d = new_out("line_" + name); d.mkdir()
            (d / "forge_selfplay_001.txt").write_bytes(good + b"\n" + line + b"\n")
            rc, so, se = run_tool("merge", "--second", d / "forge_selfplay_001.txt", "--no-hce", "--out", d.with_name(d.name + "_out"))
            if name in lines:
                self.assertEqual(rc, 1, name); self.assertIn("bad line", se, name)
            else:
                self.assertEqual(rc, 0, name + se)
            if FEN2BIN and Path(FEN2BIN).exists():
                p = subprocess.run([FEN2BIN, str(d / "forge_selfplay_001.txt"), str(d / "ref.pos")], capture_output=True, text=True)
                self.assertEqual(p.returncode, 1 if name in lines else 0, name + p.stdout)
                if name not in lines:
                    self.assertEqual((d.with_name(d.name + "_out") / "forge_s40_merged_001.pos").read_bytes(), (d / "ref.pos").read_bytes(), name)

    @unittest.skipUnless(FEN2BIN and Path(FEN2BIN).exists(), "FORGE_S40_FEN2BIN not set")
    def test_13_pos_byte_identical_to_fen2bin(self):
        rc, out, so, se = merge("fen2bin", "--include-part", "--part-committed-bytes", TRUTH["part_committed"]["bytes"],
                                "--rows-per-file", "400", hce=("--no-hce",))
        self.assertEqual(rc, 0, se)
        tmp = new_out("fen2bin_ref"); tmp.mkdir()
        for p in sorted(out.glob("*.txt")):
            ref = tmp / (p.stem + ".pos")
            subprocess.run([FEN2BIN, str(p), str(ref)], check=True, capture_output=True)
            self.assertEqual((out / (p.stem + ".pos")).read_bytes(), ref.read_bytes(), p.name)

    @unittest.skipUnless(HCE_DUMP and Path(HCE_DUMP).exists(), "FORGE_S40_HCE_DUMP not set")
    def test_14_hce_dump_route_equals_subset_route(self):
        rc1, o1, _, se1 = merge("hce_subset", "--rows-per-file", "300")
        rc2, o2, _, se2 = merge("hce_dump", "--rows-per-file", "300", hce=("--hce-dump", HCE_DUMP))
        self.assertEqual((rc1, rc2), (0, 0), se1 + se2)
        for p in sorted(o1.glob("*.hce")):
            self.assertEqual(p.read_bytes(), (o2 / p.name).read_bytes(), p.name)
        rc, o3, _, se = merge("hce_part", "--include-part", "--seen-db", F / "second_db" / "forge_seen_hashes.sqlite3",
                              hce=("--hce-dump", HCE_DUMP))
        self.assertEqual(rc, 0, se); rc, so, se = run_tool("verify", o3); self.assertEqual(rc, 0, so)

    @unittest.skipUnless(V3B and Path(V3B).exists(), "FORGE_S40_V3B not set")
    def test_15_v3b_loader_loads_outputs_unchanged(self):
        spec = importlib.util.spec_from_file_location("v3b_trainer_copy", V3B)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)  # top level only (no main())
        rc, out, so, se = merge("v3b", "--rows-per-file", "300")
        self.assertEqual(rc, 0, se)
        files = sorted(str(p) for p in out.glob("*.pos")); kept = summary(out)["reasons"]["kept"]
        d = mod.load_set(files, str(out)); dm = mod.load_set_mmap(files, str(out))
        self.assertEqual(d["n"], kept); self.assertEqual(dm["n"], kept)
        idx = np.arange(kept)
        for k in ("boards", "score", "meta", "hce"):
            self.assertTrue(np.array_equal(d[k], dm[k][idx]), k)
        boards = np.concatenate([np.fromfile(f, np.uint8, count=32 * TOOL.pos_count(f), offset=16).reshape(-1, 32) for f in files])
        self.assertTrue(np.array_equal(d["boards"], boards))
        hce = np.concatenate([np.fromfile(f[:-4] + ".hce", "<i2", offset=16) for f in files])
        self.assertTrue(np.array_equal(d["hce"], hce))


if __name__ == "__main__":
    unittest.main(verbosity=2)
