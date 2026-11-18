#!/usr/bin/env python3
"""Audit W2 from original UCI command and output logs, and compare stable lines."""

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path

from identity import BESTMOVE, NET_CHECKSUM, NET_SHA, PC20, REFUSAL

COUNT = 20
NAMES = ("initial", "arch_off", "arch_on", "reload", "hash1", "final_after_newgame")
NET_EVENTS = ((), (), ("active",), ("loaded", "active"), (), ())
NET_LINE = re.compile(rb"info string NNUE v3 (active|loaded): .*\bhidden 768\b.*\bchecksum " + NET_CHECKSUM + rb"\b")
VOLATILE = re.compile(rb" (?:time|nps|hashfull) [0-9]+(?= |$)")
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@dataclass(frozen=True)
class Trace:
    startup: list[bytes]
    frames: list[list[bytes]]
    trailer: list[bytes]
    stderr: list[bytes]
    receipt: dict


def raw_lines(path):
    data = path.read_bytes()
    for line in data.splitlines():
        if REFUSAL.search(line):
            raise ValueError(f"{path}: engine refusal: {line!r}")
    return data.splitlines()


def split_at(lines, cursor, end, context):
    for index in range(cursor, len(lines)):
        if end(lines[index]):
            return lines[cursor:index + 1], index + 1
    raise ValueError(f"{context}: end of stdout before expected protocol event")


def check_markers(lines, expected, context):
    seen = []
    for line in lines:
        if line.startswith((b"info string NNUE v3 active:", b"info string NNUE v3 loaded:")):
            match = NET_LINE.match(line)
            if match is None:
                raise ValueError(f"{context}: unexpected NNUE v3 message {line!r}")
            seen.append(match[1].decode("ascii"))
    if seen != list(expected):
        raise ValueError(f"{context}: expected net events {expected}, saw {seen}")


def check_command_trace(directory, expected):
    actual = (directory / "engine.commands.txt").read_text().splitlines()
    for index, (left, right) in enumerate(zip_longest(expected, actual), 1):
        if left != right:
            raise ValueError(f"{directory}: command {index}: expected {left!r}, saw {right!r}")


def expected_setup(net):
    return ["uci", *(f"setoption name {name} value {value}" for name, value in PC20.items()),
            f"setoption name NNUEArchFile value {net}", "setoption name NNUEArch value true", "isready"]


def warm_commands(net, positions):
    commands = expected_setup(net)
    for fen in positions:
        commands.extend((
            "ucinewgame", f"position fen {fen}", "go depth 10",
            "setoption name NNUEArch value false", "go depth 10",
            "setoption name NNUEArch value true", "go depth 10",
            f"setoption name NNUEArchFile value {net}", "setoption name NNUEArch value true", "go depth 10",
            "setoption name Hash value 1", "go depth 10",
            "setoption name Hash value 16", "ucinewgame", "go depth 10",
        ))
    return [*commands, "quit"]


def read_trace(directory, commands, net_events, expected_meta):
    check_command_trace(directory, commands)
    meta_rows = (directory / "run.meta").read_text().splitlines()
    meta = json.loads(meta_rows[0])
    if meta_rows.count("exit_code 0") != 1 or not all(
        meta.get(key) == value for key, value in expected_meta.items()
    ):
        raise ValueError(f"{directory}: run metadata failed validation")
    lines = raw_lines(directory / "engine.stdout.txt")
    stderr = raw_lines(directory / "engine.stderr.txt")
    uci, cursor = split_at(lines, 0, lambda line: line == b"uciok", directory)
    setup, cursor = split_at(lines, cursor, lambda line: line == b"readyok", directory)
    if any(line.startswith(b"bestmove ") or line == b"readyok" for line in uci):
        raise ValueError(f"{directory}: unexpected event during initial UCI handshake")
    if any(line.startswith(b"bestmove ") or line == b"uciok" for line in setup):
        raise ValueError(f"{directory}: unexpected event during setup")
    check_markers(setup, ("loaded", "active"), directory)
    frames = []
    for index, markers in enumerate(net_events, 1):
        context = f"{directory}, search {index}"
        frame, cursor = split_at(lines, cursor, lambda line: line.startswith(b"bestmove "), context)
        if any(line in (b"readyok", b"uciok") for line in frame):
            raise ValueError(f"{context}: unexpected handshake during workload")
        if not BESTMOVE.fullmatch(frame[-1]):
            raise ValueError(f"{context}: malformed bestmove {frame[-1]!r}")
        check_markers(frame, markers, context)
        label(frame)
        frames.append(frame)
    trailer = lines[cursor:]
    if any(line.startswith(b"bestmove ") or line in (b"readyok", b"uciok") for line in trailer):
        raise ValueError(f"{directory}: extra handshake or search output")
    check_markers(trailer, (), directory)
    paths = ("engine.stdout.txt", "engine.stderr.txt", "engine.commands.txt", "run.meta")
    receipt = {"meta": meta, "files_sha256": {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in paths}}
    return Trace(uci + setup, frames, trailer, stderr, receipt)


def normalized(line):
    if not line.startswith(b"info ") or line.startswith(b"info string "):
        return line
    fields, separator, pv = line.partition(b" pv ")
    return VOLATILE.sub(b"", fields) + separator + pv


def label(frame):
    try:
        info = next(line for line in reversed(frame) if line.startswith(b"info depth "))
        fields = info.partition(b" pv ")[0].split()
        parts = info.split()
        score_index = fields.index(b"score")
        score_kind = fields[score_index + 1]
        if score_kind not in (b"cp", b"mate"):
            raise ValueError(f"unknown score kind {score_kind!r}")
        return {
            "depth": int(fields[2]),
            "nodes": int(fields[fields.index(b"nodes") + 1]),
            "score_type": score_kind.decode("ascii"),
            "score": int(fields[score_index + 2]),
            "bound": next((word.decode("ascii") for word in (b"lowerbound", b"upperbound") if word in fields), None),
            "pv_head": parts[parts.index(b"pv") + 1].decode("ascii") if b"pv" in parts and parts[-1] != b"pv" else None,
            "bestmove": frame[-1].split()[1].decode("ascii"),
        }
    except (StopIteration, IndexError, ValueError) as error:
        raise ValueError(f"could not label search ending {frame[-1]!r}") from error


def line_counts(left, right):
    compared = max(len(left), len(right))
    first = None
    equal = 0
    for index, (l_line, r_line) in enumerate(zip_longest(left, right), 1):
        l_key = normalized(l_line) if l_line is not None else None
        r_key = normalized(r_line) if r_line is not None else None
        if l_key == r_key:
            equal += 1
        elif first is None:
            first = {
                "line_within_event": index,
                "left": None if l_key is None else l_key.decode("ascii", errors="replace"),
                "right": None if r_key is None else r_key.decode("ascii", errors="replace"),
            }
    return {"lines_compared": compared, "equal": equal, "differ": compared - equal,
            "left_lines": len(left), "right_lines": len(right), "first_difference": first}


def compare_frames(frames):
    totals = dict.fromkeys(("lines_compared", "equal", "differ", "left_lines", "right_lines"), 0)
    differences = []
    lookups = []
    for context, left, right in frames:
        counts = line_counts(left, right)
        for name in totals:
            totals[name] += counts[name]
        lookups.append(context | counts)
        if counts["differ"]:
            differences.append(context | counts)
    return totals | {
        "first_difference": differences[0] if differences else None,
        "events_compared": len(lookups), "events_equal": len(lookups) - len(differences),
        "events_differ": len(differences), "differing_events": differences,
    }


def compare_search_labels(frames):
    changes = []
    for context, left, right in frames:
        left_label, right_label = label(left), label(right)
        if left_label != right_label:
            changes.append(context | {"left": left_label, "right": right_label})
    return {"rows_compared": len(frames), "rows_equal": len(frames) - len(changes),
            "rows_differ": len(changes), "differences": changes}


def arm(root, positions, net, fixture_sha):
    common = {"fixture_sha256": fixture_sha, "net": str(net), "net_sha256": NET_SHA}
    trace = read_trace(root / "warm", warm_commands(net, positions),
                       NET_EVENTS * COUNT, common | {"mode": "warm"})
    executable = trace.receipt["meta"]["executable_sha256"]
    common["executable_sha256"] = executable
    control = []
    for index, fen in enumerate(positions, 1):
        control.append(read_trace(root / "fresh" / f"{index:03d}",
                                  [*expected_setup(net), f"position fen {fen}", "go depth 10", "quit"],
                                  [()], common | {"mode": "fresh_fen", "index": index, "fen": fen}))
    startpos = read_trace(root / "startpos", [*expected_setup(net), "position startpos", "go depth 10", "quit"],
                          [()], common | {"mode": "fresh_startpos"})
    return trace, control, startpos


def by_position(positions, left, right):
    frames = []
    for index, fen in enumerate(positions, 1):
        for step, name in enumerate(NAMES):
            offset = (index - 1) * len(NAMES) + step
            context = {"index": index, "input_fen": fen, "event": name,
                       "search_fen": START_FEN if name == NAMES[-1] else fen}
            frames.append((context, left.frames[offset], right.frames[offset]))
    return frames


def final_controls(positions, trace, fresh, startpos):
    original_pairs, start_pairs = [], []
    for index, fen in enumerate(positions, 1):
        final = trace.frames[index * len(NAMES) - 1]
        context = {"index": index, "input_fen": fen, "warm_final_fen": START_FEN}
        original_pairs.append((context | {"fresh_fen": fen}, final, fresh[index - 1].frames[0]))
        start_pairs.append((context | {"fresh_fen": START_FEN}, final, startpos.frames[0]))
    return {
        "final_vs_fresh_original_fen": {"lines": compare_frames(original_pairs), "labels": compare_search_labels(original_pairs)},
        "final_vs_fresh_startpos": {"lines": compare_frames(start_pairs), "labels": compare_search_labels(start_pairs)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positions", type=Path)
    parser.add_argument("net", type=Path)
    parser.add_argument("r15d", type=Path)
    parser.add_argument("kf", type=Path)
    args = parser.parse_args()
    try:
        fixture = args.positions.read_bytes()
        fens = fixture.decode("ascii").splitlines()
        if len(fens) != 1000:
            raise ValueError(f"{args.positions}: expected 1,000 FENs")
        positions = fens[:COUNT]
        fixture_sha = hashlib.sha256(fixture).hexdigest()
        net = args.net.resolve()
        left, left_fresh, left_start = arm(args.r15d, positions, net, fixture_sha)
        right, right_fresh, right_start = arm(args.kf, positions, net, fixture_sha)
        paired = by_position(positions, left, right)
        warm = compare_frames(paired)
        startup = ({"event": "startup"}, left.startup, right.startup)
        trailer = ({"event": "trailer"}, left.trailer, right.trailer)
        full = compare_frames([startup, *paired, trailer])
        result = {
            "fixture_sha256": fixture_sha, "positions_compared": COUNT,
            "normalization": "remove only typed numeric time/nps/hashfull fields on UCI info before any PV; compare positionally within search events",
            "net_checksum": NET_CHECKSUM.decode("ascii"),
            "warm_r15d_vs_kF": {
                "workload_stdout": warm, "whole_stdout": full,
                "workload_labels": compare_search_labels(paired),
                "stderr": line_counts(left.stderr, right.stderr),
            },
            "r15d_controls": final_controls(positions, left, left_fresh, left_start),
            "kF_controls": final_controls(positions, right, right_fresh, right_start),
            "receipts": {
                "r15d": {"warm": left.receipt, "fresh_original_fen": [item.receipt for item in left_fresh],
                         "fresh_startpos": left_start.receipt},
                "kF": {"warm": right.receipt, "fresh_original_fen": [item.receipt for item in right_fresh],
                       "fresh_startpos": right_start.receipt},
            },
        }
    except (OSError, ValueError, KeyError, IndexError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
