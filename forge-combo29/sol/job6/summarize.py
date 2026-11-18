#!/usr/bin/env python3
"""Compare Forge Job 6 tuning steps against matched warm and cold replay baselines."""

import argparse
import csv
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
COUNTERS = {
    "main_nodes", "q_nodes",
    *(step + suffix for step in STEPS for suffix in ("_tested", "_taken")),
    *(event for extras in EXTRA_EVENTS.values() for event in extras),
}
PROTOCOLS = ("warm-soft", "cold-soft", "warm-hard")
SOFT_PROTOCOLS = PROTOCOLS[:2]
JOB5_HARD = {
    "HistoryPruneDepth", "HistoryPruneMultiplier", "HistoryBonusQuadratic",
    "HistoryBonusLinear", "HistoryBonusMax", "LmrHistoryDivisor", "ProbcutMargin",
    "RfpMargin",
}
IDENTITY_FIELDS = ("game", "ply", "fen", "nodes", "bestmove", "cnt")


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


def read_rows(path, positions):
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
        if stream.readline():
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


def read_arm(path, positions, protocol, counters):
    arm = Arm(events={counter: 0 for counter in counters})
    for index, row in enumerate(read_rows(path, positions), start=1):
        try:
            actual_nodes, counts = read_search(row, protocol != "warm-hard", counters)
            if not isinstance(row["bestmove"], str) or not row["bestmove"]:
                raise ValueError("missing bestmove")
            arm.moves.append(row["bestmove"])
            arm.nodes += actual_nodes
            for event, count in counts.items():
                arm.events[event] += count
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"{path}:{index}: {error}") from error
    print(f"Read {path.name}: {len(arm.moves)} rows, {arm.nodes} actual main-plus-qsearch nodes.")
    return arm


def read_meta(path):
    return json.loads(path.with_suffix(path.suffix + ".meta").read_text(encoding="utf-8"))


def check_protocol(meta, protocol, old_job5):
    if old_job5:
        if protocol != "warm-hard" or meta["regime"] != "hard" or meta["search"] != "go nodes 20000":
            raise ValueError("reused Job 5 rows are not the warm hard protocol")
    elif (meta["protocol"] != protocol or meta["opening_only"]
          or meta["warm"] != protocol.startswith("warm-")):
        raise ValueError(f"expected complete {protocol} run")


def open_variant(path, positions, protocol, baseline_meta, setting, value, old_job5=False):
    sidecar = path.with_suffix(path.suffix + ".meta")
    if not path.is_file() or not sidecar.is_file():
        return None, "unfinished: missing raw rows or metadata"
    if sidecar.stat().st_size == 0:
        return None, "unfinished: metadata was not finalized"
    meta = read_meta(path)
    if meta["status"] != "complete":
        count = meta.get("positions_completed", 0)
        return None, f"{meta['status']} after {count} rows: {meta.get('error', '')}"
    try:
        check_protocol(meta, protocol, old_job5)
        if meta["positions_completed"] != len(positions):
            raise ValueError(f"expected {len(positions)} rows")
        override = f"setoption name {setting.name} value {value}"
        if (meta["variant"] != {"name": setting.name, "value": value}
                or meta["settings_sent"] != [*baseline_meta["settings_sent"], override]
                or meta["variant_reply"][-1:] != ["readyok"]):
            raise ValueError(f"expected a single accepted override ({override})")
        if any(meta[key] != baseline_meta[key] for key in ("exe_sha256", "input_sha256", "search")):
            raise ValueError("executable, game list or budget differs from baseline")
    except (KeyError, ValueError) as error:
        raise ValueError(f"{sidecar}: {error}") from error
    return path, ""


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


def pooled_setting(setting, protocol, arms, base):
    if setting.status == "skip":
        return None, f"skipped: start expected {setting.start}, observed {setting.actual}"
    available = [arms[setting.name, direction, protocol] for direction, _ in setting.directions]
    notes = [
        f"{direction} {status}" for (direction, _), (arm, status) in zip(setting.directions, available)
        if arm is None
    ]
    if notes:
        return None, " / ".join(notes)
    counter = setting.counter if protocol == "cold-soft" else "none"
    return pool([arm for arm, _ in available], base, counter), ""


def control_identity(path, base_path, positions):
    same = 0
    first = []
    for row, base in zip(read_rows(path, positions), read_rows(base_path, positions), strict=True):
        differences = [key for key in IDENTITY_FIELDS if row[key] != base[key]]
        if not differences:
            same += 1
        elif len(first) < 5:
            first.append(f"game {row['game']} ply {row['ply']}: {', '.join(differences)}")
    return same, first


def read_prediction(path, tuned):
    names = {setting.name for setting in tuned}
    guesses = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    header = "Setting warm_soft_pct cold_soft_pct"
    if header not in lines:
        raise ValueError(f"{path}: missing prediction header")
    for line in lines[lines.index(header) + 1:]:
        fields = line.split()
        if not fields:
            break
        name, *values = fields
        if name not in names or len(values) != 2 or name in guesses:
            raise ValueError(f"{path}: expected one row with two predictions for {name}")
        targets = tuple(Fraction(0) if value == "zero" else Fraction(value) for value in values)
        if any(target < 0 for target in targets):
            raise ValueError(f"{path}: expected a nonnegative prediction for {name}")
        guesses[name] = tuple(zip(values, targets))
    missing = names - guesses.keys()
    if missing:
        raise ValueError(f"{path}: missing predictions for {', '.join(sorted(missing))}")
    return guesses


def formatted(value):
    return "n/a" if value is None else f"{float(value):.4f}"


def cell(text):
    return str(text).replace("|", "&#124;").replace("\n", " ")


def changed_cell(result, note):
    if result is None:
        return cell(note)
    return f"{result.changed}/{result.searches} ({formatted(result.percent)}%)"


def print_grades(tuned, results, guesses):
    print("## Prediction grades\n")
    print("A numerical guess survives within a factor of 1.5. A zero guess requires zero changed moves.\n")
    print("| Setting | Protocol | Guess % | Observed % | Outcome |")
    print("|---|---|---:|---:|---|")
    factor = Fraction(3, 2)
    killed = survived = 0
    for setting in tuned:
        for protocol, (guess, target) in zip(SOFT_PROTOCOLS, guesses[setting.name]):
            result, note = results[setting.name, protocol]
            if result is None:
                print(f"| {setting.name} | {protocol} | {guess} | n/a | {cell('ungraded: ' + note)} |")
                continue
            matches = target / factor <= result.percent <= target * factor
            survived += matches
            killed += not matches
            verdict = "survives" if matches else "KILLED"
            print(f"| {setting.name} | {protocol} | {guess} | {formatted(result.percent)} | {verdict} |")
    print(f"\n{killed} KILLED, {survived} survive, {2 * len(tuned) - killed - survived} ungraded.\n")


def print_table_1(tuned, results):
    print("## Table 1. All tuned settings\n")
    print("Pooled comparisons include all in-range directions. One-sided settings use 1,800 "
          "searches and two-sided settings use 3,600. Node and counter rates use actual main plus qsearch nodes.\n")
    print("| Setting | Warm soft changed | Cold soft changed | Warm hard changed | Warm soft/hard | "
          "Cold nodes/base | Counter | Cold/base counter rate ratio | Cold counter / 1k | Base cold counter / 1k |")
    print("|---|---|---|---|---:|---:|---|---:|---:|---:|")
    for setting in tuned:
        (warm, wnote), (cold, cnote), (hard, hnote) = [results[setting.name, p] for p in PROTOCOLS]
        warm_hard_ratio = divide(warm.percent, hard.percent) if warm and hard else None
        ratio = formatted(cold.counter_ratio) if cold else "n/a"
        if cold and cold.base_rate == 0:
            ratio = "n/a (base zero)"
        print("| " + " | ".join((
            setting.name, changed_cell(warm, wnote), changed_cell(cold, cnote), changed_cell(hard, hnote),
            formatted(warm_hard_ratio), formatted(cold.node_ratio if cold else None), setting.counter,
            ratio, formatted(cold.counter_rate if cold else None), formatted(cold.base_rate if cold else None),
        )) + " |")
    print()


def print_table_2(tuned, results):
    print("## Table 2. Cold-soft sensitivity ranking, lowest first\n")
    print("| Setting | Cold soft changed | Warm soft changed |")
    print("|---|---|---|")
    def sort_key(setting):
        result = results[setting.name, "cold-soft"][0]
        return (result is None, result.percent if result else 0)
    for setting in sorted(tuned, key=sort_key):
        cold, cnote = results[setting.name, "cold-soft"]
        warm, wnote = results[setting.name, "warm-soft"]
        print(f"| {setting.name} | {changed_cell(cold, cnote)} | {changed_cell(warm, wnote)} |")
    for protocol, threshold in (("cold-soft", 2), ("warm-soft", 5)):
        selected = [
            setting.name for setting in tuned
            if (result := results[setting.name, protocol][0]) is not None and result.percent < threshold
        ]
        print(f"\nBelow {threshold}% {protocol} ({len(selected)}): {', '.join(selected) if selected else 'none'}.")
    print()


def read_baselines(raw, positions, counters):
    arms, metadata, paths = {}, {}, {}
    for protocol in PROTOCOLS:
        path = raw / f"base-{protocol}.jsonl"
        meta = read_meta(path)
        check_protocol(meta, protocol, old_job5=False)
        if (meta["status"] != "complete" or meta["variant"] is not None
                or meta["positions_completed"] != len(positions)):
            raise ValueError(f"{path}: expected a complete baseline")
        arms[protocol] = read_arm(path, positions, protocol, counters if protocol == "cold-soft" else ())
        metadata[protocol], paths[protocol] = meta, path
    return arms, metadata, paths


def print_table_3(positions, controls, raw, metadata, base_paths):
    print("## Table 3. Untuned control identity\n")
    print("| Control | Direction | Warm soft equal | Cold soft equal | First differences (up to five per protocol) |")
    print("|---|---|---|---|---|")
    reads = []
    for setting in controls:
        for direction, value in setting.directions:
            identities, differences = [], []
            for protocol in SOFT_PROTOCOLS:
                if setting.status == "skip":
                    identities.append(f"skipped: expected {setting.start}, observed {setting.actual}")
                    continue
                path = raw / f"{setting.name}-{direction}-{protocol}.jsonl"
                accepted, status = open_variant(path, positions, protocol, metadata[protocol], setting, value)
                if accepted is None:
                    identities.append(cell(status))
                    continue
                same, first = control_identity(accepted, base_paths[protocol], positions)
                identities.append(f"{same}/{len(positions)}")
                differences.extend(f"{protocol} {diff}" for diff in first)
                reads.append(f"Read {accepted.name}: {len(positions)} rows for control identity.")
            print(f"| {setting.name} | {direction} | {' | '.join(identities)} | {cell(' / '.join(differences))} |")
    if reads:
        print("\n" + "\n".join(reads))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--settings", type=Path, default=Path("settings.tsv"))
    parser.add_argument("--job5-raw", type=Path, required=True)
    parser.add_argument("--prediction", type=Path)
    args = parser.parse_args()
    positions = read_games(args.games)
    settings = read_settings(args.settings)
    tuned = [setting for setting in settings if setting.kind == "tuned"]
    controls = [setting for setting in settings if setting.kind == "control"]
    counters = sorted({setting.counter for setting in tuned} - {"none"})
    base, metadata, paths = read_baselines(args.raw, positions, counters)
    arms = {}
    for setting in tuned:
        if setting.status == "skip":
            continue
        for direction, value in setting.directions:
            for protocol in PROTOCOLS:
                job5 = protocol == "warm-hard" and setting.name in JOB5_HARD
                path = (args.job5_raw / f"{setting.name}-{direction}-hard.jsonl" if job5 else
                        args.raw / f"{setting.name}-{direction}-{protocol}.jsonl")
                accepted, status = open_variant(path, positions, protocol, metadata[protocol], setting, value, job5)
                requested = (setting.counter,) if protocol == "cold-soft" and setting.counter != "none" else ()
                arm = read_arm(accepted, positions, protocol, requested) if accepted else None
                arms[setting.name, direction, protocol] = arm, status

    results = {
        (setting.name, protocol): pooled_setting(setting, protocol, arms, base[protocol])
        for setting in tuned for protocol in PROTOCOLS
    }
    print()
    if args.prediction is not None:
        print_grades(tuned, results, read_prediction(args.prediction, tuned))
    print_table_1(tuned, results)
    print_table_2(tuned, results)
    print_table_3(positions, controls, args.raw, metadata, paths)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
