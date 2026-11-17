"""Are the mate claims TRUE, and are they VERIFIABLE from the wire?

A first pass flagged 8 rows as "false mates" because the PV did not end in
checkmate. That was wrong, and the reason matters: in every one of those rows the
PV was SHORTER than the distance the score claimed (`mate 8` = 15 plies against an
11-ply PV). A truncated PV cannot disprove a mate claim, so the honest verdict for
those rows is UNVERIFIABLE, not FALSE. This script separates the three cases.

For each mate claim it records:
  * claimed_plies  = 2N-1 for `mate N`
  * pv_len         = how many plies the engine actually printed
  * pv_reaches     = pv_len >= claimed_plies  (was the claim even testable?)
  * pv_ends_in_mate / pv_plies  = the played-out result, when testable
  * mate_exists_within_claim    = an independent AND/OR proof that a forced mate
                                  inside `claimed_plies` really exists, so the
                                  CLAIM itself (not the line) is checked even when
                                  the PV is too short to show it.

Verdicts:
  FALSE        the PV is long enough to reach the claim and does not mate
  LOOSE        a mate exists but the engine's distance is longer than the true DTM
  TRUE_TIGHT   the claim matches an independently proved DTM
  UNVERIFIABLE PV too short and no independent bound (should not happen here)
"""
import json
import pathlib
import sys

import chess

sys.path.insert(0, str(pathlib.Path(__file__).parent))

EVIDENCE = pathlib.Path("/tmp/asp/evidence")


def mate_within(bd, plies, memo):
    """Independent proof: can the side to move force mate within `plies`?"""
    if plies <= 0:
        return False
    key = (bd.board_fen(), bd.turn, bd.castling_xfen() or "-", bd.ep_square, plies)
    if key in memo:
        return memo[key]
    res = False
    for mv in bd.legal_moves:
        bd.push(mv)
        if bd.is_checkmate():
            bd.pop()
            res = True
            break
        if plies >= 3 and any(bd.legal_moves):
            all_mate = True
            for reply in list(bd.legal_moves):
                bd.push(reply)
                if bd.is_checkmate():
                    bd.pop()
                    all_mate = False
                    break
                if not mate_within(bd, plies - 2, memo):
                    bd.pop()
                    all_mate = False
                    break
                bd.pop()
            if all_mate:
                bd.pop()
                res = True
                break
        bd.pop()
    memo[key] = res
    return res


def true_dtm(fen, limit=15):
    bd = chess.Board(fen)
    memo = {}
    for p in range(1, limit + 1):
        if mate_within(bd, p, memo):
            return p
    return None


def play(fen, pv):
    board = chess.Board(fen)
    for i, uci in enumerate(pv):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return False, None
        if move not in board.legal_moves:
            return False, None
        board.push(move)
        if board.is_checkmate():
            return True, i + 1
        if board.is_stalemate() or board.is_insufficient_material():
            return False, None
    return False, None


def main():
    scans = [EVIDENCE / "false_mate_scan.json", EVIDENCE / "mate_windows.json"]
    dtm_cache = {}
    rows = []

    scan = json.loads((EVIDENCE / "false_mate_scan.json").read_text())
    for fx in scan["fixtures"]:
        fen = fx["fen"]
        if fen not in dtm_cache:
            dtm_cache[fen] = true_dtm(fen)
        for arm, recs in fx["arms"].items():
            for r in recs:
                if r["score_kind"] != "mate" or r["score"] < 0:
                    continue
                claimed = 2 * r["score"] - 1
                pv = r["pv"]
                ends, plies = play(fen, pv)
                rows.append({
                    "source": "false_mate_scan", "label": fx["label"], "arm": arm,
                    "depth": r["depth"], "fen": fen,
                    "claimed_plies": claimed, "pv_len": len(pv), "pv": pv,
                    "pv_reaches_claim": len(pv) >= claimed,
                    "pv_ends_in_mate": ends, "pv_mate_plies": plies,
                    "true_dtm_plies": dtm_cache[fen],
                })

    mates = json.loads((EVIDENCE / "mate_windows.json").read_text())
    for row in mates["rows"]:
        if row["fen"] not in dtm_cache:
            dtm_cache[row["fen"]] = true_dtm(row["fen"])
        for arm, a in row["arms"].items():
            if a.get("score_kind") != "mate":
                continue
            claimed = 2 * a["score"] - 1
            pv = a.get("pv") or []
            ends, plies = play(row["fen"], pv)
            rows.append({
                "source": "mate_windows", "label": row["label"], "arm": arm,
                "depth": a["depth"], "fen": row["fen"],
                "claimed_plies": claimed, "pv_len": len(pv), "pv": pv,
                "pv_reaches_claim": len(pv) >= claimed,
                "pv_ends_in_mate": ends, "pv_mate_plies": plies,
                "true_dtm_plies": dtm_cache[row["fen"]],
            })

    for r in rows:
        dtm = r["true_dtm_plies"]
        if r["pv_reaches_claim"] and not r["pv_ends_in_mate"]:
            r["verdict"] = "FALSE"
        elif dtm is None:
            r["verdict"] = "MATE_NOT_FOUND_IN_PROOF"
        elif r["claimed_plies"] == dtm:
            r["verdict"] = "TRUE_TIGHT"
        elif r["claimed_plies"] > dtm:
            r["verdict"] = "LOOSE"
        else:
            r["verdict"] = "UNVERIFIABLE_SHORT_PV"

    from collections import Counter
    counts = Counter(r["verdict"] for r in rows)
    print("=== verdicts over every positive mate claim in the corpus ===")
    for k, v in sorted(counts.items()):
        print(f"  {k:26s} {v}")
    print(f"  {'total':26s} {len(rows)}")
    print()
    testable = [r for r in rows if r["pv_reaches_claim"]]
    print(f"claims whose PV is long enough to test: {len(testable)}")
    print(f"  of those, PV ends in mate: {sum(r['pv_ends_in_mate'] for r in testable)}")
    print(f"  of those, FALSE:           {sum(r['verdict'] == 'FALSE' for r in testable)}")
    print()
    print("=== every claim that is FALSE or LOOSE ===")
    for r in rows:
        if r["verdict"] in ("FALSE", "LOOSE"):
            print(f"  {r['label']:16s} {r['arm']:12s} d{r['depth']:<2} "
                  f"claimed={r['claimed_plies']}pl pv_len={r['pv_len']} "
                  f"true_dtm={r['true_dtm_plies']}pl  {r['verdict']}")
    (EVIDENCE / "mate_claim_verdicts.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
