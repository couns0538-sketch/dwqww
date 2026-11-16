#!/usr/bin/env python3
"""quit_abort.py EXE OUTDIR : characterise what a piped `quit` (or EOF) right after `go` does to a search.

FOUND WHILE DOING JOB 1b: my own profiling harness wrote `position ... / isready / go depth N` followed
immediately by the next position, and every search reported `bestmove a2a3` with NO `info` line. That is
this build's "first legal move of the position", i.e. the engine played a move it never searched.

The test separates four ways of ending the input, each in a fresh process, each on startpos with `go depth 12`:

  A  quit written IMMEDIATELY after go, all at once (a typical pipelined harness)
  B  quit written 2 s after go (stdin kept open in between)
  C  stdin CLOSED (EOF) immediately after go, no quit at all
  D  no terminator at all: wait for `bestmove` with stdin still open, then quit

For each: how many `info depth` lines arrived, what the bestmove was, and whether the reported node count
is above zero. `bench 13` is included as the control that the same engine can search when not interrupted.
"""
import os
import subprocess
import sys
import time

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
os.environ.pop("ASAN_OPTIONS", None)
os.environ.pop("UBSAN_OPTIONS", None)
os.environ.pop("TSAN_OPTIONS", None)

POS = "position startpos"
GO = "go depth 12"


def summarize(out):
    depth = [l for l in out.splitlines() if l.startswith("info depth")]
    best = [l for l in out.splitlines() if l.startswith("bestmove")]
    nodes = [int(l.split("nodes ")[1].split()[0]) for l in out.splitlines() if " nodes " in l]
    return len(depth), (best[-1] if best else "(no bestmove)"), (max(nodes) if nodes else 0)


def run_case(name, tail, wait_before=0.0, close_stdin=False):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    head = "uci\nisready\n" + POS + "\nisready\n" + GO + "\n"
    proc.stdin.write(head)
    proc.stdin.flush()
    if wait_before:
        time.sleep(wait_before)
    out = ""
    try:
        if close_stdin:
            proc.stdin.close()
            out = proc.stdout.read()
            proc.wait(timeout=120)
        else:
            proc.stdin.write(tail)
            proc.stdin.flush()
            out, _ = proc.communicate(timeout=120)
    except Exception as exc:  # noqa: BLE001
        out += "\nEXCEPTION %r" % (exc,)
        proc.kill()
    n_depth, best, nodes = summarize(out)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("exe: %s\ninput head:\n%s\ntail: %r  wait_before=%.1fs  close_stdin=%s\n\n"
                 % (os.path.abspath(exe), head, tail, wait_before, close_stdin))
        fh.write(out)
    return name, n_depth, best, nodes


results = [
    run_case("A_quit_immediately", "quit\n"),
    run_case("B_quit_after_2s", "quit\n", wait_before=2.0),
    run_case("C_eof_immediately", "", close_stdin=True),
    run_case("D_no_terminator", "quit\n", wait_before=0.0),
]

# control: bench 13 on the same exe
proc = subprocess.run([exe], input="bench 13\nquit\n", capture_output=True, text=True, timeout=600)
bench_line = [l for l in proc.stdout.splitlines() if l.startswith("info string bench depth 13")]
with open(os.path.join(outdir, "E_bench_control.txt"), "w") as fh:
    fh.write("bench 13 with quit piped AFTER it (bench is synchronous, so this still works):\n")
    fh.write("\n".join(bench_line) + "\n")

lines = ["exe: %s" % os.path.abspath(exe), "", "| case | info depth lines | bestmove | max nodes |",
         "|---|---|---|---|"]
for name, n_depth, best, nodes in results:
    lines.append("| %s | %d | `%s` | %d |" % (name, n_depth, best, nodes))
lines.append("")
lines.append("bench control: %s" % (bench_line[-1] if bench_line else "(no bench line)"))
lines.append("")
aborted = [r for r in results if r[1] == 0]
lines.append("cases that produced NO search at all: %s" % ", ".join(r[0] for r in aborted) or "none")
lines.append("cases that searched: %s" % ", ".join(r[0] for r in results if r[1] > 0))
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
