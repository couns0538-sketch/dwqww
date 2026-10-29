#!/usr/bin/env python3
"""Chunk driver for resumable NNUE v3 training (job FB2-J1).

    fable_nnue_chunks.py --out DIR [--max-chunks N] -- <python> -I -B fable_nnue_train.py train ... --out DIR ...

Runs the trainer command repeatedly: every run after the first gets `--resume DIR/ckpt.pt`; the loop ends when
DIR/status.json carries a stop_reason (target reached, plateau, horizon), when the trainer exits without having
written a checkpoint (a real failure), or after --max-chunks runs. Each trainer run pauses itself after its own
--max-minutes, so a crash costs at most one chunk minus the last 30-minute checkpoint. Everything is logged to
DIR/chunks_log.txt."""
import argparse
import json
import os
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chunks", type=int, default=1000)
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="trainer command after --")
    args = ap.parse_args()
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        raise SystemExit("no trainer command given after --")
    os.makedirs(args.out, exist_ok=True)
    log = open(os.path.join(args.out, "chunks_log.txt"), "a", newline="\n")

    def say(msg):
        line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    ckpt = os.path.join(args.out, "ckpt.pt")
    status_path = os.path.join(args.out, "status.json")
    stop_flag = os.path.join(args.out, "driver_stop.flag")
    for chunk in range(1, args.max_chunks + 1):
        if os.path.exists(stop_flag) or os.path.exists(os.path.join(args.out, "pause.flag")):
            # Cooperative stop (killing processes is not allowed on this PC): create <out>/driver_stop.flag (the
            # driver ends after the running chunk) or <out>/pause.flag (the trainer pauses within a minute and the
            # driver does not relaunch it); resume by starting the driver again without the flag files.
            say(f"stop/pause flag present in {args.out}: not starting chunk {chunk}")
            sys.exit(0)
        run = list(cmd)
        if os.path.exists(ckpt):
            run += ["--resume", ckpt]
        say(f"chunk {chunk}: {' '.join(run)}")
        t0 = time.time()
        rc = subprocess.call(run)
        say(f"chunk {chunk}: exit {rc} after {time.time() - t0:.0f}s")
        if not os.path.exists(status_path):
            say("no status.json written: stopping the driver")
            sys.exit(1)
        status = json.load(open(status_path))
        if status.get("stop_reason"):
            say(f"run finished: {status['stop_reason']} (step {status['step']}, seen {status['seen']}, best {status['best_exact']})")
            sys.exit(0)
        if rc != 0:
            say("trainer failed; resuming from the last checkpoint in 30 s")
            time.sleep(30)
    say("max chunks reached")


if __name__ == "__main__":
    main()
