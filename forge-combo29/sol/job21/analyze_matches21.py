#!/usr/bin/env python3
"""Audit Job 21 paired PGNs, whole-pair seed pools, and exact opening overlap."""

import argparse
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job20 in (HERE.parent / "job20", HERE.parent / "sol-job20"):
    if (job20 / "analyze_matches20.py").is_file():
        sys.path.insert(0, str(job20))
        break
else:
    raise SystemExit("Job 20's analyze_matches20.py is missing from adjacent job20 or sol-job20.")

from analyze_matches20 import (
    BOOK_SHA, CANDIDATES as PRIOR20, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, check_match_preflight, digest, exploratory_read, grade_elo,
    identical_moves, interval, match_status, number, opening_fens, parse_games,
    penta_estimate, pgn_module, read_match as read_job20_match, read_pca_sha as read_pca_receipt,
    read_job19_match, replicated, summarized_output, tally_pairs, yes_no,
)
from analyze_matches17 import replicated_loss

PCA_SHA = "49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a"
MATCHES = {
    # games, seed, nodes A, nodes B, workers, A Mult/FHB, B Mult/FHB, candidate variant
    "K10": (100, 7211, 2000, 2000, 4, ("0", "3"), ("0", "3"), None),
    "C10": (200, 7212, 10000, 20000, 4, ("0", "0"), ("0", "0"), None),
    "E64tr2": (2000, 7213, 10000, 10000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
    "F7kr": (2000, 7214, 2000, 2000, 2, ("0", "7"), ("0", "0"), ("FailHighBlend", "7")),
    "F3k": (2000, 7215, 2000, 2000, 2, ("0", "3"), ("0", "0"), ("FailHighBlend", "3")),
    "F1k": (2000, 7216, 2000, 2000, 2, ("0", "1"), ("0", "0"), ("FailHighBlend", "1")),
    "E64w": (2000, 7217, 20000, 20000, 2, ("64", None), ("0", None), ("EvalSwingMult", "64")),
}
CONTROLS = ("K10", "C10")
SLOTS = (("E64tr2", "F7kr", "F3k", "F1k"), ("E64w",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**{job: names for job, names in PRIOR_JOBS.items() if job >= 17}, 20: PRIOR20}


def read_pca_sha(path):
    receipt = read_pca_receipt(path)
    if receipt != PCA_SHA:
        raise ValueError(f"{path}: PCA SHA-256 differs from Job 20")
    return receipt


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
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K10")
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
    k_result = read_match(raw, "K10", pgn, pca_sha)
    k, same, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K10 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K10 PASS: A and B both accepted explicit EvalSwingMult 0 and FailHighBlend 3 on PCA, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K10": k_result}
    c_result = read_match(raw, "C10", pgn, pca_sha)
    c, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C10 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C10 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K10": k_result, "C10": c_result}


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
        raise ValueError(f"{path}: expected five signed Elo forecasts")
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


def verify_prior_cut(raw, match):
    if match.status == "complete" or not match.games:
        return
    meta = json.loads((raw / f"{match.name}.meta").read_text(encoding="utf-8"))
    if match.status != "interrupted" or meta.get("stop_signal") != "SIGINT":
        raise ValueError(f"{match.name}: historical seed lacks an eligible cutoff status")
    report = raw.parent / "stamps.txt"
    if report.is_file():
        cutoffs = [line.split()[0] for line in report.read_text(encoding="utf-8").splitlines()
                   if line.endswith("scheduled minute-50 play cutoff")]
        if len(cutoffs) != 1:
            raise ValueError(f"{report}: expected one minute-50 cutoff timestamp")
        cutoff = datetime.fromisoformat(cutoffs[0])
    else:
        _, epoch = (raw.parent / "claim.commit").read_text(encoding="utf-8").split()
        cutoff = datetime.fromtimestamp(int(epoch), UTC) + timedelta(minutes=50)
    log = raw.parent / "slot-runs.txt"
    if not log.is_file():
        log = raw.parent / "run-measured.log"
    lines = log.read_text(encoding="utf-8").splitlines()
    marker = "Minute-50 cutoff reached. Sending SIGINT to active matches."
    if (marker not in lines or f"{match.name}: interrupted" not in lines[lines.index(marker) + 1:]
            or not datetime.fromisoformat(match.match_start) < cutoff <= datetime.fromisoformat(match.match_end)):
        raise ValueError(f"{match.name}: timestamps and slot log do not corroborate a clock-only cut")
    print(f"{match.name}: minute-50 cut verified at {cutoff.isoformat()}, {match.games} paired games eligible.")


def pool_results(seeds):
    matches = [row for row, _, _ in seeds]
    name = " + ".join(row.name for row in matches) + " pooled"
    if any(not row.games for row in matches):
        return Match(name, "unavailable", note="every seed requires completed pairs"), None
    if any(row.provenance != matches[0].provenance for row in matches[1:]):
        raise ValueError(f"{name}: executable, fastchess, book or B-side settings differ")
    cut = [f"{row.name} incomplete, {row.games} paired games included" for row in matches if row.status != "complete"]
    note = ". ".join(["interval reconstructed from summed pentanomial counts", *cut])
    penta = tuple(map(sum, zip(*(row.penta for row in matches), strict=True)))
    pooled = Match(
        name, "partial" if cut else "complete",
        *(sum(getattr(row, field) for row in matches)
          for field in ("raw_games", "games", "wins", "losses", "draws")),
        penta, abnormal=sum(row.abnormal for row in matches), note=note,
        provenance=matches[0].provenance,
    )
    if (pooled.wins + pooled.losses + pooled.draws != pooled.games
            or 2 * sum(penta) != pooled.games
            or 2 * pooled.wins + pooled.draws != sum(index * count for index, count in enumerate(penta))):
        raise ValueError(f"{name}: pooled wins, losses, draws and pentanomial bins disagree")
    if estimate := penta_estimate(penta):
        pooled.elo, pooled.width = estimate
    return pooled, sum(same for _, same, _ in seeds)


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
            dose = MATCHES[row.name][5][1] if row.name in MATCHES else "7"
            build = f"PCA, 2,000, FailHighBlend {dose}/0 and EvalSwingMult 0/0"
        else:
            budget = "20,000" if row.name == "E64w" else "10,000"
            build = f"Job 4, {budget}, EvalSwingMult 64/0"
        reading = (exploratory_read(row) if row.name in ("F3k", "F1k", "E64w") else
                   "three-seed gain comparison" if row.name.startswith("E") else "two-seed loss comparison")
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


def print_openings(results, prior_dirs, pgn, old_results):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings.\n")
    verified = {**results, **old_results}
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

    candidates = ("Job 19 E64t", "Job 20 E64tr", "E64tr2")
    for left, right in (*combinations(candidates, 2), ("Job 20 F7k", "F7kr")):
        print(f"{label(left)} and {label(right)} distinct shared exact FENs = {share(left, right)}.")
    print()
    print("| File | Status | Complete pairs | Distinct exact FENs |")
    print("|---|---|---:|---:|")
    for name, entry in all_files.items():
        status = (match_status(verified[name][0]) if name in verified
                  else "saved" if entry is not None else "missing PGN")
        pairs, distinct = (entry[0], len(entry[1])) if entry is not None else ("n/a", "n/a")
        print(f"| {name} | {status} | {pairs} | {distinct} |")

    scopes = (
        ("Within Job 21", combinations(current, 2)),
        ("Job 21 against Jobs 17–20", product(current, historical)),
    )
    for heading, pairs in scopes:
        print(f"\n### {heading}\n")
        print("| File A | File B | Shared exact FENs |")
        print("|---|---|---:|")
        for left, right in pairs:
            print(f"| {label(left)} | {label(right)} | {share(left, right)} |")


def table(raw, prior_dirs, pgn, forecasts, pca_sha):
    results = gates(raw, pgn, pca_sha)
    old_results = {
        "Job 19 E64t": read_job19_match(prior_dirs[19], "E64t", pgn),
        "Job 20 E64tr": read_job20_match(prior_dirs[20], "E64tr", pgn, pca_sha),
        "Job 20 F7k": read_job20_match(prior_dirs[20], "F7k", pgn, pca_sha),
    }
    results.update((name, read_match(raw, name, pgn, pca_sha)) for name in CANDIDATES)
    verify_slots(results)
    rows = [results[name][:2] for name in CANDIDATES]
    rows.extend(value[:2] for value in old_results.values())
    decisions = {}
    for name, fresh, history, check, side in (
        ("E64t", "E64tr2", ((19, "E64t"), (20, "E64tr")), replicated, "lower"),
        ("F7k", "F7kr", ((20, "F7k"),), replicated_loss, "upper"),
    ):
        fresh_row = results[fresh][0]
        if fresh_row.status != "complete":
            decisions[name] = f"{name} verdict withheld. {fresh} {match_status(fresh_row)}."
            continue
        seeds = []
        for job, prior in history:
            seed = old_results[f"Job {job} {prior}"]
            verify_prior_cut(prior_dirs[job], seed[0])
            seeds.append(seed)
        pooled = pool_results([*seeds, results[fresh]])
        rows.append(pooled)
        row = pooled[0]
        verdict = check(fresh_row, row)
        bound_index = 0 if side == "lower" else 1
        bound = row.interval[bound_index] if row.interval is not None else None
        decisions[name] = (f"{name} REPLICATED {yes_no(verdict)}. Fresh Elo {number(fresh_row.elo, digits=4)}, "
                           f"pooled {side} 95% bound {number(bound, digits=4)}. Evidence {match_status(row)}.")
    print_grades(results, forecasts)
    print_table(rows)
    print_openings(results, prior_dirs, pgn, old_results)
    print("\n## Declared verdicts\n")
    print("E64tr2, only if complete, gives E64t its verdict: REPLICATED when E64tr2 alone gives Elo above 0 AND "
          "the pool of E64t, E64tr and E64tr2 (pentanomial counts added; all three were cut only by the clock or "
          "are complete) has a 95 % interval whose lower end is above 0. A cut E64tr2 gives no verdict.")
    print(decisions["E64t"])
    print("\nF7kr, only if complete, gives F7k its verdict: REPLICATED (a loss) when F7kr alone gives Elo below 0 "
          "AND the pool of F7k and F7kr has a 95 % interval whose upper end is below 0.")
    print(decisions["F7k"])
    print("\nF3k, F1k and E64w are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above "
          "or wholly below 0 earns a fresh seed in a later job before anything is said about it.")


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
