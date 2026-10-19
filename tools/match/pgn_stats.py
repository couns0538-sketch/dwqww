#!/usr/bin/env python3
"""Original MIT-licensed paired PGN checker; no Elo estimator or SPRT reimplementation.
Fastchess owns the SPRT calculation. This independently checks its input outcomes.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import re

TAG = re.compile(r'^\[([A-Za-z0-9_]+) "((?:[^"\\]|\\.)*)"\]$', re.MULTILINE)
RESULTS = {"1-0": 2, "1/2-1/2": 1, "0-1": 0}


def games(text: str) -> list[tuple[dict[str, str], str]]:
    parsed = []
    for block in re.split(r'(?=^\[Event )', text, flags=re.MULTILINE):
        if not block.strip():
            continue
        tags = dict(TAG.findall(block))
        if not tags:
            raise ValueError("PGN block has no headers")
        body = TAG.sub("", block)
        body = re.sub(r'\{[^}]*\}', " ", body, flags=re.DOTALL)
        body = re.sub(r';[^\n]*', " ", body)
        body = re.sub(r'\b\d+\.(?:\.\.)?', " ", body)
        tokens = body.split()
        if not tokens or tokens[-1] != tags.get("Result") or tokens[-1] not in RESULTS:
            raise ValueError("missing, unfinished, or inconsistent game result")
        parsed.append((tags, " ".join(tokens[:-1])))
    if not parsed:
        raise ValueError("no completed games")
    return parsed


def summarize(text: str, candidate: str = "Candidate", baseline: str = "Baseline",
              require_identical_pairs: bool = False) -> dict:
    grouped: dict[str, list] = collections.defaultdict(list)
    wdl = [0, 0, 0]  # candidate wins, draws, losses
    terminations: collections.Counter = collections.Counter()
    for tags, moves in games(text):
        if {tags.get("White"), tags.get("Black")} != {candidate, baseline}:
            raise ValueError("unexpected players")
        if not tags.get("Round") or not tags.get("FEN"):
            raise ValueError("paired opening match requires Round and FEN headers")
        term = tags.get("Termination", "missing")
        if term != "normal":
            raise ValueError(f"non-normal termination: {term}")
        terminations[term] += 1
        score = RESULTS[tags["Result"]]
        if tags["Black"] == candidate:
            score = 2 - score
        wdl[2 - score] += 1
        grouped[tags["Round"]].append((tags, moves, score))
    penta = [0] * 5
    unique = set()
    for round_id, pair in grouped.items():
        if len(pair) != 2:
            raise ValueError(f"incomplete/duplicated pair in round {round_id}")
        (one, moves1, score1), (two, moves2, score2) = pair
        if one["White"] != two["Black"] or one["Black"] != two["White"]:
            raise ValueError("pair colors were not swapped")
        if one["FEN"] != two["FEN"]:
            raise ValueError("pair used different starting positions")
        position = " ".join(one["FEN"].split()[:4])
        if position in unique:
            raise ValueError("opening repeated across pairs")
        unique.add(position)
        if require_identical_pairs and (moves1 != moves2 or one["Result"] != two["Result"]):
            raise ValueError("A/A pair was not deterministic")
        penta[score1 + score2] += 1
    return {"pairs": len(grouped), "games": 2 * len(grouped),
            "candidate_wins_draws_losses": wdl, "pentanomial_0_half_1_1half_2": penta,
            "unique_openings": len(unique), "terminations": dict(terminations),
            "score_fraction": (wdl[0] + wdl[1] / 2) / (2 * len(grouped)),
            "elo_claim": None, "note": "Outcome bookkeeping only, not evidence of an Elo gain."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pgn", type=Path)
    parser.add_argument("--candidate", default="Candidate")
    parser.add_argument("--baseline", default="Baseline")
    parser.add_argument("--aa", action="store_true")
    args = parser.parse_args()
    print(json.dumps(summarize(args.pgn.read_text(), args.candidate, args.baseline, args.aa), indent=2))
