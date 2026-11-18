#!/usr/bin/env python3
"""Recount completed color-reversed games with python-chess for Job 28."""

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from hashlib import file_digest, sha256
import json
from math import comb, log10, sqrt
from pathlib import Path
import re

import chess.pgn

WHITE_HALF_POINTS = {"1-0": 2, "1/2-1/2": 1, "0-1": 0}
FINISHED = re.compile(r"^Finished game (\d+) \(([AB]) vs ([AB])\): (1-0|0-1|1/2-1/2) \{[^}]*\}$", re.M)


def require(condition, description):
    if not condition:
        raise ValueError(description)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def opening_key(fen):
    fields = fen.split()
    require(len(fields) == 6, f"expected six fields in FEN {fen}")
    return sha256(" ".join(fields[:4]).encode()).hexdigest()


def pgn_results(path, assigned):
    rounds, raw_results, all_fens = defaultdict(list), Counter(), set()
    raw_games = unresolved = 0
    with path.open(encoding="utf-8") as source:
        while (game := chess.pgn.read_game(source)) is not None:
            fields = game.headers
            round_number = int(fields["Round"])
            white, black, fen, result = (fields[key] for key in ("White", "Black", "FEN", "Result"))
            require((white, black) in (("A", "B"), ("B", "A")), f"{path}: invalid colors")
            require(not game.errors, f"{path}: round {round_number}: {game.errors}")
            key = opening_key(fen)
            require(key in assigned, f"{path}: round {round_number}: unassigned opening")
            all_fens.add(key)
            raw_games += 1
            if result == "*":
                unresolved += 1
                continue
            plies = tuple(move.uci() for move in game.mainline_moves())
            require(len(plies) == int(fields["PlyCount"]), f"{path}: round {round_number}: ply count differs")
            points = WHITE_HALF_POINTS[result] if white == "A" else 2 - WHITE_HALF_POINTS[result]
            rounds[round_number].append((white, fen, points, plies))
            raw_results[white, black, result] += 1
    paired_keys, pentanomial, scores = set(), [0] * 5, Counter()
    same_moves = equal_same = 0
    for round_number, games in rounds.items():
        if len(games) == 1:
            continue
        require(len(games) == 2, f"{path}: round {round_number}: more than two games")
        a, b = games
        require(a[0] != b[0] and a[1] == b[1], f"{path}: round {round_number}: invalid reversed-color pair")
        key = opening_key(a[1])
        require(key not in paired_keys, f"{path}: round {round_number}: reused pair opening")
        paired_keys.add(key)
        points = a[2] + b[2]
        pentanomial[points] += 1
        scores.update([a[2], b[2]])
        if a[3] == b[3]:
            same_moves += 1
            equal_same += points == 2
    return raw_games, unresolved, raw_results, all_fens, scores, pentanomial, same_moves, equal_same


def symmetric_elo(counts):
    pairs = sum(counts)
    if pairs < 2:
        return None
    mean = sum((index / 4) * count for index, count in enumerate(counts)) / pairs
    variance = sum(count * (index / 4 - mean) ** 2 for index, count in enumerate(counts)) / pairs
    spread = 1.959963984540054 * sqrt(variance / pairs)
    if not 0 < mean - spread <= mean + spread < 1:
        return None

    def elo(points):
        return -400 * log10(1 / points - 1)

    center = elo(mean)
    margin = (elo(mean + spread) - elo(mean - spread)) / 2
    return center, center - margin, center + margin


def check(raw, manifest, name, pgn):
    pgn = pgn or raw / f"{name}.pgn"
    meta = json.loads((raw / f"{name}.meta").read_bytes())
    out = raw / f"{name}.out"
    require(digest(pgn) == meta["pgn_sha256"] and digest(out) == meta["out_sha256"], f"{name}: raw hash mismatch")
    reserved = set(manifest["cells"][name]["fen_keys_sha256"])
    raw_games, unresolved, results, used, scores, penta, same, equal_same = pgn_results(pgn, reserved)
    pairs = sum(penta)
    if meta["status"] == "complete":
        require((raw_games, 2 * pairs, unresolved, used) == (meta["games_requested"], meta["games_requested"], 0, reserved),
                f"{name}: incomplete schedule or book use")
        logs = FINISHED.findall(out.read_text())
        require(Counter((w, b, result) for _, w, b, result in logs) == results
                and len({index for index, *_ in logs}) == raw_games, f"{name}: PGN and fastchess finished-game list differ")
    else:
        require(meta["status"] == "interrupted", f"{name}: unexpected raw status {meta['status']}")
    better, worse = sum(penta[3:]), sum(penta[:2])
    unequal = better + worse
    sign_p = min(1, Fraction(2 * sum(comb(unequal, k) for k in range(min(better, worse) + 1)), 2**unequal))
    rating = symmetric_elo(penta)
    reading = "unavailable" if rating is None else "BETTER" if rating[1] > 0 else "WORSE" if rating[2] < 0 else "LEVEL"
    if name in ("K17", "K18"):
        require(pairs == same == equal_same == 50 and penta[2] == 50, f"{name}: same-move control failed")
    elo = "unavailable" if rating is None else f"{rating[0]:+.8f} [{rating[1]:+.8f}, {rating[2]:+.8f}]"
    nodes = meta["nodes_a"]
    print(f"{name} {meta['status']}, {nodes:,} nodes per move, {2 * pairs:,} games / {pairs:,} complete pairs, "
          f"{raw_games - 2 * pairs:,} games excluded ({unresolved} unresolved). A W-L-D {scores[2]}-{scores[0]}-{scores[1]}; "
          f"pentanomial {penta}; {same}/{pairs} equal UCI move lists; {better} better / {worse} worse; "
          f"{equal_same} even same / {penta[2] - equal_same} even different; two-sided exact p {float(sign_p):.10g}; "
          f"unrounded symmetric Elo {elo}; {reading}.")
    print(f"{name} PGN SHA-256 {meta['pgn_sha256']}; fastchess output SHA-256 {meta['out_sha256']}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("name", choices=("K17", "K18", "M1", "M2"))
    parser.add_argument("--pgn", type=Path)
    args = parser.parse_args()
    check(args.raw, json.loads(args.manifest.read_bytes()), args.name, args.pgn)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, TypeError, KeyError) as error:
        raise SystemExit(str(error)) from error
