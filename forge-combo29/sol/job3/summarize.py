#!/usr/bin/env python3
"""Validate Forge Job 3 rows and calculate action rates from the raw counters."""

import argparse
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
import json
from pathlib import Path
import re
from statistics import median

COUNTER_PREFIX = "info string CNT "
INFO_DEPTH = re.compile(r"^info depth (\d+)\b.*\bnodes (\d+)\b")
STEPS = (
    "razor", "rfp", "null_move", "probcut", "iir_no_tt", "iir_tt", "lmp",
    "quiet_futility", "history_pruning", "quiet_see", "capture_futility",
    "noisy_see", "singular", "check_extension", "lmr", "aspiration",
    "q_futility", "fail_low_bonus", "eval_swing", "draw_jitter",
)
EXTRA_EVENTS = {
    "null_move": ("null_move_tested",),
    "probcut": ("probcut_tested",),
    "singular": ("singular_double", "singular_negative"),
    "lmr": ("lmr_plies",),
}
EVENTS = tuple(
    event for step in STEPS for event in (step + "_taken", *EXTRA_EVENTS.get(step, ()))
)
COUNTERS = {
    "main_nodes", "q_nodes",
    *(step + suffix for step in STEPS for suffix in ("_tested", "_taken")),
    *(event for extras in EXTRA_EVENTS.values() for event in extras),
}
ARMS = {
    "A": ("A-soft-warm", True),
    "B": ("B-hard-warm", False),
    "C": ("C-soft-cold", True),
    "D": ("D-hard-cold", False),
}
RATIOS = (("A", "C"), ("B", "D"), ("A", "B"), ("C", "D"))
PLY_GROUPS = ((0, 1, "0"), (1, 10, "1–9"), (10, 30, "10–29"), (30, 60, "30–59"))
PLY_EVENTS = (
    "history_pruning_taken", "lmr_taken", "quiet_futility_taken", "lmp_taken",
    "singular_taken",
)


@dataclass
class Arm:
    counts: Counter = field(default_factory=Counter)
    depths: list = field(default_factory=list)
    nodes: list = field(default_factory=list)
    group_counts: list = field(default_factory=lambda: [Counter() for _ in PLY_GROUPS])
    group_sizes: list = field(default_factory=lambda: [0] * len(PLY_GROUPS))

    @property
    def total_nodes(self):
        return self.counts["main_nodes"] + self.counts["q_nodes"]

    def add(self, counts, depth, nodes, ply):
        self.counts.update(counts)
        self.depths.append(depth)
        self.nodes.append(nodes)
        group = next(i for i, (start, end, _) in enumerate(PLY_GROUPS) if start <= ply < end)
        self.group_counts[group].update(counts)
        self.group_sizes[group] += 1


def read_games(path):
    positions = []
    with path.open(encoding="utf-8") as games:
        game_count = 0
        for game_count, line in enumerate(games, start=1):
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 4 or fields[0] != str(game_count):
                raise ValueError(f"{path}:{game_count}: expected game, FEN, moves and reason")
            _, fen, moves, reason = fields
            moves = moves.split()
            if not fen or not reason or len(moves) > 60:
                raise ValueError(f"{path}:{game_count}: invalid game record")
            positions.extend((game_count, ply, fen, move) for ply, move in enumerate(moves))
    if game_count != 100 or not positions:
        raise ValueError(f"{path}: expected 100 games with plies, got {game_count} games and {len(positions)} plies")
    return positions


def read_search(row, soft):
    if not (info := INFO_DEPTH.match(row["info"])):
        raise ValueError("missing last info depth line")
    depth, info_nodes = map(int, info.groups())
    if (depth, info_nodes) != (row["depth"], row["nodes"]):
        raise ValueError("row does not agree with its last info line")
    raw = row["cnt"]
    if not isinstance(raw, str) or not raw.startswith(COUNTER_PREFIX):
        raise ValueError("missing raw CNT line")
    payload = json.loads(raw.removeprefix(COUNTER_PREFIX))
    if not isinstance(payload, dict) or payload.keys() != COUNTERS:
        raise ValueError("unexpected CNT fields")
    counts = {}
    for event, buckets in payload.items():
        if not isinstance(buckets, list) or len(buckets) != 32 or any(type(n) is not int or n < 0 for n in buckets):
            raise ValueError(f"expected 32 nonnegative counts for {event}")
        counts[event] = sum(buckets)
    if any(payload["q_nodes"][1:]):
        raise ValueError("qsearch node counter outside bucket 0")
    actual_nodes = counts["main_nodes"] + counts["q_nodes"]
    cap = 8000 if soft else 20000
    if not 0 < actual_nodes <= cap or actual_nodes < info_nodes:
        raise ValueError(f"CNT nodes {actual_nodes} inconsistent with {info_nodes} last info nodes and cap {cap}")
    if soft:
        final = row["final_nodes"]
        if type(final) is not int or actual_nodes != final:
            raise ValueError(f"CNT nodes {actual_nodes} differ from softnodes final nodes {final}")
        if row["final_nodes_info"] != f"info string softnodes nodes {final}":
            raise ValueError("softnodes final value does not agree with its raw UCI line")
    return counts, depth, actual_nodes


def read_arm(path, positions, soft, played):
    arm = Arm()
    with path.open(encoding="utf-8") as rows:
        for index, (game, ply, fen, move) in enumerate(positions, start=1):
            line = rows.readline()
            if not line:
                raise ValueError(f"{path}: expected {len(positions)} CNT lines, got {index - 1}")
            try:
                row = json.loads(line)
                if (row["index"], row["game"], row["ply"], row["fen"]) != (index, game, ply, fen):
                    raise ValueError(f"expected game {game} ply {ply} and its original FEN")
                if played and row["bestmove"] != move:
                    raise ValueError(f"A bestmove differs from game {game} ply {ply} in games.txt")
                counts, depth, actual_nodes = read_search(row, soft)
                arm.add(counts, depth, actual_nodes, ply)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{index}: {error}") from error
        if rows.readline():
            raise ValueError(f"{path}: more than the expected {len(positions)} CNT lines")
    return arm


def read_results(games_path, raw_dir):
    positions = read_games(games_path)
    return {
        key: read_arm(raw_dir / (name + ".jsonl"), positions, soft, played=(key == "A"))
        for key, (name, soft) in ARMS.items()
    }


def event_ratio(arms, event, numerator, denominator):
    first, second = arms[numerator], arms[denominator]
    if second.counts[event] == 0:
        return None
    return Fraction(first.counts[event] * second.total_nodes, second.counts[event] * first.total_nodes)


def rate(counts, event):
    nodes = counts["main_nodes"] + counts["q_nodes"]
    return Fraction(1000 * counts[event], nodes) if nodes else None


def formatted(value):
    return "n/a" if value is None else f"{float(value):.4f}"


def read_prediction(path):
    guesses = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in EVENTS:
            continue
        event, *values = fields
        if len(values) != len(RATIOS) or event in guesses:
            raise ValueError(f"{path}: expected one row of four predictions per event: {event}")
        targets = tuple(None if value == "zero" else Fraction(value) for value in values)
        if any(target is not None and target <= 0 for target in targets):
            raise ValueError(f"{path}: expected a positive prediction or the word zero: {event}")
        guesses[event] = tuple(zip(values, targets))
    if guesses.keys() != set(EVENTS):
        raise ValueError(f"{path}: missing predictions for {', '.join(sorted(set(EVENTS) - guesses.keys()))}")
    return guesses


def print_grades(arms, predictions):
    print("## Prediction grades")
    print()
    print("A numeric guess survives when the exact ratio is within a factor of 1.5. "
          "A zero guess requires zero events in both arms. An undefined ratio kills a numeric guess.")
    print()
    print("| Counter | Ratio | Guess | Measured | Outcome |")
    print("|---|---|---:|---:|---|")
    factor = Fraction(3, 2)
    outcomes = Counter()
    for event in EVENTS:
        for (a, b), (guess, target) in zip(RATIOS, predictions[event]):
            observed = event_ratio(arms, event, a, b)
            if target is None:
                survived = not (arms[a].counts[event] or arms[b].counts[event])
            else:
                survived = observed is not None and target / factor <= observed <= target * factor
            outcome = "survives" if survived else "KILLED"
            outcomes[outcome] += 1
            print(f"| {event} | {a}/{b} | {guess} | {formatted(observed)} | {outcome} |")
    print(f"\n{outcomes['KILLED']} KILLED, {outcomes['survives']} survive.\n")


def print_tables(arms):
    print("Summed CNT lines: " + ", ".join(f"{key} {len(arm.nodes)}" for key, arm in arms.items()) + ".")
    print("Each arm matches the number and order of plies in games.txt. Rates use actual main plus qsearch nodes.")
    print()
    print("## Table 1")
    print()
    print("| Counter | A / 1k | B / 1k | C / 1k | D / 1k | A/C | B/D | A/B | C/D |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for event in EVENTS:
        rates = [formatted(rate(arm.counts, event)) for arm in arms.values()]
        ratios = [formatted(event_ratio(arms, event, a, b)) for a, b in RATIOS]
        print("| " + " | ".join([event, *rates, *ratios]) + " |")

    print()
    print("| Arm | Searches | Total nodes | Root depth median / min / max | Median actual nodes |")
    print("|---|---:|---:|---|---:|")
    for key, arm in arms.items():
        depths = arm.depths
        print(f"| {key} | {len(arm.nodes)} | {arm.total_nodes} | {median(depths):g} / {min(depths)} / {max(depths)} | {median(arm.nodes):g} |")

    print("\n## Table 2\n")
    print("| Counter | Plies | A / 1k | B / 1k | Searches per arm | A nodes | B nodes |")
    print("|---|---|---:|---:|---:|---:|---:|")
    for event in PLY_EVENTS:
        for group, (_, _, label) in enumerate(PLY_GROUPS):
            a, b = arms["A"].group_counts[group], arms["B"].group_counts[group]
            print(f"| {event} | {label} | {formatted(rate(a, event))} | {formatted(rate(b, event))} | "
                  f"{arms['A'].group_sizes[group]} | {a['main_nodes'] + a['q_nodes']} | {b['main_nodes'] + b['q_nodes']} |")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("--prediction", type=Path)
    args = parser.parse_args()
    arms = read_results(args.games, args.raw_dir)
    if args.prediction is not None:
        print_grades(arms, read_prediction(args.prediction))
    print_tables(arms)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
