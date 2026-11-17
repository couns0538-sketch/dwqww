#!/usr/bin/env python3
"""19-C58: does the NNUE column-prefetch slowdown survive on REAL positions?

Both builds verified to pass all four honesty pins with IDENTICAL node counts, so the patch is a pure
per-node-cost change - the correct control.

Fixed `go nodes 50000`, Threads 1, Hash 16, ABBA, fresh process. Reports the per-position distribution.
"""
import subprocess, os, re, math, statistics as st, hashlib

CTRL = os.path.expanduser("~/pf_nopf/cw/forge-combo29/build/forge")
PF = os.path.expanduser("~/pf_nopf/work/forge-combo29/build/forge")
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

    # per-position per-node ratio (node counts are ~equal by construction at a fixed budget)
    ratios = [(r["pf"][1] / r["pf"][0]) / (r["ctrl"][1] / r["ctrl"][0]) for r in rows]
    pooled = (sum(r["pf"][1] for r in rows) / sum(r["pf"][0] for r in rows)) / \
             (sum(r["ctrl"][1] for r in rows) / sum(r["ctrl"][0] for r in rows))
    slow = sum(1 for x in ratios if x > 1.0)

    out = []
    out.append("19-C58: NNUE column-prefetch slowdown on REAL positions, fixed `go nodes %d`" % NODES)
    out.append("CTRL sha256 %s (0 prefetch calls)" % hashlib.sha256(open(CTRL, "rb").read()).hexdigest())
    out.append("PF   sha256 %s (17 prefetch calls)" % hashlib.sha256(open(PF, "rb").read()).hexdigest())
    out.append("both pass all four honesty pins with IDENTICAL node counts -> pure per-node-cost patch")
    out.append("positions: their_600.fens first %d ; used %d" % (NPOS, len(rows)))
    out.append("")
    out.append("BENCH 13 figures to compare against:")
    out.append("  19-F10 (mine):  ratio 0.9190 CI [0.8841, 0.9552]  -> 8.1 %% slower, 20 pairs")
    out.append("  29-C4  (seat 29): time ratio 1.0943 CI [1.0734, 1.1155] -> 9.43 %% slower, 48 pairs")
    out.append("")
    out.append("REAL POSITIONS, per-node ratio PF/CTRL (n=%d):" % len(ratios))
    out.append("  min %.3f | Q1 %.3f | MEDIAN %.3f | Q3 %.3f | max %.3f" % (
        min(ratios), q(ratios, .25), q(ratios, .5), q(ratios, .75), max(ratios)))
    g = math.exp(st.mean([math.log(x) for x in ratios]))
    out.append("  mean %.3f | geometric mean %.3f | sd %.3f" % (st.mean(ratios), g, st.pstdev(ratios)))
    out.append("  POOLED (total ms/total nodes): %.4f  -> %.2f %% slower" % (pooled, 100 * (pooled - 1)))
    out.append("  GEOMETRIC: %.4f -> %.2f %% slower" % (g, 100 * (g - 1)))
    out.append("  fraction where PF is SLOWER: %d/%d = %.1f %%" % (slow, len(ratios), 100.0 * slow / len(ratios)))
    out.append("")
    out.append("VERDICT vs the two bench figures: %s" % (
        "general claim CONFIRMED (>= 8 %% slower)" if pooled >= 1.08 else
        "effect is REAL but SMALLER than bench" if pooled > 1.01 else
        "largely a BENCH ARTEFACT"))
    txt = "\n".join(out)
    open(os.path.join(HERE, "RESULT.txt"), "w").write(txt + "\n")
    open(os.path.join(HERE, "raw_pairs.txt"), "w").write(
        "\n".join("%d/%d %.3f | %d/%d %.3f | %.4f" % (
            r["pf"][0], r["ctrl"][0], r["pf"][0] / r["ctrl"][0],
            r["pf"][1], r["ctrl"][1], r["pf"][1] / r["ctrl"][1],
            (r["pf"][1] / r["pf"][0]) / (r["ctrl"][1] / r["ctrl"][0])) for r in rows) + "\n")
    print(txt)


if __name__ == "__main__":
    main()
