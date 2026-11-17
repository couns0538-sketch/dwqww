#!/usr/bin/env python3
"""19-C66: does 19-C44's "+3 ply at 20k nodes" survive 130 positions, with ties counted?

Depth is an INTEGER, so at a fixed node budget the two engines often report the SAME depth. Trap 20 applies:
a sign-share over a quantised quantity is dominated by ties, and a positive sum can coexist with most positions
being tied. So report wins / ties / losses + the sum + the median difference.
"""
import subprocess, os, re, statistics as st, hashlib

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
HERE = os.path.dirname(os.path.abspath(__file__))
FENS = os.path.join(HERE, "..", "softgran", "their_600.fens")
NPOS = int(os.environ.get("NPOS", "130"))

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
             ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(exe, fen, opts, nodes):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
    send("isready"); send("position fen %s" % fen); send("isready"); send("go nodes %d" % nodes)
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
    dep = None
    for ln in coll:
        if ln.startswith("info") and " pv " in ln:
            m = re.search(r"\bdepth (\d+)", ln)
            if m:
                dep = int(m.group(1))
    return dep


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    out = ["19-C66: does 19-C44's '+3 ply at 20k' survive n=130, with ties counted?",
           "pc20 sha256 %s ; base sha256 %s" % (
               hashlib.sha256(open(PCPATH, "rb").read()).hexdigest(),
               hashlib.sha256(open(BASEPATH, "rb").read()).hexdigest()),
           "positions: their_600.fens first %d, Threads 1, Hash 16, ABBA, fresh process" % NPOS,
           ""]
    for budget in (20000, 50000):
        rows = []
        for i, fen in enumerate(fens):
            if i % 2 == 0:
                a = run(BASEPATH, fen, S14, budget)
                b = run(PCPATH, fen, S14 + PC20EXTRA, budget)
            else:
                b = run(PCPATH, fen, S14 + PC20EXTRA, budget)
                a = run(BASEPATH, fen, S14, budget)
            if a and b:
                rows.append((a, b))
            if (i + 1) % 40 == 0:
                print("  budget %d  %d/%d" % (budget, i + 1, len(fens)), flush=True)
        wins = sum(1 for a, b in rows if b > a)
        ties = sum(1 for a, b in rows if b == a)
        loss = sum(1 for a, b in rows if b < a)
        plysum = sum(b - a for a, b in rows)
        diffs = [b - a for a, b in rows]
        n = len(rows)
        out.append("=== `go nodes %d`  (n=%d) ===" % (budget, n))
        out.append("  PC20 DEEPER %d | TIE %d (%.1f %%) | PC20 shallower %d" % (
            wins, ties, 100.0 * ties / n, loss))
        out.append("  ply sum %+d over %d positions = %+.3f ply/position" % (plysum, n, plysum / n))
        out.append("  median depth diff %+.1f ; mean %+.3f" % (st.median(diffs), st.mean(diffs)))
        out.append("  strict share (deeper / all)      = %d/%d = %.1f %%" % (wins, n, 100.0 * wins / n))
        out.append("  wins / decided (ties excluded)   = %d/%d = %.1f %%" % (
            wins, wins + loss, 100.0 * wins / (wins + loss) if wins + loss else 0))
        out.append("  depth range: S14 %d-%d, PC20 %d-%d" % (
            min(a for a, b in rows), max(a for a, b in rows),
            min(b for a, b in rows), max(b for a, b in rows)))
        out.append("")
        print("\n".join(out[-8:]), flush=True)
    out.append("19-C44's original claim: S14 59 vs PC20 62 = +3 ply summed over SIX positions (+0.500/position).")
    txt = "\n".join(out)
    open(os.path.join(HERE, "RESULT.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
