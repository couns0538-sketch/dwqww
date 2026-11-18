#!/usr/bin/env python3
"""Preflight both engines and run a pinned Job 16 fastchess match."""

import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

work = Path(__file__).resolve().parent.parent
for job13 in (work / "job13", work / "sol-job13"):
    if (job13 / "run_match13.py").is_file():
        sys.path.insert(0, str(job13))
        break
else:
    raise SystemExit("Job 13 run_match13.py is missing from the adjacent job13 or sol-job13 directory")
from run_match13 import (
    BASE, BOOK_SHA256, ENGINE_SHA256, FASTCHESS_REVISION, FASTCHESS_VERSION,
    Refused, digest, preflight, utc_now, wait_for_match,
)


def swing(mult, cap=None):
    options = (("EvalSwingMult", str(mult)),)
    return options if cap is None else (*options, ("EvalSwingMax", str(cap)))


SWING_6_200 = swing(6, 200)
MATCHES = {
    # games, seed, workers, nodes A, nodes B, extra options A and B
    "K5": (100, 7161, 4, 2000, 2000, SWING_6_200, SWING_6_200),
    "C5": (200, 7162, 4, 10000, 20000, (), ()),
    "X400": (2000, 7163, 2, 2000, 2000, swing(6, 400), SWING_6_200),
    "X100": (2000, 7164, 2, 2000, 2000, swing(6, 100), SWING_6_200),
    "X50": (2000, 7165, 2, 2000, 2000, swing(6, 50), SWING_6_200),
    "D12v3b": (2000, 7166, 2, 2000, 2000, swing(12), swing(3)),
    "E24k": (2000, 7167, 2, 2000, 2000, swing(24), swing(0)),
    "X400t": (2000, 7168, 2, 10000, 10000, swing(6, 400), SWING_6_200),
    "E12t": (2000, 7169, 2, 10000, 10000, swing(12), swing(0)),
}


def fastchess_command(fastchess, engine, book, pgn, match):
    games, seed, workers, nodes_a, nodes_b, extra_a, extra_b = MATCHES[match]
    command = [str(fastchess)]
    for name, options, nodes in (("A", extra_a, nodes_a), ("B", extra_b, nodes_b)):
        command.extend(("-engine", f"cmd={engine}", f"name={name}"))
        command.extend(f"option.{option}={value}" for option, value in (*BASE, *options))
        if nodes_a != nodes_b:
            command.append(f"nodes={nodes}")
    command.extend(("-each", "proto=uci"))
    if nodes_a == nodes_b:
        command.append(f"nodes={nodes_a}")
    command.extend((
        "-openings", f"file={book}", "format=epd", "order=random",
        "-srand", str(seed), "-rounds", str(games // 2), "-games", "2", "-repeat",
        "-concurrency", str(workers), "-maxmoves", "300", "-pgnout", f"file={pgn}",
    ))
    if workers == 2:
        command.extend(("-ratinginterval", "1"))
    return command


def preflight_side(engine, timeout, settings, meta, side):
    evidence = {"id_name": None, "preflight_uci": [], "preflight_settings_sent": [], "preflight_reply": []}
    suffix = "" if side == "A" else "_b"
    meta[f"preflight_start_utc{suffix}"] = utc_now()
    try:
        preflight(engine, timeout, settings, evidence)
    except Refused:
        meta["preflight_refused_side"] = side
        raise
    finally:
        meta.update({key + suffix: value for key, value in evidence.items()})
        meta[f"preflight_end_utc{suffix}"] = utc_now()


def run(args):
    fastchess = args.fastchess.resolve(strict=True)
    engine = args.engine.resolve(strict=True)
    book = args.book.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    pgn, raw, sidecar = (output / f"{args.match}.{suffix}" for suffix in ("pgn", "out", "meta"))
    for path in (pgn, raw, sidecar):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")

    games, seed, workers, nodes_a, nodes_b, extra_a, extra_b = MATCHES[args.match]
    settings_a = [f"setoption name {option} value {value}" for option, value in (*BASE, *extra_a)]
    settings_b = [f"setoption name {option} value {value}" for option, value in (*BASE, *extra_b)]
    variant = next((
        {"name": option, "value": value} for option, value in extra_a
        if dict(extra_b).get(option) != value
    ), None)
    command = fastchess_command(fastchess, engine, book, pgn, args.match)
    meta = {
        "match": args.match,
        "command": sys.argv,
        "fastchess_command": command,
        "fastchess": str(fastchess),
        "fastchess_sha256": digest(fastchess),
        "fastchess_revision": FASTCHESS_REVISION,
        "fastchess_version": subprocess.check_output(
            [str(fastchess), "--version"], text=True, stderr=subprocess.STDOUT,
        ).strip(),
        "exe": str(engine),
        "exe_sha256": digest(engine),
        "evaluation": "Forge embedded evaluation",
        "external_net_file": None,
        "book": str(book),
        "book_sha256": digest(book),
        "nproc": int(subprocess.check_output(["nproc"], text=True)),
        "concurrency": workers,
        "nodes_a": nodes_a,
        "nodes_b": nodes_b,
        "engine_a": "A",
        "engine_b": "B",
        "settings_a": settings_a,
        "settings_b": settings_b,
        "variant": variant,
        "pgn": str(pgn),
        "out": str(raw),
        "games_requested": games,
        "rating_interval_pairs": 1 if workers == 2 else 10,
        "elo_model": "Fastchess default paired Elo and 95% pentanomial interval",
        "seed": seed,
        "maxmoves": 300,
        "start_utc": utc_now(),
        "status": "incomplete",
    }
    cpu_max = Path("/sys/fs/cgroup/cpu.max")
    if cpu_max.is_file():
        meta["cpu_max"] = cpu_max.read_text().strip()

    caught_signal = None

    def receive_signal(signum, frame):
        nonlocal caught_signal
        if caught_signal is None:
            caught_signal = signal.Signals(signum).name

    saved_handlers = {sig: signal.signal(sig, receive_signal) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        with sidecar.open("x", encoding="utf-8") as metadata:
            try:
                for field, expected in (("book_sha256", BOOK_SHA256), ("exe_sha256", ENGINE_SHA256),
                                        ("fastchess_version", FASTCHESS_VERSION)):
                    if meta[field] != expected:
                        raise RuntimeError(f"{field} expected {expected}, got {meta[field]}")
                preflight_side(engine, args.timeout, settings_a, meta, "A")
                if not caught_signal:
                    preflight_side(engine, args.timeout, settings_b, meta, "B")
                if not caught_signal:
                    with TemporaryDirectory(prefix=f".{args.match}-fastchess-", dir=output) as cwd:
                        with raw.open("xb") as output_file:
                            meta["match_start_utc"] = utc_now()
                            child = subprocess.Popen(
                                command, stdout=output_file, stderr=subprocess.STDOUT,
                                start_new_session=True, cwd=cwd,
                            )
                            meta["fastchess_pid"] = child.pid
                            meta["fastchess_exit"] = wait_for_match(child, lambda: caught_signal, meta)
                            meta["match_end_utc"] = utc_now()
                if caught_signal:
                    meta["status"] = "interrupted"
                    meta["stop_signal"] = caught_signal
                elif meta["fastchess_exit"] != 0:
                    meta["error"] = f"fastchess exited {meta['fastchess_exit']}"
                elif not pgn.is_file() or not pgn.stat().st_size:
                    meta["error"] = "fastchess exited without a nonempty PGN"
                else:
                    meta["status"] = "complete"
            except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                meta["status"] = "refused" if isinstance(error, Refused) else "incomplete"
                meta["error"] = str(error) or type(error).__name__
            finally:
                meta["end_utc"] = utc_now()
                if pgn.is_file():
                    meta["pgn_sha256"] = digest(pgn)
                if raw.is_file():
                    meta["out_sha256"] = digest(raw)
                json.dump(meta, metadata, indent=2)
                metadata.write("\n")
    finally:
        for sig, handler in saved_handlers.items():
            signal.signal(sig, handler)

    suffix = f": {meta['error']}" if "error" in meta else ""
    print(f"{args.match}: {meta['status']}{suffix}", flush=True)
    return 0 if meta["status"] == "complete" else 130 if meta["status"] == "interrupted" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match", choices=MATCHES)
    parser.add_argument("fastchess", type=Path)
    parser.add_argument("engine", type=Path)
    parser.add_argument("book", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--timeout", type=float, default=30, help="seconds per preflight UCI response")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
