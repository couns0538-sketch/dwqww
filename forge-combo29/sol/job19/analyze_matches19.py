#!/usr/bin/env python3
"""Audit Job 19 paired PGNs, control gates, and exact opening overlap."""

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job18 in (HERE.parent / "job18", HERE.parent / "sol-job18"):
    if (job18 / "analyze_matches18.py").is_file():
        sys.path.insert(0, str(job18))
        break
else:
    raise SystemExit("Job 18's analyze_matches18.py is missing from adjacent job18 or sol-job18.")

from analyze_matches18 import (
    BOOK_SHA, CANDIDATES as PRIOR18, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, check_preflight, digest, exploratory_read, grade_elo,
    identical_moves, interval, match_status, number, opening_fens, parse_games,
    penta_estimate, pgn_module, pool_seeds, read_match as read_job18_match, replicated,
    summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/Max, B Mult/Max, candidate variant
    "K8": (100, 7191, 2000, 2000, 4, ("64", None), ("64", None), None),
    "C8": (200, 7192, 10000, 20000, 4, ("0", None), ("0", None), None),
    "E64kr": (2000, 7193, 2000, 2000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
    "E48tr": (2000, 7194, 10000, 10000, 2, ("48", None), ("0", None), ("EvalSwingMult", "48")),
    "E64t": (2000, 7195, 10000, 10000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
    "E48w": (2000, 7196, 20000, 20000, 2, ("48", None), ("0", None), ("EvalSwingMult", "48")),
}
CONTROLS = ("K8", "C8")
SLOTS = (("E64kr", "E48tr", "E64t"), ("E48w",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**PRIOR_JOBS, 18: PRIOR18}
REPLICATIONS = {"E64k": "E64kr", "E48t": "E48tr"}


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
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K8")
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
    k_result = read_match(raw, "K8", pgn)
    k, same, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K8 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K8 PASS: A and B both accepted explicit EvalSwingMult 64, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K8": k_result}
    c_result = read_match(raw, "C8", pgn)
    c, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C8 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C8 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K8": k_result, "C8": c_result}


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
            if len(fields) != 3 or fields[1] not in REPLICATIONS or fields[2].lower() not in ("yes", "no"):
                raise ValueError(f"{path}: expected replicated E64k|E48t yes|no")
            key = name, fields[1]
            if key in forecasts:
                raise ValueError(f"{path}: duplicate replication forecast for {fields[1]}")
            forecasts[key] = fields[2].lower() == "yes"
    if forecasts.keys() != {*CANDIDATES, *(("replicated", name) for name in REPLICATIONS)}:
        raise ValueError(f"{path}: expected four signed Elo and two replication forecasts")
    return forecasts


def print_grades(results, pools, verdicts, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo must have the forecast sign and fall within a factor of 1.5 of "
          "its magnitude. A zero forecast requires zero. Replication forecasts use exact yes/no matching.\n")
    print("| Forecast | Guess | Observed | Grade | Evidence status |")
    print("|---|---:|---:|---|---|")
    grades = []
    for name in CANDIDATES:
        row = results[name][0]
        grade = grade_elo(forecasts[name], row.elo)
        grades.append(grade)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(row.elo)} | {grade} | {match_status(row)} |")
    for name in REPLICATIONS:
        guess, verdict = forecasts["replicated", name], verdicts[name]
        grade = "ungraded" if verdict is None else "survives" if guess == verdict else "KILLED"
        grades.append(grade)
        print(f"| {name} REPLICATED | {yes_no(guess)} | {yes_no(verdict)} | {grade} | {match_status(pools[name][0])} |")
    print(f"\n{sum(v.startswith('KILLED') for v in grades)} KILLED, "
          f"{grades.count('survives')} survive, {grades.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table O. EvalSwing paired games and identical move lists\n")
    print("W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. "
          "Identical pairs share the complete ordered UCI move sequence.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---|---:|---|---|---|---:|---|")
    for row, same in rows:
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        reading = exploratory_read(row) if row.name in ("E64t", "E48w") else "two-seed gain comparison"
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


def print_openings(results, prior_dirs, pgn, old_results):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings.\n")
    verified = {
        **results,
        **{f"Job 18 {name}": row for name, row in old_results.items()},
    }
    tagged = {
        name: (row.games // 2, fens) if fens is not None else None
        for name, (row, _, fens) in verified.items()
    }
    current = {name: tagged[name] for name in results}
    historical = {}
    for job, names in PRIOR.items():
        for name in names:
            label = f"Job {job} {name}"
            historical[label] = (tagged[label] if label in tagged
                                 else opening_fens(prior_dirs[job] / f"{name}.pgn", pgn))
    all_files = {**current, **historical}

    def label(name):
        if name in verified and verified[name][0].status != "complete":
            return f"{name} (incomplete)"
        return name

    def share(left, right):
        a, b = all_files[left], all_files[right]
        return len(a[1] & b[1]) if a is not None and b is not None else "n/a"

    for name, fresh in REPLICATIONS.items():
        old = f"Job 18 {name}"
        print(f"{label(old)} and {label(fresh)} distinct shared exact FENs = {share(old, fresh)}.")
    print()
    print("| File | Status | Complete pairs | Distinct exact FENs |")
    print("|---|---|---:|---:|")
    for name, entry in all_files.items():
        status = (match_status(verified[name][0]) if name in verified
                  else "saved" if entry is not None else "missing PGN")
        pairs, distinct = (entry[0], len(entry[1])) if entry is not None else ("n/a", "n/a")
        print(f"| {name} | {status} | {pairs} | {distinct} |")

    comparisons = (
        ("Within Job 19", combinations(current, 2)),
        ("Job 19 against Jobs 13–18", product(current, historical)),
    )
    for heading, pairs in comparisons:
        print(f"\n### {heading}\n")
        print("| File A | File B | Shared exact FENs |")
        print("|---|---|---:|")
        for left, right in pairs:
            print(f"| {label(left)} | {label(right)} | {share(left, right)} |")


def table(raw, prior_dirs, pgn, forecasts):
    results = gates(raw, pgn)
    old_results = {name: read_job18_match(prior_dirs[18], name, pgn) for name in REPLICATIONS}
    results.update((name, read_match(raw, name, pgn)) for name in CANDIDATES)
    verify_slots(results)
    pools, verdicts, rows = {}, {}, []
    for name, fresh_name in REPLICATIONS.items():
        old, old_same, _ = old_results[name]
        fresh, fresh_same, _ = results[fresh_name]
        pooled = pool_seeds(old, fresh)
        pooled_same = old_same + fresh_same if pooled.games else None
        pools[name] = pooled, pooled_same
        verdicts[name] = replicated(fresh, pooled)
        rows.extend(((old, old_same), (fresh, fresh_same), pools[name]))
    print_grades(results, pools, verdicts, forecasts)
    rows.extend(results[name][:2] for name in CANDIDATES if name not in REPLICATIONS.values())
    print_table(rows)
    print("\nE64k (job 18 + E64kr) and E48t (job 18 + E48tr) each get a verdict by the rule of file 15: "
          "REPLICATED when the fresh seed alone gives Elo above 0 AND the pool of the two seeds (pentanomial "
          "counts added) has a 95 % interval whose lower end is above 0. E64t and E48w are exploratory: "
          "no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh "
          "seed in a later job before anything is said about it.")
    for name, fresh in REPLICATIONS.items():
        pooled = pools[name][0]
        lower = pooled.interval[0] if pooled.interval is not None else None
        print(f"{name} REPLICATED {yes_no(verdicts[name])}. Fresh Elo {number(results[fresh][0].elo, digits=4)}, "
              f"pooled lower 95% bound {number(lower, digits=4)}. Evidence {match_status(pooled)}.")
    print_openings(results, prior_dirs, pgn, old_results)


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
