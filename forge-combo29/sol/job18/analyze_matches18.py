#!/usr/bin/env python3
"""Audit Job 18 paired PGNs, control gates, and exact opening overlap."""

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job17 in (HERE.parent / "job17", HERE.parent / "sol-job17"):
    if (job17 / "analyze_matches17.py").is_file():
        sys.path.insert(0, str(job17))
        break
else:
    raise SystemExit("Job 17's analyze_matches17.py is missing from adjacent job17 or sol-job17.")

from analyze_matches17 import (
    BOOK_SHA, CANDIDATES as PRIOR17, ENGINE_SHA, FASTCHESS_REVISION, Match, PRIOR13,
    PRIOR14, PRIOR15, PRIOR16, check_preflight, digest, exploratory_read, grade_elo,
    identical_moves, interval, match_status, number, opening_fens, parse_games,
    penta_estimate, pgn_module, pool_seeds, read_match as read_job17_match, replicated,
    summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/Max, B Mult/Max, candidate variant
    "K7": (100, 7181, 2000, 2000, 4, ("48", None), ("48", None), None),
    "C7": (200, 7182, 10000, 20000, 4, (None, None), (None, None), None),
    "E48kr": (2000, 7183, 2000, 2000, 2, ("48", None), ("0", None), ("EvalSwingMult", "48")),
    "D48v24": (2000, 7184, 2000, 2000, 2, ("48", None), ("24", None), ("EvalSwingMult", "48")),
    "E64k": (2000, 7185, 2000, 2000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
    "X400k48": (2000, 7186, 2000, 2000, 2, ("48", "400"), ("48", "200"), ("EvalSwingMax", "400")),
    "X100k48": (2000, 7187, 2000, 2000, 2, ("48", "100"), ("48", "200"), ("EvalSwingMax", "100")),
    "E48t": (2000, 7188, 10000, 10000, 2, ("48", None), ("0", None), ("EvalSwingMult", "48")),
    "E24t": (2000, 7189, 10000, 10000, 2, ("24", None), ("0", None), ("EvalSwingMult", "24")),
}
CONTROLS = ("K7", "C7")
SLOTS = (("E48kr", "D48v24", "E64k", "X400k48", "X100k48"), ("E48t", "E24t"))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {13: PRIOR13, 14: PRIOR14, 15: PRIOR15, 16: PRIOR16, 17: PRIOR17}
REPLICATION = "E48k"


def read_meta(directory, name):
    path = directory / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        return None, "metadata missing or unfinished"
    data = json.loads(path.read_text(encoding="utf-8"))
    games, seed, nodes_a, nodes_b, workers, a_swing, b_swing, change = MATCHES[name]
    override = dict(zip(("name", "value"), change, strict=True)) if change is not None else None
    expected = (name, games, seed, nodes_a, nodes_b, workers, "A", "B", override, 300)
    keys = ("match", "games_requested", "seed", "nodes_a", "nodes_b", "concurrency",
            "engine_a", "engine_b", "variant", "maxmoves")
    if tuple(data.get(key) for key in keys) != expected:
        raise ValueError(f"{path}: wrong match identity, budget or number of workers")
    if (data["exe_sha256"], data["book_sha256"], data["fastchess_revision"]) != (
        ENGINE_SHA, BOOK_SHA, FASTCHESS_REVISION,
    ):
        raise ValueError(f"{path}: engine, book or fastchess provenance differs")
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
        check_preflight(data, a_swing, b_swing)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error
    return data, ""


def read_match(raw, name, pgn):
    meta, reason = read_meta(raw, name)
    if meta is None:
        return Match(name, "unavailable", note=reason), None, None
    requested = MATCHES[name][0]
    groups = parse_games(raw / f"{name}.pgn", pgn, exact_moves=True)
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K7")
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


def gates(raw, pgn, only_k=False):
    k_result = read_match(raw, "K7", pgn)
    k, same, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K7 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K7 PASS: A and B both accepted explicit EvalSwingMult 48, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K7": k_result}
    c_result = read_match(raw, "C7", pgn)
    c, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C7 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C7 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K7": k_result, "C7": c_result}


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        name = fields[0]
        if name in CANDIDATES:
            if len(fields) != 2 or name in forecasts:
                raise ValueError(f"{path}: expected one signed Elo for {name}")
            forecasts[name] = Fraction(0) if fields[1] == "zero" else Fraction(fields[1])
        elif name == "replicated":
            if len(fields) != 3 or fields[1] != REPLICATION or fields[2].lower() not in ("yes", "no") or name in forecasts:
                raise ValueError(f"{path}: expected one replicated E48k yes|no")
            forecasts[name] = fields[2].lower() == "yes"
    if forecasts.keys() != {*CANDIDATES, "replicated"}:
        raise ValueError(f"{path}: expected seven signed Elo and one replication forecast")
    return forecasts


def print_grades(results, pooled, verdict, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo must have the forecast sign and fall within a factor of 1.5 of "
          "its magnitude. A zero forecast requires zero. The replication forecast uses exact yes/no matching.\n")
    print("| Forecast | Guess | Observed | Grade | Evidence status |")
    print("|---|---:|---:|---|---|")
    grades = []
    for name in CANDIDATES:
        row = results[name][0]
        grade = grade_elo(forecasts[name], row.elo)
        grades.append(grade)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(row.elo)} | {grade} | {match_status(row)} |")
    guess = forecasts["replicated"]
    grade = "ungraded" if verdict is None else "survives" if guess == verdict else "KILLED"
    grades.append(grade)
    print(f"| {REPLICATION} REPLICATED | {yes_no(guess)} | {yes_no(verdict)} | {grade} | {match_status(pooled)} |")
    print(f"\n{sum(v.startswith('KILLED') for v in grades)} KILLED, "
          f"{grades.count('survives')} survive, {grades.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table N. EvalSwing paired games and identical move lists\n")
    print("W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. "
          "Identical pairs share the complete ordered UCI move sequence.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---|---:|---|---|---|---:|---|")
    for row, same in rows:
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        reading = ("two-seed gain comparison" if row.name in ("E48k", "E48kr", "E48k + E48kr pooled")
                   else exploratory_read(row))
        print(f"| {row.name} | {match_status(row)} | {game_count} | {wld} | {penta} | "
              f"{number(row.elo)} {interval(row.interval)} | {sequence} | {reading} |")


def verify_slots(results):
    times = {name: (results[name][0].match_start, results[name][0].match_end) for name in CANDIDATES}
    for slot in SLOTS:
        for previous, current in zip(slot, slot[1:]):
            end, start = times[previous][1], times[current][0]
            if end and start and end > start:
                raise ValueError(f"{current} began before {previous} ended in the same slot")
    start_a, end_a = times[SLOTS[0][0]]
    start_b, end_b = times[SLOTS[1][0]]
    if all((start_a, end_a, start_b, end_b)) and max(start_a, start_b) >= min(end_a, end_b):
        raise ValueError("the first match in each slot did not overlap")


def print_openings(results, prior_dirs, pgn, old_row):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings.\n")
    current = {
        name: (row.games // 2, fens) if fens is not None else None
        for name, (row, _, fens) in results.items()
    }
    historical = {
        f"Job {job} {name}": opening_fens(prior_dirs[job] / f"{name}.pgn", pgn)
        for job, names in PRIOR.items() for name in names
    }
    old_seed = historical["Job 17 E48k"]
    fresh_seed = current["E48kr"]
    if old_seed is not None and old_row.penta and 2 * old_seed[0] != old_row.games:
        raise ValueError("Job 17 E48k opening pair count disagrees with its paired statistics")
    shared_seed = len(fresh_seed[1] & old_seed[1]) if fresh_seed is not None and old_seed is not None else "n/a"
    print(f"E48k and E48kr distinct shared exact FENs = {shared_seed}.\n")

    print("| File | Status | Complete pairs | Distinct exact FENs |")
    print("|---|---|---:|---:|")
    all_files = {**current, **historical}
    for name, entry in all_files.items():
        status = (match_status(results[name][0]) if name in results
                  else "saved" if entry is not None else "missing PGN")
        pairs, distinct = (entry[0], len(entry[1])) if entry is not None else ("n/a", "n/a")
        print(f"| {name} | {status} | {pairs} | {distinct} |")

    def label(name):
        if name in results and results[name][0].status != "complete":
            return f"{name} (incomplete)"
        return name

    comparisons = (
        ("Within Job 18", combinations(current, 2)),
        ("Job 18 against Jobs 13–17", product(current, historical)),
    )
    for heading, pairs in comparisons:
        print(f"\n### {heading}\n")
        print("| File A | File B | Shared exact FENs |")
        print("|---|---|---:|")
        for left, right in pairs:
            a, b = all_files[left], all_files[right]
            shared = len(a[1] & b[1]) if a is not None and b is not None else "n/a"
            print(f"| {label(left)} | {label(right)} | {shared} |")


def table(raw, prior_dirs, pgn, forecasts):
    results = gates(raw, pgn)
    old, old_same = read_job17_match(prior_dirs[17], "E48k", pgn)
    results.update((name, read_match(raw, name, pgn)) for name in CANDIDATES)
    verify_slots(results)
    fresh, fresh_same, _ = results["E48kr"]
    pooled = pool_seeds(old, fresh)
    pooled_same = old_same + fresh_same if pooled.games else None
    verdict = replicated(fresh, pooled)
    print_grades(results, pooled, verdict, forecasts)
    print_table([(old, old_same), (fresh, fresh_same), (pooled, pooled_same),
                 *(results[name][:2] for name in CANDIDATES[1:])])
    print("\nE48k (job 17 + E48kr) gets a verdict by the rule of file 15: REPLICATED when its fresh seed alone "
          "gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose "
          "lower end is above 0. Every other cell is exploratory: no verdict, a row each; one whose 95 % interval "
          "lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.")
    lower = pooled.interval[0] if pooled.interval is not None else None
    print(f"E48k REPLICATED {yes_no(verdict)}. Fresh Elo {number(fresh.elo, digits=4)}, "
          f"pooled lower 95% bound {number(lower, digits=4)}. Evidence {match_status(pooled)}.")
    print_openings(results, prior_dirs, pgn, old)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("gates", "table"):
        option = modes.add_parser(mode)
        option.add_argument("raw", type=Path)
        option.add_argument("--python-chess-dir", type=Path)
        if mode == "gates":
            option.add_argument("--only-k", action="store_true")
        else:
            for job in PRIOR:
                option.add_argument(f"--job{job}-raw", type=Path, required=True)
            option.add_argument("--prediction", type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, args.only_k)
    else:
        prior_dirs = {job: getattr(args, f"job{job}_raw") for job in PRIOR}
        table(args.raw, prior_dirs, pgn, read_prediction(args.prediction))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
