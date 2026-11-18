#!/usr/bin/env python3
"""Verify Forge Job 3 replay identity, determinism and retained-state controls."""
import argparse
import itertools
import json
from pathlib import Path

ARM_FILES = ("A-soft-warm", "B-hard-warm", "C-soft-cold", "D-hard-cold")
PREFIX = "info string CNT "


def records(path):
    with path.open() as rows:
        for line in rows:
            yield json.loads(line)


def identity(row):
    return tuple(row[k] for k in ("nodes", "bestmove", "cnt"))


def actual_nodes(record):
    assert record["cnt"].startswith(PREFIX)
    count = json.loads(record["cnt"].removeprefix(PREFIX))
    return sum(count["main_nodes"]) + sum(count["q_nodes"])


def verify_opening(raw, job2_raw):
    for arm in ARM_FILES:
        budget = "soft" if "soft" in arm else "hard"
        reference = list(itertools.islice(records(job2_raw / f"O-{budget}.jsonl"), 100))
        current = [row for row in records(raw / f"{arm}.jsonl") if row["ply"] == 0]
        assert len(reference) == len(current) == 100, (arm, len(reference), len(current))
        for expected, actual in zip(reference, current, strict=True):
            if expected["index"] != actual["game"] or expected["fen"] != actual["fen"] or identity(expected) != identity(actual):
                raise SystemExit(f"First opening identity mismatch: arm {arm}, game {actual['game']}. "
                                 f"Job 2 index={expected['index']} nodes={expected['nodes']} "
                                 f"move={expected['bestmove']}; Job 3 nodes={actual['nodes']} "
                                 f"move={actual['bestmove']}; CNT byte-equal={expected['cnt'] == actual['cnt']}.")
        print(f"{arm}: 100/100 opening rows match Job 2 nodes, bestmove and raw CNT.")


def verify_repeat(raw, games):
    lines = games.read_text().splitlines()
    repeats = games.with_name("games-repeat10.txt").read_text().splitlines()
    assert len(lines) == 100 and len(repeats) == 10
    for index, (original, repeated) in enumerate(zip(lines[:10], repeats, strict=True), 1):
        assert original == repeated, f"Game {index} differs in the repeat."
    expected = (row for row in records(raw / "A-soft-warm.jsonl") if row["game"] <= 10)
    actual = records(raw / "A-repeat10.jsonl")
    checked = 0
    for checked, (p, q) in enumerate(zip(expected, actual, strict=True), 1):
        assert (p["game"], p["ply"], identity(p)) == (q["game"], q["ply"], identity(q)), (p["game"], p["ply"])
    assert checked > 0
    print(f"Arm A repeat: 10/10 game rows and {checked}/{checked} search CNT lines match.")


def verify_warm(raw):
    for warm, cold in ((ARM_FILES[0], ARM_FILES[2]), (ARM_FILES[1], ARM_FILES[3])):
        left = records(raw / f"{warm}.jsonl")
        right = records(raw / f"{cold}.jsonl")
        searched = info_difference = actual_difference = 0
        for x, y in zip(left, right, strict=True):
            assert all(x[k] == y[k] for k in ("game", "ply", "fen")), (warm, cold, x["game"], x["ply"])
            if x["ply"] == 0:
                continue
            searched += 1
            info_difference += x["nodes"] != y["nodes"]
            actual_difference += actual_nodes(x) != actual_nodes(y)
        assert info_difference > 0, (warm, cold, searched)
        print(f"{warm} vs {cold}: {info_difference}/{searched} later plies differ in last info nodes; "
              f"{actual_difference}/{searched} differ in actual CNT nodes.")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("raw", type=Path)
parser.add_argument("job2_raw", type=Path)
parser.add_argument("games", type=Path)
args = parser.parse_args()
verify_opening(args.raw, args.job2_raw)
verify_repeat(args.raw, args.games)
verify_warm(args.raw)
