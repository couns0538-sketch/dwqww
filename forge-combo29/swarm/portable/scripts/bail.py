"""Drawn-root bail: identical behaviour across builds, as it must be.

The bail is not arithmetic -- it is `board.is_repetition()` on the searched
position's own count, so no compile flag can reach it. That makes "identical"
the PREDICTION, and a prediction that costs nothing to test should be tested.

Cases, all from forge-findings.md sections 1b and 2:
  T1  threefold via move list -> 0 nodes, cp 0, empty pv, bestmove = generator head
  T2  twofold via move list   -> searches normally (the trigger is THREE, not two)
  T3  the same board as a bare FEN -> searches normally (proves the FEN form
      cannot reach the bail at all, so a FEN-only harness would see nothing)
  T4  budget independence: go depth 8 / go nodes 50000 / go nodes 500000 all bail
  T5  pv is empty on the bail and non-empty on the control -- the reliable signal
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import paths
from harness import Engine, parse_info

BUILDS = {name: paths.engine_path(name) for name in ("native", "v2", "v3")}

# A legal knight shuttle from startpos: after 8 plies the startpos has occurred
# three times, which is the documented trigger.
THREEFOLD = "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
TWOFOLD = "position startpos moves g1f3 g8f6 f3g1 f6g8"
SAME_AS_FEN = "position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5"

# Section 2's sharpest case: a genuine threefold root where the side to move has
# mate in one. Ra8 is mate, so the twofold control must report it and the bail
# must forfeit it. The rook shuttles a1-b1 while Black's king alternates h8-g8.
MATE_THREEFOLD = ("position fen 6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1 "
                  "moves a1b1 g8h8 b1a1 h8g8 a1b1 g8h8 b1a1 h8g8")
# The same line two plies shorter: the searched position has occurred twice, so
# the trigger is not reached and the engine must still find the mate.
MATE_TWOFOLD = ("position fen 6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1 "
                "moves a1b1 g8h8 b1a1 h8g8")


def run(eng, cmd, limits):
    eng.send("ucinewgame")
    eng.isready()
    eng.send(cmd)
    text = eng.command(limits, timeout=300)
    info, best = parse_info(text)
    return {
        "bestmove": best,
        "nodes": info.get("nodes"),
        "score": info.get("score"),
        "score_kind": info.get("score_kind"),
        "pv": info.get("pv", []),
        "pv_len": len(info.get("pv", [])),
        "depth": info.get("depth"),
    }


def generator_head(eng, cmd):
    """Section 2's independent reference: the bail returns the head of the
    generated move list, which `go perft 1` prints first."""
    eng.send(cmd)
    text = eng.command("go perft 1", wait_for="nodes", timeout=120)
    for line in text.splitlines():
        if ": " in line and not line.startswith("nodes"):
            return line.split(":")[0].strip()
    return None


def main():
    out = {}
    for name, exe in BUILDS.items():
        eng = Engine(exe, hash_mb=16, threads=1, nnue=True, book=False)
        cases = {}
        cases["T1_threefold_depth8"] = run(eng, THREEFOLD, "go depth 8")
        cases["T1_head_reference"] = {"bestmove": generator_head(eng, THREEFOLD)}
        cases["T2_twofold_depth8"] = run(eng, TWOFOLD, "go depth 8")
        cases["T3_same_board_fen"] = run(eng, SAME_AS_FEN, "go depth 8")
        cases["T4_budget_depth"] = run(eng, THREEFOLD, "go depth 8")
        cases["T4_budget_nodes50k"] = run(eng, THREEFOLD, "go nodes 50000")
        cases["T4_budget_nodes500k"] = run(eng, THREEFOLD, "go nodes 500000")
        cases["T5_mate_threefold"] = run(eng, MATE_THREEFOLD, "go depth 8")
        cases["T5_mate_threefold_nodes"] = run(eng, MATE_THREEFOLD, "go nodes 50000")
        cases["T5_mate_twofold_CONTROL"] = run(eng, MATE_TWOFOLD, "go depth 8")
        eng.close()
        out[name] = cases

    fields = ("bestmove", "nodes", "score", "score_kind", "pv_len")
    print(f"{'case':24s} " + "  ".join(f"{b:>26s}" for b in BUILDS) + "   agree")
    print("-" * 110)
    all_agree = True
    for case in out["native"]:
        cells = []
        vals = []
        for b in BUILDS:
            r = out[b][case]
            if set(r) == {"bestmove"}:
                cells.append(f"{r['bestmove']:>26s}")
                vals.append(r["bestmove"])
            else:
                s = f"{r['bestmove']} n={r['nodes']} {r['score_kind']}={r['score']} pv={r['pv_len']}"
                cells.append(f"{s:>30s}")
                vals.append(json.dumps({k: r[k] for k in fields}))
        agree = len(set(vals)) == 1
        all_agree &= agree
        print(f"{case:24s} " + "  ".join(cells) + ("   YES" if agree else "   *** NO ***"))

    # the load-bearing comparison, stated explicitly
    n0 = out["native"]["T1_threefold_depth8"]
    print()
    print(f"bail on all three builds: nodes={n0['nodes']} score={n0['score']} "
          f"pv_len={n0['pv_len']} bestmove={n0['bestmove']}")
    print(f"generator head (independent reference): {out['native']['T1_head_reference']['bestmove']}")
    print(f"bail bestmove == generator head: "
          f"{n0['bestmove'] == out['native']['T1_head_reference']['bestmove']}")
    print(f"twofold control searched (nodes > 0): {out['native']['T2_twofold_depth8']['nodes'] > 0}")
    print(f"same board as FEN searched (nodes > 0): {out['native']['T3_same_board_fen']['nodes'] > 0}")
    print(f"budget independence: depth={out['native']['T4_budget_depth']['nodes']}, "
          f"nodes50k={out['native']['T4_budget_nodes50k']['nodes']}, "
          f"nodes500k={out['native']['T4_budget_nodes500k']['nodes']}")
    print(f"\nALL CASES IDENTICAL ACROSS THE THREE BUILDS: {all_agree}")
    json.dump(out, open(paths.out_path("bail.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
