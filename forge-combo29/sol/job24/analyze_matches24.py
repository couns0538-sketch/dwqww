#!/usr/bin/env python3
"""Audit Job 24 PGNs, move divergences, and exact opening overlap."""

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations, product, zip_longest
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
for job23 in (HERE.parent / "job23", HERE.parent / "sol-job23"):
    if (job23 / "analyze_matches23.py").is_file():
        sys.path.insert(0, str(job23))
        break
else:
    raise SystemExit("Job 23's analyze_matches23.py is missing from adjacent job23 or sol-job23.")

from analyze_matches23 import (
    BOOK_SHA, CANDIDATES as PRIOR23, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, digest, exploratory_read, historical_openings, identical_moves,
    interval, markdown_rows, match_status, number, parse_games, penta_estimate,
    pgn_module, section_lines, summarized_output, tally_pairs,
)
from analyze_matches16 import REFUSAL

MATCHES = {
    # games, seed, nodes A, nodes B, workers, explicit appended options for A/B
    "K13": (100, 7241, 2000, 2000, 4, (), ()),
    "C13": (200, 7242, 10000, 20000, 4, (), ()),
    "L1": (1000, 7243, 2000, 2000, 2, (("HistoryPruneDepth", "0"), ("HistoryPruneMultiplier", "2220")),
           (("HistoryPruneDepth", "3"), ("HistoryPruneMultiplier", "20000"))),
    "L2": (1000, 7244, 2000, 2000, 2, (("NullMoveBase", "6"), ("NullMoveDepthDivisor", "3")),
           (("NullMoveBase", "5"), ("NullMoveDepthDivisor", "1"))),
    "D2": (2000, 7245, 2000, 2000, 2, (("DrawJitter", "8"),), (("DrawJitter", "0"),)),
    "H2k": (2000, 7246, 2000, 2000, 2, (("HistoryPruneDepth", "0"), ("HistoryPruneMultiplier", "2220")),
            (("HistoryPruneDepth", "3"), ("HistoryPruneMultiplier", "2220"))),
    "H20": (1600, 7247, 20000, 20000, 2, (("HistoryPruneDepth", "0"), ("HistoryPruneMultiplier", "2220")),
            (("HistoryPruneDepth", "3"), ("HistoryPruneMultiplier", "2220"))),
}
CONTROLS = ("K13", "C13")
LOOKALIKES = ("L1", "L2")
SLOTS = (("L1", "L2", "D2", "H2k"), ("H20",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**PRIOR_JOBS, 23: PRIOR23}


def check_match_preflight(data, a_options, b_options):
    from run_match16 import BASE

    command = data["fastchess_command"]
    sections = [i for i, arg in enumerate(command) if arg == "-engine"]
    if len(sections) != 2 or command.count("-each") != 1:
        raise ValueError("fastchess argv is missing expected engine sections")
    for side, suffix, options, start, end in (
        ("A", "", a_options, sections[0], sections[1]),
        ("B", "_b", b_options, sections[1], command.index("-each")),
    ):
        settings = [f"setoption name {key} value {value}" for key, value in (*BASE, *options)]
        reply = data[f"preflight_reply{suffix}"]
        uci = data[f"preflight_uci{suffix}"]
        if (data[f"settings_{side.lower()}"] != settings or data[f"preflight_settings_sent{suffix}"] != settings
                or reply[-1:] != ["readyok"] or uci[-1:] != ["uciok"]
                or any(REFUSAL.search(line) for line in (*uci, *reply))):
            raise ValueError(f"engine {side}: literal PC20 or explicit options did not receive a clean acknowledgement")
        args = command[start + 1:end]
        expected = [f"option.{key}={value}" for key, value in (*BASE, *options)]
        if (f"name={side}" not in args or f"cmd={data['exe']}" not in args
                or [arg for arg in args if arg.startswith("option.")] != expected):
            raise ValueError(f"engine {side}: fastchess argv options differ from preflight")


def read_meta(directory, name):
    path = directory / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        if any(file.is_file() and file.stat().st_size for file in
               (directory / f"{name}.pgn", directory / f"{name}.out")):
            return None, "incomplete", "raw output exists without a final sidecar"
        return None, "not played", "no final match sidecar"
    data = json.loads(path.read_text(encoding="utf-8"))
    games, seed, nodes_a, nodes_b, workers, a_options, b_options = MATCHES[name]
    changed = next(({"name": key, "value": value} for key, value in a_options
                    if dict(b_options).get(key) != value), None)
    expected = (name, games, seed, nodes_a, nodes_b, workers, "A", "B", changed, 300)
    keys = ("match", "games_requested", "seed", "nodes_a", "nodes_b", "concurrency",
            "engine_a", "engine_b", "variant", "maxmoves")
    if tuple(data.get(key) for key in keys) != expected:
        raise ValueError(f"{path}: wrong match identity, budget or number of workers")
    if (data["exe_sha256"], data["book_sha256"], data["fastchess_revision"]) != (
        ENGINE_SHA, BOOK_SHA, FASTCHESS_REVISION,
    ):
        raise ValueError(f"{path}: wrong executable, book or fastchess provenance")
    if data["status"] == "refused":
        return None, "refused", data.get("error", "option refusal")
    if not data.get("pgn_sha256") or not data.get("out_sha256"):
        return None, data["status"], data.get("error", "PGN or fastchess output missing")
    if data["status"] == "complete" and data.get("fastchess_exit") != 0:
        raise ValueError(f"{path}: complete match has nonzero fastchess exit")
    for suffix in ("pgn", "out"):
        file = directory / f"{name}.{suffix}"
        if digest(file) != data[f"{suffix}_sha256"]:
            raise ValueError(f"{file}: SHA-256 differs from sidecar")
    try:
        check_match_preflight(data, a_options, b_options)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error
    return data, data["status"], ""


def read_match(raw, name, pgn):
    meta, status, reason = read_meta(raw, name)
    if meta is None:
        return Match(name, status, note=reason), None, None, None
    requested = MATCHES[name][0]
    groups = parse_games(raw / f"{name}.pgn", pgn, exact_moves=True)
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K13")
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
    return row, identical_moves(groups), fens, groups if name in LOOKALIKES else None


def gates(raw, pgn, only_k=False):
    k_result = read_match(raw, "K13", pgn)
    k, same, _, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K13 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K13 PASS: A and B both accepted the identical PC20 settings on the Job 4 executable, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K13": k_result}
    c_result = read_match(raw, "C13", pgn)
    c, _, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C13 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C13 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K13": k_result, "C13": c_result}


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in CANDIDATES:
            continue
        name = fields[0]
        if name in LOOKALIKES:
            if len(fields) != 3 or name in forecasts:
                raise ValueError(f"{path}: expected name and integer same-pair bounds for {name}")
            low, high = map(int, fields[1:])
            if not 0 <= low <= high <= MATCHES[name][0] // 2:
                raise ValueError(f"{path}: {name} interval must be within 0–500 pairs")
            forecasts[name] = low, high
        else:
            if len(fields) != 4 or name in forecasts:
                raise ValueError(f"{path}: expected name, signed Elo, low and high for {name}")
            point, low, high = map(Fraction, fields[1:])
            if not low <= point <= high:
                raise ValueError(f"{path}: range for {name} must contain its point forecast")
            forecasts[name] = point, low, high
    if forecasts.keys() != set(CANDIDATES):
        raise ValueError(f"{path}: expected two exact-move count ranges and three signed Elo ranges")
    return forecasts


def result_status(row):
    if row.status in ("refused", "not played"):
        note = row.note.replace("|", "&#124;").replace("\n", " ")
        return f"{row.status}: {note}" if note else row.status
    return match_status(row)


def print_grades(results, forecasts):
    print("\n## Prediction grades\n")
    print("Same-move count ranges apply to all 500 planned pairs in L1 and L2. A cut pair-count forecast is ungraded. "
          "For Elo forecasts, the observed sign and inclusive range are checked separately.\n")
    print("| Match | Same-pair forecast | Observed same / played | Range | Status |")
    print("|---|---|---:|---|---|")
    for name in LOOKALIKES:
        row, same, _, _ = results[name]
        low, high = forecasts[name]
        observed = f"{same}/{row.games // 2}" if same is not None else "n/a"
        grade = "ungraded" if row.status != "complete" else "met" if low <= same <= high else "missed"
        print(f"| {name} | [{low}, {high}] | {observed} | {grade} | {result_status(row)} |")
    print("\n| Match | Elo forecast | Predicted range | Observed | Sign | Range | Overall | Evidence status |")
    print("|---|---:|---|---:|---|---|---|---|")
    for name in CANDIDATES:
        if name in LOOKALIKES:
            continue
        point, low, high = forecasts[name]
        row = results[name][0]
        if row.elo is None:
            sign = range_grade = overall = "ungraded"
        else:
            signed = (point > 0) == (row.elo > 0) and (point < 0) == (row.elo < 0)
            covered = low <= row.elo <= high
            sign = "met" if signed else "missed"
            range_grade = "met" if covered else "missed"
            overall = "survives" if signed and covered else "KILLED"
        print(f"| {name} | {number(point)} | {interval((low, high))} | {number(row.elo)} | "
              f"{sign} | {range_grade} | {overall} | {result_status(row)} |")


def print_table_p(results):
    print("\n## Table P. Job 24 paired games\n")
    print("All rows use the Job 4 executable, PC20, embedded evaluation, Threads 1, Hash 16 and the pinned book. "
          "W-L-D is from A's perspective. Identical pairs share the complete ordered UCI move sequence.\n")
    print("| Match | Nodes per move | Explicit options A/B | Status | Games | W-L-D | Pentanomial | "
          "Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---:|---|---|---:|---|---|---|---:|---|")
    for name in CANDIDATES:
        row, same, _, _ = results[name]
        _, _, nodes, _, _, aside, bside = MATCHES[name]
        options = ", ".join(f"{option} {a}/{b}" for (option, a), (_, b) in zip(aside, bside, strict=True))
        games = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        reading = "move-sequence comparison" if name in LOOKALIKES else exploratory_read(row)
        print(f"| {name} | {nodes:,} | {options} | {result_status(row)} | {games} | {wld} | {penta} | "
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


def first_difference(first, second, chess):
    if first.start != second.start:
        raise ValueError(f"round {first.round}: different openings in same pair")
    board = chess.Board() if first.start == "startpos" else chess.Board(first.start)
    for ply, (move_a, move_b) in enumerate(zip_longest(first.moves, second.moves), 1):
        if move_a != move_b:
            active = (first.white, second.white) if board.turn == chess.WHITE else (first.black, second.black)
            return ply, board.fen(en_passant="fen"), move_a or "ended", active[0], move_b or "ended", active[1]
        board.push_uci(move_a)
    return None


def print_table_l(results):
    import chess

    print("\n## Table L. First move differences in reversed-color pairs\n")
    print("Game 1 and game 2 follow PGN file order within each round. Ply 1 is the first move from the opening FEN. "
          "The listed engine is the side on move in that game at the shared position. The ended marker means "
          "that game's move list stops at the shared position.\n")
    print("| Match | Status | Identical pairs | Complete pairs | Differing pairs |")
    print("|---|---|---:|---:|---:|")
    differing = {}
    for name in LOOKALIKES:
        row, same, _, matching = results[name]
        if matching is None:
            print(f"| {name} | {result_status(row)} | n/a | n/a | n/a |")
            differing[name] = []
            continue
        differences = []
        for round_, pair in sorted(matching.items()):
            if len(pair) == 2 and (diff := first_difference(*pair, chess)) is not None:
                differences.append((round_, diff))
        if same + len(differences) != row.games // 2:
            raise ValueError(f"{name}: Table L did not account for every complete pair")
        differing[name] = differences
        print(f"| {name} | {result_status(row)} | {same} | {row.games // 2} | {len(differences)} |")

    print("\n| Match | Round | Ply | Exact pre-move FEN | Game 1 move | Game 1 engine | Game 2 move | Game 2 engine |")
    print("|---|---:|---:|---|---|---|---|---|")
    for name, rows in differing.items():
        label = name if results[name][0].status == "complete" else f"{name} (incomplete)"
        for round_, (ply, fen, move_a, side_a, move_b, side_b) in rows:
            print(f"| {label} | {round_} | {ply} | `{fen}` | {move_a} | {side_a} | {move_b} | {side_b} |")
    if not any(differing.values()):
        print("\nNo differing complete pair was observed.")


THREEFOLD = re.compile(r"\b(?:3[- ]?fold|three[- ]?fold) repetition\b", re.IGNORECASE)


def threefold_draws(path, pgn, row):
    records = defaultdict(list)
    with path.open(encoding="utf-8") as stream:
        while (game := pgn.read_game(stream)) is not None:
            if game.errors:
                raise ValueError(f"{path}: PGN parse errors: {game.errors}")
            draw = game.headers["Result"] == "1/2-1/2"
            markers = (game.headers.get("Termination", ""), game.end().comment)
            repeated = any(THREEFOLD.search(value) for value in markers)
            if repeated and not draw:
                raise ValueError(f"{path}: threefold termination marked on a non-draw in round {game.headers['Round']}")
            records[int(game.headers["Round"])].append((draw, repeated))
    paired = [game for group in records.values() if len(group) == 2 for game in group]
    if len(paired) != row.games or sum(draw for draw, _ in paired) != row.draws:
        raise ValueError(f"{path}: repetition recount disagrees with paired totals")
    return sum(repeated for _, repeated in paired)


def print_d2(raw, pgn, row):
    print("\n## D2 draw terminations\n")
    if not row.games:
        print(f"D2 {result_status(row)}. No completed pair is available.")
        return
    repeated = threefold_draws(raw / "D2.pgn", pgn, row)
    print("D2 uses Job 4, PC20, built-in evaluation, Threads 1, Hash 16, 2,000 nodes per move, "
          "and DrawJitter 8 for A and 0 for B. The count uses the saved termination tag or final move comment.\n")
    print("| Match | Status | Paired games | Draws | Threefold repetition draws |")
    print("|---|---|---:|---:|---:|")
    print(f"| D2 | {result_status(row)} | {row.games} | {row.draws} | {repeated} |")


WITHIN_HEADING = "### Within Job 24"
HISTORICAL_HEADING = "### Job 24 against Jobs 17–23"


def print_openings(results, prior_dirs, pgn):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings. The two tables cover every new-file pair and every new file against every prior measurement.\n")
    known = {
        name: (row.status, (row.games // 2, fens) if fens is not None else None)
        for name, (row, _, fens, _) in results.items()
    }
    historic = {}
    for job, names in PRIOR.items():
        for name in names:
            label = f"Job {job} {name}"
            historic[label] = historical_openings(prior_dirs[job], name, pgn)
    all_files = {**{name: known[name] for name in results}, **historic}

    def label(name):
        status, _ = all_files[name]
        return name if status == "complete" else f"{name} (incomplete)"

    def share(left, right):
        a, b = all_files[left][1], all_files[right][1]
        return len(a[1] & b[1]) if a is not None and b is not None else "n/a"

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


def audit_openings(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    historic = tuple(f"Job {job} {name}" for job, names in PRIOR.items() for name in names)
    if len(MATCHES) != 7 or len(historic) != 38 or "Job 20 F7k" not in historic:
        raise ValueError("opening scopes lost a scheduled file or historical cohort")
    inventory_rows = list(markdown_rows(
        section_lines(lines, "## Shared openings"), ("File", "Status", "Complete pairs", "Distinct exact FENs"),
    ))
    if Counter(record[0] for record in inventory_rows) != Counter((*MATCHES, *historic)):
        raise ValueError(f"{path}: opening inventory must contain each expected file exactly once")
    inventory = {name: (status, pairs) for name, status, pairs, _ in inventory_rows}
    for cut in ("Job 19 E64t", "Job 20 E64tr"):
        if not inventory[cut][0].startswith("incomplete"):
            raise ValueError(f"{path}: opening inventory lost the cut status for {cut}")

    def label(name):
        return f"{name} (incomplete)" if inventory[name][0].startswith("incomplete") else name

    for heading, pairs in ((WITHIN_HEADING, combinations(MATCHES, 2)),
                           (HISTORICAL_HEADING, product(MATCHES, historic))):
        expected = {
            (label(left), label(right)): "n/a" in (inventory[left][1], inventory[right][1])
            for left, right in pairs
        }
        rows = list(markdown_rows(section_lines(lines, heading), ("File A", "File B", "Shared exact FENs")))
        if Counter((left, right) for left, right, _ in rows) != Counter(expected.keys()):
            raise ValueError(f"{path}: {heading} has missing, duplicate or mislabeled pair rows")
        for left, right, count in rows:
            valid = count == "n/a" if expected[left, right] else count.isdecimal()
            if not valid:
                raise ValueError(f"{path}: invalid shared FEN count for {left} and {right}")
        print(f"{heading.removeprefix('### ')} verified: {len(rows)} comparisons, one per required file pair.")




def table(raw, prior_dirs, pgn, forecasts):
    results = gates(raw, pgn)
    results.update((name, read_match(raw, name, pgn)) for name in CANDIDATES)
    verify_slots(results)
    print_grades(results, forecasts)
    print_table_p(results)
    print_openings(results, prior_dirs, pgn)
    print_table_l(results)
    print_d2(raw, pgn, results["D2"][0])
    print("\n## What this check cannot see\n")
    print("The PC's own net (its engine plays with a net, your tree with the built-in evaluation), its compiler "
          "and processor; more than one search thread; time controls other than fixed nodes.")


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
    audit = modes.add_parser("audit-openings")
    audit.add_argument("report", type=Path)
    args = parser.parse_args()
    if args.mode == "audit-openings":
        audit_openings(args.report)
        return
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
