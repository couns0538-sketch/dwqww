#!/usr/bin/env python3
"""Audit Job 25 match gates, draw termination counts and D2r move divergences."""

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations, product, zip_longest
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for job24 in (HERE.parent / "job24", HERE.parent / "sol-job24"):
    if (job24 / "analyze_matches24.py").is_file():
        sys.path.insert(0, str(job24))
        break
else:
    raise SystemExit("Job 24's analyze_matches24.py is missing from adjacent job24 or sol-job24.")

from analyze_matches24 import (
    BOOK_SHA, CANDIDATES as PRIOR24, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, check_match_preflight, digest, exploratory_read, historical_openings,
    identical_moves, interval, markdown_rows, match_status, number, parse_games, penta_estimate,
    pgn_module, read_match as read_job24_match, result_status, section_lines,
    summarized_output, tally_pairs,
)
from analyze_matches21 import pool_results

MATCHES = {
    # games, seed, nodes A, nodes B, workers, explicit appended options for A/B
    "K14": (100, 7251, 2000, 2000, 4, (), ()),
    "C14": (200, 7252, 10000, 20000, 4, (), ()),
    "D2r": (4000, 7253, 2000, 2000, 2, (("DrawJitter", "8"),), (("DrawJitter", "0"),)),
    "D2q": (2000, 7254, 2000, 2000, 2, (("DrawJitter", "4"),), (("DrawJitter", "0"),)),
    "D2o": (2000, 7256, 2000, 2000, 2, (("DrawJitter", "1"),), (("DrawJitter", "0"),)),
    "D20": (1600, 7255, 20000, 20000, 2, (("DrawJitter", "8"),), (("DrawJitter", "0"),)),
}
CONTROLS = ("K14", "C14")
SLOTS = (("D2r", "D2q", "D2o"), ("D20",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**PRIOR_JOBS, 24: PRIOR24}
PAIR_FORECAST = "D2r_non_1_1"
DRAW_REASONS = (
    "Draw by 3-fold repetition",
    "Draw by fifty moves rule",
    "Draw by insufficient mating material",
    "Draw by stalemate",
)


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
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K14")
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
    return row, identical_moves(groups), fens, groups if name == "D2r" else None


def gates(raw, pgn, only_k=False):
    k_result = read_match(raw, "K14", pgn)
    k, same, _, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K14 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K14 PASS: A and B both accepted the identical PC20 settings on the Job 4 executable, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K14": k_result}
    c_result = read_match(raw, "C14", pgn)
    c, _, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C14 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C14 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K14": k_result, "C14": c_result}


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        name = fields[0]
        if name in CANDIDATES:
            if len(fields) != 4 or name in forecasts:
                raise ValueError(f"{path}: expected one {name} SIGNED_ELO LOWER UPPER forecast")
            point, low, high = map(Fraction, fields[1:])
            if not low <= point <= high:
                raise ValueError(f"{path}: the {name} forecast must lie within its range")
            forecasts[name] = point, low, high
        elif name == PAIR_FORECAST:
            if len(fields) != 2 or name in forecasts or not fields[1].isdigit():
                raise ValueError(f"{path}: expected one {PAIR_FORECAST} INTEGER forecast")
            count = int(fields[1])
            if count > MATCHES["D2r"][0] // 2:
                raise ValueError(f"{path}: {PAIR_FORECAST} cannot exceed 2,000 pairs")
            forecasts[name] = count
    if forecasts.keys() != {*CANDIDATES, PAIR_FORECAST}:
        raise ValueError(f"{path}: expected four signed Elo ranges and one D2r pair count")
    return forecasts


def non_even_pairs(row):
    return sum(row.penta) - row.penta[2] if row.penta else None


def print_grades(results, forecasts):
    print("\n## Prediction grades\n")
    print("The observed Elo sign and inclusive range are checked separately. The overall Elo forecast survives "
          "when both pass. A cut D2r leaves the full 2,000-pair forecast ungraded.\n")
    print("| Match | Elo forecast | Predicted range | Observed | Sign | Range | Overall | Evidence status |")
    print("|---|---:|---|---:|---|---|---|---|")
    for name in CANDIDATES:
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
    row = results["D2r"][0]
    measured = non_even_pairs(row)
    guess = forecasts[PAIR_FORECAST]
    grade = "ungraded" if row.status != "complete" else "met" if measured == guess else "missed"
    value = f"{measured}/{row.games // 2}" if measured is not None else "n/a"
    print("\n| Count forecast | Forecast | Observed non-1–1 / played | Exact match | Status |")
    print("|---|---:|---|---|---|")
    print(f"| D2r non-1–1 | {guess} | {value} | {grade} | {result_status(row)} |")


def print_table_p(rows):
    print("\n## Table P. Job 25 paired games\n")
    print("All rows use Job 4, PC20, embedded evaluation, Threads 1, Hash 16 and the pinned book. W-L-D is from A's "
          "perspective. Intervals use the fastchess symmetric 95% pentanomial Elo ± halfwidth convention. "
          "Only complete color-reversed pairs contribute.\n")
    print("| Match | Nodes per move | DrawJitter A/B | Status | Games | W-L-D | Pentanomial | "
          "Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---:|---|---|---:|---|---|---|---:|---|")
    for row, same in rows:
        if row.name in MATCHES:
            nodes = MATCHES[row.name][2]
            jitter = MATCHES[row.name][5][0][1]
        else:
            nodes, jitter = 2000, "8"
        games = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        if row.name == "D2r":
            reading = "fresh-seed decision"
        elif row.name == "D2":
            reading = "Job 24 first seed"
        elif row.name == "D2 + D2r pooled":
            reading = "descriptive pool, verdict uses D2r"
        else:
            reading = exploratory_read(row)
        print(f"| {row.name} | {nodes:,} | {jitter}/0 | {result_status(row)} | {games} | {wld} | {penta} | "
              f"{number(row.elo)} {interval(row.interval)} | {sequence} | {reading} |")


def d2_verdict(row):
    if row.status != "complete" or row.elo is None:
        return "NO VERDICT"
    if row.elo <= 0:
        return "NOT REPLICATED"
    if row.interval is None:
        return "NO VERDICT"
    return "REPLICATED (a gain)" if row.interval[0] > 0 else "OPEN"


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


def draw_terminations(path, pgn, row):
    records = defaultdict(list)
    with path.open(encoding="utf-8") as stream:
        while (game := pgn.read_game(stream)) is not None:
            if game.errors:
                raise ValueError(f"{path}: PGN parse errors: {game.errors}")
            result = game.headers["Result"]
            comment = game.end().comment.strip()
            reason = next((marker for marker in DRAW_REASONS if comment.endswith(marker)), None)
            draw = result == "1/2-1/2"
            if reason is not None and not draw:
                raise ValueError(f"{path}: draw termination on a non-draw in round {game.headers['Round']}")
            records[int(game.headers["Round"])].append((draw, reason))
    paired = [game for group in records.values() if len(group) == 2 for game in group]
    if len(paired) != row.games or sum(draw for draw, _ in paired) != row.draws:
        raise ValueError(f"{path}: draw termination recount disagrees with the paired games")
    return Counter(reason for draw, reason in paired if draw)


def print_table_d(raw, prior_raw, pgn, results, old):
    print("\n## Table D. Draw terminations\n")
    print("The counts use each PGN's last comment and retain complete pairs. Other includes all remaining draws, "
          "including comments without one of the four listed terminal reasons.\n")
    print("| Match | Status | Paired games | Draws | Threefold repetition | Fifty-move rule | "
          "Insufficient material | Stalemate | Other |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    sources = [("Job 24 D2", prior_raw / "D2.pgn", old[0])]
    sources.extend((name, raw / f"{name}.pgn", results[name][0]) for name in MATCHES)
    for label, path, row in sources:
        if not row.games:
            print(f"| {label} | {result_status(row)} | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        counts = draw_terminations(path, pgn, row)
        values = [counts[marker] for marker in DRAW_REASONS]
        print(f"| {label} | {result_status(row)} | {row.games} | {row.draws} | "
              f"{' | '.join(map(str, values))} | {counts[None]} |")


def position_key(board):
    """FIDE equality ignores clocks and distinguishes only a legal en-passant capture."""
    return (board.board_fen(), board.turn, board.clean_castling_rights(),
            board.ep_square if board.has_legal_en_passant() else None)


def divergence(first, second, chess):
    if first.start != second.start:
        raise ValueError(f"round {first.round}: different openings in same pair")
    board = chess.Board() if first.start == "startpos" else chess.Board(first.start)
    earlier = {position_key(board)}
    for ply, (left, right) in enumerate(zip_longest(first.moves, second.moves), 1):
        if left == right:
            board.push_uci(left)
            earlier.add(position_key(board))
            continue
        fen = board.fen(en_passant="fen")
        records = []
        for game, move in ((first, left), (second, right)):
            engine = game.white if board.turn == chess.WHITE else game.black
            if move is None:
                records.append(("ended", engine, "n/a"))
                continue
            board.push_uci(move)
            repeated = position_key(board) in earlier
            board.pop()
            records.append((move, engine, "yes" if repeated else "no"))
        return ply, fen, *records
    return None


def print_table_j(result):
    import chess

    row, _, _, groups = result
    print("\n## Table J. D2r pairs with an unequal score\n")
    print("D2r uses Job 4, PC20, built-in evaluation, Threads 1, Hash 16, 2,000 nodes and DrawJitter 8/0. "
          "Ply 1 is the first move from the supplied opening FEN, the first known position. Game order follows "
          "the PGN within its Round. Repeated means the position immediately after that move occurred earlier "
          "in the recorded game, with the same pieces, side to move, castling rights and legal en-passant "
          "availability. Clocks are ignored. The ended marker gives the side on move if play had continued.\n")
    if groups is None:
        print(f"D2r {result_status(row)}. No completed pairs are available.")
        return
    label = row.name if row.status == "complete" else f"{row.name} (incomplete)"
    print(f"{label} had {non_even_pairs(row)} non-1–1 scores in {row.games // 2} complete pairs.\n")
    print("| Match | Round | Score A–B | First divergent ply | Exact pre-move FEN | Game 1 move | Game 1 engine | "
          "Game 1 repeated | Game 2 move | Game 2 engine | Game 2 repeated |")
    print("|---|---:|---|---:|---|---|---|---|---|---|---|")
    found = 0
    for round_, games in sorted(groups.items()):
        if len(games) != 2:
            continue
        points = sum(game.points_a for game in games)
        if points == 2:
            continue
        found += 1
        score = f"{points / 2:g}–{2 - points / 2:g}"
        diff = divergence(*games, chess)
        if diff is None:
            print(f"| {label} | {round_} | {score} | none | n/a | identical move lists | n/a | n/a | "
                  "identical move lists | n/a | n/a |")
            continue
        ply, fen, left, right = diff
        print(f"| {label} | {round_} | {score} | {ply} | `{fen}` | "
              f"{' | '.join(left)} | {' | '.join(right)} |")
    if found != non_even_pairs(row):
        raise ValueError("Table J did not account for every complete unequal-score pair")
    if not found:
        print("\nEvery complete pair scored 1–1.")


WITHIN_HEADING = "### Within Job 25"
HISTORICAL_HEADING = "### Job 25 against Jobs 17–24"


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
    if len(MATCHES) != 6 or len(historic) != 43 or "Job 20 F7k" not in historic:
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
    old = read_job24_match(prior_dirs[24], "D2", pgn)
    if old[0].status != "complete":
        raise ValueError("the prior complete Job 24 D2 seed is unavailable")
    results.update((name, read_match(raw, name, pgn)) for name in CANDIDATES)
    verify_slots(results)
    fresh = results["D2r"]
    pooled = pool_results([old[:3], fresh[:3]])
    print_grades(results, forecasts)
    print_table_p([*(results[name][:2] for name in CANDIDATES), old[:2], pooled])
    print_openings(results, prior_dirs, pgn)
    print_table_d(raw, prior_dirs[24], pgn, results, old)
    print_table_j(fresh)

    fresh_row = fresh[0]
    print("\n## Declared verdict\n")
    print("D2r is the second seed of D2: REPLICATED (a gain) when D2r's 95 % interval lies wholly above 0; "
          "NOT REPLICATED when its point estimate is at or below 0; otherwise OPEN. "
          "The pool D2 + D2r (counts added) is a row, not a verdict.")
    print("D2q, D2o and D20 are exploratory, one seed each: no verdict, a row each; one whose 95 % interval "
          "lies wholly above or below 0 earns a fresh seed in a later job.")
    print("A cut match gives no verdict.\n")
    print(f"D2r verdict: {d2_verdict(fresh_row)}. Fresh Elo {number(fresh_row.elo, digits=4)}, "
          f"95% interval {interval(fresh_row.interval, digits=4)}, {result_status(fresh_row)}.")
    print("\n## What this check cannot see\n")
    print("The PC's own net (its engine plays with a net, your tree with the built-in evaluation), its compiler "
          "and processor; more than one search thread; time controls other than fixed nodes; "
          "the soft node limit of the PC's self-play.")


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
