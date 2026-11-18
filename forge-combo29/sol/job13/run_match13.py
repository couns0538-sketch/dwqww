#!/usr/bin/env python3
"""Preflight and run a pinned Job 13 fastchess match."""

import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

work = Path(__file__).resolve().parent.parent
for job12 in (work / "job12", work / "sol-job12"):
    if (job12 / "run_match.py").is_file():
        sys.path.insert(0, str(job12))
        break
else:
    raise SystemExit("Job 12 run_match.py is missing from the adjacent job12 or sol-job12 directory")
from run_match import BASE, Refused, digest, preflight, utc_now, wait_for_match

MATCHES = {
    # games, seed, concurrency, nodes A, nodes B, EvalSwingMult for A
    "K2": (100, 7111, 4, 20000, 20000, None),
    "C2": (200, 7112, 4, 10000, 20000, None),
    "E2": (2000, 7113, 2, 20000, 20000, "3"),
    "E3k": (2000, 7114, 2, 2000, 2000, "3"),
    "E6": (1000, 7115, 2, 20000, 20000, "6"),
}
BOOK_SHA256 = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
ENGINE_SHA256 = "63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333"
FASTCHESS_REVISION = "d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75"
FASTCHESS_VERSION = "fastchess alpha 1.8.3 20261107-d7b47e8"


def fastchess_command(fastchess, engine, book, pgn, match, options_a):
    games, seed, concurrency, nodes_a, nodes_b, variant = MATCHES[match]
    command = [str(fastchess)]
    for name, options, nodes in (("A", options_a, nodes_a), ("B", BASE, nodes_b)):
        command.extend(("-engine", f"cmd={engine}", f"name={name}"))
        command.extend(f"option.{option}={value}" for option, value in options)
        if nodes_a != nodes_b:
            command.append(f"nodes={nodes}")
    command.extend(("-each", "proto=uci"))
    if nodes_a == nodes_b:
        command.append(f"nodes={nodes_a}")
    command.extend((
        "-openings", f"file={book}", "format=epd", "order=random",
        "-srand", str(seed), "-rounds", str(games // 2), "-games", "2", "-repeat",
        "-concurrency", str(concurrency), "-maxmoves", "300", "-pgnout", f"file={pgn}",
    ))
    if variant is not None:
        command.extend(("-ratinginterval", "1"))
    return command


def run(args):
    fastchess = args.fastchess.resolve(strict=True)
    engine = args.engine.resolve(strict=True)
    book = args.book.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    pgn = output / f"{args.match}.pgn"
    raw = output / f"{args.match}.out"
    sidecar = output / f"{args.match}.meta"
    for path in (pgn, raw, sidecar):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")

    games, seed, concurrency, nodes_a, nodes_b, value = MATCHES[args.match]
    options_a = (*BASE, ("EvalSwingMult", value)) if value is not None else BASE
    settings_a = [f"setoption name {name} value {setting}" for name, setting in options_a]
    settings_b = [f"setoption name {name} value {setting}" for name, setting in BASE]
    command = fastchess_command(fastchess, engine, book, pgn, args.match, options_a)
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
        "concurrency": concurrency,
        "nodes_a": nodes_a,
        "nodes_b": nodes_b,
        "engine_a": "A",
        "engine_b": "B",
        "settings_a": settings_a,
        "settings_b": settings_b,
        "variant": {"name": "EvalSwingMult", "value": value} if value is not None else None,
        "id_name": None,
        "preflight_settings_sent": [],
        "preflight_reply": [],
        "pgn": str(pgn),
        "out": str(raw),
        "games_requested": games,
        "rating_interval_pairs": 1 if value is not None else 10,
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
                meta["preflight_start_utc"] = utc_now()
                try:
                    preflight(engine, args.timeout, settings_a, meta)
                finally:
                    meta["preflight_end_utc"] = utc_now()
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
