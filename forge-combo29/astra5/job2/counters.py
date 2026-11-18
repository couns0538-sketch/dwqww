"""Recount and compare completed PCADC depth-12 searches from astra5 job 2."""

import argparse
import csv
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import re
import sys


SUITES = {"G": 353, "O": 200}
SETTINGS = ("base", "fhb7", "del", "del_fhb7", "sd20_base", "sd20_fhb7", "dm12", "dm0", "sm1")
PAIRS = (("base", "fhb7"), ("del", "del_fhb7"), ("sd20_base", "sd20_fhb7"))
LABELS = ("tests", "ext+1", "ext+2", "multicut", "ext-2", "ext-1", "none",
          "TT lower", "TT upper", "TT exact", "RFP")
# Known PC20 sums from kimi5 job 25, as specified in job 2.
KNOWN = {
    ("G", "base"): {0: 176423, 2: 67359, 3: 31604, 7: 1202904, 10: 4748667},
    ("G", "fhb7"): {0: 164148, 2: 39128, 3: 29016, 7: 1041548, 10: 4134563},
    ("O", "base"): {0: 48220, 2: 5794},
    ("O", "fhb7"): {0: 47952, 2: 2124},
}


@dataclass
class Run:
    positions: list
    nodes: int
    counts: list

    def rate(self, slot):
        return Fraction(1000 * self.counts[slot], self.nodes)


def read_run(path):
    suite, setting = path.stem.split("_", 1)
    if suite not in SUITES or setting not in SETTINGS:
        raise ValueError(f"unexpected row filename {path.name}")
    size = SUITES[suite]
    if f"completed_rows {size}" not in Path(str(path) + ".meta").read_text().splitlines():
        raise ValueError(f"{path.name}: missing completion marker for {size} rows")
    positions = []
    counts = [0] * 16
    nodes = 0
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if reader.fieldnames != ["index", "fen", "nodes", "bestmove", "a25c"]:
            raise ValueError(f"{path.name}: unexpected header {reader.fieldnames}")
        for i, row in enumerate(reader, 1):
            context = f"{path.name} position {i}"
            if row["index"] != str(i) or not row["fen"] or not row["bestmove"]:
                raise ValueError(f"{context}: malformed position record")
            tokens = row["a25c"].split()
            if len(tokens) != 17 or tokens[0] != "A25C" or not all(x.isdecimal() for x in tokens[1:]):
                raise ValueError(f"{context}: invalid A25C line {row['a25c']!r}")
            c = [int(x) for x in tokens[1:]]
            if c[0] != sum(c[1:7]) or c[15] != sum(c[11:15]):
                raise ValueError(f"{context}: counter closure failed: {row['a25c']}")
            if (setting in ("del", "del_fhb7") and c[2]) or (setting.startswith("sd20_") and c[0]):
                raise ValueError(f"{context}: disabled-event control failed: {row['a25c']}")
            positions.append(row["fen"])
            nodes += int(row["nodes"])
            counts = [a + b for a, b in zip(counts, c)]
    if len(positions) != size or nodes <= 0:
        raise ValueError(f"{path.name}: read {len(positions)} rows, {nodes} nodes")
    for slot, expected in KNOWN.get((suite, setting), {}).items():
        if counts[slot] != expected:
            raise ValueError(f"{path.name}: read {size} A25C lines, slot [{slot}]={counts[slot]}, expected {expected}")
    return Run(positions, nodes, counts)


def fmt(value):
    return f"{float(value):.6f}"


def rate_ratio(a, b, slot):
    return b.rate(slot) / a.rate(slot) if a.counts[slot] else None


def ratio_text(a, b, slot):
    ratio = rate_ratio(a, b, slot)
    if ratio is None:
        return "undefined (0/0)" if not b.counts[slot] else "undefined (+/0)"
    return fmt(ratio)


def md_row(values):
    cells = (str(value).replace("|", r"\|") for value in values)
    print("| " + " | ".join(cells) + " |")


def md_header(values):
    md_row(values)
    md_row(["---"] * len(values))


def summarize(runs):
    print("#### Raw A25C totals — PCADC, PC20 first, depth 12\n")
    md_header(["Suite", "Setting", "A25C lines", "Nodes"] + [f"[{i}]" for i in range(16)])
    for (suite, setting), run in runs.items():
        md_row([suite, setting, len(run.positions), run.nodes, *run.counts])
    print("\n#### Events per 1,000 nodes\n")
    md_header(["Suite", "Setting", "A25C lines", "Nodes"] + list(LABELS))
    for (suite, setting), run in runs.items():
        md_row([suite, setting, len(run.positions), run.nodes, *(fmt(run.rate(i)) for i in range(11))])
    print("\n#### Matched-setting ratios\n")
    md_header(["Suite", "Treatment/base", "Node ratio"] + list(LABELS))
    for suite in SUITES:
        for base, treatment in PAIRS:
            a, b = runs[suite, base], runs[suite, treatment]
            md_row([suite, f"{treatment}/{base}", fmt(Fraction(b.nodes, a.nodes)),
                    *(ratio_text(a, b, i) for i in range(11))])


def rank_changes(label, suite, base, treatment, slots):
    a, b = base, treatment
    relative = {i: abs(rate_ratio(a, b, i) - 1) for i in slots if a.counts[i]}
    absolute = {i: abs(b.rate(i) - a.rate(i)) for i in slots}
    for metric, changes in (("max |rate ratio - 1|", relative), ("max |rate difference|", absolute)):
        for slot, change in changes.items():
            if change == max(changes.values()):
                delta = b.rate(slot) - a.rate(slot)
                md_row([label, suite, metric, f"[{slot}] {LABELS[slot]}", fmt(a.rate(slot)),
                        fmt(b.rate(slot)), ratio_text(a, b, slot), fmt(delta)])


def questions(runs):
    print("\n#### Q1 and Q2 changes in event rates\n")
    md_header(["Question", "Suite", "Criterion", "Slot", "Base/1k", "Fhb7/1k", "Rate ratio", "Difference/1k"])
    rank_changes("Q1, del", "G", runs["G", "del"], runs["G", "del_fhb7"], range(11))
    for suite in SUITES:
        rank_changes("Q2, SD20", suite, runs[suite, "sd20_base"], runs[suite, "sd20_fhb7"], range(7, 11))
    print("\n#### Q3 distance from the PC20 base two-ply extension rate\n")
    md_header(["Suite", "Fhb7 setting", "Base ext+2/1k", "Setting ext+2/1k", "Abs distance/1k",
               "Ext+2 rate ratio", "Tree nodes/base", "Closest"])
    for suite in SUITES:
        a = runs[suite, "base"]
        settings = ("dm12", "dm0", "sm1")
        distances = {s: abs(runs[suite, s].rate(2) - a.rate(2)) for s in settings}
        for setting in settings:
            b = runs[suite, setting]
            md_row([suite, setting, fmt(a.rate(2)), fmt(b.rate(2)), fmt(distances[setting]),
                    ratio_text(a, b, 2), fmt(Fraction(b.nodes, a.nodes)),
                    "yes" if distances[setting] == min(distances.values()) else ""])


def grade(runs, prediction):
    """Read the eight machine-recognizable forecast rows in the frozen prediction text."""
    checks = []
    for line in prediction.read_text().splitlines():
        match = re.fullmatch(
            r"(Q[12])\s+(del|SD20)\s+([GO])\s+(proportional|absolute),\s*slots (\d+)\.\.(\d+)\s+"
            r"\[(\d+)\] .+?\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
        if match:
            question, name, suite, metric, start, end, assumed, point, low, high = match.groups()
            a, b = ((runs[suite, "del"], runs[suite, "del_fhb7"]) if name == "del"
                    else (runs[suite, "sd20_base"], runs[suite, "sd20_fhb7"]))
            slots = range(int(start), int(end) + 1)
            if metric == "proportional":
                gaps = {i: abs(rate_ratio(a, b, i) - 1) for i in slots if a.counts[i]}
            else:
                gaps = {i: abs(b.rate(i) - a.rate(i)) for i in slots}
            winners = [str(i) for i, gap in gaps.items() if gap == max(gaps.values())]
            ratio = rate_ratio(a, b, int(assumed))
            win_ratios = [rate_ratio(a, b, int(i)) for i in winners]
            label = f"{question} {suite} {metric}"
        else:
            q3 = re.fullmatch(r"([GO])\s+(sm1|dm0|dm12)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
            if not q3:
                continue
            suite, assumed, point, low, high = q3.groups()
            a = runs[suite, "base"]
            distances = {s: abs(runs[suite, s].rate(2) - a.rate(2)) for s in ("dm12", "dm0", "sm1")}
            winners = [s for s, dist in distances.items() if dist == min(distances.values())]
            ratio = rate_ratio(a, runs[suite, assumed], 2)
            win_ratios = [rate_ratio(a, runs[suite, s], 2) for s in winners]
            label = f"Q3 {suite} nearest"
        named = assumed in winners
        inside = ratio is not None and Fraction(low) <= ratio <= Fraction(high)
        checks.append((label, assumed, point, low, high, winners, ratio, win_ratios, named, inside))
    if len(checks) != 8:
        raise ValueError(f"parsed {len(checks)} forecasts, expected eight")
    print("#### Job 2 frozen predictions graded on completed Step 4 rows\n")
    md_header(["Forecast", "Predicted class", "Point", "Inclusive bounds", "Actual winner",
               "Predicted class rate ratio", "Winner rate ratio", "Class", "Interval for predicted class", "Joint"])
    for label, assumed, point, low, high, winners, ratio, win_ratios, named, inside in checks:
        md_row([label, assumed, point, f"{low} to {high}", ", ".join(winners), fmt(ratio),
                ", ".join(map(fmt, win_ratios)), "yes" if named else "no", "yes" if inside else "no",
                "pass" if named and inside else "miss"])
    named_total = sum(row[-2] for row in checks)
    interval_total = sum(row[-1] for row in checks)
    joint_total = sum(row[-1] and row[-2] for row in checks)
    print(f"\nClass {named_total}/8, interval for predicted class {interval_total}/8, joint {joint_total}/8.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("run", help="check controls and recount one full counter file")
    single.add_argument("path", type=Path)
    table = sub.add_parser("table", help="recount all complete Step 4 tables")
    table.add_argument("directory", type=Path)
    score = sub.add_parser("grade", help="grade the eight frozen job 2 forecasts")
    score.add_argument("directory", type=Path)
    score.add_argument("prediction", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        run = read_run(args.path)
        print(f"{args.path.name}: read {len(run.positions)} A25C lines; nodes={run.nodes}; "
              f"slots[0..15]={run.counts}")
        return
    runs = {}
    for suite in SUITES:
        for setting in SETTINGS:
            run = read_run(args.directory / f"{suite}_{setting}.tsv")
            if setting != "base" and run.positions != runs[suite, "base"].positions:
                raise ValueError(f"{suite}_{setting}: FEN order differs from base")
            runs[suite, setting] = run
    if args.command == "grade":
        grade(runs, args.prediction)
    else:
        summarize(runs)
        questions(runs)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        sys.exit(str(exc))
