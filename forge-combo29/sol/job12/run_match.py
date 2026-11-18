#!/usr/bin/env python3
"""Preflight and run one of the four pinned Job 12 fastchess matches."""

import argparse
from hashlib import file_digest
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory

work = Path(__file__).resolve().parent.parent
for job5 in (work / "job5", work / "sol-job5"):
    if (job5 / "run_variants.py").is_file():
        sys.path.insert(0, str(job5))
        break
else:
    raise SystemExit("Job 5 run_variants.py is missing from the adjacent job5 or sol-job5 directory")
from run_variants import VariantEngine
from run_matrix import PC20, Refused, utc_now

MATCHES = {
    "K": (200, 7101, 20000, None),
    "C": (400, 7102, 10000, None),
    "E": (2000, 7103, 20000, ("EvalSwingMult", "3")),
    "I": (2000, 7104, 20000, ("IirDepth", "1")),
}
BASE = (("Threads", "1"), ("Hash", "16"), *PC20)
NODES_B = 20000


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def fastchess_command(fastchess, engine, book, pgn, match, concurrency, options_a):
    games, seed, nodes_a, _ = MATCHES[match]
    command = [str(fastchess)]
    for name, options, nodes in (("A", options_a, nodes_a), ("B", BASE, NODES_B)):
        command.extend(("-engine", f"cmd={engine}", f"name={name}"))
        command.extend(f"option.{option}={value}" for option, value in options)
        if match == "C":
            command.append(f"nodes={nodes}")
    command.extend(("-each", "proto=uci"))
    if match != "C":
        command.append(f"nodes={NODES_B}")
    command.extend((
        "-openings", f"file={book}", "format=epd", "order=random",
        "-srand", str(seed), "-rounds", str(games // 2), "-games", "2", "-repeat",
        "-concurrency", str(concurrency), "-maxmoves", "300", "-pgnout", f"file={pgn}",
    ))
    if match in ("E", "I"):
        # This release emits no final rating block on interruption.
        command.extend(("-ratinginterval", "1"))
    return command


def preflight(engine, timeout, settings, meta):
    with VariantEngine(engine, timeout) as uci:
        uci.send("uci")
        meta["preflight_uci"] = uci.until("uciok")
        meta["id_name"] = next(
            (line for line in meta["preflight_uci"] if line.startswith("id name ")), None,
        )
        if not meta["id_name"]:
            raise RuntimeError("missing Forge id name")
        for setting in settings:
            uci.send(setting)
            meta["preflight_settings_sent"].append(setting)
        uci.send("isready")
        uci.wait_for_variant(meta["preflight_reply"])


def wait_for_match(child, stop_requested, meta):
    while True:
        if stop_requested():
            meta["stop_requested_utc"] = utc_now()
            # Only signal fastchess, so it can stop and join its own engines.
            child.send_signal(signal.SIGINT)
            try:
                return child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                meta["forced_stop"] = True
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                return child.wait()
        try:
            return child.wait(timeout=0.25)
        except subprocess.TimeoutExpired:
            continue


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

    nproc = int(subprocess.check_output(["nproc"], text=True))
    concurrency = nproc // 2 if args.match in ("E", "I") else nproc
    if concurrency < 1:
        raise RuntimeError("nproc is too small to give each concurrent match a worker")
    games, seed, nodes_a, variant = MATCHES[args.match]
    options_a = (*BASE, variant) if variant else BASE
    settings_a = [f"setoption name {name} value {value}" for name, value in options_a]
    settings_b = [f"setoption name {name} value {value}" for name, value in BASE]
    command = fastchess_command(fastchess, engine, book, pgn, args.match, concurrency, options_a)
    meta = {
        "match": args.match,
        "command": sys.argv,
        "fastchess_command": command,
        "fastchess": str(fastchess),
        "fastchess_sha256": digest(fastchess),
        "fastchess_version": subprocess.check_output(
            [str(fastchess), "--version"], text=True, stderr=subprocess.STDOUT,
        ).strip(),
        "exe": str(engine),
        "exe_sha256": digest(engine),
        "evaluation": "Forge embedded evaluation",
        "external_net_file": None,
        "book": str(book),
        "book_sha256": digest(book),
        "nproc": nproc,
        "concurrency": concurrency,
        "nodes_a": nodes_a,
        "nodes_b": NODES_B,
        "engine_a": "A",
        "engine_b": "B",
        "settings_a": settings_a,
        "settings_b": settings_b,
        "variant": {"name": variant[0], "value": variant[1]} if variant else None,
        "id_name": None,
        "preflight_settings_sent": [],
        "preflight_reply": [],
        "pgn": str(pgn),
        "out": str(raw),
        "games_requested": games,
        "rating_interval_pairs": 1 if args.match in ("E", "I") else 10,
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
                meta["preflight_start_utc"] = utc_now()
                try:
                    preflight(engine, args.timeout, settings_a, meta)
                finally:
                    meta["preflight_end_utc"] = utc_now()
                if not caught_signal:
                    # Fastchess writes config.json in its working directory.
                    # Isolate that scratch file between concurrent E and I.
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
