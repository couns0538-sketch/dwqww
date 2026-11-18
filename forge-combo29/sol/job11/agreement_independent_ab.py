#!/usr/bin/env python3
"""Compare Job 11 independent-reference agreement with Job 10 on the same Forge arms."""

import argparse
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job10 in (HERE.parent / "job10", HERE.parent / "sol-job10"):
    if (job10 / "agreement_r.py").is_file() and (job10 / "agreement_ab.py").is_file():
        sys.path.insert(0, str(job10))
        break
else:
    raise SystemExit("Expected Job 10's agreement readers in adjacent job10 or sol-job10")

from agreement_ab import (
    ArmComparison, BUDGETS, DIRECTIONS, direction_choice, flagged, load, number, ratio_grade,
    read_settings, reports_b, signed, table_b_cell, tidy, units_for,
)
from agreement_r import Agreement, agreement, load_reference, read_positions
from agreement_independent import load_stockfish

A_FORECASTS = tuple((arm, budget) for arm in ("warm-base", "W1", "W2", "S-5") for budget in BUDGETS)
B_FORECASTS = ("soft", "hard", "negative")
REFS = ("R", "S")


@dataclass
class PairedReference:
    forge: Agreement | None = None
    stockfish: Agreement | None = None
    note: str = ""

    def select(self, reference):
        return self.forge if reference == "R" else self.stockfish


def compare_both(rows, base, references, note=""):
    if rows is None:
        return PairedReference(note=note)
    return PairedReference(
        agreement(rows, base, references["R"]), agreement(rows, base, references["S"]),
    )


def gather_a(args, positions, anchors, references):
    results = {}
    for budget in BUDGETS:
        warm, cold = anchors["warm", budget], anchors["cold", budget]
        results["warm-base", budget] = compare_both(warm, cold, references)
        replay_paths = {
            **{
                f"S-{mask}": args.job9_s / f"mask-{mask}-{budget}.jsonl"
                for mask in (1, 2, 5, 7)
            },
            **{
                f"S-{mask}": args.job10_s2 / f"mask-{mask}-{budget}.jsonl"
                for mask in (3, 4, 6)
            },
            **{arm: args.job9_w / f"{arm}-{budget}.jsonl" for arm in ("W1", "W2")},
            **{
                f"keep-{keep}": args.job8_age / f"keep-{keep}-warm-{budget}.jsonl"
                for keep in (896, 768, 512, 256, 0)
            },
        }
        for name, path in replay_paths.items():
            rows, note = load(path, positions, budget, f"A' {name} {budget}", optional=True)
            results[name, budget] = compare_both(rows, warm, references, note)
    return results


def gather_b(args, settings, positions, anchors, references):
    results = {}
    for setting in settings:
        for budget in BUDGETS:
            for direction in DIRECTIONS:
                key = setting.name, budget, direction
                if setting.value(direction) == "-":
                    results[key] = PairedReference(note="out of range")
                    continue
                if setting.status == "skip":
                    results[key] = PairedReference(
                        note=f"skipped: expected start {setting.start}, observed {setting.actual}",
                    )
                    continue
                source = args.job6_raw if budget == "soft" else args.job8_raw
                path = source / f"{setting.name}-{direction}-cold-{budget}.jsonl"
                rows, note = load(path, positions, budget, f"B' {setting.name} {direction} {budget}", optional=True)
                results[key] = compare_both(rows, anchors["cold", budget], references, note)
    return results


def read_prediction(path):
    a, b = {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        content = line.split()
        if len(content) == 4 and content[0] == "A" and tuple(content[1:3]) in A_FORECASTS:
            key = tuple(content[1:3])
            if key in a:
                raise ValueError(f"{path}: duplicate forecast for {key}")
            a[key] = content[3], number(content[3])
        if len(content) == 3 and content[0] == "B" and content[1] in B_FORECASTS:
            key = content[1]
            if key in b:
                raise ValueError(f"{path}: duplicate forecast for B {key}")
            guess = number(content[2])
            maximum = 152 if key == "negative" else 76
            if guess.denominator != 1 or not 0 <= guess <= maximum:
                raise ValueError(f"{path}: expected a whole count from 0 to {maximum} for {key}")
            b[key] = content[2], guess
    if a.keys() != set(A_FORECASTS) or b.keys() != set(B_FORECASTS):
        raise ValueError(f"{path}: expected eight A and three B forecasts")
    return a, b


def load_units(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    units = {budget: data["U_" + budget] for budget in BUDGETS}
    if any(type(value) is not int for value in units.values()):
        raise ValueError(f"{path}: expected signed integer ruler units")
    return units


def projection(views, reference):
    return {key: ArmComparison(view.select(reference), view.note) for key, view in views.items()}


def negative_deltas(views, budget=None):
    measured = [
        view.result for key, view in views.items()
        if view.result is not None and (budget is None or key[1] == budget)
    ]
    return sum(result.delta < 0 for result in measured), len(measured)


def print_grades(a, b_stockfish, units, predictions):
    forecasts_a, forecasts_b = predictions
    print("## Prediction grades\n")
    print("A nonzero forecast requires the observed sign and a magnitude within a factor of 1.5. "
          "A zero forecast requires zero. Incomplete totals and undefined ruler effects remain ungraded.\n")
    print("| Table | Arm or statistic | Budget | Guess | Observed | Grade |")
    print("|---|---|---|---:|---:|---|")
    verdicts = []
    for name, budget in A_FORECASTS:
        view = a[name, budget]
        actual = units_for(view.stockfish, units[budget]) if view.stockfish is not None else None
        text, guess = forecasts_a[name, budget]
        verdict = ratio_grade(guess, actual)
        verdicts.append(verdict)
        reason = view.note or ("zero Stockfish ruler delta" if actual is None else "")
        display = verdict + (f": {reason}" if reason else "")
        print(f"| A' | {name} | {budget} | {text} | {signed(actual)} | {tidy(display)} |")
    for budget, measured, nflag in reports_b(b_stockfish):
        text, guess = forecasts_b[budget]
        verdict = ratio_grade(guess, Fraction(nflag) if measured == 76 else None)
        verdicts.append(verdict)
        print(f"| B' | Arms reaching abs(z) ≥ 3 | {budget} | {text} | {nflag}/{measured} measured | {verdict} |")
    negative, size = negative_deltas(b_stockfish)
    text, guess = forecasts_b["negative"]
    verdict = ratio_grade(guess, Fraction(negative) if size == 152 else None)
    verdicts.append(verdict)
    print(f"| B' | Negative deltas | both | {text} | {negative}/{size} measured | {verdict} |")
    print(
        f"\n{sum(v.startswith('KILLED') for v in verdicts)} KILLED, "
        f"{verdicts.count('survives')} survive, {verdicts.count('ungraded')} ungraded.\n"
    )


def a_cells(result, unit, note):
    if result is None:
        return [tidy(note), "n/a", "n/a", "n/a", "n/a"]
    rate = 100 * Fraction(result.agree, result.total)
    return [
        f"{result.agree}/{result.total} ({float(rate):.4f}%)",
        str(result.a), str(result.b), signed(result.z), signed(units_for(result, unit)),
    ]


def print_a(views, units):
    print("## Table A'. Replay-arm agreement against Forge R and Stockfish S\n")
    print("| Arm | Budget | Matched base | Agree R | a R | b R | z R | Doublings R | "
          "Agree S | a S | b S | z S | Doublings S |")
    print("|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|")
    for (name, budget), view in views.items():
        baseline = f"{'cold' if name == 'warm-base' else 'warm'} {budget}"
        cells = [name, budget, baseline]
        for ref in REFS:
            cells.extend(a_cells(view.select(ref), units[ref][budget], view.note))
        print("| " + " | ".join(cells) + " |")
    print()


def print_b(views, settings, units):
    print("## Table B'. One-step tuning arms against Forge R and Stockfish S\n")
    print("Each comparison cell gives agreement-count delta, z and effect in doublings. "
          "† marks exact abs(z) ≥ 3 before rounding.\n")
    headings = [f"{b.capitalize()} {d} {r}" for b in BUDGETS for d in DIRECTIONS for r in REFS]
    print("| Setting | " + " | ".join(headings) + " |")
    print("|---|" + "---|" * len(headings))
    compared = {ref: projection(views, ref) for ref in REFS}
    for setting in settings:
        row = [
            table_b_cell(compared[r][setting.name, budget, direction], units[r][budget])
            for budget in BUDGETS for direction in DIRECTIONS for r in REFS
        ]
        print(f"| {setting.name} | " + " | ".join(row) + " |")

    print("\n### Arms reaching abs(z) ≥ 3 against either reference\n")
    print("| Setting | Budget | Direction | Flagged against | Delta R | z R | Delta S | z S | "
          "Higher agreement direction R | Higher agreement direction S |")
    print("|---|---|---|---|---:|---:|---:|---:|---|---|")
    for setting in settings:
        for budget in BUDGETS:
            flagged_refs = {
                ref for ref in REFS if any(
                    (score := compared[ref][setting.name, budget, d].result) is not None and flagged(score)
                    for d in DIRECTIONS
                )
            }
            for direction in DIRECTIONS:
                view = views[setting.name, budget, direction]
                flags = [r for r in REFS if (score := view.select(r)) is not None and flagged(score)]
                if not flags:
                    continue
                cells = [setting.name, budget, direction, ", ".join(flags)]
                for ref in REFS:
                    score = view.select(ref)
                    cells.extend((f"{score.delta:+d}", signed(score.z)) if score else ("n/a", "n/a"))
                cells.extend(
                    direction_choice(compared[ref], setting, budget) if ref in flagged_refs else "–"
                    for ref in REFS
                )
                print("| " + " | ".join(cells) + " |")

    print("\n### Negative deltas and threshold totals\n")
    print("| Reference | Budget | Negative deltas | Flagged arms | Measured arms |")
    print("|---|---|---:|---:|---:|")
    for ref in REFS:
        rows = reports_b(compared[ref])
        for budget, measured, flags in rows:
            negative, _ = negative_deltas(compared[ref], budget)
            print(f"| {ref} | {budget} | {negative} | {flags} | {measured}/76 |")
        negative, measured = negative_deltas(compared[ref])
        print(f"| {ref} | both | {negative} | {sum(flags for _, _, flags in rows)} | {measured}/152 |")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    for option in ("s-dir", "r-dir", "units-json", "forge-units-json", "job6-raw", "job8-raw",
                   "job8-age", "job9-s", "job9-w", "job10-s2", "settings", "prediction"):
        parser.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    forecasts = read_prediction(args.prediction)
    settings = read_settings(args.settings)
    positions = read_positions(args.games)
    if len(positions) != 1800:
        raise ValueError(f"{args.games}: expected 1,800 ordered replay positions")
    units = {"R": load_units(args.forge_units_json), "S": load_units(args.units_json)}
    references = {
        "R": load_reference(args.r_dir, positions),
        "S": load_stockfish(args.s_dir, positions, fixture_hash=sha256(args.games.read_bytes()).hexdigest()),
    }
    anchors = {}
    for state in ("cold", "warm"):
        for budget in BUDGETS:
            source = args.job8_raw if (state, budget) == ("cold", "hard") else args.job6_raw
            anchors[state, budget], _ = load(
                source / f"base-{state}-{budget}.jsonl", positions, budget, f"base {state} {budget}",
            )
    a = gather_a(args, positions, anchors, references)
    b = gather_b(args, settings, positions, anchors, references)
    print()
    for ref, pairs in units.items():
        print(f"Ruler {ref}: soft {pairs['soft']:+d}, hard {pairs['hard']:+d} agreement counts.")
        for budget, unit in pairs.items():
            if unit == 0:
                print(f"Ruler {ref} {budget} delta is zero. Its doubling effects are undefined.")
            if unit < 0:
                print(f"Ruler {ref} {budget} delta is negative. Its doubling effects reverse the sign of the agreement deltas.")
    print("For each reference, a counts agreements lost, b counts agreements gained and z = (b − a)/sqrt(a + b). "
          "z is zero for no discordant pairs. Threshold flags are descriptive across the tested arms.")
    print()
    print_grades(a, projection(b, "S"), units["S"], forecasts)
    print_a(a, units)
    print_b(b, settings, units)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
