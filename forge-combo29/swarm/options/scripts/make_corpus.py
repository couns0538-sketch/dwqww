#!/usr/bin/env python3
"""Build the two audit corpora: 200 legality positions and 30 proved mates.

Everything here is independent of the engine under audit. Move generation and
mate proof come from python-chess and from `mateproof.py`, whose own self-test
(`prover_selftest.py`) checks it against unpruned minimax before it is trusted.

Legality corpus: real game positions from the PGN chunks present at the audit
base commit. Selection is deterministic so the set is nameable and
re-derivable: for every game, the position after ply 16 and after ply 24 (when
the game is that long) is a candidate, candidates are deduplicated by board
identity, sorted, and the first 200 kept.

Mate corpus: 30 positions with a PROVED forced mate, mixing both signs:
  * sign +1: the side to move has a forced mate in d plies
  * sign -1: the side to move is mated in d plies whatever it does
The second shape is essential. A mate checker that assumes the side to move is
the attacker is wrong on every one of them, and a switch that mangles a
negative mate score is invisible in a one-sided corpus.

Fixture construction is by random playout out of sparse endgame seeds; the mate
is then PROVED, never assumed. Playouts give real positions with real histories;
the proof is what makes them fixtures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys

import chess
import chess.pgn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mateproof  # noqa: E402

PLIES = (16, 24)


# ---------------------------------------------------------------- legality


def board_id(board: chess.Board) -> str:
    """Board identity without the move counters, which do not change legality."""
    b = board.copy(stack=False)
    b.halfmove_clock = 0
    b.fullmove_number = 1
    return b.fen()


def candidates(paths: list[str]) -> list[chess.Board]:
    seen: dict[str, chess.Board] = {}
    for path in paths:
        with open(path, errors="ignore") as fh:
            while True:
                game = chess.pgn.read_game(fh)
                if game is None:
                    break
                if game.errors:
                    continue
                board = game.board()
                ply = 0
                for move in game.mainline_moves():
                    if not board.is_legal(move):
                        break
                    board.push(move)
                    ply += 1
                    if ply in PLIES:
                        if board.is_game_over(claim_draw=False) or not board.legal_moves:
                            continue
                        key = board_id(board)
                        if key not in seen:
                            seen[key] = board.copy(stack=False)
                    if board.is_game_over(claim_draw=False):
                        break
    return [seen[k] for k in sorted(seen)]


def build_legality(paths: list[str], want: int) -> list[chess.Board]:
    pool = candidates(paths)
    if len(pool) < want:
        raise SystemExit(f"only {len(pool)} distinct candidate positions, need {want}")
    picked = pool[:want]
    # The corpus contract, asserted rather than assumed: a corpus that silently
    # lost a property is indistinguishable from one that never had it.
    assert len(picked) == want, len(picked)
    assert len({board_id(b) for b in picked}) == want, "duplicate board in corpus"
    assert any(b.turn == chess.WHITE for b in picked)
    assert any(b.turn == chess.BLACK for b in picked)
    assert any(b.is_check() for b in picked), "corpus has no position in check"
    for b in picked:
        assert b.is_valid(), b.fen()
        assert b.legal_moves
    return picked


# ---------------------------------------------------------------- mate corpus


SEEDS = [
    "6k1/8/6K1/8/8/8/8/7Q w - - 0 1",           # KQ vs K
    "6k1/8/6K1/8/8/8/8/2B1B3 w - - 0 1",         # KBB vs K
    "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",      # back rank
    "2r3k1/5ppp/8/8/8/8/5PPP/2R3K1 w - - 0 1",   # rook pair on the seventh
    "4r1k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1",   # doubled rooks
    "8/8/8/8/8/1k6/8/K1R5 w - - 0 1",            # KR vs K
    "r4rk1/ppp2ppp/8/8/8/8/PPP2PPP/R4RK1 w - - 0 1",  # rooks and pawns
]


def playout(seed: chess.Board, rng: random.Random, plies: int) -> chess.Board:
    """Random legal playout that keeps the seed's material.

    Checks are preferred half the time, so the walk explores mating nets instead
    of shuffling into a repetition. Material is pinned so the playout cannot
    wander into a position where the mate we want is no longer available for the
    reason the fixture is about.
    """
    b = seed.copy()
    start = b.occupied_co[chess.WHITE].bit_count() + b.occupied_co[chess.BLACK].bit_count()
    for _ in range(plies):
        moves = list(b.legal_moves)
        if not moves:
            break
        checks = [m for m in moves if b.gives_check(m)]
        pool = checks if checks and rng.random() < 0.5 else moves
        b.push(rng.choice(pool))
        if b.is_game_over(claim_draw=False):
            break
        if b.occupied_co[chess.WHITE].bit_count() + b.occupied_co[chess.BLACK].bit_count() != start:
            break
    return b


def build_mates(want: int, limit: int, budget: int, want_negative: int,
                deep_want: int = 10) -> tuple[list[dict], dict]:
    """Collect proved mates, cheapest proof first.

    The bound is raised only when a lower one has been exhausted, because a
    proof at bound d costs far more than at d-2 and the corpus does not need
    long mates to be useful: what it needs is both SIGNS and enough depth that a
    dropped move has somewhere to hide. The walk stops as soon as the requested
    mix is met, and reports how many candidates it examined.
    """
    rng = random.Random(20261117)
    found: list[dict] = []
    seen: set[str] = set()
    tally = {"PROVED": 0, "NOMATE": 0, "duplicate": 0, "rules_excluded": 0, "attempts": 0}

    def consider(board: chess.Board, tag: str, bound: int) -> None:
        key = board_id(board)
        if key in seen:
            tally["duplicate"] += 1
            return
        seen.add(key)
        tally["attempts"] += 1
        result = mateproof.prove(board, bound, budget)
        if result is None:
            tally["NOMATE"] += 1
            return
        sign, plies = result
        if not mateproof.rule_clean(board, plies):
            tally["rules_excluded"] += 1
            return
        tally["PROVED"] += 1
        found.append({
            "fen": board.fen(),
            "sign": sign,
            "mate_plies": plies,
            "stm_is_attacker": sign > 0,
            "source": tag,
        })

    def enough() -> bool:
        pos = sum(1 for e in found if e["sign"] > 0)
        neg = sum(1 for e in found if e["sign"] < 0)
        deep = sum(1 for e in found if e["sign"] > 0 and e["mate_plies"] >= 5)
        return (pos >= want - want_negative and neg >= want_negative
                and deep >= min(deep_want, want - want_negative))

    # Bound ladder. Each rung reuses the same playout pool; a position that had
    # no mate at a lower bound is retried one rung up, which is cheaper than
    # starting at the top. The rungs that matter are 5 and above: a mate in 3
    # plies is found by almost any search, so it barely exercises the pruning
    # the switches touch, while a mate in 7 or 9 sits right at the depth-12
    # horizon where a dropped move can still be recovered or not.
    for bound in (3, 4, 5, 6, min(limit, 7)):
        if enough():
            break
        for seed_fen in SEEDS:
            seed = chess.Board(seed_fen)
            if not seed.is_valid() or not seed.legal_moves:
                continue
            consider(seed, "seed", bound)
            for n in range(220):
                if enough():
                    break
                b = playout(seed, rng, 2 + n % 11)
                if b.is_game_over(claim_draw=False) or not b.legal_moves:
                    continue
                consider(b, "playout", bound)

    positive = [e for e in found if e["sign"] > 0]
    negative = [e for e in found if e["sign"] < 0]
    if len(negative) < want_negative:
        raise SystemExit(
            f"only {len(negative)} negative-sign fixtures, need {want_negative}; tally {tally}"
        )

    # Compose with a stated mix rather than taking whatever filled first. Mate
    # in one is the weakest fixture (one legal check settles it), so the set caps
    # how many it carries and spends the rest on longer mates.
    positive.sort(key=lambda e: -e["mate_plies"])
    negative.sort(key=lambda e: -e["mate_plies"])
    short = [e for e in positive if e["mate_plies"] >= 3]
    ones = [e for e in positive if e["mate_plies"] == 1]

    picked: list[dict] = []
    picked.extend(negative[:want_negative])
    remaining = want - len(picked)
    picked.extend(short[: max(0, remaining - 3)])
    picked.extend(ones[: max(0, want - len(picked))])
    for e in short:
        if len(picked) >= want:
            break
        if e not in picked:
            picked.append(e)
    picked = picked[:want]

    hist: dict[str, int] = {}
    for e in picked:
        k = f"{e['sign']:+d}"
        hist[k] = hist.get(k, 0) + 1
    ply_hist: dict[str, int] = {}
    for e in picked:
        k = str(e["mate_plies"])
        ply_hist[k] = ply_hist.get(k, 0) + 1
    return picked, {
        "tally": tally,
        "available": {
            "positive": len(positive),
            "negative": len(negative),
            "positive_mate_in_1": len(ones),
            "positive_mate_in_3_plus": len(short),
        },
        "sign_counts": hist,
        "ply_counts": ply_hist,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="forge-combo29 directory at the base commit")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--positions", type=int, default=200)
    ap.add_argument("--mates", type=int, default=30)
    ap.add_argument("--mate-limit", type=int, default=7)
    ap.add_argument("--mate-budget", type=int, default=3_000_000)
    ap.add_argument("--negative", type=int, default=8)
    ap.add_argument("--deep", type=int, default=10, help="minimum fixtures of mate in 5+ plies")
    args = ap.parse_args()

    import glob

    paths = sorted(glob.glob(os.path.join(args.root, "tests_r3fu_*", "**", "*.pgn"), recursive=True))
    if not paths:
        raise SystemExit("no PGN inputs found")

    legality = build_legality(paths, args.positions)
    os.makedirs(args.out, exist_ok=True)

    pos_path = os.path.join(args.out, "positions200.fens")
    with open(pos_path, "w") as fh:
        for b in legality:
            fh.write(b.fen() + "\n")

    mates, mate_meta = build_mates(args.mates, args.mate_limit, args.mate_budget, args.negative, args.deep)
    if len(mates) < args.mates:
        raise SystemExit(f"only {len(mates)} mate fixtures of {args.mates}; {mate_meta}")
    # Re-prove every fixture once more after selection, from a clean prover.
    # A fixture that survives only because of an earlier search's state is not
    # a fixture.
    for entry in mates:
        again = mateproof.prove(chess.Board(entry["fen"]), entry["mate_plies"], args.mate_budget)
        assert again == (entry["sign"], entry["mate_plies"]), (entry, again)
    with open(os.path.join(args.out, "mates30.json"), "w") as fh:
        json.dump(mates, fh, indent=1)

    digest = hashlib.sha256(open(pos_path, "rb").read()).hexdigest()
    mate_digest = hashlib.sha256(json.dumps(mates, sort_keys=True).encode()).hexdigest()
    meta = {
        "positions": len(legality),
        "positions_sha256": digest,
        "in_check": sum(1 for b in legality if b.is_check()),
        "white_to_move": sum(1 for b in legality if b.turn == chess.WHITE),
        "inputs": [os.path.relpath(p, args.root) for p in paths],
        "selection": f"dedup by board identity, sorted, first {args.positions}; plies {PLIES}",
        "mates": len(mates),
        "mates_sha256": mate_digest,
        "mate_prover": mate_meta,
        "mate_ply_histogram": {
            f"{s:+d}": sum(1 for m in mates if m["sign"] == s)
            for s in (-1, 1)
        },
        "mate_sources": {
            k: sum(1 for m in mates if m["source"] == k)
            for k in sorted({m["source"] for m in mates})
        },
    }
    with open(os.path.join(args.out, "corpus.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    print(json.dumps(meta, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
