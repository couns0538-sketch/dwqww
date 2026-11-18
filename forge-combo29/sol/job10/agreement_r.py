#!/usr/bin/env python3
"""Validate the deep reference and compute Forge Job 10's agreement ruler."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from pathlib import Path
import re
from statistics import median
import sys


COUNTER_PREFIX = "info string CNT "
INFO_DEPTH = re.compile(r"^info depth (\d+)\b.*\bnodes (\d+)\b")
SOFT_BUDGETS = (500, 1000, 2000, 4000, 8000)
HARD_BUDGETS = (5000, 10000, 20000, 40000)


@dataclass(frozen=True, slots=True)
class Position:
    index: int
    game: int
    ply: int
    fen: str


@dataclass(frozen=True, slots=True)
class SearchRow:
    index: int
    game: int
    ply: int
    fen: str
    depth: int
    nodes: int
    actual_nodes: int
    bestmove: str
    cnt: str


@dataclass(frozen=True, slots=True)
class Agreement:
    agree: int
    base_agree: int
    a: int
    b: int
    z: float
    total: int

    @property
    def delta(self):
        return self.b - self.a

    def doublings(self, unit):
        return self.delta / unit if unit else None


def read_positions(games):
    positions = []
    with games.open(encoding="utf-8") as stream:
        for game in range(1, 31):
            fields = stream.readline().rstrip("\r\n").split("\t")
            if len(fields) != 4 or fields[0] != str(game):
                raise ValueError(f"{games}:{game}: expected game index, FEN, moves and reason")
            _, fen, moves, reason = fields
            if not fen or not reason or len(moves.split()) != 60:
                raise ValueError(f"{games}:{game}: expected an original FEN and 60 plies")
            positions.extend(Position(len(positions) + 1, game, ply, fen) for ply in range(60))
    return positions


def read_meta(path):
    return json.loads(path.with_name(path.name + ".meta").read_text(encoding="utf-8"))


def counter_nodes(raw):
    if not isinstance(raw, str) or not raw.startswith(COUNTER_PREFIX):
        raise ValueError("missing raw CNT line")
    payload = json.loads(raw.removeprefix(COUNTER_PREFIX))
    total = 0
    for name in ("main_nodes", "q_nodes"):
        buckets = payload[name]
        if (not isinstance(buckets, list) or len(buckets) != 32
                or any(type(count) is not int or count < 0 for count in buckets)):
            raise ValueError(f"invalid CNT node buckets for {name}")
        if name == "q_nodes" and any(buckets[1:]):
            raise ValueError("qsearch nodes outside bucket zero")
        total += sum(buckets)
    return total


def read_arm(paths, positions, search, *, label=None):
    if isinstance(paths, Path):
        paths = (paths,)
    if not paths:
        raise ValueError(f"{label or search}: no rows files")
    command, kind, budget_text = search.split()
    if command != "go" or kind not in {"nodes", "softnodes"}:
        raise ValueError(f"unsupported UCI search {search}")
    budget = int(budget_text)
    cap = 4 * budget if kind == "softnodes" else budget
    wanted = {position.index: position for position in positions}
    rows = {}
    for path in paths:
        meta = read_meta(path)
        if meta.get("status") != "complete":
            raise ValueError(f"{path}: {meta.get('status', 'incomplete')}: {meta.get('error', '')}")
        if meta.get("search") != search:
            raise ValueError(f"{path}: .meta search {meta.get('search')!r} differs from {search!r}")
        count = nodes_sum = info_nodes_sum = 0
        last_index = 0
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
                    match = INFO_DEPTH.match(raw["info"])
                    if not match or tuple(map(int, match.groups())) != (raw["depth"], raw["nodes"]):
                        raise ValueError("row differs from its last info depth line")
                    if not isinstance(raw["bestmove"], str) or not raw["bestmove"]:
                        raise ValueError("missing bestmove")
                    actual_nodes = counter_nodes(raw["cnt"])
                    if not 0 <= raw["nodes"] <= actual_nodes <= cap:
                        raise ValueError(f"inconsistent info/CNT nodes or above cap {cap}")
                    if kind == "softnodes" and (
                        raw["final_nodes"] != actual_nodes
                        or raw["final_nodes_info"] != f"info string softnodes nodes {actual_nodes}"
                    ):
                        raise ValueError("softnodes final count differs from CNT nodes")
                    rows[index] = SearchRow(
                        index, position.game, position.ply, position.fen, raw["depth"],
                        raw["nodes"], actual_nodes, raw["bestmove"], raw["cnt"],
                    )
                    last_index = index
                    count += 1
                    nodes_sum += actual_nodes
                    info_nodes_sum += raw["nodes"]
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError(f"{path}:{line_no}: {error}") from error
        if count != meta.get("positions_completed") or info_nodes_sum != meta.get("last_info_nodes_sum"):
            raise ValueError(f"{path}: row count or last info node sum differs from .meta")
        print(f"Read {path}: {count} rows, {nodes_sum} actual nodes.")
    if rows.keys() != wanted.keys():
        missing = sorted(wanted.keys() - rows.keys())
        raise ValueError(f"{label or search}: missing {len(missing)} replay indices, first {missing[:10]}")
    ordered = [rows[position.index] for position in positions]
    if len(paths) > 1:
        nodes = sum(row.actual_nodes for row in ordered)
        print(f"Read {label or search}: {len(ordered)} rows, {nodes} actual nodes across {len(paths)} shards.")
    return ordered


def reference_paths(r_dir):
    return sorted(r_dir.glob("R-part*.jsonl"))


def load_reference(r_dir, positions):
    return read_arm(reference_paths(r_dir), positions, "go nodes 400000", label="R")


def agreement(arm, base, reference):
    agree = base_agree = a = b = 0
    for result, control, answer in zip(arm, base, reference, strict=True):
        if result.index != control.index or result.index != answer.index:
            raise ValueError("arm, baseline and reference replay indices differ")
        arm_equal = result.bestmove == answer.bestmove
        base_equal = control.bestmove == answer.bestmove
        agree += arm_equal
        base_agree += base_equal
        a += base_equal and not arm_equal
        b += arm_equal and not base_equal
    return Agreement(agree, base_agree, a, b, (b - a) / sqrt(a + b) if a + b else 0, len(reference))


def gates(reference, r1, original_soft, r2):
    fields = ("nodes", "actual_nodes", "bestmove")
    passed = True
    for label, expected, actual, check_fields in (
        ("R1", reference[:300], r1, fields),
        ("R2", original_soft[:300], r2, (*fields, "cnt")),
    ):
        differences = []
        for original, repeat in zip(expected, actual, strict=True):
            changed = [field for field in check_fields if getattr(original, field) != getattr(repeat, field)]
            if changed:
                differences.append((original.index, ", ".join(changed)))
        equal = len(actual) - len(differences)
        print(f"{label}: {equal}/{len(actual)} match ({', '.join(check_fields)}).")
        for index, changed in differences[:10]:
            print(f"{label} mismatch at replay index {index}: {changed}.")
        passed &= not differences
    return passed


def verify_reference_identity(paths, games):
    fixture = hashlib.sha256(games.read_bytes()).hexdigest()
    expected = None
    for path in paths:
        meta = read_meta(path)
        identity = (meta["exe_sha256"], meta["id_name"], meta["settings_sent"])
        if expected is None:
            expected = identity
        if identity != expected or meta.get("input_sha256") != fixture:
            raise ValueError(f"{path}: engine, UCI settings or replay input differs from R")
        if meta.get("warm") is not False or meta.get("reset_frequency") != "once per search":
            raise ValueError(f"{path}: expected a cold reset before every position")
    if expected is not None:
        print(f"Reference and ruler use {expected[1]} with executable SHA-256 {expected[0]}.")


def print_ruler(arms, reference):
    stats = {}
    print("\n### Table R\n")
    print("| Budget | Agree | Agree % | a | b | z | Actual nodes | Median actual nodes |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for kind, budgets, base_budget in (
        ("softnodes", SOFT_BUDGETS, 2000), ("nodes", HARD_BUDGETS, 20000),
    ):
        base = arms[kind, base_budget]
        for budget in budgets:
            values = arms[kind, budget]
            result = agreement(values, base, reference)
            stats[kind, budget] = result
            actual = [row.actual_nodes for row in values]
            print(f"| {kind} {budget} | {result.agree} | {100*result.agree/result.total:.2f}% | "
                  f"{result.a} | {result.b} | {result.z:.4f} | {sum(actual)} | {median(actual)} |")
    return stats


def run(args):
    positions = read_positions(args.games)
    r1_path = args.r_dir / "R1.jsonl"
    r2_path = args.r_dir / "R2.jsonl"
    verify_reference_identity([*reference_paths(args.r_dir), r1_path, r2_path, args.soft_base], args.games)
    reference = load_reference(args.r_dir, positions)
    r1 = read_arm(r1_path, positions[:300], "go nodes 400000")
    r2 = read_arm(r2_path, positions[:300], "go softnodes 2000")
    soft_base = read_arm(args.soft_base, positions, "go softnodes 2000")
    if not gates(reference, r1, soft_base, r2):
        print("STOP: R1 or R2 identity failed.")
        return 1
    if args.gates_only:
        return 0

    paths = {(kind, budget): args.ruler_dir / f"{kind}-{budget}.jsonl"
             for kind, budgets in (("softnodes", SOFT_BUDGETS), ("nodes", HARD_BUDGETS))
             for budget in budgets}
    paths["softnodes", 2000] = args.soft_base
    paths["nodes", 20000] = args.hard_base
    verify_reference_identity([*reference_paths(args.r_dir), *paths.values()], args.games)
    arms = {key: soft_base if key == ("softnodes", 2000)
            else read_arm(path, positions, f"go {key[0]} {key[1]}")
            for key, path in paths.items()}
    stats = print_ruler(arms, reference)
    u_soft = stats["softnodes", 4000].delta
    u_hard = stats["nodes", 40000].delta
    print(f"\nRuler units: U_soft = {u_soft}, U_hard = {u_hard}.")
    passed = True
    for kind, budget in (("softnodes", 500), ("nodes", 5000)):
        result = stats[kind, budget]
        passed &= result.z <= -3
        print(f"{kind} {budget} negative control: a={result.a}, b={result.b}, z={result.z:.4f}, "
              f"{'PASS' if result.z <= -3 else 'FAIL'}.")
    if not passed:
        print("STOP: at least one negative control failed.")
        return 1
    if args.units_json:
        args.units_json.write_text(json.dumps({"U_soft": u_soft, "U_hard": u_hard}, indent=2) + "\n", encoding="utf-8")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--r-dir", type=Path, required=True)
    parser.add_argument("--ruler-dir", type=Path)
    parser.add_argument("--soft-base", type=Path, required=True)
    parser.add_argument("--hard-base", type=Path)
    parser.add_argument("--units-json", type=Path)
    parser.add_argument("--gates-only", action="store_true")
    args = parser.parse_args()
    if not args.gates_only and (args.ruler_dir is None or args.hard_base is None):
        parser.error("--ruler-dir and --hard-base are required for Table R")
    try:
        return run(args)
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"STOP: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
