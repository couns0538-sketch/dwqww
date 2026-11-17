#!/usr/bin/env python3
"""check_s12f24.py OUT — my own check of seat 12's S-F24, the fixed-node machine-speed anchor.

Their claim, in three parts:
 (1) `go nodes 1000000` takes about **594 ms per million REPORTED nodes** on their box, median of 7;
 (2) it measures machine speed with no Hash/MultiPV in it — so it is an anchor for the ratio;
 (3) **the anchor ALONE can be fooled**: a uniformly slow engine that also misreports nodes was reported as
     **0.67x FASTER** by the anchor. That third part is the interesting one, and it is a claim about the
     anchor's LIMIT rather than its value.

I can check (1) on my box — expecting a DIFFERENT number, since the claim is machine-specific — and I can check (3)
directly with a fake engine that is slow AND under-reports nodes.

(1) is the wrong thing to confirm numerically (different box), so the useful check is: does the anchor's number move
when machine speed moves, and does it FAIL to detect a lying engine? That is (3), and it is testable with a plant.

ARGUMENT ORDER: OUT first.
"""
import os
import statistics
import subprocess
import sys
import threading
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
N = 1000000
REPEATS = 7
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]
FEN = "r2q1rk1/ppp2ppp/3bbn2/3p4/8/1PN1PN2/PBPPBPPP/R2Q1RK1 w - - 0 10"

# a fake engine that searches for a fixed WALL time and then LIES about how many nodes it visited
FAKE = "/tmp/fake_slow_liar.sh"
open(FAKE, "w").write("""#!/usr/bin/env bash
# slow, and reports only 1/3 of the nodes it pretends to have visited
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name FAKE_SLOW_LIAR"; echo "uciok";;
    isready) echo "readyok";;
    setoption*) : ;;
    ucinewgame) : ;;
    position*) : ;;
    go*) sleep 1.2; echo "info depth 1 score cp 0 nodes 333333 pv e2e4"; echo "bestmove e2e4";;
    quit) exit 0;;
  esac
done
""")
os.chmod(FAKE, 0o755)


def anchor(exe, is_fake=False):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    if not is_fake:
        for k, v in PC20:
            send("setoption name %s value %s" % (k, v))
            sync()
    send("ucinewgame")
    sync()
    send("position fen " + FEN)
    sync()
    lines = []
    done = threading.Event()

    def rd():
        while True:
            l = p.stdout.readline()
            if not l:
                break
            lines.append(l.rstrip("\n"))
            if l.startswith("bestmove"):
                break
        done.set()

    t0 = time.monotonic()
    send("go nodes %d" % N)
    threading.Thread(target=rd, daemon=True).start()
    if not done.wait(180.0):
        p.kill()
        return None
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    nodes = None
    for l in lines:
        if l.startswith("info depth") and "nodes" in l.split():
            t = l.split()
            try:
                nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
    return {"wall": wall, "nodes": nodes}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 12 S-F24 — the fixed-node anchor, and its LIMITATION (the part worth checking)")
emit()
emit("`go nodes %d`, PC r15 PC20, Threads 1, Hash 16, %d fresh processes." % (N, REPEATS))
emit()
real = [anchor(EXE) for _ in range(REPEATS)]
real = [r for r in real if r]
per_million = [(r["wall"] / (r["nodes"] / N)) if r["nodes"] else None for r in real]
per_million = [x for x in per_million if x]
emit("| run | wall ms | reported nodes | ms per million reported nodes |")
emit("|---|---|---|---|")
for i, r in enumerate(real, 1):
    pm = (r["wall"] / (r["nodes"] / N)) if r["nodes"] else None
    emit("| %d | %.1f | %s | %s |" % (i, r["wall"], f"{r['nodes']:,}", ("%.1f" % pm) if pm else "-"))
emit()
emit("| quantity | my box | seat 12's box |")
emit("|---|---|---|")
emit("| **median ms per million reported nodes** | **%.1f** | 594 (their reported figure) |" %
     (statistics.median(per_million) if per_million else 0))
emit()
emit("(The absolute number SHOULD differ between boxes — that is what an anchor is for. So I do not treat a "
     "difference as a refutation; I report mine for the record.)")

emit()
emit("## The limitation they name, tested with a plant: a slow engine that LIES about nodes")
fake = [anchor(FAKE, is_fake=True) for _ in range(3)]
fake = [f for f in fake if f]
emit()
emit("| arm | wall ms | reported nodes | anchor's ms per million REPORTED nodes |")
emit("|---|---|---|---|")
emit("| real engine (median) | %.1f | %s | **%.1f** |" %
     (statistics.median([r["wall"] for r in real]), f"{statistics.median([r['nodes'] for r in real]):,}",
      statistics.median(per_million) if per_million else 0))
emit("| fake slow liar (median) | %.1f | %s | **%.1f** |" %
     (statistics.median([f["wall"] for f in fake]), f"{statistics.median([f['nodes'] for f in fake]):,}",
      statistics.median([f["wall"] / (f["nodes"] / N) for f in fake if f["nodes"]])))
real_pm = statistics.median(per_million) if per_million else 1
fake_pm = statistics.median([f["wall"] / (f["nodes"] / N) for f in fake if f["nodes"]]) if fake else 0
ratio = fake_pm / real_pm if real_pm else 0
emit()
emit("| question | answer |")
emit("|---|---|")
emit("| the fake is genuinely SLOWER in wall time | **%s** (%.0f ms vs %.0f ms) |" %
     ("YES" if statistics.median([f["wall"] for f in fake]) > statistics.median([r["wall"] for r in real]) else "no",
      statistics.median([f["wall"] for f in fake]), statistics.median([r["wall"] for r in real])))
emit("| the anchor reports the fake as FASTER (ratio < 1) | **%s** (fake/real = %.2f) |" %
     ("YES — the anchor is fooled" if ratio < 1 else "no — the anchor is not fooled here", ratio))
emit()
if ratio < 1:
    emit("**CONFIRMS their limitation**: a uniformly slow engine that under-reports its node count is scored as")
    emit("FASTER by an anchor that divides wall time by REPORTED nodes. The anchor measures (machine speed) / (honesty")
    emit("about nodes), and it cannot separate the two. That is exactly why they keep a ratio-based grid beside it")
    emit("rather than trusting the anchor alone.")
else:
    emit("**Does NOT reproduce on my plant**: the anchor was not fooled at this level of dishonesty (ratio %.2f)." % ratio)
    emit("Either my fake's under-report was too small to flip the ratio, or the limitation is narrower than stated.")
    emit("I report which, rather than claiming agreement.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
