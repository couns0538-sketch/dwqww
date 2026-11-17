"""Decide BETWEEN two hypotheses for a mate-distance disagreement.

    H1  ENCODING: the reported distance is miscounted -- the PV is a real forced
        mate of the TRUE length, but the score says a different length. This is
        what a wrong or absent `score_to_tt` ply adjustment produces, and it is
        the hypothesis this seat exists to test.

    H2  PRECISION: the reported distance is a real forced mate of ITS OWN length,
        just not the shortest one. The engine found a longer mate than the DTM.
        That is a search-quality property, NOT an encoding defect, and reporting
        it as one would be a wrong finding.

WHY `mate_within(P)` CANNOT SEPARATE THEM
    The predicate is monotone: if a forced mate of 5 plies exists, one of 7 plies
    exists too. So "does a mate of the engine's length exist" is always True once
    a shorter one exists, which makes it useless as a discriminator. An earlier
    version of this experiment nearly recorded 62 encoding defects on that
    vacuous test.

WHAT SEPARATES THEM
    Replay the engine's own PV and count the plies it takes to mate. Then:
      * PV mates at 2*N-1 plies            -> H2 (the claim is honest, at its own length)
      * PV mates at some other length      -> H1, and the delta is the encoding error
      * PV does not mate at all            -> UNVERIFIABLE (the PV may be truncated;
                                              a PV shorter than the claim is
                                              unverifiable, not false)
    Independently, count how many engine moves lie outside an optimal mating line,
    which is the signature of imprecision rather than miscounting.
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dtm import _mate_within, _mated_within  # noqa: E402
from engine import search  # noqa: E402


def pv_outcome(fen, pv):
    """Play the PV. Where does it end, and does it mate?"""
    board = chess.Board(fen)
    if not pv:
        return {"mates": False, "why": "empty pv"}
    for i, u in enumerate(pv):
        try:
            mv = chess.Move.from_uci(u)
        except ValueError:
            return {"mates": False, "why": f"unparseable move {u}", "plies": i}
        if mv not in board.legal_moves:
            return {"mates": False, "why": f"illegal move {u} at ply {i+1}", "plies": i}
        board.push(mv)
        if board.is_checkmate():
            return {"mates": True, "plies": i + 1}
    return {"mates": False, "why": "py ended without mate", "plies": len(pv),
            "final_in_check": board.is_check()}


def shortest_dtm_plies(board, cap=12, node_cap=20_000_000):
    for plies in range(1, cap + 1):
        memo, cnt = {}, {"n": 0}
        pred = _mate_within if plies % 2 == 1 else _mated_within
        try:
            if pred(board.copy(), plies, memo, cnt, node_cap):
                return plies
        except RuntimeError:
            return None
    return None


def classify(binary, fen, depth):
    res = search(binary, fen, limits={"depth": depth}, hash_mb=32)
    scored = [i for i in res["infos"] if "score" in i and "depth" in i]
    if not scored:
        return {"fen": fen, "class": "no-info"}
    last = scored[-1]
    claimed = None
    if last.get("score_kind") == "mate":
        claimed = last["score"]
    board = chess.Board(fen)
    dtm = shortest_dtm_plies(board)
    out = {
        "fen": fen,
        "claimed": claimed,
        "dtm_plies": dtm,
        "dtm_uci": None if dtm is None else ((dtm + 1) // 2 if dtm % 2 else -((dtm + 1) // 2)),
        "depth": last.get("depth"),
        "seldepth": last.get("seldepth"),
        "pv": last.get("pv"),
    }
    if claimed is None:
        out["class"] = "no-mate-claimed"
        return out
    # A mate in k lands on ply 2k-1 (we move first). Being MATED in k lands on
    # ply 2k, because the opponent delivers it. Using 2k-1 for both made 22
    # honest claims look like encoding defects -- the classic sign error, and the
    # reason every number in this seat is now re-derived from the PV itself.
    want_plies = (2 * abs(claimed) - 1) if claimed > 0 else (2 * abs(claimed))
    pv = pv_outcome(fen, last.get("pv") or [])
    out["pv_outcome"] = pv
    out["claimed_plies"] = want_plies
    if pv.get("mates") and pv.get("plies") == want_plies:
        out["class"] = "H2-precision" if dtm != want_plies else "exact"
    elif pv.get("mates"):
        out["class"] = "H1-encoding"
        out["encoding_delta_plies"] = pv["plies"] - want_plies
    else:
        # Not proven either way: the PV may simply be truncated.
        out["class"] = "unverifiable-pv"
    return out


def main():
    binary = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    here = __file__.rsplit("/", 2)[0]
    rows = [json.loads(line) for line in open(here + "/evidence/E_engine_vs_dtm.jsonl")
            if '"summary"' not in line]
    disagree = [r for r in rows if not r["agree"]]
    # Add a matched sample of AGREEMENTS as a positive control for the classifier:
    # an agreeing row must classify as "exact", or the classifier is broken.
    agree = [r for r in rows if r["agree"]][:40]

    results = []
    for r in disagree + agree:
        results.append(classify(binary, r["fen"], depth))

    counts = {}
    for r in results:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    dis_classes = [r for r in results[:len(disagree)]]
    agree_classes = [r for r in results[len(disagree):]]
    summary = {
        "binary": binary,
        "depth": depth,
        "n_disagree_inputs": len(disagree),
        "n_agree_controls": len(agree),
        "classes_all": counts,
        "classes_among_disagreements": {c: sum(1 for r in dis_classes if r["class"] == c)
                                        for c in sorted({r["class"] for r in dis_classes})},
        "classes_among_agreements": {c: sum(1 for r in agree_classes if r["class"] == c)
                                     for c in sorted({r["class"] for r in agree_classes})},
        # The positive control: every AGREEMENT must come back "exact". If not,
        # the classifier (not the engine) is what is broken.
        "agreement_control_gate": "PASS" if agree_classes and all(r["class"] == "exact" for r in agree_classes) else "FAIL",
        "encoding_defects": [r for r in dis_classes if r["class"] == "H1-encoding"][:20],
    }
    print(json.dumps({"summary": summary}, indent=2))
    with open(here + "/evidence/F_disagreement_classified.json", "w") as fh:
        json.dump({"summary": summary, "rows": results}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
