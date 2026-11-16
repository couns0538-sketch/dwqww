#!/usr/bin/env python3
"""isready_during.py EXE OUTDIR : does `isready` sent WHILE a search runs abort that search?

This matters for every seat: the brief's own instruction is "after every setoption and every position send
isready and read EVERY line up to readyok". If sending isready mid-search aborts the search, then a harness
that interleaves isready with `go` is measuring nothing. (The brief puts isready BEFORE go, which is safe;
the question is what happens if one lands AFTER go.)

Cases, fresh process each, startpos, `go depth 12`:
  A  go, then isready 50 ms later, then quit 3 s later        (isready DURING the search)
  B  go, then nothing for 3 s, then quit                       (control: the search completes)
  C  go, then a second `position startpos` 50 ms later         (a position command during the search)
  D  go, then another `go depth 12` 50 ms later                (a second go during the search)
"""
import os
import subprocess
import sys
import time

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for var in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(var, None)


def summarize(out):
    depth = [l for l in out.splitlines() if l.startswith("info depth")]
    best = [l for l in out.splitlines() if l.startswith("bestmove")]
    nodes = [int(l.split("nodes ")[1].split()[0]) for l in out.splitlines() if " nodes " in l]
    return len(depth), (best[-1] if best else "(no bestmove)"), (max(nodes) if nodes else 0)


def run(name, mid, mid_delay=0.05, final_delay=3.0):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    proc.stdin.write("uci\nisready\nposition startpos\nisready\ngo depth 12\n")
    proc.stdin.flush()
    if mid:
        time.sleep(mid_delay)
        proc.stdin.write(mid + "\n")
        proc.stdin.flush()
    time.sleep(final_delay)
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    out, _ = proc.communicate(timeout=120)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("mid-command: %r after %.2fs, quit after %.1fs\n\n" % (mid, mid_delay, final_delay))
        fh.write(out)
    return name, summarize(out)


res = [
    run("A_isready_during_search", "isready"),
    run("B_control_nothing_during", ""),
    run("C_position_during_search", "position startpos"),
    run("D_go_during_search", "go depth 12"),
]

lines = ["| case | mid-command | info depth lines | bestmove | max nodes |", "|---|---|---|---|---|"]
for (name, (n_depth, best, nodes)), mid in zip(res, ["isready", "(none)", "position startpos", "go depth 12"]):
    lines.append("| %s | `%s` | %d | `%s` | %d |" % (name, mid, n_depth, best, nodes))
lines.append("")
ok = [r for r in res if r[1][0] > 0]
lines.append("cases where the search completed: %s" % ", ".join(r[0] for r in ok))
lines.append("cases where the search produced nothing: %s"
             % ", ".join(r[0] for r in res if r[1][0] == 0))
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
