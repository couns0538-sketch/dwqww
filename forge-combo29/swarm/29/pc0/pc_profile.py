#!/usr/bin/env python3
"""Profile the PC r15 build under PC20 over a position set at depth 12, Threads 1.

This is my area-9 job re-done on the build the owner actually plays, which is what TEXT 2 asks for. Shares are
task-clock samples (the only event this unprivileged user can open), so each symbol carries about +-1 point; the
point of the run is the ORDERING and the big movers, not third-decimal precision.

Every parsed share is asserted to exist: a symbol that is not sampled is reported NOT FOUND, never as 0.
"""
import re, subprocess, sys, os

EXE = sys.argv[1]
FENS = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 200
OUT = sys.argv[4] if len(sys.argv) > 4 else "/tmp/pcprof"
os.makedirs(OUT, exist_ok=True)
PERF = "/usr/lib/linux-tools/6.8.0-149-generic/perf"

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

WANT = ["pick_best", "MovePicker::next(bool)", "probe_body", "see_ge", "fill_pseudo_legal",
        "Worker::search", "qsearch", "evaluate_position", "apply_and_evaluate", "corrected_eval"]

fens = [l.strip() for l in open(FENS) if l.strip()][:N]

script = os.path.join(OUT, "driver.py")
with open(script, "w") as f:
    f.write("import subprocess\n")
    f.write(f"p=subprocess.Popen([{EXE!r}],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)\n")
    f.write(f"cmds={['uci']!r}\n")
    f.write("def send(c):\n    p.stdin.write(c+'\\n'); p.stdin.flush()\n")
    f.write("send('uci')\n")
    f.write("for line in p.stdout:\n    if line.startswith('uciok'): break\n")
    for k, v in PC20:
        f.write(f"send({('setoption name %s value %s' % (k, v))!r})\n")
    f.write("send('isready')\n")
    f.write("for line in p.stdout:\n    if line.startswith('readyok'): break\n")
    f.write(f"for fen in {fens!r}:\n")
    f.write("    send('position fen '+fen)\n")
    f.write("    send('go depth 12')\n")
    f.write("    for line in p.stdout:\n")
    f.write("        if line.startswith('bestmove'): break\n")
    f.write("send('quit')\np.wait()\n")

data = os.path.join(OUT, "pc20.data")
subprocess.run([PERF, "record", "-q", "-e", "task-clock", "-o", data, sys.executable, script],
               check=False, capture_output=True)
rep = subprocess.run([PERF, "report", "-i", data, "--stdio", "--no-children", "--percent-limit", "0.2"],
                     capture_output=True, text=True).stdout
print(f"positions {len(fens)}, depth 12, PC20, Threads 1")
print()
got = {}
for line in rep.splitlines():
    m = re.match(r'^\s+([0-9]+\.[0-9]+)%\s+\S+\s+\S+\s+\[\S\]\s+(.*)$', line)
    if not m:
        continue
    pct, sym = float(m.group(1)), m.group(2).strip()
    for w in WANT:
        if w in sym and (w not in got or pct > got[w]):
            got[w] = pct
for w in WANT:
    print(f"{w:22s} {('%.2f%%' % got[w]) if w in got else 'NOT FOUND':>10}")
if len(got) < 4:
    raise SystemExit("ABORT: too few symbols sampled; refusing to draw a conclusion")
