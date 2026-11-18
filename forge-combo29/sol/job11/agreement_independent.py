#!/usr/bin/env python3
"""Validate Forge Job 11's Stockfish reference and compute Table R′."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from statistics import median
import sys


for job in ("job10", "sol-job10"):
    previous = Path(__file__).resolve().parent.parent / job
    if (previous / "agreement_r.py").is_file():
        sys.path.insert(0, str(previous))
        break
else:
    raise SystemExit("Job 10 agreement_r.py is missing from the adjacent job10 or sol-job10 directory")

from agreement_r import (
    HARD_BUDGETS,
    INFO_DEPTH,
    SOFT_BUDGETS,
    agreement,
    read_arm,
    read_meta,
    read_positions,
    reference_paths,
    verify_reference_identity,
)


STOCKFISH_REVISION = "edb0d9db6731067ec50ce619ff372b463bc4dd5d"
STOCKFISH_SEARCH = "go nodes 1000000"
STOCKFISH_SETTINGS = ["setoption name Threads value 1", "setoption name Hash value 16"]


@dataclass(frozen=True, slots=True)
class StockfishRow:
    index: int
    nodes: int
    bestmove: str


def stockfish_paths(directory):
    return sorted(directory.glob("S-part*.jsonl"))


def read_stockfish(paths, positions, *, fixture_hash=None):
    if not paths:
        raise ValueError("no Stockfish rows files")
    wanted = {position.index: position for position in positions}
    rows = {}
    identity = None
    for path in paths:
        meta = read_meta(path)
        if meta.get("status") != "complete":
            raise ValueError(f"{path}: {meta.get('status', 'incomplete')}: {meta.get('error', '')}")
        if (
            meta.get("stockfish_revision") != STOCKFISH_REVISION
            or not str(meta.get("id_name", "")).startswith("id name Stockfish 19")
            or meta.get("search") != STOCKFISH_SEARCH
            or meta.get("settings_sent") != STOCKFISH_SETTINGS
            or meta.get("warm") is not False
            or meta.get("reset_commands") != ["ucinewgame", "isready"]
            or meta.get("reset_frequency") != "once per search"
        ):
            raise ValueError(f"{path}: expected official Stockfish 19, T1/Hash16 cold, {STOCKFISH_SEARCH}")
        this_identity = (meta["exe_sha256"], meta["id_name"], meta["input_sha256"],
                         meta.get("nnue_defaults"), meta.get("build_receipt_sha256"))
        if identity is None:
            identity = this_identity
        if this_identity != identity or (fixture_hash is not None and identity[2] != fixture_hash):
            raise ValueError(f"{path}: executable, UCI identity or input differs from Stockfish reference")
        first_index = last_index = count = nodes_sum = 0
        with path.open(encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                try:
                    raw = json.loads(line)
                    index = raw["index"]
                    if type(index) is not int or index <= last_index or index in rows:
                        raise ValueError("duplicate or unordered replay index")
                    position = wanted.get(index)
                    if position is None or (raw["game"], raw["ply"], raw["fen"]) != (
                        position.game, position.ply, position.fen,
                    ):
                        raise ValueError(f"unexpected position for replay index {index}")
                    info = INFO_DEPTH.match(raw["info"])
                    if not info or tuple(map(int, info.groups())) != (raw["depth"], raw["nodes"]):
                        raise ValueError("row differs from its last info depth line")
                    if not isinstance(raw["bestmove"], str) or not raw["bestmove"]:
                        raise ValueError("missing bestmove")
                    rows[index] = StockfishRow(index, raw["nodes"], raw["bestmove"])
                    if count == 0:
                        first_index = index
                    last_index = index
                    count += 1
                    nodes_sum += raw["nodes"]
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(f"{path}:{line_no}: {error}") from error
        if (
            (first_index, last_index) != (meta.get("first"), meta.get("last"))
            or count != meta.get("positions_completed")
            or nodes_sum != meta.get("last_info_nodes_sum")
        ):
            raise ValueError(f"{path}: replay range, row count or last info node sum differs from .meta")
        print(f"Read {path}: {count} rows, {nodes_sum} last reported nodes.")
    if rows.keys() != wanted.keys():
        missing = sorted(wanted.keys() - rows.keys())
        raise ValueError(f"Stockfish reference: missing {len(missing)} replay indices, first {missing[:10]}")
    ordered = [rows[position.index] for position in positions]
    if len(paths) > 1:
        nodes = sum(row.nodes for row in ordered)
        print(f"Read Stockfish S: {len(ordered)} rows, {nodes} last reported nodes across {len(paths)} shards.")
    return ordered


def load_stockfish(s_dir, positions, *, fixture_hash=None):
    return read_stockfish(stockfish_paths(s_dir), positions, fixture_hash=fixture_hash)


def check_repeat(reference, repeated):
    mismatches = []
    for original, repeat in zip(reference[:len(repeated)], repeated, strict=True):
        if (original.index, original.nodes, original.bestmove) != (repeat.index, repeat.nodes, repeat.bestmove):
            mismatches.append((original, repeat))
    print(f"S1: {len(repeated) - len(mismatches)}/{len(repeated)} match (last reported nodes, bestmove).")
    for original, repeat in mismatches[:10]:
        print(f"S1 index {original.index}: ({original.nodes}, {original.bestmove}) != "
              f"({repeat.nodes}, {repeat.bestmove}).")
    return not mismatches


def print_ruler(arms, reference):
    stats = {}
    print("\n### Table R′\n")
    print("| Forge budget | Agree with S | Agree % | a | b | z | Actual nodes | Median actual nodes |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for kind, budgets, base_budget in (
        ("softnodes", SOFT_BUDGETS, 2000), ("nodes", (*HARD_BUDGETS, 400000), 20000),
    ):
        base = arms[kind, base_budget]
        for budget in budgets:
            values = arms[kind, budget]
            result = agreement(values, base, reference)
            stats[kind, budget] = result
            actual = [row.actual_nodes for row in values]
            label = f"{kind} {budget}" if budget != 400000 else "R (nodes 400000)"
            print(f"| {label} | {result.agree} | {100*result.agree/result.total:.2f}% | "
                  f"{result.a} | {result.b} | {result.z:.4f} | {sum(actual)} | {median(actual)} |")
    return stats


def run(args):
    positions = read_positions(args.games)
    fixture_hash = sha256(args.games.read_bytes()).hexdigest()
    source_paths = stockfish_paths(args.s_dir)
    stockfish = read_stockfish(source_paths, positions, fixture_hash=fixture_hash)
    repeat_path = args.s_dir / "S1.jsonl"
    repeated = read_stockfish([repeat_path], positions[:300], fixture_hash=fixture_hash)
    first_meta, repeat_meta = read_meta(source_paths[0]), read_meta(repeat_path)
    for field in ("exe_sha256", "id_name", "nnue_defaults", "build_receipt_sha256"):
        if first_meta.get(field) != repeat_meta.get(field):
            raise ValueError(f"S1 {field} differs from S")
    if not check_repeat(stockfish, repeated):
        print("STOP: S1 identity failed.")
        return 1
    if args.gates_only:
        return 0

    paths = {(kind, budget): args.ruler_dir / f"{kind}-{budget}.jsonl"
             for kind, budgets in (("softnodes", SOFT_BUDGETS), ("nodes", HARD_BUDGETS))
             for budget in budgets}
    paths["softnodes", 2000] = args.soft_base
    paths["nodes", 20000] = args.hard_base
    forge_r_paths = reference_paths(args.r_dir)
    verify_reference_identity([*forge_r_paths, *paths.values()], args.games)
    arms = {key: read_arm(path, positions, f"go {key[0]} {key[1]}") for key, path in paths.items()}
    arms["nodes", 400000] = read_arm(forge_r_paths, positions, "go nodes 400000", label="R")
    stats = print_ruler(arms, stockfish)
    u_soft = stats["softnodes", 4000].delta
    u_hard = stats["nodes", 40000].delta
    print(f"\nRuler units: U′_soft = {u_soft}, U′_hard = {u_hard}.")
    passed = True
    for kind, budget in (("softnodes", 500), ("nodes", 5000)):
        control = stats[kind, budget]
        passed &= control.z <= -3
        print(f"{kind} {budget} negative control: a={control.a}, b={control.b}, z={control.z:.4f}, "
              f"{'PASS' if control.z <= -3 else 'FAIL'}.")
    if not passed:
        print("STOP: at least one negative control failed against S.")
        return 1
    if args.units_json:
        units = {"U_soft": u_soft, "U_hard": u_hard}
        args.units_json.write_text(json.dumps(units, indent=2) + "\n", encoding="utf-8")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--s-dir", type=Path, required=True)
    parser.add_argument("--r-dir", type=Path)
    parser.add_argument("--ruler-dir", type=Path)
    parser.add_argument("--soft-base", type=Path)
    parser.add_argument("--hard-base", type=Path)
    parser.add_argument("--units-json", type=Path)
    parser.add_argument("--gates-only", action="store_true")
    args = parser.parse_args()
    if not args.gates_only and any(path is None for path in (args.r_dir, args.ruler_dir, args.soft_base, args.hard_base)):
        parser.error("--r-dir, --ruler-dir, --soft-base, and --hard-base are required for Table R′")
    try:
        return run(args)
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
