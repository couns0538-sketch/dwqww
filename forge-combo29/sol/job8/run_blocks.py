#!/usr/bin/env python3
"""Run the pinned history-age or cold-hard replay arms within Job 8's budget."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from hashlib import sha256
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

AGE_EXE = "559961f449b5e742f60984a43b7b1c672c2512b4ec1e6af2b5e4b6d4ecc60fd9"
BASE_EXE = "63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333"
GAME_SHA = "6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1"
KEEPS = (1024, 896, 768, 512, 256, 0)


def age_arm(keep, protocol, folder):
    overrides = [] if keep == 1024 else ["--set", "HistoryAgeKeep", str(keep)]
    if folder == "opening-raw":
        overrides.append("--opening-only")
    return protocol, folder, f"keep-{keep}-{protocol}", overrides


def arms(stage):
    if stage == "defaults":
        for protocol in ("warm-soft","warm-hard","cold-soft"):
            yield age_arm(1024, protocol, "age-raw")
    elif stage == "pre":
        for keep in KEEPS:
            for protocol in ("warm-soft","warm-hard"):
                yield age_arm(keep, protocol, "opening-raw")
        for keep in (512, 0):
            yield age_arm(keep, "cold-soft", "age-raw")
        yield age_arm(0, "warm-soft", "age-raw")
    elif stage == "A":
        for keep in KEEPS[1:]:
            for protocol in ("warm-soft","warm-hard"):
                if keep or protocol == "warm-hard":
                    yield age_arm(keep, protocol, "age-raw")
    elif stage == "D-base":
        yield "cold-hard", "raw", "base-cold-hard", []
    elif stage == "D-controls":
        for direction, value in (("minus","34"),("plus","46")):
            yield "cold-hard", "raw", f"QsSeeMargin-{direction}-cold-hard", ["--set","QsSeeMargin",value]
    elif stage == "D":
        with Path("settings.tsv").open() as handle:
            for spec in csv.DictReader(handle, delimiter="\t"):
                if spec["kind"] != "tuned" or spec["status"] != "run":
                    continue
                name = spec["name"]
                for direction, field in (("minus","lower"),("plus","upper")):
                    if spec[field] != "-":
                        yield "cold-hard", "raw", f"{name}-{direction}-cold-hard", ["--set",name,spec[field]]


def run_arm(item, args):
    protocol, folder, label, overrides = item
    output = Path(folder) / f"{label}.jsonl"
    output.parent.mkdir(exist_ok=True)
    logfile = Path("status") / f"{args.stage}-{folder}-{label}.txt"
    deadline = args.claim_epoch + 50 * 60
    if time.time() >= deadline:
        return label, "unfinished: measurement deadline"
    command = [sys.executable,"run_age.py",protocol,str(args.engine),str(args.games),str(output),*overrides]
    with logfile.open("x", encoding="utf-8") as log:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            status = proc.wait(timeout=max(0.1,deadline-time.time()))
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL)
                proc.wait()
            return label, "unfinished: measurement deadline"
    return label, "complete" if status == 0 else f"exit {status}; see {logfile}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=("defaults","pre","A","D-base","D-controls","D"))
    parser.add_argument("engine",type=Path)
    parser.add_argument("games",type=Path)
    parser.add_argument("claim_epoch",type=int)
    args = parser.parse_args()
    expected = BASE_EXE if args.stage.startswith("D") else AGE_EXE
    if sha256(args.engine.read_bytes()).hexdigest() != expected or sha256(args.games.read_bytes()).hexdigest() != GAME_SHA:
        parser.error("build or games hash differs")
    if args.stage in ("A","D","D-base","D-controls") and not Path("prediction.commit").is_file():
        parser.error("full measured blocks require the pushed prediction")
    if args.stage == "D-base" and time.time() >= args.claim_epoch + 40 * 60:
        print("Block D unfinished: minute 40 reached before the block started.")
        return 2
    Path("status").mkdir(exist_ok=True)
    failures = 0
    batch = list(arms(args.stage))
    with ThreadPoolExecutor(max_workers=4) as executor:
        for name,status in executor.map(lambda arm: run_arm(arm,args),batch):
            print(f"{name}: {status}",flush=True)
            failures += status != "complete"
    print(f"{args.stage}: {len(batch)-failures}/{len(batch)} runs completed.")
    return int(bool(failures) and args.stage not in ("A","D"))


if __name__ == "__main__":
    raise SystemExit(main())
