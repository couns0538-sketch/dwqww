#!/usr/bin/env python3
"""Run a separate W2 diagnostic with the input FEN restored after the final reset."""

import argparse
import json
from pathlib import Path

from compare_w2 import (
    NET_EVENTS, arm, compare_frames, compare_search_labels, read_trace, warm_commands,
)
from run_w2 import COUNT, NET_SHA, capture, file_sha, fixture, warm


class RestoreFinalPosition:
    def __init__(self, engine):
        self.engine = engine
        self.previous = None
        self.position_command = None

    def send(self, command):
        self.engine.send(command)
        if command.startswith("position fen "):
            self.position_command = command
        if command == "ucinewgame" and self.previous == "setoption name Hash value 16":
            if self.position_command is None:
                raise RuntimeError("final new-game reset preceded its input FEN")
            self.engine.send(self.position_command)
        self.previous = command

    def receive(self, done, description):
        return self.engine.receive(done, description)


def expected_restore(net, fens):
    standard = warm_commands(net, fens)
    commands = []
    fens_in_order = iter(fens)
    for index, command in enumerate(standard):
        commands.append(command)
        if standard[index - 1:index + 2] == ["setoption name Hash value 16", "ucinewgame", "go depth 10"]:
            commands.append(f"position fen {next(fens_in_order)}")
    if len(commands) - len(standard) != len(fens):
        raise ValueError("expected a restored FEN for every input")
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positions", type=Path)
    parser.add_argument("net", type=Path)
    parser.add_argument("r15d_primary", type=Path)
    parser.add_argument("kf_primary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        net = args.net.resolve()
        if file_sha(net) != NET_SHA:
            raise ValueError("net SHA-256 mismatch")
        fens, fixture_sha = fixture(args.positions)
        previous = {
            name: arm(path, fens, net, fixture_sha)
            for name, path in (("r15d", args.r15d_primary), ("kF", args.kf_primary))
        }
        outcome = {}
        for name, (primary, fresh, _) in previous.items():
            source_meta = primary.receipt["meta"]
            executable = Path(source_meta["executable"])
            if file_sha(executable) != source_meta["executable_sha256"]:
                raise ValueError(f"{name}: executable SHA-256 differs from primary W2 receipt")
            receipt = source_meta | {"mode": "restored_final_fen"}
            directory = args.output / name
            capture(executable, net, directory, args.timeout,
                    lambda engine: warm(RestoreFinalPosition(engine), net, fens), receipt)
            current = read_trace(directory, expected_restore(net, fens), NET_EVENTS * COUNT, receipt)
            comparisons = [
                ({"index": index, "fen": fen}, current.frames[index * len(NET_EVENTS) - 1], fresh[index - 1].frames[0])
                for index, fen in enumerate(fens, 1)
            ]
            outcome[name] = {"lines": compare_frames(comparisons), "labels": compare_search_labels(comparisons),
                             "receipt": current.receipt}
        print(json.dumps(outcome, indent=2))
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
