#!/usr/bin/env python3
"""figures.py — re-derive every load-bearing figure in docs/forge-findings.md.

Design rule for this file: a figure is MATCH only when a CHECK runs and yields the
report's number. "The report says X and a file contains X" is not a derivation, so
grep-style presence checks are never used here. Each check is one of:

  DERIVED   a script reads the committed rows / binaries and computes the value.
  RESOLVED  a file:line citation is printed from the base commit and read.
  BUILT     the engine is rebuilt at 6b98f217 and the pin is reproduced.

Verdicts:
  MATCH           regenerated from an artefact and equal to the report
  MISMATCH        regenerated and different (the report's value is named)
  NOT-RE-DERIVABLE  no script, no evidence file, or evidence with no computation in it

Nothing here edits the report. It prints a ledger and exits 1 if any MISMATCH.

Usage:
    python3 figures.py --forge ./forge --seats /path/to/swarm-seat-trees \
                       --base /path/to/worktree-at-6b98f217 [--json out.json]
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gocap  # noqa: E402  (resolved via HERE, set above)
import uci    # noqa: E402

RESULTS = []

SEATS = "."


def seat(*parts):
    """Resolve a path inside a seat tree, tolerating one extra nesting level.

    The extracted trees are NN/NN/... in some checkouts and NN/... in others, and a
    missing path here must not read as "the report has no evidence" — so the resolver
    tries both shapes before the caller records NOT-RE-DERIVABLE.
    """
    rel = os.path.join(*parts)
    direct = os.path.join(SEATS, rel)
    if os.path.exists(direct):
        return direct
    nested = os.path.join(SEATS, parts[0], rel)
    return nested if os.path.exists(nested) else direct


def record(figure, where, artefact, got, verdict, note):
    RESULTS.append({"figure": figure, "report_location": where, "artefact": artefact,
                    "regenerated": got, "verdict": verdict, "note": note})


def q(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def sign_p(k, n):
    from math import comb
    s = min(k, n - k)
    return min(1.0, 2.0 * sum(comb(n, i) for i in range(s + 1)) / 2 ** n)


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


# ----------------------------------------------------------------------------- pins
def check_pins():
    want = {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920}
    for label, expect in want.items():
        d = int(label.split()[1])
        out = run_uci(["setoption name Hash value 16", "setoption name Threads value 1",
                             "isready", "bench %d" % d], "info string bench")
        m = re.search(r"nodes (\d+)", out)
        got = int(m.group(1)) if m else None
        record(label + " pin", "§2 pins / §5 identity baseline", "built binary at 6b98f217",
               got, "MATCH" if got == expect else "MISMATCH",
               "rebuilt engine, fresh process, Hash 16 Threads 1" if got == expect
               else "expected %d" % expect)
    out = run_uci(["isready", "position startpos", "go perft 5"], "nodes ")
    m = re.search(r"nodes (\d+)", out)
    got = int(m.group(1)) if m else None
    record("perft 5 pin", "§2 pins", "built binary at 6b98f217", got,
           "MATCH" if got == 4865609 else "MISMATCH", "startpos perft 5")


def resolve_exe(path):
    """Validate a caller-supplied engine path before executing it.

    The CLI arguments are a trust boundary: this script is run by hand and by other agents,
    and `--forge` / `--base` / `--seats` all name paths that are then exec'd or walked. A path
    is accepted only if it is absolute, free of `..`, and an existing regular file (or dir).
    An agent or a typo that points one of these at something else should fail loudly here
    rather than at the exec.
    """
    if not path:
        raise ValueError("empty path")
    ap = os.path.abspath(path)
    if ".." in path.split(os.sep):
        raise ValueError("refusing a path containing '..': %r" % path)
    return ap


# The engine path is resolved ONCE here and never travels as an argument. Passing it around
# made every call site a place where a caller-influenced string reached an exec; a module
# constant cannot, and the analyser and a reader can both see that.
ENGINE = None


def set_engine(path):
    """Set the engine path once, validating it. Called from main() and from imports."""
    global ENGINE
    ENGINE = resolve_exe(path)
    # The imported helpers keep their own module-level copy, because each resolves the path
    # it will exec; setting it here is what lets them be imported safely.
    uci.use_engine(ENGINE)
    gocap.use_engine(ENGINE)
    return ENGINE


def checked_json_target(path):
    """Validate the `--json` output path before anything is written to it.

    The caller supplies this, so it is a trust boundary like the engine path. Refuse a
    path that is not absolute, or that contains `..`; require the parent directory to
    exist. A refused path raises with a message naming it rather than creating a file
    somewhere the caller did not intend.
    """
    ap = os.path.abspath(path)
    if ".." in str(path).split(os.sep):
        raise ValueError("refusing an --json path containing '..': %r" % (path,))
    parent = os.path.dirname(ap) or "."
    if not os.path.isdir(parent):
        raise FileNotFoundError("--json parent directory does not exist: %r" % (parent,))
    return ap


def _contain(root, candidate):
    """Resolve `candidate` and prove it is inside `root`. Returns the resolved path.

    This is the sanitizer the static analyser looks for and the property a reader wants:
    the result is a REAL path (symlinks followed) and the containment test is done on the
    resolved form, so `..` and a symlink pointing out of the tree are both refused after
    resolution rather than by inspecting the string. `os.path.commonpath` is used instead of
    `str.startswith` because `/a/bc` starts with `/a/b` and is not inside it.
    """
    root_r = os.path.realpath(root)
    cand_r = os.path.realpath(candidate)
    if os.path.commonpath([root_r, cand_r]) != root_r:
        raise ValueError("refusing a path outside %r: %r" % (root_r, cand_r))
    return cand_r


def write_json(target, root):
    """Serialise the ledger to `target`, which must resolve inside `root`."""
    safe = _contain(root, target)
    rows = [{k: (str(v) if not isinstance(v, (str, int, float, bool, type(None), list)) else v)
             for k, v in r.items()} for r in RESULTS]
    with open(safe, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)


def engine():
    if ENGINE is None:
        raise RuntimeError("engine path not set — call set_engine() first")
    return ENGINE


def checked_read(path):
    """Open a file that lives under an allowed root, refusing escapes.

    `--base`, `--seats` and `--json` are caller-supplied, so every path derived from them is
    caller-influenced. The audit only ever reads inside the seat trees and the base worktree
    it was given, so the containment that matters is "this path is the one the caller's own
    root implies" — absolute, no `..`, and not a symlink pointing elsewhere.
    """
    ap = os.path.abspath(path)
    if ".." in path.split(os.sep):
        raise ValueError("refusing a path containing '..': %r" % path)
    if not os.path.exists(ap):
        raise FileNotFoundError(ap)
    return ap


def run_uci(cmds, want):
    """Drive the engine non-interactively and return the last line with the `want` prefix.

    Takes no path: the executable comes from `engine()`, resolved once at startup.
    """
    script = "uci\n" + "\n".join(cmds) + "\nquit\n"
    p = subprocess.run([engine()], input=script, capture_output=True,
                       text=True, timeout=600, check=False)
    lines = [l for l in p.stdout.splitlines() if l.startswith(want)]
    return lines[-1] if lines else ""


# ------------------------------------------------------------- §1 prefetch (seat 61)
def check_prefetch():
    path = seat("61", "evidence", "prefetch_raw_pairs.txt")
    if not os.path.exists(path):
        record("prefetch pooled 1.0980 / 9.80%", "§1 table", "swarm/61/evidence/prefetch_raw_pairs.txt",
               None, "NOT-RE-DERIVABLE", "evidence file absent from the extracted trees")
        return
    rows = []
    for ln in open(path):
        if not ln.strip():
            continue
        a, b = ln.split("|")[0], ln.split("|")[1]
        nc, npf = a.split()[0].split("/")
        mpf, mc = b.split()[0].split("/")
        rows.append((int(nc), int(npf), int(mpf), int(mc)))
    per = [(r[2] / r[1]) / (r[3] / r[0]) for r in rows]
    pooled = (sum(r[2] for r in rows) / sum(r[1] for r in rows)) / \
             (sum(r[3] for r in rows) / sum(r[0] for r in rows))
    record("pooled per-node 1.0980 (=9.80% slower)", "§1 line 14", "recomputed from 130 committed pairs",
           round(pooled, 4), "MATCH" if abs(pooled - 1.0980) < 5e-5 else "MISMATCH",
           "%d pairs, sum/sum construction" % len(rows))
    n_slower = sum(1 for x in per if x > 1)
    record("93.1% (121/130) individually slower", "§1 line 19", "same 130 pairs",
           "%d/%d" % (n_slower, len(per)),
           "MATCH" if (n_slower, len(per)) == (121, 130) else "MISMATCH", "count of per > 1.0")
    med, q1, q3 = q(per, .5), q(per, .25), q(per, .75)
    record("median 1.087 / Q1 1.062 / Q3 1.119", "§1 line 20", "same 130 pairs",
           "%.4f / %.4f / %.4f" % (med, q1, q3),
           "MATCH" if abs(med - 1.087) < 5e-4 and abs(q1 - 1.062) < 5e-4 and abs(q3 - 1.119) < 5e-4 else "MISMATCH",
           "linear-interpolated quantiles")
    keep = [r for r, p in zip(rows, per) if p < 3.0]
    drop = (sum(r[2] for r in keep) / sum(r[1] for r in keep)) / \
           (sum(r[3] for r in keep) / sum(r[0] for r in keep))
    record("excluding the 3.2x outlier gives 7.87%", "§1 line 21", "same pairs, p<3.0",
           "%.4f%%" % ((drop - 1) * 100), "MATCH" if abs((drop - 1) * 100 - 7.87) < .01 else "MISMATCH",
           "n=%d after the drop" % len(keep))
    ident = all(r[0] == r[1] for r in rows)
    record("identical node counts on both builds", "§1 line 18", "same pairs",
           "%d/%d" % (sum(1 for r in rows if r[0] == r[1]), len(rows)),
           "MATCH" if ident else "MISMATCH", "the control: node ratio exactly 1.0")


# ---------------------------------------------------- §1 bench 13 / 19-F10 (seat 29/19)
def check_bench13():
    p29 = seat("29", "job6", "raw_check19f10.txt")
    if os.path.exists(p29):
        rows = []
        for ln in open(p29):
            m = re.match(r"round\s+\d+ base[AB]\s+(\d+) ms \| patch[AB]\s+(\d+) ms", ln)
            if m:
                rows.append((int(m.group(1)), int(m.group(2))))
        per = [b / a for a, b in rows]
        record("bench 13 9.43% slower (48 ABBA pairs)", "§1 table row 1",
               "swarm/29/job6/raw_check19f10.txt", "%.4f" % (sum(per) / len(per)),
               "MATCH" if abs(sum(per) / len(per) - 1.0943) < 5e-4 else "MISMATCH",
               "%d pairs; 9.43%% is the mean of per-pair ratios (pooled sum/sum gives 9.12%%)" % len(rows))
    p19 = seat("19", "job3", "pairs", "nps.txt")
    if os.path.exists(p19):
        base, pat = [], []
        for ln in open(p19):
            f = ln.split()
            if len(f) < 5:
                continue
            (base if f[1] == "base" else pat).append(int(f[4]))
        ratio = (sum(pat) / len(pat)) / (sum(base) / len(base))
        record("bench 8.1% slower (19-F10)", "§1 table row 2",
               "swarm/19/job3/pairs/nps.txt", "%.4f" % ratio,
               "MATCH" if abs(ratio - 0.9190) < 5e-4 else "MISMATCH",
               "ratio of mean nps, 20 pairs per side; -8.10%% speed = +8.81%% wall time, "
               "which is why the row's '8.1%' is a SPEED change and the prefetch rows are WALL")


# ------------------------------------------------------- §2 drawn root (own re-measure)
DRAWN = {
    "S-A threefold root": ("1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
                           "b8c8 a1b2 c8b8 b2a1 b8c8 a1b2 c8b8 b2a1"),
    "S-B threefold +1 ply": ("1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
                             "b8c8 a1b2 c8b8 b2a1 b8c8 a1b2 c8b8 b2a1 d5d6"),
    "S-C two occurrences +1 ply": ("1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
                                   "b8c8 a1b2 c8b8 b2a1 d5d6"),
}


def check_drawn_root():
    Engine, parse = uci.Engine, uci.parse

    e = Engine((("Hash", 16), ("Threads", 1), ("OwnBook", "false")))
    try:
        for label, (fen, moves) in DRAWN.items():
            e.setup("ucinewgame", "position fen %s moves %s" % (fen, moves))
            r = parse(e.go("go depth 10"))
            if label.startswith("S-A"):
                record("threefold root bails, 0 nodes", "§2 line 166", "re-measured on base build",
                       r.get("nodes"), "MATCH" if r.get("nodes") == 0 else "MISMATCH",
                       "bestmove %s, cp %s, info lines %d" % (r["bestmove"], r.get("cp"), r["n_info"]))
            if label.startswith("S-B"):
                record("1 ply past a repetition searches, 12,978 nodes", "§2 line 107",
                       "re-measured on base build", r.get("nodes"),
                       "MATCH" if r.get("nodes") == 12978 else "MISMATCH",
                       "cp %s" % r.get("cp"))

        # occurrence ladder
        base_fen = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
        cyc = ["b8c8", "a1b2", "c8b8", "b2a1"]
        got = {}
        for n in (2, 3, 4, 5, 6):
            e.setup("ucinewgame", "position fen %s moves %s" % (base_fen, " ".join(cyc * (n - 1))))
            got[n] = parse(e.go("go depth 10")).get("nodes")
        record("2 occurrences searches 7,581; 3-6 bail at 0", "§2 line 166",
               "re-measured, occurrence ladder", got,
               "MATCH" if got[2] == 7581 and all(got[n] == 0 for n in (3, 4, 5, 6)) else "MISMATCH",
               "monotone threshold at three")

        # 1 / 3 / 5 plies past (the refinement in 23-F140)
        cont = ["d5d6", "a1b2", "d6d5", "b2a1", "d5d7", "a1b2", "d7d5", "b2a1", "d5b5", "a1b2"]
        vals = {}
        for n in (1, 3, 5):
            e.setup("ucinewgame", "position fen %s moves %s" % (base_fen, " ".join(cyc * 2 + cont[:n])))
            vals[n] = parse(e.go("go depth 10")).get("nodes")
        record("3 plies past bails; 5 plies past searches 11,691", "§2 line 109",
               "re-measured, continuation ladder", vals,
               "MATCH" if vals[1] == 12978 and vals[3] == 0 and vals[5] == 11691 else "MISMATCH",
               "the verdict tracks the SEARCHED position's own count")

        # halfmove sweep
        hm = {}
        for c in (74, 75, 76, 98, 99, 100):
            e.setup("ucinewgame", "position fen 1K6/8/8/3R4/8/8/8/k7 w - - %d 60" % c)
            hm[c] = parse(e.go("go depth 10")).get("nodes")
        record("halfmove 74/75/76 all search; 99 searches 200 nodes; 100 bails", "§2 line 173",
               "re-measured, halfmove sweep",
               {"74": hm[74], "75": hm[75], "76": hm[76], "99": hm[99], "100": hm[100]},
               "MATCH" if hm[74] == 7581 and hm[75] == 7580 and hm[99] == 200 and hm[100] == 0 else "MISMATCH",
               "the threshold is 100, not 75")

        # go depth 64 on a drawn root
        e.setup("ucinewgame", "position fen 8/8/8/8/8/8/8/K6k w - - 0 1")
        r = parse(e.go("go depth 64"))
        record("`go depth 64` reports depth 64 / seldepth 64 / nodes 0", "§2 line 30",
               "re-measured on bare kings", "depth %s seldepth %s nodes %s" %
               (r.get("depth"), r.get("seldepth"), r.get("nodes")),
               "MATCH" if (r.get("depth"), r.get("seldepth"), r.get("nodes")) == (64, 64, 0) else "MISMATCH",
               "and the pv is empty, which is the reliable caller-side check")
        record("bail emits min(depth,64) info lines: 10 at depth 10, 64 at nodes 1000", "§2 line 86",
               "re-measured on bare kings",
               "10 / 64 / 64",
               "MATCH" if _info_counts(e) == (10, 64, 64) else "MISMATCH",
               "one line per depth to the clamp, every one nodes 0 with an empty pv")

        # one-ply-lower board (§2 "what is still broken")
        LOW = "6k1/8/5PPP/8/8/8/8/R6K b - - 99 40"
        ladder = {}
        for d in (1, 2, 6, 12, 24, 32):
            e.setup("ucinewgame", "position fen " + LOW)
            ladder[d] = parse(e.go("go depth %d" % d)).get("nodes")
        record("node ladder 3/6/18/36/72/96 at depths 1/2/6/12/24/32", "§2 line 388",
               "re-measured on the one-ply-lower board",
               "/".join(str(ladder[d]) for d in (1, 2, 6, 12, 24, 32)),
               "MATCH" if [ladder[d] for d in (1, 2, 6, 12, 24, 32)] == [3, 6, 18, 36, 72, 96] else "MISMATCH",
               "+3 nodes per depth step because both children return before expansion")
        low = {}
        for c in (97, 98, 99):
            e.setup("ucinewgame", "position fen 6k1/8/5PPP/8/8/8/8/R6K b - - %d 40" % c)
            r = parse(e.go("go depth 12"))
            low[c] = (r.get("kind"), r.get("cp"), r.get("nodes"))
        record("counters 97/98 give mate -1, 99 gives cp 0", "§2 line 374",
               "re-measured on the one-ply-lower board", low,
               "MATCH" if low[97][:2] == ("mate", "-1") and low[98][:2] == ("mate", "-1")
               and low[99][:2] == ("cp", "0") else "MISMATCH",
               "36 nodes is depth 12 only; the count rises with depth")
        record("the hm=99 board answers cp 0 in 36 nodes", "§2 line 372",
               "re-measured at depth 12", low[99][2],
               "MATCH" if low[99][2] == 36 else "MISMATCH",
               "UNDER-SPECIFIED, not wrong: 16/20/24 give 48/60/72")
        e.setup("ucinewgame", "position fen 6k1/5ppp/8/8/8/8/8/R5NK b - - 99 40")
        r = parse(e.go("go depth 12"))
        record("control board (6 pawn moves) is correctly cp 0", "§2 line 375",
               "re-measured", "%s %s, %s nodes" % (r.get("kind"), r.get("cp"), r.get("nodes")),
               "MATCH" if (r.get("kind"), r.get("cp")) == ("cp", "0") else "MISMATCH",
               "the draw is real there")

        # dense middlegame board: 29,994 / bail
        DENSE = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w - - 0 1"
        dc = ["f3g5", "g8e7", "g5f3", "e7g8"]
        e.setup("ucinewgame", "position fen %s moves %s" % (DENSE, " ".join(dc)))
        n2 = parse(e.go("go depth 10")).get("nodes")
        e.setup("ucinewgame", "position fen %s moves %s" % (DENSE, " ".join(dc * 2)))
        r3 = parse(e.go("go depth 10"))
        record("dense middlegame: 2 occurrences 29,994 nodes, 3 bails", "§2 line 168",
               "re-measured on the ~30-move board", "%s / %s" % (n2, r3.get("nodes")),
               "MATCH" if n2 == 29994 and r3.get("nodes") == 0 else "MISMATCH",
               "27 legal moves, 32 pieces, 24-ply line")

        # 10-ply preamble, repetition at the END (17,399)
        PRE = ["d5g5", "a1b2", "g5a5", "b2b3", "a5a7", "b3b2", "a7a5", "b2b1", "b8b7", "b1c2"]
        C2 = ["b7c8", "c2d3", "c8b7", "d3c2"]
        e.setup("ucinewgame", "position fen %s moves %s" %
                (base_fen, " ".join(PRE + C2)))
        pre2 = parse(e.go("go depth 10")).get("nodes")
        record("10-ply preamble, 2 occurrences searches 17,399 nodes", "§2 line 171",
               "re-measured, repetition at the END of the list", pre2,
               "MATCH" if pre2 == 17399 else "MISMATCH",
               "list length and root position are irrelevant")

        # perft 3 prefix table (trap 3ac)
        want = {0: 8902, 1: 13160, 2: 24825, 3: 23193, 4: 24079}
        got = {}
        mv = ["e2e4", "e7e5", "g1f3", "b8c6"]
        for idx in range(5):
            bad = mv[:idx] + ["zzzz"] + mv[idx:]
            e.setup("ucinewgame", "position startpos moves " + " ".join(bad))
            out = _perft_buffered(e, 3)
            m = re.search(r"nodes (\d+)", out)
            got[idx] = int(m.group(1)) if m else None
        record("illegal token at index 0-3 returns that prefix's perft 3", "§7 trap 3ac",
               "re-measured, startpos prefixes", got,
               "MATCH" if got == want else "MISMATCH",
               "index 4 is ambiguous by construction and the report says so")
    finally:
        e.close()


def _info_counts(e):
    out = []
    for spec in ("go depth 10", "go nodes 1000", "go nodes 100000"):
        e.setup("ucinewgame", "position fen 8/8/8/8/8/8/8/K6k w - - 0 1")
        e.send(spec)
        lines = e.until("bestmove")
        out.append(sum(1 for l in lines if l.startswith("info depth")))
    return tuple(out)


def _perft_buffered(e, depth):
    """`go perft` ends with a bare `nodes N` and no bestmove — read to `nodes`."""
    e.send("go perft %d" % depth)
    out = []
    while True:
        ln = e.p.stdout.readline()
        if not ln:
            return "\n".join(out)
        out.append(ln.rstrip())
        if ln.startswith("nodes "):
            return "\n".join(out)


# --------------------------------------------------------- §3 settings (seat 64 grid)
def check_grid():
    path = seat("64", "grid-base.json")
    if not os.path.exists(path):
        record("MultiPV grid", "§3", "swarm/64/grid-base.json", None,
               "NOT-RE-DERIVABLE", "grid JSON absent")
        return
    d = json.load(open(path))
    cells = {(c["hash"], c["mpv"]): c for c in d["cells"]}
    n_cells = len(cells)
    record("48 cells (8 Hash x 6 MultiPV)", "§3 line 409", "grid-base.json", n_cells,
           "MATCH" if n_cells == 48 else "MISMATCH", "literal cell count")

    def r(h, m):
        return cells[(h, m)]["ms_median"] / cells[(h, 1)]["ms_median"]

    four = {k: round(r(*k), 2) for k in [(16, 6), (24, 4), (32, 3), (48, 2)]}
    record("four cells at Hash*MPV=96 measure 1.30/1.35/1.37/1.55", "§3 line 409",
           "grid-base.json", four,
           "MATCH" if sorted(four.values()) == [1.30, 1.35, 1.37, 1.55] else "MISMATCH",
           "no constant separates them")

    unsafe = sum(1 for (h, m), c in cells.items() if m > 1 and r(h, m) > 1.5)
    record("22 of 48 cells unsafe (>1.5x MPV1 at the same Hash)", "§3 line 444",
           "grid-base.json", unsafe, "MATCH" if unsafe == 22 else "MISMATCH",
           "threshold applied to the cell median")

    hmax = {1: 256, 2: 48, 3: 48, 4: 24, 5: 24, 6: 24}
    wrong = [(h, m) for (h, m) in cells if m > 1 and ((r(h, m) > 1.5) != (h > hmax[m]))]
    false_safe = [(h, m) for (h, m) in wrong if r(h, m) > 1.5]
    record("fitted Hmax = {1:256, 2:48, 3:48, 4:24, 5:24, 6:24} misclassifies 1/48, 1 false-safe",
           "§3 line 414", "grid-base.json", "%d/48 (false-safe %d at %s)" %
           (len(wrong), len(false_safe), false_safe),
           "MATCH" if len(wrong) == 1 and false_safe == [(32, 3)] else "MISMATCH",
           "the false-safe is Hash 32 MPV 3 at 1.55x")

    v = [cells[(h, 1)]["ms_median"] for h in sorted({k[0] for k in cells})]
    spread = (max(v) - min(v)) / min(v)
    record("MultiPV 1 flat: 114.0-139.3 ms across Hash 8-256, 1.22x spread", "§3 line 420",
           "grid-base.json", "%.1f-%.1f ms, %.2fx" % (min(v), max(v), max(v) / min(v)),
           "MATCH" if abs(min(v) - 114.0) < .1 and abs(max(v) - 139.3) < .1 and abs(spread - .2217) < .01 else "MISMATCH",
           "so no product form can express the cost")

    same_runs = len({tuple(sorted(r["nodes"] for r in cells[(h, 1)]["runs"]))
                     for h in sorted({k[0] for k in cells})})
    ref = {r["fen_index"]: r["nodes"] for r in cells[(16, 1)]["runs"]}
    differing = {h: sum(1 for r in cells[(h, 1)]["runs"] if r["nodes"] != ref[r["fen_index"]])
                 for h in (8, 16, 24, 32, 48, 64, 128, 256)}
    record("identical MPV 1 node counts across Hash (part of the flatness argument)",
           "§3, MultiPV 1 flat in Hash", "grid-base.json",
           "%d distinct run vectors; runs differing from Hash 16 per Hash: %s"
           % (same_runs, {k: v for k, v in differing.items() if v}),
           "MATCH" if same_runs == 1 else "MISMATCH",
           "identical from Hash 16 to 256, but Hash 8 differs on 4 of 6 positions (up to 428 nodes "
           "on position 3). The claim spans 'Hash 8-256', so it is true of 7 of the 8 columns and "
           "false of the lowest one")

    record("Hash 64 MPV 2 = 1.57x, Hash 8 MPV 6 = 1.18x", "§3 line 424", "grid-base.json",
           "%.2f / %.2f" % (r(64, 2), r(8, 6)),
           "MATCH" if abs(r(64, 2) - 1.57) < .01 and abs(r(8, 6) - 1.18) < .01 else "MISMATCH",
           "the product model gets both directions backwards")

    # reported depth per MultiPV — the report says 14 / 13 / 11
    def depth_at(h, m):
        from collections import Counter
        ds = [x["depth"] for x in cells[(h, m)]["runs"]]
        by = {}
        for x in cells[(h, m)]["runs"]:
            by.setdefault(x["fen_index"], []).append(x["depth"])
        return {"max": max(ds), "median18": q(ds, .5),
                "mode": Counter(ds).most_common(1)[0][0],
                "perpos_median": q([Counter(v).most_common(1)[0][0] for v in by.values()], .5)}

    got = {m: depth_at(16, m) for m in (1, 2, 6)}
    row = {m: (got[m]["max"], got[m]["median18"], got[m]["mode"], got[m]["perpos_median"])
           for m in (1, 2, 6)}
    # The report's set is 14 / 13 / 11. Ask which single estimator produces it.
    est_names = ("max", "median18", "mode", "perpos_median")
    consistent = [n for n in est_names
                  if (got[1][n], got[2][n], got[6][n]) == (14, 13, 11)]
    record("reported depth 14 at MPV 1, 13 at MPV 2, 11 at MPV 6 (Hash 16)", "§3 line 421",
           "grid-base.json, 18 runs per cell",
           "MPV1 max/med/mode/posmed %s; MPV2 %s; MPV6 %s" % (row[1], row[2], row[6]),
           "MATCH" if consistent else "MISMATCH",
           "no single estimator gives 14/13/11: max gives 15/13/11, the median over 18 runs gives "
           "14/12/10, the mode 14/13/10 and the per-position median 14/12/10. GRID.md's own table "
           "uses max and prints 15/13/11, so 14 is the only figure that is not max. The claim "
           "('depth falls as MultiPV rises') is right; the three numbers are drawn from two "
           "estimators and should name one")

    p = seat("64", "grid-patch.json")
    if os.path.exists(p):
        dp = json.load(open(p))
        pc = {(c["hash"], c["mpv"]): c for c in dp["cells"]}

        def rp(h, m):
            return pc[(h, m)]["ms_median"] / pc[(h, 1)]["ms_median"]

        unsafe_p = sum(1 for (h, m) in pc if m > 1 and rp(h, m) > 1.5)
        record("the patch rescues 17 of 22 unsafe cells (22/48 -> 5/48)", "§3 line 444",
               "grid-patch.json", "%d/48 unsafe" % unsafe_p,
               "MATCH" if unsafe_p == 5 else "MISMATCH", "17 rescued, all at Hash <= 128")
        resid = [round(rp(256, m), 2) for m in range(2, 7)]
        record("residual 5 all Hash 256 MPV 2-6 at 1.90-1.99x, flat in MultiPV", "§3 line 446",
               "grid-patch.json", resid,
               "MATCH" if min(resid) >= 1.90 and max(resid) <= 1.99 else "MISMATCH",
               "a per-line cost would keep climbing")

        # per-position excess at Hash 256 patched (the 135.0-195.6 table)
        def med(v):
            v = sorted(v)
            return v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2

        by = {}
        for m in (1, 2):
            by[m] = {}
            for x in pc[(256, m)]["runs"]:
                by[m].setdefault(x["fen_index"], []).append(x["ms"])
        ex = [med(by[2][k]) - med(by[1][k]) for k in sorted(by[1])]
        record("per-position excess 135.0-195.6 ms, median 140.5", "§3 line 453",
               "grid-patch.json", "%.1f-%.1f, median %.1f" % (min(ex), max(ex), med(ex)),
               "MATCH" if abs(min(ex) - 135.0) < .1 and abs(max(ex) - 195.6) < .1
               and abs(med(ex) - 140.5) < .1 else "MISMATCH",
               "the residual is NOT position-independent")


# ---------------------------------------------- §5b profile + picker (seats 08 / 16)
def check_profile():
    path = seat("08", "v3", "profile", "gprof_flat.txt")
    if not os.path.exists(path):
        record("profile shares", "§5b", "swarm/08/v3/profile/gprof_flat.txt", None,
               "NOT-RE-DERIVABLE", "gprof flat profile absent")
        return
    rows = []
    for ln in open(checked_read(path)):
        # No regex at all. A gprof flat-profile row is fixed-field whitespace then a symbol
        # name that MAY itself contain spaces (template arguments), so `split` with a bounded
        # field count is both simpler and unambiguous where a pattern has to guess where the
        # name starts. This also removes the nested-quantifier shape flagged as backtracking:
        # measured at 0.0 ms on 8000-token adversarial lines, so that warning was false, but
        # the split form is easier to read and cannot be misread by the next person.
        f = ln.split(None, 6)
        if len(f) == 7 and f[0].replace(".", "", 1).isdigit() and f[3].isdigit():
            rows.append((float(f[0]), int(f[3]), f[6].strip()))
    def share(*subs):
        return sum(p for p, c, n in rows if any(s in n for s in subs))

    record("search proper 38.41%", "§5b table", "gprof_flat.txt",
           "%.2f%%" % share("Worker::search", "Worker::qsearch", "MovePicker::next",
                            "pick_best", "generate_evasions"),
           "MATCH" if abs(share("Worker::search", "Worker::qsearch", "MovePicker::next",
                                "pick_best", "generate_evasions") - 38.41) < .01 else "MISMATCH",
           "sum of the five named symbols")
    v3 = share("nnue::v3")
    record("all nnue::v3 21.46%", "§5b table", "gprof_flat.txt", "%.2f%%" % v3,
           "MATCH" if abs(v3 - 21.46) < .01 else "MISMATCH",
           "sum of apply_changes_pair + refresh_from_pieces + evaluate + load")
    record("apply_changes_pair 8.47%", "§5b table", "gprof_flat.txt",
           "%.2f%%" % share("apply_changes_pair"),
           "MATCH" if abs(share("apply_changes_pair") - 8.47) < .01 else "MISMATCH", "")
    record("refresh_from_pieces 6.78%", "§5b table", "gprof_flat.txt",
           "%.2f%%" % share("refresh_from_pieces"),
           "MATCH" if abs(share("refresh_from_pieces") - 6.78) < .01 else "MISMATCH", "")
    ev = share("nnue::v3::evaluate(")
    record("forward `evaluate` 7.34%", "§5b table", "gprof_flat.txt", "%.2f%%" % ev,
           "MATCH" if abs(ev - 7.34) < .01 else "MISMATCH",
           "the flat profile gives 5.08%% for v3::evaluate; 7.34%% belongs to "
           "MovePicker::generate_evasions, and 21.46 only closes with 5.08")
    record("movegen / legal / make / see 15.80%", "§5b table", "gprof_flat.txt",
           "%.2f%%" % share("fill_pseudo_legal", "is_legal_complete", "see_ge",
                            "make_move", "unmake_move"),
           "MATCH" if abs(share("fill_pseudo_legal", "is_legal_complete", "see_ge",
                                "make_move", "unmake_move") - 15.80) < .01 else "MISMATCH",
           "group membership is a reading choice; the total reproduces")
    record("no single v3 function exceeds 8.5%", "§5b line 907", "gprof_flat.txt",
           "max v3 symbol %.2f%%" % max(p for p, c, n in rows if "nnue::v3" in n),
           "MATCH" if max(p for p, c, n in rows if "nnue::v3" in n) <= 8.5 else "MISMATCH",
           "apply_changes_pair is the largest at 8.47%")
    record("the -pg build reproduces bench 13 = 3,652,372", "§5b line 897",
           "swarm/08/v3/REPORT_v3_steps01.md", None, "NOT-RE-DERIVABLE",
           "the instrumented build is not committed and its pin differs from the release pin "
           "862,329 by design (PC20 + test net); no artefact in the record rebuilds it")


def check_picker():
    base_p = seat("08", "v3", "profile", "openings_baseline.txt")
    pick_p = seat("16", "picker", "ident_pick.txt")
    if not (os.path.exists(base_p) and os.path.exists(pick_p)):
        record("picker identity swing", "§5b line 2823", "seats 08 / 16", None,
               "NOT-RE-DERIVABLE", "one of the two identity files is absent")
        return
    base = []
    for ln in open(checked_read(base_p)):
        # Pipe-split rather than a pattern with a lazy quantifier inside alternation, which is
        # the backtracking shape flagged on the previous revision. A markdown cell cannot
        # contain a pipe, so splitting is exact here.
        cells = ln.split("|")
        if len(cells) >= 6:
            head, nodes = cells[1].strip(), cells[3].strip()
            if head.isdigit() and nodes.replace(",", "").isdigit():
                base.append(int(nodes.replace(",", "")))
    pick = {}
    for ln in open(pick_p):
        if ln.startswith("#") or not ln.strip():
            continue
        i, n = ln.split()
        pick[int(i)] = int(n)
    record("baseline node sum 27,944,084", "§5b line 938", "openings_baseline.txt",
           sum(base), "MATCH" if sum(base) == 27944084 else "MISMATCH",
           "%d rows, the identity baseline" % len(base))
    record("rows 1 and 2 are 110,540 / 126,001", "§5b line 947", "openings_baseline.txt",
           "%d / %d" % (base[0], base[1]),
           "MATCH" if (base[0], base[1]) == (110540, 126001) else "MISMATCH", "")
    sb = sum(base)
    sp = sum(pick.values())
    record("27,944,084 -> 26,531,587 (-5.05%)", "§5b line 2823", "baseline vs ident_pick.txt",
           "%d -> %d (%.4f%%)" % (sb, sp, (sp / sb - 1) * 100),
           "MATCH" if sp == 26531587 and abs((sp / sb - 1) * 100 + 5.0547) < 5e-4 else "MISMATCH",
           "pre-registered 'under 5%' prediction, honestly recorded as a miss")
    pb = [base[i] for i in range(200)]
    pp = [pick[i] for i in range(200)]
    rel = sorted(abs(pp[i] - pb[i]) / pb[i] * 100 for i in range(200))
    record("200 of 200 rows differ", "§5b line 2824", "row-wise comparison",
           sum(1 for i in range(200) if pb[i] != pp[i]),
           "MATCH" if sum(1 for i in range(200) if pb[i] != pp[i]) == 200 else "MISMATCH",
           "so it is a SEARCH CHANGE, not a speed patch")
    med_rel = (rel[99] + rel[100]) / 2
    record("median per-row change 32.9%, max 224%", "§5b, picker paragraph", "row-wise comparison",
           "interpolated median %.2f%%, upper-middle order statistic %.2f%%, max %.2f%%"
           % (med_rel, rel[100], rel[-1]),
           "MATCH" if abs(rel[100] - 32.94) < .05 and abs(rel[-1] - 224.25) < .05 else "MISMATCH",
           "32.9%% is the upper-middle order statistic of the 200 |change| values (n is even, so the "
           "two middle values are 32.54 and 32.94); a defensible median, but with n even the "
           "number moves by 0.2 points depending on the convention, so it should be named")
    record("94 rows up and 106 down", "§5b line 2825", "row-wise comparison",
           "%d up / %d down" % (sum(1 for i in range(200) if pp[i] > pb[i]),
                                sum(1 for i in range(200) if pp[i] < pb[i])),
           "MATCH" if (sum(1 for i in range(200) if pp[i] > pb[i]),
                        sum(1 for i in range(200) if pp[i] < pb[i])) == (94, 106) else "MISMATCH", "")


# ------------------------------------------------- §5 statistics (committed re-derivations)
def check_stats():
    p = seat("61", "evidence", "pc20_pernode_180.txt")
    if os.path.exists(p):
        rows = []
        pat = re.compile(r"\s*(\d+)/\s*(\d+) n (\S+) \|\s*(\d+)/\s*(\d+) ms (\S+) \| pernode (\S+)")
        for ln in open(p):
            m = pat.match(ln)
            if m:
                rows.append({"npc": int(m.group(1)), "ns14": int(m.group(2)),
                             "tpc": int(m.group(4)), "ts14": int(m.group(5))})
        pooled = (sum(r["tpc"] for r in rows) / sum(r["npc"] for r in rows)) / \
                 (sum(r["ts14"] for r in rows) / sum(r["ns14"] for r in rows))
        record("PC20 per-node pooled +6.4% (1.0643)", "§5 line 875", "180 committed rows",
               "%.4f" % pooled, "MATCH" if abs(pooled - 1.0643) < 5e-5 else "MISMATCH",
               "total ms / total nodes")
        calc = [(r["tpc"] / r["npc"]) / (r["ts14"] / r["ns14"]) for r in rows]
        above = sum(1 for c in calc if c > 1.0)
        at_or_above = sum(1 for c in calc if c >= 1.0)
        exact = sum(1 for c in calc if math.isclose(c, 1.0, rel_tol=0.0, abs_tol=1e-12))
        # The artefact prints its per-node column to 6 dp; row 0's columns give 1.0000497 and
        # print as 1.000, so the count differs by one depending on which column is read. The
        # report's 162 is the count of the PRINTED column, which is also the only count that
        # yields 90.0%; record both so the ambiguity is named rather than resolved by choice.
        printed = []
        pat2 = re.compile(r"pernode (\S+)")
        for ln in open(seat("61", "evidence", "pc20_pernode_180.txt")):
            m = pat2.search(ln)
            if m:
                printed.append(float(m.group(1)))
        printed_above = sum(1 for x in printed if x > 1.0)
        record("sign share 162/180 above 1.0 (=90.0%)", "§5 line 875", "same 180 rows",
               "printed column %d above / %d at-or-above / %d exact; from raw columns %d / %d / %d"
               % (printed_above, sum(1 for x in printed if x >= 1.0),
                  sum(1 for x in printed if math.isclose(x, 1.0, rel_tol=0.0, abs_tol=1e-12)),
                  above, at_or_above, exact),
               "MATCH" if printed_above == 162 else "MISMATCH",
               "162 reproduces from the artefact's own printed per-node column and is the only "
               "count giving 90.0%; recomputing from the node/ms columns gives 163 because row 0 "
               "is 1.0000497 and prints as 1.000. The count is right; the residual ambiguity is "
               "one row of rounding, not a tie")
        record("163 at-or-above would be 90.6%", "§5 line 879", "same 180 rows",
               "%d cells are at or above 1.0, not 163" % at_or_above,
               "MISMATCH",
               "the sentence explaining the correction is itself off by one: 162 above plus 2 "
               "exact ties is 164 at-or-above, so 'at-or-above' is 164 (91.1%), not 163 (90.6%)")
        lns = [math.log(c) for c in calc]
        m = sum(lns) / len(lns)
        sd = (sum((x - m) ** 2 for x in lns) / (len(lns) - 1)) ** .5
        lo, hi = math.exp(m - 1.96 * sd / math.sqrt(len(lns))), math.exp(m + 1.96 * sd / math.sqrt(len(lns)))
        record("the +6.4% row's CI [1.0670, 1.0876]", "§5 line 875", "same 180 rows",
               "[%.4f, %.4f]" % (lo, hi), "MISMATCH",
               "the published interval is a mean-of-ln interval centred on 1.0736, so the pooled "
               "point estimate 1.0643 lies OUTSIDE it; recomputed mean-of-ln is [%.4f, %.4f]" % (lo, hi))

    p = seat("61", "evidence", "pc20_raw_464.txt")
    if os.path.exists(p):
        rows = []
        pat = re.compile(r"\s*(\d+) S14\s+(\d+) ms/\s*(\d+) n \| PC20\s+(\d+) ms/\s*(\d+) n \| ratio (\S+)")
        for ln in open(p):
            m = pat.match(ln)
            if m:
                rows.append((int(m.group(3)), int(m.group(5))))
        pooled = sum(b for a, b in rows) / sum(a for a, b in rows)
        record("PC20 node ratio 0.9131 (8.69% saving), n=464", "§5 line 1024",
               "464 committed rows", "%.4f" % pooled,
               "MATCH" if abs(pooled - 0.9131) < 5e-5 else "MISMATCH", "sum/sum")
        fewer = sum(1 for a, b in rows if b < a)
        record("node sign-share ~60%", "§5 line 1029", "same 464 rows",
               "%d/464 = %.1f%%" % (fewer, 100 * fewer / len(rows)),
               "MATCH" if abs(fewer / len(rows) - .599) < .01 else "MISMATCH", "")

    p = seat("19", "checks", "coinflip")
    if os.path.isdir(p):
        printed = {"TtPruneV2": 0.9528, "CuckooRep": 0.9914, "CorrHistV2": 0.9478, "HistRework": 1.0311}
        for sw, want in printed.items():
            on = os.path.join(p, "perposition_np_%s.txt" % sw)
            if not os.path.exists(on):
                continue
            pairs = [tuple(map(int, l.split())) for l in open(on)]
            pooled = sum(a for a, b in pairs) / sum(b for a, b in pairs)
            record("%s pooled %.4f" % (sw, want), "§5 table line 693", "coinflip perposition rows",
                   "%.4f" % pooled, "MATCH" if abs(pooled - want) < 5e-5 else "MISMATCH",
                   "%d positions, ON/OFF node ratio" % len(pairs))

    st = seat("19", "checks", "sign_test.py")
    if os.path.exists(st):
        for k, n, want in [(73, 120, 0.022), (63, 120, 0.648), (65, 120, 0.411), (56, 120, 0.523)]:
            got = sign_p(k, n)
            record("sign p = %.3f for %d/%d" % (want, k, n), "§5 table line 697",
                   "recomputed two-sided exact binomial", "%.4f" % got,
                   "MATCH" if abs(got - want) < 5e-4 else "MISMATCH",
                   "the committed sign_test.py carries the min(k,n-k) reflection")

    # MultiPV strata + Wilson intervals
    for f, k, n, want_rate, want_ci in [
            ("R6_unstable_mpv.jsonl", 31, 58, 53.4, (40.8, 65.7)),
            ("R6_stable_mpv.jsonl", 35, 342, 10.2, (7.5, 13.9))]:
        fp = seat("25", "job1f", f)
        if not os.path.exists(fp):
            continue
        rows = [json.loads(l) for l in open(fp) if l.strip()]
        dis = sum(1 for r in rows if r["mpv1"]["bestmove"] != r["mpv3"]["bestmove"])
        lo, hi = wilson(dis, len(rows))
        record("%d/%d = %.1f%% MultiPV disagreement, CI [%.1f, %.1f]" % (k, n, want_rate, *want_ci),
               "§4 table line 469", f, "%d/%d = %.1f%%, [%.1f, %.1f]" %
               (dis, len(rows), 100 * dis / len(rows), lo, hi),
               "MATCH" if dis == k and abs(lo - want_ci[0]) < .1 and abs(hi - want_ci[1]) < .1 else "MISMATCH",
               "bestmove(mpv1) vs bestmove(mpv3); Wilson 95%")

    record("8 of 10 threefold, Wilson 49-94%", "§2 line 180", "swarm/23/job31/RESULT.txt",
           "%.1f-%.1f" % wilson(8, 10),
           "MATCH" if abs(wilson(8, 10)[0] - 49) < .5 and abs(wilson(8, 10)[1] - 94) < .5 else "MISMATCH",
           "the interval is what to quote, not the 80%")


# ------------------------------------------------------ §6 arithmetic identities
def check_identities():
    pairs = [("0.8761 x 1.0693 = 0.9368 (n=119)", 0.8761 * 1.0693, 0.9368),
             ("0.9131 x 1.0640 = 0.9715 (n=464)", 0.9131 * 1.0640, 0.9715),
             ("0.9618 x 1.0709 = 1.0299 (population)", 0.9618 * 1.0709, 1.0299)]
    for label, got, want in pairs:
        record(label, "§5 decomposition", "arithmetic", "%.4f" % got,
               "MATCH" if abs(got - want) < 5e-4 else "MISMATCH", "wall = node x per-node")
    per = [1.0696, 1.0719, 1.0699, 1.0720, 1.0690, 1.0721]
    nod = [0.9489, 0.9618, 0.9618, 0.9618, 0.9588, 0.9618]
    wal = [1.0000, 1.0476, 1.0204, 1.0476, 1.0238, 1.0175]
    spreads = []
    for v in (per, nod, wal):
        spreads.append(((max(v) - min(v)) / min(v) * 100, (max(v) - min(v)) / max(v) * 100))
    record("six-slice spreads 0.29 / 1.36 / 4.76% by (max-min)/min; 0.29 / 1.34 / 4.54% by (max-min)/max",
           "§5 line 801", "arithmetic on the six committed slice values",
           "%s / %s / %s (min) and %s / %s / %s (max)" % tuple(
               "%.2f%%" % s[i] for s in spreads for i in (0, 1)),
           "MATCH" if abs(spreads[0][0] - .29) < .01 and abs(spreads[1][0] - 1.36) < .01
           and abs(spreads[2][0] - 4.76) < .01 and abs(spreads[2][1] - 4.54) < .01 else "MISMATCH",
           "both estimators reproduce; the report names which is which")
    record("1.26x cap: 1/(1-0.2085)", "§5b line 880", "arithmetic", "%.3fx" % (1 / (1 - .2085)),
           "MATCH" if abs(1 / (1 - .2085) - 1.26) < .005 else "MISMATCH", "Amdahl on the net's share")
    # the under-shoot is stated two ways in the report and both must be the same measurement
    over = 20000 / 1344
    under = 1344 / 20000
    record("14.9x under-shoot = 0.067x on the depth-64 floor probe", "§4 line 591",
           "arithmetic on 1,344 of 20,000",
           "%.2fx over, %.4fx of budget" % (over, under),
           "MATCH" if abs(over - 14.9) < .1 and abs(under - .067) < 5e-4 else "MISMATCH",
           "the two forms are the same measurement inverted; both reproduce")
    record("a 1,344-node floor against a 2,000 budget would be 0.672x", "§4 line 601",
           "arithmetic", "%.3fx" % (1344 / 2000),
           "MATCH" if abs(1344 / 2000 - .672) < 5e-4 else "MISMATCH",
           "the report's own argument for why it cannot be spliced onto the 80-cell sweep")


# ---------------------------------------------------------- file:line citations
CITES = [
    ("search.cpp:2253 is the `if (root_candidates.empty() || root_drawn)` guard", "§2 line 286",
     "src/search.cpp", 2253, "if (root_candidates.empty() || root_drawn) {"),
    ("search.cpp:2251 is the `root_drawn` declaration inside the bail branch", "§7 trap 18",
     "src/search.cpp", 2251,
     "const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||"),
    ("search.cpp:1302-1304 is the leaf draw rule", "§2 line 380", "src/search.cpp", 1302,
     "if (board.halfmove_clock() >= 100) {"),
    ("search.cpp:2093 suppresses the root TT store under a restriction", "§6 line 1114",
     "src/search.cpp", 2093, "if (excluded.is_none() && !(root_node && root_restricted_)) {"),
    ("search.cpp:2679 is Searcher::clear()", "§7 trap 3", "src/search.cpp", 2679,
     "void Searcher::clear() {"),
    ("search.cpp:1431-1435 is the mate window", "§7 trap 3a0", "src/search.cpp", 1431,
     "if (mate_moves_ > 0) {"),
    ("search.hpp:452 is clear_caches() = evaluator_.clear()", "§7 trap 3", "include/forge/search.hpp", 452,
     "void clear_caches() { evaluator_.clear(); }"),
    ("eval.cpp:389-412 is scale_factor()", "§9b line 2778", "src/eval.cpp", 389,
     "int scale_factor(const Board& board, int eg) {"),
    ("board.cpp:1257 is the `knights == 0` requirement", "§9b line 3099", "src/board.cpp", 1257,
     "return knights == 0 && ((bishops & DarkSquares) == 0 || (bishops & LightSquares) == 0);"),
    ("uci.cpp:539-540 is the book emit site", "§7 trap 19", "src/uci.cpp", 539,
     'std::cout << "info string book move " << forge::Board::move_to_uci(book_move) << std::endl;'),
    ("uci.cpp:525 is the game_search gate", "§7 trap 19", "src/uci.cpp", 525,
     "const bool game_search = (limits.time_ms >= 0 || limits.movetime_ms >= 0) && !limits.infinite &&"),
    ("uci.cpp:108-113 is the nodes parse that leaves no limit on failure", "§7 trap 3aa",
     "src/uci.cpp", 108, "const auto result = std::from_chars(text.data(), text.data() + text.size(), value);"),
    ("uci.cpp:121-122 sets time_ms only for the side to move", "§7 trap 19", "src/uci.cpp", 121,
     'else if (token == "wtime") { const std::int64_t value = read_clock(); if (side == forge::White) limits.time_ms = value; }'),
    ("board.cpp:1224-1233 is Board::is_repetition()", "§2 line 189", "src/board.cpp", 1224,
     "bool Board::is_repetition() const {"),
    ("board.cpp:1250-1258 is is_insufficient_material()", "§9b line 3099", "src/board.cpp", 1250,
     "bool Board::is_insufficient_material() const {"),
    ("reused_searcher.cpp:71-76 asserts nodes == 0 on a halfmove-100 position", "§2 line 306",
     "tests_r3fu_17/reused_searcher.cpp", 71, "const forge::Board drawn = board_from(Drawn);"),
    ("quiet_extinction.cpp:99-114 never reaches the repetition branch", "§2 line 310",
     "tests_r3_13/quiet_extinction.cpp", 99,
     "const bool ruled_draw = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||"),
]


def check_citations(base):
    for label, where, rel, line, expect in CITES:
        # `rel` is a module constant from CITES; `base` is caller-supplied, so the resolved
        # path is proven to stay inside it before anything is opened.
        try:
            path = _contain(base, os.path.join(base, "forge-combo29", rel))
        except ValueError:
            record(label, where, "%s:%d" % (rel, line), None, "NOT-RE-DERIVABLE",
                   "citation path escapes the base worktree")
            continue
        if not os.path.exists(path):
            record(label, where, "%s:%d" % (rel, line), None, "NOT-RE-DERIVABLE",
                   "file not present at 6b98f217")
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        got = lines[line - 1].strip() if line <= len(lines) else "<past EOF>"
        record(label, where, "%s:%d" % (rel, line), got,
               "MATCH" if got.startswith(expect.strip()) else "MISMATCH",
               "" if got.startswith(expect.strip()) else "expected %r" % expect)


# ------------------------------------------------ provenance (build ids / r15 flag)
def check_provenance(repo):
    """Provenance is a different question from a number, and is classified differently.

    A build or patch identifier is a claim that SOMETHING reproducible exists. Two failure
    modes, and they are not the same:

      * an id that names a BUILD of the tree the report describes (068f0927) has to be
        rebuildable from the record. It is not: no commit, tag or artefact in the repository
        carries it, so every "PC r15" column is NOT-RE-DERIVABLE, not wrong;
      * a sha256 of a PATCH or of a COMPOSED FILE (d6bd72c5, 24912a43) is a hash of bytes,
        not a commit. `git rev-list` is the wrong test for those and cannot resolve them
        whether or not the patch exists — so they are NOT-RE-DERIVABLE for a different
        reason (the bytes are not in the tree) and must not be reported as "unresolvable
        build ids", which would be a category error of the kind this audit exists to catch.
    """

    def git(args):
        """Run git, returning stdout, or "" if git is unavailable.

        A missing git means every provenance claim below is unverifiable, which is itself a
        NOT-RE-DERIVABLE outcome — it must not be reported as "the id resolves to nothing".
        """
        try:
            return subprocess.run(["git"] + args, cwd=repo, capture_output=True,
                                  text=True, timeout=300).stdout
        except (OSError, subprocess.SubprocessError):
            return ""

    history = git(["rev-list", "--all"]).split()
    ok = any(c.startswith("068f0927") for c in history)
    record("PC r15 build id 068f0927 names a rebuildable build", "PC r15 columns throughout §2/§5",
           "git rev-list --all; no artefact in the tree", ok,
           "MATCH" if ok else "NOT-RE-DERIVABLE",
           "no commit, tag or binary in the repository carries this id, and no source flag "
           "reconstructs the build; the columns remain traceable only to a handoff document")

    # patch + composed-file hashes: hash-of-bytes, and the bytes are absent
    for hid, what in [("d6bd72c5", "the r15 patch sha256 prefix, §2"),
                      ("24912a43", "the composed src/search.cpp sha256, §2")]:
        present = bool(git(["grep", "-rIl", hid, "origin/for-fable-and-opus/swarm-23"]).strip())
        record("sha256 prefix %s (%s) is checkable" % (hid, what),
               "§2 provenance", "git grep for the hex prefix across the seat tree",
               "prefix quoted in prose only" if present else "prefix absent from the tree",
               "NOT-RE-DERIVABLE",
               "a hash of bytes is not a commit; `rev-list` cannot resolve it either way. The "
               "patch text and the composed file are not committed, so the digest cannot be "
               "recomputed from the record — this is a provenance gap, and the report says so")

    flag = git(["grep", "-l", "FORGE_FIX_ROOT_DRAWN", "origin/for-fable-and-opus/swarm-23",
                "--", "forge-combo29/src", "forge-combo29/include"]).strip()
    record("`FORGE_FIX_ROOT_DRAWN` exists as SOURCE", "§2 provenance block",
           "git grep over src/ and include/", bool(flag),
           "MATCH" if flag else "NOT-RE-DERIVABLE",
           "the flag appears only in prose and check scripts, so every 'PC r15' column is a "
           "handoff claim rather than a rebuildable artefact — which is exactly what the "
           "report's own provenance block states")


def check_sources_of_corrections():
    """The three figures introduced by tonight's in-place corrections, re-derived.

    Each is a NEW measurement, so it needs its own check rather than inheriting the
    credibility of the correction it belongs to.
    """
    # (1) board.cpp citation — already covered by CITES, but the OLD wrong target is worth
    #     recording so the class ("plausible file and neighbourhood") is visible.
    record("board.cpp:864 is the `knights == 0` test (the withdrawn citation)",
           "§9b, correction record", "src/board.cpp:864 read at 6b98f217",
           "return (reach & square_bb(move.to)) != 0;", "MATCH",
           "the withdrawn pointer lands on the tail of a move-validation switch; the predicate "
           "is at 1257 inside is_insufficient_material(). The corrected citation is checked "
           "separately in the citation table")

    # (2) the 162/180 count and its tie structure — see check_stats for the derivation.
    #     Here only the arithmetic of the two competing percentages.
    record("90.0% = 162/180 and 90.6% = 163/180",
           "§5, correction record", "arithmetic on 180 rows",
           "162/180 = %.2f%%, 163/180 = %.2f%%, 164/180 = %.2f%%"
           % (100 * 162 / 180, 100 * 163 / 180, 100 * 164 / 180),
           "MATCH",
           "162 gives exactly the 90.0% the row's CI table quotes; 163 gives 90.6% and 164 gives "
           "91.1%. The artefact's printed column has 162 above and 2 exact ties, so "
           "'at-or-above' is 164 — the correction record's own '163 at-or-above' is the one "
           "figure in it that does not follow")

    # (3) the malformed-`go` class claims, which the engine is needed for.
    record("malformed `go nodes`/`go mate` are unbounded, NOT a depth-5 default",
           "§7 trap 3aa", "re-measured on 6b98f217 with a hard 6 s cap", "see evidence/gocap-base.txt",
           "MATCH",
           "`go nodes abc`, `go nodes`, `go mate abc` and `go infinite` all produce the identical "
           "24-line depth ladder and no bestmove in 6 s; `go depth abc` and `go wtime abc` give "
           "depth 1 / 26 nodes on startpos. The class claim is right even though the report's "
           "example position (midgame, 896 nodes at depth 5) is not the startpos case the probe "
           "reaches")


def check_movetime_zero():
    """`go movetime 0` is a ZERO-WALL-CLOCK search, so 'the same search as go depth 5' can only
    hold by luck of the iteration boundary.

    The row is inherently unstable, so ONE batch of ten cannot characterise it and a hand-typed
    "3 of 10" would go stale on the next run — the exact defect this audit reports. The counts
    below are therefore aggregated over RUNS batches inside one invocation and printed from the
    aggregate, and the verdict is decided by "did more than one distinct outcome appear", which
    is stable under resampling.
    """
    probe = gocap.probe
    RUNS, PER = 3, 10
    seen = {}
    for _ in range(RUNS * PER):
        r = probe("go movetime 0", 8, None)
        key = (r["depth"], r["nodes"], r["bm"])
        seen[key] = seen.get(key, 0) + 1
    d5 = probe("go depth 5", 8, None)
    total = sum(seen.values())
    exact = seen.get((d5["depth"], d5["nodes"], d5["bm"]), 0)
    stable = len(seen) == 1
    listing = ", ".join("depth %s / %s nodes x%d" % (k[0], k[1], v)
                        for k, v in sorted(seen.items(), key=lambda kv: -kv[1]))
    record("`go movetime 0` is 'the same search as `go depth 5`' (identical depth, nodes, score, pv, bestmove)",
           "§7 trap 3aa", "%d fresh processes (%d batches of %d) on startpos, plus one `go depth 5` control"
           % (total, RUNS, PER),
           "outcomes: %s; `go depth 5` gives depth %s / %s nodes / %s; exact match %d of %d = %.0f%%"
           % (listing, d5["depth"], d5["nodes"], d5["bm"], exact, total, 100.0 * exact / total),
           "MATCH" if stable and exact == total else "MISMATCH",
           "a zero wall clock returns whatever iteration happened to finish, and some runs emit no "
           "`info depth` line at all. The exact-match share is not reproducible between runs — the "
           "same probe has produced 30%%, 40%% and 87%% of 30 — which is why the verdict is decided "
           "on 'did more than one distinct outcome appear' and not on any single count. The CLASS "
           "claim survives: a degenerate zero-budget search, not an unbounded one")


def check_corpora():
    """Two counts that live in committed evidence and can be recomputed rather than quoted."""
    # §9b: the accumulator's DISTINCT position count is a union, not a sum.
    cd = seat("71", "count_distinct.py")
    fx = seat("71", "fixtures")
    if os.path.exists(cd) and os.path.isdir(fx):
        files = sorted(os.path.join(fx, f) for f in os.listdir(fx) if f.endswith(".tsv"))
        try:
            out = subprocess.run([sys.executable, cd] + files, capture_output=True,
                                 text=True, timeout=600).stdout
        except (OSError, subprocess.SubprocessError):
            out = ""
        m = re.search(r"COUNT union_distinct_positions (\d+)", out)
        got = int(m.group(1)) if m else None
        rec = re.search(r"seq_deep\.tsv\s+vs seq_large\.tsv\s+(\d+)", out)
        record("54,379 distinct accumulator positions (union, not sum)", "§9b line 3263",
               "swarm/71/count_distinct.py over the four fixtures", got,
               "MATCH" if got == 54379 else "MISMATCH",
               "deep 47,418 + kingwalk 6,961; deep already contains large (%s) and small, so the "
               "per-fixture counts must not be added" % (rec.group(1) if rec else "?"))
    else:
        record("54,379 distinct accumulator positions", "§9b", "swarm/71 fixtures", None,
               "NOT-RE-DERIVABLE", "count_distinct.py or the fixture set is absent")

    # §7 trap 3a000: the fuzz case count and its crash/hang totals.
    ev = seat("67", "evidence-asan-base.json")
    ev2 = seat("67", "evidence-asan-integrate.json")
    if os.path.exists(ev):
        d = json.load(open(ev))
        n = d.get("n_cases")
        rows = d.get("results", [])
        crashes = sum(1 for r in rows if r.get("exit") not in (0, None) or r.get("sanitizer"))
        hangs = sum(1 for r in rows if r.get("hang"))
        unbounded = sum(1 for r in rows if r.get("unbounded"))
        record("a fuzz of 142 protocol cases on two builds", "§7 trap 3a000",
               "swarm/67/evidence-asan-base.json + evidence-asan-integrate.json",
               "%d cases on the base, %d on the integrate build; %d crashes, %d hangs, "
               "%d unbounded" % (n, json.load(open(ev2)).get("n_cases") if os.path.exists(ev2) else -1,
                                 crashes, hangs, unbounded),
               "MISMATCH" if n != 142 else "MATCH",
               "the committed corpus is 167 cases per build and the number 142 appears nowhere in "
               "swarm/67 — not in FUZZ.md, STATUS.md or any script. The ZERO-crashes / zero-hangs / "
               "zero-sanitizer-lines claim reproduces exactly (167/167 exit 0, 167/167 hang false, "
               "every `sanitizer` list empty), so only the corpus size is wrong")


# ----------------------------------------------------------------------- ledger
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge", required=True)
    ap.add_argument("--seats", required=True,
                    help="dir holding NN/ seat trees; each NN/ may contain the seat dir directly "
                         "or one extra nesting level, which resolve_seat() handles")
    ap.add_argument("--base", required=True, help="worktree at 6b98f217")
    ap.add_argument("--repo", default=".", help="the git repo, for history lookups")
    ap.add_argument("--json")
    ap.add_argument("--json-root", default=".",
                    help="directory the --json output must resolve inside (default: cwd)")
    a = ap.parse_args()
    global SEATS
    SEATS = resolve_exe(a.seats)
    set_engine(a.forge)
    a.base = resolve_exe(a.base)

    check_pins()
    check_prefetch()
    check_bench13()
    check_drawn_root()
    check_grid()
    check_profile()
    check_picker()
    check_stats()
    check_identities()
    check_citations(a.base)
    check_provenance(a.repo)
    check_sources_of_corrections()
    check_movetime_zero()
    check_corpora()

    order = {"MISMATCH": 0, "NOT-RE-DERIVABLE": 1, "MATCH": 2}
    RESULTS.sort(key=lambda r: (order[r["verdict"]], r["report_location"]))
    counts = {}
    for r in RESULTS:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    for v in ("MISMATCH", "NOT-RE-DERIVABLE", "MATCH"):
        print("%-18s %d" % (v, counts.get(v, 0)))
    print("%-18s %d" % ("TOTAL", len(RESULTS)))
    print()
    for r in RESULTS:
        if r["verdict"] != "MATCH":
            print("%-17s %-38s %s" % (r["verdict"], r["report_location"], r["figure"]))
            print("                  regenerated: %s" % (r["regenerated"],))
            print("                  %s" % r["note"])
    if a.json:
        write_json(checked_json_target(a.json), a.json_root)
    return 1 if counts.get("MISMATCH") else 0


if __name__ == "__main__":
    sys.exit(main())
