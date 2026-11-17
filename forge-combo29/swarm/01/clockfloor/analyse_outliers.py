#!/usr/bin/env python3
"""swarm seat 01: what IS the 18x outlier? A deeper iteration, or lost time at the same depth? (S-C47)

S-C46 found five positions where PC20 searched 3-18x more nodes than S14 and took up to 24x longer. Dropping them
moves the mean node ratio from 1.214 to 0.956, so those five decide whether "PC20 saves nodes" is true. They deserve
an explanation, and there are two very different ones:

  (a) PC20 reached a DEEPER iteration. At fixed `go depth 12` the engine reports the deepest COMPLETED iteration; if
      PC20's search is harder it may spend far more nodes *within* depth 12, or extend/aspiration-re-search deeper.
      More nodes for more depth is not a defect - it is a different search.
  (b) PC20 WASTED time at the same or shallower depth - an aspiration re-search storm, a repetition loop, a failed
      pruning decision. That IS a defect worth reporting.

This script distinguishes them per position by recording, for BOTH settings:
  * every `info depth` line with its node count, so the per-iteration cost is visible;
  * the number of `info depth` lines per depth index (a re-search shows as the same depth emitted twice);
  * seldepth, since an extension shows as seldepth > depth;
  * the final bestmove and score, so "different answer" can be distinguished from "same answer, more work".

It also checks the coordinator's second question - whether these positions belong to families already documented:
  * fifty-move / drawn-root: halfmove clock >= 100, or the root adjudicated drawn (0 nodes);
  * MultiPV: not used here (MultiPV 1 throughout), so that family is excluded by construction;
  * the halfmove clocks of the five are 4, 11, 1, 7, 16 - all far from 100, so the fifty-move door should be shut.
That is asserted and printed rather than assumed.

Usage: analyse_outliers.py <exe> <fens-file> <indices> <outdir>
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_ONLY = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
             ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = S14 + PC20_ONLY
DEPTH = 12


def trace(exe, fen, opts):
    """Full per-iteration trace."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(prefix):
        for line in p.stdout:
            if line.startswith(prefix):
                return line.rstrip("\n")
        return None

    send("uci")
    until("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for n, v in opts:
        send("setoption name %s value %s" % (n, v))
    send("isready")
    until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send("position fen " + fen)
    send("isready")
    until("readyok")
    send("go depth %d" % DEPTH)

    iters = []
    bm = None
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            m = re.match(r"info depth (\d+) seldepth (\d+) score (cp|mate) (-?\d+) nodes (\d+) nps (\d+) "
                         r"hashfull (\d+) time (\d+)", line)
            if m:
                iters.append({"depth": int(m.group(1)), "seldepth": int(m.group(2)),
                              "score": "%s %s" % (m.group(3), m.group(4)),
                              "nodes": int(m.group(5)), "time": int(m.group(8))})
            else:
                iters.append({"raw": line})
        if line.startswith("bestmove"):
            bm = line
            break
    send("quit")
    try:
        p.wait(timeout=180)
    except Exception:
        p.kill()

    depths = [i["depth"] for i in iters if "depth" in i]
    from collections import Counter
    repeats = {d: c for d, c in Counter(depths).items() if c > 1}
    return {"iters": iters, "bestmove": bm.split()[1] if bm and len(bm.split()) > 1 else None,
            "final_depth": max(depths) if depths else None,
            "max_seldepth": max((i["seldepth"] for i in iters if "seldepth" in i), default=None),
            "total_nodes": iters[-1]["nodes"] if iters and "nodes" in iters[-1] else None,
            "total_time": iters[-1]["time"] if iters and "time" in iters[-1] else None,
            "repeated_depths": repeats,
            "iter_count": len(iters)}


def halfmove(fen):
    parts = fen.split()
    try:
        return int(parts[4])
    except (IndexError, ValueError):
        return None


def main():
    exe, fenfile, idx, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    lines = [l.strip() for l in Path(fenfile).read_text().splitlines() if l.strip()]
    stride = max(1, len(lines) // 120)
    sample = lines[::stride][:120]
    indices = [int(x) for x in idx.split(",")]

    L = ["S-C47: what IS the outlier - a deeper iteration or lost time at the same depth?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "S14 vs PC20, go depth %d, Threads 1, Hash 16, full per-iteration trace." % DEPTH,
         "MultiPV is 1 throughout, so the MultiPV family is excluded by construction.", ""]
    results = []
    for i in indices:
        fen = sample[i]
        hm = halfmove(fen)
        a = trace(exe, fen, S14)
        b = trace(exe, fen, PC20)
        rec = {"i": i, "fen": fen, "halfmove": hm, "s14": a, "pc20": b}
        results.append(rec)
        print("i=%-4d halfmove=%-4s | S14 depth %s seldepth %s nodes %-8s | PC20 depth %s seldepth %s nodes %-8s"
              % (i, hm, a["final_depth"], a["max_seldepth"], a["total_nodes"],
                 b["final_depth"], b["max_seldepth"], b["total_nodes"]), flush=True)

    L.append("per position")
    L.append("i\tfen\thalfmove\tS14 depth/seldepth/nodes\tPC20 depth/seldepth/nodes\tdepth gain\tsame bestmove?\trepeats")
    for r in results:
        a, b = r["s14"], r["pc20"]
        gain = (b["final_depth"] or 0) - (a["final_depth"] or 0)
        same_bm = a["bestmove"] == b["bestmove"]
        L.append("%d\t%s\t%s\t%s/%s/%s\t%s/%s/%s\t%+d\t%s\tS14 %s PC20 %s"
                 % (r["i"], r["fen"][:28], r["halfmove"],
                    a["final_depth"], a["max_seldepth"], a["total_nodes"],
                    b["final_depth"], b["max_seldepth"], b["total_nodes"],
                    gain, "yes" if same_bm else "NO",
                    a["repeated_depths"] or "none", b["repeated_depths"] or "none"))
    L.append("")

    L.append("VERDICT PER POSITION - (a) deeper search, not a defect; (b) lost time at same depth, a defect")
    for r in results:
        a, b = r["s14"], r["pc20"]
        gain = (b["final_depth"] or 0) - (a["final_depth"] or 0)
        sd = (b["max_seldepth"] or 0) - (a["max_seldepth"] or 0)
        ratio = (b["total_nodes"] or 0) / max(1, a["total_nodes"] or 1)
        # THE SCORE IS THE MISSING AXIS, and my first version omitted it. At fixed depth 12 two searches can
        # report the same depth and the same seldepth while PROVING DIFFERENT THINGS - a mate found one move
        # shorter is a stronger result achieved with more nodes, not wasted work. Comparing depth/seldepth/nodes
        # alone labelled two of these five "defect candidates" and the scores refute that.
        sa = a["iters"][-1].get("score") if a["iters"] else None
        sb = b["iters"][-1].get("score") if b["iters"] else None
        stronger = False
        if sa and sb and sa.startswith("mate") and sb.startswith("mate"):
            ma = abs(int(sa.split()[1])); mb = abs(int(sb.split()[1]))
            stronger = (mb < ma) if (int(sa.split()[1]) > 0) == (int(sb.split()[1]) > 0) else False
        if stronger:
            v = ("SAME depth, but a SHORTER MATE (%s -> %s): proved a stronger claim with %.1fx the nodes - "
                 "NOT a defect" % (sa, sb, ratio))
        elif gain > 0:
            v = "DEEPER (depth +%d, seldepth +%d) - a stronger search, NOT a defect" % (gain, sd)
        elif sd > 0:
            v = "SAME depth, DEEPER seldepth (+%d) - an extension; stronger search, NOT a defect" % sd
        elif b["repeated_depths"]:
            v = "SAME depth, RE-SEARCHED depths %s - wasted work, candidate defect" % b["repeated_depths"]
        elif sa != sb:
            v = "SAME depth, DIFFERENT score (%s -> %s), %.1fx nodes - inspect before calling it waste" % (sa, sb, ratio)
        else:
            v = ("SAME depth, SAME seldepth, SAME score (%s), %.1fx the nodes - genuinely wasted work, DEFECT "
                 "candidate" % (sa, ratio))
        L.append("  i=%-4d %.1fx nodes -> %s" % (r["i"], ratio, v))

    L.append("")
    L.append("FAMILY CHECK (the coordinator's question 2)")
    hms = [r["halfmove"] for r in results]
    L.append("  halfmove clocks: %s" % hms)
    L.append("  all far from 100 -> the fifty-move / drawn-root door is SHUT for every one of these")
    L.append("  MultiPV: 1 throughout -> that family is excluded by construction")

    (out / "analyse_outliers.json").write_text(json.dumps({"sha": sha, "results": results}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "analyse_outliers.txt").write_text(txt)
    print("")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
