#!/usr/bin/env python3
"""19-C60: is the per-position "coin flip" specific to CorrHistV2, or general to the PC20 switches?

One switch at a time, all other PC20 options held constant, PC r15, Threads 1, Hash 16, fixed depth,
real positions, interleaved, fresh process. Reports sign-agreement fraction and IQR/effect for each.
"""
import subprocess, os, re, math, statistics as st, hashlib

PC = os.path.expanduser("~/pcbuild/build/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "120"))
DEPTH = int(os.environ.get("DEPTH", "12"))

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# each entry: (label, options WITH switch at PC20 value, options WITH switch at its OFF/base value)
TESTS = [
    ("TtPruneV2", PC20, [o for o in PC20 if o[0] != "TtPruneV2"] + [("TtPruneV2", "false")]),
    ("CuckooRep", PC20, [o for o in PC20 if o[0] != "CuckooRep"] + [("CuckooRep", "false")]),
    ("CorrHistV2", PC20, [o for o in PC20 if o[0] != "CorrHistV2"] + [("CorrHistV2", "false")]),
    ("HistRework", PC20, [o for o in PC20 if o[0] != "HistRework"] + [("HistRework", 0)]),
]


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
    nodes = dep = None
    for ln in coll:
        if ln.startswith("info") and " pv " in ln:
            m = re.search(r"\bnodes (\d+)", ln)
            if m: nodes = int(m.group(1))
            m = re.search(r"\bdepth (\d+)", ln)
            if m: dep = int(m.group(1))
    return nodes, dep


def q(v, p):
    v = sorted(v); i = (len(v) - 1) * p
    lo = int(i); hi = min(lo + 1, len(v) - 1); f = i - lo
    return v[lo] * (1 - f) + v[hi] * f


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    out = ["19-C60: is the per-position coin flip specific to CorrHistV2 or general to the switches?",
           "PC r15 sha256 %s ; depth %d ; Threads 1 ; Hash 16 ; %d real positions" % (
               hashlib.sha256(open(PC, "rb").read()).hexdigest(), DEPTH, len(fens)),
           "",
           "%-12s %8s %8s %9s %10s %9s %9s" % ("switch", "pooled", "median", "share ON<OFF", "IQR", "effect", "IQR/eff")]
    for label, on_opts, off_opts in TESTS:
        rows = []
        for i, fen in enumerate(fens):
            if i % 2 == 0:
                a = run(fen, on_opts); b = run(fen, off_opts)
            else:
                b = run(fen, off_opts); a = run(fen, on_opts)
            if a[0] and b[0] and a[1] == DEPTH and b[1] == DEPTH:
                rows.append((a[0], b[0]))
        if not rows:
            continue
        ratios = [x[0] / x[1] for x in rows]
        pooled = sum(x[0] for x in rows) / sum(x[1] for x in rows)
        iqr = q(ratios, .75) - q(ratios, .25)
        effect = abs(pooled - 1.0)
        share = sum(1 for x in ratios if x < 1) / len(ratios)
        line = "%-12s %8.4f %8.3f %8.1f %% %10.3f %9.3f %9.1f" % (
            label, pooled, q(ratios, .5), 100 * share, iqr, effect, iqr / effect if effect else 0)
        out.append(line)
        print(line, flush=True)
        out.append("             n=%d  min %.3f Q1 %.3f Q3 %.3f max %.3f" % (
            len(ratios), min(ratios), q(ratios, .25), q(ratios, .75), max(ratios)))
    out.append("")
    out.append("PREDICTED: all four IQR/effect > 5 ; TtPruneV2 share 65-80 %% ; CuckooRep/HistRework 50-60 %%")
    out.append("KILL: if all four share < 60 %, the coin flip is general and C56 must say so for the whole set.")
    open(os.path.join(HERE, "RESULT.txt"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
