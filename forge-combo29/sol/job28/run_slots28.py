#!/usr/bin/env python3
"""Run a Job 28 match without passing its Opus clock cutoff."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
FASTCHESS = WORK / "sol-job12/fastchess-source/fastchess"
COUNT = WORK / "sol-job4/buttons-build/forge"
H = HERE / "h-build/forge"
MINUTES = {"K17": 50, "K18": 50, "M1": 50, "M2": 45}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match", choices=MINUTES)
    args = parser.parse_args()
    limit = MINUTES[args.match]
    cutoff = int((HERE / "claim.epoch").read_text()) + limit * 60
    if time.time() >= cutoff:
        raise SystemExit(f"The minute-{limit} cutoff has passed.")

    command = [sys.executable, "-u", str(HERE / "run_match28.py"), args.match, str(FASTCHESS),
               str(COUNT if args.match == "K17" else H), str(HERE / "openings" / f"{args.match}.epd"),
               str(HERE / "raw")]
    if args.match != "K17":
        command.extend(("--h-sha", (HERE / "h-build.sha256").read_text().split()[0]))
    if args.match == "K18":
        command.extend(("--engine-b", str(COUNT)))
    environment = dict(os.environ, PYTHONPATH=str(WORK / "sol-job3/deps"), PYTHONDONTWRITEBYTECODE="1")
    requested_stop = None

    def receive_signal(signum, frame):
        nonlocal requested_stop
        requested_stop = signal.Signals(signum).name

    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, receive_signal)
    with subprocess.Popen(command, env=environment) as process:
        while (status := process.poll()) is None:
            if requested_stop or time.time() >= cutoff:
                reason = requested_stop or f"Minute-{limit} cutoff"
                print(f"{reason} reached. Sending SIGINT to {args.match}.", flush=True)
                process.send_signal(signal.SIGINT)
                return process.wait()
            time.sleep(min(0.5, max(0, cutoff - time.time())))
        return status


if __name__ == "__main__":
    raise SystemExit(main())
