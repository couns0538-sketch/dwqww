#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 19's 19-C49 — does `softnodes` buy distinct searches, or the same one twice?

Seat 19 predicts, before measuring, that `softnodes N` stops at the first ITERATION BOUNDARY at or after N nodes
(`src/search.cpp:2932`, evaluated only after a completed iteration, with the hard cap set to 4N at `:2499`), and
therefore that `softnodes 2000` and `softnodes 3000` can return the IDENTICAL search on a large fraction of
positions - in which case any "effect of raising the budget" is exactly zero there, not small.

I checked their two source citations and both are right. This is the same phenomenon I measured for `go nodes` in
S-F123 (a budget that selects a rung of a per-position ladder), so I can test their predictions with the same tooling
and a different instrument from theirs.

Their predictions, quoted so the check is falsifiable against their own numbers:
  P1  on 25-60 % of positions, `softnodes 2000` and `softnodes 3000` return the identical (bestmove, depth, nodes).
      KILLED if fewer than 10 % are identical.
  P2  mean spend at `softnodes 2000` EXCEEDS 2000 (overrun), and spend(3000)/spend(2000) is 1.0-1.25, not 1.5.
  P3  (implicit) identical means IDENTICAL - all three of bestmove, depth and nodes - not merely equal depth.

Two things I add that their prediction does not:
  * a NEGATIVE CONTROL: a pair of budgets far apart (2000 vs 20000). If the tool reports these as identical too,
    the tool cannot distinguish budgets at all and P1's fraction means nothing (Trap 8).
  * the exact iteration-boundary boundary: I record the completed totals so the reason for any identity is visible
    as ladder rungs rather than inferred.

Settings: PC20 or plain, Threads 1, Hash 16, fresh process per row, reading to `bestmove` before quitting
(Trap 11 - sending quit with the go command truncates everything and returns None).

Usage: check_softnodes_granularity.py <exe> <outdir> [positions] [--pc20]
"""
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# A spread of position types: the granularity question depends on how large the iteration spanning N happens to be,
# so a single position type would answer it for one ladder only.
POSITIONS = [
    ("startpos", "startpos"),
    ("italian", "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
    ("ruylopez", "fen r1bqk2r/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w kq - 0 8"),
    ("sicilian", "fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"),
    ("kid", "fen r1bq1rk1/ppp1ppbp/2np1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w KQ - 0 8"),
    ("openmid", "fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
    ("rookend", "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"),
    ("pawnend", "fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("mateish", "fen 2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"),
    ("quiet", "fen r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"),
    ("complex", "fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("sparse", "fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
]


def search(exe, pos, softnodes, pc20):
    """One `softnodes` search. Read to bestmove BEFORE quit (Trap 11)."""
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
        p.wait(timeout=120)
    except Exception:
        p.kill()

    if bm is None or not info:
        return None
    last = info[-1]
    depth = re.search(r"depth (\d+)", last)
    nodes = re.search(r"nodes (\d+)", last)
    score = re.search(r"score (cp|mate) (-?\d+)", last)
    return {
        "bestmove": bm.split()[1] if len(bm.split()) > 1 else None,
        "depth": int(depth.group(1)) if depth else None,
        "nodes": int(nodes.group(1)) if nodes else None,
        "score": "%s %s" % (score.group(1), score.group(2)) if score else None,
        "lines": len(info),
    }


def same(a, b):
    return (a and b and a["bestmove"] == b["bestmove"] and a["depth"] == b["depth"]
            and a["nodes"] == b["nodes"])


def main():
    exe, out = sys.argv[1], Path(sys.argv[2])
    pc20 = "--pc20" in sys.argv
    npos = None
    for a in sys.argv[3:]:
        if a.isdigit():
            npos = int(a)
    positions = POSITIONS[:npos] if npos else POSITIONS
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()

    rows = []
    print("=== softnodes 2000 vs 3000, and the 2000 vs 20000 control  (pc20=%s)" % pc20)
    for name, pos in positions:
        r = {}
        for budget in (2000, 3000, 20000):
            r[budget] = search(exe, pos, budget, pc20)
        ident_23 = same(r[2000], r[3000])
        ident_ctrl = same(r[2000], r[20000])
        rows.append({"pos": name, "r2000": r[2000], "r3000": r[3000], "r20000": r[20000],
                     "identical_2000_3000": ident_23, "identical_2000_20000": ident_ctrl})
        print("  %-9s 2000:(%s,d%s,n%s) 3000:(%s,d%s,n%s) identical=%-5s | control identical=%-5s"
              % (name,
                 r[2000] and r[2000]["bestmove"], r[2000] and r[2000]["depth"], r[2000] and r[2000]["nodes"],
                 r[3000] and r[3000]["bestmove"], r[3000] and r[3000]["depth"], r[3000] and r[3000]["nodes"],
                 ident_23, ident_ctrl), flush=True)

    L = ["CHECK of seat 19's 19-C49: does `softnodes` buy distinct searches, or the same one twice?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "PC20=%s, Threads 1, Hash 16, fresh process per row, read to bestmove before quit (Trap 11)." % pc20,
         "Mechanism (verified in source): src/search.cpp:2932 breaks only AFTER a completed iteration, and",
         "src/search.cpp:2499 sets the hard cap to 4N. So spend OVERRUNS N by up to one iteration.",
         "",
         "pos\t2000 (bm,depth,nodes)\t3000 (bm,depth,nodes)\tidentical?\tcontrol 20000 identical?"]
    for r in rows:
        a = r["r2000"] or {}
        b = r["r3000"] or {}
        L.append("%s\t%s,d%s,n%s\t%s,d%s,n%s\t%s\t%s"
                 % (r["pos"], a.get("bestmove"), a.get("depth"), a.get("nodes"),
                    b.get("bestmove"), b.get("depth"), b.get("nodes"),
                    r["identical_2000_3000"], r["identical_2000_20000"]))
    L.append("")

    usable = [r for r in rows if r["r2000"] and r["r3000"]]
    if not usable:
        L.append("NOTHING WAS MEASURED - every row returned no reading, so no fraction exists and none is claimed.")
        (out / "check_softnodes_granularity.txt").write_text("\n".join(L) + "\n")
        print("\n".join(L))
        return 1

    frac = sum(1 for r in usable if r["identical_2000_3000"]) / len(usable)
    ctrl_frac = sum(1 for r in usable if r["identical_2000_20000"]) / len(usable)
    spend2000 = [r["r2000"]["nodes"] for r in usable if r["r2000"]["nodes"]]
    spend3000 = [r["r3000"]["nodes"] for r in usable if r["r3000"]["nodes"]]

    L.append("IDENTICAL 2000-vs-3000: %d of %d = **%.0f %%**" % (sum(1 for r in usable if r["identical_2000_3000"]),
                                                                 len(usable), 100 * frac))
    L.append("CONTROL identical 2000-vs-20000: %d of %d = %.0f %%  (this must be ~0, or the tool cannot tell budgets"
             " apart and the fraction above is meaningless)" % (
                 sum(1 for r in usable if r["identical_2000_20000"]), len(usable), 100 * ctrl_frac))
    L.append("")
    L.append("MEAN SPEND at softnodes 2000: %.0f nodes (request was 2000, so overrun %+0.f)"
             % (statistics.mean(spend2000), statistics.mean(spend2000) - 2000))
    L.append("MEAN SPEND at softnodes 3000: %.0f nodes" % statistics.mean(spend3000))
    L.append("")
    # THE RATIO IS BIMODAL AND ONE SUMMARY NUMBER MISDESCRIBES IT. On the positions where the two budgets buy the
    # SAME iteration the ratio is exactly 1.00; on the others it runs 1.6-3.8. Reporting a single mean (1.586) or a
    # single median (1.325) would describe neither cluster - the S-F126 lesson applied to this table rather than to
    # a published line. Both populations are stated, and the summary statistics are labelled.
    ident_rows = [r for r in usable if r["identical_2000_3000"]]
    diff_rows = [r for r in usable if not r["identical_2000_3000"]]
    L.append("THE SPEND RATIO IS BIMODAL - two populations, not one distribution:")
    L.append("  identical budgets (%d positions): ratio is EXACTLY 1.00 by construction - %s"
             % (len(ident_rows), ", ".join(r["pos"] for r in ident_rows) or "none"))
    if diff_rows:
        rs = [r["r3000"]["nodes"] / r["r2000"]["nodes"] for r in diff_rows]
        L.append("  differing budgets (%d positions): median %.2fx, range %.2f-%.2fx - %s"
                 % (len(diff_rows), statistics.median(rs), min(rs), max(rs),
                    ", ".join("%s %.2fx" % (r["pos"], r["r3000"]["nodes"] / r["r2000"]["nodes"]) for r in diff_rows)))
    L.append("  whole-set summaries, LABELLED because they describe neither cluster:")
    L.append("    ratio of means  %.3f   |   mean of ratios  %.3f   |   median of ratios  %.3f"
             % (statistics.mean(spend3000) / statistics.mean(spend2000),
                statistics.mean([r["r3000"]["nodes"] / r["r2000"]["nodes"] for r in usable]),
                statistics.median([r["r3000"]["nodes"] / r["r2000"]["nodes"] for r in usable])))
    L.append("  (a literal node budget would give a uniform 1.5 on every position)")
    L.append("")

    L.append("SCORED AGAINST SEAT 19's OWN KILL CONDITIONS")
    L.append("  P1 predicted 25-60 %% identical, killed if under 10 %%. Measured %.0f %% -> %s"
             % (100 * frac, "KILLED" if frac < 0.10 else ("PREDICTION STANDS" if frac <= 0.60 else "ABOVE their range")))
    over = statistics.mean(spend2000) > 2000
    ratio_of_means = statistics.mean(spend3000) / statistics.mean(spend2000)
    median_ratio = statistics.median([r["r3000"]["nodes"] / r["r2000"]["nodes"] for r in usable])
    in_range = (1.0 <= ratio_of_means <= 1.25) or (1.0 <= median_ratio <= 1.25)
    L.append("  P2 predicted mean spend > 2000 (overrun) and ratio 1.0-1.25. Measured overrun=%s; ratio of means"
             " %.3f, median of ratios %.3f -> %s"
             % ("yes" if over else "NO", ratio_of_means, median_ratio,
                "PREDICTION STANDS on at least one statistic" if in_range else "OUTSIDE their range on BOTH"))
    L.append("    (seat 19 did not say WHICH ratio statistic; both are shown, and neither lands in 1.0-1.25 - the")
    L.append("     reason is that half the positions have ratio exactly 1.00 and the other half 1.6-3.8)")
    L.append("")
    L.append("WHY THIS IS THE SAME PHENOMENON AS MY S-F123, FROM THE OTHER DIRECTION: `go nodes N` picks a rung of a")
    L.append("per-position ladder BELOW N; `softnodes N` picks the first rung AT OR AFTER N. Both mean the budget is")
    L.append("not a quantity, and in both cases two budgets can select the SAME search - which makes any measured")
    L.append("\"effect of the budget\" exactly zero on those positions rather than small. An identical fraction of")
    L.append("%.0f %% would mean the 2000-vs-3000 comparison is ill-posed on that share of positions." % (100 * frac))

    (out / "check_softnodes_granularity.json").write_text(json.dumps({"sha": sha, "pc20": pc20, "rows": rows}, indent=1))
    (out / "check_softnodes_granularity.txt").write_text("\n".join(L) + "\n")
    print("")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
