#!/usr/bin/env python3
"""Measure Forge Job 10 deep-reference agreement for Tables A and B."""

import argparse
import csv
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
import subprocess

from agreement_r import Agreement, agreement, load_reference, read_arm, read_positions

BUDGETS = ("soft", "hard")
DIRECTIONS = ("minus", "plus")
SOFT_SEARCH = "go softnodes 2000"
HARD_SEARCH = "go nodes 20000"
A_FORECASTS = (
    ("warm-base", "soft"), ("warm-base", "hard"),
    ("S-5", "soft"), ("S-5", "hard"),
    ("W2", "soft"), ("keep-0", "soft"), ("keep-0", "hard"),
)


@dataclass
class ArmComparison:
    result: Agreement | None = None
    note: str = ""


@dataclass
class Setting:
    name: str
    lower: str
    upper: str
    status: str
    start: str
    actual: str

    def value(self, direction):
        return self.lower if direction == "minus" else self.upper


def read_settings(path):
    settings = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["kind"] == "tuned":
                settings.append(Setting(*(row[key] for key in ("name", "lower", "upper", "status", "start", "actual"))))
    unique = {s.name for s in settings}
    directions = sum(s.value(d) != "-" for s in settings for d in DIRECTIONS)
    if len(settings) != 40 or len(unique) != 40 or directions != 76:
        raise ValueError(f"{path}: expected 40 unique tuning settings and 76 in-range directions")
    if any(s.status not in ("run", "skip") for s in settings):
        raise ValueError(f"{path}: unknown setting status")
    return settings


def read_prediction(path):
    a, b = {}, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[0] == "A" and tuple(fields[1:3]) in A_FORECASTS:
            key = tuple(fields[1:3])
            if key in a:
                raise ValueError(f"{path}: duplicate forecast for {key[0]} {key[1]}")
            a[key] = fields[3], number(fields[3])
        if len(fields) == 3 and fields[0] == "B" and fields[1] in BUDGETS:
            if fields[1] in b:
                raise ValueError(f"{path}: duplicate arm-count forecast for {fields[1]}")
            guess = number(fields[2])
            if guess.denominator != 1 or not 0 <= guess <= 76:
                raise ValueError(f"{path}: expected an arm count from 0 to 76")
            b[fields[1]] = fields[2], guess
    if a.keys() != set(A_FORECASTS) or b.keys() != set(BUDGETS):
        raise ValueError(f"{path}: expected seven A and two B forecasts")
    return a, b


def number(value):
    return Fraction(0) if value == "zero" else Fraction(value)


def ratio_grade(guess, actual):
    if actual is None:
        return "ungraded"
    if guess == 0 or actual == 0:
        return "survives" if guess == actual else "KILLED (zero)"
    if (guess > 0) != (actual > 0):
        return "KILLED (sign)"
    factor = Fraction(3, 2)
    return "survives" if abs(guess) / factor <= abs(actual) <= abs(guess) * factor else "KILLED"


def flagged(result):
    discordant = result.a + result.b
    return discordant > 0 and result.delta * result.delta >= 9 * discordant


def units_for(result, unit):
    return Fraction(result.delta, unit) if unit else None


def search_for(budget):
    return SOFT_SEARCH if budget == "soft" else HARD_SEARCH


def complete_path(path, optional):
    sidecar = path.with_suffix(path.suffix + ".meta")
    if not path.is_file() or not sidecar.is_file():
        note = "unfinished: missing raw data or metadata"
    elif not sidecar.stat().st_size:
        note = "unfinished: metadata not finalized"
    else:
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        if meta["status"] == "complete":
            return ""
        note = f"{meta['status']} after {meta.get('positions_completed', 0)} rows: {meta.get('error', '')}"
    if optional:
        return note
    raise ValueError(f"{path}: {note}")


def load(path, positions, budget, label, optional=False):
    note = complete_path(path, optional)
    if note:
        return None, note
    return read_arm(path, positions, search_for(budget), label=label), ""


def gather_a(args, positions, anchors, reference):
    results = {}
    for budget in BUDGETS:
        warm, cold = anchors["warm", budget], anchors["cold", budget]
        results["warm-base", budget] = ArmComparison(agreement(warm, cold, reference))
        runs = {
            **{f"S-{mask}": args.job9_s / f"mask-{mask}-{budget}.jsonl" for mask in (1, 2, 5, 7)},
            **{arm: args.job9_w / f"{arm}-{budget}.jsonl" for arm in ("W1", "W2")},
            **{f"keep-{keep}": args.job8_age / f"keep-{keep}-warm-{budget}.jsonl"
               for keep in (896, 768, 512, 256, 0)},
        }
        for name, path in runs.items():
            rows, note = load(path, positions, budget, f"A {name} {budget}", optional=True)
            results[name, budget] = ArmComparison(agreement(rows, warm, reference) if rows else None, note)
    return results


def gather_b(args, settings, positions, anchors, reference):
    results = {}
    for setting in settings:
        for budget in BUDGETS:
            for direction in DIRECTIONS:
                value = setting.value(direction)
                key = setting.name, budget, direction
                if value == "-":
                    results[key] = ArmComparison(note="out of range")
                    continue
                if setting.status == "skip":
                    results[key] = ArmComparison(note=f"skipped: expected start {setting.start}, observed {setting.actual}")
                    continue
                raw = args.job6_raw if budget == "soft" else args.job8_raw
                path = raw / f"{setting.name}-{direction}-cold-{budget}.jsonl"
                rows, note = load(path, positions, budget, f"B {setting.name} {direction} {budget}", optional=True)
                results[key] = ArmComparison(agreement(rows, anchors["cold", budget], reference) if rows else None, note)
    return results


def tidy(text):
    return str(text).replace("|", "&#124;").replace("\n", " ")


def signed(value):
    return "n/a" if value is None else f"{float(value):+.4f}"


def reports_b(views):
    measured = {key: view.result for key, view in views.items() if view.result is not None}
    return [
        (budget, sum(key[1] == budget for key in measured),
         sum(key[1] == budget and flagged(value) for key, value in measured.items()))
        for budget in BUDGETS
    ]


def print_grades(views_a, views_b, units, predictions):
    a, b = predictions
    print("## Prediction grades\n")
    print("A sign must agree, and a nonzero magnitude must be within a factor of 1.5. "
          "A zero forecast requires zero. Incomplete totals and undefined ruler effects stay ungraded.\n")
    print("| Table | Arm or statistic | Budget | Guess | Measured | Grade |")
    print("|---|---|---|---:|---:|---|")
    verdicts = []
    for name, budget in A_FORECASTS:
        view = views_a[name, budget]
        observed = units_for(view.result, units[budget]) if view.result is not None else None
        text, guess = a[name, budget]
        verdict = ratio_grade(guess, observed)
        verdicts.append(verdict)
        reason = view.note or ("zero ruler delta" if observed is None else "")
        suffix = f": {reason}" if reason else ""
        print(f"| A | {name} | {budget} | {text} | {signed(observed)} | {tidy(verdict + suffix)} |")
    for budget, measured, flags in reports_b(views_b):
        text, guess = b[budget]
        verdict = ratio_grade(guess, Fraction(flags) if measured == 76 else None)
        verdicts.append(verdict)
        print(f"| B | Arms reaching abs(z) ≥ 3 | {budget} | {text} | {flags}/{measured} measured | {verdict} |")
    print(f"\n{sum(v.startswith('KILLED') for v in verdicts)} KILLED, "
          f"{verdicts.count('survives')} survive, {verdicts.count('ungraded')} ungraded.\n")


def print_a(views, units):
    print("## Table A. Deep cold reference agreement by replay arm\n")
    print("| Arm | Budget | Matched base | Agree with R | a, base only | b, arm only | z | Node doublings |")
    print("|---|---|---|---|---:|---:|---:|---:|")
    for (name, budget), view in views.items():
        baseline = "cold" if name == "warm-base" else "warm"
        score = view.result
        if score is None:
            print(f"| {name} | {budget} | {baseline} {budget} | {tidy(view.note)} | n/a | n/a | n/a | n/a |")
            continue
        percent = Fraction(100 * score.agree, score.total)
        print(f"| {name} | {budget} | {baseline} {budget} | {score.agree}/{score.total} ({float(percent):.4f}%) | "
              f"{score.a} | {score.b} | {signed(score.z)} | {signed(units_for(score, units[budget]))} |")
    print()


def table_b_cell(view, unit):
    if view.result is None:
        return tidy(view.note)
    result = view.result
    star = " †" if flagged(result) else ""
    return f"{result.delta:+d}, {signed(result.z)}, {signed(units_for(result, unit))}{star}"


def direction_choice(views, setting, budget):
    low = views[setting.name, budget, "minus"]
    high = views[setting.name, budget, "plus"]
    if low.result is None or high.result is None:
        if low.result is not None and high.note == "out of range":
            return "minus only (plus out of range)"
        if high.result is not None and low.note == "out of range":
            return "plus only (minus out of range)"
        return "unavailable (one direction incomplete)"
    delta = high.result.agree - low.result.agree
    return "tie" if delta == 0 else f"{'plus' if delta > 0 else 'minus'} (+{abs(delta)} agreements)"


def print_b(views, settings, units):
    print("## Table B. One-step tuning-arm agreement against cold\n")
    print("Each arm cell gives the signed agreement-count delta, z and effect in doublings. "
          "† marks the exact threshold abs(z) ≥ 3 before rounding.\n")
    print("| Setting | Soft minus | Soft plus | Hard minus | Hard plus |")
    print("|---|---|---|---|---|")
    for setting in settings:
        values = [table_b_cell(views[setting.name, budget, d], units[budget])
                  for budget in BUDGETS for d in DIRECTIONS]
        print(f"| {setting.name} | " + " | ".join(values) + " |")
    print("\n### Arms reaching abs(z) ≥ 3\n")
    print("| Setting | Budget | Direction | Agreement delta | a | b | z | Doublings | Higher-agreement direction |")
    print("|---|---|---|---:|---:|---:|---:|---:|---|")
    for setting in settings:
        for budget in BUDGETS:
            for direction in DIRECTIONS:
                result = views[setting.name, budget, direction].result
                if result is not None and flagged(result):
                    print(f"| {setting.name} | {budget} | {direction} | {result.delta:+d} | {result.a} | {result.b} | "
                          f"{signed(result.z)} | {signed(units_for(result, units[budget]))} | "
                          f"{direction_choice(views, setting, budget)} |")
    for budget, measured, flags in reports_b(views):
        print(f"\n{budget}: {flags} of {measured} measured arms reach the threshold. {76 - measured} of 76 unavailable.")
    print()


def ruler_units(args, parser):
    if args.units_json is not None:
        if args.u_soft is not None or args.u_hard is not None:
            parser.error("provide either --units-json or the two individual ruler units")
        values = json.loads(args.units_json.read_text(encoding="utf-8"))
        units = {budget: values[f"U_{budget}"] for budget in BUDGETS}
    else:
        if args.u_soft is None or args.u_hard is None:
            parser.error("provide --units-json or both --u-soft and --u-hard")
        units = dict(zip(BUDGETS, (args.u_soft, args.u_hard)))
    if any(type(value) is not int for value in units.values()):
        raise ValueError("ruler units must be signed integer count deltas")
    return units


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("games", type=Path)
    reference = parser.add_mutually_exclusive_group(required=True)
    reference.add_argument("--reference-dir", type=Path)
    reference.add_argument("--reference", type=Path, nargs="+")
    parser.add_argument("--units-json", type=Path)
    parser.add_argument("--u-soft", type=int)
    parser.add_argument("--u-hard", type=int)
    parser.add_argument("--job6-raw", type=Path, required=True)
    parser.add_argument("--job8-raw", type=Path, required=True)
    parser.add_argument("--job8-age", type=Path, required=True)
    parser.add_argument("--job9-s", type=Path, required=True)
    parser.add_argument("--job9-w", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--prediction", type=Path, required=True)
    parser.add_argument("--stamp-dir", type=Path, help="write UTC completion stamps for the A and B readbacks")
    args = parser.parse_args()
    units = ruler_units(args, parser)
    forecasts = read_prediction(args.prediction)
    settings = read_settings(args.settings)
    positions = read_positions(args.games)
    if len(positions) != 1800:
        raise ValueError(f"{args.games}: expected 1,800 ordered positions")
    ref_rows = (load_reference(args.reference_dir, positions) if args.reference_dir
                else read_arm(args.reference, positions, "go nodes 400000", label="R"))
    anchors = {}
    for state in ("cold", "warm"):
        for budget in BUDGETS:
            raw = args.job8_raw if (state, budget) == ("cold", "hard") else args.job6_raw
            anchors[state, budget], _ = load(
                raw / f"base-{state}-{budget}.jsonl", positions, budget, f"base {state} {budget}",
            )
    a = gather_a(args, positions, anchors, ref_rows)
    if args.stamp_dir:
        with (args.stamp_dir / "A-readback.stamp").open("w") as stamp:
            subprocess.run(["date", "-u", "+%FT%TZ"], stdout=stamp, check=True)
    b = gather_b(args, settings, positions, anchors, ref_rows)
    if args.stamp_dir:
        with (args.stamp_dir / "B-readback.stamp").open("w") as stamp:
            subprocess.run(["date", "-u", "+%FT%TZ"], stdout=stamp, check=True)
    print(f"\nRuler units are signed agreement-count deltas: soft {units['soft']:+d}, hard {units['hard']:+d}.")
    print("Positive z means more new agreements than lost agreements. Negative z means fewer. "
          "With no discordant pairs z is zero. Flags are descriptive across the tested arms.")
    for budget, unit in units.items():
        if unit == 0:
            print(f"{budget.capitalize()} has a zero ruler delta, so its effects in doublings are undefined.")
        if unit < 0:
            print(f"{budget.capitalize()} has a negative ruler delta, which reverses the effect's sign in doublings.")
    print()
    print_grades(a, b, units, forecasts)
    print_a(a, units)
    print_b(b, settings, units)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
