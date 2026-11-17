#!/usr/bin/env python3
"""19-C54: the per-node ratio is a DISTRIBUTION, not a point estimate (answers seat 15).

What went wrong in 19-C53b: the headline 1.0693 was a POOLED ratio (total ms / total nodes per engine).
A heavy right tail drags a pooled ratio upward. Seat 15's replication shows the distribution is bimodal,
so a pooled number is the wrong summary and "~7 % per-node penalty" is the wrong claim.

This run reports:
  - per-position per-node ratio with FULL distribution (min/Q1/median/Q3/max, mean, geometric mean)
  - the CLEAN subset: pairs where the two engines' node counts agree within 2 %, so the time ratio IS
    the per-node ratio with no node-count contamination
  - how much of the pooled ratio is contributed by the tail (top 5 % of pairs)
"""
import subprocess, os, re, math, statistics as st, hashlib
import chess

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "180"))
NODES = int(os.environ.get("NODES", "50000"))

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
             ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(exe, fen, opts, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); send("position fen %s" % fen); send("isready"); send("go %s" % go)
    coll = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        coll.append(ln.rstrip("\n"))
        if ln.startswith("bestmove"):
            break
    try:
        send("quit"); p.wait(timeout=60)
    except Exception:
        p.kill()
    nodes = tms = None
    for ln in coll:
        if ln.startswith("info") and " pv " in ln:
            m = re.search(r"\bnodes (\d+)", ln)
            if m: nodes = int(m.group(1))
            m = re.search(r"\btime (\d+)", ln)
            if m: tms = int(m.group(1))
    return nodes, tms


def q(v, p):
    v = sorted(v); i = (len(v) - 1) * p
    lo = int(i); hi = min(lo + 1, len(v) - 1); f = i - lo
    return v[lo] * (1 - f) + v[hi] * f


def dist(v, label, out):
    g = math.exp(st.mean([math.log(x) for x in v]))
    line = ("%s (n=%d)\n  min %.3f | Q1 %.3f | MEDIAN %.3f | Q3 %.3f | max %.3f\n"
            "  mean %.3f | geometric mean %.3f | sd %.3f" % (
                label, len(v), min(v), q(v, .25), q(v, .5), q(v, .75), max(v),
                st.mean(v), g, st.pstdev(v)))
    out.append(line); print(line)


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    rows = []
    for i, fen in enumerate(fens):
        if i % 2 == 0:
            a = run(BASEPATH, fen, S14, "nodes %d" % NODES)
            b = run(PCPATH, fen, S14 + PC20EXTRA, "nodes %d" % NODES)
        else:
            b = run(PCPATH, fen, S14 + PC20EXTRA, "nodes %d" % NODES)
            a = run(BASEPATH, fen, S14, "nodes %d" % NODES)
        if a[0] and b[0] and a[1] and b[1]:
            rows.append({"fen": fen, "sn": a[0], "sms": a[1], "pn": b[0], "pms": b[1]})
        if (i + 1) % 40 == 0:
            print("  %d/%d" % (i + 1, len(fens)), flush=True)

    out = []
    out.append("19-C54: per-node ratio DISTRIBUTION at fixed `go nodes %d`" % NODES)
    out.append("pc20 sha256 %s" % hashlib.sha256(open(PCPATH, "rb").read()).hexdigest())
    out.append("positions: their_600.fens first %d ; usable %d" % (NPOS, len(rows)))
    out.append("")

    # per-position per-node ratio
    pn_ratio = [(r["pms"] / r["pn"]) / (r["sms"] / r["sn"]) for r in rows]
    node_ratio = [r["pn"] / r["sn"] for r in rows]
    time_ratio = [r["pms"] / r["sms"] for r in rows]

    dist(node_ratio, "NODE ratio (PC20/S14) at fixed node budget", out)
    dist(time_ratio, "TIME ratio (PC20/S14)", out)
    dist(pn_ratio, "PER-NODE ratio (PC20/S14)", out)

    pooled_pn = (sum(r["pms"] for r in rows) / sum(r["pn"] for r in rows)) / \
                (sum(r["sms"] for r in rows) / sum(r["sn"] for r in rows))
    out.append("\nPOOLED per-node ratio (total ms/total nodes, PC20 vs S14): %.4f" % pooled_pn)
    out.append("  <-- THIS is the form 19-C53 published as 1.0693")

    # the clean subset: node counts agree within 2 %
    clean = [r for r in rows if abs(r["pn"] / r["sn"] - 1.0) <= 0.02]
    if len(clean) >= 10:
        cp = [(r["pms"] / r["pn"]) / (r["sms"] / r["sn"]) for r in clean]
        ct = [r["pms"] / r["sms"] for r in clean]
        dist(cp, "\nCLEAN SUBSET (node counts within 2 %%): per-node ratio", out)
        dist(ct, "CLEAN SUBSET: time ratio", out)
        out.append("  clean n = %d of %d (%.0f %%)" % (len(clean), len(rows), 100.0 * len(clean) / len(rows)))

    # tail contribution
    order = sorted(rows, key=lambda r: -(r["pn"] / r["sn"]))
    top = order[:max(1, len(order) // 20)]
    rest = order[len(order) // 20:]
    out.append("\nTAIL CONTRIBUTION (top 5 %% of node-ratio pairs, n=%d):" % len(top))
    out.append("  their node ratios: %s" % [round(r["pn"] / r["sn"], 2) for r in top])
    out.append("  pooled per-node ratio WITHOUT them: %.4f" % (
        (sum(r["pms"] for r in rest) / sum(r["pn"] for r in rest)) /
        (sum(r["sms"] for r in rest) / sum(r["sn"] for r in rest))))
    out.append("  pooled per-node ratio WITH them   : %.4f" % pooled_pn)

    with open(os.path.join(HERE, "distribution_result.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
        f.write("\nper-position (node ratio, time ratio, per-node ratio):\n")
        for r in rows:
            f.write("  %5d/%5d n %.3f | %4d/%4d ms %.3f | pernode %.3f\n" % (
                r["pn"], r["sn"], r["pn"] / r["sn"], r["pms"], r["sms"], r["pms"] / r["sms"],
                (r["pms"] / r["pn"]) / (r["sms"] / r["sn"])))


if __name__ == "__main__":
    main()
