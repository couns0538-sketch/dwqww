#!/usr/bin/env python3
"""Audit Job 14 paired games and apply the declared two-seed replication rule."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job13 in (HERE.parent / "job13", HERE.parent / "sol-job13"):
    if (job13 / "analyze_matches13.py").is_file():
        sys.path.insert(0, str(job13))
        break
else:
    raise SystemExit("Job 13's analyze_matches13.py is missing from adjacent job13 or sol-job13.")

from analyze_matches13 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, Match, REFUSAL, digest, grade_elo, interval,
    number, parse_games, penta_estimate, pgn_module, read_match as read_job13_match,
    summarized_output, tally_pairs, yes_no,
)

MATCHES = {
    "K3": (100, 7121, 20000, 20000, 4, None),
    "C3": (200, 7122, 10000, 20000, 4, None),
    "E3k2": (2000, 7123, 2000, 2000, 2, "3"),
    "E6b": (2000, 7124, 20000, 20000, 2, "6"),
    "E6k": (2000, 7125, 2000, 2000, 2, "6"),
    "E12k": (2000, 7126, 2000, 2000, 2, "12"),
}
CANDIDATES = ("E3k2", "E6b", "E6k", "E12k")
REPLICATIONS = {"E3k": "E3k2", "E6": "E6b"}


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
    candidate = [*baseline, f"setoption name EvalSwingMult value {variant}"] if variant is not None else baseline
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
    groups = parse_games(directory / f"{name}.pgn", pgn, exact_moves=name == "K3")
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K3")
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
    elif name in ("K3", "C3"):
        raise ValueError(f"{name}: no printed pentanomial interval matches the PGN and pair counts")
    elif actual is None:
        result.note = "no usable paired interval"
    else:
        result.elo, result.width = actual
        result.note = "interval reconstructed from paired PGN counts; no matching printed interval"
    return result


def gates(raw, pgn, only_k):
    k = read_match(raw, "K3", pgn)
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0):
        raise ValueError(f"K3 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K3 PASS: 50/50 pairs with identical moves and 1–1 points.")
    if only_k:
        return
    c = read_match(raw, "C3", pgn)
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C3 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C3 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")



def pool_seeds(first, fresh):
    name = f"{first.name} + {fresh.name} pooled"
    if not first.games or not fresh.games:
        return Match(name, "unavailable", note="both seeds require completed pairs")
    if (first.provenance[0], first.provenance[2:]) != (fresh.provenance[0], fresh.provenance[2:]):
        raise ValueError(f"{name}: engine, book or PC20 provenance differs")
    end = "complete" if first.status == fresh.status == "complete" else "partial"
    bins = tuple(a + b for a, b in zip(first.penta, fresh.penta, strict=True))
    result = Match(
        name, end, first.raw_games + fresh.raw_games, first.games + fresh.games,
        first.wins + fresh.wins, first.losses + fresh.losses, first.draws + fresh.draws, bins,
        abnormal=first.abnormal + fresh.abnormal, note="interval reconstructed from summed penta counts",
    )
    if (result.wins + result.losses + result.draws != result.games
            or 2 * sum(bins) != result.games
            or 2 * result.wins + result.draws != sum(index * count for index, count in enumerate(bins))):
        raise ValueError(f"{name}: raw pooled counts disagree on games or points")
    if measured := penta_estimate(bins):
        result.elo, result.width = measured
    else:
        result.note = "no usable combined paired interval"
    return result


def replicated(fresh, pool):
    if fresh.elo is not None and fresh.elo <= 0:
        return False
    if pool.interval is not None and pool.interval[0] <= 0:
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
                raise ValueError(f"{path}: expected one signed Elo forecast for {name}")
            forecasts[name] = Fraction(0) if fields[1] == "zero" else Fraction(fields[1])
        if fields[0] == "replicated":
            if len(fields) != 3 or fields[1] not in REPLICATIONS or fields[2].lower() not in ("yes", "no"):
                raise ValueError(f"{path}: expected replicated E3k|E6 yes|no")
            key = "replicated", fields[1]
            if key in forecasts:
                raise ValueError(f"{path}: duplicate replication forecast")
            forecasts[key] = fields[2].lower() == "yes"
    expected = {*CANDIDATES, *(("replicated", name) for name in REPLICATIONS)}
    if forecasts.keys() != expected:
        raise ValueError(f"{path}: expected four signed Elo and two replication forecasts")
    return forecasts


def print_grades(matches, verdicts, forecasts):
    print("\n## Prediction grades\n")
    print("A nonzero Elo forecast requires the observed sign and a magnitude within a factor of 1.5. "
          "Zero requires zero. Replication forecasts are exact yes/no grades.\n")
    print("| Forecast | Guess | Observed | Grade |")
    print("|---|---:|---:|---|")
    results = []
    for name in CANDIDATES:
        observed = matches[name].elo
        verdict = grade_elo(forecasts[name], observed)
        results.append(verdict)
        print(f"| {name} Elo | {number(forecasts[name])} | {number(observed)} | {verdict} |")
    for name in REPLICATIONS:
        predicted, observed = forecasts["replicated", name], verdicts[name]
        verdict = "ungraded" if observed is None else "survives" if predicted == observed else "KILLED"
        results.append(verdict)
        print(f"| {name} REPLICATED | {yes_no(predicted)} | {yes_no(observed)} | {verdict} |")
    print(f"\n{sum(v.startswith('KILLED') for v in results)} KILLED, "
          f"{results.count('survives')} survive, {results.count('ungraded')} ungraded.\n")


def print_table(rows):
    print("## Table J. EvalSwingMult paired-game results\n")
    print("W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial "
          "Elo ± halfwidth convention. Each analyzed pair contains both colors.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] |")
    print("|---|---|---:|---|---|---|")
    for row in rows:
        status = f"{row.status}: {row.note}" if row.note else row.status
        if row.raw_games > row.games:
            status += f" ({row.raw_games - row.games} unpaired excluded)"
        status = status.replace("|", "&#124;").replace("\n", " ")
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        counts = ", ".join(map(str, row.penta)) or "n/a"
        print(f"| {row.name} | {status} | {game_count} | {wld} | {counts} | "
              f"{number(row.elo)} {interval(row.interval)} |")


def verify_slots(matches):
    same_time = matches["E6b"], matches["E3k2"]
    if all(match.match_start and match.match_end for match in same_time):
        if max(match.match_start for match in same_time) >= min(match.match_end for match in same_time):
            raise ValueError("the two slots did not overlap")
    for first, second in (("E3k2", "E6k"), ("E6k", "E12k")):
        ended, started = matches[first].match_end, matches[second].match_start
        if ended and started and started < ended:
            raise ValueError(f"{second} started before {first} finished in the same slot")


def table(raw, old_raw, pgn, forecasts):
    previous = {name: read_job13_match(old_raw, name, pgn) for name in REPLICATIONS}
    matches = {name: read_match(raw, name, pgn) for name in CANDIDATES}
    verify_slots(matches)
    pools = {name: pool_seeds(previous[name], matches[fresh]) for name, fresh in REPLICATIONS.items()}
    verdicts = {name: replicated(matches[fresh], pools[name]) for name, fresh in REPLICATIONS.items()}
    print_grades(matches, verdicts, forecasts)
    rows = [row for name, fresh in REPLICATIONS.items() for row in (previous[name], matches[fresh], pools[name])]
    print_table([*rows, matches["E6k"], matches["E12k"]])
    print("\nA cell is REPLICATED when its fresh seed alone gives Elo above 0 AND the pool "
          "of its two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. "
          "E6k and E12k are exploratory: no verdict, a row each.")
    for name, fresh in REPLICATIONS.items():
        bound = pools[name].interval[0] if pools[name].interval is not None else None
        print(f"{name} REPLICATED: {yes_no(verdicts[name])}. "
              f"Fresh Elo {number(matches[fresh].elo, digits=4)}, pooled lower 95% bound {number(bound, digits=4)}.")


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
            sub.add_argument("--job13-raw", type=Path, required=True)
            sub.add_argument("--prediction", type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, args.only_k)
    else:
        table(args.raw, args.job13_raw, pgn, read_prediction(args.prediction))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
