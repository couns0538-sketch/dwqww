#!/usr/bin/env python3
"""Validate Forge Job 5 history-setting experiments and compare their moves against the warm baseline."""

import argparse
from dataclasses import dataclass, field
from fractions import Fraction
import json
from pathlib import Path
from statistics import median
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
COUNTERS = {
    "main_nodes", "q_nodes",
    *(step + suffix for step in STEPS for suffix in ("_tested", "_taken")),
    *(event for extras in EXTRA_EVENTS.values() for event in extras),
}
SETTINGS = {
    "HistoryPruneDepth": (3, 1),
    "HistoryPruneMultiplier": (2220, 200),
    "HistoryBonusQuadratic": (24, 3),
    "HistoryBonusLinear": (54, 6),
    "HistoryBonusMax": (2212, 180),
    "LmrHistoryDivisor": (5643, 500),
    "ProbcutMargin": (180, 15),
    "RfpMargin": (72, 6),
}
REGIMES = ("soft", "hard")
DIRECTIONS = ("minus", "plus")
FIRST_CHANGE_SETTINGS = ("HistoryPruneDepth", "HistoryPruneMultiplier")
JOB3_BASE = {"soft": "A-soft-warm", "hard": "B-hard-warm"}
IDENTITY_FIELDS = (
    "index", "game", "ply", "fen", "depth", "nodes", "bestmove", "cnt", "final_nodes",
    "final_nodes_info",
)
VOLATILE_INFO = re.compile(r" (?:time|nps) [0-9]+(?= |$)")


@dataclass
class Arm:
    moves: list = field(default_factory=list)
    depths: list = field(default_factory=list)
    history: int = 0
    nodes: int = 0


@dataclass
class Comparison:
    changed: int
    searches: int
    percent: Fraction
    history_ratio: Fraction | None
    node_ratio: Fraction | None
    depth_median: int | float


def read_games(path):
    positions = []
    with path.open(encoding="utf-8") as games:
        for game in range(1, 31):
            fields = games.readline().rstrip("\r\n").split("\t")
            if len(fields) != 4 or fields[0] != str(game):
                raise ValueError(f"{path}:{game}: expected game index, FEN, moves and reason")
            _, fen, moves, reason = fields
            moves = moves.split()
            if not fen or not reason or len(moves) != 60:
                raise ValueError(f"{path}:{game}: expected an original FEN and 60 plies")
            positions.extend((game, ply, fen) for ply, _ in enumerate(moves))
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
    return actual_nodes, sum(payload["history_pruning_taken"])


def identity(row):
    return (*[row[key] for key in IDENTITY_FIELDS], VOLATILE_INFO.sub("", row["info"]))


def read_rows(path, positions, prefix=False):
    with path.open(encoding="utf-8") as stream:
        for index, (game, ply, fen) in enumerate(positions, start=1):
            line = stream.readline()
            if not line:
                raise ValueError(f"{path}: expected {len(positions)} rows, found {index - 1}")
            try:
                row = json.loads(line)
                if (row["index"], row["game"], row["ply"], row["fen"]) != (index, game, ply, fen):
                    raise ValueError(f"expected original FEN for game {game}, ply {ply}")
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{index}: {error}") from error
            yield row
        if not prefix and stream.readline():
            raise ValueError(f"{path}: more than the expected {len(positions)} rows")


def read_arm(path, positions, soft):
    arm = Arm()
    for index, row in enumerate(read_rows(path, positions), start=1):
        try:
            actual_nodes, history = read_search(row, soft)
            if not isinstance(row["bestmove"], str) or not row["bestmove"]:
                raise ValueError("missing bestmove")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path}:{index}: {error}") from error
        arm.moves.append(row["bestmove"])
        arm.depths.append(row["depth"])
        arm.nodes += actual_nodes
        arm.history += history
    print(f"Read {path.name}: {len(arm.moves)} rows, {arm.nodes} actual nodes, "
          f"{arm.history} history-pruning events.")
    return arm


def check_identity(path, reference, positions, reference_prefix=False):
    current = read_rows(path, positions)
    old = read_rows(reference, positions, prefix=reference_prefix)
    for row, expected in zip(current, old, strict=True):
        if identity(row) != identity(expected):
            keys = [key for key in IDENTITY_FIELDS if row[key] != expected[key]]
            if VOLATILE_INFO.sub("", row["info"]) != VOLATILE_INFO.sub("", expected["info"]):
                keys.append("info excluding time/NPS")
            raise ValueError(f"{path.name}: first mismatch against {reference.name} at game "
                             f"{row['game']}, ply {row['ply']}, in {', '.join(keys)}")
    print(f"{path.name}: {len(positions)}/{len(positions)} identical to {reference.name}.")


def check_gates(positions, raw, old):
    print("Identity includes game, ply, FEN, depth, nodes, bestmove, final nodes, byte-equal CNT "
          "and last info with only volatile time/NPS omitted.")
    bases = {}
    for regime in REGIMES:
        path = raw / f"base-{regime}.jsonl"
        check_identity(path, old / (JOB3_BASE[regime] + ".jsonl"), positions, reference_prefix=True)
        bases[regime] = read_arm(path, positions, soft=(regime == "soft"))
    for name in SETTINGS:
        check_identity(raw / f"{name}-start-soft.jsonl", raw / "base-soft.jsonl", positions)
    base = bases["soft"]
    zero = read_arm(raw / "HistoryPruneMultiplier-zero-soft.jsonl", positions, soft=True)
    maximum = read_arm(raw / "HistoryPruneMultiplier-max-soft.jsonl", positions, soft=True)
    zero_ratio = divide(history_rate(zero), history_rate(base))
    max_ratio = divide(history_rate(maximum), history_rate(base))
    print(f"History pruning taken per 1k actual nodes: base {formatted(history_rate(base))}, "
          f"zero {formatted(history_rate(zero))} ({formatted(zero_ratio)}×), "
          f"max {formatted(history_rate(maximum))} ({formatted(max_ratio)}×).")
    if zero_ratio is None or zero_ratio <= 2 or max_ratio is None or max_ratio >= 1:
        raise ValueError("HistoryPruneMultiplier controls failed to move in both required directions")
    print("All three Job 5 gates passed.")


def divide(numerator, denominator):
    return numerator / denominator if denominator else None


def history_rate(arm):
    return Fraction(1000 * arm.history, arm.nodes)


def compare(arms, base):
    changed = sum(
        move != expected for arm in arms for move, expected in zip(arm.moves, base.moves, strict=True)
    )
    count = sum(len(arm.moves) for arm in arms)
    nodes = sum(arm.nodes for arm in arms)
    hist = sum(arm.history for arm in arms)
    depths = [depth for arm in arms for depth in arm.depths]
    return Comparison(
        changed=changed, searches=count, percent=Fraction(100 * changed, count),
        history_ratio=divide(Fraction(1000 * hist, nodes), history_rate(base)),
        node_ratio=Fraction(nodes, base.nodes * len(arms)), depth_median=median(depths),
    )


def first_changes(positions, variant, base):
    first = {}
    for (game, ply, _), move, original in zip(positions, variant.moves, base.moves, strict=True):
        if move != original:
            first.setdefault(game, ply)
    bins = ((0, 1), (1, 10), (10, 30), (30, 60))
    counts = tuple(sum(start <= ply < end for ply in first.values()) for start, end in bins)
    return (*counts, 30 - len(first))


def formatted(value):
    return "n/a" if value is None else f"{float(value):.4f}"


def read_prediction(path):
    guesses = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    header = "Setting soft_share_pct hard_share_pct soft_hard_ratio"
    if header not in lines:
        raise ValueError(f"{path}: missing prediction header")
    for line in lines[lines.index(header) + 1:]:
        fields = line.split()
        if not fields:
            break
        name, *values = fields
        if name not in SETTINGS or len(values) != 3 or name in guesses:
            raise ValueError(f"{path}: expected one row with three predictions for {name}")
        targets = tuple(None if value == "zero" else Fraction(value) for value in values)
        if any(target is not None and target <= 0 for target in targets):
            raise ValueError(f"{path}: expected a positive number or the word zero for {name}")
        guesses[name] = tuple(zip(values, targets))
    if guesses.keys() != SETTINGS.keys():
        raise ValueError(f"{path}: missing predictions for {', '.join(sorted(SETTINGS.keys() - guesses.keys()))}")
    return guesses


def print_grades(pooled, predictions):
    print("## Prediction grades\n")
    print("A numeric guess survives within a factor of 1.5. A zero guess requires an observed "
          "zero. A ratio with no hard-budget changes is undefined.\n")
    print("| Setting | Quantity | Guess | Measured | Outcome |")
    print("|---|---|---:|---:|---|")
    factor = Fraction(3, 2)
    killed = survived = 0
    for name in SETTINGS:
        soft, hard = (pooled[name, regime] for regime in REGIMES)
        valid = soft is not None and hard is not None
        values = (soft.percent, hard.percent, divide(soft.percent, hard.percent)) if valid else (None,) * 3
        for label, observed, (guess, target) in zip(("Soft %", "Hard %", "Soft/hard"), values, predictions[name]):
            if not valid:
                outcome = "ungraded"
            else:
                equal = (observed == 0) if target is None else (
                    observed is not None and target / factor <= observed <= target * factor
                )
                killed += not equal
                survived += equal
                outcome = "survives" if equal else "KILLED"
            print(f"| {name} | {label} | {guess} | {formatted(observed)} | {outcome} |")
    print(f"\n{killed} KILLED, {survived} survive, {24 - killed - survived} ungraded.\n")


def load_variant(path, positions, regime, base_meta, name, value):
    metadata_path = path.with_name(path.name + ".meta")
    if not metadata_path.is_file():
        return None, "unfinished: missing metadata"
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    if meta["status"] != "complete":
        return None, f"{meta['status']} after {meta['positions_completed']} rows: {meta.get('error', '')}"
    if meta["positions_completed"] != len(positions) or meta["regime"] != regime:
        raise ValueError(f"{metadata_path}: wrong position count or regime")
    setting = f"setoption name {name} value {value}"
    if (meta["variant"] != {"name": name, "value": str(value)}
            or meta["settings_sent"] != [*base_meta["settings_sent"], setting]
            or meta["variant_reply"][-1:] != ["readyok"]):
        raise ValueError(f"{metadata_path}: expected one accepted override ({setting})")
    if any(meta[key] != base_meta[key] for key in ("exe_sha256", "input_sha256", "search")):
        raise ValueError(f"{metadata_path}: executable, game list or budget differs from baseline")
    return read_arm(path, positions, soft=(regime == "soft")), ""


def print_comparison(heading, entries):
    print(f"## {heading}\n")
    print("| Setting | Direction | Soft changed | Soft % | Hard changed | Hard % | Soft/hard | "
          "History pruning soft/base | History pruning hard/base | Soft nodes/base | Soft median depth |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for name, direction, soft, hard, soft_status, hard_status in entries:
        soft_changed = f"{soft.changed}/{soft.searches}" if soft else soft_status.replace("|", "&#124;")
        hard_changed = f"{hard.changed}/{hard.searches}" if hard else hard_status.replace("|", "&#124;")
        soft_pct, hard_pct = (arm.percent if arm else None for arm in (soft, hard))
        ratio = divide(soft_pct, hard_pct) if soft and hard else None
        print(f"| {name} | {direction} | {soft_changed} | {formatted(soft_pct)} | {hard_changed} | "
              f"{formatted(hard_pct)} | {formatted(ratio)} | {formatted(soft.history_ratio if soft else None)} | "
              f"{formatted(hard.history_ratio if hard else None)} | {formatted(soft.node_ratio if soft else None)} | "
              f"{soft.depth_median if soft else 'n/a'} |")
    print()


def print_tables(positions, raw, prediction):
    base = {r: read_arm(raw / f"base-{r}.jsonl", positions, soft=(r == "soft")) for r in REGIMES}
    base_metadata = {
        r: json.loads((raw / f"base-{r}.jsonl.meta").read_text(encoding="utf-8")) for r in REGIMES
    }
    variants, status = {}, {}
    for name, (start, step) in SETTINGS.items():
        for direction, value in zip(DIRECTIONS, (start - step, start + step)):
            for regime in REGIMES:
                key = name, direction, regime
                variants[key], status[key] = load_variant(
                    raw / (f"{'-'.join(key)}.jsonl"), positions, regime, base_metadata[regime], name, value,
                )

    single, pooled = {}, {}
    for name in SETTINGS:
        for regime in REGIMES:
            arms = [variants[name, direction, regime] for direction in DIRECTIONS]
            for direction, arm in zip(DIRECTIONS, arms):
                single[name, direction, regime] = compare([arm], base[regime]) if arm else None
            pooled[name, regime] = compare(arms, base[regime]) if all(arms) else None
    if prediction is not None:
        print()
        print_grades(pooled, read_prediction(prediction))

    print("History rates divide history-pruning takes by actual main plus qsearch nodes. "
          "Pooled rows sum both directions and compare the corresponding two baseline repeats.\n")
    print_comparison("Table 1. One-step changes", (
        (name, direction, single[name, direction, "soft"], single[name, direction, "hard"],
         status[name, direction, "soft"], status[name, direction, "hard"])
        for name in SETTINGS for direction in DIRECTIONS
    ))
    print_comparison("Table 2. Both directions pooled", (
        (name, "pooled", pooled[name, "soft"], pooled[name, "hard"],
         "direction incomplete", "direction incomplete") for name in SETTINGS
    ))

    print("## Table 3. First changed bestmove by game\n")
    print("First changes are recommendations on a fixed replay. The following search uses the "
          "recorded move. The 30–59 bin retains later first changes separately from unchanged games.\n")
    print("| Setting | Direction | Regime | Ply 0 | Plies 1–9 | Plies 10–29 | Plies 30–59 | No change |")
    print("|---|---|---|---:|---:|---:|---:|---:|")
    for name in FIRST_CHANGE_SETTINGS:
        for direction in DIRECTIONS:
            for regime in REGIMES:
                arm = variants[name, direction, regime]
                counts = first_changes(positions, arm, base[regime]) if arm else ("n/a",) * 5
                print("| " + " | ".join(map(str, (name, direction, regime, *counts))) + " |")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="mode", required=True)
    tables = subcommands.add_parser("tables")
    gates = subcommands.add_parser("gates")
    for command in (tables, gates):
        command.add_argument("games", type=Path)
        command.add_argument("raw", type=Path)
    tables.add_argument("--prediction", type=Path)
    gates.add_argument("job3_raw", type=Path)
    args = parser.parse_args()
    positions = read_games(args.games)
    if args.mode == "gates":
        check_gates(positions, args.raw, args.job3_raw)
    else:
        print_tables(positions, args.raw, args.prediction)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
