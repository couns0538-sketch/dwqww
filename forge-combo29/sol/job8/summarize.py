#!/usr/bin/env python3
"""Summarize Forge Job 8 history ageing and the cold hard-budget tuning-step map."""

import argparse
import csv
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
COUNTERS = {
    "main_nodes", "q_nodes",
    *(step + suffix for step in STEPS for suffix in ("_tested", "_taken")),
    *(event for extras in EXTRA_EVENTS.values() for event in extras),
}
HISTORY = "history_pruning_taken"
KEEPS = (1024, 896, 768, 512, 256, 0)
BUDGETS = ("soft", "hard")
PLY_BINS = ((0, 1, "0"), (1, 10, "1–9"), (10, 30, "10–29"), (30, 60, "30–59"))
IDENTITY_FIELDS = ("game", "ply", "fen", "nodes", "bestmove", "cnt")
JOB6_COUNT = re.compile(r"^(\d+)/(\d+) \(([0-9.]+)%\)$")


@dataclass
class Setting:
    name: str
    kind: str
    status: str
    start: str
    actual: str
    counter: str
    directions: tuple


@dataclass
class Arm:
    moves: list = field(default_factory=list)
    events: dict = field(default_factory=dict)
    depths: list = field(default_factory=list)
    nodes: int = 0


@dataclass
class Pooled:
    changed: int
    searches: int
    percent: Fraction
    node_ratio: Fraction
    counter_rate: Fraction | None
    base_rate: Fraction | None
    counter_ratio: Fraction | None


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


def read_settings(path):
    settings = []
    with path.open(newline="", encoding="utf-8") as settings_file:
        seen = set()
        for number, row in enumerate(csv.DictReader(settings_file, delimiter="\t"), start=2):
            try:
                name = row["name"]
                if not name or name in seen:
                    raise ValueError("missing or duplicate setting name")
                seen.add(name)
                kind = row["kind"]
                if kind != "tuned" and ("control" in kind or "untuned" in kind):
                    kind = "control"
                if kind not in ("tuned", "control") or row["status"] not in ("run", "skip"):
                    raise ValueError(f"unknown kind or status for {name}")
                counter = row["counter"]
                if counter in ("-", "none", ""):
                    counter = "none"
                if counter not in COUNTERS and counter != "none":
                    raise ValueError(f"unrecognized counter {counter!r} for {name}")
                directions = tuple(
                    (direction, row[column])
                    for direction, column in (("minus", "lower"), ("plus", "upper")) if row[column] != "-"
                )
                if row["status"] == "run" and not directions:
                    raise ValueError(f"no eligible direction for {name}")
                settings.append(Setting(name, kind, row["status"], row["start"], row["actual"], counter, directions))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{number}: {error}") from error
    tuned = sum(setting.kind == "tuned" for setting in settings)
    if tuned != 40 or len(settings) - tuned != 5:
        raise ValueError(f"{path}: expected 40 tuned settings and 5 controls, got {tuned} and {len(settings) - tuned}")
    return settings


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


def read_search(row, soft, counters):
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
    for event in ("main_nodes", "q_nodes", *counters):
        buckets = payload[event]
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
    return actual_nodes, {event: sum(payload[event]) for event in counters}


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


def pool(arms, base, counter):
    changed = sum(
        move != expected for arm in arms for move, expected in zip(arm.moves, base.moves, strict=True)
    )
    searches = sum(len(arm.moves) for arm in arms)
    nodes = sum(arm.nodes for arm in arms)
    if counter == "none":
        count_rate = base_rate = ratio = None
    else:
        count_rate = Fraction(1000 * sum(arm.events.get(counter, 0) for arm in arms), nodes)
        base_rate = Fraction(1000 * base.events.get(counter, 0), base.nodes)
        ratio = divide(count_rate, base_rate)
    return Pooled(
        changed, searches, Fraction(100 * changed, searches),
        Fraction(nodes, base.nodes * len(arms)), count_rate, base_rate, ratio,
    )


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


def read_job6_counts(path, tuned):
    expected = {setting.name: setting for setting in tuned}
    counts = {}
    inside = False
    cold_column = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Table 1."):
            inside = True
        elif inside and line.startswith("## "):
            break
        if not inside or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells[0] == "Setting":
            cold_column = cells.index("Cold soft changed")
            continue
        name = cells[0]
        if name not in expected:
            continue
        if cold_column is None or name in counts:
            raise ValueError(f"{path}: missing table header or duplicate {name}")
        if not (match := JOB6_COUNT.fullmatch(cells[cold_column])):
            raise ValueError(f"{path}: no exact Job 6 cold-soft count for {name}")
        changed, total = int(match[1]), int(match[2])
        if total != 1800 * len(expected[name].directions) or not 0 <= changed <= total:
            raise ValueError(f"{path}: wrong cold-soft denominator or count for {name}")
        if formatted(Fraction(100 * changed, total)) != match[3]:
            raise ValueError(f"{path}: count and displayed percentage disagree for {name}")
        counts[name] = changed, total
    if counts.keys() != expected.keys():
        raise ValueError(f"{path}: missing prior cold-soft counts for {', '.join(sorted(expected.keys() - counts.keys()))}")
    return counts


def run_metadata(path, protocol, positions, variant, baseline_meta=None):
    sidecar = path.with_suffix(path.suffix + ".meta")
    if not path.is_file() or not sidecar.is_file():
        return None, "unfinished: missing rows or metadata"
    if sidecar.stat().st_size == 0:
        return None, "unfinished: metadata was not finalized"
    meta = read_meta(path)
    if meta["status"] != "complete":
        return None, f"{meta['status']} after {meta.get('positions_completed', 0)} rows: {meta.get('error', '')}"
    if (meta["protocol"] != protocol or meta["opening_only"]
            or meta["positions_completed"] != len(positions) or meta["variant"] != variant):
        raise ValueError(f"{sidecar}: incorrect protocol, position count or override")
    if variant is not None:
        setting = f"setoption name {variant['name']} value {variant['value']}"
        if meta["variant_reply"][-1:] != ["readyok"] or meta["settings_sent"][-1:] != [setting]:
            raise ValueError(f"{sidecar}: override not followed by readyok")
        if baseline_meta is not None and meta["settings_sent"][:-1] != baseline_meta["settings_sent"]:
            raise ValueError(f"{sidecar}: PC20 options differ from baseline")
    if baseline_meta is not None and any(
        meta[key] != baseline_meta[key] for key in ("exe_sha256", "input_sha256", "search")
    ):
        raise ValueError(f"{sidecar}: executable, game list or budget differs from baseline")
    return meta, ""


def read_age_results(age_raw, positions, old_soft, old_hard):
    cold_refs = {
        "soft": read_arm(old_soft, positions, "cold-soft", ()),
        "hard": read_arm(old_hard, positions, "cold-hard", (), prefix=True),
    }
    results = {}
    for budget in BUDGETS:
        protocol = f"warm-{budget}"
        path = age_raw / f"keep-1024-{protocol}.jsonl"
        baseline_meta, unavailable = run_metadata(path, protocol, positions, None)
        if baseline_meta is None:
            for keep in KEEPS:
                results[keep, budget] = None, "default " + unavailable
            continue
        default = read_arm(path, positions, protocol, (HISTORY,))
        results[1024, budget] = age_result(default, default, cold_refs[budget], positions), ""
        for keep in KEEPS[1:]:
            path = age_raw / f"keep-{keep}-{protocol}.jsonl"
            variant = {"name": "HistoryAgeKeep", "value": str(keep)}
            meta, reason = run_metadata(path, protocol, positions, variant, baseline_meta)
            if meta is None:
                results[keep, budget] = None, reason
                continue
            arm = read_arm(path, positions, protocol, (HISTORY,))
            results[keep, budget] = age_result(arm, default, cold_refs[budget], positions), ""
    return results


def check_hard_baseline(path, reference, positions):
    for row, old in zip(read_rows(path, positions), read_rows(reference, positions, prefix=True), strict=True):
        if any(row[key] != old[key] for key in IDENTITY_FIELDS):
            raise ValueError(f"Block D baseline differs from Job 3 at game {row['game']} ply {row['ply']}")
    print(f"Block D cold hard base agrees with Job 3 D on {len(positions)}/{len(positions)} rows.")


def read_block_d(raw, positions, tuned, old_hard):
    path = raw / "base-cold-hard.jsonl"
    meta, reason = run_metadata(path, "cold-hard", positions, None)
    if meta is None:
        return {s.name: (None, "base " + reason) for s in tuned}
    check_hard_baseline(path, old_hard, positions)
    counters = sorted({setting.counter for setting in tuned} - {"none"})
    base = read_arm(path, positions, "cold-hard", counters)
    results = {}
    for setting in tuned:
        if setting.status == "skip":
            results[setting.name] = None, f"skipped: start expected {setting.start}, observed {setting.actual}"
            continue
        arms, notes = [], []
        for direction, value in setting.directions:
            path = raw / f"{setting.name}-{direction}-cold-hard.jsonl"
            variant = {"name": setting.name, "value": value}
            variant_meta, reason = run_metadata(path, "cold-hard", positions, variant, meta)
            if variant_meta is None:
                notes.append(f"{direction} {reason}")
                continue
            requested = (setting.counter,) if setting.counter != "none" else ()
            arms.append(read_arm(path, positions, "cold-hard", requested))
        results[setting.name] = (None, " / ".join(notes)) if notes else (pool(arms, base, setting.counter), "")
    return results


def read_prediction(path, tuned):
    guesses, named = {}, None
    names = {setting.name for setting in tuned}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("below 2% cold hard:"):
            text = line.partition(":")[2].strip().rstrip(".").replace(chr(96), "")
            named = set() if text.lower() == "none" else {entry.strip() for entry in text.split(",")}
            if not named <= names:
                raise ValueError(f"{path}: unknown below-2% setting(s): {', '.join(sorted(named - names))}")
            continue
        fields = line.split()
        if not fields or fields[0] not in ("896", "768", "512", "256"):
            continue
        if len(fields) != 5:
            raise ValueError(f"{path}: expected keep, budget and three predictions")
        keep, budget, *values = fields
        key = int(keep), budget.removeprefix("warm-")
        if key[1] not in BUDGETS or key in guesses:
            raise ValueError(f"{path}: duplicate or invalid prediction key {key}")
        targets = tuple(Fraction(0) if value == "zero" else Fraction(value) for value in values)
        if any(target < 0 for target in targets):
            raise ValueError(f"{path}: expected nonnegative predictions")
        guesses[key] = tuple(zip(values, targets))
    if len(guesses) != 8 or named is None:
        raise ValueError(f"{path}: expected eight keep/budget predictions and the below-2% list")
    return guesses, named


def formatted(value):
    return "n/a" if value is None else f"{float(value):.4f}"


def cell(text):
    return str(text).replace("|", "&#124;").replace("\n", " ")


def print_grades(ages, cold_hard, predictions):
    guesses, named = predictions
    print("## Prediction grades\n")
    print("Each numeric forecast survives within a factor of 1.5. A zero guess requires observed zero.\n")
    print("| Keep | Budget | Quantity | Guess | Observed | Outcome |")
    print("|---:|---|---|---:|---:|---|")
    factor = Fraction(3, 2)
    killed = survived = 0
    for keep in (896, 768, 512, 256):
        for budget in BUDGETS:
            result, note = ages[keep, budget]
            values = (result.prune_ratio, result.changed_pct, result.cold_diff_pct) if result else (None,) * 3
            for label, value, (guess, target) in zip(
                ("Pruning / default", "Changed vs default %", "Changed vs cold %"), values, guesses[keep, budget],
            ):
                if result is None:
                    verdict = "ungraded: " + note
                else:
                    ok = value is not None and target / factor <= value <= target * factor
                    survived += ok
                    killed += not ok
                    verdict = "survives" if ok else "KILLED"
                print(f"| {keep} | {budget} | {label} | {guess} | {formatted(value)} | {cell(verdict)} |")
    print(f"\n{killed} KILLED, {survived} survive, {24 - killed - survived} ungraded.\n")
    measured = {name for name, (result, _) in cold_hard.items() if result is not None}
    selected = {name for name in measured if cold_hard[name][0].percent < 2}
    all_below = named & measured
    def names(items):
        return ", ".join(sorted(items)) if items else "none"
    print(f"Below-2% cold-hard forecast: {len(all_below & selected)} hits.")
    print(f"Predicted below, measured at or above 2% ({len(all_below - selected)}): {names(all_below - selected)}.")
    print(f"Measured below, not predicted ({len(selected - named)}): {names(selected - named)}.")
    print(f"Predicted below but unmeasured ({len(named - measured)}): {names(named - measured)}.\n")


def print_age_results(results):
    print("## Table A. Warm replays by history retention and budget\n")
    print("Rates use actual main plus qsearch nodes. The largest ply group is by raw number "
          "of changed best moves against default. Counts are grouped by ply 0, 1–9, 10–29 and 30–59.\n")
    print("| Keep | Budget | Pruning / 1k | Pruning / default | Changed vs default | Changed vs cold | "
          "Soft actual nodes | Soft nodes/default | Soft median root depth | Changes by ply group | Largest non-opening group |")
    print("|---:|---|---:|---:|---|---|---:|---:|---:|---|---|")
    for keep in KEEPS:
        for budget in BUDGETS:
            row, note = results[keep, budget]
            if row is None:
                print(f"| {keep} | {budget} | n/a | n/a | {cell(note)} | n/a | n/a | n/a | n/a | n/a | n/a |")
                continue
            bins = " / ".join(map(str, row.bins))
            largest = ", ".join(row.largest_bins) if row.largest_bins else "none"
            nodes, ratio, depth = ((str(row.nodes), formatted(row.nodes_ratio), str(row.depth_median))
                                   if budget == "soft" else ("–", "–", "–"))
            print(f"| {keep} | {budget} | {formatted(row.prune_rate)} | {formatted(row.prune_ratio)} | "
                  f"{row.changed}/1800 ({formatted(row.changed_pct)}%) | {row.cold_diff}/1800 ({formatted(row.cold_diff_pct)}%) | "
                  f"{nodes} | {ratio} | {depth} | {bins} | {largest} |")
    print()


def print_block_d(results, prior, tuned):
    print("## Table D. Cold hard-budget tuning-step sensitivity, lowest first\n")
    print("Cold-soft percentages are recomputed from the exact changed/total counts in Job 6 Table 1. "
          "Cold-hard rates use actual main plus qsearch nodes.\n")
    print("| Setting | Cold hard changed | Job 6 cold soft changed | Cold hard nodes/base | Counter | "
          "Counter rate/base | Counter / 1k | Baseline counter / 1k |")
    print("|---|---|---|---:|---|---:|---:|---:|")
    def sort_key(setting):
        result = results[setting.name][0]
        return result is None, result.percent if result else 0
    for setting in sorted(tuned, key=sort_key):
        result, note = results[setting.name]
        changed, count = prior[setting.name]
        previous = f"{changed}/{count} ({formatted(Fraction(100 * changed, count))}%)"
        if result is None:
            print(f"| {setting.name} | {cell(note)} | {previous} | n/a | {setting.counter} | n/a | n/a | n/a |")
            continue
        ratio = "n/a (base zero)" if result.base_rate == 0 else formatted(result.counter_ratio)
        print(f"| {setting.name} | {result.changed}/{result.searches} ({formatted(result.percent)}%) | "
              f"{previous} | {formatted(result.node_ratio)} | {setting.counter} | {ratio} | "
              f"{formatted(result.counter_rate)} | {formatted(result.base_rate)} |")
    below = [s.name for s in sorted(tuned, key=sort_key)
             if (result := results[s.name][0]) is not None and result.percent < 2]
    print(f"\nBelow 2% cold hard ({len(below)}): {', '.join(below) or 'none measured'}.")
    unmeasured = sum(result is None for result, _ in results.values())
    if unmeasured:
        print(f"Cold-hard results unavailable for {unmeasured} settings.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    parser.add_argument("age_raw", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--settings", type=Path, default=Path("settings.tsv"))
    parser.add_argument("--job6-raw", type=Path, required=True)
    parser.add_argument("--job6-summary", type=Path, required=True)
    parser.add_argument("--job3-raw", type=Path, required=True)
    parser.add_argument("--prediction", type=Path)
    args = parser.parse_args()
    positions = read_games(args.games)
    tuned = [setting for setting in read_settings(args.settings) if setting.kind == "tuned"]
    previous = read_job6_counts(args.job6_summary, tuned)
    old_soft = args.job6_raw / "base-cold-soft.jsonl"
    old_hard = args.job3_raw / "D-hard-cold.jsonl"
    ages = read_age_results(args.age_raw, positions, old_soft, old_hard)
    cold_hard = read_block_d(args.raw, positions, tuned, old_hard)
    print()
    if args.prediction is not None:
        print_grades(ages, cold_hard, read_prediction(args.prediction, tuned))
    print_age_results(ages)
    print_block_d(cold_hard, previous, tuned)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
