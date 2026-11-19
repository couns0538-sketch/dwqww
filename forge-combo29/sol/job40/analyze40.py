#!/usr/bin/env python3
"""Build the Job 40 test matrix and verify raw search records against each baseline."""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
for prior in (HERE.parent / "job39", HERE.parent / "sol-job39"):
    if (prior / "analyze39.py").is_file():
        sys.path.insert(0, str(prior))
        break

from analyze39 import (
    ENGINE_PINS, NET_CHECKSUM, NET_PIN, PC20_PIN, STATUS,
    first_difference, read_records, verify,
)
from generate_draws39 import SETTINGS


LIMITS = {"N2": ("hard", "go nodes 20000", 410001), "N1": ("soft", "go softnodes 2000", 400001)}
CONTROLS = {
    "BASE": ("BASE-b", None, False),
    "EvalSwingMax220": ("EvalSwingMax220", ("EvalSwingMax", 220), False),
    "CaptureFutilityMultiplier275": ("CaptureFutilityMultiplier275", ("CaptureFutilityMultiplier", 275), False),
    "LmrQuietBase101": ("LmrQuietBase/PLUS", ("LmrQuietBase", 101), True),
}
DESIGN_COLUMNS = ("name", "start", "min", "max", "step", "minus_variant", "minus", "plus")


def design_rows():
    rows = []
    for name, start, low, high, step in SETTINGS:
        variant, minus = ("MINUS", start - step) if start - step >= low else ("PLUS2", start + 2 * step)
        plus = start + step
        verify(low <= minus <= high and low <= plus <= high, f"{name}: run outside permitted bounds")
        rows.append(dict(zip(DESIGN_COLUMNS, (name, start, low, high, step, variant, minus, plus), strict=True)))
    verify(len(rows) == len({row["name"] for row in rows}) == 40, "Expected 40 unique settings")
    verify([row["name"] for row in rows if row["minus_variant"] == "PLUS2"] ==
           ["DrawJitter", "CaptureFutilityBase", "FailLowContinuationBonus", "EvalSwingMult"], "Wrong PLUS2 rows")
    return rows


def write_tsv(path, columns, rows):
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow("NA" if row.get(column) in (None, "") else row[column] for column in columns)


def verify_setup(path, meta, option):
    data = path.read_bytes()
    verify(sha256(data).hexdigest() == meta["uci_setup_sha256"], f"{path}: UCI log digest mismatch")
    verify(meta["exe_sha256"] == ENGINE_PINS["r15d"] and meta["external_net_sha256"] == NET_PIN
           and meta["external_net_checksum_expected"] == NET_CHECKSUM, f"{path}: incorrect binary or net")
    log = data.decode().splitlines()
    sent = [line[2:] for line in log if line.startswith("> setoption ")]
    if meta["status"] != "complete":
        return
    verify(sent == meta["settings_sent"] and sent[:2] == ["setoption name Threads value 1", "setoption name Hash value 16"]
           and sha256(("\n".join(sent[2:22]) + "\n").encode()).hexdigest() == PC20_PIN
           and sent[22:24] == [f"setoption name NNUEArchFile value {meta['external_net_file']}",
                               "setoption name NNUEArch value true"]
           and sent[24:] == ([] if option is None else [f"setoption name {option[0]} value {option[1]}"]),
           f"{path}: option schedule differs from declared run")
    exchange = [line for line in log if line.startswith(("> ", "< readyok"))]
    ready = [item for command in sent for item in (f"> {command}", "> isready", "< readyok")]
    verify(exchange == ["> uci", *ready] and meta["settings_ready_count"] == len(sent),
           f"{path}: ready barrier missing after an option")
    active = [line[2:] for line in log if line.startswith("< info string NNUE v3 active:")]
    verify(active == [meta["active_line"]] and f"checksum {NET_CHECKSUM}" in active[0], f"{path}: active net not confirmed")


def read_run(raw, limit, label, option):
    folder = raw / limit / label
    receipt = folder / "run.json"
    mode, search, first = LIMITS[limit]
    last = first + 19
    option_json = None if option is None else {"name": option[0], "value": option[1]}
    core = {"run": f"{limit}/{label}", "limit": limit, "build": "r15d", "option": option_json, "search": search,
            "first_game": first, "last_game": last}
    if not receipt.is_file() or not receipt.stat().st_size:
        wrapper = folder.with_name(f"{folder.name}.driver.out")
        started = wrapper.is_file() or (folder.is_dir() and any(folder.iterdir()))
        core.update(status="unfinalized" if started else "not played", games=0, records=0, nodes=0)
        if wrapper.is_file():
            core["wrapper_output"] = wrapper.read_text(errors="replace").splitlines()
        return core, None
    meta = json.loads(receipt.read_text())
    status = meta["status"]
    verify(status in STATUS and (meta["limit"], meta["mode"], meta["search"], meta["option"]) ==
           (limit, mode, search, option_json) and (meta["first_game"], meta["last_game"], meta["games_requested"]) ==
           (first, last, 20), f"{receipt}: run identity or status differs from schedule")
    verify_setup(folder / "uci-setup.txt", meta, option)
    path = folder / "records.txt"
    data = path.read_bytes()
    digest = sha256(data).hexdigest()
    verify(digest == meta["records_sha256"], f"{path}: records digest mismatch")
    counts, nodes = read_records(data, path, first, last)
    games = meta["games"]
    verify(len(games) == meta["games_completed"] <= 20
           and [game["game"] for game in games] == list(range(first, first + len(games)))
           and (status != "complete" or len(games) == 20)
           and all(counts[game["game"]] == game["plies"] for game in games)
           and set(counts) <= {game["game"] for game in games}, f"{receipt}: completed game list mismatch")
    records = sum(counts.values())
    verify((records, nodes) == (meta["positions_completed"], meta["last_info_nodes_sum"]), f"{receipt}: totals mismatch")
    core.update(status=status, games=len(games), records=records, nodes=nodes, records_sha256=digest,
                record_file=str(path.relative_to(raw)), uci_setup_sha256=meta["uci_setup_sha256"])
    for field in ("error", "stop_reason", "last_command", "last_reply", "stopped_at", "start_utc", "end_utc"):
        core[field] = meta.get(field)
    return core, data


def compare(raw, baseline, other):
    left, data = baseline
    right, candidate = other
    if left["status"] != "complete" or right["status"] != "complete":
        reading = "NOT PLAYED" if right["status"] == "not played" else "INCOMPLETE"
        return {"reading": reading, "games_differ": None, "differing_games": [], "first_difference": None}
    cmp_result = subprocess.run(["cmp", "-s", raw / left["record_file"], raw / right["record_file"]], check=False)
    verify(cmp_result.returncode == (data != candidate), f"{right['run']}: cmp differs from reference bytes")
    if cmp_result.returncode == 0:
        return {"reading": "IDENTICAL", "games_differ": 0, "differing_games": [], "first_difference": None}
    grouped = []
    for contents in (data, candidate):
        games = {}
        for line in contents.splitlines(keepends=True):
            game = int(line.split(b" ", 1)[0])
            games.setdefault(game, []).append(line)
        grouped.append(games)
    a, b = grouped
    different = [game for game in sorted(a.keys() | b.keys()) if a.get(game) != b.get(game)]
    verify(different, f"{right['run']}: unequal records without a differing game")
    return {"reading": "DIFFERS", "games_differ": len(different), "differing_games": different,
            "first_difference": first_difference(data, candidate)}


def analyze_limit(raw, limit, design):
    receipts = {}

    def load(label, option):
        if label not in receipts:
            receipts[label] = read_run(raw, limit, label, option)
        return receipts[label]

    baseline = load("BASE-a", None)
    checks = {}
    for name, (label, option, should_differ) in CONTROLS.items():
        outcome = compare(raw, baseline, load(label, option))
        expected = "DIFFERS" if should_differ else "IDENTICAL"
        checks[name] = {"runs": [f"{limit}/BASE-a", f"{limit}/{label}"], "expected": expected,
                        "passes": outcome["reading"] == expected, **outcome}

    results = []
    for row in design:
        name = row["name"]
        arms = {}
        for arm, variant in (("minus", row["minus_variant"]), ("plus", "PLUS")):
            value = row[arm]
            run = load(f"{name}/{variant}", (name, value))
            arms[arm] = {"variant": variant, "value": value, "run": run[0]["run"], "status": run[0]["status"],
                         **compare(raw, baseline, run)}
        differences = [arm["games_differ"] for arm in arms.values()]
        if any(value is not None and value > 0 for value in differences):
            reading = "LIVE"
        elif differences == [0, 0]:
            reading = "NO CHANGE SEEN"
        elif all(arm["status"] == "not played" for arm in arms.values()):
            reading = "NOT PLAYED"
        else:
            reading = "INCOMPLETE"
        results.append({"name": name, **arms, "reading": reading})
    return {
        "gate": {"passes": all(check["passes"] for check in checks.values()), "checks": checks},
        "settings": results,
        "settings_complete": sum(row["minus"]["status"] == row["plus"]["status"] == "complete" for row in results),
        "live": sum(row["reading"] == "LIVE" for row in results),
        "no_change_seen": [row["name"] for row in results if row["reading"] == "NO CHANGE SEEN"],
        "runs": {run[0]["run"]: run[0] for run in receipts.values()},
    }


def grade(result, forecast, names):
    bounds, expected = forecast["live"], forecast["no_change_seen"]
    verify(isinstance(bounds, list) and len(bounds) == 2 and all(type(x) is int for x in bounds)
           and 0 <= bounds[0] <= bounds[1] <= 40, "Invalid LIVE forecast bounds")
    verify(isinstance(expected, list) and len(set(expected)) == len(expected) and set(expected) <= names,
           "Invalid expected NO CHANGE SEEN list")
    completed = result["gate"]["passes"] and result["settings_complete"] == len(names)
    actual, observed = ((result["live"], result["no_change_seen"]) if completed else (None, None))
    return {
        "live": {"forecast": bounds, "observed": actual,
                 "grade": "ungraded" if actual is None else "met" if bounds[0] <= actual <= bounds[1] else "missed"},
        "no_change_seen": {"forecast": expected, "observed": observed,
                           "grade": "ungraded" if observed is None else "met" if set(expected) == set(observed) else "missed",
                           "forecast_only": None if observed is None else sorted(set(expected) - set(observed)),
                           "observed_only": None if observed is None else sorted(set(observed) - set(expected))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--limit", choices=LIMITS)
    parser.add_argument("--design-tsv", type=Path)
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--runs-tsv", type=Path)
    args = parser.parse_args()
    design = design_rows()
    if args.design_tsv:
        write_tsv(args.design_tsv, DESIGN_COLUMNS, design)
    limits = {limit: analyze_limit(args.raw, limit, design) for limit in ((args.limit,) if args.limit else LIMITS)}
    result = {"limits": limits}
    if args.prediction:
        forecast = json.loads(args.prediction.read_text())
        result["prediction"] = {limit: grade(run, forecast[limit], {row["name"] for row in design})
                                for limit, run in limits.items()}
    if args.runs_tsv:
        columns = ("run", "limit", "build", "search", "first_game", "last_game", "status", "games", "records", "nodes",
                   "records_sha256", "uci_setup_sha256")
        write_tsv(args.runs_tsv, columns, (row for result in limits.values() for row in result["runs"].values()))
    output = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.json:
        args.json.write_text(output)
    print(output, end="")


if __name__ == "__main__":
    main()
