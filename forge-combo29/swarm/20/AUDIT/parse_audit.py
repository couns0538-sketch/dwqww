#!/usr/bin/env python3
"""parse_audit.py — seat 20: can any of my checks print a verdict when NOTHING was parsed?

Seat 19 reports a check that searched for a `clock_plan` line the engine never prints: the parser got no number,
the comparison went NaN, and the check printed CONFIRMS while measuring nothing. This script looks for that defect
class in MY checkers:

  (1) every script of mine that greps/parses engine output, and
  (2) for each, whether its verdict path can be reached with an EMPTY or MISSING parse.

The mechanical test: for each checker I feed a FAKE engine that prints a VALID uci handshake but NO result line
(no `info depth`, no `info string eval`, no `bestmove`), and record what the checker prints. A checker that reports
a confirmation on such an engine is DEFECTIVE.

usage: parse_audit.py <outdir>
"""
import os
import stat
import subprocess
import sys
import tempfile

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)

FAKE = r'''#!/usr/bin/env python3
"""a fake engine: correct uci handshake, then NOTHING. Every search and eval is silent, then it exits at EOF."""
import sys
for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name FAKE silent engine", flush=True)
        print("option name Hash type spin default 32 min 1 max 2048", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("option name LmpBase type spin default 4 min 0 max 20", flush=True)
        print("option name Threads type spin default 1 min 1 max 256", flush=True)
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd.startswith("go perft"):
        print("nodes 0", flush=True)
    elif cmd == "eval":
        pass           # NO eval line at all
    elif cmd.startswith("go"):
        pass           # NO bestmove, NO info: a search that answers nothing
'''

# the checkers of mine that PARSE engine output into a verdict
CHECKERS = [
    ("job9/check_s06f1b.py", "python3 {f} {exe} {out}"),
    ("job11/check_s05f3.py", "python3 {f} {exe} {out}"),
    ("job12/check_mate_pv_s14.py", "python3 {f} {exe} {out}"),
    ("job13/bisect_s14.py", "python3 {f} {exe} {out}"),
    ("job10/check_s28f1.py", "python3 {f} {exe} {out}"),
    ("job14/lmpbase_ladder.py", "python3 {f} {exe} {out}"),
]

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # forge-combo29/swarm/20

with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
    fh.write(FAKE)
    fake = fh.name
os.chmod(fake, 0o755)

print("== the fake engine, first: it must answer uciok and then nothing")
r = subprocess.run([fake], input="uci\nisready\nposition startpos\ngo depth 6\nquit\n",
                   capture_output=True, text=True, timeout=60)
print("   its stdout:", repr(r.stdout[:200]))
print()

lines = []
for rel, cmd in CHECKERS:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        lines.append(f"{rel:32s} MISSING")
        continue
    outdir = os.path.join(OUT, "fake_" + rel.replace("/", "_"))
    os.makedirs(outdir, exist_ok=True)
    c = cmd.format(f=path, exe=fake, out=outdir)
    try:
        rr = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=150)
        out = (rr.stdout + rr.stderr)
    except subprocess.TimeoutExpired:
        out = "<TIMEOUT>"
    # what verdict words appear?
    bad = [w for w in ("CONFIRMS", "CONSISTENT", "ok (searched)", "EQUAL") if w in out]
    crash = ("Traceback" in out) or out == "<TIMEOUT>"
    verdict = "REFUSED/CRASHED (good)" if crash else ("*** PRINTED A POSITIVE VERDICT ON A SILENT ENGINE ***"
                                                      if bad else "no positive verdict (good)")
    lines.append(f"{rel:32s} crash={str(crash):5s} positive_words={bad}  -> {verdict}")
    open(os.path.join(outdir, "checker_stdout.txt"), "w").write(out[:4000])

print("== each checker fed a silent fake engine (correct handshake, no results):")
for l in lines:
    print("  " + l)
print()
open(os.path.join(OUT, "parse_audit.txt"), "w").write("\n".join(lines) + "\n")
print("wrote", os.path.join(OUT, "parse_audit.txt"))
