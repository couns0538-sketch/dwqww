#!/usr/bin/env python3
"""Audit Job 16 paired games, track fresh-seed eligibility, and compare openings."""

import argparse
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job15 in (HERE.parent / "job15", HERE.parent / "sol-job15"):
    if (job15 / "analyze_matches15.py").is_file():
        sys.path.insert(0, str(job15))
        break
else:
    raise SystemExit("Job 15's analyze_matches15.py is missing from adjacent job15 or sol-job15.")

from analyze_matches15 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, Match, REFUSAL, digest, grade_elo, interval,
    number, parse_games, penta_estimate, pgn_module, pool_seeds, read_match as read_job15_match,
    replicated, summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/Max, B Mult/Max, candidate variant
    "K5": (100, 7161, 2000, 2000, 4, ("6", "200"), ("6", "200"), None),
    "C5": (200, 7162, 10000, 20000, 4, (None, None), (None, None), None),
    "X400": (2000, 7163, 2000, 2000, 2, ("6", "400"), ("6", "200"), ("EvalSwingMax", "400")),
    "X100": (2000, 7164, 2000, 2000, 2, ("6", "100"), ("6", "200"), ("EvalSwingMax", "100")),
    "X50": (2000, 7165, 2000, 2000, 2, ("6", "50"), ("6", "200"), ("EvalSwingMax", "50")),
    "D12v3b": (2000, 7166, 2000, 2000, 2, ("12", None), ("3", None), ("EvalSwingMult", "12")),
    "E24k": (2000, 7167, 2000, 2000, 2, ("24", None), ("0", None), ("EvalSwingMult", "24")),
    "X400t": (2000, 7168, 10000, 10000, 2, ("6", "400"), ("6", "200"), ("EvalSwingMax", "400")),
    "E12t": (2000, 7169, 10000, 10000, 2, ("12", None), ("0", None), ("EvalSwingMult", "12")),
}
CANDIDATES = tuple(name for name in MATCHES if name not in ("K5", "C5"))
PRIOR13 = ("E2", "E3k", "E6")
PRIOR14 = ("E3k2", "E6b", "E6k", "E12k")
PRIOR15 = ("E6k2", "E12k2", "D12v3", "E6m", "E6t")
SWING_OPTIONS = ("EvalSwingMult", "EvalSwingMax")
SENT_PREFIXES = tuple(f"setoption name {option} value " for option in SWING_OPTIONS)


def engine_swing_options(command):
    found = {}
    for start, flag in enumerate(command):
        if flag != "-engine":
            continue
        end = next((i for i in range(start + 1, len(command)) if command[i].startswith("-")), len(command))
        args = command[start + 1:end]
        names = [arg.removeprefix("name=") for arg in args if arg.startswith("name=")]
        if len(names) != 1 or names[0] in found:
            raise ValueError("fastchess argv must contain distinct A and B engine sections")
        found[names[0]] = tuple(
            tuple(arg.removeprefix(f"option.{option}=") for arg in args if arg.startswith(f"option.{option}="))
            for option in SWING_OPTIONS
        )
    return found


def check_preflight(meta, expected_a, expected_b):
    argv_swing = engine_swing_options(meta["fastchess_command"])
    if argv_swing.keys() != {"A", "B"}:
        raise ValueError("fastchess argv must contain exactly engines A and B")
    baselines = {}
    for side, suffix, expected in (("A", "", expected_a), ("B", "_b", expected_b)):
        settings = meta[f"settings_{side.lower()}"]
        sent = meta[f"preflight_settings_sent{suffix}"]
        reply = meta[f"preflight_reply{suffix}"]
        uci = meta[f"preflight_uci{suffix}"]
        desired = tuple((value,) if value is not None else () for value in expected)
        actual = tuple(tuple(line.removeprefix(p) for line in settings if line.startswith(p)) for p in SENT_PREFIXES)
        if actual != desired or argv_swing.get(side) != desired:
            raise ValueError(f"engine {side}: wrong explicit EvalSwingMult or EvalSwingMax")
        if (sent != settings or reply[-1:] != ["readyok"] or uci[-1:] != ["uciok"]
                or any(REFUSAL.search(line) for line in (*uci, *reply))):
            raise ValueError(f"engine {side}: preflight did not acknowledge its literal options cleanly")
        baselines[side] = [line for line in settings if not line.startswith(SENT_PREFIXES)]
    required = {"setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false"}
    if baselines["A"] != baselines["B"] or not required <= set(baselines["B"]):
        raise ValueError("engine sides disagree on their common baseline settings")


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
        return Match(name, "unavailable", note=reason)
    requested = MATCHES[name][0]
    groups = parse_games(directory / f"{name}.pgn", pgn, exact_moves=name == "K5")
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K5")
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
    elif name in ("K5", "C5"):
        raise ValueError(f"{name}: no printed pentanomial interval matches the PGN and pair counts")
    elif actual is None:
        result.note = "no usable paired interval"
    else:
        result.elo, result.width = actual
        result.note = "interval reconstructed from paired PGN counts; no matching printed interval"
    return result


def gates(raw, pgn, only_k):
    k = read_match(raw, "K5", pgn)
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0):
        raise ValueError(f"K5 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K5 PASS: A and B both accepted explicit EvalSwingMult 6 and EvalSwingMax 200, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return
    c = read_match(raw, "C5", pgn)
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C5 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C5 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")





def match_status(row):
    status = "complete" if row.status == "complete" else f"incomplete ({row.status})"
    if row.note:
        status += f": {row.note}"
    if row.raw_games > row.games:
        status += f" ({row.raw_games - row.games} unpaired excluded)"
    return status.replace("|", "&#124;").replace("\n", " ")



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
            if (len(fields) != 3 or fields[1] != "D12v3" or fields[2].lower() not in ("yes", "no")
                    or "replicated" in forecasts):
                raise ValueError(f"{path}: expected replicated D12v3 yes|no")
            forecasts["replicated"] = fields[2].lower() == "yes"
    if forecasts.keys() != {*CANDIDATES, "replicated"}:
        raise ValueError(f"{path}: expected seven signed Elo and one replication forecasts")
    return forecasts


def exploratory_read(row):
    if row.interval is None:
        return "exploratory, interval unavailable"
    lower, upper = row.interval
    if lower > 0:
        return "exploratory, earns a fresh seed (above zero)"
    if upper < 0:
        return "exploratory, earns a fresh seed (below zero)"
    return "exploratory, interval includes zero"


def print_grades(matches, pool, verdict, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo must have the forecast sign and a magnitude within a factor of 1.5. "
          "A zero forecast requires zero. Replication forecasts use exact yes/no matching.\n")
    print("| Forecast | Guess | Observed | Grade | Evidence status |")
    print("|---|---:|---:|---|---|")
    grades = []
    for name in CANDIDATES:
        row = matches[name]
        grade = grade_elo(forecasts[name], row.elo)
        grades.append(grade)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(row.elo)} | {grade} | {match_status(row)} |")
    guess = forecasts["replicated"]
    grade = "ungraded" if verdict is None else "survives" if guess == verdict else "KILLED"
    grades.append(grade)
    print(f"| D12v3 REPLICATED | {yes_no(guess)} | {yes_no(verdict)} | {grade} | {match_status(pool)} |")
    print(f"\n{sum(v.startswith('KILLED') for v in grades)} KILLED, "
          f"{grades.count('survives')} survive, {grades.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table L. EvalSwingMult and EvalSwingMax paired-game results\n")
    print("W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial "
          "Elo ± halfwidth convention. Each analyzed pair contains both colors.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Reading |")
    print("|---|---|---:|---|---|---|---|")
    for row in rows:
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        counts = ", ".join(map(str, row.penta)) or "n/a"
        reading = "two-seed D12v3 comparison" if row.name.startswith("D12v3") else exploratory_read(row)
        print(f"| {row.name} | {match_status(row)} | {game_count} | {wld} | {counts} | "
              f"{number(row.elo)} {interval(row.interval)} | {reading} |")


def verify_slots(matches):
    initial = matches["X400"], matches["X400t"]
    if all(match.match_start and match.match_end for match in initial):
        if max(match.match_start for match in initial) >= min(match.match_end for match in initial):
            raise ValueError("the two slots did not overlap")
    for first, second in (("X400", "X100"), ("X100", "X50"), ("X50", "D12v3b"),
                          ("D12v3b", "E24k"), ("X400t", "E12t")):
        ended, started = matches[first].match_end, matches[second].match_start
        if ended and started and started < ended:
            raise ValueError(f"{second} began before {first} ended in the same slot")


def opening_fens(path, pgn):
    if not path.is_file():
        return None
    groups = parse_games(path, pgn, exact_moves=False)
    tally_pairs(groups, exact_moves=False)  # Validate colors and exact opening tags in every complete pair.
    tags = [games[0].start for games in groups.values() if len(games) == 2]
    return len(tags), set(tags)


def print_openings(raw, prior13, prior14, prior15, pgn, matches):
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



def table(raw, prior13, prior14, prior15, pgn, forecasts):
    original = read_job15_match(prior15, "D12v3", pgn)
    matches = {name: read_match(raw, name, pgn) for name in CANDIDATES}
    verify_slots(matches)
    fresh = matches["D12v3b"]
    pooled = pool_seeds(original, fresh)
    verdict = replicated(fresh, pooled)
    print_grades(matches, pooled, verdict, forecasts)
    rows = [row for name in CANDIDATES
            for row in ((original, fresh, pooled) if name == "D12v3b" else (matches[name],))]
    print_table(rows)
    print("\nD12v3 (job 15 + D12v3b) gets a verdict by the rule of file 15: REPLICATED when its fresh seed "
          "alone gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % "
          "interval whose lower end is above 0. Every other cell is exploratory: no verdict, a row each; "
          "one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job "
          "before anything is said about it.")
    bound = pooled.interval[0] if pooled.interval is not None else None
    print(f"D12v3 REPLICATED: {yes_no(verdict)}. Fresh Elo {number(fresh.elo, digits=4)}, "
          f"pooled lower 95% bound {number(bound, digits=4)}. Evidence {match_status(pooled)}.")
    print_openings(raw, prior13, prior14, prior15, pgn, matches)


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
            for name in ("job13-raw", "job14-raw", "job15-raw", "prediction"):
                option.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, args.only_k)
    else:
        table(args.raw, args.job13_raw, args.job14_raw, args.job15_raw, pgn, read_prediction(args.prediction))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
