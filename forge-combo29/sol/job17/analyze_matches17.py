#!/usr/bin/env python3
"""Audit Job 17 paired results, move-list identity, and opening overlap."""

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job16 in (HERE.parent / "job16", HERE.parent / "sol-job16"):
    if (job16 / "analyze_matches16.py").is_file():
        sys.path.insert(0, str(job16))
        break
else:
    raise SystemExit("Job 16's analyze_matches16.py is missing from adjacent job16 or sol-job16.")

from analyze_matches16 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, Match, PRIOR13, PRIOR14, PRIOR15,
    check_preflight, digest, exploratory_read, grade_elo, interval, match_status, number,
    opening_fens, parse_games, penta_estimate, pgn_module, pool_seeds,
    read_match as read_job16_match, replicated, summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/Max, B Mult/Max, candidate variant
    "K6": (100, 7171, 2000, 2000, 4, ("3", "400"), ("3", "400"), None),
    "C6": (200, 7172, 10000, 20000, 4, (None, None), (None, None), None),
    "X400r": (2000, 7173, 2000, 2000, 2, ("6", "400"), ("6", "200"), ("EvalSwingMax", "400")),
    "E24kr": (2000, 7174, 2000, 2000, 2, ("24", None), ("0", None), ("EvalSwingMult", "24")),
    "X400m3": (2000, 7175, 2000, 2000, 2, ("3", "400"), ("3", "200"), ("EvalSwingMax", "400")),
    "X100m3": (2000, 7176, 2000, 2000, 2, ("3", "100"), ("3", "200"), ("EvalSwingMax", "100")),
    "E48k": (2000, 7177, 2000, 2000, 2, ("48", None), ("0", None), ("EvalSwingMult", "48")),
    "X400w": (1600, 7178, 20000, 20000, 2, ("6", "400"), ("6", "200"), ("EvalSwingMax", "400")),
}
CANDIDATES = tuple(name for name in MATCHES if name not in ("K6", "C6"))
REPLICATIONS = {"X400": "X400r", "E24k": "E24kr"}
PRIOR16 = ("X400", "X100", "X50", "D12v3b", "E24k", "X400t", "E12t")
SLOT1 = ("X400r", "E24kr", "X400m3", "X100m3", "E48k")


def identical_moves(groups):
    return sum(games[0].moves == games[1].moves for games in groups.values() if len(games) == 2)


def read_meta(directory, name):
    path = directory / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        return None, "unfinished: metadata missing or unfinished"
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


def read_match(directory, name, pgn):
    meta, reason = read_meta(directory, name)
    if meta is None:
        return Match(name, "unavailable", note=reason), None
    requested = MATCHES[name][0]
    groups = parse_games(directory / f"{name}.pgn", pgn, exact_moves=True)
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K6")
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
    elif name in ("K6", "C6"):
        raise ValueError(f"{name}: no printed pentanomial interval matches the PGN and pair counts")
    elif actual is None:
        result.note = "no usable paired interval"
    else:
        result.elo, result.width = actual
        result.note = "interval reconstructed from paired PGN counts; no matching printed interval"
    return result, identical_moves(groups)


def gates(raw, pgn, only_k):
    k, same = read_match(raw, "K6", pgn)
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K6 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K6 PASS: A and B both accepted explicit EvalSwingMult 3 and EvalSwingMax 400, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return
    c, _ = read_match(raw, "C6", pgn)
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C6 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C6 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
def prior_match(raw, name, pgn):
    row = read_job16_match(raw, name, pgn)
    if row.penta == ():
        return row, None
    groups = parse_games(raw / f"{name}.pgn", pgn, exact_moves=True)
    wld, penta, _ = tally_pairs(groups, exact_moves=False)
    if wld != (row.wins, row.losses, row.draws) or penta != row.penta:
        raise ValueError(f"{name}: exact-move parse disagrees with prior paired counts")
    return row, identical_moves(groups)


def replicated_loss(fresh, pool):
    if fresh.elo is not None and fresh.elo >= 0:
        return False
    if pool.interval is not None and pool.interval[1] >= 0:
        return False
    return None if fresh.elo is None or pool.interval is None else True


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] in CANDIDATES:
            name = fields[0]
            if len(fields) != 2 or name in forecasts:
                raise ValueError(f"{path}: expected one signed Elo for {name}")
            forecasts[name] = Fraction(0) if fields[1] == "zero" else Fraction(fields[1])
        if fields[0] == "replicated":
            if len(fields) != 3 or fields[1] not in REPLICATIONS or fields[2].lower() not in ("yes", "no"):
                raise ValueError(f"{path}: expected replicated X400|E24k yes|no")
            key = "replicated", fields[1]
            if key in forecasts:
                raise ValueError(f"{path}: duplicate replication forecast")
            forecasts[key] = fields[2].lower() == "yes"
    expected = {*CANDIDATES, *(("replicated", name) for name in REPLICATIONS)}
    if forecasts.keys() != expected:
        raise ValueError(f"{path}: expected six signed Elo and two replication forecasts")
    return forecasts


def print_grades(matches, pools, verdicts, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo must have the forecast sign and fall within a factor of 1.5 of "
          "its magnitude. A zero forecast requires zero. Replication forecasts use exact yes/no matching.\n")
    print("| Forecast | Guess | Observed | Grade | Evidence status |")
    print("|---|---:|---:|---|---|")
    grades = []
    for name in CANDIDATES:
        row, _ = matches[name]
        grade = grade_elo(forecasts[name], row.elo)
        grades.append(grade)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(row.elo)} | {grade} | {match_status(row)} |")
    for name in REPLICATIONS:
        before, after = forecasts["replicated", name], verdicts[name]
        grade = "ungraded" if after is None else "survives" if before == after else "KILLED"
        grades.append(grade)
        print(f"| {name} REPLICATED | {yes_no(before)} | {yes_no(after)} | {grade} | {match_status(pools[name][0])} |")
    print(f"\n{sum(v.startswith('KILLED') for v in grades)} KILLED, "
          f"{grades.count('survives')} survive, {grades.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table M. EvalSwing moves and paired games\n")
    print("W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial Elo ± halfwidth "
          "convention. Same moves compare the complete ordered UCI sequence within a color-reversed pair.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---|---:|---|---|---|---:|---|")
    for row, same in rows:
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        counts = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        reading = ("two-seed LOSS comparison" if row.name in ("X400", "X400r", "X400 + X400r pooled")
                   else "two-seed gain comparison" if row.name in ("E24k", "E24kr", "E24k + E24kr pooled")
                   else exploratory_read(row))
        print(f"| {row.name} | {match_status(row)} | {game_count} | {wld} | {counts} | "
              f"{number(row.elo)} {interval(row.interval)} | {sequence} | {reading} |")


def verify_slots(matches):
    first, wide = (matches[name][0] for name in ("X400r", "X400w"))
    if first.match_start and first.match_end and wide.match_start and wide.match_end:
        if max(first.match_start, wide.match_start) >= min(first.match_end, wide.match_end):
            raise ValueError("the two slots did not overlap")
    for earlier, later in zip(SLOT1, SLOT1[1:]):
        ended, started = matches[earlier][0].match_end, matches[later][0].match_start
        if ended and started and started < ended:
            raise ValueError(f"{later} began before {earlier} ended in the same slot")


def print_openings(raw, prior13, prior14, prior15, prior16, pgn, matches):
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
        **{f"Job 15 {name}": opening_fens(prior15 / f"{name}.pgn", pgn) for name in PRIOR15},
        **{f"Job 16 {name}": opening_fens(prior16 / f"{name}.pgn", pgn) for name in PRIOR16},
    }
    for name, match in matches.items():
        if (entry := new[name]) is not None and match.penta and 2 * entry[0] != match.games:
            raise ValueError(f"{name}: opening pair tally differs from Table M")
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

def table(raw, prior13, prior14, prior15, prior16, pgn, forecasts):
    old = {name: prior_match(prior16, name, pgn) for name in REPLICATIONS}
    matches = {name: read_match(raw, name, pgn) for name in CANDIDATES}
    verify_slots(matches)
    pools = {}
    for name, fresh in REPLICATIONS.items():
        old_row, old_same = old[name]
        fresh_row, fresh_same = matches[fresh]
        pooled = pool_seeds(old_row, fresh_row)
        same = old_same + fresh_same if old_same is not None and fresh_same is not None and pooled.games else None
        pools[name] = pooled, same
    verdicts = {
        "X400": replicated_loss(matches["X400r"][0], pools["X400"][0]),
        "E24k": replicated(matches["E24kr"][0], pools["E24k"][0]),
    }
    print_grades(matches, pools, verdicts, forecasts)
    rows = [row for name, fresh in REPLICATIONS.items() for row in (old[name], matches[fresh], pools[name])]
    print_table([*rows, *(matches[name] for name in CANDIDATES if name not in REPLICATIONS.values())])
    print("\nE24k (job 16 + E24kr) gets a verdict by the rule of file 15: REPLICATED when its fresh seed alone "
          "gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose "
          "lower end is above 0. X400 (job 16 + X400r) is a LOSS, so the same rule mirrored: REPLICATED when its "
          "fresh seed alone gives Elo below 0 AND the pooled interval's upper end is below 0. Every other cell "
          "is exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 "
          "earns a fresh seed in a later job before anything is said about it.")
    for name, fresh in REPLICATIONS.items():
        pooled, _ = pools[name]
        bound_label, bound_index = ("upper", 1) if name == "X400" else ("lower", 0)
        bound = pooled.interval[bound_index] if pooled.interval is not None else None
        print(f"{name} REPLICATED: {yes_no(verdicts[name])}. Fresh Elo {number(matches[fresh][0].elo, digits=4)}, "
              f"pooled {bound_label} 95% bound {number(bound, digits=4)}. Evidence {match_status(pooled)}.")
    print_openings(raw, prior13, prior14, prior15, prior16, pgn, {name: row for name, (row, _) in matches.items()})


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
            for name in ("job13-raw", "job14-raw", "job15-raw", "job16-raw", "prediction"):
                option.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, args.only_k)
    else:
        table(args.raw, args.job13_raw, args.job14_raw, args.job15_raw, args.job16_raw,
              pgn, read_prediction(args.prediction))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
