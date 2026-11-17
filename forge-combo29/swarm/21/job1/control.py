#!/usr/bin/env python3
"""control.py EXE OUTDIR

Control cases required by area 1 job 1, plus a few from the brief's "known" list.
Each case runs in a FRESH engine process (so a crash is attributable) and keeps the
raw output. A case is judged by: did the process survive, what did it answer to
`position fen`, and what did `go depth 2` / `go perft 3` answer.
"""
import os
import subprocess
import sys

CASES = []


def case(name, lines):
    CASES.append((name, lines))


long_field = "1" * 3000
case("control_3000char_first_field",
     ["position fen %s/8/8/8/8/8/8/8 w - - 0 1" % long_field, "isready", "go depth 2"])
case("control_3000char_field_only",
     ["position fen %s" % long_field, "isready", "go depth 2"])
case("known_impossible_castling",
     ["position fen r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "isready",
      "position fen 4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1", "isready", "go perft 3"])
case("known_triple_check_knights",
     ["position fen 4k3/8/8/8/8/2n1n3/1n6/4K3 w - - 0 1", "isready", "go perft 1"])
case("control_startpos_sanity",
     ["position startpos", "isready", "go perft 3"])
case("control_empty_position",
     ["position fen", "isready", "go depth 2"])
case("control_no_fields",
     ["position fen    ", "isready", "go depth 2"])


def run_case(exe, name, lines, outdir):
    raw = os.path.join(outdir, name + ".txt")
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    proc = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                          capture_output=True, timeout=120, env=env)
    with open(raw, "w") as fh:
        fh.write("=== exe: %s\n" % os.path.abspath(exe))
        fh.write("=== lines sent:\n")
        for ln in lines:
            fh.write(">>> " + ln + "\n")
        fh.write("=== stdout:\n" + proc.stdout)
        fh.write("=== stderr:\n" + proc.stderr)
        fh.write("=== returncode: %d\n" % proc.returncode)
    san = any(m in proc.stderr or m in proc.stdout
              for m in ("AddressSanitizer", "runtime error", "__asan", "__ubsan"))
    return proc.returncode, san, proc.stdout


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    summary = []
    for name, lines in CASES:
        rc, san, stdout = run_case(exe, name, lines, outdir)
        answer = [ln for ln in stdout.splitlines() if ln.startswith("info string") or
                  ln.startswith("nodes") or ln.startswith("bestmove")]
        summary.append("%-32s rc=%d sanitizer=%s  %s" %
                       (name, rc, san, " ;; ".join(answer[:4])))
    with open(os.path.join(outdir, "summary.txt"), "w") as fh:
        fh.write("\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
