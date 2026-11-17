#!/usr/bin/env python3
"""19-C49: what does `softnodes N` actually buy? (granularity of the soft budget)

Source fact (src/search.cpp:2932): the soft limit is tested only after a COMPLETED iteration, and the hard
cap is 4N (search.cpp:2499). So `softnodes N` stops at the first iteration boundary >= N nodes.

Question: do `softnodes 2000` and `softnodes 3000` buy the SAME search? If so, the 2000-vs-3000 dispute is
about a variable that is often not varying.
"""
import subprocess, sys, os, hashlib, json

PCPATH = os.path.expanduser("~/pcbuild/build/forge")
BASEPATH = os.path.expanduser("~/build_rel/forge")
FENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "positions_used_200.fens")
OUTDIR = os.path.dirname(os.path.abspath(__file__))

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
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def run(exe, fen, opts, go):
    """One search with an arbitrary `go` line. stdin stays open; read to bestmove."""
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
    send("go %s" % go)
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
    out = "\n".join(coll)
    for b in BAD:
        if b in out:
            raise RuntimeError("guard: %r\n%s" % (b, out[:800]))
    best, dep, nodes, score = None, None, None, None
    degenerate = False
    softnodes_reported = None
    for ln in out.splitlines():
        t = ln.split()
        if not t:
            continue
        if t[0] == "bestmove":
            best = t[1]
        elif t[0] == "info" and t[1:2] == ["string"] and "softnodes nodes" in ln:
            import re as _re
            m = _re.search(r"softnodes nodes (\d+)", ln)
            if m:
                softnodes_reported = int(m.group(1))
        elif t[0] == "info" and " pv " in ln:
            import re
            m = re.search(r"\bdepth (\d+)", ln)
            if m:
                dep = int(m.group(1))
            m = re.search(r"\bnodes (\d+)", ln)
            if m:
                nodes = int(m.group(1))
            m = re.search(r"\bscore (cp|mate) (-?\d+)", ln)
            if m:
                score = (m.group(1), int(m.group(2)))
    # DEGENERATE CASE (19-C49): `softnodes N` has hard cap 4N (search.cpp:2499) and only stops at a
    # COMPLETED iteration (search.cpp:2932). On an expensive position no iteration completes before the
    # hard cap, so the engine emits no info line at all and returns root_candidates.front() - a move
    # chosen by nothing. That is NOT a failed search to be thrown away; it is a state to be counted,
    # because it makes "depth" 0 and silently corrupts any depth comparison that includes it.
    if nodes is None or nodes == 0 or best is None or score is None:
        if softnodes_reported is not None and best is not None:
            degenerate = True
            return best, 0, softnodes_reported, None, True, softnodes_reported
        raise RuntimeError("no real search: nodes=%r best=%r score=%r\n%s" % (nodes, best, score, out[:800]))
    return best, dep, nodes, score, degenerate, softnodes_reported


def main():
    pos = [l.strip() for l in open(FENS) if l.strip()]
    slice_ = pos[:200]          # the file already IS the 200 positions searched in 19-C49
    results = {}
    for tag, exe, opts in (("s14", BASEPATH, S14), ("pc20", PCPATH, S14 + PC20EXTRA)):
        rows = []
        for i, fen in enumerate(slice_):
            r = {}
            for budget in (2000, 3000):
                best, dep, nodes, score, degen, rep = run(exe, fen, opts, "softnodes %d" % budget)
                r[budget] = (best, dep, nodes, score, degen)
            r["fen"] = fen
            rows.append(r)
            if (i + 1) % 25 == 0:
                same = sum(1 for x in rows if x[2000][:1] == x[3000][:1] and x[2000][1] == x[3000][1])
                print("%s %d/%d  identical-so-far %d" % (tag, i + 1, len(slice_), same), flush=True)
        results[tag] = rows

    with open(os.path.join(OUTDIR, "raw_result.txt"), "w") as f:
        f.write("19-C49: does softnodes 2000 vs 3000 buy the same search?\n")
        f.write("build pc20 sha256 %s ; base sha256 %s\n" % (
            hashlib.sha256(open(PCPATH, "rb").read()).hexdigest(),
            hashlib.sha256(open(BASEPATH, "rb").read()).hexdigest()))
        f.write("positions: R_2911.fens odd lines, %d\n\n" % len(slice_))
        for tag in ("s14", "pc20"):
            rows = results[tag]
            n = len(rows)
            ident = [r for r in rows if r[2000][0] == r[3000][0] and r[2000][1] == r[3000][1]]
            depth_same = [r for r in rows if r[2000][1] == r[3000][1]]
            n2000 = sum(r[2000][2] for r in rows)
            n3000 = sum(r[3000][2] for r in rows)
            d2000 = sum(r[2000][1] for r in rows)
            d3000 = sum(r[3000][1] for r in rows)
            f.write("=== %s ===\n" % tag)
            f.write("identical (bestmove AND depth) 2000 vs 3000: %d of %d = %.1f %%\n" % (
                len(ident), n, 100.0 * len(ident) / n))
            f.write("same depth only: %d of %d = %.1f %%\n" % (
                len(depth_same), n, 100.0 * len(depth_same) / n))
            f.write("total nodes: 2000-budget %d, 3000-budget %d, ratio %.4f\n" % (
                n2000, n3000, n3000 / n2000))
            f.write("mean nodes: %.1f vs %.1f  (budget says 2000/3000; if softnodes overruns this shows it)\n" % (
                n2000 / n, n3000 / n))
            f.write("total depth: %d vs %d (diff %+d)\n" % (d2000, d3000, d3000 - d2000))
            # 19-C49: the degenerate class. depth 0 + no PV + hard cap hit = no iteration ever completed.
            deg = [r for r in rows if r[2000][4] or r[3000][4]]
            deg2 = [r for r in rows if r[2000][4]]
            deg3 = [r for r in rows if r[3000][4]]
            f.write("DEGENERATE (no completed iteration, hard cap 4N hit, move unsearched):\n")
            f.write("  at 2000: %d of %d = %.1f %%\n" % (len(deg2), n, 100.0 * len(deg2) / n))
            f.write("  at 3000: %d of %d = %.1f %%\n" % (len(deg3), n, 100.0 * len(deg3) / n))
            f.write("  either : %d of %d = %.1f %%\n" % (len(deg), n, 100.0 * len(deg) / n))
            f.write("  indices: %s\n" % [rows.index(r) for r in deg][:40])
            # depth difference restricted to the SAME-BESTMOVE subset (seat 27's control point)
            same_bm = [r for r in rows if r[2000][0] == r[3000][0]]
            if same_bm:
                ds = sum(r[3000][1] - r[2000][1] for r in same_bm)
                f.write("  depth diff on same-bestmove subset (%d pos): %+d\n" % (len(same_bm), ds))
            diffbm = [r for r in rows if r[2000][0] != r[3000][0]]
            if diffbm:
                dd = sum(r[3000][1] - r[2000][1] for r in diffbm)
                f.write("  depth diff on DIFFERENT-bestmove subset (%d pos): %+d\n" % (len(diffbm), dd))
            f.write("\n")
        f.write("per-position:\n")
        for i in range(len(slice_)):
            f.write("  %3d %s\n" % (i, slice_[i]))
            for tag in ("s14", "pc20"):
                r = results[tag][i]
                f.write("      %-4s 2k: %s d%-2s n%-6s | 3k: %s d%-2s n%-6s %s\n" % (
                    tag, r[2000][0], r[2000][1], r[2000][2], r[3000][0], r[3000][1], r[3000][2],
                    "IDENTICAL" if (r[2000][0] == r[3000][0] and r[2000][1] == r[3000][1]) else ""))
    for tag in ("s14", "pc20"):
        rows = results[tag]
        n = len(rows)
        ident = sum(1 for r in rows if r[2000][0] == r[3000][0] and r[2000][1] == r[3000][1])
        print("%s: identical %d/%d = %.1f %%, mean nodes %.0f/%.0f, depth diff %+d" % (
            tag, ident, n, 100.0 * ident / n,
            sum(r[2000][2] for r in rows) / n, sum(r[3000][2] for r in rows) / n,
            sum(r[3000][1] - r[2000][1] for r in rows)))


if __name__ == "__main__":
    main()
