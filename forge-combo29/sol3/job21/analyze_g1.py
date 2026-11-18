#!/usr/bin/env python3
"""Compute Job 21 Tables A, B and C from the measured G1 rows."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

FIELDS = (
    "game ply pieces last_depth last_nodes last_time_ms final_nodes wall_ns cap "
    "prev_depth prev_nodes prev2_depth prev2_nodes bestmove root_fen"
).split()
TARGET = 2000
HARD = 4 * TARGET
MS_NS = 1_000_000
K_VALUES = (1, 2, 3, 4, 6, 8)
FINAL_LINE = re.compile(r"info string softnodes nodes (\d+)")
PIECE_GROUPS = ((25, 32, "25+"), (13, 24, "13–24"), (2, 12, "12 or fewer"))


@dataclass(frozen=True)
class Iteration:
    depth: int
    nodes: int


@dataclass(frozen=True)
class Row:
    game: int
    ply: int
    pieces: int
    last: Iteration
    last_time_ms: int
    final_nodes: int
    wall_ns: int
    cap: bool
    prev: Iteration | None
    prev2: Iteration | None
    bestmove: str
    root_fen: str

    @property
    def key(self):
        return (self.game, self.ply)

    @property
    def tail_nodes(self):
        return self.final_nodes - self.last.nodes

    @property
    def wall_after_info_ns(self):
        return self.wall_ns - self.last_time_ms * MS_NS


def iteration(row, prefix):
    depth, nodes = row[f"{prefix}_depth"], row[f"{prefix}_nodes"]
    if depth == nodes == "":
        return None
    result = Iteration(int(depth), int(nodes))
    if result.depth < 0 or result.nodes < 0:
        raise ValueError(f"negative depth or node count in {prefix}")
    return result


def read_rows(path):
    rows = []
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path}: unexpected TSV header {reader.fieldnames}")
        for number, raw in enumerate(reader, 2):
            try:
                if None in raw or any(value is None for value in raw.values()):
                    raise ValueError("wrong number of TSV fields")
                last = iteration(raw, "last")
                if last is None:
                    raise ValueError("missing last iteration")
                cap = int(raw["cap"])
                if cap not in (0, 1):
                    raise ValueError("cap must be 0 or 1")
                row = Row(
                    int(raw["game"]), int(raw["ply"]), int(raw["pieces"]), last,
                    int(raw["last_time_ms"]), int(raw["final_nodes"]), int(raw["wall_ns"]), bool(cap),
                    iteration(raw, "prev"), iteration(raw, "prev2"), raw["bestmove"], raw["root_fen"],
                )
                if not (41 <= row.game <= 140 and 1 <= row.ply <= 200 and 2 <= row.pieces <= 32):
                    raise ValueError("game, ply or pieces outside G1 range")
                if row.last_time_ms < 0 or row.wall_ns < 0 or row.tail_nodes < 0:
                    raise ValueError("negative timing or final node count below last completed count")
                if row.cap != (row.tail_nodes > 0):
                    raise ValueError("cap flag disagrees with final_nodes > last_nodes")
                fen_fields = row.root_fen.split()
                if len(fen_fields) != 6 or sum(c in "prnbqkPRNBQK" for c in fen_fields[0]) != row.pieces:
                    raise ValueError(f"piece count disagrees with FEN {row.root_fen!r}")
                rows.append(row)
            except (ValueError, TypeError) as error:
                raise ValueError(f"{path}:{number}: {error}") from error
    return rows


def ratio(numerator, denominator):
    return None if denominator == 0 else 100 * numerator / denominator


def sizes(rows):
    return {
        "searches": len(rows),
        "last_info_nodes": sum(row.last.nodes for row in rows),
        "final_nodes": sum(row.final_nodes for row in rows),
        "excess_nodes": sum(row.tail_nodes for row in rows),
        "last_info_time_ms": sum(row.last_time_ms for row in rows),
        "wall_ns": sum(row.wall_ns for row in rows),
    }


def summarize(rows):
    capped = [row for row in rows if row.cap]
    all_totals = sizes(rows)
    cap_totals = sizes(capped)
    tail_ns = sum(row.wall_after_info_ns for row in capped)
    return {
        "all": all_totals,
        "cap": cap_totals,
        "noncap": sizes([row for row in rows if not row.cap]),
        "cap_share_searches_pct": ratio(len(capped), len(rows)),
        "excess_share_all_nodes_pct": ratio(cap_totals["excess_nodes"], all_totals["final_nodes"]),
        "excess_share_capped_nodes_pct": ratio(cap_totals["excess_nodes"], cap_totals["final_nodes"]),
        "wall_minus_last_info_on_cap_ns": tail_ns,
        "estimated_tail_share_all_wall_pct": ratio(tail_ns, all_totals["wall_ns"]),
        "estimated_tail_share_capped_wall_pct": ratio(tail_ns, cap_totals["wall_ns"]),
        "last_info_time_truncation_budget_ns": len(capped) * MS_NS,
        "cap_negative_wall_minus_info": sum(row.wall_after_info_ns < 0 for row in capped),
    }


def address(row):
    return {"game": row.game, "ply": row.ply, "pieces": row.pieces}


def triplet(row):
    values = (row.prev2, row.prev, row.last)
    return [None if it is None else {"depth": it.depth, "nodes": it.nodes} for it in values]


def adjacent(previous, current):
    return previous is not None and previous.depth + 1 == current.depth and previous.nodes <= current.nodes


def depth_issues(row):
    checks = ((row.prev2, row.prev, "prev2→prev"), (row.prev, row.last, "prev→last"))
    issues = []
    for previous, current, name in checks:
        if previous is None:
            continue
        if current is None:
            issues.append(f"{name}: missing next snapshot")
        elif current.depth <= previous.depth:
            issues.append(f"{name}: duplicate or descending depth")
        elif current.depth != previous.depth + 1:
            issues.append(f"{name}: gap in depth")
        if current is not None and current.nodes < previous.nodes:
            issues.append(f"{name}: descending cumulative nodes")
    if row.prev is None and row.last.depth > 1:
        issues.append("last depth exceeds 1 but previous snapshot is missing")
    if row.prev is not None and row.prev2 is None and row.prev.depth > 1:
        issues.append("previous depth exceeds 1 but antepenultimate snapshot is missing")
    return issues


def accepts(current, previous, multiplier):
    return (
        adjacent(previous, current)
        and current.nodes < TARGET
        and current.nodes + multiplier * (current.nodes - previous.nodes) > HARD
    )


def depth_histogram(rows):
    return dict(sorted(Counter(row.last.depth for row in rows).items()))


def rules(rows):
    final_nodes = sum(row.final_nodes for row in rows)
    with_valid_last_pair = [row for row in rows if adjacent(row.prev, row.last)]
    with_valid_triplet = [
        row for row in with_valid_last_pair if adjacent(row.prev2, row.prev)
    ]
    final_candidates = [row for row in with_valid_last_pair if row.cap and row.last.nodes < TARGET]
    completed_candidates = [row for row in with_valid_triplet if row.prev.nodes < TARGET]
    literal_candidates = [row for row in completed_candidates if row.last.nodes < TARGET]
    output = {
        "capped_candidate_count": len(final_candidates),
        "capped_missing_previous_count": sum(row.prev is None and row.last.nodes < TARGET for row in rows if row.cap),
        "completed_candidate_count": len(completed_candidates),
        "completed_candidate_count_literal_last_below_target": len(literal_candidates),
        "rows": {},
    }
    for multiplier in K_VALUES:
        cap = [row for row in final_candidates if accepts(row.last, row.prev, multiplier)]
        false = [row for row in completed_candidates if accepts(row.prev, row.prev2, multiplier)]
        false_literal = [row for row in false if row.last.nodes < TARGET]
        false_keys = {row.key for row in false}
        overlap = [row for row in cap if row.key in false_keys]
        savings = sum(row.tail_nodes for row in cap)
        overlap_nodes = sum(row.tail_nodes for row in overlap)
        output["rows"][multiplier] = {
            "capped_searches_stopped": len(cap),
            "tail_nodes_upper_bound": savings,
            "share_all_nodes_upper_bound_pct": ratio(savings, final_nodes),
            "false_stop_searches": len(false),
            "completed_depths_lost": depth_histogram(false),
            "false_stop_searches_literal_last_below_target": len(false_literal),
            "completed_depths_lost_literal_last_below_target": depth_histogram(false_literal),
            "overlap_searches": len(overlap),
            "overlap_tail_nodes": overlap_nodes,
            "capped_without_observed_earlier_false_stop": len(cap) - len(overlap),
            "tail_nodes_excluding_overlap": savings - overlap_nodes,
            "capped_positions": [address(row) | {"iterations": triplet(row), "final_nodes": row.final_nodes} for row in cap],
            "false_stop_positions": [
                address(row) | {
                    "iterations": triplet(row), "lost_depth": row.last.depth,
                    "actual_final_completed_below_target": row.last.nodes < TARGET,
                } for row in false
            ],
        }
    return output


def parse_info(line):
    tokens = line.split()
    return (
        Iteration(int(tokens[2]), int(tokens[tokens.index("nodes") + 1])),
        int(tokens[tokens.index("time") + 1]),
    )


def compare_raw(root, aggregate_rows):
    aggregate = {row.key: row for row in aggregate_rows}
    seen = set()
    odd = []
    files = []
    for stdout in sorted(root.rglob("engine.stdout.txt")):
        tsv = stdout.with_name("rows.tsv")
        if not tsv.is_file():
            continue
        expected = read_rows(tsv)
        frames = []
        latest = []
        final = []
        for line in stdout.read_text().splitlines():
            if line.startswith("info depth "):
                latest.append(parse_info(line))
            if line.startswith("info string softnodes nodes"):
                marker = FINAL_LINE.fullmatch(line)
                if marker is None:
                    raise ValueError(f"{stdout}: malformed softnodes line {line!r}")
                final.append(int(marker[1]))
            if line.startswith("bestmove "):
                frames.append((latest, final, line.split()[1]))
                latest, final = [], []
        if len(frames) != len(expected) or latest or final:
            raise ValueError(f"{stdout}: expected {len(expected)} completed searches, got {len(frames)}")
        for row, (infos, final, bestmove) in zip(expected, frames):
            if row.key in seen or aggregate.get(row.key) != row:
                raise ValueError(f"{tsv}: duplicate or inconsistent aggregate row {row.key}")
            seen.add(row.key)
            actual = [it for it, _ in infos[-3:]]
            reported = [it for it in (row.prev2, row.prev, row.last) if it is not None]
            if actual != reported or not infos or infos[-1][1] != row.last_time_ms or final != [row.final_nodes] or bestmove != row.bestmove:
                raise ValueError(f"{stdout}: raw search differs from TSV at game {row.game}, ply {row.ply}")
            problems = []
            for (old, old_ms), (new, new_ms) in zip(infos, infos[1:]):
                if not adjacent(old, new):
                    problems.append({"depths": [old.depth, new.depth], "nodes": [old.nodes, new.nodes]})
                if new_ms < old_ms:
                    problems.append({"depths": [old.depth, new.depth], "times_ms": [old_ms, new_ms]})
            if problems:
                odd.append(address(row) | {"problems": problems})
        files.append(str(stdout.relative_to(root)))
    if seen != set(aggregate):
        missing = sorted(set(aggregate) - seen)
        raise ValueError(f"{root}: raw readback is missing {len(missing)} aggregate rows, first {missing[:1]}")
    return {"raw_files": files, "searches_verified": len(seen), "out_of_order_duplicate_gap_or_reverse_rows": odd}


def analysis(rows):
    keys = [row.key for row in rows]
    if keys != sorted(set(keys)):
        raise ValueError("rows.tsv must be in increasing game/ply order with no duplicate")
    by_pieces = {
        label: summarize([row for row in rows if minimum <= row.pieces <= maximum])
        for minimum, maximum, label in PIECE_GROUPS
    }
    by_depth = {
        depth: summarize([row for row in rows if row.last.depth == depth])
        for depth in sorted({row.last.depth for row in rows})
    }
    return {
        "games_with_searches": len({row.game for row in rows}),
        "searches": len(rows),
        "soft_target_nodes": TARGET,
        "hard_cap_nodes": HARD,
        "table_A": summarize(rows),
        "table_B_by_piece_count": by_pieces,
        "table_B_by_last_completed_depth": by_depth,
        "table_C": rules(rows),
        "anomalies": {
            "depth_snapshot_issues": [
                address(row) | {"iterations": triplet(row), "issues": issues}
                for row in rows if (issues := depth_issues(row))
            ],
            "cap_flag_below_hard_node_threshold": [address(row) for row in rows if row.cap and row.final_nodes < HARD],
            "hard_node_threshold_seen_without_node_gap": [address(row) for row in rows if not row.cap and row.final_nodes >= HARD],
            "cap_with_last_completed_at_or_above_soft_target": [address(row) for row in rows if row.cap and row.last.nodes >= TARGET],
            "negative_wall_minus_info_on_cap": [
                address(row) | {"wall_ns": row.wall_ns, "last_time_ms": row.last_time_ms}
                for row in rows if row.cap and row.wall_after_info_ns < 0
            ],
        },
        "interpretation": {
            "time": "An estimate from wall through bestmove minus Forge's truncated-ms last depth time on capped searches, divided by total measured wall. Different clock origins and UCI/dispatch overhead also enter the estimate.",
            "cap": "Flag exactly means final nodes exceed last completed depth nodes. The 8,000 node test is a consistency check.",
            "rule": "At the final boundary test cap savings against n_d and n_(d-1). At the penultimate boundary test a false stop before the observed completed d using n_(d-1) and n_(d-2). Each boundary requires its own current snapshot below 2,000.",
            "literal_sensitivity": "Restrict the false-stop test to searches where the actual final completed snapshot is also below 2,000.",
            "overlap": "Report boundary outcomes separately and also exclude cap rows with an earlier observed false stop. No earlier boundary is reconstructed from the G1 TSV.",
            "upper_bound": "Tail nodes saved in replay are a local upper bound because the skipped work leaves fewer hash entries for later searches, and changed moves can change subsequent positions.",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rows", type=Path)
    parser.add_argument("--raw-root", type=Path, help="optional saved per-game logs to audit without using them for table calculations")
    args = parser.parse_args()
    try:
        rows = read_rows(args.rows)
        output = analysis(rows)
        output["rows_sha256"] = hashlib.sha256(args.rows.read_bytes()).hexdigest()
        if args.raw_root is not None:
            output["raw_readback"] = compare_raw(args.raw_root, rows)
    except (OSError, ValueError, IndexError, KeyError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
