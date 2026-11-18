#!/usr/bin/env python3
"""Audit Job 22 PGNs, FailHighBlend masks, and exhaustive opening overlap."""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job21 in (HERE.parent / "job21", HERE.parent / "sol-job21"):
    if (job21 / "analyze_matches21.py").is_file():
        sys.path.insert(0, str(job21))
        break
else:
    raise SystemExit("Job 21's analyze_matches21.py is missing from adjacent job21 or sol-job21.")

from analyze_matches21 import (
    BOOK_SHA, CANDIDATES as PRIOR21, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, check_match_preflight, digest, exploratory_read, grade_elo,
    identical_moves, interval, match_status, number, opening_fens, parse_games,
    penta_estimate, pgn_module, pool_results, read_job20_match, read_match as read_job21_match,
    read_pca_sha, replicated, replicated_loss, summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/FHB, B Mult/FHB, candidate variant
    "K11": (100, 7221, 2000, 2000, 4, ("0", "6"), ("0", "6"), None),
    "C11": (200, 7222, 10000, 20000, 4, ("0", "0"), ("0", "0"), None),
    "F1kr": (2000, 7223, 2000, 2000, 2, ("0", "1"), ("0", "0"), ("FailHighBlend", "1")),
    "F3kr": (2000, 7224, 2000, 2000, 2, ("0", "3"), ("0", "0"), ("FailHighBlend", "3")),
    "F2k": (2000, 7225, 2000, 2000, 2, ("0", "2"), ("0", "0"), ("FailHighBlend", "2")),
    "F4k": (2000, 7226, 2000, 2000, 2, ("0", "4"), ("0", "0"), ("FailHighBlend", "4")),
    "F5k": (2000, 7227, 2000, 2000, 2, ("0", "5"), ("0", "0"), ("FailHighBlend", "5")),
    "F6k": (2000, 7228, 2000, 2000, 2, ("0", "6"), ("0", "0"), ("FailHighBlend", "6")),
    "E64wr": (2000, 7229, 20000, 20000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
}
CONTROLS = ("K11", "C11")
SLOTS = (("F1kr", "F3kr", "F2k", "F4k", "F5k", "F6k"), ("E64wr",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**PRIOR_JOBS, 21: PRIOR21}
REPLICATIONS = {"F1k": "F1kr", "F3k": "F3kr", "E64w": "E64wr"}
EXPLORATORY = ("F2k", "F4k", "F5k", "F6k")


def read_meta(directory, name, pca_sha):
    path = directory / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        return None, "metadata missing or unfinished"
    data = json.loads(path.read_text(encoding="utf-8"))
    games, seed, nodes_a, nodes_b, workers, a_extras, b_extras, change = MATCHES[name]
    override = dict(zip(("name", "value"), change, strict=True)) if change is not None else None
    expected = (name, games, seed, nodes_a, nodes_b, workers, "A", "B", override, 300)
    keys = ("match", "games_requested", "seed", "nodes_a", "nodes_b", "concurrency",
            "engine_a", "engine_b", "variant", "maxmoves")
    if tuple(data.get(key) for key in keys) != expected:
        raise ValueError(f"{path}: wrong match identity, budget or number of workers")
    expected_exe = ENGINE_SHA if name.startswith("E64") else pca_sha
    if (data["exe_sha256"], data["book_sha256"], data["fastchess_revision"]) != (
        expected_exe, BOOK_SHA, FASTCHESS_REVISION,
    ):
        raise ValueError(f"{path}: wrong executable, book or fastchess provenance")
    if data["status"] == "refused":
        return None, f"refused: {data.get('error', '')}"
    if not data.get("pgn_sha256") or not data.get("out_sha256"):
        return None, f"{data['status']}: {data.get('error', 'PGN or fastchess output missing')}"
    if data["status"] == "complete" and data.get("fastchess_exit") != 0:
        raise ValueError(f"{path}: complete match has nonzero fastchess exit")
    for suffix in ("pgn", "out"):
        file = directory / f"{name}.{suffix}"
        if digest(file) != data[f"{suffix}_sha256"]:
            raise ValueError(f"{file}: SHA-256 differs from sidecar")
    try:
        check_match_preflight(data, a_extras, b_extras)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error
    return data, ""


def read_match(raw, name, pgn, pca_sha):
    meta, reason = read_meta(raw, name, pca_sha)
    if meta is None:
        return Match(name, "unavailable", note=reason), None, None
    requested = MATCHES[name][0]
    groups = parse_games(raw / f"{name}.pgn", pgn, exact_moves=True)
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K11")
    games = 2 * sum(penta)
    if raw_games > requested or max(groups, default=0) > requested // 2:
        raise ValueError(f"{name}: PGN exceeds its scheduled game count or round IDs")
    if meta["status"] == "complete" and (raw_games, games) != (requested, requested):
        raise ValueError(f"{name}: reported complete without {requested} complete paired games")
    row = Match(
        name, meta["status"], raw_games, games, w, l, d, penta, abnormal=abnormal,
        match_start=meta.get("match_start_utc"), match_end=meta.get("match_end_utc"),
        provenance=(meta["exe_sha256"], meta["fastchess_sha256"], meta["book_sha256"], tuple(meta["settings_b"])),
    )
    print(f"{name}: {raw_games} PGN games, {games} paired, {raw_games - games} unpaired, "
          f"A W-L-D {w}-{l}-{d}, penta {penta}, abnormal terminations {abnormal}.")
    printed = [
        report for report in summarized_output(raw / f"{name}.out")
        if (report["games"], report["wins"], report["losses"], report["draws"], report["penta"])
        == (games, w, l, d, penta)
    ]
    actual = penta_estimate(penta, deterministic=bool(printed))
    if printed:
        latest = printed[-1]
        reported = latest["elo"], latest["margin"]
        if actual is None or any(abs(float(a - b)) > 0.0050001 for a, b in zip(reported, actual, strict=True)):
            raise ValueError(f"{name}: printed Elo or 95% halfwidth disagrees with paired PGN reconstruction")
        row.elo, row.width = reported
        print(f"{name}: printed Elo {number(row.elo)} 95% {interval(row.interval)} verified.")
    elif name in CONTROLS:
        raise ValueError(f"{name}: no printed pentanomial interval matches the PGN and pair counts")
    elif actual is None:
        row.note = "no usable paired interval"
    else:
        row.elo, row.width = actual
        row.note = "interval reconstructed from paired PGN counts; no matching printed interval"
    fens = {pair[0].start for pair in groups.values() if len(pair) == 2}
    return row, identical_moves(groups), fens


def gates(raw, pgn, pca_sha, only_k=False):
    k_result = read_match(raw, "K11", pgn, pca_sha)
    k, same, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K11 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K11 PASS: A and B both accepted explicit EvalSwingMult 0 and FailHighBlend 6 on PCA, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K11": k_result}
    c_result = read_match(raw, "C11", pgn, pca_sha)
    c, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C11 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C11 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K11": k_result, "C11": c_result}


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in CANDIDATES:
            continue
        name = fields[0]
        if len(fields) != 2 or name in forecasts:
            raise ValueError(f"{path}: expected one signed Elo for {name}")
        forecasts[name] = Fraction(0) if fields[1] == "zero" else Fraction(fields[1])
    if forecasts.keys() != set(CANDIDATES):
        raise ValueError(f"{path}: expected seven signed Elo forecasts")
    return forecasts


def print_grades(results, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo must have the forecast sign and fall within a factor of 1.5 of "
          "its magnitude. A zero forecast requires zero.\n")
    print("| Forecast | Guess | Observed | Grade | Evidence status |")
    print("|---|---:|---:|---|---|")
    grades = []
    for name in CANDIDATES:
        row = results[name][0]
        grade = grade_elo(forecasts[name], row.elo)
        grades.append(grade)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(row.elo)} | {grade} | {match_status(row)} |")
    print(f"\n{sum(v.startswith('KILLED') for v in grades)} KILLED, "
          f"{grades.count('survives')} survive, {grades.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table P. FailHighBlend and EvalSwing paired games\n")
    print("All rows use PC20, embedded evaluation, Threads 1, Hash 16 and the pinned opening book. W-L-D is from A's "
          "perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. Identical pairs "
          "share the complete ordered UCI move sequence.\n")
    print("| Match | Build, nodes per move, options A/B | Status | Games | W-L-D | Pentanomial | "
          "Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---|---|---:|---|---|---|---:|---|")
    for row, same in rows:
        games = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        if row.name.startswith("F"):
            build = f"PCA, 2,000, FailHighBlend {row.name[1]}/0 and EvalSwingMult 0/0"
            reading = exploratory_read(row) if row.name in EXPLORATORY else "two-seed loss comparison"
        else:
            build = "Job 4, 20,000, EvalSwingMult 64/0"
            reading = "two-seed gain comparison"
        print(f"| {row.name} | {build} | {match_status(row)} | {games} | {wld} | {penta} | "
              f"{number(row.elo)} {interval(row.interval)} | {sequence} | {reading} |")


def verify_slots(results):
    times = {name: (results[name][0].match_start, results[name][0].match_end) for name in CANDIDATES}
    for slot in SLOTS:
        for previous, current in zip(slot, slot[1:]):
            end, start = times[previous][1], times[current][0]
            if end and start and end > start:
                raise ValueError(f"{current} began before {previous} ended in the same slot")
    a_start, a_end = times[SLOTS[0][0]]
    b_start, b_end = times[SLOTS[1][0]]
    if all((a_start, a_end, b_start, b_end)) and max(a_start, b_start) >= min(a_end, b_end):
        raise ValueError("the first match in each slot did not overlap")


def historical_openings(raw, name, pgn):
    path = raw / f"{name}.pgn"
    meta = json.loads((raw / f"{name}.meta").read_text(encoding="utf-8"))
    if meta["match"] != name or meta["status"] not in ("complete", "interrupted") or digest(path) != meta["pgn_sha256"]:
        raise ValueError(f"{path}: historical opening file or metadata identity cannot be verified")
    pairs, tags = opening_fens(path, pgn)
    if meta["status"] == "complete" and pairs * 2 != meta["games_requested"]:
        raise ValueError(f"{path}: historical complete match has wrong pair count")
    return meta["status"], (pairs, tags)


WITHIN_HEADING = "### Within Job 22"
HISTORICAL_HEADING = "### Job 22 against Jobs 17–21"


def print_openings(results, prior_dirs, pgn, old_results):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings. The two tables account for every scheduled new-file pair and every new-file by prior-file pair.\n")
    known = {
        name: (row.status, (row.games // 2, fens) if fens is not None else None)
        for name, (row, _, fens) in {**results, **old_results}.items()
    }
    historic = {}
    for job, names in PRIOR.items():
        for name in names:
            label = f"Job {job} {name}"
            historic[label] = (known[label] if label in known
                               else historical_openings(prior_dirs[job], name, pgn))
    all_files = {**{name: known[name] for name in results}, **historic}

    def label(name):
        status, _ = all_files[name]
        return name if status == "complete" else f"{name} (incomplete)"

    def share(left, right):
        a, b = all_files[left][1], all_files[right][1]
        return len(a[1] & b[1]) if a is not None and b is not None else "n/a"

    for old, fresh in REPLICATIONS.items():
        archived = f"Job 21 {old}"
        print(f"{label(archived)} and {label(fresh)} distinct shared exact FENs = {share(archived, fresh)}.")
    print()
    print("| File | Status | Complete pairs | Distinct exact FENs |")
    print("|---|---|---:|---:|")
    for name, (status, entry) in all_files.items():
        readable = "complete" if status == "complete" else f"incomplete ({status})"
        pairs, distinct = (entry[0], len(entry[1])) if entry is not None else ("n/a", "n/a")
        print(f"| {name} | {readable} | {pairs} | {distinct} |")

    for heading, pairs in ((WITHIN_HEADING, combinations(results, 2)),
                           (HISTORICAL_HEADING, product(results, historic))):
        print(f"\n{heading}\n")
        print("| File A | File B | Shared exact FENs |")
        print("|---|---|---:|")
        for left, right in pairs:
            print(f"| {label(left)} | {label(right)} | {share(left, right)} |")


def section_lines(lines, heading):
    if lines.count(heading) != 1:
        raise ValueError(f"expected exactly one {heading} heading")
    start = lines.index(heading) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("#")), len(lines))
    return lines[start:end]


def markdown_rows(lines, header):
    for line in lines:
        if not line.startswith("| "):
            continue
        if not line.endswith("|"):
            raise ValueError(f"table row lacks a closing pipe: {line}")
        record = tuple(field.strip() for field in line[1:-1].split("|"))
        if len(record) != len(header):
            raise ValueError(f"table row has wrong number of cells: {line}")
        if record != header:
            yield record


def audit_openings(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    historical = tuple(f"Job {job} {name}" for job, names in PRIOR.items() for name in names)
    names = (*MATCHES, *historical)
    inventory_rows = list(markdown_rows(
        section_lines(lines, "## Shared openings"), ("File", "Status", "Complete pairs", "Distinct exact FENs"),
    ))
    if Counter(record[0] for record in inventory_rows) != Counter(names):
        raise ValueError(f"{path}: opening inventory must contain each expected file exactly once")
    inventory = {name: (status, pairs) for name, status, pairs, _ in inventory_rows}
    for cut in ("Job 19 E64t", "Job 20 E64tr"):
        if not inventory[cut][0].startswith("incomplete"):
            raise ValueError(f"{path}: opening inventory lost the cut status for {cut}")
    if len(MATCHES) != 9 or len(historical) != 26 or "Job 20 F7k" not in historical:
        raise ValueError("opening scopes lost a scheduled file or historical cohort")

    def label(name):
        return f"{name} (incomplete)" if inventory[name][0].startswith("incomplete") else name

    for heading, pairs in ((WITHIN_HEADING, combinations(MATCHES, 2)),
                           (HISTORICAL_HEADING, product(MATCHES, historical))):
        expected = {
            (label(left), label(right)): "n/a" in (inventory[left][1], inventory[right][1])
            for left, right in pairs
        }
        rows = list(markdown_rows(section_lines(lines, heading), ("File A", "File B", "Shared exact FENs")))
        observed = Counter((left, right) for left, right, _ in rows)
        if observed != Counter(expected.keys()):
            raise ValueError(f"{path}: {heading} has missing, duplicate or mislabeled pair rows")
        for left, right, count in rows:
            valid = count == "n/a" if expected[left, right] else count.isdecimal()
            if not valid:
                raise ValueError(f"{path}: invalid shared FEN count for {left} and {right}")
        print(f"{heading.removeprefix('### ')} verified: {len(rows)} comparisons, one per required file pair.")


def print_fhb_summary(results, old_results, pools, decisions):
    print("\n## FailHighBlend settings at 2,000 nodes\n")
    print("PCA, PC20, embedded evaluation, Threads 1, Hash 16, EvalSwingMult 0 on both sides. "
          "Each nonzero mask was measured against FailHighBlend 0.\n")
    print("| Value | Enabled parts | Games | Elo [95%] | Replicated | Evidence |")
    print("|---:|---|---:|---|---|---|")
    parts = {
        1: "Reverse-futility return blend",
        2: "Quiescence fail-high blends",
        4: "Non-PV main-search fail-high blend",
    }
    for value in range(1, 8):
        name = f"F{value}k"
        if name in pools:
            row = pools[name][0]
            decision = decisions[name]
            verdict = "yes (loss)" if decision is True else "no" if decision is False else "unavailable"
            evidence = match_status(row)
        elif name in ("F1k", "F3k"):
            row = old_results[f"Job 21 {name}"][0]
            fresh = results[REPLICATIONS[name]][0]
            verdict = "withheld"
            evidence = f"{name} only. {fresh.name} {match_status(fresh)}"
        else:
            row = results[name][0]
            if not row.games:
                continue
            verdict = "one seed"
            evidence = match_status(row)
        enabled = ", ".join(part for bit, part in parts.items() if value & bit)
        games = row.games if row.penta else "n/a"
        print(f"| {value} | {enabled} | {games} | {number(row.elo)} {interval(row.interval)} | {verdict} | {evidence} |")


def table(raw, prior_dirs, pgn, forecasts, pca_sha):
    results = gates(raw, pgn, pca_sha)
    old_results = {
        f"Job 21 {name}": read_job21_match(prior_dirs[21], name, pgn, pca_sha)
        for name in (*REPLICATIONS, "F7kr")
    }
    old_results["Job 20 F7k"] = read_job20_match(prior_dirs[20], "F7k", pgn, pca_sha)
    if any(row.status != "complete" for row, _, _ in old_results.values()):
        raise ValueError("a required complete Job 20 or 21 pool seed is unavailable")
    results.update((name, read_match(raw, name, pgn, pca_sha)) for name in CANDIDATES)
    verify_slots(results)
    rows = [results[name][:2] for name in CANDIDATES]
    rows.extend(old_results[f"Job 21 {name}"][:2] for name in REPLICATIONS)
    pools, decisions = {}, {}
    for name, fresh in REPLICATIONS.items():
        if results[fresh][0].status != "complete":
            continue
        pooled = pool_results([old_results[f"Job 21 {name}"], results[fresh]])
        rows.append(pooled)
        pools[name] = pooled
        check = replicated if name == "E64w" else replicated_loss
        decisions[name] = check(results[fresh][0], pooled[0])
    f7 = pool_results([old_results["Job 20 F7k"], old_results["Job 21 F7kr"]])
    pools["F7k"] = f7
    decisions["F7k"] = replicated_loss(old_results["Job 21 F7kr"][0], f7[0])

    print_grades(results, forecasts)
    print_table(rows)
    print_openings(results, prior_dirs, pgn, old_results)
    print("\n## Declared verdicts\n")
    print("F1kr, only if complete, gives F1k its verdict: REPLICATED (a loss) when F1kr alone gives Elo below 0 "
          "AND the pool of F1k and F1kr (pentanomial counts added) has a 95 % interval whose upper end is below 0. "
          "The same for F3kr and F3k.")
    print("E64wr, only if complete, gives E64w its verdict: REPLICATED (a gain) when E64wr alone gives Elo above 0 "
          "AND the pool of E64w and E64wr has a 95 % interval whose lower end is above 0.")
    print("F2k, F4k, F5k and F6k are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above "
          "or wholly below 0 earns a fresh seed in a later job before anything is said about it.")
    print("A cut match gives no verdict.\n")
    for name, fresh in REPLICATIONS.items():
        fresh_row = results[fresh][0]
        if name not in pools:
            print(f"{name} verdict withheld. {fresh} {match_status(fresh_row)}.")
            continue
        row = pools[name][0]
        side, index = ("lower", 0) if name == "E64w" else ("upper", 1)
        bound = row.interval[index] if row.interval is not None else None
        print(f"{name} REPLICATED {yes_no(decisions[name])}. Fresh Elo {number(fresh_row.elo, digits=4)}, "
              f"pooled {side} 95% bound {number(bound, digits=4)}. Evidence {match_status(row)}.")
    print_fhb_summary(results, old_results, pools, decisions)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("gates", "table"):
        option = modes.add_parser(mode)
        option.add_argument("raw", type=Path)
        option.add_argument("--pca-sha256", type=Path, required=True)
        option.add_argument("--python-chess-dir", type=Path)
        if mode == "gates":
            option.add_argument("--only-k", action="store_true")
        else:
            for job in PRIOR:
                option.add_argument(f"--job{job}-raw", type=Path, required=True)
            option.add_argument("--prediction", type=Path, required=True)
    audit = modes.add_parser("audit-openings")
    audit.add_argument("report", type=Path)
    args = parser.parse_args()
    if args.mode == "audit-openings":
        audit_openings(args.report)
        return
    pgn = pgn_module(args.python_chess_dir)
    pca_sha = read_pca_sha(args.pca_sha256)
    if args.mode == "gates":
        gates(args.raw, pgn, pca_sha, args.only_k)
    else:
        prior_dirs = {job: getattr(args, f"job{job}_raw") for job in PRIOR}
        table(args.raw, prior_dirs, pgn, read_prediction(args.prediction), pca_sha)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
