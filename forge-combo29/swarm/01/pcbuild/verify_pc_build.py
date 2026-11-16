#!/usr/bin/env python3
"""swarm seat 01: verify the PC r15 build's KNOWN answers from FABLE_TO_swarm_5.

The three regimes must not be mixed (file 4): the four pins are DEFAULT-option numbers (no setoption at all),
the S14 sums and the PC20 numbers are taken under their option sets, each setoption followed by isready read to
readyok, and `ucinewgame` + `isready` before every `go`.

Expected, from file 5's table and file 4:
  none  : bench 11 312866, bench 13 862329, bench 16 3024920, go perft 5 4865609
  S14   : bench 11 242796, bench 13 656517
  PC20  : bench 11 278024, bench 13 587276

Every check is a FRESH process (one process per line), because a warm hash changes node counts (seat 10).
Every option name is checked against the exe's own `uci` list first, and the run STOPS on `unknown option`,
`invalid value` or `ERROR`.

Usage: verify_pc_build.py <exe> <outdir>
"""
import hashlib
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 1200.0

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

EXPECT = {
    "none_bench11": 312866, "none_bench13": 862329, "none_bench16": 3024920, "none_perft5": 4865609,
    "s14_bench11": 242796, "s14_bench13": 656517,
    "pc20_bench11": 278024, "pc20_bench13": 587276,
}


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def uci_option_names(exe):
    p = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, timeout=120)
    names = set()
    for l in p.stdout.splitlines():
        if l.startswith("option name "):
            rest = l[len("option name "):]
            names.add(rest.split(" type ")[0].strip())
    return names


def run_bench(exe, options, command):
    """One fresh process. Returns (nodes_or_None, raw_lines, problems)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []
    problems = []

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    deadline = time.monotonic() + TIMEOUT
    send("uci")
    if until("uciok", deadline) is None:
        problems.append("no uciok")
    for name, value in options:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        if until("readyok", deadline) is None:
            problems.append("no readyok after setoption %s" % name)
            break
        for l in buf:
            if l.startswith("unknown option"):
                problems.append("unknown option %s" % name)
            if l.startswith("info string invalid value"):
                problems.append("invalid value for %s" % name)
            if l.startswith("ERROR"):
                problems.append("ERROR line: %s" % l)
    if options:
        send("ucinewgame")
        send("isready")
        if until("readyok", deadline) is None:
            problems.append("no readyok after ucinewgame")
    send(command)
    if command.startswith("go perft"):
        # the engine's perft total line starts with "nodes "
        if until("nodes ", deadline) is None:
            problems.append("no 'nodes ' line for perft")
    else:
        # the engine prints "info string bench depth N nodes M ..." - the line starts with
        # "info string bench", NOT "bench". Waiting for "bench " waits forever (seat 19's failure mode).
        if until("info string bench", deadline) is None:
            problems.append("no 'info string bench' line")
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    nodes = None
    for l in buf:
        m = re.search(r"\bnodes (\d+)", l)
        if m:
            nodes = int(m.group(1))
    return nodes, buf, problems


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    have = uci_option_names(exe)
    lines = ["PC r15 build verification against FABLE_TO_swarm_5's table",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "options the exe lists: %d" % len(have)]
    needed = [n for n, _ in S14 + PC20_EXTRA]
    missing = [n for n in needed if n not in have]
    lines.append("options needed by S14/PC20 but NOT in the exe's uci list: %s" % (missing or "(none)"))
    lines.append("")

    checks = [
        ("none_bench11", [], "bench 11"),
        ("none_bench13", [], "bench 13"),
        ("none_bench16", [], "bench 16"),
        ("none_perft5", [], "position startpos\ngo perft 5"),
        ("s14_bench11", S14, "bench 11"),
        ("s14_bench13", S14, "bench 13"),
        ("pc20_bench11", S14 + PC20_EXTRA, "bench 11"),
        ("pc20_bench13", S14 + PC20_EXTRA, "bench 13"),
    ]
    lines.append("check\tsettings\tcommand\tgot\texpected\tverdict\tproblems")
    results = {}
    for name, opts, cmd in checks:
        if "\n" in cmd:
            nodes, buf, problems = run_bench_multi(exe, opts, cmd)
        else:
            nodes, buf, problems = run_bench(exe, opts, cmd)
        exp = EXPECT[name]
        got = nodes
        ok = (got == exp) and not problems
        verdict = "PASS" if ok else ("FAIL(expected %d)" % exp if got != exp else "FAIL(problems)")
        results[name] = {"got": got, "expected": exp, "problems": problems, "verdict": verdict}
        lines.append("%s\t%s\t%s\t%s\t%d\t%s\t%s" % (
            name, "none" if not opts else ("S14" if opts is S14 else "PC20"), cmd.replace("\n", "; "),
            got, exp, verdict, "; ".join(problems) or "(none)"))
        (out / (name + ".raw.txt")).write_text("\n".join(buf) + "\n")
        print("%-14s got=%-9s expected=%-9d %s %s" % (name, got, exp, verdict,
                                                      "; ".join(problems) or ""), flush=True)
    allpass = all(v["verdict"] == "PASS" for v in results.values())
    lines.append("")
    lines.append("ALL PASS" if allpass else "MISMATCH — see the rows above")
    (out / "verify_pc_build.txt").write_text("\n".join(lines) + "\n")
    print("")
    print("\n".join(lines[-2:]))


def run_bench_multi(exe, options, command):
    """For commands with more than one line (position + go perft)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []
    problems = []

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    deadline = time.monotonic() + TIMEOUT
    send("uci")
    until("uciok", deadline)
    lines_cmd = command.split("\n")
    for line in lines_cmd:
        send(line)
    send("isready")
    until("readyok", deadline)
    for l in buf:
        if l.startswith("unknown option") or l.startswith("ERROR") or "invalid value" in l:
            problems.append(l)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    nodes = None
    for l in buf:
        m = re.search(r"\bnodes (\d+)", l)
        if m:
            nodes = int(m.group(1))
    return nodes, buf, problems


if __name__ == "__main__":
    main()
