#!/usr/bin/env python3
"""Run the literal W2 protocol and capture two distinct types of fresh control."""

import argparse
import hashlib
import json
import re
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

from identity import EngineRun, NET_CHECKSUM, NET_SHA, OPTION, PC20, REFUSAL

FIXTURE_SHA = "3c1b17332eca46a912f572eae8197324f466a8e2f909653104c427457ffb0521"
COUNT = 20
ACTIVE = b"info string NNUE v3 active: "
LOADED = b"info string NNUE v3 loaded: "
NET768 = re.compile(rb"\bhidden 768\b.*\bchecksum " + NET_CHECKSUM + rb"\b")


def fixture(path):
    data = path.read_bytes()
    if b"\r" in data or not data.endswith(b"\n"):
        raise ValueError("expected LF-delimited fixture with a final LF")
    fens = data.decode("ascii").splitlines()
    if len(fens) != 1000:
        raise ValueError(f"expected 1000 fixture positions, got {len(fens)}")
    for index, fen in enumerate(fens, 1):
        fields = fen.split(" ")
        if len(fields) != 6 or not all(fields) or fields[1] not in ("w", "b"):
            raise ValueError(f"fixture line {index}: invalid six-field FEN")
    return fens[:COUNT], hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def setup(engine, net):
    engine.send("uci")
    hello = engine.receive(lambda line: line == b"uciok", "uciok")
    advertised = {m[1].decode("ascii") for line in hello if (m := OPTION.match(line))}
    required = PC20.keys() | {"NNUEArch", "NNUEArchFile"}
    if missing := required - advertised:
        raise RuntimeError(f"missing advertised UCI options: {sorted(missing)}")
    for name, value in PC20.items():
        engine.send(f"setoption name {name} value {value}")
    engine.send(f"setoption name NNUEArchFile value {net}")
    engine.send("setoption name NNUEArch value true")
    verify_net(engine.ready(), (LOADED, ACTIVE), "setup")


def verify_net(lines, expected, name):
    messages = [line for line in lines if line.startswith((ACTIVE, LOADED))]
    if len(messages) != len(expected) or any(
        not line.startswith(prefix) or not NET768.search(line)
        for line, prefix in zip(messages, expected)
    ):
        raise RuntimeError(f"{name}: expected net768 lifecycle messages {expected!r}, got {messages!r}")


def go(engine, description, markers=()):
    engine.send("go depth 10")
    lines = engine.receive(lambda line: line.startswith(b"bestmove "), description)
    verify_net(lines, markers, description)


def warm(engine, net, fens):
    for index, fen in enumerate(fens, 1):
        engine.send("ucinewgame")
        engine.send(f"position fen {fen}")
        go(engine, f"position {index} initial bestmove")

        engine.send("setoption name NNUEArch value false")
        go(engine, f"position {index} arch-off bestmove")

        engine.send("setoption name NNUEArch value true")
        go(engine, f"position {index} arch-on bestmove", (ACTIVE,))

        engine.send(f"setoption name NNUEArchFile value {net}")
        engine.send("setoption name NNUEArch value true")
        go(engine, f"position {index} reload bestmove", (LOADED, ACTIVE))

        engine.send("setoption name Hash value 1")
        go(engine, f"position {index} Hash=1 bestmove")

        engine.send("setoption name Hash value 16")
        engine.send("ucinewgame")
        go(engine, f"position {index} final bestmove")


def fresh(engine, position):
    engine.send(f"position {position}")
    go(engine, "fresh process first bestmove")


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def capture(executable, net, directory, timeout, operation, source):
    directory.mkdir(parents=True)
    with (directory / "run.meta").open("x") as meta:
        meta.write(json.dumps(source, sort_keys=True) + "\n")
        meta.write(f"started {timestamp()}\n")
        meta.flush()
        status = 1
        try:
            with ExitStack() as stack:
                stdout = stack.enter_context((directory / "engine.stdout.txt").open("x+b"))
                stderr = stack.enter_context((directory / "engine.stderr.txt").open("x+b"))
                commands = stack.enter_context((directory / "engine.commands.txt").open("xb"))
                with EngineRun(str(executable), stdout, stderr, commands, timeout) as engine:
                    setup(engine, net)
                    operation(engine)
                for stream in (stdout, stderr):
                    stream.seek(0)
                    for line in stream:
                        if REFUSAL.search(line):
                            raise RuntimeError(f"refusal in complete {stream.name}: {line!r}")
            status = 0
        finally:
            meta.write(f"exit_code {status}\nfinished {timestamp()}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("positions", type=Path)
    parser.add_argument("net", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--timeout", type=float, default=60.0, help="seconds per protocol event")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        executable, net = args.executable.resolve(), args.net.resolve()
        fens, fixture_sha = fixture(args.positions)
        net_sha = file_sha(net)
        if net_sha != NET_SHA:
            raise ValueError(f"net SHA-256 mismatch: {net_sha}")
        immutable = {
            "executable": str(executable), "executable_sha256": file_sha(executable),
            "net": str(net), "net_sha256": net_sha, "fixture_sha256": fixture_sha,
            "matches_expected_fixture": fixture_sha == FIXTURE_SHA,
        }
        args.output.mkdir(parents=True)
        capture(executable, net, args.output / "warm", args.timeout,
                lambda engine: warm(engine, net, fens), immutable | {"mode": "warm"})
        for index, fen in enumerate(fens, 1):
            capture(executable, net, args.output / "fresh" / f"{index:03d}", args.timeout,
                    lambda engine: fresh(engine, f"fen {fen}"),
                    immutable | {"mode": "fresh_fen", "index": index, "fen": fen})
        capture(executable, net, args.output / "startpos", args.timeout,
                lambda engine: fresh(engine, "startpos"), immutable | {"mode": "fresh_startpos"})
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
