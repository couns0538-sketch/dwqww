#!/usr/bin/env python3
"""Execute independent pinned UCI arms, within the job's wall-clock budget."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import csv
from hashlib import sha256
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

EXE = "63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333"
GAME_SHA = "6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1"
JOB5 = {
    "HistoryPruneDepth", "HistoryPruneMultiplier", "HistoryBonusQuadratic", "HistoryBonusLinear",
    "HistoryBonusMax", "LmrHistoryDivisor", "ProbcutMargin", "RfpMargin",
}


def arms(settings, stage):
    for spec in settings:
        if spec["status"] != "run":
            continue
        name = spec["name"]
        tuned = spec["kind"] == "tuned"
        for direction, field in (("minus", "lower"), ("plus", "upper")):
            value = spec[field]
            if value == "-":
                continue
            if stage == "repeat" and name in JOB5:
                yield name, direction, "warm-soft", value
            elif stage == "controls" and not tuned:
                for protocol in ("warm-soft", "cold-soft"):
                    yield name, direction, protocol, value
            elif stage == "openings":
                for protocol in ("warm-soft", "cold-soft"):
                    yield name, direction, protocol, value
            elif stage == "A" and tuned and name not in JOB5:
                yield name, direction, "warm-soft", value
            elif stage == "B" and tuned:
                yield name, direction, "cold-soft", value
            elif stage == "C" and tuned and name not in JOB5:
                yield name, direction, "warm-hard", value


def run_arm(item, args, deadline):
    name, direction, protocol, value = item
    label = f"{name}-{direction}-{protocol}"
    output_dir = Path("opening-raw" if args.stage == "openings" else "raw")
    output_dir.mkdir(exist_ok=True)
    destination = output_dir / f"{label}.jsonl"
    logfile = Path("status") / f"{args.stage}-{label}.txt"
    if time.time() >= deadline:
        return label, "unfinished: deadline reached"
    command = [sys.executable, "run_sweep.py", protocol, str(args.engine), str(args.games), str(destination),
               "--set", name, value]
    if args.stage == "openings":
        command.append("--opening-only")
    with logfile.open("x", encoding="utf-8") as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            result = child.wait(timeout=max(0.1, deadline-time.time()))
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGINT)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            return label, "unfinished: measurement deadline"
    return label, "complete" if result == 0 else f"exit {result}; see {logfile}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("repeat", "controls", "openings", "A", "B", "C"))
    parser.add_argument("engine", type=Path)
    parser.add_argument("games", type=Path)
    parser.add_argument("claim_epoch", type=int)
    args = parser.parse_args()
    if sha256(args.engine.read_bytes()).hexdigest() != EXE or sha256(args.games.read_bytes()).hexdigest() != GAME_SHA:
        parser.error("engine or game file does not match the pinned lab input")
    if args.stage in ("A","B","C") and not Path("prediction.commit").is_file():
        parser.error("full blocks require verified remote prediction")
    if args.stage == "C" and time.time() >= args.claim_epoch + 40 * 60:
        print("Block C unfinished: reached minute 40 before starting it.")
        return 0
    Path("status").mkdir(exist_ok=True)
    with Path("settings.tsv").open(encoding="utf-8") as handle:
        batch = list(arms(list(csv.DictReader(handle, delimiter="\t")), args.stage))
    deadline = args.claim_epoch + 50 * 60
    failures = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        for name, status in executor.map(lambda arm: run_arm(arm, args, deadline), batch):
            print(f"{name}: {status}", flush=True)
            failures += status != "complete"
    print(f"{args.stage}: {len(batch)-failures}/{len(batch)} runs completed.")
    return int(bool(failures) and args.stage in ("repeat", "controls", "openings"))


if __name__ == "__main__":
    raise SystemExit(main())
