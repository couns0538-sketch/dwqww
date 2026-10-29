#!/usr/bin/env python3
"""R5D proof loops: the fixed tree vs the base tree on the KRK mate in 3 and on forge_tt_mate_tb_tests.

Run it on a 3-CPU affinity mask (job rule: at most 3 threads; Threads 4 then means 4 search threads on 3 CPUs):
  python run_pinned.py --mask 0x700 -- r5d_proof.py --out DIR --repro-fix EXE --repro-base EXE --tt-fix EXE
         --tt-base EXE --prefill FILE --reference TSV [--krk-runs 10000] [--base-runs 2000] [--tt-runs 200]
         [--sweep-runs 500] [--warm-reps 3] [--only STEP[,STEP]]
Steps (each one or more child processes at BelowNormal, in this order):
  krk    fresh Searcher per run, go depth 14, Threads 2 and 4 x SmpV2 off/on: --krk-runs (fix) / --base-runs (base)
  best   the same with UCI SmpBestThread (SmpV2 off): fix --base-runs, base --base-runs / 2
  sweep  fix only: go depth 10..18, Threads 2 and 4 x SmpV2 off/on, --sweep-runs each
  warm   an unrelated depth-9 search first (each FEN of --prefill, --warm-reps times), then KRK at depth 14 on the same
         Searcher: Threads 1 (both trees, deterministic), Threads 2 and 4 x SmpV2 off/on (fix; base Threads 2 only)
  tt     forge_tt_mate_tb_tests (its Threads block via FORGE_TT_MATE_THREADS / FORGE_TT_MATE_SMPV2): Threads 2 and 4 x
         SmpV2 off/on, --tt-runs per configuration and tree; a run fails when the test exits non-zero
A run of r5d_mate_repro fails when the score is not a mate for the side to move or is shorter than the true mate.
Output: DIR/proof.tsv (one row per configuration: step tree threads smpv2 depth runs failures exact seconds) and
DIR/logs/*.log (every child's output). A file DIR/proof.halt stops the driver before its next child process.
"""
import argparse
import os
import re
import subprocess
import sys
import time

BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
SUMMARY = re.compile(r"runs (\d+) .*: failures (\d+) \([^)]*\), exact (\d+), ([0-9.]+) s")


class Halted(Exception):
    pass


class Proof:
    def __init__(self, args):
        self.args = args
        os.makedirs(os.path.join(args.out, "logs"), exist_ok=True)
        self.tsv = open(os.path.join(args.out, "proof.tsv"), "a", newline="\n")
        if self.tsv.tell() == 0:
            self.tsv.write("step\ttree\tthreads\tsmpv2\tdepth\truns\tfailures\texact\tseconds\textra\n")

    def halt_check(self):
        if os.path.exists(os.path.join(self.args.out, "proof.halt")):
            raise Halted()

    def child(self, cmd, log_name, env=None):
        self.halt_check()
        t0 = time.monotonic()
        p = subprocess.run(cmd, capture_output=True, text=True, creationflags=BELOW_NORMAL, env=env)
        with open(os.path.join(self.args.out, "logs", log_name), "a", newline="\n") as f:
            f.write("$ " + " ".join(cmd) + "\n" + p.stdout + p.stderr)
        return p, time.monotonic() - t0

    def row(self, step, tree, threads, smpv2, depth, runs, failures, exact, seconds, extra=""):
        line = f"{step}\t{tree}\t{threads}\t{smpv2}\t{depth}\t{runs}\t{failures}\t{exact}\t{seconds:.1f}\t{extra}"
        self.tsv.write(line + "\n")
        self.tsv.flush()
        print(line, flush=True)

    def repro(self, step, tree, exe, runs, threads, smpv2, depth=14, extra_args=(), extra=""):
        cmd = [exe, str(runs), str(threads), str(smpv2), str(depth), "--show", "3", *extra_args]
        p, seconds = self.child(cmd, f"{step}_{tree}.log")
        m = None
        for line in p.stdout.splitlines():
            m = SUMMARY.search(line) or m
        if m is None or int(m.group(1)) != runs:
            raise SystemExit(f"r5d_proof: no summary line from {' '.join(cmd)}:\n{p.stdout[-500:]}{p.stderr[-500:]}")
        self.row(step, tree, threads, smpv2, depth, runs, int(m.group(2)), int(m.group(3)), seconds, extra)

    def warm(self, tree, exe, threads, smpv2, fens, reps):
        failures = exact = runs = 0
        t0 = time.monotonic()
        for _ in range(reps):
            for fen in fens:
                p, _ = self.child([exe, "1", str(threads), str(smpv2), "14", "--prefill-fen", fen, "--prefill-depth",
                                   "9", "--show", "1"], f"warm_{tree}.log")
                m = SUMMARY.search(p.stdout)
                if m is None:
                    raise SystemExit(f"r5d_proof: no summary line (warm, {tree}, {fen}):\n{p.stdout[-500:]}")
                runs += 1
                failures += int(m.group(2))
                exact += int(m.group(3))
        self.row("warm", tree, threads, smpv2, 14, runs, failures, exact, time.monotonic() - t0,
                 f"{len(fens)} FENs x {reps}")

    def tt(self, tree, exe, threads, smpv2, runs):
        failed = longer = 0
        t0 = time.monotonic()
        env = dict(os.environ, FORGE_TT_MATE_THREADS=str(threads), FORGE_TT_MATE_SMPV2=str(smpv2))
        env.pop("FORGE_SYZYGY_PATH", None)  # the mate part only (the tablebase part has no Threads block)
        for _ in range(runs):
            p, _ = self.child([exe, self.args.reference], f"tt_{tree}_t{threads}_v{smpv2}.log", env)
            if p.returncode != 0 or "PASS forge_tt_mate_tb_tests" not in p.stdout:
                failed += 1
            longer += p.stdout.count("reported a longer mate")
        self.row("tt", tree, threads, smpv2, 14, runs, failed, -1, time.monotonic() - t0,
                 f"INFO longer-mate lines {longer}")


def main():
    ap = argparse.ArgumentParser()
    for name in ("--out", "--repro-fix", "--repro-base", "--tt-fix", "--tt-base", "--prefill", "--reference"):
        ap.add_argument(name, required=True)
    ap.add_argument("--krk-runs", type=int, default=10000)
    ap.add_argument("--base-runs", type=int, default=2000)
    ap.add_argument("--tt-runs", type=int, default=200)
    ap.add_argument("--sweep-runs", type=int, default=500)
    ap.add_argument("--warm-reps", type=int, default=3)
    ap.add_argument("--only", default="krk,best,sweep,warm,tt")
    args = ap.parse_args()
    steps = args.only.split(",")
    fens = [l.strip() for l in open(args.prefill, encoding="utf-8") if l.strip()]
    pr = Proof(args)
    trees = (("fix", args.repro_fix, args.krk_runs), ("base", args.repro_base, args.base_runs))
    try:
        if "krk" in steps:
            for tree, exe, runs in trees:
                for threads in (2, 4):
                    for smpv2 in (0, 1):
                        pr.repro("krk", tree, exe, runs, threads, smpv2)
        if "best" in steps:
            for tree, exe, runs in (("fix", args.repro_fix, args.base_runs), ("base", args.repro_base, args.base_runs // 2)):
                for threads in (2, 4):
                    pr.repro("best", tree, exe, runs, threads, 0, extra_args=("--best-thread",), extra="SmpBestThread")
        if "sweep" in steps:
            for depth in range(10, 19):
                for threads in (2, 4):
                    for smpv2 in (0, 1):
                        pr.repro("sweep", "fix", args.repro_fix, args.sweep_runs, threads, smpv2, depth)
        if "warm" in steps:
            for tree, exe, _ in trees:
                pr.warm(tree, exe, 1, 0, fens, 1)
            for threads in (2, 4):
                for smpv2 in (0, 1):
                    pr.warm("fix", args.repro_fix, threads, smpv2, fens, args.warm_reps)
            pr.warm("base", args.repro_base, 2, 0, fens, args.warm_reps)
        if "tt" in steps:
            for tree, exe in (("fix", args.tt_fix), ("base", args.tt_base)):
                for threads in (2, 4):
                    for smpv2 in (0, 1):
                        pr.tt(tree, exe, threads, smpv2, args.tt_runs)
    except Halted:
        print("r5d_proof: halted by proof.halt", flush=True)
        sys.exit(2)
    print("r5d_proof: done", flush=True)


main()
