"""Is a false mate caused BY aspiration, or is it independent of it?

Two KQK rows publish `score mate N` whose PV does not end in mate at all
(measured: `mate 8` with an 11-ply PV that ends in a quiet position, and
`mate 17`). That is a soundness problem wherever it comes from; the question for
this audit is whether aspiration is what causes it.

Method: for each KQK fixture and every depth 1..max, run BOTH arms (aspiration
on with the default delta, aspiration never narrowing), play each published PV
out with python-chess, and record whether the line mates and whether it mates in
the claimed number of plies. A false mate that appears on BOTH arms is not an
aspiration defect. One that appears only with aspiration on is.
"""
import json
import pathlib
import sys

import chess

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from uci import Engine  # noqa: E402

EVIDENCE = pathlib.Path("/tmp/asp/evidence")
BASE = {"OwnBook": "false"}

FIXTURES = [
    ("KQK-dtm7-a", "8/8/8/5KQ1/8/5k2/8/8 w - - 0 1", 7),
    ("KQK-dtm7-b", "8/8/8/3K4/6Q1/8/8/4k3 w - - 0 1", 7),
    ("KQK-dtm5-a", "6Q1/8/8/k7/8/2K5/8/8 w - - 0 1", 5),
    ("KQK-dtm5-b", "8/3K4/8/k7/8/8/8/2Q5 w - - 0 1", 5),
    ("KQK-dtm3-a", "8/8/8/8/7Q/5K2/8/6k1 w - - 0 1", 3),
    ("KQK-dtm3-b", "8/Q7/7k/4K3/8/8/8/8 w - - 0 1", 3),
]

ARMS = {
    "asp_on": ("/tmp/asp/build-stock/forge", {}),
    "asp_off": ("/tmp/asp/build-noasp/forge", {}),
    "capped": ("/tmp/asp/build-stock/forge", {"AspCappedReopen": "true"}),
    "arm_late": ("/tmp/asp/build-stock/forge", {"AspArmLate": "true"}),
}


def check_pv(fen, pv):
    """Play a PV out. Returns (legal, ends_in_mate, plies_to_mate)."""
    board = chess.Board(fen)
    for i, uci in enumerate(pv):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return False, False, None
        if move not in board.legal_moves:
            return False, False, None
        board.push(move)
        if board.is_checkmate():
            return True, True, i + 1
        if board.is_stalemate() or board.is_insufficient_material():
            return True, False, None
    return True, False, None


def main():
    max_depth = 14
    out = {"fixtures": [], "max_depth": max_depth}
    totals = {a: {"mate_claims": 0, "false": 0, "distance_wrong": 0}
              for a in ARMS}

    for label, fen, dtm in FIXTURES:
        fx = {"label": label, "fen": fen, "dtm_plies": dtm, "arms": {}}
        for arm, (build, opts) in ARMS.items():
            merged = dict(BASE)
            merged.update(opts)
            rows = []
            with Engine(build, merged) as eng:
                eng.newgame()
                eng.position(fen)
                for depth in range(1, max_depth + 1):
                    res = eng.search(f"go depth {depth}")
                    per_depth = {r["depth"]: r for r in res["info"]
                                 if r["depth"] is not None}
                    if depth not in per_depth:
                        continue
                    r = per_depth[depth]
                    rec = {"depth": depth, "score_kind": r["score_kind"],
                           "score": r["score"], "seldepth": r["seldepth"],
                           "pv": r["pv"]}
                    if r["is_mate"]:
                        claimed = 2 * r["score"] - 1 if r["score"] > 0 else None
                        legal, ends, plies = check_pv(fen, r["pv"])
                        rec.update({"claimed_plies": claimed, "pv_legal": legal,
                                    "pv_ends_in_mate": ends, "actual_plies": plies,
                                    "false_mate": (claimed is not None and not ends),
                                    "distance_wrong": (ends and plies != claimed)})
                        totals[arm]["mate_claims"] += 1
                        if claimed is not None and not ends:
                            totals[arm]["false"] += 1
                        if ends and plies != claimed:
                            totals[arm]["distance_wrong"] += 1
                    rows.append(rec)
            fx["arms"][arm] = rows
        out["fixtures"].append(fx)
        print(f"{label:12s} " + "  ".join(
            f"{arm}: {sum(1 for r in fx['arms'][arm] if r.get('false_mate'))} false"
            for arm in ARMS))

    out["totals"] = totals
    (EVIDENCE / "false_mate_scan.json").write_text(json.dumps(out, indent=2) + "\n")

    print("\n=== totals across 6 KQK fixtures, depths 1..14 ===")
    for arm, t in totals.items():
        print(f"  {arm:10s} mate_claims={t['mate_claims']:>3}  "
              f"FALSE (PV never mates)={t['false']:>3}  "
              f"wrong distance={t['distance_wrong']:>3}")

    print("\n=== every false mate ===")
    any_false = False
    for fx in out["fixtures"]:
        for arm, rows in fx["arms"].items():
            for r in rows:
                if r.get("false_mate"):
                    any_false = True
                    print(f"  {fx['label']:12s} {arm:10s} d{r['depth']:<2} "
                          f"claimed mate {r['score']} ({r['claimed_plies']} pl) "
                          f"pv_len={len(r['pv'])} pv={' '.join(r['pv'])}")
    if not any_false:
        print("  none")


if __name__ == "__main__":
    main()
