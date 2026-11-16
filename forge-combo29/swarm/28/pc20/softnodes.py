#!/usr/bin/env python3
"""softnodes.py EXE OUTDIR — `go softnodes N` on the PC build under PC20, Threads 1.

FABLE_TO_swarm_6 item 4: "`go softnodes N` on the PC build under PC20, Threads 1: is it deterministic run
to run (it must be), does it stop at a finished depth, and how far past N does it go?"

Per search this records the full node count at every depth (so "stops at a finished depth" is checkable, not
assumed), the final node count, and the final depth. Then it repeats each N five times to test determinism.

N values: 2000 (the owner's self-play), 20000, 50000, 250000 (its matches).

Usage: softnodes.py EXE OUTDIR [NPOS] [REPS]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
NS = (2000, 20000, 50000, 250000)


def probe(exe, fen, n):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"go softnodes {n}")
    out, ok = eng.read_until("bestmove", 120)
    eng.close()
    if not ok:
        return {"best": "NORESP", "final_nodes": None, "final_depth": 0, "per_depth": [], "ok": False}
    per_depth = []   # (depth, nodes)
    best = ""
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            if "depth" in f and "nodes" in f:
                per_depth.append((int(f[f.index("depth") + 1]), int(f[f.index("nodes") + 1])))
    # collapse repeated lines per depth, keeping the max nodes seen for that depth
    seen = {}
    for d, nn in per_depth:
        seen[d] = max(seen.get(d, 0), nn)
    seq = sorted(seen.items())
    return {"best": best, "final_nodes": seq[-1][1] if seq else None,
            "final_depth": seq[-1][0] if seq else 0, "per_depth": seq, "ok": True}


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    npos = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens")], npos)
    print(f"PC20, Threads 1, Hash 16; {npos} positions x {reps} repeats per N")
    print()
    print("| N | position | final nodes | final/N | final depth | bestmove | stops at a depth "
          "boundary |")
    print("|---|---|---|---|---|---|---|")
    results = {}
    for n in NS:
        for pi, fen in enumerate(fens, 1):
            reps_out = []
            for _ in range(reps):
                reps_out.append(probe(exe, fen, n))
            finals = [r["final_nodes"] for r in reps_out if r["ok"]]
            moves = {r["best"] for r in reps_out}
            depths = {r["final_depth"] for r in reps_out}
            # "stops at a depth boundary": the final node count equals a depth's own reported count
            ok_runs = [r for r in reps_out if r["ok"]]
            at_boundary = all(r["final_nodes"] in {nn for _d, nn in r["per_depth"]} for r in ok_runs)
            det = (len(set(finals)) == 1) if finals else False
            print(f"| {n} | #{pi} | {finals[0] if finals else '-'} | "
                  f"{(finals[0]/n if finals else 0):.2f} | {sorted(depths)[0] if depths else '-'} | "
                  f"{sorted(moves)[0] if len(moves) == 1 else '/'.join(sorted(moves))} | "
                  f"{'yes' if at_boundary else 'no'} |")
            results[(n, pi)] = {"finals": finals, "moves": moves, "depths": depths, "det": det,
                                "at_boundary": at_boundary, "per_depth": ok_runs[0]["per_depth"]
                                if ok_runs else []}
        print()

    print("## Determinism and overshoot summary")
    print()
    print("| N | deterministic across repeats (all positions) | final/N min..max | final depth range |")
    print("|---|---|---|---|")
    for n in NS:
        dets = [results[(n, pi)]["det"] for pi in range(1, npos + 1)]
        ratios = [f / n for pi in range(1, npos + 1) for f in results[(n, pi)]["finals"]]
        depths = [d for pi in range(1, npos + 1) for d in results[(n, pi)]["depths"]]
        if ratios:
            print(f"| {n} | {'YES' if all(dets) else 'NO'} | {min(ratios):.2f}..{max(ratios):.2f} | "
                  f"{min(depths)}..{max(depths)} |")

    with open(os.path.join(outdir, "softnodes.tsv"), "w") as fh:
        fh.write("n\tposition\tfinal_nodes\tratio\tfinal_depth\tper_depth_ladder\tdeterministic\t"
                 "at_depth_boundary\n")
        for (n, pi), v in sorted(results.items()):
            ladder = " ".join(f"{d}:{nn}" for d, nn in v["per_depth"])
            fh.write(f"{n}\t{pi}\t{v['finals'][0] if v['finals'] else ''}\t"
                     f"{(v['finals'][0]/n if v['finals'] else 0):.4f}\t"
                     f"{sorted(v['depths'])[0] if v['depths'] else ''}\t{ladder}\t"
                     f"{v['det']}\t{v['at_boundary']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
