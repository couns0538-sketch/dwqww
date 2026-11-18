#!/usr/bin/env python3
"""Verify Job 10 mask openings and read S2 against the Job 10 reference."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job9 in (HERE.parent / "job9", HERE.parent / "sol-job9"):
    if (job9 / "verify_known.py").is_file() and (job9 / "summarize.py").is_file():
        sys.path.insert(0, str(job9))
        break
else:
    raise SystemExit("Job 9 verification and summary scripts are missing from adjacent job9 or sol-job9")

from summarize import BUDGETS, HISTORY, accept_replay, age_result, cell, completion, formatted, read_arm, read_games
from verify_known import compare, rows

MASKS = (3, 4, 6)


def check_meta(path, budget, mask):
    meta, reason = completion(path)
    if meta is None:
        raise ValueError(f"{path}: {reason}")
    variants = [] if mask is None else [
        {"name": "HistoryAgeKeep", "value": "729"},
        {"name": "HistoryAgeTables", "value": str(mask)},
    ]
    if meta["protocol"] != f"warm-{budget}" or meta["button_commands"] or meta["variants"] != variants:
        raise ValueError(f"{path}: wrong warm {budget} settings for mask {mask}")
    commands = [f"setoption name {variant['name']} value {variant['value']}" for variant in variants]
    replies = meta["variant_replies"]
    if [reply["command"] for reply in replies] != commands or any(
        not reply["lines"] or reply["lines"][-1] != "readyok" for reply in replies
    ):
        raise ValueError(f"{path}: missing readiness acknowledgment for an age setting")
    return meta


def checked_openings(path, baseline, baseline_exe, games, openings, budget, mask, full):
    if check_meta(path, budget, mask)["exe_sha256"] != baseline_exe:
        raise ValueError(f"{path}: executable differs from the default opening replay")
    candidate = rows(path, games if full else openings, selected=full, opening_file=not full)
    stage = "full" if full else "ply-0-only"
    return compare(f"S2 {stage}, keep 729 mask {mask} {budget}", candidate, baseline)


def default_openings(folder, openings, budget):
    path = folder / f"default-{budget}.jsonl"
    meta = check_meta(path, budget, None)
    return list(rows(path, openings, opening_file=True)), meta["exe_sha256"]


def verify_openings(raw, default_raw, games, openings, full):
    valid = True
    source = raw / ("S2-raw" if full else "S2-openings")
    for budget in BUDGETS:
        baseline, baseline_exe = default_openings(default_raw, openings, budget)
        for mask in MASKS:
            path = source / f"mask-{mask}-{budget}.jsonl"
            valid &= checked_openings(path, baseline, baseline_exe, games, openings, budget, mask, full)
    return valid


def count_agreement(arm, reference_moves):
    return sum(best == reference for best, reference in zip(arm.moves, reference_moves, strict=True))


def table(args, games, openings):
    from agreement_r import load_reference, read_positions

    keyed_positions = read_positions(args.games)
    reference = load_reference(args.r_dir, keyed_positions)
    reference_moves = [row.bestmove for row in reference]
    if len(reference_moves) != len(games):
        raise ValueError("reference and replay position counts differ")
    units = json.loads(args.units.read_text(encoding="utf-8"))
    if any(type(units[f"U_{budget}"]) is not int for budget in BUDGETS):
        raise ValueError("soft and hard ruler units must be whole agreement counts")

    results = []
    total = len(games)
    print(f"S2 reference: {len(reference_moves)} rows.")
    for budget in BUDGETS:
        warm = read_arm(args.job6_raw / f"base-warm-{budget}.jsonl", games, f"warm-{budget}", (HISTORY,))
        cold_folder = args.job6_raw if budget == "soft" else args.job8_raw
        cold = read_arm(cold_folder / f"base-cold-{budget}.jsonl", games, f"cold-{budget}", (HISTORY,))
        warm_agree = count_agreement(warm, reference_moves)
        unit = units[f"U_{budget}"]
        baseline, baseline_exe = default_openings(args.job9_openings, openings, budget)
        print(f"S2 {budget} warm baseline: {warm_agree}/{total} agree. Ruler unit: {unit:+d} agreements.")
        for mask in MASKS:
            path = args.raw / "S2-raw" / f"mask-{mask}-{budget}.jsonl"
            accepted, note = accept_replay(path, games, budget, age_mask=mask)
            if not accepted:
                results.append(f"| {mask} | {budget} | {cell(note)} |" + " n/a |" * 10)
                continue

            before = args.raw / "S2-openings" / f"mask-{mask}-{budget}.jsonl"
            if not checked_openings(before, baseline, baseline_exe, games, openings, budget, mask, full=False):
                raise ValueError(f"{before}: ply-0-only identity failed")
            if not checked_openings(path, baseline, baseline_exe, games, openings, budget, mask, full=True):
                raise ValueError(f"{path}: full-run ply-0 identity failed")

            arm = read_arm(path, games, f"warm-{budget}", (HISTORY,))
            age = age_result(arm, warm, cold, games)
            agree = count_agreement(arm, reference_moves)
            agree_pct = formatted(Fraction(100 * agree, total))
            doubling = f"{float(Fraction(agree - warm_agree, unit)):+.4f}" if unit else "n/a"
            bins = " / ".join(map(str, age.bins))
            largest = ", ".join(age.largest_bins) if age.largest_bins else "none"
            nodes, ratio, depth = (
                (str(age.nodes), formatted(age.nodes_ratio), str(age.depth_median))
                if budget == "soft"
                else ("–", "–", "–")
            )
            results.append(
                f"| {mask} | {budget} | {formatted(age.prune_rate)} | {formatted(age.prune_ratio)} | "
                f"{age.changed}/{total} ({formatted(age.changed_pct)}%) | "
                f"{age.cold_diff}/{total} ({formatted(age.cold_diff_pct)}%) | "
                f"{nodes} | {ratio} | {depth} | {bins} | {largest} | "
                f"{agree}/{total} ({agree_pct}%) | {doubling} |"
            )

    print("\n## Table S2. Additional history-age masks at keep 729\n")
    print("Rates use actual main plus quiescence nodes. Ply groups are 0, 1–9, 10–29 and 30–59. "
          "Signed doublings compare with the warm base at the same budget.\n")
    print("| Mask | Budget | Pruning / 1k | Pruning / default | Changed vs default | Changed vs cold | "
          "Soft actual nodes | Soft nodes/default | Soft median depth | Changes by ply group | "
          "Largest non-opening group | Agree with R | Doublings vs warm |")
    print("|---:|---|---:|---:|---|---|---:|---:|---:|---|---|---:|---:|")
    print("\n".join(results))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    gate = commands.add_parser("openings")
    gate.add_argument("scope", choices=("pre", "full"))
    measurements = commands.add_parser("table")
    for command in (gate, measurements):
        command.add_argument("games", type=Path)
        command.add_argument("--raw", type=Path, default=HERE)
        command.add_argument("--job9-openings", type=Path, required=True)
    for option in ("job6-raw", "job8-raw", "r-dir", "units"):
        measurements.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    games = read_games(args.games)
    openings = [position for position in games if position[1] == 0]
    if args.command == "openings":
        return 0 if verify_openings(args.raw, args.job9_openings, games, openings, args.scope == "full") else 3
    table(args, games, openings)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
