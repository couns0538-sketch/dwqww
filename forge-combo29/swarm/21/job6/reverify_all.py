#!/usr/bin/env python3
"""reverify_all.py EXE OUTDIR

Re-runs, under the 19-F12-safe driver, EVERY search-based measurement of mine that came
from a harness which piped `quit`:

  1. fullmove 0 (21-F8)          — was `go perft 1`, synchronous, but re-done to be sure
  2. illegal-prefix plies (21-C2) — was `go perft 1/2`, synchronous
  3. the sticky-board probe (21-F2) — see f2_safe.py for the controlled version
  4. the 20,000-FEN job's `go depth 2` — see job6/fen_rerun.py

For each: SAFE = read to bestmove, never close stdin mid-search. OLD = the pipelined form,
kept beside it so the report shows which numbers were fabricated.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess


def piped(exe, lines, timeout=180):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    return subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                          capture_output=True, timeout=timeout, env=env).stdout


def perft2(bd):
    t = 0
    for m in bd.legal_moves:
        bd.push(m)
        t += bd.legal_moves.count()
        bd.pop()
    return t


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []

    # 1. fullmove 0
    fen0 = "4k3/8/8/8/8/8/8/4K2R w K - 0 0"
    fen1 = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"
    e = SafeEngine(exe, os.path.join(outdir, "fullmove0_safe_raw.txt"))
    ans0 = e.position("position fen " + fen0)
    n0 = [l for l in e.go("go perft 1", token="nodes") if l.startswith("nodes ")]
    ans1 = e.position("position fen " + fen1)
    n1 = [l for l in e.go("go perft 1", token="nodes") if l.startswith("nodes ")]
    e.close()
    rows.append(("fullmove 0 refused / control", " ;; ".join(l for l in ans0 if 'info string' in l),
                 n0[0] if n0 else "-", " ;; ".join(l for l in ans1 if 'info string' in l) or "none",
                 n1[0] if n1 else "-", str(chess.Board(fen1).legal_moves.count())))

    # 2. illegal prefix in a long list
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job4"))
    import long_moves as lm
    plies, boards = lm.build_game(1000)
    for k in (1, 10, 500):
        pos = boards[k - 1]
        tok = lm.illegal_token(pos)
        seq = plies[:k - 1] + [tok] + plies[k - 1:]
        e = SafeEngine(exe, os.path.join(outdir, "prefix_%d_safe_raw.txt" % k))
        a = e.position("position startpos moves " + " ".join(seq))
        got1 = [l for l in e.go("go perft 1", token="nodes") if l.startswith("nodes ")]
        got2 = [l for l in e.go("go perft 2", token="nodes") if l.startswith("nodes ")]
        e.close()
        rows.append(("illegal at ply %d (%s)" % (k, tok),
                     " ;; ".join(l for l in a if 'info string' in l),
                     "%s / %s" % (got1[0].split()[1] if got1 else "-",
                                  got2[0].split()[1] if got2 else "-"),
                     "python-chess prefix", "%d / %d" % (boards[k-1].legal_moves.count(),
                                                         perft2(boards[k-1].copy())), ""))

    hdr = "| case | answer line | SAFE perft nodes | control | expected | python |"
    out = [hdr, "|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    text = "\n".join(out)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()