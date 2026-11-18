#!/usr/bin/env python3
"""Summarize Forge Job 2 JSONL rows in O hard, O soft, G hard, G soft order."""

import argparse
import json
from pathlib import Path
import re
from statistics import median

PREFIX = "info string CNT "
INFO = re.compile(r"^info depth (\d+)\b.*\bnodes (\d+)\b")
STEPS = (
    "razor", "rfp", "null_move", "probcut", "iir_no_tt", "iir_tt", "lmp",
    "quiet_futility", "history_pruning", "quiet_see", "capture_futility",
    "noisy_see", "singular", "check_extension", "lmr", "aspiration",
    "q_futility", "fail_low_bonus", "eval_swing", "draw_jitter",
)
EXTRA_EVENTS = {
    "null_move": ("null_move_tested",),
    "probcut": ("probcut_tested",),
    "singular": ("singular_double", "singular_negative"),
    "lmr": ("lmr_plies",),
}
EVENTS = tuple(
    event for step in STEPS for event in (step + "_taken", *EXTRA_EVENTS.get(step, ()))
)
COUNTERS = {
    "main_nodes", "q_nodes",
    *(step + suffix for step in STEPS for suffix in ("_tested", "_taken")),
    *(event for extras in EXTRA_EVENTS.values() for event in extras),
}
DEPTH_RANGES = ((0, 3), (3, 6), (6, 9), (9, 32))


def read_rows(path, size, soft):
    totals = {counter: [0] * 32 for counter in COUNTERS}
    fens, depths, counted_nodes, info_nodes = [], [], [], []
    with path.open(encoding="utf-8") as rows:
        for index, line in enumerate(rows, start=1):
            try:
                row = json.loads(line)
                if row["index"] != index or not row["fen"]:
                    raise ValueError("missing or out-of-order position")
                if not (match := INFO.match(row["info"])):
                    raise ValueError("missing depth/node record in last info line")
                depth, nodes = map(int, match.groups())
                if (depth, nodes) != (row["depth"], row["nodes"]):
                    raise ValueError("row does not agree with its last info line")
                raw = row["cnt"]
                if not isinstance(raw, str) or not raw.startswith(PREFIX):
                    raise ValueError("missing raw CNT line")
                counts = json.loads(raw.removeprefix(PREFIX))
                if not isinstance(counts, dict) or counts.keys() != COUNTERS:
                    raise ValueError("unexpected CNT fields")
                for event, buckets in counts.items():
                    if len(buckets) != 32 or any(type(n) is not int or n < 0 for n in buckets):
                        raise ValueError(f"expected 32 nonnegative counts for {event}")
                    totals[event] = [a + b for a, b in zip(totals[event], buckets)]
                count = sum(counts["main_nodes"]) + sum(counts["q_nodes"])
                cap = 8000 if soft else 20000
                if not 0 < count <= cap or count < nodes:
                    raise ValueError(f"CNT nodes {count} inconsistent with {nodes} info nodes and cap {cap}")
                if soft:
                    final = row["final_nodes"]
                    if type(final) is not int or count != final:
                        raise ValueError(f"CNT nodes {count} differ from softnodes final nodes {final}")
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{index}: {error}") from error
            fens.append(row["fen"])
            depths.append(depth)
            counted_nodes.append(count)
            info_nodes.append(nodes)
    if len(fens) != size:
        raise ValueError(f"{path}: expected {size} CNT lines, got {len(fens)}")
    return fens, totals, depths, counted_nodes, info_nodes


def rate(buckets, node_count):
    return sum(buckets) * 1000 / node_count


def shares(buckets):
    count = sum(buckets)
    if count == 0:
        return "n/a"
    return " / ".join(f"{sum(buckets[start:end]) * 100 / count:.1f}" for start, end in DEPTH_RANGES)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("O_hard", "O_soft", "G_hard", "G_soft"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()

    data = {}
    for dataset, size in (("O", 200), ("G", 353)):
        hard = read_rows(getattr(args, f"{dataset}_hard"), size, soft=False)
        soft = read_rows(getattr(args, f"{dataset}_soft"), size, soft=True)
        if hard[0] != soft[0]:
            raise ValueError(f"{dataset}: budget files use different positions or order")
        data[dataset] = hard, soft

    budget_labels = ("nodes 20000", "softnodes 2000")
    line_counts = [sum(len(rows[0]) for rows in (data["O"][i], data["G"][i])) for i in range(2)]
    print(f"Summed {line_counts[0]} CNT lines per budget (hard: {line_counts[0]}, soft: {line_counts[1]}).\n")
    print("| Set | Budget | CNT lines | Total nodes | Root depth median / min / max | CNT nodes median | Last info nodes median | Rows with extra CNT nodes |")
    print("|---|---|---:|---:|---|---:|---:|---:|")
    for dataset, runs in data.items():
        for budget, (_, _, depths, counted, info) in zip(budget_labels, runs):
            gap_count = sum(actual > shown for actual, shown in zip(counted, info))
            print(f"| {dataset} | {budget} | {len(counted)} | {sum(counted)} | "
                  f"{median(depths):g} / {min(depths)} / {max(depths)} | "
                  f"{median(counted):g} | {median(info):g} | {gap_count} |")

    print("\nRemaining-depth shares (%): 0–2 / 3–5 / 6–8 / 9+. Rates use actual main plus qsearch nodes.")
    print("The lmr_plies row counts plies rather than events. Tested rows are tries for null move and ProbCut.\n")
    print("| Set | Counter | Hard / 1k | Soft / 1k | Soft / hard | Hard depth shares (%) | Soft depth shares (%) |")
    print("|---|---|---:|---:|---:|---|---|")
    for dataset, ((_, hard, _, hard_nodes, _), (_, soft, _, soft_nodes, _)) in data.items():
        hard_total, soft_total = sum(hard_nodes), sum(soft_nodes)
        for event in EVENTS:
            hard_rate, soft_rate = rate(hard[event], hard_total), rate(soft[event], soft_total)
            ratio = f"{soft_rate / hard_rate:.4f}" if hard_rate else "n/a"
            print(f"| {dataset} | {event} | {hard_rate:.4f} | {soft_rate:.4f} | {ratio} | "
                  f"{shares(hard[event])} | {shares(soft[event])} |")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
