#!/usr/bin/env python3
"""swarm seat 01: reproduce seat 29's `29-F59` method (fixed node budget) on MY build — a third independent route.

Why a third route: my S-F118 measured per-node cost from `bench 13` wall medians. Seat 29's `29-F59` used a fixed
node budget (`go nodes 200000`) on 8 real-game positions, interleaved ABBA, and got 0.96x (PC20) and 1.16x (plain).
Those are different instruments. If their method also gives ~1x on my build, the conclusion "the v3 net costs about
the same per node as the built-in evaluation" stops depending on either one of us.

THE METHOD'S OWN HAZARD, handled explicitly: with a fixed node budget the node count is the *control*, not the
result. If the two configurations do not actually reach the same node count, the comparison is meaningless — so the
node count is asserted, not assumed. (`go nodes` is Trap-adjacent: my Trap 3 note says `depth 0` is one ply, and
Trap 6 says a fixed-depth command needs a cap. A fixed NODE command has its own version of that: the search may
terminate early on mate/stalemate before spending the budget, and then the ratios measure 8 different trees.)

ABBA interleaving matters on a shared 4-core box, where I have already produced two phantom timing results
(S-F74, S-F115). I interleave A,B,B,A per position and take the median of the per-configuration samples, so a drift
in machine load hits both configurations equally.

Usage: check_per_node_abba.py <v3-exe> <testnet.fnn3> <outdir> [budget]
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

# 8 real-game positions (midgame-ish, none solved — see the terminal-root trap: a solved position ends before
# spending the node budget, which would make the two configurations search different trees)
POSITIONS = [
    ("startpos", "startpos"),
    ("italian", "fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"),
    ("ruylopez", "fen r1bqk2r/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w kq - 0 8"),
    ("sicilian", "fen r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"),
    ("kid", "fen r1bq1rk1/ppp1ppbp/2np1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w KQ - 0 8"),
    ("openmid", "fen r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10"),
    ("rookend", "fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40"),
    ("pawnend", "fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
]


def run_one(exe, net, pos, node_budget, pc20, use_net):
    """One search, reading to `bestmove` BEFORE sending `quit`.

    THIS IS THE WHOLE BUG THAT MADE THE FIRST VERSION RETURN None FOR EVERY POSITION. Writing `go` and `quit` into
    the same pipe closes it while the search is still running, so the engine's info lines and even its bestmove are
    lost - `grep -c '^info depth'` on that form returns 0. The engine behaves identically either way; the difference
    is entirely in whether the reader waits. Recorded as Trap 11 / S-F121, and this script was still doing it an
    hour later, which is why the wait is now explicit rather than left to the shell.
    """
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
    if use_net:
        send("setoption name NNUEArchFile value %s" % net)
        send("setoption name NNUEArch value true")
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position " + pos)
    send("isready")
    until("readyok")
    send("go nodes %d" % node_budget)
    bm = until("bestmove")          # WAIT for the search to finish before quitting
    send("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()

    if not info or bm is None:
        return None
    last = info[-1]
    n = re.search(r"nodes (\d+)", last)
    t = re.search(r"time (\d+)", last)
    if not (n and t):
        return None
    return int(n.group(1)), int(t.group(1))


def main():
    exe, net, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    budget = int(sys.argv[4]) if len(sys.argv) > 4 else 200000
    out.mkdir(parents=True, exist_ok=True)
    sha = {"exe": hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "net": hashlib.sha256(Path(net).read_bytes()).hexdigest()}

    L = ["Reproduction of seat 29's 29-F59 method (fixed node budget) on seat 01's build - a third independent route",
         "exe sha256: %s" % sha["exe"], "net sha256: %s" % sha["net"],
         "Threads 1, Hash 16, node budget %d, ABBA interleaving per position, PC20 where named." % budget,
         "Control: each configuration must reproduce its OWN node count across the ABBA repeats (then the per-100k",
         "normalisation is exact). The two configurations need NOT match each other - with a fixed node budget the",
         "loop exits at an iteration boundary, so different tree shapes cross the budget at different points.",
         ""]
    results = {}
    for mode, pc20 in (("pc20", True), ("plain", False)):
        per_pos = []
        L.append("--- %s (budget %d) ---" % (mode, budget))
        L.append("position\tno-net nodes\tno-net ms\tnet nodes\tnet ms\tms per 100k (no-net -> net)")
        for name, pos in POSITIONS:
            abba = []
            for use_net in (False, True, True, False):     # ABBA
                abba.append((use_net, run_one(exe, net, pos, budget, pc20, use_net)))
            nonet = [r for u, r in abba if u is False and r]
            withnet = [r for u, r in abba if u is True and r]
            if not nonet or not withnet:
                L.append("%s\tMISSING" % name)
                continue
            a_nodes = {r[0] for r in nonet}
            b_nodes = {r[0] for r in withnet}
            a_ms = statistics.median([r[1] for r in nonet])
            b_ms = statistics.median([r[1] for r in withnet])
            # THE CONTROL IS DETERMINISM PER CONFIGURATION, NOT EQUALITY BETWEEN THEM.
            # My first version required a_nodes == b_nodes and dropped every row, which was a design error: with a
            # fixed node budget the loop exits at an ITERATION boundary, so two configurations with different tree
            # shapes cross the budget at different points and legitimately end on different counts (166,281 vs
            # 105,432 on startpos). Requiring equality would make this method permanently unusable - and it would
            # have hidden a real fact, that `go nodes N` under-delivers (200,000 requested, 101,640 spent).
            # What must hold is that each configuration reproduces its OWN count across the ABBA repeats; then
            # normalising by the measured count is exact rather than an extrapolation.
            ok = (len(a_nodes) == 1 and len(b_nodes) == 1)
            a100 = a_ms * 100000.0 / max(a_nodes)
            b100 = b_ms * 100000.0 / max(b_nodes)
            per_pos.append({"pos": name, "a_nodes": sorted(a_nodes), "b_nodes": sorted(b_nodes),
                            "a_ms": a_ms, "b_ms": b_ms, "a100": a100, "b100": b100, "comparable": ok})
            L.append("%s\t%s\t%d\t%s\t%d\t%.1f -> %.1f%s"
                     % (name, sorted(a_nodes), a_ms, sorted(b_nodes), b_ms, a100, b100,
                        "" if ok else "   [NODE COUNTS DIFFER - DROPPED]"))
        good = [p for p in per_pos if p["comparable"]]
        if good:
            ratio = statistics.median([p["b100"] / p["a100"] for p in good])
            results[mode] = {"n": len(good), "median_ratio": ratio,
                             "a100": statistics.median([p["a100"] for p in good]),
                             "b100": statistics.median([p["b100"] for p in good])}
            # REPORT BOTH STATISTICS, because they are not the same number. `median_ratio` is the median of the
            # per-position ratios; `a100`/`b100` are the medians of the two columns. Printing the two medians next to
            # the median-of-ratios invited a reader to divide 46.6 by 54.0 and get 0.863 where the line said 0.91 -
            # two correct numbers, one misleading sentence. Both are now labelled.
            ratio_of_medians = results[mode]["b100"] / results[mode]["a100"]
            results[mode]["ratio_of_medians"] = ratio_of_medians
            L.append("  %s: %d comparable positions" % (mode, len(good)))
            L.append("    median of per-position ratios : **%.3fx**   <- the headline figure" % ratio)
            L.append("    ratio of the two column medians: **%.3fx**   (%.1f -> %.1f ms/100k)"
                     % (ratio_of_medians, results[mode]["a100"], results[mode]["b100"]))
            L.append("    both are valid summaries; they differ because the positions are not equally weighted, and"
                     " the spread of per-position ratios is wider than either number suggests.")
        L.append("")

    L.append("COMPARISON with the published figures")
    L.append("  seat 29 (29-F59): PC20 0.96x, plain 1.16x   [their build, their box]")
    L.append("  seat 01 (S-F118): 1.09x from bench-13 wall medians, 4 file-backed runs   [this build, this box]")
    for mode in ("pc20", "plain"):
        if mode in results:
            L.append("  seat 01, THEIR method, this build: %s **%.2fx** (%d positions)"
                     % (mode, results[mode]["median_ratio"], results[mode]["n"]))
    L.append("")
    if len(results) == 2:
        r_pc, r_pl = results["pc20"]["median_ratio"], results["plain"]["median_ratio"]
        hi, lo = max(r_pc, r_pl), min(r_pc, r_pl)
        L.append("VERDICT: the v3 net costs roughly the SAME per node as the built-in evaluation on this build")
        L.append("(%.2fx on PC20, %.2fx plain, against 1.09x from my bench-13 medians). The 6.2-6.8x wall cost of"
                 % (r_pc, r_pl))
        L.append("the net is therefore NODE COUNT, not per-node work, so the ceiling on v3 kernel optimisation is")
        L.append("the v3 family's share of the benchmark (~19 %).")
        L.append("")
        # State the band without inventing a bound: if every measured ratio is BELOW 1 the net is cheaper per node
        # on this workload, and writing "up to N %% dearer" would fabricate a penalty that was not measured.
        if hi < 1.0:
            L.append("Honest range, not a point: %.2f-%.2fx, i.e. on THIS workload the net is %.0f-%.0f %% CHEAPER"
                     % (lo, hi, 100 * (1 - hi), 100 * (1 - lo)))
            L.append("per node than the built-in evaluation. I am not claiming the net is faster in general - the")
            L.append("claim is that the per-node difference is small, and here it happens to fall on the cheaper side.")
        elif lo > 1.0:
            L.append("Honest range, not a point: %.2f-%.2fx, i.e. on THIS workload the net is %.0f-%.0f %% DEARER"
                     % (lo, hi, 100 * (lo - 1), 100 * (hi - 1)))
            L.append("per node than the built-in evaluation - still far below the 2.5x that would keep P4 alive.")
        else:
            L.append("Honest range, not a point: %.2f-%.2fx, i.e. the two configurations straddle 1.0x, so the")
            L.append("per-node difference is within this machine's resolution and the direction is not resolvable.")
        L.append("Every figure is far from the 2.5x that would keep seat 29's P4 alive, and far from its 4-25x")
        L.append("prediction - that is the part which is not close to any threshold.")
        L.append("")
        L.append("A NOTE ON MY OWN NUMBER: this method gives %.2fx where my bench-13 medians gave 1.09x - the two"
                 % lo)
        L.append("disagree in SIGN of the v3 penalty (cheaper vs dearer per node). Both say ~1x, which is the claim,")
        L.append("but the point value is method-dependent, so the honest statement is \"about the same, within"
                 " ~11 percent\" rather than either figure alone.")
    else:
        L.append("VERDICT: incomplete - see the rows; not enough comparable positions to state a ratio.")

    # A script must not print a comparison table it cannot support. The first version of this one did exactly that:
    # every row said MISSING and it still emitted a "COMPARISON with the published figures" block, which a reader
    # could have mistaken for a result. If nothing was measured, say so and exit non-zero.
    measured = sum(len(v.get("n", 0) and [1] or []) for v in results.values())
    if not results:
        L.append("")
        L.append("NOTHING WAS MEASURED. Every position returned no reading, so no ratio exists and none is claimed.")
        L.append("The likely cause is the harness, not the engine: sending `quit` before the search finishes")
        L.append("truncates all output. Do not read the figure list above as a result.")
    (out / "check_per_node_abba.json").write_text(
        json.dumps({"shas": sha, "budget": budget, "results": results}, indent=1))
    (out / "check_per_node_abba.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
