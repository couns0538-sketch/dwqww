#!/usr/bin/env python3
"""sticky.py EXE OUTDIR

Does a REFUSED `position fen` leave the previous position in place?
For each case one fresh process, raw output kept. Sequence per case:
  position startpos / isready / go perft 3            (baseline, expect 8902)
  position fen <bad> / isready                        (the refused command)
  go perft 3                                          (still the OLD position?)
  position fen <good different position> / isready     (a new command does take effect)
  go perft 3
Additionally the consequence test: startpos -> refused FEN -> `go depth 1` (which bestmove?).
"""
import os
import subprocess
import sys

BAD = [
    ("missing_rook_for_castling", "4k3/8/8/8/8/8/8/R3K3 w Kk - 0 1"),
    ("rights_with_no_rooks", "4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1"),
    ("three_fields", "8/8/8/8/8/8/8/8"),
    ("garbage", "this is not a fen at all"),
]
GOOD = "4k3/8/8/8/8/8/8/4KB1R w K - 0 1"


def run(exe, outdir, name, lines):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    proc = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                          capture_output=True, timeout=180, env=env)
    path = os.path.join(outdir, name + ".txt")
    with open(path, "w") as fh:
        fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("=== stdout:\n" + proc.stdout + "\n=== stderr:\n" + proc.stderr)
        fh.write("=== returncode: %d\n" % proc.returncode)
    nodes = [ln.split()[1] for ln in proc.stdout.splitlines() if ln.startswith("nodes ")]
    infos = [ln for ln in proc.stdout.splitlines()
             if ln.startswith("info string") or ln.startswith("bestmove")]
    return nodes, infos


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    out = []
    for name, bad in BAD:
        lines = ["position startpos", "isready", "go perft 3",
                 "position fen " + bad, "isready", "go perft 3",
                 "position fen " + GOOD, "isready", "go perft 3",
                 "position startpos", "isready", "position fen " + bad, "isready", "go depth 1"]
        nodes, infos = run(exe, outdir, name, lines)
        out.append((name, bad, nodes, infos))
    with open(os.path.join(outdir, "summary.txt"), "w") as fh:
        for name, bad, nodes, infos in out:
            fh.write("CASE %s  bad FEN: %s\n" % (name, bad))
            fh.write("  perft3 after startpos        = %s (expect 8902)\n" % (nodes[0] if nodes else "-"))
            fh.write("  perft3 after the REFUSED fen = %s (8902 => old position kept)\n"
                     % (nodes[1] if len(nodes) > 1 else "-"))
            fh.write("  perft3 after a GOOD fen      = %s (must differ from 8902)\n"
                     % (nodes[2] if len(nodes) > 2 else "-"))
            fh.write("  answer lines: %s\n\n" % " ;; ".join(infos[:4]))
    print(open(os.path.join(outdir, "summary.txt")).read())


if __name__ == "__main__":
    main()
