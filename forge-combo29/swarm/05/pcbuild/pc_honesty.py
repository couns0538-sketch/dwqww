#!/usr/bin/env python3
"""pc_honesty.py EXE OUTDIR -- checks the PC r15 build against the numbers FABLE_TO_swarm_5.md states.

Three regimes, each with FRESH PROCESSES and its OWN option list (file 4's warning: pins are default-option
numbers, sums are S14/PC20 numbers — never mix them):
  regime "none"  : no setoption at all
  regime "S14"   : the 14 settings of file 1
  regime "PC20"  : S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
                   MateAlphaGuard true, OwnBook false
Recorded expectations (file 5):
  none : bench11 312866, bench13 862329, bench16 3024920, perft5 4865609
  S14  : bench11 242796, bench13 656517
  PC20 : bench11 278024, bench13 587276
"""
import hashlib
import os
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
OUT = sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
    "setoption name Threads value 1", "setoption name Hash value 16",
]
PC20 = S14 + [
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false",
]
REGIMES = {"none": [], "S14": S14, "PC20": PC20}

EXPECT = {
    ("none", "bench 11"): 312866, ("none", "bench 13"): 862329,
    ("none", "bench 16"): 3024920, ("none", "go perft 5"): 4865609,
    ("S14", "bench 11"): 242796, ("S14", "bench 13"): 656517,
    ("PC20", "bench 11"): 278024, ("PC20", "bench 13"): 587276,
}
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move", "ERROR")


def run(regime, cmd):
    opts = REGIMES[regime]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok, limit=300):
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                lines.append("### EOF")
                return
            line = line.rstrip("\n")
            lines.append(line)
            if line.startswith(tok):
                return
        lines.append("### TIMEOUT")

    send("uci")
    until("uciok")
    for o in opts:
        send(o)
        send("isready")
        r_start = len(lines)
        until("readyok")
        bad = [l for l in lines[r_start:] if any(b in l for b in BAD)]
        if bad:
            send("quit")
            p.kill()
            return None, bad[0]
    send(cmd)
    send("isready")
    until("readyok")
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines, None


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


with open(f"{OUT}/meta.txt", "w") as m:
    m.write(f"exe: {os.path.abspath(EXE)}\nsha256: {sha(EXE)}\n")
    m.write(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    m.write("regime none: no setoption\nregime S14: the 14 file-1 settings + Threads 1 + Hash 16\n")
    m.write("regime PC20: S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, "
            "MateAlphaGuard true, OwnBook false\n")
    p = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True)
    for l in p.stdout.splitlines():
        if l.startswith("id name"):
            m.write(f"id_name: {l}\n")
    have = set()
    for l in p.stdout.splitlines():
        mm = re.match(r"option name (.+?) type", l)
        if mm:
            have.add(mm.group(1))
    for name in ("CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard", "OwnBook",
                 "LmrQuietBase", "NonPawnCorrection"):
        m.write(f"option_present {name}: {name in have}\n")

print("| regime | command | expected | got | verdict |")
print("|---|---|---|---|---|")
allok = True
for regime in ("none", "S14", "PC20"):
    for cmd in ("bench 11", "bench 13", "bench 16", "go perft 5"):
        if (regime, cmd) not in EXPECT:
            continue
        lines, bad = run(regime, cmd)
        path = f"{OUT}/{regime.replace(' ', '_')}__{cmd.replace(' ', '_')}.raw.txt"
        with open(path, "w") as f:
            f.write("\n".join(lines or []) + "\n")
        if bad:
            print(f"| {regime} | `{cmd}` | {EXPECT[(regime, cmd)]} | HARNESS_STOP | **REFUSED: {bad}** |")
            allok = False
            continue
        got = None
        for l in lines:
            mm = re.search(r"nodes (\d+)", l)
            if mm:
                got = int(mm.group(1))
        want = EXPECT[(regime, cmd)]
        ok = (got == want)
        allok = allok and ok
        print(f"| {regime} | `{cmd}` | {want} | {got} | {'OK' if ok else '**MISMATCH**'} |")
print()
print("PC r15 HONESTY", "PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
