#!/usr/bin/env python3
"""extreme.py EXE OUTDIR

Area 1 job 2: extreme numbers in the FEN fields.
Each case is ONE field of the base board changed, run in a FRESH process:
  `position fen <FEN>` + `isready` (all answer lines kept), `go depth 4`, `go perft 2`.
Raw output per case; a summary table is written by this script from the raw files.

Case list and the expectation for each are in prediction.txt (committed before this ran).
"""
import json
import os
import subprocess
import sys

import chess

BASE = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"

CASES = [
    ("hm_0", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
    ("hm_99", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 99 1"),
    ("hm_100", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 100 1"),
    ("hm_150", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 150 1"),
    ("hm_9999", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 9999 1"),
    ("hm_neg1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - -1 1"),
    ("hm_2147483648", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 2147483648 1"),
    ("fm_0", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 0"),
    ("fm_1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
    ("fm_1e9", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1000000000"),
    ("fm_neg1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 -1"),
    ("ep_wrong_rank_e3", "r3k2r/pppppppp/8/8/8/4P3/PPPP1PPP/R3K2R w KQkq e3 0 1"),
    ("ep_wrong_rank_e6", "r3k2r/pppppppp/4P3/8/8/8/PPPP1PPP/R3K2R w KQkq e6 0 1"),
    ("ep_legal_d6", "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"),
    ("ep_bad_file_z3", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq z3 0 1"),
    ("ep_bad_square", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq e9 0 1"),
    ("two_white_kings", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K1KR w KQkq - 0 1"),
    ("two_black_kings", "r3k1kr/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
    ("three_kings", "r3k1kr/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"),
    ("no_kings", "r7/pppppppp/8/8/8/8/PPPPPPPP/R7 w KQkq - 0 1"),
    ("white_pawn_rank1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/P3K2R w kq - 0 1"),
    ("white_pawn_rank8", "P3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w kq - 0 1"),
    ("black_pawn_rank1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2p w KQkq - 0 1"),
    ("black_pawn_rank8", "r3k2r/pppppppp/8/8/8/8/PPPPPPPp/R3K2R w KQkq - 0 1"),
    ("nine_in_rank", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1".replace(
        "r3k2r", "r9")),
]


def run(exe, outdir, name, fen, extra=(), timeout=180):
    lines = ["position fen " + fen, "isready", "go depth 4"]
    lines += list(extra)
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=timeout, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("=== exe: %s\n" % os.path.abspath(exe))
        fh.write("=== fen: %s\n" % fen)
        fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
        fh.write("=== returncode: %d\n" % p.returncode)
    return p


SAN = ("__asan_", "__ubsan_", "AddressSanitizer", "Sanitizer", "runtime error",
       "SUMMARY: UndefinedBehavior", "SEGV")


def perft_py(fen, depth):
    b = chess.Board(fen)

    def rec(bd, d):
        if d == 0:
            return 1
        t = 0
        for m in bd.legal_moves:
            bd.push(m)
            t += rec(bd, d - 1)
            bd.pop()
        return t
    return rec(b, depth)


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    results = []
    for name, fen in CASES:
        p = run(exe, outdir, name, fen, extra=["isready", "go perft 2"])
        out = p.stdout
        refused = "invalid FEN" in out
        answer = [ln for ln in out.splitlines() if ln.startswith("info string")]
        sani = any(m in out or m in p.stderr for m in SAN)
        score = [ln for ln in out.splitlines() if ln.startswith("info depth 4")]
        score_line = score[-1] if score else ""
        bm = [ln for ln in out.splitlines() if ln.startswith("bestmove")]
        best = bm[0].split()[1] if bm else ""
        nodes = [ln.split()[1] for ln in out.splitlines() if ln.startswith("nodes ")]
        perft_engine = nodes[0] if nodes else "-"
        try:
            py_ok = True
            chess.Board(fen)
        except Exception:
            py_ok = False
        py_perft = "-"
        if py_ok:
            try:
                py_perft = perft_py(fen, 2)
            except Exception as exc:
                py_perft = "ERR:%s" % type(exc).__name__
        results.append(dict(name=name, fen=fen, refused=refused,
                            answer=answer[0] if answer else "",
                            san=sani, rc=p.returncode, best=best,
                            engine_perft=perft_engine,
                            py_accepts=py_ok, py_perft=py_perft,
                            score=score_line))
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    rows = ["| case | refused | answer line | rc | san | depth-4 last info | bestmove | perft2 engine | py accepts | perft2 python |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        rows.append("| %s | %s | %s | %d | %s | %s | %s | %s | %s | %s |" % (
            r["name"], r["refused"], r["answer"].replace("|", "/")[:70], r["rc"], r["san"],
            r["score"][-60:].replace("|", "/"), r["best"], r["engine_perft"],
            r["py_accepts"], r["py_perft"]))
    mism = [r["name"] for r in results
            if r["py_accepts"] and r["engine_perft"] != "-" and str(r["py_perft"]) != r["engine_perft"]]
    rows.append("")
    rows.append("perft 2 mismatches where python-chess accepts: %s" % (mism or "none"))
    rows.append("sanitizer lines: %s" % ("YES" if any(r["san"] for r in results) else "none"))
    text = "\n".join(rows)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
