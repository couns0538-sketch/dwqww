#!/usr/bin/env python3
"""Run Job 30 K19, M3 or M4 using Job 28's pinned binary and match harness."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "job28", HERE.parent / "sol-job28"):
    if (candidate / "run_match28.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit("Job 28's match harness is missing")

import run_match28


def main():
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--m-star", type=int, required=True, choices=(2220, 1600, 1200, 900, 600, 400, 250, 150, 80))
    options, remaining = parser.parse_known_args()
    run_match28.adjacent(16, "run_match16.py")
    import run_match16

    aged = (("HistoryAgeKeep", "896"), ("HistoryPruneMultiplier", str(options.m_star)))
    default = (("HistoryAgeKeep", "1024"), ("HistoryPruneMultiplier", "2220"))
    matches = {
        "K19": (100, 7291, 4, 2000, 2000, aged, aged),
        "M3": (8000, 7292, 4, 2000, 2000, aged, default),
        "M4": (2000, 7293, 4, 20000, 20000, aged, default),
    }
    save_base, save_run = run_match16.BASE, run_match16.run
    save_grid, save_here, save_description = run_match28.MATCHES, run_match28.HERE, run_match28.__doc__
    save_argv = sys.argv
    if dict(save_base)["HistoryPruneMultiplier"] != "2220":
        raise SystemExit("PC20 must have its original 2220 multiplier")

    def run_with_multiplier(args):
        status = save_run(args)
        output = args.output / f"{args.match}.meta"
        meta = json.loads(output.read_bytes())
        meta.update(history_prune_multiplier_a=options.m_star,
                    history_prune_multiplier_b=options.m_star if args.match == "K19" else 2220)
        temporary = output.with_name(f".{output.name}.tmp")
        temporary.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        temporary.replace(output)
        return status

    run_match16.BASE = tuple((option, value) for option, value in save_base if option != "HistoryPruneMultiplier")
    run_match16.run = run_with_multiplier
    run_match28.MATCHES, run_match28.HERE = matches, HERE
    run_match28.__doc__ = __doc__
    sys.argv = [save_argv[0], *remaining]
    try:
        return run_match28.main()
    finally:
        run_match16.BASE, run_match16.run = save_base, save_run
        run_match28.MATCHES, run_match28.HERE, sys.argv = save_grid, save_here, save_argv
        run_match28.__doc__ = save_description


if __name__ == "__main__":
    raise SystemExit(main())
