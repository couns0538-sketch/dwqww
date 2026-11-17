#!/usr/bin/env python3
"""19-C53: at adequate power, does PC20's ~11 % node saving become wall time?

Fixed depth 12 so the node counts differ and the saving can show. Interleaved ABBA, fresh process per search.
Timing recorded two ways: the engine's own `time` on the final PV line (excludes startup), and external wall
time around the whole process (includes startup). Both reported - the engine figure is the per-node-cost
question, the external figure is what a user feels.
"""
import subprocess, os, re, json, hashlib, time, statistics as st, math

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "120"))
DEPTH = 12

S14 = [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
    ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
    ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
    ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
    ("IirDepth", 2), ("NonPawnCorrection", "true"),
]
PC20EXTRA = [
    ("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]


def run(exe, fen, opts):
    t0 = time.perf_counter()
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready")
    send("position fen %s" % fen)
    send("isready")
    send("go depth %d" % DEPTH)
    coll = []
    while True:
        ln = p.stdout.readline()
        if not ln:
            break
        coll.append(ln.rstrip("\n"))
        if ln.startswith("bestmove"):
            break
    try:
        send("quit")
        p.wait(timeout=30)
    except Exception:
        p.kill()
    ext_ms = (time.perf_counter() - t0) * 1000.0

    best, dep, nodes, eng_ms = None, None, None, None
    for ln in coll:
        t = ln.split()
        if not t:
            continue
        if t[0] == "bestmove":
            best = t[1]
        elif t[0] == "info" and " pv " in ln:
            m = re.search(r"\bdepth (\d+)", ln)
            if m:
                dep = int(m.group(1))
            m = re.search(r"\bnodes (\d+)", ln)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"\btime (\d+)", ln)
            if m:
                eng_ms = int(m.group(1))
    return {"bestmove": best, "depth": dep, "nodes": nodes, "eng_ms": eng_ms, "ext_ms": ext_ms}


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    rows = []
    for i, fen in enumerate(fens):
        # ABBA within each position: alternate which engine goes first to cancel ordering drift
        if i % 2 == 0:
            a = run(BASEPATH, fen, S14)
            b = run(PCPATH, fen, S14 + PC20EXTRA)
            s, p = a, b
        else:
            b = run(PCPATH, fen, S14 + PC20EXTRA)
            a = run(BASEPATH, fen, S14)
            s, p = a, b
        rows.append({"fen": fen, "s14": s, "pc20": p})
        if (i + 1) % 20 == 0:
            print("  %d/%d" % (i + 1, len(fens)), flush=True)

    ok = [r for r in rows if r["s14"]["eng_ms"] and r["pc20"]["eng_ms"]
          and r["s14"]["nodes"] and r["pc20"]["nodes"]
          and r["s14"]["depth"] == DEPTH and r["pc20"]["depth"] == DEPTH]
    dropped = len(rows) - len(ok)

    def summarize(key, label):
        rs = [r for r in ok if r["s14"][key] and r["pc20"][key] and r["s14"][key] > 0]
        lnr = [math.log(r["pc20"][key] / r["s14"][key]) for r in rs]
        n = len(lnr)
        mean = st.mean(lnr)
        sd = st.pstdev(lnr) if n > 1 else 0.0
        se = sd / math.sqrt(n)
        lo, hi = math.exp(mean - 1.96 * se), math.exp(mean + 1.96 * se)
        ratio = math.exp(mean)
        # 80 % power at this sd
        n80_12 = ((1.96 + 0.84) * sd / 0.12) ** 2
        return ("%s: n=%d  ratio PC20/S14 = %.4f  95%% CI [%.4f, %.4f]  sd(ln)=%.3f  "
                "n needed for 12%% at 80%% power = %.0f" % (
                    label, n, ratio, lo, hi, sd, n80_12))

    node_ln = [math.log(r["pc20"]["nodes"] / r["s14"]["nodes"]) for r in ok]
    node_ratio = math.exp(st.mean(node_ln))

    with open(os.path.join(HERE, "raw_result.txt"), "w") as f:
        f.write("19-C53: does PC20's node saving become wall time?  depth %d, Threads 1, Hash 16\n" % DEPTH)
        f.write("pc20 sha256 %s\nbase sha256 %s\n" % (
            hashlib.sha256(open(PCPATH, "rb").read()).hexdigest(),
            hashlib.sha256(open(BASEPATH, "rb").read()).hexdigest()))
        f.write("positions: their_600.fens first %d ; used %d, dropped %d (did not reach depth %d)\n\n" % (
            NPOS, len(ok), dropped, DEPTH))
        f.write("NODE RATIO (PC20/S14), geometric mean: %.4f\n" % node_ratio)
        f.write("  total nodes S14 %d ; PC20 %d ; saving %.2f %%\n\n" % (
            sum(r["s14"]["nodes"] for r in ok), sum(r["pc20"]["nodes"] for r in ok),
            100.0 * (1 - sum(r["pc20"]["nodes"] for r in ok) / sum(r["s14"]["nodes"] for r in ok))))
        for key, label in (("eng_ms", "ENGINE-REPORTED time (ms)"), ("ext_ms", "EXTERNAL wall time (ms)")):
            line = summarize(key, label)
            f.write(line + "\n")
            print(line)
        f.write("\nper-position:\n")
        for i, r in enumerate(ok):
            f.write("  %3d S14 %5d ms/%7d n | PC20 %5d ms/%7d n | ratio %.3f\n" % (
                i, r["s14"]["eng_ms"], r["s14"]["nodes"], r["pc20"]["eng_ms"], r["pc20"]["nodes"],
                r["pc20"]["eng_ms"] / r["s14"]["eng_ms"] if r["s14"]["eng_ms"] else 0))
    print("\nnode ratio %.4f ; saved %.2f %%" % (
        node_ratio, 100.0 * (1 - sum(r["pc20"]["nodes"] for r in ok) / sum(r["s14"]["nodes"] for r in ok))))


if __name__ == "__main__":
    main()
