#!/usr/bin/env python3
"""Validate Forge Job 4 rows and summarize raw and depth-standardized action rates."""

import argparse
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
import json
from pathlib import Path
import re

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
SOFT_ARMS = ("A2", "C2", "E", "F", "G", "H")
HARD_ARMS = ("B2", "D2", "EH", "FH")
TABLE_GROUPS = (("A2", "C2", "E", "F"), ("B2", "D2", "EH", "FH"))
PREDICTION_EVENTS = (
    "history_pruning_taken", "null_move_taken", "probcut_taken", "singular_taken",
    "iir_no_tt_taken", "lmr_taken", "aspiration_taken",
)
PREDICTION_COMPARISONS = (
    ("E", "C2", False), ("F", "C2", False), ("E", "C2", True), ("F", "C2", True),
    ("EH", "D2", False), ("FH", "D2", False), ("EH", "D2", True), ("FH", "D2", True),
)
EXPECTED_COLD_WARM_HISTORY = {
    "A2": "4.417 / 8.554 / 2.944 / 0.861 / 0.366",
    "B2": "12.648 / 33.970 / 37.569 / 37.707 / 24.523",
    "C2": "0.160 / 0.063 / 0.010 / 0.000 / 0.000",
    "D2": "1.662 / 1.635 / 0.566 / 0.121 / 0.048",
}
OLD_ANSWERS = {
    "null_move_taken": "1.222",
    "probcut_taken": "1.402",
    "singular_taken": "0.993",
    "history_pruning_taken": "41.226",
    "lmr_taken": "0.636",
    "iir_no_tt_taken": "0.704",
}


@dataclass
class Arm:
    buckets: dict = field(default_factory=lambda: {counter: [0] * 32 for counter in COUNTERS})
    lines: int = 0

    @property
    def total_main(self):
        return sum(self.buckets["main_nodes"])

    @property
    def total_nodes(self):
        return self.total_main + sum(self.buckets["q_nodes"])

    def add(self, payload):
        for event, bins in payload.items():
            self.buckets[event] = [total + count for total, count in zip(self.buckets[event], bins)]
        self.lines += 1


def read_games(path):
    positions = []
    with path.open(encoding="utf-8") as games:
        game = 0
        for game, line in enumerate(games, start=1):
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 4 or fields[0] != str(game):
                raise ValueError(f"{path}:{game}: expected game, FEN, moves and reason")
            _, fen, moves, reason = fields
            moves = moves.split()
            if not fen or not reason or len(moves) > 60:
                raise ValueError(f"{path}:{game}: invalid game record")
            positions.extend((game, ply, fen) for ply, _ in enumerate(moves))
    if game != 100 or len(positions) != 6000:
        raise ValueError(f"{path}: expected 100 games and 6000 plies, got {game} games and {len(positions)} plies")
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
    for event, buckets in payload.items():
        if not isinstance(buckets, list) or len(buckets) != 32 or any(type(n) is not int or n < 0 for n in buckets):
            raise ValueError(f"expected 32 nonnegative counts for {event}")
    if any(payload["q_nodes"][1:]):
        raise ValueError("qsearch node counter outside bucket 0")
    actual_nodes = sum(payload["main_nodes"]) + sum(payload["q_nodes"])
    cap = 8000 if soft else 20000
    if not 0 < actual_nodes <= cap or actual_nodes < info_nodes:
        raise ValueError(f"CNT nodes {actual_nodes} inconsistent with {info_nodes} last info nodes and cap {cap}")
    if soft:
        final = row["final_nodes"]
        if type(final) is not int or actual_nodes != final:
            raise ValueError(f"CNT nodes {actual_nodes} differ from softnodes final nodes {final}")
        if row["final_nodes_info"] != f"info string softnodes nodes {final}":
            raise ValueError("softnodes final value does not agree with its raw UCI line")
    return payload



def read_arm(path, positions, soft):
    arm = Arm()
    with path.open(encoding="utf-8") as rows:
        for index, (game, ply, fen) in enumerate(positions, start=1):
            line = rows.readline()
            if not line:
                raise ValueError(f"{path}: expected {len(positions)} CNT lines, got {index - 1}")
            try:
                row = json.loads(line)
                if (row["index"], row["game"], row["ply"], row["fen"]) != (index, game, ply, fen):
                    raise ValueError(f"expected game {game} ply {ply} and its original FEN")
                arm.add(read_search(row, soft))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{index}: {error}") from error
        if rows.readline():
            raise ValueError(f"{path}: more than the expected {len(positions)} CNT lines")
    return arm


def read_results(games_path, raw_dir):
    positions = read_games(games_path)
    return {
        arm: read_arm(raw_dir / (arm + ".jsonl"), positions, soft=(arm in SOFT_ARMS))
        for arm in (*SOFT_ARMS, *HARD_ARMS)
    }


def rate(arm, event):
    return Fraction(1000 * sum(arm.buckets[event]), arm.total_nodes) if arm.total_nodes else None


def ratio(source, cold, event, depth_mix=False):
    cold_events = sum(cold.buckets[event])
    if not cold_events:
        return None
    if depth_mix:
        weighted_terms = (
            Fraction(events * cold_nodes, source_nodes)
            for events, source_nodes, cold_nodes in zip(
                source.buckets[event], source.buckets["main_nodes"], cold.buckets["main_nodes"],
            )
            if source_nodes
        )
        standardized = sum(weighted_terms, Fraction(0))
        return standardized / cold_events
    if not source.total_nodes:
        return None
    return Fraction(sum(source.buckets[event]) * cold.total_nodes, source.total_nodes * cold_events)


def interaction(both, history, hash_):
    if both is None or not history or not hash_:
        return None
    return both / (history * hash_)


def main_share(arm, depth):
    return Fraction(100 * arm.buckets["main_nodes"][depth], arm.total_main) if arm.total_main else None


def history_at_depth(arm, depth):
    main = arm.buckets["main_nodes"][depth]
    return Fraction(1000 * arm.buckets["history_pruning_taken"][depth], main) if main else None


def formatted(value, decimals=4):
    return "n/a" if value is None else f"{float(value):.{decimals}f}"


def history_profile(arm):
    return " / ".join(formatted(history_at_depth(arm, d), 3) for d in range(1, 6))


def old_depth_mix_gate(games_path, old_dir):
    positions = read_games(games_path)
    warm = read_arm(old_dir / "A-soft-warm.jsonl", positions, soft=True)
    cold = read_arm(old_dir / "C-soft-cold.jsonl", positions, soft=True)
    matches = 0
    print(f"Job 3 opening and replay rows summed: A {warm.lines}, C {cold.lines}.")
    for event, expected in OLD_ANSWERS.items():
        observed = ratio(warm, cold, event, depth_mix=True)
        agrees = formatted(observed, 3) == expected
        matches += agrees
        print(f"{event}: {formatted(observed, 9)}, expected {expected} to three decimals. "
              f"{'Match' if agrees else 'MISMATCH'}.")
    if matches != len(OLD_ANSWERS):
        raise ValueError(f"Depth-mix gate failed ({matches}/{len(OLD_ANSWERS)}).")
    print(f"Depth-mix gate passed ({matches}/{len(OLD_ANSWERS)}).")


def read_prediction(path):
    guesses = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in PREDICTION_EVENTS:
            continue
        event, *values = fields
        if len(values) != len(PREDICTION_COMPARISONS) or event in guesses:
            raise ValueError(f"{path}: expected one row of eight predictions per event: {event}")
        targets = tuple(None if value == "zero" else Fraction(value) for value in values)
        if any(target is not None and target <= 0 for target in targets):
            raise ValueError(f"{path}: expected a positive prediction or the word zero: {event}")
        guesses[event] = tuple(zip(values, targets))
    if guesses.keys() != set(PREDICTION_EVENTS):
        missing = ", ".join(sorted(set(PREDICTION_EVENTS) - guesses.keys()))
        raise ValueError(f"{path}: missing predictions for {missing}")
    return guesses


def print_grades(arms, predictions):
    print("## Prediction grades\n")
    print("A numeric guess survives when the exact ratio is within a factor of 1.5. "
          "A zero guess requires zero events in both arms. An undefined ratio kills a numeric guess.\n")
    print("| Counter | Comparison | Mix | Guess | Measured | Outcome |")
    print("|---|---|---|---:|---:|---|")
    factor = Fraction(3, 2)
    outcomes = Counter()
    for event in PREDICTION_EVENTS:
        for (a, b, depth_mix), (guess, target) in zip(PREDICTION_COMPARISONS, predictions[event]):
            observed = ratio(arms[a], arms[b], event, depth_mix)
            if target is None:
                survived = not (sum(arms[a].buckets[event]) or sum(arms[b].buckets[event]))
            else:
                survived = observed is not None and target / factor <= observed <= target * factor
            outcome = "survives" if survived else "KILLED"
            outcomes[outcome] += 1
            print(f"| {event} | {a}/{b} | {'cold' if depth_mix else 'plain'} | {guess} | {formatted(observed)} | {outcome} |")
    print(f"\n{outcomes['KILLED']} KILLED, {outcomes['survives']} survive.\n")


def table_ratios(arms, group, event, depth_mix):
    both, cold, history, hash_ = (arms[key] for key in group)
    history_ratio = ratio(history, cold, event, depth_mix)
    hash_ratio = ratio(hash_, cold, event, depth_mix)
    both_ratio = ratio(both, cold, event, depth_mix)
    return history_ratio, hash_ratio, both_ratio, interaction(both_ratio, history_ratio, hash_ratio)


def print_tables(arms):
    print("Summed CNT lines: " + ", ".join(f"{key} {arm.lines}" for key, arm in arms.items()) + ".")
    print("Each arm matches the 6,000 positions in games.txt. Rates use actual main plus qsearch nodes.\n")
    print("| Arm | CNT lines | Main nodes | Total nodes |")
    print("|---|---:|---:|---:|")
    for key, arm in arms.items():
        print(f"| {key} | {arm.lines} | {arm.total_main} | {arm.total_nodes} |")

    print("\n## Table 1. Plain rates\n")
    for group in TABLE_GROUPS:
        both, cold, hist, hash_ = group
        print(f"| Counter | {both} / 1k | {cold} / 1k | {hist} / 1k | {hash_} / 1k | "
              f"{hist}/{cold} | {hash_}/{cold} | {both}/{cold} | Interaction |")
        print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for event in EVENTS:
            rates = [rate(arms[key], event) for key in group]
            ratios = table_ratios(arms, group, event, depth_mix=False)
            print("| " + " | ".join([event, *map(formatted, rates + list(ratios))]) + " |")
        print()

    print("## Table 2. Ratios on the cold main-node depth mix\n")
    print("Source events per main node at each depth are weighted by cold main nodes at that depth, "
          "then divided by all cold events. Depths with zero source main nodes are skipped.\n")
    for group in TABLE_GROUPS:
        both, cold, hist, hash_ = group
        print(f"| Counter | {hist}/{cold} | {hash_}/{cold} | {both}/{cold} | Interaction |")
        print("|---|---:|---:|---:|---:|")
        for event in PREDICTION_EVENTS:
            ratios = table_ratios(arms, group, event, depth_mix=True)
            print("| " + " | ".join([event, *map(formatted, ratios)]) + " |")
        print()

    print("## Table 3. Main-node depth shares and history pruning by depth\n")
    print("| Arm | Main-node share d1–8 (%) | History pruning per 1k main nodes d1–5 |")
    print("|---|---|---|")
    for key, arm in arms.items():
        shares = " / ".join(formatted(main_share(arm, d), 3) for d in range(1, 9))
        print(f"| {key} | {shares} | {history_profile(arm)} |")
    if all(history_profile(arms[key]) == expected for key, expected in EXPECTED_COLD_WARM_HISTORY.items()):
        print("\nAll 20 history-pruning depth rates for A2, B2, C2 and D2 match the Job 3 known answers.")
    else:
        for key, expected in EXPECTED_COLD_WARM_HISTORY.items():
            observed = history_profile(arms[key])
            if observed != expected:
                print(f"\nHistory-pruning depth profile mismatch for {key}. Expected {expected}, observed {observed}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for mode in ("old-gate", "tables"):
        subcommand = subcommands.add_parser(mode)
        subcommand.add_argument("games", type=Path)
        subcommand.add_argument("raw_dir", type=Path)
        if mode == "tables":
            subcommand.add_argument("--prediction", type=Path)
    args = parser.parse_args()
    if args.command == "old-gate":
        old_depth_mix_gate(args.games, args.raw_dir)
        return
    arms = read_results(args.games, args.raw_dir)
    if args.prediction is not None:
        print_grades(arms, read_prediction(args.prediction))
    print_tables(arms)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
