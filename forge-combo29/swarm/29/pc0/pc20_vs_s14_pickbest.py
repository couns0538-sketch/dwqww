#!/usr/bin/env python3
"""Do my move-ordering findings (29-F10: pick_best vs next is position-dependent) hold on the PC r15 build, and does
the PC20 option set change them? Profiles the SAME position set under S14 and under PC20 at depth 12, Threads 1.

Shares are task-clock samples (+-1 point per symbol); the question is ORDERING, not third decimals. A symbol that is
not sampled prints NOT FOUND and no ordering claim is made on it.
"""
import re, subprocess, sys, os

EXE, FENS, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
OUT = sys.argv[4]
os.makedirs(OUT, exist_ok=True)
PERF = "/usr/lib/linux-tools/6.8.0-149-generic/perf"

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
WANT = ["pick_best", "MovePicker::next(bool)", "probe_body", "see_ge"]
fens = [l.strip() for l in open(FENS) if l.strip()][:N]


def profile(label, settings):
    drv = os.path.join(OUT, f"drv_{label}.py")
    with open(drv, "w") as f:
        f.write("import subprocess\n")
        f.write(f"p=subprocess.Popen([{EXE!r}],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)\n")
        f.write("def send(c):\n    p.stdin.write(c+'\\n'); p.stdin.flush()\n")
        f.write("send('uci')\n")
        f.write("for line in p.stdout:\n    if line.startswith('uciok'): break\n")
        for k, v in settings:
            f.write(f"send({('setoption name %s value %s' % (k, v))!r})\n")
        f.write("send('isready')\n")
        f.write("for line in p.stdout:\n    if line.startswith('readyok'): break\n")
        f.write(f"for fen in {fens!r}:\n")
        f.write("    send('position fen '+fen)\n    send('go depth 12')\n")
        f.write("    for line in p.stdout:\n        if line.startswith('bestmove'): break\n")
        f.write("send('quit')\np.wait()\n")
    data = os.path.join(OUT, f"{label}.data")
    subprocess.run([PERF, "record", "-q", "-e", "task-clock", "-o", data, sys.executable, drv],
                   check=False, capture_output=True)
    rep = subprocess.run([PERF, "report", "-i", data, "--stdio", "--no-children", "--percent-limit", "0.2"],
                         capture_output=True, text=True).stdout
    got = {}
    for line in rep.splitlines():
        m = re.match(r'^\s+([0-9]+\.[0-9]+)%\s+\S+\s+\S+\s+\[\S\]\s+(.*)$', line)
        if not m:
            continue
        pct, sym = float(m.group(1)), m.group(2).strip()
        for w in WANT:
            if w in sym and (w not in got or pct > got[w]):
                got[w] = pct
    return got


res = {lbl: profile(lbl, st) for lbl, st in (("S14", S14), ("PC20", PC20))}
print(f"PC r15 build, {len(fens)} positions, depth 12, Threads 1")
print(f"{'symbol':22s} {'S14':>10} {'PC20':>10}")
for w in WANT:
    a = f"{res['S14'][w]:.2f}%" if w in res["S14"] else "NOT FOUND"
    b = f"{res['PC20'][w]:.2f}%" if w in res["PC20"] else "NOT FOUND"
    print(f"{w:22s} {a:>10} {b:>10}")
for lbl in ("S14", "PC20"):
    pb, nx = res[lbl].get("pick_best"), res[lbl].get("MovePicker::next(bool)")
    if pb is None or nx is None:
        print(f"{lbl}: INCONCLUSIVE (pick_best={pb} next={nx})")
    else:
        print(f"{lbl}: pick_best {'>' if pb > nx else '<'} next  ({pb:.2f} vs {nx:.2f})")
