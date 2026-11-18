#!/usr/bin/env python3
"""Validate Job 13 paired matches, pool E and E2, and grade the forecast."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job12 in (HERE.parent / "job12", HERE.parent / "sol-job12"):
    if (job12 / "analyze_matches.py").is_file():
        sys.path.insert(0, str(job12))
        break
else:
    raise SystemExit("Job 12's analyze_matches.py is missing from adjacent job12 or sol-job12.")

from analyze_matches import (
    Match, REFUSAL, digest, grade_elo, interval, number, parse_games, penta_elo,
    pgn_module, read_match as read_job12_match, summarized_output, tally_pairs,
)

MATCHES = {
    "K2": (100, 7111, 20000, 20000, 4, None),
    "C2": (200, 7112, 10000, 20000, 4, None),
    "E2": (2000, 7113, 20000, 20000, 2, "3"),
    "E3k": (2000, 7114, 2000, 2000, 2, "3"),
    "E6": (1000, 7115, 20000, 20000, 2, "6"),
}
FORECAST_MATCHES = ("E2", "E3k", "E6")
ENGINE_SHA = "63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333"
BOOK_SHA = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
FASTCHESS_REVISION = "d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75"
ELO_UNIT = Fraction("173.89")


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


def penta_estimate(counts, deterministic=False):
    if sum(counts) < 2:
        return None
    if not deterministic and sum(count > 0 for count in counts) <= 1:
        return None
    measured = penta_elo(counts)
    return tuple(Fraction(str(value)) for value in measured) if measured is not None else None


def read_match(directory, name, pgn):
    meta, reason = read_meta(directory, name)
    if meta is None:
        return Match(name, "unavailable", note=reason)
    requested = MATCHES[name][0]
    groups = parse_games(directory / f"{name}.pgn", pgn, exact_moves=name == "K2")
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K2")
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
    elif name in ("K2", "C2"):
        raise ValueError(f"{name}: no printed pentanomial interval matches the PGN and pair counts")
    elif actual is None:
        result.note = "no usable paired interval"
    else:
        result.elo, result.width = actual
        result.note = "interval reconstructed from paired PGN counts; no matching printed interval"
    return result


def gates(raw, pgn, only_k):
    k = read_match(raw, "K2", pgn)
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0):
        raise ValueError(f"K2 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K2 PASS: 50/50 pairs with identical moves and 1–1 points.")
    if only_k:
        return
    c = read_match(raw, "C2", pgn)
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C2 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C2 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")


def pooled_seeds(original, repeat):
    name = "E + E2 pooled"
    if not original.games or not repeat.games:
        return Match(name, "unavailable", note="both seeds require completed pairs")
    if (original.provenance[0], original.provenance[2:]) != (repeat.provenance[0], repeat.provenance[2:]):
        raise ValueError("E and E2 disagree on engine, book or PC20 baseline provenance")
    finish = "complete" if original.status == repeat.status == "complete" else "partial"
    penta = tuple(a + b for a, b in zip(original.penta, repeat.penta, strict=True))
    pool = Match(
        name, finish, original.raw_games + repeat.raw_games, original.games + repeat.games,
        original.wins + repeat.wins, original.losses + repeat.losses, original.draws + repeat.draws, penta,
        abnormal=original.abnormal + repeat.abnormal, note="interval reconstructed from summed penta counts",
    )
    if (sum((pool.wins, pool.losses, pool.draws)) != pool.games
            or 2 * sum(pool.penta) != pool.games
            or 2 * pool.wins + pool.draws != sum(index * count for index, count in enumerate(pool.penta))):
        raise ValueError("pooled W-L-D and pentanomial counts disagree on games or points")
    actual = penta_estimate(pool.penta)
    if actual:
        pool.elo, pool.width = actual
    else:
        pool.note = "no usable combined paired interval"
    return pool


def excludes_zero(row):
    if row.interval is None:
        return None
    low, high = row.interval
    return low > 0 or high < 0


def read_prediction(path):
    forecast = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in (*FORECAST_MATCHES, "pooled_excludes_zero"):
            continue
        if len(fields) != 2 or fields[0] in forecast:
            raise ValueError(f"{path}: expected one value per forecast line")
        name, value = fields
        if name == "pooled_excludes_zero":
            if value.lower() not in ("yes", "no"):
                raise ValueError(f"{path}: pooled interval forecast must be yes or no")
            forecast[name] = value.lower() == "yes"
        else:
            forecast[name] = Fraction(0) if value == "zero" else Fraction(value)
    if forecast.keys() != {*FORECAST_MATCHES, "pooled_excludes_zero"}:
        raise ValueError(f"{path}: expected E2, E3k, E6 and pooled_excludes_zero forecasts")
    return forecast


def yes_no(flag):
    return "n/a" if flag is None else "yes" if flag else "no"


def table(raw, old_raw, pgn, forecast):
    original = read_job12_match(old_raw, "E", pgn)
    matches = {name: read_match(raw, name, pgn) for name in FORECAST_MATCHES}
    repeat, soft, large = (matches[name] for name in FORECAST_MATCHES)
    if repeat.match_start and repeat.match_end and soft.match_start and soft.match_end:
        if max(repeat.match_start, soft.match_start) >= min(repeat.match_end, soft.match_end):
            raise ValueError("E2 and E3k did not play concurrently")
    if soft.match_end and large.match_start and large.match_start < soft.match_end:
        raise ValueError("E6 started before the E3k match in its slot ended")
    pool = pooled_seeds(original, repeat)
    flag = excludes_zero(pool)
    print("\n## Prediction grades\n")
    print("| Forecast | Guess | Observed | Grade |")
    print("|---|---:|---:|---|")
    verdicts = []
    for name in FORECAST_MATCHES:
        observed = matches[name].elo
        verdict = grade_elo(forecast[name], observed)
        verdicts.append(verdict)
        print(f"| {name} Elo | {number(forecast[name])} | {number(observed)} | {verdict} |")
    expected = forecast["pooled_excludes_zero"]
    verdict = "ungraded" if flag is None else "survives" if flag == expected else "KILLED"
    verdicts.append(verdict)
    print(f"| Pooled interval excludes zero | {yes_no(expected)} | {yes_no(flag)} | {verdict} |")
    print(f"\n{sum(v.startswith('KILLED') for v in verdicts)} KILLED, "
          f"{verdicts.count('survives')} survive, {verdicts.count('ungraded')} ungraded.\n")
    print("## Table H. EvalSwingMult paired-game results\n")
    print("W-L-D is from A's perspective. Displayed 95% intervals use the fastchess pentanomial "
          "Elo ± halfwidth convention. A completed pair supplies both games.\n")
    print("| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Elo / 173.89 |")
    print("|---|---|---:|---|---|---|---:|")
    for row in (original, repeat, pool, soft, large):
        note = f"{row.status}: {row.note}" if row.note else row.status
        if row.raw_games > row.games:
            note += f" ({row.raw_games - row.games} unpaired excluded)"
        note = note.replace("|", "&#124;").replace("\n", " ")
        game_count = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        counts = ", ".join(map(str, row.penta)) or "n/a"
        normalized = row.elo / ELO_UNIT if row.elo is not None else None
        print(f"| {row.name} | {note} | {game_count} | {wld} | {counts} | "
              f"{number(row.elo)} {interval(row.interval)} | {number(normalized, digits=4)} |")
    print(f"\nPooled interval excludes zero: {yes_no(flag)}.")


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
            sub.add_argument("--job12-raw", type=Path, required=True)
            sub.add_argument("--prediction", type=Path, required=True)
    args = parser.parse_args()
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, args.only_k)
    else:
        table(args.raw, args.job12_raw, pgn, read_prediction(args.prediction))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
