#!/usr/bin/env python3
"""Check unchanged Forge sweep baselines, reruns, controls and opening identity."""
import argparse
import csv
from itertools import islice
import json
import re
from pathlib import Path

FIELDS = ("game", "ply", "fen", "depth", "nodes", "bestmove", "final_nodes", "final_nodes_info", "cnt")
VOLATILE_INFO = re.compile(r" (?:time|nps) [0-9]+(?= |$)")
JOB5 = {
    "HistoryPruneDepth", "HistoryPruneMultiplier", "HistoryBonusQuadratic", "HistoryBonusLinear",
    "HistoryBonusMax", "LmrHistoryDivisor", "ProbcutMargin", "RfpMargin",
}


def compare(new, old, size, prefix=False, examples=1, only_openings=False):
    count = mismatches = 0
    with new.open(encoding="utf-8") as recent, old.open(encoding="utf-8") as prior:
        if prefix:
            prior = islice(prior, size)
        if only_openings:
            recent = (line for line in recent if json.loads(line)["ply"] == 0)
            prior = (line for line in prior if json.loads(line)["ply"] == 0)
        for count, (new_line, old_line) in enumerate(zip(recent, prior, strict=True), 1):
            a, b = json.loads(new_line), json.loads(old_line)
            different = [key for key in FIELDS if a[key] != b[key]]
            if VOLATILE_INFO.sub("", a["info"]) != VOLATILE_INFO.sub("", b["info"]):
                different.append("info_without_time_nps")
            if different:
                mismatches += 1
                if mismatches <= examples:
                    print(f"{new.name} differs from {old.name} at row {count}: {', '.join(different)}.")
                    print(json.dumps({"new": a, "reference": b}, separators=(",", ":")))
    if count != size:
        raise ValueError(f"{new.name} vs {old.name}: expected {size} paired rows, got {count}")
    print(f"{new.name} vs {old.name}: {count-mismatches}/{count} exact.")
    return mismatches


def settings(path):
    with path.open(encoding="utf-8") as file:
        for setting in csv.DictReader(file, delimiter="\t"):
            if setting["status"] != "run":
                continue
            for direction, field in (("minus", "lower"), ("plus", "upper")):
                if setting[field] != "-":
                    yield setting, direction, int(setting[field])


def run(args):
    raw = args.raw
    if args.stage == "bases":
        results = [
            compare(raw / "base-warm-soft.jsonl", args.job5 / "base-soft.jsonl", 1800),
            compare(raw / "base-warm-hard.jsonl", args.job5 / "base-hard.jsonl", 1800),
            compare(raw / "base-cold-soft.jsonl", args.job3 / "C-soft-cold.jsonl", 1800, prefix=True),
        ]
        return int(any(results))

    mismatches = arms = 0
    for setting, direction, value in settings(args.settings):
        name = setting["name"]
        if args.stage == "repeat" and name in JOB5:
            mismatches += compare(raw / f"{name}-{direction}-warm-soft.jsonl",
                                  args.job5 / f"{name}-{direction}-soft.jsonl", 1800, examples=5)
            arms += 1
        elif args.stage == "controls" and setting["kind"] == "control":
            for protocol in ("warm-soft", "cold-soft"):
                mismatches += compare(raw / f"{name}-{direction}-{protocol}.jsonl",
                                      raw / f"base-{protocol}.jsonl", 1800, examples=5)
                arms += 1
        elif args.stage in ("openings", "full-openings"):
            directory = args.opening_raw if args.stage == "openings" else raw
            warm = directory / f"{name}-{direction}-warm-soft.jsonl"
            cold = directory / f"{name}-{direction}-cold-soft.jsonl"
            if args.stage == "full-openings":
                sidecars = [path.with_suffix(".jsonl.meta") for path in (warm, cold)]
                if any(not meta.exists() or not meta.stat().st_size or
                       json.loads(meta.read_text())["status"] != "complete" for meta in sidecars):
                    print(f"{name}-{direction}: full-arm readback unfinished; opening-only gate retained.")
                    continue
            mismatches += compare(warm, cold, 30, examples=1, only_openings=args.stage == "full-openings")
            arms += 1
    print(f"{args.stage}: {arms} paired arms, {mismatches} differing rows.")
    if args.stage != "controls":
        return int(mismatches != 0)
    return 0


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=("bases", "repeat", "controls", "openings", "full-openings"))
parser.add_argument("--raw", type=Path, default=Path("raw"))
parser.add_argument("--opening-raw", type=Path, default=Path("opening-raw"))
parser.add_argument("--settings", type=Path, default=Path("settings.tsv"))
parser.add_argument("--job3", type=Path, required=True)
parser.add_argument("--job5", type=Path, required=True)
raise SystemExit(run(parser.parse_args()))
