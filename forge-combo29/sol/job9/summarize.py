#!/usr/bin/env python3
"""Summarize Forge Job 9 table ageing, clearing, and KRK replay results."""

import argparse
from hashlib import sha256
from dataclasses import dataclass, field
from fractions import Fraction
import json
from pathlib import Path
import re
import random
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
COUNTERS = {
    "main_nodes", "q_nodes",
    *(step + suffix for step in STEPS for suffix in ("_tested", "_taken")),
    *(event for extras in EXTRA_EVENTS.values() for event in extras),
}
HISTORY = "history_pruning_taken"
MASKS = (1, 2, 5, 7)
BUDGETS = ("soft", "hard")
W_ARMS = ("W1", "W2")
K_CONFIGS = ("count", "default", "decay", "zero")
K_MODES = ("fresh", "stain", "game")
K_PREDICTIONS = (("default", "game"), ("default", "stain"), ("zero", "game"))
PLY_BINS = ((0, 1, "0"), (1, 10, "1–9"), (10, 30, "10–29"), (30, 60, "30–59"))
RAW_DEPTH14 = re.compile(r"^info depth 14\b")
RAW_SCORE = re.compile(r"\bscore (mate|cp) (-?\d+)\b")


@dataclass
class Arm:
    moves: list = field(default_factory=list)
    events: dict = field(default_factory=dict)
    depths: list = field(default_factory=list)
    nodes: int = 0


@dataclass
class Age:
    prune_rate: Fraction
    prune_ratio: Fraction | None
    changed: int
    changed_pct: Fraction
    cold_diff: int
    cold_diff_pct: Fraction
    nodes: int
    nodes_ratio: Fraction
    depth_median: int | float
    bins: tuple
    largest_bins: tuple


@dataclass
class Clearing:
    warm_count: int
    warm_pct: Fraction
    cold_count: int
    cold_pct: Fraction
    prune_rate: Fraction
    nodes: int


@dataclass
class Position:
    index: int
    label: str
    dtm: str
    plies: int
    mate: int
    fen: str


@dataclass
class Krk:
    searches: int
    misses: int
    non_mate7: int
    non_fixture_mate: int
    last_info_nodes: int
    actual_nodes: int
    missed_positions: tuple


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


def read_counters(row, counters):
    raw = row["cnt"]
    if not isinstance(raw, str) or not raw.startswith(COUNTER_PREFIX):
        raise ValueError("missing raw CNT line")
    payload = json.loads(raw.removeprefix(COUNTER_PREFIX))
    if not isinstance(payload, dict) or payload.keys() != COUNTERS:
        raise ValueError("unexpected CNT fields")
    for event in ("main_nodes", "q_nodes", *counters):
        buckets = payload[event]
        if not isinstance(buckets, list) or len(buckets) != 32 or any(type(n) is not int or n < 0 for n in buckets):
            raise ValueError(f"expected 32 nonnegative counts for {event}")
    if any(payload["q_nodes"][1:]):
        raise ValueError("qsearch node counter outside bucket 0")
    actual_nodes = sum(payload["main_nodes"]) + sum(payload["q_nodes"])
    return actual_nodes, {event: sum(payload[event]) for event in counters}


def read_search(row, soft, counters):
    if not (info := INFO_DEPTH.match(row["info"])):
        raise ValueError("missing last info depth line")
    depth, info_nodes = map(int, info.groups())
    if (depth, info_nodes) != (row["depth"], row["nodes"]):
        raise ValueError("row does not agree with its last info line")
    actual_nodes, counts = read_counters(row, counters)
    cap = 8000 if soft else 20000
    if not 0 < actual_nodes <= cap or actual_nodes < info_nodes:
        raise ValueError(f"CNT nodes {actual_nodes} inconsistent with {info_nodes} last info nodes and cap {cap}")
    if soft:
        final = row["final_nodes"]
        if type(final) is not int or actual_nodes != final:
            raise ValueError(f"CNT nodes {actual_nodes} differ from softnodes final nodes {final}")
        if row["final_nodes_info"] != f"info string softnodes nodes {final}":
            raise ValueError("softnodes final value does not agree with its raw UCI line")
    return actual_nodes, counts


def read_arm(path, positions, protocol, counters, prefix=False):
    arm = Arm(events={counter: 0 for counter in counters})
    for index, row in enumerate(read_rows(path, positions, prefix), start=1):
        try:
            actual_nodes, counts = read_search(row, protocol.endswith("-soft"), counters)
            if not isinstance(row["bestmove"], str) or not row["bestmove"]:
                raise ValueError("missing bestmove")
            arm.moves.append(row["bestmove"])
            arm.depths.append(row["depth"])
            arm.nodes += actual_nodes
            for event, count in counts.items():
                arm.events[event] += count
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path}:{index}: {error}") from error
    print(f"Read {path.name}: {len(arm.moves)} rows, {arm.nodes} actual main-plus-qsearch nodes.")
    return arm


def read_meta(path):
    return json.loads(path.with_suffix(path.suffix + ".meta").read_text(encoding="utf-8"))


def divide(numerator, denominator):
    return numerator / denominator if denominator else None


def age_result(arm, default, cold, positions):
    changed = [
        ply for (_, ply, _), best, original in zip(positions, arm.moves, default.moves, strict=True)
        if best != original
    ]
    cold_diff = sum(best != other for best, other in zip(arm.moves, cold.moves, strict=True))
    count = len(positions)
    hist = Fraction(1000 * arm.events[HISTORY], arm.nodes)
    baseline_hist = Fraction(1000 * default.events[HISTORY], default.nodes)
    bins = tuple(sum(start <= ply < end for ply in changed) for start, end, _ in PLY_BINS)
    max_nonopening = max(bins[1:])
    largest = tuple(
        label for (_, _, label), value in zip(PLY_BINS[1:], bins[1:])
        if max_nonopening and value == max_nonopening
    )
    return Age(
        hist, divide(hist, baseline_hist), len(changed), Fraction(100 * len(changed), count),
        cold_diff, Fraction(100 * cold_diff, count), arm.nodes, Fraction(arm.nodes, default.nodes),
        median(arm.depths), bins, largest,
    )


def completion(path):
    sidecar = path.with_suffix(path.suffix + ".meta")
    if not path.is_file() or not sidecar.is_file():
        return None, "unfinished: missing rows or metadata"
    if sidecar.stat().st_size == 0:
        return None, "unfinished: metadata was not finalized"
    meta = read_meta(path)
    if meta["status"] != "complete":
        return None, f"{meta['status']} after {meta.get('positions_completed', 0)} rows: {meta.get('error', '')}"
    return meta, ""


def accept_replay(path, positions, budget, age_mask=None, warming=None):
    meta, note = completion(path)
    if meta is None:
        return False, note
    protocol = f"warm-{budget}"
    if (meta["protocol"] != protocol or meta["positions_completed"] != len(positions)
            or meta["opening_only"]):
        raise ValueError(f"{path}: expected complete {protocol} metadata")
    if age_mask is not None:
        expected = {"HistoryAgeKeep": "729", "HistoryAgeTables": str(age_mask)}
        variants = meta["variants"]
        if age_mask == 7 and len(variants) == 1:
            del expected["HistoryAgeTables"]
        actual = {variant["name"]: variant["value"] for variant in variants}
        if len(variants) != len(actual) or actual != expected:
            raise ValueError(f"{path}: unexpected settings for mask {age_mask}")
    if warming is not None:
        button = "Clear Hash" if warming == "W1" else "ClearWorkers"
        if meta["variants"] or meta["button_commands"] != [f"setoption name {button}"]:
            raise ValueError(f"{path}: expected only the {button} button for {warming}")
    return True, ""


def read_replays(positions, s_dir, w_dir, job6, job8):
    worlds = {
        (state, budget): read_arm(
            job8 / "base-cold-hard.jsonl" if (state, budget) == ("cold", "hard")
            else job6 / f"base-{state}-{budget}.jsonl",
            positions, f"{state}-{budget}", (HISTORY,),
        )
        for state in ("warm", "cold") for budget in BUDGETS
    }
    s_results, w_results = {}, {}
    for budget in BUDGETS:
        warm, cold = worlds["warm", budget], worlds["cold", budget]
        for mask in MASKS:
            path = s_dir / f"mask-{mask}-{budget}.jsonl"
            accepted, note = accept_replay(path, positions, budget, age_mask=mask)
            if not accepted:
                s_results[mask, budget] = None, note
                continue
            arm = read_arm(path, positions, f"warm-{budget}", (HISTORY,))
            s_results[mask, budget] = age_result(arm, warm, cold, positions), ""
        for name in W_ARMS:
            path = w_dir / f"{name}-{budget}.jsonl"
            accepted, note = accept_replay(path, positions, budget, warming=name)
            if not accepted:
                w_results[name, budget] = None, note
                continue
            arm = read_arm(path, positions, f"warm-{budget}", (HISTORY,))
            nwarm = sum(a != b for a, b in zip(arm.moves, warm.moves, strict=True))
            ncold = sum(a != b for a, b in zip(arm.moves, cold.moves, strict=True))
            w_results[name, budget] = Clearing(
                nwarm, Fraction(100 * nwarm, len(positions)),
                ncold, Fraction(100 * ncold, len(positions)),
                Fraction(1000 * arm.events[HISTORY], arm.nodes), arm.nodes,
            ), ""
    return s_results, w_results


def read_krk_fixture(path):
    fixture = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = [field.strip() for field in line.split("|")]
        if len(fields) != 7:
            raise ValueError(f"{path}: expected seven fields in each KRK fixture row")
        label, dtm, _, _, _, _, fen = fields
        match = re.fullmatch(r"(\d+) \(M(\d+)\)", dtm)
        if not match or int(label) != len(fixture):
            raise ValueError(f"{path}: unexpected position index or mate distance")
        plies, mate = map(int, match.groups())
        fen_fields = fen.split()
        if plies != 2 * mate - 1 or len(fen_fields) != 6 or fen_fields[1] != "w":
            raise ValueError(f"{path}: malformed KRK entry at index {label}")
        fixture.append(Position(len(fixture), label, dtm, plies, mate, fen))
    if len(fixture) != 40:
        raise ValueError(f"{path}: wanted 40 KRK positions, found {len(fixture)}")
    return fixture


def krk_order(mode, count):
    if mode == "fresh":
        return [(1, index, index) for index in range(count)]
    order = []
    for pass_ in range(1, 11):
        permuted = list(range(count))
        random.Random(pass_).shuffle(permuted)
        order.extend((pass_, ordinal, index) for ordinal, index in enumerate(permuted))
    return order


def depth14_score(row):
    raw = row["info_depth14"]
    result = None, None
    if raw is not None:
        if not RAW_DEPTH14.match(raw):
            raise ValueError("expected the raw last info depth 14 line")
        if match := RAW_SCORE.search(raw):
            result = match[1], int(match[2])
    if result != (row["score_kind"], row["score_value"]):
        raise ValueError("score columns disagree with the raw depth-14 line")
    return result


def read_krk_rows(path, mode, fixture, fixture_hash):
    meta, note = completion(path)
    if meta is None:
        return None, note
    expected = krk_order(mode, len(fixture))
    if (meta["mode"].lower() != mode or meta["positions_completed"] != len(expected)
            or meta["fixture_sha256"] != fixture_hash):
        raise ValueError(f"{path}: unexpected KRK mode, row count or fixture SHA-256")
    rows = []
    with path.open(encoding="utf-8") as source:
        for number, (pass_, ordinal, index) in enumerate(expected, start=1):
            line = source.readline()
            if not line:
                raise ValueError(f"{path}: row {number} missing")
            try:
                row = json.loads(line)
                position = fixture[index]
                got = (row["mode"].lower(), row["index"], row["pass"], row["shuffle_index"], row["position_index"])
                if got != (mode, number, pass_, ordinal, index):
                    raise ValueError("mode or shuffled visit order differs from protocol")
                if (row["fixture_index"], row["fixture_dtm"], row["fixture_dtm_plies"],
                    row["fixture_mate_moves"], row["fen"]) != (
                    position.label, position.dtm, position.plies, position.mate, position.fen,
                ):
                    raise ValueError("position does not match pinned fixture")
                info = INFO_DEPTH.match(row["info"])
                if not info or tuple(map(int, info.groups())) != (row["depth"], row["nodes"]):
                    raise ValueError("node count does not match last raw info line")
                if not isinstance(row["bestmove"], str) or not row["bestmove"]:
                    raise ValueError("missing bestmove")
                depth14_score(row)
                actual_nodes, _ = read_counters(row, ())
                if actual_nodes <= 0 or actual_nodes < row["nodes"]:
                    raise ValueError("CNT main-plus-qsearch nodes are smaller than last-info nodes or zero")
                row["actual_nodes"] = actual_nodes
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{number}: {error}") from error
            rows.append(row)
        if source.readline():
            raise ValueError(f"{path}: unexpected trailing rows")
    last_info_nodes = sum(row["nodes"] for row in rows)
    actual_nodes = sum(row["actual_nodes"] for row in rows)
    differences = sum(row["actual_nodes"] != row["nodes"] for row in rows)
    if last_info_nodes != meta["last_info_nodes_sum"]:
        raise ValueError(f"{path}: last-info node sum does not match the metadata")
    print(f"Read {path.name}: {len(rows)} searches, {last_info_nodes} last-info nodes, "
          f"{actual_nodes} actual CNT nodes, {differences} searches with different totals.")
    return rows, ""


def krk_result(rows, fixture):
    missing = tuple(f"{row['pass']}:{fixture[row['position_index']].label}"
                    for row in rows if row["score_kind"] != "mate")
    non_sevens = sum(row["score_kind"] == "mate" and row["score_value"] != 7 for row in rows)
    other_exact = sum(
        row["score_kind"] == "mate"
        and row["score_value"] != fixture[row["position_index"]].mate for row in rows
    )
    return Krk(len(rows), len(missing), non_sevens, other_exact, sum(row["nodes"] for row in rows),
               sum(row["actual_nodes"] for row in rows), missing)


def require_same(rows, reference, label):
    fields = ("position_index", "pass", "nodes", "bestmove", "score_kind", "score_value")
    for row, other in zip(rows, reference, strict=True):
        differences = [field for field in fields if row[field] != other[field]]
        if differences:
            raise ValueError(
                f"{label}: first mismatch at pass {row['pass']}, position {row['fixture_index']}. "
                + ", ".join(f"{field} {row[field]!r} vs {other[field]!r}" for field in differences)
            )
    print(f"{label}: {len(rows)}/{len(rows)} equal in nodes, bestmove and depth-14 score.")


def k_gate(fixture_path, raw, fresh_only=False):
    fixture = read_krk_fixture(fixture_path)
    fixture_hash = sha256(fixture_path.read_bytes()).hexdigest()
    for mode in ("fresh",) if fresh_only else K_MODES:
        count, reason = read_krk_rows(raw / f"count-{mode}.jsonl", mode, fixture, fixture_hash)
        if count is None:
            raise ValueError(f"Block K count {mode}: {reason}")
        for config in K_CONFIGS[1:] if mode == "fresh" else ("default",):
            run, reason = read_krk_rows(raw / f"{config}-{mode}.jsonl", mode, fixture, fixture_hash)
            if run is None:
                raise ValueError(f"Block K {config} {mode}: {reason}")
            require_same(run, count, f"{config} {mode} vs count")
    print("Block K FRESH identity gate passed." if fresh_only
          else "Block K FRESH and default-copy identity gates passed.")


def read_krk_results(fixture_path, raw):
    fixture = read_krk_fixture(fixture_path)
    fixture_hash = sha256(fixture_path.read_bytes()).hexdigest()
    results = {}
    for config in K_CONFIGS:
        for mode in K_MODES:
            rows, note = read_krk_rows(raw / f"{config}-{mode}.jsonl", mode, fixture, fixture_hash)
            results[config, mode] = (krk_result(rows, fixture), "") if rows is not None else (None, note)
    return results


def read_prediction(path):
    expected = {
        "S": {(str(mask), b) for mask in MASKS[:-1] for b in BUDGETS},
        "W": {(arm, b) for arm in W_ARMS for b in BUDGETS},
        "K": set(K_PREDICTIONS),
    }
    quantities = {"S": 3, "W": 2, "K": 1}
    predictions = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) < 3 or fields[0] not in expected:
            continue
        block, arm, mode, *values = fields
        key = (arm, mode.lower().removeprefix("warm-"))
        if key not in expected[block]:
            continue
        if len(values) != quantities[block] or (block, *key) in predictions:
            raise ValueError(f"{path}: wrong or duplicated predictions for {block} {key}")
        targets = tuple(Fraction(0) if value == "zero" else Fraction(value) for value in values)
        if any(target < 0 for target in targets):
            raise ValueError(f"{path}: predictions must be nonnegative")
        predictions[block, *key] = tuple(zip(values, targets))
    required = {(block, *key) for block, keys in expected.items() for key in keys}
    if predictions.keys() != required:
        raise ValueError(f"{path}: missing predictions for {sorted(required - predictions.keys())}")
    return predictions


def formatted(value):
    return "n/a" if value is None else f"{float(value):.4f}"


def cell(text):
    return str(text).replace("|", "&#124;").replace("\n", " ")


def print_grades(predictions, s_results, w_results, k_results):
    print("## Prediction grades\n")
    print("A numeric guess survives within a factor of 1.5. A zero guess requires observed zero.\n")
    print("| Block | Arm | Budget or mode | Quantity | Guess | Observed | Outcome |")
    print("|---|---|---|---|---:|---:|---|")
    totals = {"KILLED": 0, "survives": 0, "ungraded": 0}
    factor = Fraction(3, 2)
    for (block, name, context), guesses in predictions.items():
        if block == "S":
            row, note = s_results[int(name), context]
            labels = ("Pruning / default", "Changed vs default %", "Changed vs cold %")
            values = (row.prune_ratio, row.changed_pct, row.cold_diff_pct) if row else (None,) * 3
        elif block == "W":
            row, note = w_results[name, context]
            labels = ("Changed vs warm %", "Changed vs cold %")
            values = (row.warm_pct, row.cold_pct) if row else (None,) * 2
        else:
            row, note = k_results[name, context]
            labels = ("Misses",)
            values = (row.misses if row else None,)
        for label, value, (guess, target) in zip(labels, values, guesses, strict=True):
            if row is None:
                result = "ungraded"
            else:
                result = "survives" if value is not None and target / factor <= value <= target * factor else "KILLED"
            totals[result] += 1
            display = str(value) if block == "K" and value is not None else formatted(value)
            verdict = cell(result + ": " + note) if note else result
            print(f"| {block} | {name} | {context} | {label} | {guess} | {display} | {verdict} |")
    print(f"\n{totals['KILLED']} KILLED, {totals['survives']} survive, {totals['ungraded']} ungraded.\n")


def print_s(results):
    print("## Table S. History-age masks at keep 729\n")
    print("Rates use actual main plus qsearch nodes. Ply bins tally all best moves that differ from the "
          "default in order 0, 1–9, 10–29 and 30–59.\n")
    print("| Mask | Budget | Pruning / 1k | Pruning / default | Changed vs default | Changed vs cold | "
          "Soft actual nodes | Soft nodes/default | Soft median root depth | Changes by ply group | Largest non-opening group |")
    print("|---:|---|---:|---:|---|---|---:|---:|---:|---|---|")
    for mask in MASKS:
        for budget in BUDGETS:
            row, note = results[mask, budget]
            if row is None:
                print(f"| {mask} | {budget} | n/a | n/a | {cell(note)} | n/a | n/a | n/a | n/a | n/a | n/a |")
                continue
            bins = " / ".join(map(str, row.bins))
            largest = ", ".join(row.largest_bins) if row.largest_bins else "none"
            nodes, ratio, depth = ((str(row.nodes), formatted(row.nodes_ratio), str(row.depth_median))
                                   if budget == "soft" else ("–", "–", "–"))
            print(f"| {mask} | {budget} | {formatted(row.prune_rate)} | {formatted(row.prune_ratio)} | "
                  f"{row.changed}/1800 ({formatted(row.changed_pct)}%) | {row.cold_diff}/1800 ({formatted(row.cold_diff_pct)}%) | "
                  f"{nodes} | {ratio} | {depth} | {bins} | {largest} |")
    print()


def print_w(results):
    print("## Table W. Hash or worker clearing\n")
    print("| Arm | Budget | Changed vs warm | Changed vs cold | History pruning / 1k actual nodes | Soft actual nodes |")
    print("|---|---|---|---|---:|---:|")
    for name in W_ARMS:
        for budget in BUDGETS:
            row, note = results[name, budget]
            if row is None:
                print(f"| {name} | {budget} | {cell(note)} | n/a | n/a | n/a |")
                continue
            nodes = str(row.nodes) if budget == "soft" else "–"
            print(f"| {name} | {budget} | {row.warm_count}/1800 ({formatted(row.warm_pct)}%) | "
                  f"{row.cold_count}/1800 ({formatted(row.cold_pct)}%) | {formatted(row.prune_rate)} | {nodes} |")
    print()


def print_k(results):
    print("## Table K. KRK mate reporting at depth 14\n")
    print("Misses have no mate score in the last depth-14 line. The raw fixture has ten positions each at "
          "M7, M6, M5 and M4. A mate other than +7 and a mismatch against the fixture distance are counted "
          "separately. Miss indexes use pass:zero-based fixture index. Last-info nodes come from the last emitted "
          "search info line. Actual nodes sum the CNT main and quiescence searches.\n")
    print("| Config | Mode | Misses | Mates other than +7 | Mates differing from fixture DTM | "
          "Last-info nodes | Actual CNT nodes | Missed positions |")
    print("|---|---|---|---:|---:|---:|---:|---|")
    for config in K_CONFIGS:
        for mode in K_MODES:
            row, note = results[config, mode]
            if row is None:
                print(f"| {config} | {mode.upper()} | {cell(note)} | n/a | n/a | n/a | n/a | n/a |")
                continue
            print(f"| {config} | {mode.upper()} | {row.misses}/{row.searches} | {row.non_mate7} | "
                  f"{row.non_fixture_mate} | {row.last_info_nodes} | {row.actual_nodes} | "
                  f"{', '.join(row.missed_positions) or 'none'} |")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    gate = subcommands.add_parser("k-gate")
    gate.add_argument("krk", type=Path)
    gate.add_argument("k_raw", type=Path)
    gate.add_argument("--fresh-only", action="store_true")
    tables = subcommands.add_parser("tables")
    for name in ("games", "krk", "s_raw", "w_raw", "k_raw"):
        tables.add_argument(name, type=Path)
    tables.add_argument("--job6-raw", type=Path, required=True)
    tables.add_argument("--job8-raw", type=Path, required=True)
    tables.add_argument("--prediction", type=Path)
    args = parser.parse_args()
    if args.command == "k-gate":
        k_gate(args.krk, args.k_raw, args.fresh_only)
        return
    positions = read_games(args.games)
    s_results, w_results = read_replays(positions, args.s_raw, args.w_raw, args.job6_raw, args.job8_raw)
    k_results = read_krk_results(args.krk, args.k_raw)
    print()
    if args.prediction is not None:
        print_grades(read_prediction(args.prediction), s_results, w_results, k_results)
    print_s(s_results)
    print_w(w_results)
    print_k(k_results)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
