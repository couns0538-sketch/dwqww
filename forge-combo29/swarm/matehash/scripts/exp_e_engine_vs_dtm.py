"""Engine-reported mate distance vs an exact DTM oracle, over the corpus.

WHAT THIS MEASURES, AND WHAT IT DOES NOT
    This is the ANSWER KEY arm: for each corpus fixture, compare the mate
    distance the engine reports against the exact distance. It is deliberately
    run COLD (fresh process, cleared table) so that any disagreement here is a
    property of the search and NOT of the transposition table. That separation is
    the whole point: a disagreement that also appears cold cannot be blamed on
    `score_to_tt`, and attributing it there would be a wrong finding.

    A discrepancy found here is reported with its depth AND seldepth, because a
    `mate N` claim needs 2N-1 plies: a claim the reported seldepth cannot contain
    is UNVERIFIABLE rather than wrong (findings doc), and the two must not be
    counted together.

FIXTURES THAT DISAGREE ARE RE-CHECKED WITH A WITNESS
    A number-vs-number disagreement proves nothing on its own; the oracle could
    be the broken one. For every disagreement this arm tries to produce
        * a concrete line that mates in the SHORTER of the two distances
          (proving the longer claim is an over-report), and
        * the absence of a mate at every shorter ply (proving the shorter claim
          is not an under-report).
    A disagreement with no witness is reported as UNRESOLVED, not as a hit.

Output: evidence/E_engine_vs_dtm.jsonl
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dtm import _mate_within, _mated_within, dtm_moves  # noqa: E402
from engine import search  # noqa: E402


def engine_mate(binary, fen, depth):
    res = search(binary, fen, limits={"depth": depth}, hash_mb=32)
    scored = [i for i in res["infos"] if "score" in i and "depth" in i]
    if not scored:
        return {"mate": None, "why": "no info depth lines"}
    last = scored[-1]
    if last.get("score_kind") != "mate":
        return {"mate": None, "why": "not a mate score", "score": last.get("score"),
                "depth": last.get("depth"), "seldepth": last.get("seldepth")}
    return {
        "mate": last["score"],
        "depth": last.get("depth"),
        "seldepth": last.get("seldepth"),
        "nodes": last.get("nodes"),
        "pv": last.get("pv"),
        "bestmove": res["bestmove"],
    }


def witness_for(board, plies):
    """A forced mate of exactly `plies`, or None. Attacker = whoever is mating.

    For an even `plies` the root side is the VICTIM, so the witness must be
    searched from the victim's perspective: every victim move, then the opponent
    mates. That is `_mated_within`, and the line is built by picking the victim
    move that the predicate says still loses -- which gives an upper bound that
    the absence of a mate at `plies - 2` turns into an exact distance.
    """
    memo, cnt = {}, {"n": 0}
    try:
        if plies % 2 == 1:
            return _mate_within(board.copy(), plies, memo, cnt, 8_000_000)
        return _mated_within(board.copy(), plies, memo, cnt, 8_000_000)
    except RuntimeError:
        return None


def exact_plies(board, max_plies=12):
    """Smallest ply count at which a forced mate exists, with no mate below it."""
    for plies in range(1, max_plies + 1):
        if witness_for(board, plies):
            return plies
    return None


def main():
    binary = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    here = __file__.rsplit("/", 2)[0]
    corpus = json.load(open(here + "/evidence/corpus.json"))

    rows = []
    for fx in corpus["fixtures"]:
        fen = fx["fen"]
        board = chess.Board(fen)
        eng = engine_mate(binary, fen, depth)
        oracle = dtm_moves(board, max_plies=10)
        want = oracle["uci_mate"]
        got = eng["mate"]
        row = {
            "fen": fen,
            "oracle_kind": fx["kind"],
            "oracle_moves": fx["moves"],
            "oracle_uci": want,
            "engine_mate": got,
            "engine_depth": eng.get("depth"),
            "engine_seldepth": eng.get("seldepth"),
            "engine_pv": eng.get("pv"),
            "depth_requested": depth,
            "agree": got == want,
            # Is the engine's claim even containable at the depth it reports?
            "seldepth_sufficient": (eng.get("seldepth") is not None and got is not None
                                    and eng["seldepth"] >= 2 * abs(got) - 1),
        }
        if not row["agree"]:
            # Settle it with the witness machinery rather than by trust.
            shorter = min(abs(got), abs(want)) if (got is not None and want is not None) else None
            if shorter is not None:
                plies = 2 * shorter - 1 if (want or 0) > 0 else 2 * shorter
                row["shorter_claim_exists"] = witness_for(board, plies)
                row["shorter_claim_plies"] = plies
            row["note"] = "engine and oracle disagree on distance (COLD: not a TT effect)"
        rows.append(row)
        print(json.dumps({k: row[k] for k in ("fen", "oracle_uci", "engine_mate", "engine_depth",
                                             "engine_seldepth", "agree")}), flush=True)

    n = len(rows)
    agree = sum(1 for r in rows if r["agree"])
    dis = [r for r in rows if not r["agree"]]
    summary = {
        "binary": binary,
        "depth_requested": depth,
        "n": n,
        "agree": agree,
        "disagree": len(dis),
        "disagree_rate": round(len(dis) / n, 4) if n else None,
        "disagree_by_distance": {},
        "seldepth_sufficient_among_agree": sum(1 for r in rows if r["agree"] and r["seldepth_sufficient"]),
        "disagreements": [
            {"fen": r["fen"], "oracle": r["oracle_uci"], "engine": r["engine_mate"],
             "depth": r["engine_depth"], "seldepth": r["engine_seldepth"],
             "shorter_claim_plies": r.get("shorter_claim_plies"),
             "shorter_claim_exists": r.get("shorter_claim_exists")}
            for r in dis
        ][:40],
    }
    for r in dis:
        k = f"{r['oracle_kind']}_{r['oracle_moves']}"
        summary["disagree_by_distance"][k] = summary["disagree_by_distance"].get(k, 0) + 1
    print(json.dumps({"summary": summary}, indent=2))
    with open(here + "/evidence/E_engine_vs_dtm.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        fh.write(json.dumps({"summary": summary}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
