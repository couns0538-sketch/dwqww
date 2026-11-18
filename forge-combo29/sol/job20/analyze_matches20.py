#!/usr/bin/env python3
"""Audit Job 20 paired PGNs, executable settings, and exact opening overlap."""

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
for job19 in (HERE.parent / "job19", HERE.parent / "sol-job19"):
    if (job19 / "analyze_matches19.py").is_file():
        sys.path.insert(0, str(job19))
        break
else:
    raise SystemExit("Job 19's analyze_matches19.py is missing from adjacent job19 or sol-job19.")

from analyze_matches19 import (
    BOOK_SHA, CANDIDATES as PRIOR19, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, check_preflight, digest, exploratory_read, grade_elo,
    identical_moves, interval, match_status, number, opening_fens, parse_games,
    penta_estimate, pgn_module, pool_seeds, read_match as read_job19_match, replicated,
    summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/FHB, B Mult/FHB, candidate variant
    "K9": (100, 7201, 2000, 2000, 4, ("0", "7"), ("0", "7"), None),
    "C9": (200, 7202, 10000, 20000, 4, ("0", "7"), ("0", "7"), None),
    "F7k": (2000, 7203, 2000, 2000, 2, ("0", "7"), ("0", "0"), ("FailHighBlend", "7")),
    "F7t": (2000, 7204, 10000, 10000, 2, ("0", "7"), ("0", "0"), ("FailHighBlend", "7")),
    "E64tr": (2000, 7205, 10000, 10000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
    "F7w": (2000, 7206, 20000, 20000, 2, ("0", "7"), ("0", "0"), ("FailHighBlend", "7")),
}
CONTROLS = ("K9", "C9")
SLOTS = (("F7k", "F7t", "E64tr"), ("F7w",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**PRIOR_JOBS, 19: PRIOR19}
FHB_PREFIX = "setoption name FailHighBlend value "
FHB_ADVERTISEMENT = "option name FailHighBlend type spin default 0 min 0 max 7"


def read_pca_sha(path):
    fields = path.read_text(encoding="utf-8").split()
    if not fields or not re.fullmatch(r"[0-9a-f]{64}", fields[0]) or fields[0] == ENGINE_SHA:
        raise ValueError(f"{path}: expected the distinct PCA executable SHA-256")
    return fields[0]


def check_match_preflight(data, a_extras, b_extras):
    command = data["fastchess_command"]
    sections = [i for i, value in enumerate(command) if value == "-engine"]
    if len(sections) != 2 or command.count("-each") != 1:
        raise ValueError("fastchess argv is missing expected engine sections")
    boundary = command.index("-each")
    cleaned = dict(data)
    for side, suffix, extras, start, end in (
        ("A", "", a_extras, sections[0], sections[1]),
        ("B", "_b", b_extras, sections[1], boundary),
    ):
        _, fhb = extras
        settings_key = f"settings_{side.lower()}"
        sent_key = f"preflight_settings_sent{suffix}"
        settings, sent = data[settings_key], data[sent_key]
        engine_args = command[start + 1:end]
        matching_options = [line for line in settings if line.startswith(FHB_PREFIX)]
        expected_settings = [FHB_PREFIX + fhb] if fhb is not None else []
        if f"name={side}" not in engine_args or f"cmd={data['exe']}" not in engine_args:
            raise ValueError(f"engine {side}: fastchess argv refers to a different engine")
        setting_args = ["option." + line.removeprefix("setoption name ").replace(" value ", "=", 1)
                        for line in settings]
        if [arg for arg in engine_args if arg.startswith("option.")] != setting_args:
            raise ValueError(f"engine {side}: fastchess options differ from preflight settings")
        if matching_options != expected_settings or settings != sent:
            raise ValueError(f"engine {side}: wrong explicit FailHighBlend or mismatched preflight commands")
        if fhb is not None and FHB_ADVERTISEMENT not in data[f"preflight_uci{suffix}"]:
            raise ValueError(f"engine {side}: PCA preflight did not advertise the expected FailHighBlend range")
        if fhb is None and any(line.startswith("option name FailHighBlend ") for line in data[f"preflight_uci{suffix}"]):
            raise ValueError(f"engine {side}: Job 4 preflight unexpectedly advertised FailHighBlend")
        cleaned[settings_key] = [line for line in settings if not line.startswith(FHB_PREFIX)]
        cleaned[sent_key] = cleaned[settings_key]
    check_preflight(cleaned, (a_extras[0], None), (b_extras[0], None))


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
    expected_exe = ENGINE_SHA if name == "E64tr" else pca_sha
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
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K9")
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
    k_result = read_match(raw, "K9", pgn, pca_sha)
    k, same, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K9 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K9 PASS: A and B both accepted explicit EvalSwingMult 0 and FailHighBlend 7 on PCA, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K9": k_result}
    c_result = read_match(raw, "C9", pgn, pca_sha)
    c, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C9 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C9 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K9": k_result, "C9": c_result}


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
        raise ValueError(f"{path}: expected four signed Elo forecasts")
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
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        if row.name.startswith("F7"):
            build = f"PCA, {MATCHES[row.name][2]:,}, FailHighBlend 7/0 and EvalSwingMult 0/0"
            reading = exploratory_read(row)
        else:
            build = "Job 4, 10,000, EvalSwingMult 64/0"
            reading = "two-seed gain comparison"
        print(f"| {row.name} | {build} | {match_status(row)} | {game_count} | {wld} | {penta} | "
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


def print_openings(results, prior_dirs, pgn, old_result):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings.\n")
    old_seed = "Job 19 E64t"
    verified = {**results, old_seed: old_result}
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

    print(f"{label(old_seed)} and {label('E64tr')} distinct shared exact FENs = {share(old_seed, 'E64tr')}.\n")
    print("| File | Status | Complete pairs | Distinct exact FENs |")
    print("|---|---|---:|---:|")
    for name, entry in all_files.items():
        status = (match_status(verified[name][0]) if name in verified
                  else "saved" if entry is not None else "missing PGN")
        pairs, distinct = (entry[0], len(entry[1])) if entry is not None else ("n/a", "n/a")
        print(f"| {name} | {status} | {pairs} | {distinct} |")

    comparisons = (
        ("Within Job 20", combinations(current, 2)),
        ("Job 20 against Jobs 13–19", product(current, historical)),
    )
    for heading, pairs in comparisons:
        print(f"\n### {heading}\n")
        print("| File A | File B | Shared exact FENs |")
        print("|---|---|---:|")
        for left, right in pairs:
            print(f"| {label(left)} | {label(right)} | {share(left, right)} |")


def table(raw, prior_dirs, pgn, forecasts, pca_sha):
    results = gates(raw, pgn, pca_sha)
    old_result = read_job19_match(prior_dirs[19], "E64t", pgn)
    old, old_same, _ = old_result
    results.update((name, read_match(raw, name, pgn, pca_sha)) for name in CANDIDATES)
    verify_slots(results)
    fresh, fresh_same, _ = results["E64tr"]
    rows = [results[name][:2] for name in CANDIDATES]
    pooled = None
    if fresh.status == "complete":
        pooled = pool_seeds(old, fresh)
        if pooled.games and old.status != "complete":
            pooled.note += f". Job 19 E64t incomplete, {old.games} paired games included"
        rows.extend((old_result[:2], (pooled, old_same + fresh_same if pooled.games else None)))
    print_grades(results, forecasts)
    print_table(rows)
    print("\nF7k, F7t and F7w are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above "
          "or wholly below 0 earns a fresh seed in a later job before anything is said about it. E64tr, only if "
          "complete, gives E64t its verdict by the rule of file 15 (REPLICATED when the fresh seed alone gives "
          "Elo above 0 AND the pool of the two seeds, pentanomial counts added, has a 95 % interval whose lower "
          "end is above 0); a cut E64tr gives no verdict.")
    if pooled is None:
        print(f"E64t verdict withheld. E64tr {match_status(fresh)}.")
    else:
        lower = pooled.interval[0] if pooled.interval is not None else None
        print(f"E64t REPLICATED {yes_no(replicated(fresh, pooled))}. Fresh Elo {number(fresh.elo, digits=4)}, "
              f"pooled lower 95% bound {number(lower, digits=4)}. Evidence {match_status(pooled)}.")
    print_openings(results, prior_dirs, pgn, old_result)


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
    args = parser.parse_args()
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
