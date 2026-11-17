#!/usr/bin/env python3
"""v3_step0.py EXE NETPATH OUTDIR : file 7 Step 0, the gate.

Checks the EIGHT bench numbers and the THREE eval lines that file 7 publishes for the PC's tree with the v3 path
compiled in and the deterministic test net loaded. One miss = STOP THE JOB and report the raw output.

Load order is file 7's: NNUEArchFile FIRST, then NNUEArch true; the engine answers an
`info string NNUE v3 active: ...` / `loaded: ...` line. A refusal (`unknown option`, `invalid value`, `ERROR`) or a
missing active line stops the run rather than producing a number.

Rows, in file 7's order:
  no net, no setoption      bench 11 312866   bench 13 862329
  PC20, no net              bench 11 278024   bench 13 587276
  test net only             bench 11 965454   bench 13 4191906
  PC20, then the test net   bench 11 625258   bench 13 3652372
Eval lines under PC20 + test net (each must read `info string eval hce 0 nnue X total X`):
  startpos                                                        968
  r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3  1176
  8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40                          31
"""
import os
import re
import subprocess
import sys
import time

EXE, NET, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUTDIR, exist_ok=True)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASE_OPTS = [("Threads", 1), ("Hash", 16)]

BENCH = [
    ("no_net", "bench 11", 312866, None),
    ("no_net", "bench 13", 862329, None),
    ("pc20_no_net", "bench 11", 278024, "pc20"),
    ("pc20_no_net", "bench 13", 587276, "pc20"),
    ("net_only", "bench 11", 965454, "net"),
    ("net_only", "bench 13", 4191906, "net"),
    ("pc20_net", "bench 11", 625258, "pc20net"),
    ("pc20_net", "bench 13", 3652372, "pc20net"),
]
EVALS = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 968),
    ("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3", 1176),
    ("8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40", 31),
]

fails = []
out = []


class Refused(Exception):
    pass


def run(regime, command, fen=None):
    """One fresh process. regime in {None,'pc20','net','pc20net'}. Returns all stdout lines."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=300):
        got = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return got, False
            l = l.rstrip("\n")
            got.append(l)
            if l.strip().startswith(tok):
                return got, True
        return got, False

    send("uci")
    uci, ok = to("uciok", 30)
    if not ok:
        raise Refused("no uciok")
    known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
    if "NNUEArch" not in known:
        raise Refused("NNUEArch missing from the uci list -> the build lacks -DFORGE_NNUE_V3=1")
    send("isready"); to("readyok", 30)

    opts = list(BASE_OPTS)
    if regime in ("pc20", "pc20net"):
        opts += PC20
    if regime in ("net", "pc20net"):
        # file 7's load order: file FIRST, then the switch
        opts += [("NNUEArchFile", NET), ("NNUEArch", "true")]
    n3lines = []
    for n, v in opts:
        if n not in known:
            raise Refused(f"option {n} absent")
        send(f"setoption name {n} value {v}")
        send("isready")
        got, ok = to("readyok", 30)
        n3lines += [l for l in got if "NNUE v3" in l]
        if not ok:
            raise Refused(f"no readyok after setoption {n}")
        for l in got:
            low = l.lower()
            if "unknown option" in low or "invalid value" in low or "error" in low:
                raise Refused(f"refused setoption {n}: {l}")

    # ORDER MATTERS: `ucinewgame` RESETS THE BOARD TO STARTPOS on this tree (seat 12's S-F1), so it must come
    # BEFORE `position`. My first Step 0 run had them the other way round and every eval returned the startpos
    # value 968, which is what exposed it.
    send("ucinewgame"); send("isready"); to("readyok", 30)
    if fen:
        send("position fen " + fen)
        send("isready"); to("readyok", 30)
    # bench and eval answer with an `info string ...` line and NOT a bestmove, so send isready FIRST and wait
    # for its readyok; the answer line arrives before it.
    send(command)
    send("isready")
    lines, ok = to("readyok", 300)
    if not ok:
        raise Refused(f"no readyok after '{command}' within 300 s")
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return lines + n3lines


def bench_nodes(regime, spec):
    lines = run(regime, spec)
    for l in reversed(lines):
        m = re.search(r"\bnodes (\d+)", l)
        if m:
            return int(m.group(1)), lines
    return None, lines


out.append(f"exe  {EXE}")
out.append(f"net  {NET}")
out.append("")
out.append("=== EIGHT BENCH NUMBERS (file 7)")
print(out[-1])
for name, spec, expect, regime in BENCH:
    try:
        got, lines = bench_nodes(regime, spec)
    except Refused as exc:
        out.append(f"{name:12s} {spec:10s} REFUSED: {exc}")
        fails.append(f"{name} {spec}: {exc}")
        continue
    ok = (got == expect)
    out.append(f"{name:12s} {spec:10s} expect {expect:8d}  got {str(got):>8s}  {'MATCH' if ok else 'MISMATCH'}")
    if not ok:
        fails.append(f"{name} {spec}: expected {expect}, got {got}")
        out.append("   raw tail: " + " | ".join(lines[-4:]))
    print(out[-1], flush=True)

out.append("")
out.append("=== THREE EVAL LINES (PC20 + test net; each must show hce 0 and nnue == total)")
print(out[-1])
for fen, expect in EVALS:
    try:
        lines = run("pc20net", "eval", fen=fen)
    except Refused as exc:
        out.append(f"eval {fen[:36]:38s} REFUSED: {exc}")
        fails.append(f"eval {fen}: {exc}")
        continue
    ev = next((l for l in lines if l.startswith("info string eval")), None)
    if ev is None:
        out.append(f"eval {fen[:36]:38s} NO EVAL LINE")
        fails.append(f"eval {fen}: no eval line")
        continue
    m = re.search(r"hce (-?\d+) nnue (-?\d+) total (-?\d+)", ev)
    if not m:
        out.append(f"eval {fen[:36]:38s} UNPARSED: {ev}")
        fails.append(f"eval {fen}: unparsed {ev}")
        continue
    hce, nnue, total = (int(x) for x in m.groups())
    ok = (nnue == expect and total == expect and hce == 0)
    out.append(f"eval {fen[:36]:38s} expect nnue {expect:5d}  got hce {hce} nnue {nnue} total {total}  "
               f"{'MATCH' if ok else 'MISMATCH'}")
    if not ok:
        fails.append(f"eval {fen}: expected nnue=total={expect} hce=0, got {hce}/{nnue}/{total}")
    print(out[-1], flush=True)

# the load line, for the record
try:
    lines = run("pc20net", "eval", fen=EVALS[0][0])
    load = [l for l in lines if "NNUE v3" in l]
    out.append("")
    out.append("=== LOAD LINE")
    out += load if load else ["(none found)"]
except Refused as exc:
    out.append(f"load line REFUSED: {exc}")

out.append("")
out.append("=== VERDICT")
if fails:
    out.append(f"STEP 0 FAILED: {len(fails)} mismatch(es) -> STOP THE JOB and report the raw output.")
    for f in fails:
        out.append("  - " + f)
else:
    out.append("STEP 0 PASSED: all eight bench numbers and all three eval lines match file 7.")

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "step0.txt"), "w") as fh:
    fh.write(text)
print(text.split("=== VERDICT")[1])
sys.exit(1 if fails else 0)
