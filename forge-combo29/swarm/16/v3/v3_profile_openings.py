#!/usr/bin/env python3
"""v3_profile_openings.py EXE NET PERFBIN OUTDIR FENS [COUNT] : file 7 Step 1, the SECOND arm.

Profiles the 200 openings at `go depth 12` under PC20 + the test net, Threads 1, Hash 16, with `ucinewgame` +
`isready` before each search. Writes the UCI script to a file FIRST, records the per-position node counts (these
are also Step 2's identity rows), then profiles with perf and reports the symbol shares.
"""
import os
import re
import subprocess
import sys
import time

EXE, NET, PERFBIN, OUTDIR, FENS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
COUNT = int(sys.argv[6]) if len(sys.argv) > 6 else 200
os.makedirs(OUTDIR, exist_ok=True)
DEPTH = 12

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

fens = [l.strip() for l in open(FENS) if l.strip()][:COUNT]

# ---- the UCI script, written to a file FIRST ----
script_path = os.path.join(OUTDIR, "openings.uci")
with open(script_path, "w") as fh:
    fh.write("uci\nisready\n")
    for n, v in [("Threads", 1), ("Hash", 16)] + PC20:
        fh.write(f"setoption name {n} value {v}\nisready\n")
    fh.write(f"setoption name NNUEArchFile value {NET}\nisready\n")
    fh.write("setoption name NNUEArch value true\nisready\n")
    for fen in fens:
        fh.write("ucinewgame\nisready\n")
        fh.write(f"position fen {fen}\nisready\n")
        fh.write(f"go depth {DEPTH}\nisready\n")
    fh.write("quit\n")

meta_path = os.path.join(OUTDIR, "openings.meta")
with open(meta_path, "w") as fh:
    fh.write(f"exe started: {EXE}\n")
    fh.write(subprocess.run(["sha256sum", EXE], capture_output=True, text=True).stdout)
    fh.write(subprocess.run([EXE, "-"], input="uci\nquit\n", capture_output=True, text=True).stdout
             .split("id name")[1].split("\n")[0].join(["id name", ""]) + "\n"
             if False else "")
    uci = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True).stdout
    for l in uci.splitlines():
        if l.startswith("id name"):
            fh.write(l + "\n")
    fh.write("--- option lines sent (in order):\n")
    for n, v in [("Threads", 1), ("Hash", 16)] + PC20 + [("NNUEArchFile", NET), ("NNUEArch", "true")]:
        fh.write(f"setoption name {n} value {v}\n")
    fh.write(f"--- positions {len(fens)}, depth {DEPTH}\n")

# ---- the node rows (identity data, also needed by Step 2) ----
# DISCIPLINE: one long-lived process, but every search is driven to `bestmove` before the next command is
# written, and `quit` only at the very end. A fully pipelined script (all searches queued, then quit) makes this
# engine answer a FABRICATED `bestmove a2a3` with zero info lines -- seat 19's trap, which I hit on the first
# attempt and which produced 0 usable rows.
t0 = time.monotonic()
p_proc = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, bufsize=1)


def snd(c):
    p_proc.stdin.write(c + "\n")
    p_proc.stdin.flush()


def rto(tok, lim=300):
    got = []
    dl = time.monotonic() + lim
    while time.monotonic() < dl:
        l = p_proc.stdout.readline()
        if not l:
            return got, False
        l = l.rstrip("\n")
        got.append(l)
        if l.strip().startswith(tok):
            return got, True
    return got, False


snd("uci"); rto("uciok", 30)
for n, v in [("Threads", 1), ("Hash", 16)] + PC20:
    snd(f"setoption name {n} value {v}"); snd("isready"); rto("readyok", 30)
snd(f"setoption name NNUEArchFile value {NET}"); snd("isready"); rto("readyok", 30)
snd("setoption name NNUEArch value true"); snd("isready"); rto("readyok", 30)
rows = []
for fen in fens:
    snd("ucinewgame"); snd("isready"); rto("readyok", 30)
    snd("position fen " + fen); snd("isready"); rto("readyok", 30)
    snd(f"go depth {DEPTH}")
    lines, ok = rto("bestmove", 600)
    if not ok:
        print(f"  STOP: no bestmove for {fen}")
        break
    n_nodes = None
    for l in lines:
        m = re.match(rf"^info depth {DEPTH} .*nodes (\d+)", l)
        if m:
            n_nodes = int(m.group(1))
    if n_nodes is None:
        print(f"  STOP: no depth-{DEPTH} info for {fen} (fabricated bestmove?)")
        break
    rows.append(n_nodes)
snd("quit")
try:
    p_proc.wait(timeout=20)
except Exception:
    p_proc.kill()
wall = time.monotonic() - t0
with open(os.path.join(OUTDIR, "node_rows.txt"), "w") as fh:
    fh.write(f"# depth {DEPTH}, PC20 + test net, Threads 1, Hash 16, {len(fens)} positions\n")
    fh.write("# index\tnodes\n")
    for i, n in enumerate(rows):
        fh.write(f"{i}\t{n}\n")
    fh.write(f"# sum\t{sum(rows)}\n")
print(f"node rows {len(rows)} of {len(fens)}, sum {sum(rows)}, wall {wall:.0f}s")

# ---- the profile ----
perfdata = os.path.join(OUTDIR, "perf_openings.data")
# Under perf the SAME driven discipline is needed, so perf launches a small driver that paces the searches.
driver = os.path.join(OUTDIR, "drive.py")
with open(driver, "w") as fh:
    fh.write(f"""import subprocess, sys, time, re
exe = {EXE!r}
fens = {fens!r}
depth = {DEPTH}
opts = {([("Threads", 1), ("Hash", 16)] + PC20)!r}
net = {NET!r}
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)
def snd(c):
    p.stdin.write(c + chr(10)); p.stdin.flush()
def rto(tok, lim=600):
    dl = time.monotonic() + lim
    while time.monotonic() < dl:
        l = p.stdout.readline()
        if not l:
            return False
        if l.strip().startswith(tok):
            return True
    return False
snd("uci"); rto("uciok")
for n, v in opts:
    snd(f"setoption name {{n}} value {{v}}"); snd("isready"); rto("readyok")
snd(f"setoption name NNUEArchFile value {{net}}"); snd("isready"); rto("readyok")
snd("setoption name NNUEArch value true"); snd("isready"); rto("readyok")
for f in fens:
    snd("ucinewgame"); snd("isready"); rto("readyok")
    snd("position fen " + f); snd("isready"); rto("readyok")
    snd(f"go depth {{depth}}")
    rto("bestmove")
snd("quit")
""")
subprocess.run([PERFBIN, "record", "-q", "-F", "199", "-g", "-o", perfdata, "--",
                sys.executable, driver], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
rep = subprocess.run([PERFBIN, "report", "-i", perfdata, "--stdio", "--no-children", "-g", "none"],
                     capture_output=True, text=True).stdout
with open(os.path.join(OUTDIR, "perf_openings.txt"), "w") as fh:
    fh.write(rep)

total = 0.0
nnue = 0.0
picker = 0.0
v3hot = []
for l in rep.splitlines():
    m = re.match(r"\s+([\d.]+)%\s+\S+\s+\S+\s+\[\w*\]\s+(.*)$", l)
    if not m:
        continue
    p, sym = float(m.group(1)), m.group(2)
    total += p
    if "nnue::" in sym:
        nnue += p
        v3hot.append((p, sym.split("(")[0]))
    if re.search(r"MovePicker|generate_evasions|fill_pseudo_legal|is_legal_complete|see_ge|pick_best", sym):
        picker += p
print(f"accounted {total:.1f}%   nnue:: {nnue:.2f}%   picker+gen {picker:.2f}%")
print("top v3:")
for p, s in sorted(v3hot, reverse=True)[:5]:
    print(f"  {p:6.2f}%  {s}")
with open(os.path.join(OUTDIR, "summary.txt"), "w") as fh:
    fh.write(f"# openings arm, depth {DEPTH}\n")
    fh.write(f"accounted_pct\t{total:.2f}\n")
    fh.write(f"nnue_pct\t{nnue:.2f}\n")
    fh.write(f"picker_gen_pct\t{picker:.2f}\n")
    for p, s in sorted(v3hot, reverse=True):
        fh.write(f"v3\t{p:.2f}\t{s}\n")
