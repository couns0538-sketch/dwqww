#!/usr/bin/env python3
"""19-C56: re-check bench-measured NODE claims on real positions.

19-F32 claims `CorrHistV2` saves 4.3 % of nodes, from bench 13 ONLY (587,276 on vs 613,774 off).
19-C55 showed bench gets the SIGN of the PC20 node effect wrong on 2 of 3 benches. So a bench-13
magnitude needs re-checking against real positions.

Test: PC r15, Threads 1, Hash 16, real positions from their_600.fens, fixed DEPTH, toggle CorrHistV2
only (all other PC20 options held constant), interleaved, fresh process per search.
"""
import subprocess, os, re, math, statistics as st, hashlib

PC = os.path.expanduser("~/pcbuild/build/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "120"))
DEPTH = int(os.environ.get("DEPTH", "12"))

BASE = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
        ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
        ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
        ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
        ("IirDepth", 2), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]
ON = BASE + [("CorrHistV2", "true")]
OFF = BASE + [("CorrHistV2", "false")]


def run(fen, opts):
    p = subprocess.Popen([PC], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); send("position fen %s" % fen); send("isready"); send("go depth %d" % DEPTH)
    coll = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        coll.append(ln.rstrip("\n"))
        if ln.startswith("bestmove"):
            break
    try:
        send("quit"); p.wait(timeout=30)
    except Exception:
        p.kill()
    nodes = dep = best = None
    for ln in coll:
        t = ln.split()
        if t and t[0] == "bestmove":
            best = t[1]
        elif ln.startswith("info") and " pv " in ln:
            m = re.search(r"\bnodes (\d+)", ln)
            if m: nodes = int(m.group(1))
            m = re.search(r"\bdepth (\d+)", ln)
            if m: dep = int(m.group(1))
    return nodes, dep, best


def q(v, p):
    v = sorted(v); i = (len(v) - 1) * p
    lo = int(i); hi = min(lo + 1, len(v) - 1); f = i - lo
    return v[lo] * (1 - f) + v[hi] * f


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    rows = []
    for i, fen in enumerate(fens):
        if i % 2 == 0:
            a = run(fen, ON); b = run(fen, OFF)
        else:
            b = run(fen, OFF); a = run(fen, ON)
        if a[0] and b[0] and a[1] == DEPTH and b[1] == DEPTH:
            rows.append({"on": a, "off": b})
        if (i + 1) % 30 == 0:
            print("  %d/%d" % (i + 1, len(fens)), flush=True)

    on_n = sum(r["on"][0] for r in rows); off_n = sum(r["off"][0] for r in rows)
    ratios = [r["on"][0] / r["off"][0] for r in rows]
    pooled = on_n / off_n
    line = []
    line.append("19-C56: CorrHistV2 node effect on REAL positions, depth %d, PC r15, Threads 1, Hash 16" % DEPTH)
    line.append("pc sha256 %s" % hashlib.sha256(open(PC, "rb").read()).hexdigest())
    line.append("positions: their_600.fens first %d ; used %d (both reached depth %d)" % (NPOS, len(rows), DEPTH))
    line.append("")
    line.append("BENCH 13 claim (19-F32): 587,276 on vs 613,774 off = ratio %.4f (saves %.1f %%)" % (
        587276 / 613774, 100 * (1 - 587276 / 613774)))
    line.append("REAL POSITIONS: %d on vs %d off = POOLED ratio %.4f (saves %.1f %%)" % (
        on_n, off_n, pooled, 100 * (1 - pooled)))
    line.append("  per-position ratio: min %.3f | Q1 %.3f | MEDIAN %.3f | Q3 %.3f | max %.3f" % (
        min(ratios), q(ratios, .25), q(ratios, .5), q(ratios, .75), max(ratios)))
    line.append("  mean %.3f | geometric %.3f | sd %.3f" % (
        st.mean(ratios), math.exp(st.mean([math.log(x) for x in ratios])), st.pstdev(ratios)))
    line.append("  fraction where ON uses FEWER nodes: %d/%d = %.1f %%" % (
        sum(1 for x in ratios if x < 1), len(ratios), 100 * sum(1 for x in ratios if x < 1) / len(ratios)))
    line.append("  fraction where bestmove DIFFERS: %d/%d = %.1f %%" % (
        sum(1 for r in rows if r["on"][2] != r["off"][2]), len(rows),
        100 * sum(1 for r in rows if r["on"][2] != r["off"][2]) / len(rows)))
    txt = "\n".join(line)
    open(os.path.join(HERE, "RESULT.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
