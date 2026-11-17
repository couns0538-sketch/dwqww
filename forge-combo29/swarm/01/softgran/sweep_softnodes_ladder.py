#!/usr/bin/env python3
"""swarm seat 01: HOW MANY DISTINCT SEARCHES do a range of budgets buy? (extends seat 19's 19-C49)

Seat 19's own closing question, from their prediction: if a large share of positions get the identical search at two
budgets, then "the practical question is NOT '2000 vs 3000' but 'how many distinct searches do these budgets buy'".
This script answers that directly by sweeping a budget range and counting DISTINCT (bestmove, depth, nodes) triples.

Why a sweep rather than more pairs: a pair tells you whether two budgets collide; a sweep shows the LADDER - where the
rungs are, how wide the gaps are, and therefore which budget ranges are indistinguishable. That converts "50 %
identical at 2000-vs-3000" into a shape a person planning an experiment can use: pick two budgets that land on
different rungs, or accept that your comparison is a no-op.

Design notes, each from a trap I have already paid for:
  * read to `bestmove` before `quit` (Trap 11) - the piped form returns nothing;
  * fresh process per row, `ucinewgame` + `isready` before each (warm-state trap S-F20);
  * report the DISTINCT rungs and their node counts, not just counts of collisions, so the ladder is visible;
  * a control: the largest budget in the sweep must differ from the smallest, or the sweep cannot see the ladder
    at all (Trap 8) and the whole table would be an artefact;
  * state that node counts are deterministic here (verified in S-F123), because otherwise "distinct" would just be
    noise between runs.

Usage: sweep_softnodes_ladder.py <exe> <outdir> [--pc20] [--budgets 500,1000,...]
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# Three positions of contrasting character: one tactical, one quiet, one endgame. The ladder shape differs, which is
# the point - a single position would give a single ladder and invite a generalisation that does not hold.
POSITIONS = [
    ("startpos", "startpos"),
    ("italian", "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
    ("rookend", "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"),
]

DEFAULT_BUDGETS = [250, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 7000, 10000, 15000]


def search(exe, pos, softnodes, pc20):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")
    info = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix):
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("info depth"):
                info.append(line)
            if line.startswith(prefix):
                return line
        return None

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    if pc20:
        for n, v in PC20:
            send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position " + pos)
    send("isready")
    until("readyok")
    send("go softnodes %d" % softnodes)
    bm = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=180)
    except Exception:
        p.kill()

    if bm is None or not info:
        return None
    last = info[-1]
    d = re.search(r"depth (\d+)", last)
    n = re.search(r"nodes (\d+)", last)
    return {"bestmove": bm.split()[1] if len(bm.split()) > 1 else None,
            "depth": int(d.group(1)) if d else None,
            "nodes": int(n.group(1)) if n else None}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    exe, out = args[0], Path(args[1])
    pc20 = "--pc20" in sys.argv
    budgets = DEFAULT_BUDGETS
    if "--budgets" in sys.argv:
        budgets = [int(x) for x in sys.argv[sys.argv.index("--budgets") + 1].split(",")]
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    all_rows = {}
    L = ["HOW MANY DISTINCT SEARCHES does a softnodes budget range buy? (extends 19-C49)",
         "exe: %s" % exe, "sha256: %s" % sha,
         "PC20=%s, Threads 1, Hash 16, fresh process per row, read to bestmove before quit." % pc20,
         "Node counts are deterministic on this build (S-F123), so a repeated rung is a real collision, not noise.",
         "Budgets swept: %s" % budgets, ""]
    print("=== sweeping %d budgets x %d positions" % (len(budgets), len(POSITIONS)), flush=True)

    for name, pos in POSITIONS:
        rows = []
        for b in budgets:
            r = search(exe, pos, b, pc20)
            r["budget"] = b
            rows.append(r)
            print("  %-9s softnodes %-6d -> %s d%s n%s"
                  % (name, b, r["bestmove"], r["depth"], r["nodes"]), flush=True)
        all_rows[name] = rows

        # distinct triples, in the order first seen
        seen, distinct = set(), []
        for r in rows:
            key = (r["bestmove"], r["depth"], r["nodes"])
            if key not in seen:
                seen.add(key)
                distinct.append(r)

        L.append("--- %s ---" % name)
        L.append("budget -> bestmove d=depth n=nodes   [rung index]")
        rung_of = {}
        for i, r in enumerate(distinct):
            rung_of[(r["bestmove"], r["depth"], r["nodes"])] = i + 1
        for r in rows:
            idx = rung_of[(r["bestmove"], r["depth"], r["nodes"])]
            L.append("  %-6d -> %-6s d%-3s n%-7s [rung %d]"
                     % (r["budget"], r["bestmove"], r["depth"], r["nodes"], idx))
        L.append("  **%d budgets bought %d DISTINCT searches**" % (len(rows), len(distinct)))
        L.append("")

        # the Trap 8 control: the sweep must see at least two rungs, or it cannot see the ladder at all
        if len(distinct) < 2:
            L.append("  CONTROL FAILED for %s: every budget returned the same search, so this sweep cannot" % name)
            L.append("  distinguish budgets and its collision count is meaningless. Reported, not used.")
        all_rows[name + "_distinct"] = len(distinct)

    L.append("SUMMARY")
    # THE PAIR COLLISION RATE MUST BE COUNTED, NOT DERIVED FROM THE RUNG COUNT. My first formula here was
    # `1 - (distinct-1)/(n-1)`, which printed 36/55/45 %; the true rate - the fraction of budget PAIRS that return
    # the identical search - is 11/15/17 %, computed by enumerating the pairs. The formula was a plausible guess at a
    # quantity I had not defined; two rungs holding many budgets do not collide with each other as often as their
    # sizes suggest, because the pairs within a rung are few relative to all pairs. Same class of error as S-F126.
    import itertools
    for name, _ in POSITIONS:
        rs = all_rows[name]
        d = all_rows[name + "_distinct"]
        keys = [(r["bestmove"], r["depth"], r["nodes"]) for r in rs]
        pairs = list(itertools.combinations(range(len(rs)), 2))
        same = sum(1 for i, j in pairs if keys[i] == keys[j])
        L.append("  %-9s %d budgets -> %d distinct searches; **%d of %d budget pairs (%.0f %%) return the IDENTICAL"
                 " search**"
                 % (name, len(rs), d, same, len(pairs), 100.0 * same / max(1, len(pairs))))
    L.append("")
    L.append("WHAT THIS IS FOR: seat 19's own closing question was how many distinct searches a budget range buys.")
    L.append("A pair test (their 2000 vs 3000) can only report a collision rate. This table shows WHERE the rungs are,")
    L.append("which is what someone choosing budgets needs: two budgets inside one gap buy the identical search, so")
    L.append("an experiment comparing them measures nothing, and the fix is to pick budgets that straddle a rung.")

    (out / ("ladder_%s.json" % ("pc20" if pc20 else "plain"))).write_text(
        json.dumps({"sha": sha, "pc20": pc20, "budgets": budgets, "rows": {
            k: v for k, v in all_rows.items() if not k.endswith("_distinct")}}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / ("ladder_%s.txt" % ("pc20" if pc20 else "plain"))).write_text(txt)
    print("")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
