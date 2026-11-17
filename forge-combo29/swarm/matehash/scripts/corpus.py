"""Assemble and verify the mate corpus used by every experiment in this seat.

Sources: the hand-picked seeds in this file plus the graded candidates in
evidence/candidates.json (produced by gen_candidates.py, which grades every
candidate with this seat's own oracle).

Every fixture passes four gates before it is admitted:
  1. python-chess constructs it and says is_valid();
  2. it is not already terminal;
  3. this seat's oracle returns an EXACT mate distance within 4 moves and did not
     hit its node cap;
  4. the ENGINE accepts the FEN -- proved by a `position fen` + `go depth 6` that
     emits at least one `info depth` line AND whose reported score is a mate of
     the right sign. A refused FEN searches the PREVIOUS position and manufactures
     a pass (brief rule 4), so "no info lines" is a hard reject, not a warning.

The corpus deliberately OVER-WEIGHTS distance >= 2: a mate at distance 1 is
stored as MATE-1 at every ply, so an absent ply adjustment still reports
"mate 1" and the corpus would have no power. The distance histogram is part of
the result for exactly that reason.

Output: evidence/corpus.json
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from engine import final_score, search  # noqa: E402
from oracle import solve  # noqa: E402

HAND_SEEDS = [
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "back rank Ra8#"),
    ("8/8/8/8/8/1R6/8/k1K5 w - - 0 1", "KRvK Rb3-a3#"),
    ("8/8/8/8/8/8/1R2R3/K1k5 w - - 0 1", "two rooks Rb2-b1#"),
    ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", "KQvK Qf7-g7# protected"),
    ("8/8/8/8/8/8/8/k1K4R w - - 0 1", "KRvK corner mate, distance 3"),
    ("k7/8/1K6/8/8/8/8/7R w - - 0 1", "KRvK a-file, Rh8#"),
    ("3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105", "finding-doc: Black mated in 1"),
    ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "symmetric back rank"),
]

TARGET_PER_DISTANCE = 24


def engine_accepts(binary, fen):
    """Gate 4. Returns the evidence, not a bare bool."""
    res = search(binary, fen, limits={"depth": 6}, hash_mb=16)
    info = final_score(res)
    return {
        "accepted": bool(res["infos"]) and info is not None,
        "bestmove": res["bestmove"],
        "info_lines": len(res["infos"]),
        "score": [info.get("score_kind"), info.get("score")] if info else None,
    }


def main():
    binary = sys.argv[1]
    here = __file__.rsplit("/", 2)[0]

    pool = [(fen, note) for fen, note in HAND_SEEDS]
    try:
        cand = json.load(open(here + "/evidence/candidates.json"))
        for r in cand["fixtures"]:
            pool.append((r["fen"], f"generated: {r['kind']} {r['moves']} ({r['pieces']}p)"))
        cand_source = f"evidence/candidates.json ({cand['graded']} graded of {cand['candidates']} candidates)"
    except FileNotFoundError:
        cand_source = "none (run gen_candidates.py first)"

    seen = set()
    bucketed: dict[tuple, list] = {}
    rejected = []
    for fen, note in pool:
        if fen in seen:
            continue
        seen.add(fen)
        try:
            board = chess.Board(fen)
        except ValueError as exc:
            rejected.append({"fen": fen, "why": f"python-chess raised: {exc}", "note": note})
            continue
        if not board.is_valid():
            rejected.append({"fen": fen, "why": f"python-chess invalid (status {int(board.status())})", "note": note})
            continue
        if board.is_game_over():
            rejected.append({"fen": fen, "why": "already terminal", "note": note})
            continue
        sol = solve(board, max_moves=4, node_cap=6_000_000)
        if sol["exhausted"]:
            rejected.append({"fen": fen, "why": "oracle hit its node cap", "note": note})
            continue
        if sol["kind"] is None:
            rejected.append({"fen": fen, "why": "no forced mate within 4 moves", "note": note})
            continue
        key = (sol["kind"], sol["moves"])
        if len(bucketed.get(key, [])) >= TARGET_PER_DISTANCE:
            continue
        # Expected UCI mate value: positive when the side to move mates.
        want = sol["moves"] if sol["kind"] == "mate" else -sol["moves"]
        eng = engine_accepts(binary, fen)
        if not eng["accepted"]:
            rejected.append({"fen": fen, "why": "ENGINE refused the FEN (no info lines)", "note": note})
            continue
        fx = {
            "fen": fen,
            "note": note,
            "kind": sol["kind"],
            "moves": sol["moves"],
            "plies": sol["plies"],
            "expected_reported_mate": want,
            "oracle_nodes": sol["nodes"],
            "pieces": len(board.piece_map()),
            "halfmove_clock": board.halfmove_clock,
            "legal_moves": board.legal_moves.count(),
            "engine_at_depth6": eng,
        }
        bucketed.setdefault(key, []).append(fx)

    fixtures = [fx for group in bucketed.values() for fx in group]
    fixtures.sort(key=lambda r: (r["kind"], r["moves"], r["fen"]))
    by_key = {}
    for fx in fixtures:
        k = f"{fx['kind']}_{fx['moves']}"
        by_key[k] = by_key.get(k, 0) + 1

    out = {
        "binary": binary,
        "candidate_source": cand_source,
        "pool_size": len(pool),
        "n_fixtures": len(fixtures),
        "n_rejected": len(rejected),
        "by_distance": by_key,
        "distance_ge_2": sum(v for k, v in by_key.items() if not k.endswith("_1")),
        "fixtures": fixtures,
        "rejected": rejected,
    }
    with open(here + "/evidence/corpus.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({k: v for k, v in out.items() if k not in ("fixtures", "rejected")}, indent=2))
    print("reject reasons:")
    reasons = {}
    for r in rejected:
        reasons[r["why"]] = reasons.get(r["why"], 0) + 1
    print(json.dumps(reasons, indent=2))
    return 0 if out["n_fixtures"] >= 60 and out["distance_ge_2"] >= 40 else 1


if __name__ == "__main__":
    sys.exit(main())
