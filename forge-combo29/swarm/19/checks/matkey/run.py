#!/usr/bin/env python3
"""19-C64: is the material-key cache a real speed win on REAL positions?

CTRL and PF verified to pass all four honesty pins with IDENTICAL node counts, so this is a pure
per-node-cost comparison (same control structure as 19-C58).
"""
import subprocess, os, re, math, statistics as st, hashlib

CTRL = "/home/ubuntu/mk/ctrl/forge-combo29/build/forge"
PF = "/home/ubuntu/mk/work/forge-combo29/build/forge"
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "130"))
NODES = int(os.environ.get("NODES", "50000"))


def run(exe, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    send("isready"); send("position fen %s" % fen); send("isready"); send("go nodes %d" % NODES)
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


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    rows = []
    for i, fen in enumerate(fens):
        if i % 2 == 0:
            a = run(CTRL, fen); b = run(PF, fen)
        else:
            b = run(PF, fen); a = run(CTRL, fen)
        if a[1] and b[1] and a[0] and b[0]:
            rows.append({"ctrl": a, "pf": b})
        if (i + 1) % 30 == 0:
            print("  %d/%d" % (i + 1, len(fens)), flush=True)

    ratios = [(r["pf"][1] / r["pf"][0]) / (r["ctrl"][1] / r["ctrl"][0]) for r in rows]
    node_r = [r["pf"][0] / r["ctrl"][0] for r in rows]
    pooled = (sum(r["pf"][1] for r in rows) / sum(r["pf"][0] for r in rows)) / \
             (sum(r["ctrl"][1] for r in rows) / sum(r["ctrl"][0] for r in rows))
    g = math.exp(st.mean([math.log(x) for x in ratios]))
    faster = sum(1 for x in ratios if x < 1.0)

    out = ["19-C64: material-key cache on REAL positions, fixed `go nodes %d`" % NODES,
           "CTRL sha256 %s" % hashlib.sha256(open(CTRL, "rb").read()).hexdigest(),
           "PF   sha256 %s" % hashlib.sha256(open(PF, "rb").read()).hexdigest(),
           "both pass all four honesty pins with IDENTICAL node counts -> pure per-node-cost control",
           "positions: their_600.fens first %d ; used %d" % (NPOS, len(rows)),
           "",
           "19-F9 claim: nps ratio 1.0059, CI [0.9680, 1.0454], on BENCH 13, n=10 per side",
           "19-F6 claim: material key = 2.71 %% of total self time",
           "",
           "REAL POSITIONS, per-node ratio PF/CTRL (n=%d):" % len(ratios),
           "  min %.3f | Q1 %.3f | MEDIAN %.3f | Q3 %.3f | max %.3f" % (
               min(ratios), q(ratios, .25), q(ratios, .5), q(ratios, .75), max(ratios)),
           "  mean %.4f | geometric %.4f | sd %.4f" % (st.mean(ratios), g, st.pstdev(ratios)),
           "  POOLED %.4f (%.2f %% %s)" % (pooled, abs(100 * (pooled - 1)),
                                            "faster" if pooled < 1 else "slower"),
           "  GEOMETRIC %.4f (%.2f %% %s)" % (g, abs(100 * (g - 1)), "faster" if g < 1 else "slower"),
           "  fraction where PF is FASTER: %d/%d = %.1f %%" % (faster, len(ratios), 100.0 * faster / len(ratios)),
           "  node ratio achieved: mean %.5f (fixed budget held)" % st.mean(node_r)]

    # bootstrap CI on the pooled ratio
    import random
    random.seed(1901)
    bs = []
    n = len(rows)
    for _ in range(4000):
        s = [rows[random.randrange(n)] for _ in range(n)]
        d = sum(r["ctrl"][1] for r in s)
        if d:
            bs.append((sum(r["pf"][1] for r in s) / sum(r["pf"][0] for r in s)) /
                      (sum(r["ctrl"][1] for r in s) / sum(r["ctrl"][0] for r in s)))
    bs.sort()
    lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
    out.append("  pooled bootstrap 95%% CI: [%.4f, %.4f] -> %s" % (
        lo, hi, "EXCLUDES 1.0 = REAL" if (lo > 1.0 or hi < 1.0) else "INCLUDES 1.0 = NOT ESTABLISHED"))
    txt = "\n".join(out)
    open(os.path.join(HERE, "RESULT.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
