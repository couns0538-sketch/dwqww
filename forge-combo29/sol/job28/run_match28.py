#!/usr/bin/env python3
"""Run one Job 28 cell on its pinned fresh opening subset."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
FASTCHESS_SHA256 = "fb945c0930ff17786ccc1c07267930e1c0a6098f9bb16dcd13be20a11baec72e"
COUNT_SHA256 = "63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333"
KEEP_1024 = (("HistoryAgeKeep", "1024"),)
KEEP_896 = (("HistoryAgeKeep", "896"),)
MATCHES = {
    # games, seed, workers, nodes A, nodes B, extra options A and B
    "K17": (100, 7281, 4, 2000, 2000, (), ()),
    "K18": (100, 7282, 4, 2000, 2000, KEEP_1024, ()),
    "M1": (4000, 7283, 4, 2000, 2000, KEEP_896, KEEP_1024),
    "M2": (2000, 7284, 4, 20000, 20000, KEEP_896, KEEP_1024),
}


def adjacent(job, filename):
    for directory in (HERE.parent / f"job{job}", HERE.parent / f"sol-job{job}"):
        if (directory / filename).is_file():
            sys.path.insert(0, str(directory))
            return
    raise SystemExit(f"Missing Job {job} dependency {filename}")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--engine-b", type=Path)
    parser.add_argument("--h-sha")
    extra, inherited = parser.parse_known_args()
    original_argv = sys.argv
    sys.argv = [original_argv[0], *inherited]
    adjacent(16, "run_match16.py")
    adjacent(27, "run_match27.py")
    import run_match16
    import run_match27

    original_grid = run_match16.MATCHES
    original_description = run_match16.__doc__
    original_run = run_match16.run
    original_preflight = run_match16.preflight_side
    original_command = run_match16.fastchess_command
    official_book_sha = run_match16.BOOK_SHA256
    original_engine_sha = run_match16.ENGINE_SHA256
    original_openings_grid = run_match27.MATCHES
    engine_b = None

    def command_for_two_engines(fastchess, engine_a, book, pgn, match):
        command = original_command(fastchess, engine_a, book, pgn, match)
        _, second = [index + 1 for index, argument in enumerate(command) if argument == "-engine"]
        command[second] = f"cmd={engine_b}"
        command.extend(("-ratinginterval", "1"))
        return command

    def preflight_b(engine_a, timeout, settings, meta, side):
        return original_preflight(engine_a if side == "A" else engine_b, timeout, settings, meta, side)

    def run_with_pins(args):
        nonlocal engine_b
        engine_b = (extra.engine_b or args.engine).resolve(strict=True)
        expected_a = COUNT_SHA256 if args.match == "K17" else extra.h_sha
        expected_b = COUNT_SHA256 if args.match in ("K17", "K18") else expected_a
        if not expected_a or not re.fullmatch("[0-9a-f]{64}", expected_a):
            raise SystemExit(f"{args.match} requires --h-sha with H's full pinned SHA-256")
        if run_match16.digest(engine_b) != expected_b:
            raise SystemExit(f"{args.match} B binary SHA-256 does not match its pin")
        if run_match16.digest(args.fastchess) != FASTCHESS_SHA256:
            raise SystemExit("Fastchess binary SHA-256 does not match its pin")
        provenance = run_match27.opening_provenance(
            HERE / "openings/manifest.json", args.match, args.book, official_book_sha,
        )
        run_match16.BOOK_SHA256 = provenance.pop("book_sha256")
        run_match16.ENGINE_SHA256 = expected_a
        status = original_run(args)
        sidecar = args.output / f"{args.match}.meta"
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        meta.update(provenance, exe_b=str(engine_b), exe_sha256_b=expected_b, rating_interval_pairs=1)
        temporary = sidecar.with_name(f".{sidecar.name}.tmp")
        temporary.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        temporary.replace(sidecar)
        return status

    run_match27.MATCHES = MATCHES
    run_match16.MATCHES = MATCHES
    run_match16.run = run_with_pins
    run_match16.preflight_side = preflight_b
    run_match16.fastchess_command = command_for_two_engines
    run_match16.__doc__ = __doc__
    try:
        return run_match16.main()
    finally:
        run_match16.MATCHES = original_grid
        run_match16.__doc__ = original_description
        run_match16.run = original_run
        run_match16.preflight_side = original_preflight
        run_match16.fastchess_command = original_command
        run_match16.BOOK_SHA256 = official_book_sha
        run_match16.ENGINE_SHA256 = original_engine_sha
        run_match27.MATCHES = original_openings_grid
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
