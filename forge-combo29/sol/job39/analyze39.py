#!/usr/bin/env python3
"""Verify Job 39 run receipts and compare record files without launching an engine."""

import argparse
from collections import Counter
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path
import random
import re
import subprocess

from generate_draws39 import NAMES, draw_values


STAGES = ("K39", "C39", "L39", "A", "B")
BUILDS = ("r15d", "kF")
MODES = {"A": "hard", "B": "soft"}
FIRST = {"A": 391000, "B": 392000}
STATUS = {"complete", "cut", "refused", "crash", "hang", "incomplete"}
RECORD = re.compile(rb"([0-9]+) ([0-9]+) ([a-h][1-8][a-h][1-8][qrbn]?) ([0-9]+)\n")
ENGINE_PINS = {
    "r15d": "9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671",
    "kF": "c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb",
}
NET_PIN = "c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7"
NET_CHECKSUM = "30ab43b4ba5db5f3"
PC20_PIN = "e355dbddb98abb000283ca7b37126e4cf71e152ce6df0bec8f1ea11fb715c7af"


def verify(condition, message):
    if not condition:
        raise ValueError(message)


def read_records(data, path, first, last):
    groups = Counter()
    last_game, last_ply, node_sum = first - 1, 7, 0
    for index, line in enumerate(data.splitlines(keepends=True), 1):
        match = RECORD.fullmatch(line)
        verify(match, f"{path}: invalid record at line {index}: {line!r}")
        game, ply, nodes = (int(match[group]) for group in (1, 2, 4))
        verify(first <= game <= last and last_game <= game and 8 <= ply < 300
               and ply == (last_ply + 1 if game == last_game else 8),
               f"{path}: invalid game or ply at line {index}")
        groups[game] += 1
        node_sum += nodes
        last_game, last_ply = game, ply
    return groups, node_sum


def validate_setup(path, meta, build, draw, lmr60):
    data = path.read_bytes()
    verify(sha256(data).hexdigest() == meta["uci_setup_sha256"], f"{path}: setup SHA-256 differs from receipt")
    verify(meta["exe_sha256"] == ENGINE_PINS[build] and meta["external_net_sha256"] == NET_PIN
           and meta["external_net_checksum_expected"] == NET_CHECKSUM and meta["lmr60"] == lmr60,
           f"{path}: executable, net or LMR control differs from schedule")
    expected = {} if draw == "pc20" else dict(zip(NAMES, map(str, draw_values(draw)), strict=True))
    if lmr60:
        expected["LmrQuietBase"] = "60"
    verify(meta["draw_settings"] == expected, f"{path}: recorded draw settings differ from schedule")

    lines = data.decode().splitlines()
    sent = [line[2:] for line in lines if line.startswith("> setoption ")]
    acknowledged = meta["settings_sent"]
    verify(sent == acknowledged
           or (meta["status"] != "complete" and len(sent) == len(acknowledged) + 1
               and sent[:-1] == acknowledged), f"{path}: sent option commands differ from receipt")
    if meta["status"] != "complete":
        return
    verify(sent[:2] == ["setoption name Threads value 1", "setoption name Hash value 16"]
           and sha256(("\n".join(sent[2:22]) + "\n").encode()).hexdigest() == PC20_PIN
           and sent[22:24] == [f"setoption name NNUEArchFile value {meta['external_net_file']}",
                               "setoption name NNUEArch value true"]
           and sent[24:] == [f"setoption name {name} value {value}" for name, value in expected.items()],
           f"{path}: sent options differ from the declared order")
    exchange = [line for line in lines if line.startswith(("> ", "< readyok"))]
    sequence = [item for command in sent for item in (f"> {command}", "> isready", "< readyok")]
    verify(exchange == ["> uci", *sequence] and meta["settings_ready_count"] == len(sent),
           f"{path}: ready barrier missing after an option")
    active = [line[2:] for line in lines if line.startswith("< info string NNUE v3 active:")]
    verify(active == [meta["active_line"]] and f"checksum {NET_CHECKSUM}" in active[0],
           f"{path}: missing active-net confirmation")


def read_run(raw, label, build, draw, mode, first):
    folder = raw / label
    receipt = folder / "run.json"
    last = first + 9
    base = {"build": build, "draw": draw, "mode": mode, "first_game": first, "last_game": last}
    if not receipt.is_file() or not receipt.stat().st_size:
        wrapper = folder.with_name(f"{folder.name}.driver.out")
        started = wrapper.is_file() or (folder.is_dir() and any(folder.iterdir()))
        status = "unfinalized" if started else "not played"
        run = {**base, "status": status, "games": 0, "records": 0, "nodes": 0}
        if wrapper.is_file():
            run["wrapper_output"] = wrapper.read_text(errors="replace").splitlines()
            run["wrapper_file"] = str(wrapper.relative_to(raw))
        return run, None
    meta = json.loads(receipt.read_text())
    status = meta["status"]
    verify(status in STATUS and str(meta["draw"]) == str(draw)
           and (meta["build"], meta["mode"], meta["first_game"], meta["last_game"]) == (build, mode, first, last),
           f"{receipt}: run identity or status differs from schedule")
    search = "go nodes 20000" if mode == "hard" else "go softnodes 2000"
    verify(meta["search"] == search, f"{receipt}: unexpected search command")
    validate_setup(folder / "uci-setup.txt", meta, build, draw, label == "C39")
    path = folder / "records.txt"
    data = path.read_bytes()
    digest = sha256(data).hexdigest()
    verify(meta["records_sha256"] == digest, f"{path}: SHA-256 differs from receipt")
    counts, nodes = read_records(data, path, first, last)
    games = meta["games"]
    numbers = [game["game"] for game in games]
    verify(len(games) == meta["games_completed"] <= 10 and numbers == list(range(first, first + len(games)))
           and (status != "complete" or len(games) == 10), f"{receipt}: invalid completed-game list")
    verify(set(counts) <= set(numbers)
           and all(counts[game["game"]] == game["plies"] for game in games),
           f"{receipt}: recorded game lengths differ from receipt")
    records = sum(counts.values())
    verify(meta["positions_completed"] == records and meta["last_info_nodes_sum"] == nodes,
           f"{receipt}: record count or last-info node total differs from receipt")
    return {
        **base, "status": status, "games": len(games), "records": records, "nodes": nodes,
        "records_sha256": digest, "games_with_records": len(counts), "search": search,
        "record_file": str(path.relative_to(raw)), "error": meta.get("error"),
        "stop_reason": meta.get("stop_reason"), "uci_setup_sha256": meta["uci_setup_sha256"],
        "last_command": meta.get("last_command"), "last_reply": meta.get("last_reply"),
        "stopped_at": meta.get("stopped_at"), "start_utc": meta.get("start_utc"),
        "end_utc": meta.get("end_utc"),
    }, data


def opening_moves(game):
    import chess

    verify(chess.__version__ == "1.11.2", f"Unexpected python-chess version {chess.__version__}")
    board = chess.Board()
    rng = random.Random(game)
    moves = []
    for _ in range(8):
        move = rng.choice(list(board.legal_moves))
        moves.append(move.uci())
        board.push(move)
        if board.is_game_over(claim_draw=True):
            break
    return moves


def position_at(lines, index, line):
    if line is None:
        return None
    game, ply, bestmove, nodes = line.decode().split()
    before = []
    for prev in reversed(lines[:index]):
        prev_game, _, move, _ = prev.decode().split()
        if prev_game != game:
            break
        before.append(move)
    moves = opening_moves(int(game)) + before[::-1]
    verify(len(moves) == int(ply), f"Cannot reconstruct position for {line!r}")
    return {
        "game": int(game), "ply": int(ply), "bestmove": bestmove, "nodes": int(nodes),
        "moves_before": moves, "command": "position startpos moves " + " ".join(moves),
    }


def first_difference(left, right):
    a, b = (data.splitlines() for data in (left, right))
    for index, (first, second) in enumerate(zip_longest(a, b)):
        if first != second:
            return {
                "line": index + 1, "left": first.decode() if first is not None else None,
                "right": second.decode() if second is not None else None,
                "left_position": position_at(a, index, first), "right_position": position_at(b, index, second),
            }
    raise ValueError("Different record files had no differing record")


def compare(raw, left, right, left_data, right_data):
    if left["status"] != "complete" or right["status"] != "complete":
        return {"reading": "NOT PLAYED" if all(row["status"] == "not played" for row in (left, right))
                else "INCOMPLETE", "first_difference": None}
    check = subprocess.run(["cmp", "-s", raw / left["record_file"], raw / right["record_file"]], check=False)
    verify(check.returncode == (left_data != right_data), "cmp result differs from bytes read")
    if check.returncode == 0:
        return {"reading": "IDENTICAL", "first_difference": None}
    return {"reading": "DIFFERS", "first_difference": first_difference(left_data, right_data)}


def controls(raw, stage, runs, contents):
    pairs = {"K39": ("K39a", "K39b"), "C39": ("K39a", "C39"), "L39": ("K39a", "L39")}
    keys = pairs[stage]
    for key in keys:
        if key not in runs:
            runs[key], contents[key] = read_run(raw, key, "r15d", "pc20" if key == "L39" else 1, "hard", 390001)
    left, right = (runs[key] for key in keys)
    outcome = compare(raw, left, right, *(contents[key] for key in keys))
    expected = "IDENTICAL" if stage == "K39" else "DIFFERS"
    return {"left_run": keys[0], "right_run": keys[1], "expected": expected,
            "passes": outcome["reading"] == expected, **outcome}


def read_draws(path):
    if not path.is_file():
        return {}
    draws = {}
    for index, line in enumerate(path.read_text().splitlines(), 1):
        row = [int(value) for value in line.split("\t")]
        verify(len(row) == 41 and row[0] == index, f"{path}: malformed draw {index}")
        verify(tuple(row[1:]) == draw_values(index), f"{path}: values differ from the generator for draw {index}")
        draws[index] = row[1:]
    verify(len(draws) == 100, f"{path}: expected 100 draws")
    return draws


def measured(raw, stage, runs, values):
    draws = []
    failures = []
    games = dict.fromkeys(BUILDS, 0)
    records = dict.fromkeys(BUILDS, 0)
    nodes = dict.fromkeys(BUILDS, 0)
    for k in range(1, 101):
        keys = {build: f"{stage}/draw-{k:03d}/{build}" for build in BUILDS}
        content = {}
        outcome = {}
        for build, key in keys.items():
            row, content[build] = read_run(raw, key, build, k, MODES[stage], FIRST[stage] + 10 * k)
            runs[key] = row
            outcome[build] = row["status"]
            if row["status"] not in ("not played", "complete"):
                failures.append({"run": key, **row})
            games[build] += row["games"]
            records[build] += row["records"]
            nodes[build] += row["nodes"]
        decision = compare(raw, *(runs[keys[build]] for build in BUILDS), *(content[build] for build in BUILDS))
        if first := decision["first_difference"]:
            first.update({"r15d": first["left"], "kF": first["right"]})
            verify(k in values, f"{stage} draw {k}: differing pair is missing its draws.tsv row")
        draws.append({"draw": k, "runs": keys, "outcomes": outcome, "values": values.get(k), **decision})
    readings = Counter(row["reading"] for row in draws)
    differing = readings["DIFFERS"]
    same = readings["IDENTICAL"]
    incomplete = readings["INCOMPLETE"]
    unplayed = readings["NOT PLAYED"]
    reading = "DIFFERS" if differing else "KEEPS" if same == 100 else "NOT PLAYED" if unplayed == 100 else "INCOMPLETE"
    return {
        "reading": reading, "draws_started": 100 - unplayed, "draws_played": differing + same,
        "draws_identical": same, "draws_differ": differing, "draws_incomplete": incomplete,
        "draws_not_played": unplayed, "games": games, "records": records, "nodes": nodes, "draws": draws,
        "run_failures": failures,
    }


def grade(predictions, comparisons):
    result = {}
    for stage, comparison in comparisons.items():
        interval = predictions[stage]
        verify(isinstance(interval, list) and len(interval) == 2 and all(type(value) is int for value in interval)
               and 0 <= interval[0] <= interval[1] <= 100, f"{stage}: invalid prediction range")
        actual = comparison["draws_differ"] if comparison["draws_played"] == 100 else None
        outcome = "ungraded" if actual is None else "met" if interval[0] <= actual <= interval[1] else "missed"
        result[stage] = {"forecast": interval, "observed": actual, "grade": outcome}
    return result


def write_runs(path, runs):
    columns = ("build", "draw", "mode", "first_game", "last_game", "status", "games", "records", "nodes", "records_sha256")
    with path.open("w") as output:
        print("run", *columns, sep="\t", file=output)
        for run, row in runs.items():
            print(run, *(row.get(field, "NA") for field in columns), sep="\t", file=output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--stage", choices=STAGES)
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--runs-tsv", type=Path)
    args = parser.parse_args()
    try:
        stages = (args.stage,) if args.stage else STAGES
        runs, contents, control, comparisons = {}, {}, {}, {}
        values = read_draws(args.raw.parent / "draws.tsv")
        for stage in stages:
            if stage in MODES:
                comparisons[stage] = measured(args.raw, stage, runs, values)
            else:
                control[stage] = controls(args.raw, stage, runs, contents)
        result = {"control": control, "runs": runs, "comparisons": comparisons}
        if args.prediction:
            result["prediction"] = grade(json.loads(args.prediction.read_text()), comparisons)
        if args.runs_tsv:
            write_runs(args.runs_tsv, runs)
        serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.json:
            args.json.write_text(serialized)
        print(serialized, end="")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
