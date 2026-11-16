#!/usr/bin/env python3
"""reverify.py EXE OUTDIR

Re-runs, with the 19-F12-safe driver (read to `bestmove` before any further command, never
close stdin mid-search), the two results of mine whose harness piped `quit` after `go depth`:

  A  the GUI trace behind 21-F2 (refused FEN, then `go depth 1` / `go depth 4`)
  B  the halfmove>=100 0-node shortcut behind 21-F9 (`go depth 4` / `go depth 8`)

For each I also run the OLD pipelined form in a separate process, so the report shows
whether the old numbers were fabricated and what the true numbers are.
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

PIPE_CASES = {}


def piped(exe, outdir, name, lines):
    """The OLD, invalid form: everything in one pipe including quit."""
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=120, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("=== OLD PIPELINED FORM (invalid for search results, 19-F12)\n")
        fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n>>> quit\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
    return p.stdout


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = []

    # ---------- A: the 21-F2 GUI trace ----------
    history = "e2e4 e7e5 g1f3 b8c6 f1b5"
    bad = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKBR1 w KQkq - 0 3"
    e = SafeEngine(exe, os.path.join(outdir, "A_safe_raw.txt"))
    a1 = e.position("position startpos moves " + history)
    a1_go = e.go("go depth 1")
    a2 = e.position("position fen " + bad)
    a2_go = e.go("go depth 4")
    e.close()
    old = piped(exe, outdir, "A_old_pipeline",
                ["position startpos moves " + history, "isready", "go depth 1",
                 "position fen " + bad, "isready", "go depth 4"])
    rows.append(("A 21-F2 trace: go depth 1 then go depth 4", bestmove_of(a1_go),
                 last_info(a1_go)[:60], bestmove_of(a2_go), last_info(a2_go)[:60],
                 " | ".join(l for l in a2 if l.startswith("info string")),
                 [l for l in old.splitlines() if l.startswith("bestmove")]))

    # ---------- B: the 21-F9 halfmove shortcut ----------
    for hm, tag in ((100, "B_hm100"), (2147483648, "B_hm2147483648")):
        fen = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - %d 1" % hm
        e = SafeEngine(exe, os.path.join(outdir, tag + "_safe_raw.txt"))
        e.position("position fen " + fen)
        lines = e.go("go depth 8")
        e.close()
        oldout = piped(exe, outdir, tag + "_old_pipeline",
                       ["position fen " + fen, "isready", "go depth 8"])
        rows.append((tag + ": go depth 8", bestmove_of(lines), last_info(lines)[:110], "",
                     "", "", [l for l in oldout.splitlines() if l.startswith("bestmove")]))

    out = ["| case | SAFE bestmove | SAFE last info depth | SAFE 2nd bestmove | SAFE 2nd info | answer lines | OLD pipelined bestmoves |",
           "|---|---|---|---|---|---|---|"]
    for a, b, c, d, f, g, h in rows:
        out.append("| %s | %s | %s | %s | %s | %s | %s |" % (a, b, c, d, f, g, h))
    text = "\n".join(out)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()