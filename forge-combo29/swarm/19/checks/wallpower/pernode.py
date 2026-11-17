#!/usr/bin/env python3
"""19-C53b: measure PC20 per-node cost DIRECTLY on real positions.

Fix the NODE count (go nodes 50000) for both engines, so the node counts are (near) equal and the time ratio
IS the per-node cost ratio - no inference from two noisy ratios.

This tests the transferability of 19-C35, which measured per-node cost at ~1.2 % using `bench 16`.
If the per-node ratio here is materially above 1.02, then bench does not represent real positions and 19-C35
must be qualified.
"""
import subprocess, os, re, math, statistics as st, time, hashlib

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "120"))
NODES = int(os.environ.get("NODES", "50000"))

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
        send("quit"); p.wait(timeout=30)
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
    rows = []
    for i, fen in enumerate(fens):
        if i % 2 == 0:
            a = run(BASEPATH, fen, S14, "nodes %d" % NODES)
            b = run(PCPATH, fen, S14 + PC20EXTRA, "nodes %d" % NODES)
            s, p = a, b
        else:
            b = run(PCPATH, fen, S14 + PC20EXTRA, "nodes %d" % NODES)
            a = run(BASEPATH, fen, S14, "nodes %d" % NODES)
            s, p = a, b
        rows.append((s, p))
        if (i + 1) % 30 == 0:
            print("  %d/%d" % (i + 1, len(fens)), flush=True)

    ok = [(s, p) for s, p in rows if s[0] and p[0] and s[1] and p[1]]
    res = []
    for s, p in ok:
        # normalise to per-node: ms per 100k nodes
        res.append((s[0], s[1], p[0], p[1]))
    tot_s_ms = sum(x[1] for x in res); tot_p_ms = sum(x[3] for x in res)
    tot_s_n = sum(x[0] for x in res); tot_p_n = sum(x[2] for x in res)
    pernode_s = tot_s_ms / (tot_s_n / 1e5)
    pernode_p = tot_p_ms / (tot_p_n / 1e5)
    ratio = pernode_p / pernode_s

    # paired bootstrap-free CI on the ratio of totals is not right; use per-position ln ratio of ms-per-node
    ln = [math.log((x[3] / x[2]) / (x[1] / x[0])) for x in res if x[1] > 0 and x[3] > 0]
    m = st.mean(ln); se = st.pstdev(ln) / math.sqrt(len(ln))

    out = []
    out.append("19-C53b: PC20 PER-NODE cost on real positions, FIXED node budget %d" % NODES)
    out.append("pc20 sha256 %s" % hashlib.sha256(open(PCPATH, "rb").read()).hexdigest())
    out.append("base sha256 %s" % hashlib.sha256(open(BASEPATH, "rb").read()).hexdigest())
    out.append("positions: their_600.fens first %d ; used %d" % (NPOS, len(res)))
    out.append("")
    out.append("node totals: S14 %d ; PC20 %d  (equal-budget check: ratio %.5f)" % (
        tot_s_n, tot_p_n, tot_p_n / tot_s_n))
    out.append("per-100k-nodes: S14 %.2f ms ; PC20 %.2f ms" % (pernode_s, pernode_p))
    out.append("PER-NODE COST RATIO (PC20/S14), aggregate: %.4f" % ratio)
    out.append("  per-position ln-ratio: mean %.4f -> %.4f, 95%% CI [%.4f, %.4f]" % (
        m, math.exp(m), math.exp(m - 1.96 * se), math.exp(m + 1.96 * se)))
    out.append("")
    out.append("COMPARISON WITH 19-C35 (bench 16, ratio 1.0119, CI [0.9997, 1.0241]):")
    out.append("  bench figure says <=1.2 %% dearer ; this run says %.2f %%" % (100 * (ratio - 1)))
    line = "\n".join(out)
    open(os.path.join(HERE, "pernode_result.txt"), "w").write(line + "\n")
    print(line.encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
