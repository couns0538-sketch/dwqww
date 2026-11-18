#!/usr/bin/env python3
"""Audit Job 15 paired games, apply the replication rule, and compare opening FENs."""

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job14 in (HERE.parent / "job14", HERE.parent / "sol-job14"):
    if (job14 / "analyze_matches14.py").is_file():
        sys.path.insert(0, str(job14))
        break
else:
    raise SystemExit("Job 14's analyze_matches14.py is missing from adjacent job14 or sol-job14.")

from analyze_matches14 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, Match, REFUSAL, digest, grade_elo, interval,
    number, parse_games, penta_estimate, pgn_module, pool_seeds, read_match as read_job14_match,
    replicated, summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    "K4": (100, 7151, 5000, 5000, 4, None),
    "C4": (200, 7152, 10000, 20000, 4, None),
    "E6k2": (2000, 7154, 2000, 2000, 2, "6"),
    "E12k2": (2000, 7155, 2000, 2000, 2, "12"),
    "D12v3": (2000, 7156, 2000, 2000, 2, "12"),
    "E6m": (2000, 7157, 5000, 5000, 2, "6"),
    "E6t": (2000, 7158, 10000, 10000, 2, "6"),
}
CANDIDATES = tuple(name for name in MATCHES if name not in ("K4", "C4"))
REPLICATIONS = {"E6k": "E6k2", "E12k": "E12k2"}
EXPLORATORY = ("D12v3", "E6m", "E6t")
PRIOR13 = ("E2", "E3k", "E6")
PRIOR14 = ("E3k2", "E6b", "E6k", "E12k")


def engine_doses(command):
    engine_sections = []
    for start, flag in enumerate(command):
        if flag != "-engine":
            continue
        end = next((index for index in range(start + 1, len(command)) if command[index].startswith("-")), len(command))
        engine_sections.append(command[start + 1:end])
    result = {}
    for section in engine_sections:
        names = [arg.removeprefix("name=") for arg in section if arg.startswith("name=")]
        if len(names) != 1 or names[0] in result:
            raise ValueError("fastchess argv must contain two distinct named engines")
        prefix = "option.EvalSwingMult="
        result[names[0]] = [arg.removeprefix(prefix) for arg in section if arg.startswith(prefix)]
    return result


def read_meta(directory, name):
    path = directory / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        return None, "unfinished: metadata missing or unfinished"
    data = json.loads(path.read_text(encoding="utf-8"))
    games, seed, nodes_a, nodes_b, workers, variant = MATCHES[name]
    override = {"name": "EvalSwingMult", "value": variant} if variant is not None else None
    expected = (name, games, seed, nodes_a, nodes_b, workers, "A", "B", override, 300)
    keys = ("match", "games_requested", "seed", "nodes_a", "nodes_b", "concurrency",
            "engine_a", "engine_b", "variant", "maxmoves")
    if tuple(data.get(key) for key in keys) != expected:
        raise ValueError(f"{path}: match identity, node budgets or worker count are incorrect")
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
    baseline = data["settings_b"]
    required = {"setoption name Threads value 1", "setoption name Hash value 16",
                "setoption name OwnBook value false"}
    if not required <= set(baseline):
        raise ValueError(f"{path}: baseline settings differ in threads, hash or book")
    compare_12_to_3 = name == "D12v3"
    baseline_doses = ["3"] if compare_12_to_3 else []
    candidate_doses = [*baseline_doses, variant] if variant is not None else baseline_doses
    dose_prefix = "setoption name EvalSwingMult value "
    if [option.removeprefix(dose_prefix) for option in baseline if option.startswith(dose_prefix)] != baseline_doses:
        raise ValueError(f"{path}: wrong EvalSwingMult for engine B")
    candidate = [*baseline, f"{dose_prefix}{variant}"] if variant is not None else baseline
    expected_doses = {"A": candidate_doses, "B": baseline_doses}
    if engine_doses(data["fastchess_command"]) != expected_doses:
        raise ValueError(f"{path}: wrong per-engine EvalSwingMult settings in fastchess argv")
    if (data["settings_a"] != candidate or data["preflight_settings_sent"] != candidate
            or data["preflight_reply"][-1:] != ["readyok"]
            or any(REFUSAL.search(line) for line in data["preflight_reply"])):
        raise ValueError(f"{path}: missing clean preflight for the specified settings")
    return data, ""



def read_match(directory, name, pgn):
    meta, reason = read_meta(directory, name)
    if meta is None:
        return Match(name, "unavailable", note=reason)
    requested = MATCHES[name][0]
    groups = parse_games(directory / f"{name}.pgn", pgn, exact_moves=name == "K4")
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K4")
    games = 2 * sum(penta)
    if raw_games > requested or max(groups, default=0) > requested // 2:
        raise ValueError(f"{name}: PGN exceeds its scheduled game count or round IDs")
    if meta["status"] == "complete" and (raw_games, games) != (requested, requested):
        raise ValueError(f"{name}: reported complete without {requested} complete paired games")
    result = Match(
        name, meta["status"], raw_games, games, w, l, d, penta, abnormal=abnormal,
        match_start=meta.get("match_start_utc"), match_end=meta.get("match_end_utc"),
        provenance=(meta["exe_sha256"], meta["fastchess_sha256"], meta["book_sha256"], tuple(meta["settings_b"])),
    )
    print(f"{name}: {raw_games} PGN games, {games} paired, {raw_games - games} unpaired, "
          f"A W-L-D {w}-{l}-{d}, penta {penta}, abnormal terminations {abnormal}.")
    printed = [
        report for report in summarized_output(directory / f"{name}.out")
        if (report["games"], report["wins"], report["losses"], report["draws"], report["penta"])
        == (games, w, l, d, penta)
    ]
    actual = penta_estimate(penta, deterministic=bool(printed))
    if printed:
        report = printed[-1]
        raw_elo, raw_width = report["elo"], report["margin"]
        if actual is None or any(abs(float(x - y)) > 0.0050001
                                 for x, y in zip((raw_elo, raw_width), actual, strict=True)):
            raise ValueError(f"{name}: printed Elo or 95% halfwidth disagrees with paired PGN reconstruction")
        result.elo, result.width = raw_elo, raw_width
        print(f"{name}: printed Elo {number(result.elo)} 95% {interval(result.interval)} verified.")
    elif name in ("K4", "C4"):
        raise ValueError(f"{name}: no printed pentanomial interval matches the PGN and pair counts")
    elif actual is None:
        result.note = "no usable paired interval"
    else:
        result.elo, result.width = actual
        result.note = "interval reconstructed from paired PGN counts; no matching printed interval"
    return result


def gates(raw, pgn, only_k):
    k = read_match(raw, "K4", pgn)
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0):
        raise ValueError(f"K4 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K4 PASS: 50/50 pairs with identical moves and 1–1 points.")
    if only_k:
        return
    c = read_match(raw, "C4", pgn)
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C4 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C4 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")




def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] in CANDIDATES:
            name = fields[0]
            if len(fields) != 2 or name in forecasts:
                raise ValueError(f"{path}: expected one signed Elo forecast for {name}")
            forecasts[name] = Fraction(0) if fields[1] == "zero" else Fraction(fields[1])
        if fields[0] == "replicated":
            if len(fields) != 3 or fields[1] not in REPLICATIONS or fields[2].lower() not in ("yes", "no"):
                raise ValueError(f"{path}: expected replicated E6k|E12k yes|no")
            key = "replicated", fields[1]
            if key in forecasts:
                raise ValueError(f"{path}: duplicate replication forecast")
            forecasts[key] = fields[2].lower() == "yes"
    expected = {*CANDIDATES, *(("replicated", name) for name in REPLICATIONS)}
    if forecasts.keys() != expected:
        raise ValueError(f"{path}: expected five signed Elo and two replication forecasts")
    return forecasts


def match_status(row):
    status = "complete" if row.status == "complete" else f"incomplete ({row.status})"
    if row.note:
        status += f": {row.note}"
    if row.raw_games > row.games:
        status += f" ({row.raw_games - row.games} unpaired excluded)"
    return status.replace("|", "&#124;").replace("\n", " ")


def print_grades(matches, pools, verdicts, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo must have the forecast sign and fall within a factor of 1.5 "
          "of its magnitude. A zero forecast requires zero. Replication forecasts use exact yes/no matching.\n")
    print("| Forecast | Guess | Observed | Grade | Evidence status |")
    print("|---|---:|---:|---|---|")
    grades = []
    for name in CANDIDATES:
        row = matches[name]
        verdict = grade_elo(forecasts[name], row.elo)
        grades.append(verdict)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(row.elo)} | {verdict} | {match_status(row)} |")
    for name in REPLICATIONS:
        predicted, observed = forecasts["replicated", name], verdicts[name]
        verdict = "ungraded" if observed is None else "survives" if predicted == observed else "KILLED"
        grades.append(verdict)
        print(f"| {name} REPLICATED | {yes_no(predicted)} | {yes_no(observed)} | {verdict} | "
              f"{match_status(pools[name])} |")
    print(f"\n{sum(v.startswith('KILLED') for v in grades)} KILLED, "
          f"{grades.count('survives')} survive, {grades.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table K. EvalSwingMult paired-game results\n")
    print("W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial "
          "Elo ± halfwidth convention. Each analyzed pair contains both colors.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] |")
    print("|---|---|---:|---|---|---|")
    for row in rows:
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        counts = ", ".join(map(str, row.penta)) or "n/a"
        print(f"| {row.name} | {match_status(row)} | {game_count} | {wld} | {counts} | "
              f"{number(row.elo)} {interval(row.interval)} |")


def verify_slots(matches):
    initial = matches["E6k2"], matches["E6t"]
    if all(match.match_start and match.match_end for match in initial):
        if max(match.match_start for match in initial) >= min(match.match_end for match in initial):
            raise ValueError("the two slots did not overlap")
    for first, second in (("E6k2", "E12k2"), ("E12k2", "D12v3"), ("D12v3", "E6m")):
        ended, started = matches[first].match_end, matches[second].match_start
        if ended and started and started < ended:
            raise ValueError(f"{second} started before {first} ended in the same slot")


def opening_fens(path, pgn):
    if not path.is_file():
        return None
    groups = parse_games(path, pgn, exact_moves=False)
    tally_pairs(groups, exact_moves=False)  # Validate colors and exact opening tags in every complete pair.
    tags = [games[0].start for games in groups.values() if len(games) == 2]
    return len(tags), set(tags)


def print_openings(raw, prior13, prior14, pgn, matches):
    print("\n## Shared openings\n")
    print("Counts are distinct exact FEN tags shared by two files. Each file contributes one "
          "opening per complete color-reversed pair. The inventory shows complete pairs and distinct FEN tags.\n")
    new = {
        name: opening_fens(raw / f"{name}.pgn", pgn)
        if name not in matches or matches[name].penta else None for name in MATCHES
    }
    old = {
        **{f"Job 13 {name}": opening_fens(prior13 / f"{name}.pgn", pgn) for name in PRIOR13},
        **{f"Job 14 {name}": opening_fens(prior14 / f"{name}.pgn", pgn) for name in PRIOR14},
    }
    for name, match in matches.items():
        if (entry := new[name]) is not None and match.penta and 2 * entry[0] != match.games:
            raise ValueError(f"{name}: opening pair tally differs from Table K")
    fens = {**new, **old}
    print("| File | Status | Complete pairs | Distinct exact FENs |")
    print("|---|---|---:|---:|")
    for name, entry in fens.items():
        status = match_status(matches[name]) if name in matches else "saved" if entry is not None else "missing PGN"
        print(f"| {name} | {status} | {entry[0] if entry else 'n/a'} | {len(entry[1]) if entry else 'n/a'} |")
    print("\n| File A | File B | Shared exact FENs |")
    print("|---|---|---:|")
    def label(name):
        return f"{name} (incomplete)" if name in matches and matches[name].status != "complete" else name
    for left, right in (*combinations(new, 2), *product(new, old)):
        a, b = fens[left], fens[right]
        shared = len(a[1] & b[1]) if a is not None and b is not None else "n/a"
        print(f"| {label(left)} | {label(right)} | {shared} |")


def table(raw, prior13, prior14, pgn, forecasts):
    previous = {name: read_job14_match(prior14, name, pgn) for name in REPLICATIONS}
    matches = {name: read_match(raw, name, pgn) for name in CANDIDATES}
    verify_slots(matches)
    pools = {name: pool_seeds(previous[name], matches[fresh]) for name, fresh in REPLICATIONS.items()}
    verdicts = {name: replicated(matches[fresh], pools[name]) for name, fresh in REPLICATIONS.items()}
    print_grades(matches, pools, verdicts, forecasts)
    rows = [row for name, fresh in REPLICATIONS.items() for row in (previous[name], matches[fresh], pools[name])]
    print_table([*rows, *(matches[name] for name in EXPLORATORY)])
    print("\nA cell is REPLICATED when its fresh seed alone gives Elo above 0 AND the pool of its two "
          "seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. "
          "Cells E6k (job 14 + E6k2) and E12k (job 14 + E12k2) get a verdict; D12v3, E6m and E6t "
          "are exploratory: no verdict, a row each.")
    for name, fresh in REPLICATIONS.items():
        bound = pools[name].interval[0] if pools[name].interval is not None else None
        print(f"{name} REPLICATED: {yes_no(verdicts[name])}. Fresh Elo {number(matches[fresh].elo, digits=4)}, "
              f"pooled lower 95% bound {number(bound, digits=4)}. Evidence {match_status(pools[name])}.")
    print_openings(raw, prior13, prior14, pgn, matches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("gates", "table"):
        sub = modes.add_parser(mode)
        sub.add_argument("raw", type=Path)
        sub.add_argument("--python-chess-dir", type=Path)
        if mode == "gates":
            sub.add_argument("--only-k", action="store_true")
        else:
            for option in ("job13-raw", "job14-raw", "prediction"):
                sub.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, args.only_k)
    else:
        table(args.raw, args.job13_raw, args.job14_raw, pgn, read_prediction(args.prediction))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
