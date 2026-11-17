#!/usr/bin/env python3
"""softnodes_probe.py <exe> <outdir> [--settings PC20] [--label NAME]

The new area FABLE_TO_swarm_6 suggests: `go softnodes N` on the PC build under PC20 at Threads 1.

Its self-play uses this: "the search stops at the end of the first depth after 2,000 nodes". So the three
questions that matter for the owner:
  1. DETERMINISM: same position, same N, repeated fresh processes -> identical node count, score and move?
     (It must be deterministic; if it is not, its self-play labels are not reproducible.)
  2. Does it stop at a FINISHED depth? The engine's own contract (search.cpp) is that the soft budget is
     the finished-iteration target and the hard budget is 4x; so the reply should come from a COMPLETED
     iteration, never a partial one.
  3. How far PAST N does it go? Node count at stop / N, across several N and several depths.
Also records whether the reported `info depth` corresponds to a complete iteration (the pv must be non-empty
and the depth must equal the last announced depth).

Threads 1, Hash 16, PC20, fresh process per search, `go` awaited to bestmove.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]

# positions from real games (O and G are game sets; these are two middlegame FENs from O/G families)
POSITIONS = [
    ("O-mid1", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("O-mid2", "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4"),
    ("G-mid",  "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
    ("tactic", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
]
BUDGETS = [2000, 20000]


class Missing(Exception):
    pass


def search(exe, settings, fen, limit, timeout=600):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(limit)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not ok:
            raise Missing("no bestmove for %r %r" % (fen, limit))
        infos = [l for l in lines if l.startswith("info depth")]
        # GUARD (S-W1): zero info lines means no score, no nodes, no nps. Abort rather than record.
        if not infos:
            raise Missing("no 'info depth' line for this search (zero-info-line signature; row aborted)")
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        soft = [l for l in lines if "info string softnodes" in l]
        # the softnodes report carries the FINAL node count; prefer it, else the last info line
        final_nodes = None
        if soft:
            m = re.search(r"softnodes nodes (\d+)", soft[-1])
            if m:
                final_nodes = int(m.group(1))
        last = infos[-1] if infos else ""
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        d = re.search(r"depth (\d+)", last)
        pv = re.search(r"\bpv\b", last)
        return {"limit": limit, "fen": fen, "bestmove": bm,
                "last_info": last,
                "info_depth": int(d.group(1)) if d else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "nodes_last_info": int(n.group(1)) if n else None,
                "nodes_softnodes_line": final_nodes,
                "has_pv": pv is not None,
                "n_info": len(infos),
                "softnodes_line": soft[-1] if soft else ""}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--label", default="run")
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "label": a.label,
           "reps": a.reps,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "results": []}

    for name, fen in POSITIONS:
        for n in BUDGETS:
            reps = [search(exe, settings, fen, "go softnodes %d" % n) for _ in range(a.reps)]
            keys = {(r["bestmove"], r["score"], r["nodes_softnodes_line"] or r["nodes_last_info"])
                    for r in reps}
            nodes_final = reps[0]["nodes_softnodes_line"] or reps[0]["nodes_last_info"]
            row = {"position": name, "fen": fen, "N": n, "reps": reps,
                   "deterministic": len(keys) == 1,
                   "nodes_final": nodes_final,
                   "overshoot_ratio": round(nodes_final / n, 2) if nodes_final else None,
                   "finished_depth": all(r["has_pv"] for r in reps),
                   "last_depth": reps[0]["info_depth"],
                   "score": reps[0]["score"], "bestmove": reps[0]["bestmove"]}
            out["results"].append(row)
            print("%-8s N=%-6d det=%-5s depth=%-3s nodes=%-8s (%.2fx N) pv=%-5s score %s %s bm %s"
                  % (name, n, row["deterministic"], row["last_depth"], row["nodes_final"],
                     row["overshoot_ratio"] or 0, row["finished_depth"],
                     row["score"][0] if row["score"] else "-",
                     row["score"][1] if row["score"] else "-", row["bestmove"]))

    with open(os.path.join(a.outdir, "softnodes_%s_%s.json" % (a.label, a.settings)), "w") as f:
        json.dump(out, f, indent=2)

    nd = sum(1 for r in out["results"] if not r["deterministic"])
    ratios = [r["overshoot_ratio"] for r in out["results"] if r["overshoot_ratio"]]
    print("\nnon-deterministic cells: %d of %d" % (nd, len(out["results"])))
    if ratios:
        print("overshoot ratio (final nodes / N): min %.2f, max %.2f, median %.2f"
              % (min(ratios), max(ratios), sorted(ratios)[len(ratios) // 2]))
    print("all replies carried a pv (a finished iteration): %s"
          % all(r["finished_depth"] for r in out["results"]))
    print("wrote", os.path.join(a.outdir, "softnodes_%s_%s.json" % (a.label, a.settings)))


if __name__ == "__main__":
    main()
