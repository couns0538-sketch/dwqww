#!/usr/bin/env python3
"""Verify Job 37 run receipts and calculate paired B/A wall and engine CPU ratios."""

import argparse
from hashlib import sha256
from itertools import zip_longest
import json
import math
from pathlib import Path
import re
import statistics


PLAN = {"C37": 4, "W0": 1, "T1": 16, "P1": 8}
CHECKSUM = "30ab43b4ba5db5f3"
ENGINE_SHA256 = {
    "r15d": "9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671",
    "kF": "c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb",
}
NET_SHA256 = "c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7"
MOVE = re.compile(rb"[a-h][1-8][a-h][1-8][qrbn]?")
MINIMUM_CONTROL_RATIO = 1.10
ORDERS = ("AB", "BA", "BA", "AB")
# The 0.975 Student t quantiles for df=1 through 15, verified with scipy.stats.t.ppf.
T_CRITICAL = (
    12.706204736174694, 4.302652729749462, 3.1824463052837078, 2.7764451051977934,
    2.5705818356363146, 2.4469118511449786, 2.364624251592784, 2.306004135204166,
    2.262157162798205, 2.228138851986274, 2.200985160091639, 2.1788128296672284,
    2.1603686564627913, 2.144786687917804, 2.131449545559776,
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run_spec(stage, block, arm):
    base = 199000 if stage == "W0" else 200000 + 1000 * block
    build = "kF" if stage in ("W0", "T1") and arm == "B" else "r15d"
    nodes = 3000 if stage == "C37" and arm == "B" else 2000
    return base, build, nodes


def record_totals(contents, workers, base, path):
    previous = (base - 1, -1)
    count = node_sum = games = 0
    require(not contents or contents.endswith(b"\n"), f"{path}: missing final newline")
    for line in contents.splitlines():
        game, ply, move, nodes = line.split()
        game, ply, nodes = int(game), int(ply), int(nodes)
        require(base <= game < base + workers * 25 and 8 <= ply < 300 and nodes > 0
                and MOVE.fullmatch(move), f"{path}: invalid record at line {count + 1}")
        expected_ply = previous[1] + 1 if game == previous[0] else 8
        require(game >= previous[0] and ply == expected_ply,
                f"{path}: unordered, repeated or skipped ply at line {count + 1}")
        games += game != previous[0]
        count += 1
        node_sum += nodes
        previous = game, ply
    return count, node_sum, games


def run_receipt(raw, stage, block, arm, workers):
    folder = raw / stage / f"block-{block:02d}" / arm
    receipt_path = folder / "run.json"
    base, build, nodes = run_spec(stage, block, arm)
    if not receipt_path.is_file():
        if folder.is_dir() and any(folder.iterdir()):
            return {"status": "unfinalized", "base": base, "build": build, "nodes": nodes}, None
        return {"status": "not done", "base": base, "build": build, "nodes": nodes}, None
    receipt = json.loads(receipt_path.read_bytes())
    status = receipt["status"]
    require(status in ("complete", "interrupted", "failed"), f"{receipt_path}: invalid run status {status!r}")
    require((receipt["base"], receipt["build"], receipt["nodes"]) == (base, build, nodes),
            f"{receipt_path}: run build, base or node limit differs from the declared schedule")
    require(receipt["engine_sha256"] == ENGINE_SHA256[build] and receipt["net_sha256"] == NET_SHA256,
            f"{receipt_path}: artifact digest differs from Job 34")
    actual_workers = receipt["workers"]
    require(type(actual_workers) is int and actual_workers > 0 and (workers is None or actual_workers == workers),
            f"{receipt_path}: worker count differs from nproc")
    complete = status == "complete"
    expected_games = 25 * actual_workers
    games = receipt["games_completed"]
    require(receipt["games_requested"] == expected_games and 0 <= games <= expected_games
            and (not complete or games == expected_games), f"{receipt_path}: inconsistent game counts")
    wall = receipt.get("wall_seconds")
    cpu = receipt.get("engine_cpu_seconds")
    if complete:
        require(all(type(value) in (int, float) and math.isfinite(value) and value > 0 for value in (wall, cpu)),
                f"{receipt_path}: completed run lacks positive timings")
        require(wall == receipt["monotonic_stop"] - receipt["monotonic_start"],
                f"{receipt_path}: monotonic clock does not match wall duration")
        ticks = receipt["engine_ticks"]
        require(sorted(tick["worker"] for tick in ticks) == list(range(actual_workers)) and
                cpu == sum(tick["user"] + tick["system"] for tick in ticks) / receipt["ticks_per_second"],
                f"{receipt_path}: recorded engine CPU does not match the /proc ticks")

    contents = None
    node_sum = record_games = None
    log_paths = sorted(folder.glob("worker*.out"))
    if complete:
        require(len(log_paths) == actual_workers, f"{receipt_path}: missing worker logs")
        for path in log_paths:
            require(any("NNUE v3 active" in line and f"checksum {CHECKSUM}" in line
                        for line in path.read_text().splitlines()), f"{path}: missing active net receipt")
    records_path = folder / "records.tsv"
    if complete or records_path.is_file():
        contents = records_path.read_bytes()
        require(sha256(contents).hexdigest() == receipt["record_sha256"],
                f"{records_path}: SHA-256 differs from run receipt")
        count, node_sum, record_games = record_totals(contents, actual_workers, base, records_path)
        require(count == receipt["records"], f"{records_path}: line count differs from run receipt")
    return {
        "path": str(folder.relative_to(raw)), "status": status, "base": base, "build": build, "nodes": nodes,
        "workers": actual_workers, "games": games, "games_requested": expected_games, "wall_seconds": wall,
        "engine_cpu_seconds": cpu, "records": receipt.get("records"), "record_sha256": receipt.get("record_sha256"),
        "node_sum": node_sum, "games_with_records": record_games, "started_utc": receipt.get("started_utc"),
        "finished_utc": receipt.get("finished_utc"),
    }, contents


def first_difference(left, right):
    for number, (a, b) in enumerate(zip_longest(left.splitlines(keepends=True), right.splitlines(keepends=True)), 1):
        if a != b:
            return {"line": number, "A": None if a is None else a.removesuffix(b"\n").decode(),
                    "B": None if b is None else b.removesuffix(b"\n").decode()}
    raise ValueError("different validated records have no differing line")


def ratio_summary(rows, field):
    ratios = [row["B"][field] / row["A"][field] for row in rows]
    if not ratios:
        return None
    count = len(ratios)
    degrees = count - 1
    mean = statistics.mean(ratios)
    interval = None
    if degrees:
        error = T_CRITICAL[degrees - 1] * statistics.stdev(ratios) / math.sqrt(count)
        interval = [mean - error, mean + error]
    return {
        "median": statistics.median(ratios), "pooled": math.fsum(row["B"][field] for row in rows)
        / math.fsum(row["A"][field] for row in rows), "mean": mean, "ci95": interval,
        "degrees_of_freedom": degrees if degrees else None, "blocks": count,
        "below_one": sum(ratio < 1 for ratio in ratios),
    }


def analyze_stage(raw, stage, workers):
    blocks = []
    for block in range(1, PLAN[stage] + 1):
        a, left = run_receipt(raw, stage, block, "A", workers)
        b, right = run_receipt(raw, stage, block, "B", workers)
        row = {"block": block, "base": a["base"], "order": ORDERS[(block - 1) % len(ORDERS)], "A": a, "B": b,
               "complete": False, "eligible": False, "record_identity": "not compared",
               "first_difference": None, "wall_ratio": None, "cpu_ratio": None}
        if a["status"] == b["status"] == "complete":
            require(a["workers"] == b["workers"], f"{stage} block {block}: workers differ between arms")
            row["complete"] = True
            if stage != "C37":
                row["record_identity"] = "identical" if left == right else "different"
                if left != right:
                    row["first_difference"] = first_difference(left, right)
            row["eligible"] = stage == "C37" or (stage in ("T1", "P1") and left == right)
            if row["eligible"]:
                row["wall_ratio"] = b["wall_seconds"] / a["wall_seconds"]
                row["cpu_ratio"] = b["engine_cpu_seconds"] / a["engine_cpu_seconds"]
        blocks.append(row)
    eligible = [row for row in blocks if row["eligible"]]
    return {
        "planned_blocks": len(blocks), "complete_blocks": sum(row["complete"] for row in blocks),
        "eligible_blocks": len(eligible), "blocks": blocks, "wall": ratio_summary(eligible, "wall_seconds"),
        "cpu": ratio_summary(eligible, "engine_cpu_seconds"),
    }


def reading(interval, reference):
    if interval is None:
        return "NOT DONE"
    if interval[1] < reference[0]:
        return "PAYS"
    if interval[0] > reference[1]:
        return "COSTS"
    return "NOT SEEN"


def verdict(stages):
    t1 = stages.get("T1", {}).get("wall")
    p1 = stages.get("P1", {}).get("wall")
    t1_interval = t1["ci95"] if t1 else None
    p1_interval = p1["ci95"] if p1 else None
    unit = [1, 1]
    unit_t1 = reading(t1_interval, unit)
    p1_reading = reading(p1_interval, unit)
    reference = p1_interval if p1_reading in ("PAYS", "COSTS") else unit
    return {
        "T1": reading(t1_interval, reference), "P1": p1_reading, "T1_against_one": unit_t1,
        "T1_reference_wall_interval": reference, "noise_adjusted": reference != unit,
    }


def grade(stages, readings, forecast):
    grades = {}
    for stage in ("T1", "P1"):
        key = f"{stage}_pooled_wall_ratio"
        if key in forecast:
            lo, hi = forecast[key]
            require(lo <= hi, f"{key}: inverted forecast range")
            wall = stages.get(stage, {}).get("wall")
            observed = wall["pooled"] if wall else None
            grades[key] = {"forecast": forecast[key], "observed": observed,
                           "grade": "ungraded" if observed is None else "met" if lo <= observed <= hi else "missed"}
        key = f"{stage}_reading"
        if key in forecast:
            expected = forecast[key]
            require(expected in ("PAYS", "COSTS", "NOT SEEN"), f"{key}: invalid forecast reading")
            observed = readings[stage]
            grades[key] = {"forecast": expected, "observed": observed,
                           "grade": "ungraded" if observed == "NOT DONE" else "met" if expected == observed else "missed"}
    return grades


def write_runs_table(stages, target):
    columns = ("stage", "block", "arm", "build", "base", "nodes", "workers", "status", "games",
               "wall_seconds", "engine_cpu_seconds", "records", "record_sha256", "node_sum")
    with target.open("w") as source:
        print(*columns, sep="\t", file=source)
        for stage, result in stages.items():
            for row in result["blocks"]:
                for arm in row["order"]:
                    run = row[arm]
                    if run["status"] == "not done":
                        continue
                    fields = (stage, row["block"], arm, *(run.get(key) for key in columns[3:]))
                    print(*(value if value is not None else "NA" for value in fields), sep="\t", file=source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--stage", choices=PLAN)
    parser.add_argument("--workers", type=int, help="expected nproc for every run")
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--runs-tsv", type=Path)
    args = parser.parse_args()
    try:
        stages = {stage: analyze_stage(args.raw, stage, args.workers)
                  for stage in ((args.stage,) if args.stage else PLAN)}
        c37 = stages.get("C37")
        ratio = c37["wall"]["pooled"] if c37 and c37["wall"] else None
        control = {"planned_blocks": PLAN["C37"], "complete_blocks": c37["complete_blocks"] if c37 else 0,
                   "pooled_wall_ratio": ratio, "threshold": MINIMUM_CONTROL_RATIO,
                   "passes": bool(c37 and c37["complete_blocks"] == PLAN["C37"]
                                  and ratio is not None and ratio > MINIMUM_CONTROL_RATIO)}
        readings = verdict(stages)
        result = {"control": control, "reading": readings, "stages": stages}
        if args.prediction:
            result["prediction"] = grade(stages, readings, json.loads(args.prediction.read_bytes()))
        serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.json:
            args.json.write_text(serialized)
        if args.runs_tsv:
            write_runs_table(stages, args.runs_tsv)
        print(serialized, end="")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
