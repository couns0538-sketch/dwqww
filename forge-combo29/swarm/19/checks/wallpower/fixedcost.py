#!/usr/bin/env python3
"""19-C53c: is PC20's excess cost FIXED PER SEARCH rather than per node?

Hypothesis from 19-C53: at fixed DEPTH 12 (~31 ms searches) PC20's time fell only 6.6 % while its nodes fell
12.4 %, implying +6.6 % per-node cost. But a fixed-NODE test says per-node cost is 1.0089 (equal). Both cannot
hold unless PC20 carries a FIXED overhead per search that is amortised as the search grows.

Test: measure ms-per-100k-nodes at several fixed node budgets. A FIXED per-search cost shows as a per-node
ratio that FALLS toward 1.0 as the budget grows; a truly higher per-node cost stays flat.
"""
import subprocess, os, re, math, statistics as st, hashlib

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "60"))

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


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    out = ["19-C53c: fixed per-search cost vs per-node cost in PC20",
           "pc20 sha256 %s" % hashlib.sha256(open(PCPATH, "rb").read()).hexdigest(),
           "positions: their_600.fens first %d" % NPOS,
           "",
           "%-8s %8s %10s %10s %8s %8s %8s" % ("budget", "n", "S14 ms/Mn", "PC20 ms/Mn", "ratio",
                                              "S14 med", "PC20 med")]
    for budget in (2000, 5000, 20000, 100000):
        rows = []
        for i, fen in enumerate(fens):
            if i % 2 == 0:
                a = run(BASEPATH, fen, S14, "nodes %d" % budget)
                b = run(PCPATH, fen, S14 + PC20EXTRA, "nodes %d" % budget)
            else:
                b = run(PCPATH, fen, S14 + PC20EXTRA, "nodes %d" % budget)
                a = run(BASEPATH, fen, S14, "nodes %d" % budget)
            if a[0] and b[0] and a[1] and b[1]:
                rows.append((a, b))
        if not rows:
            continue
        sn = sum(x[0][0] for x in rows); sms = sum(x[0][1] for x in rows)
        pn = sum(x[1][0] for x in rows); pms = sum(x[1][1] for x in rows)
        per_s = sms / (sn / 1e6); per_p = pms / (pn / 1e6)
        out.append("%-8d %8d %10.1f %10.1f %8.4f %8.0f %8.0f" % (
            budget, len(rows), per_s, per_p, per_p / per_s,
            st.median(x[0][1] for x in rows), st.median(x[1][1] for x in rows)))
        print(out[-1], flush=True)
    out.append("")
    out.append("READ: if the ratio FALLS toward 1.000 as budget grows, PC20's excess is a FIXED per-search cost.")
    out.append("      if it stays flat, it is genuinely higher per-node cost.")
    open(os.path.join(HERE, "fixedcost_result.txt"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
