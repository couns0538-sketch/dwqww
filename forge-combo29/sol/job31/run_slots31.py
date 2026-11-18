#!/usr/bin/env python3
"""Run a Job 31 cell with the declared soft cutoff and signal handling."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
H_JOB = WORK / "sol-job28"
FASTCHESS = WORK / "sol-job12/fastchess-source/fastchess"
MINUTES = {"K21": 50, "C21": 50, "M3b": 50, "M4b": 45}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match", choices=MINUTES)
    args = parser.parse_args()
    limit = MINUTES[args.match]
    cutoff = int((HERE / "claim.epoch").read_text()) + limit * 60
    if time.time() >= cutoff:
        raise SystemExit(f"The minute-{limit} cutoff has passed.")

    command = [sys.executable, "-u", str(HERE / "run_match31.py"), args.match,
               str(FASTCHESS), str(H_JOB / "h-build/forge"), str(HERE / "openings" / f"{args.match}.epd"),
               str(HERE / "raw"), "--m-star", (HERE / "mstar.txt").read_text().strip(),
               "--h-sha", (H_JOB / "h-build.sha256").read_text().split()[0]]
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
