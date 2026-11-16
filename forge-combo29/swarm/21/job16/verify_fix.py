#!/usr/bin/env python3
"""verify_fix.py EXE OUTDIR

FINAL, CORRECTED verification of seat 12's `two_doors_mate.patch.txt`. This supersedes the
first version in this folder (which piped `quit` and, separately, built its repetition cases
with a `position fen ... moves` line that Forge did read — but whose results I then mis-read).

Rules applied (all three came from notices in this session):
  * 19-F12: every search goes through safe_engine — stdout read to `bestmove` before the next
    command, stdin never closed mid-search.
  * seat 10: a cold baseline is a FRESH PROCESS or `ucinewgame`, never `Clear Hash`, and two
    searches in one process are never compared by node count. Every case here is ONE fresh
    process and one search.
  * seat 19 integrity: the FEN acceptance is asserted, and the `nodes`/`bestmove` line must be
    present or the case raises.

Cases (mate existence verified with python-chess, board copied per candidate move):
  fifty-move door:  hm 100 vs hm 99, White and Black
  repetition door:  the same position THREE times vs TWICE, White and Black
  quiet control:    a drawn root with NO mate available must stay adjudicated (0 nodes)
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

W_HM = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - {hm} 60"
B_HM = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - {hm} 60"
W_REP_START = "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60"
W_CYCLE = ["e1d1", "g8h8", "d1e1", "h8g8"]
B_REP_START = "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 60"
B_CYCLE = ["a8b8", "g1h1", "b8a8", "h1g1"]
QUIET = "4k3/8/8/8/8/8/4P3/4K2R w - - {hm} 60"


def mates_in_one(fen):
    b = chess.Board(fen)
    out = []
    for m in list(b.legal_moves):
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def rep_position(start, cycle, reps):
    b = chess.Board(start)
    seq = []
    for _ in range(reps):
        for mv in cycle:
            b.push_uci(mv)
            seq.append(mv)
    return b, seq


def one(exe, outdir, tag, pos, mates):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"))
    ans = e.position(pos)
    if any("invalid FEN" in l for l in ans):
        e.close()
        raise AssertionError("%s: FEN refused" % tag)
    try:
        lines = e.go("go depth 5", timeout=180)
    finally:
        e.close()
    bm = bestmove_of(lines)
    info = last_info(lines)
    if not bm:
        raise AssertionError("%s: no bestmove read" % tag)
    nd = re.search(r" nodes (\d+)", info)
    nodes = nd.group(1) if nd else "?"
    return dict(bm=bm, nodes=nodes, info=info, found=(bm in mates) if mates else None)


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = ["| case | python mate in 1 | bestmove | nodes | mate found | last info |",
            "|---|---|---|---|---|---|"]
    R = {}

    def add(tag, pos, mates):
        R[tag] = one(exe, outdir, tag, pos, mates)
        rows.append("| %s | %s | %s | %s | %s | %s |" % (
            tag, ", ".join(mates) or "none", R[tag]["bm"], R[tag]["nodes"],
            ("YES" if R[tag]["found"] else "no") if mates else "n/a",
            R[tag]["info"][-52:].replace("|", "/")))

    add("W_hm100", "position fen " + W_HM.format(hm=100), mates_in_one(W_HM.format(hm=100)))
    add("W_hm99", "position fen " + W_HM.format(hm=99), mates_in_one(W_HM.format(hm=99)))
    add("B_hm100", "position fen " + B_HM.format(hm=100), mates_in_one(B_HM.format(hm=100)))
    add("B_hm99", "position fen " + B_HM.format(hm=99), mates_in_one(B_HM.format(hm=99)))

    for tag, start, cycle in (("W", W_REP_START, W_CYCLE), ("B", B_REP_START, B_CYCLE)):
        for reps, label in ((2, "rep3"), (1, "rep2")):
            b, seq = rep_position(start, cycle, reps)
            pos = "position fen %s moves %s" % (start, " ".join(seq))
            add("%s_%s" % (tag, label), pos, mates_in_one(b.fen()))
            with open(os.path.join(outdir, "%s_%s_python.txt" % (tag, label)), "w") as fh:
                fh.write("fen: %s\nthreefold: %s\nmates: %s\n"
                         % (b.fen(), b.is_repetition(3), mates_in_one(b.fen())))

    add("QUIET_hm100", "position fen " + QUIET.format(hm=100), [])
    add("QUIET_hm99", "position fen " + QUIET.format(hm=99), [])

    verdicts = []
    doors = R["W_hm100"]["found"] and R["W_rep3"]["found"] and R["B_hm100"]["found"] and R["B_rep3"]["found"]
    controls = R["W_hm99"]["found"] and R["B_hm99"]["found"] and R["W_rep2"]["found"] and R["B_rep2"]["found"]
    quiet = R["QUIET_hm100"]["nodes"] == "0" and R["QUIET_hm99"]["nodes"] != "0"
    verdicts.append("both doors closed in BOTH colours: %s" % doors)
    verdicts.append("controls (counter 99, two occurrences) find the mate: %s" % controls)
    verdicts.append("quiet drawn root still adjudicated at 0 nodes, searched at 99: %s" % quiet)
    ok = doors and controls and quiet
    text = "\n".join(rows) + "\n\n" + "\n".join(verdicts) + "\n\n=> " + (
        "FIX VERIFIED" if ok else "FIX NOT VERIFIED")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()