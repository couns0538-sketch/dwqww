#!/usr/bin/env python3
"""P4: run the sanitizer build and demand EMPTY stderr.

Two runs, both with the option on:
  * `bench 13`
  * 200 of the P2 positions (`ucinewgame`, `position fen`, `go depth 9`)

stderr is captured to its own file for each run.  A clean result means the file
is empty and the process exited 0; anything else is printed and the script exits
nonzero.  The sanitizer build is compiled with -fno-sanitize-recover=all, so any
UBSan finding also aborts rather than printing and continuing -- that is what
makes "empty stderr" a real test (see logs/p4-planted.txt for proof that this
build's flags do catch a planted fault).

Usage: python3 p4_sanitizer.py <sanitizer_exe> <book>
"""
import subprocess
import sys
from pathlib import Path


def run_bench(exe, divisor, stderr_path):
    inp = f"uci\nsetoption name CorrMargin value 20\nsetoption name MinorCorrection value 50\nisready\nbench 13\nquit\n"
    with open(stderr_path, "w") as err:
        proc = subprocess.run([exe], input=inp, text=True, stdout=subprocess.PIPE,
                              stderr=err, timeout=3000)
    return proc.returncode, proc.stdout


def run_positions(exe, book, count, depth, divisor, stderr_path):
    fens = []
    with open(book) as fh:
        for line in fh:
            parts = line.split()
            if len(parts) >= 6 and parts[1] in ("w", "b"):
                fens.append(" ".join(parts[:6]))
            if len(fens) >= count:
                break
    script = [f"uci\nsetoption name CorrMargin value 20\nsetoption name MinorCorrection value 50\nisready\n"]
    for fen in fens:
        script.append(f"ucinewgame\nisready\nposition fen {fen}\ngo depth {depth}\n")
    script.append("quit\n")
    with open(stderr_path, "w") as err:
        proc = subprocess.run([exe], input="".join(script), text=True,
                              stdout=subprocess.PIPE, stderr=err, timeout=3000)
    return proc.returncode, proc.stdout


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    exe, book = sys.argv[1], sys.argv[2]
    logs = Path(__file__).resolve().parent / "logs"
    logs.mkdir(exist_ok=True)
    bad = 0

    for divisor in (1,):
        rc, out = run_bench(exe, divisor, logs / f"p4-stderr-bench13-K{divisor}.txt")
        err_txt = (logs / f"p4-stderr-bench13-K{divisor}.txt").read_text()
        nodes = [l for l in out.splitlines() if "bench depth" in l]
        print(f"bench 13, K={divisor}: exit={rc} stderr_bytes={len(err_txt)} "
              f"{nodes[-1].strip() if nodes else 'NO BENCH LINE'}")
        if rc != 0 or err_txt:
            bad += 1
            print("  STDERR:", err_txt[:2000])

    for divisor in (1,):
        rc, out = run_positions(exe, book, 200, 9, divisor,
                                logs / f"p4-stderr-200pos-K{divisor}.txt")
        err_txt = (logs / f"p4-stderr-200pos-K{divisor}.txt").read_text()
        n_best = out.count("bestmove")
        print(f"200 positions, K={divisor}: exit={rc} stderr_bytes={len(err_txt)} bestmoves={n_best}")
        if rc != 0 or err_txt or n_best != 200:
            bad += 1
            print("  STDERR:", err_txt[:2000])

    print("P4 RESULT:", "PASS (all stderr empty, all exits 0)" if bad == 0 else f"FAIL ({bad} bad runs)")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
