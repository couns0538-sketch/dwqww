#!/usr/bin/env python3
"""Verify Job 9 replay gates before measurement and compare full-S openings."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import re

from summarize import BUDGETS, HISTORY, MASKS, completion, read_games, read_rows, read_search

HERE = Path(__file__).resolve().parent
FIELDS = ("game", "ply", "fen", "depth", "nodes", "bestmove", "cnt", "final_nodes", "final_nodes_info")
VOLATILE = re.compile(r" (?:time|nps) [0-9]+(?= |$)")
CONTROL_LIMIT = Fraction(527, 1000)


def rows(path, positions, selected=False, opening_file=False):
    meta, reason = completion(path)
    if meta is None:
        raise ValueError(f"{path}: {reason}")
    if meta["positions_completed"] != len(positions) or meta["opening_only"] != opening_file:
        raise ValueError(f"{path}: wrong number of rows or opening-only mode in metadata")
    return (row for row in read_rows(path, positions) if not selected or row["ply"] == 0)


def comparable(row):
    return {**{field: row[field] for field in FIELDS}, "info": VOLATILE.sub("", row["info"])}


def compare(label, candidate, reference, num_examples=1):
    matches = count = 0
    for row, expected in zip(candidate, reference, strict=True):
        count += 1
        actual, previous = comparable(row), comparable(expected)
        if actual == previous:
            matches += 1
        elif count - matches <= num_examples:
            differing = [field for field in actual if actual[field] != previous[field]]
            print(f"{label} discrepancy at game {row['game']} ply {row['ply']}: {', '.join(differing)}.")
            print("  current  " + json.dumps(row, separators=(",", ":")))
            print("  expected " + json.dumps(expected, separators=(",", ":")))
    print(f"{label}: {matches}/{count} paired rows equal.")
    return matches == count


def opening_gate(raw, games, opening_positions, full):
    valid = True
    source = "S-raw" if full else "opening-raw"
    for budget in BUDGETS:
        default = raw / "opening-raw" / f"default-{budget}.jsonl"
        for mask in MASKS:
            candidate = raw / source / f"mask-{mask}-{budget}.jsonl"
            valid &= compare(
                f"Gate 3 {'full' if full else 'pre-prediction'} mask {mask} {budget}",
                rows(candidate, games if full else opening_positions, selected=full, opening_file=not full),
                rows(default, opening_positions, opening_file=True),
            )
    return valid


def rate(path, positions):
    nodes = takes = 0
    for row in rows(path, positions):
        on_nodes, counts = read_search(row, soft=True, counters=(HISTORY,))
        nodes += on_nodes
        takes += counts[HISTORY]
    return Fraction(1000 * takes, nodes), takes, nodes


def verify_known(raw, games, opening_positions, job6, job8, ages):
    for keep in (896, 512):
        for budget in BUDGETS:
            if not compare(
                f"Gate 1 keep {keep}, mask 7 {budget}",
                rows(raw / "identity-raw" / f"keep-{keep}-{budget}.jsonl", games),
                rows(ages / f"keep-{keep}-warm-{budget}.jsonl", games),
            ):
                return 2
    if not compare(
        "Gate 2 keep 729, mask 0 warm soft",
        rows(raw / "identity-raw" / "mask-0-soft.jsonl", games),
        rows(job6 / "base-warm-soft.jsonl", games),
    ):
        return 2

    openings_ok = opening_gate(raw, games, opening_positions, full=False)
    warm_soft = job6 / "base-warm-soft.jsonl"
    cold_refs = {"soft": job6 / "base-cold-soft.jsonl", "hard": job8 / "base-cold-hard.jsonl"}
    for budget in BUDGETS:
        compare(
            f"Gate 4 W0 {budget} vs cold",
            rows(raw / "W-raw" / f"W0-{budget}.jsonl", games), rows(cold_refs[budget], games),
            num_examples=5,
        )

    control, takes, nodes = rate(raw / "S-raw" / "mask-7-soft.jsonl", games)
    baseline, base_takes, base_nodes = rate(warm_soft, games)
    control_ok = control < CONTROL_LIMIT and control < baseline / 5
    print(f"Gate 5 mask 7 warm soft: {takes}/{nodes} = {float(control):.6f}/1k actual nodes; "
          f"baseline {base_takes}/{base_nodes} = {float(baseline):.6f}/1k; "
          f"{'pass' if control_ok else 'FAIL'} (required below 0.527 and below one fifth baseline).")
    if not openings_ok or not control_ok:
        print("Block S stopped. Blocks W and K may proceed.")
        return 3
    print("Job 9 pre-prediction replay gates passed. Gate 4 discrepancies, if any, are advisory.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="stage", required=True)
    for label in ("known", "full"):
        command = modes.add_parser(label)
        command.add_argument("games", type=Path)
        command.add_argument("--raw", type=Path, default=HERE)
        if label == "known":
            for label in ("job6-raw", "job8-raw", "job8-age"):
                command.add_argument("--" + label, type=Path, required=True)
    args = parser.parse_args()
    positions = read_games(args.games)
    openings = [position for position in positions if position[1] == 0]
    print("Identity preserves game, ply, FEN, depth, nodes, bestmove, raw CNT, final nodes and last info excluding time/NPS.")
    if args.stage == "full":
        return 0 if opening_gate(args.raw, positions, openings, full=True) else 3
    return verify_known(args.raw, positions, openings, args.job6_raw, args.job8_raw, args.job8_age)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
