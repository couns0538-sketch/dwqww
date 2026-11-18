#!/usr/bin/env python3
"""Audit Job 26 fresh openings, paired PGNs and interval calibration."""

import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import combinations, product
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
for job25 in (HERE.parent / "job25", HERE.parent / "sol-job25"):
    if (job25 / "analyze_matches25.py").is_file():
        sys.path.insert(0, str(job25))
        break
else:
    raise SystemExit("Job 25's analyze_matches25.py is missing from adjacent job25 or sol-job25.")

from analyze_matches25 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, Match, check_match_preflight, digest, divergence,
    identical_moves, interval, markdown_rows, non_even_pairs, number, parse_games, penta_estimate,
    pgn_module, result_status, section_lines, summarized_output, tally_pairs,
)

MATCHES = {
    # games, seed, nodes A, nodes B, workers, explicit appended options for A/B
    "K15": (100, 7261, 2000, 2000, 4, (), ()),
    "C15": (200, 7262, 10000, 20000, 4, (), ()),
    "P1": (2000, 7263, 2002, 2000, 4, (), ()),
    "P2": (2000, 7264, 2002, 2000, 4, (), ()),
    "E2": (2000, 7265, 2040, 2000, 4, (), ()),
    "P3": (2000, 7266, 2002, 2000, 4, (), ()),
    "P4": (2000, 7267, 2002, 2000, 4, (), ()),
}
CONTROLS = ("K15", "C15")
CANDIDATES = ("P1", "P2", "E2", "P3", "P4")
CALIBRATION = ("P1", "P2", "P3", "P4")
BOUNDS = {4: (Fraction("9.49"), Fraction("2.50")),
          3: (Fraction("7.81"), Fraction("2.39")),
          2: (Fraction("5.99"), Fraction("2.24"))}
HEX = re.compile(r"[0-9a-f]{64}")
FEN_TAG = re.compile(r'^\[FEN "([^"]+)"\]$')
SOURCE_POSITIONS = 2632036


def fen4(fen):
    fields = fen.split()
    if len(fields) < 4:
        raise ValueError(f"invalid opening FEN: {fen}")
    return " ".join(fields[:4])


def fen_key(fen):
    return sha256(fen4(fen).encode("utf-8")).hexdigest()


def read_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    source = data["source"]
    if (source.get("sha256"), source.get("positions")) != (BOOK_SHA, SOURCE_POSITIONS):
        raise ValueError(f"{path}: official opening book identity or size differs")
    if data["cells"].keys() != MATCHES.keys():
        raise ValueError(f"{path}: reserved cells differ from the Job 26 schedule")
    reserved_keys, source_lines = set(), set()
    for name, (games, seed, *_) in MATCHES.items():
        cell = data["cells"][name]
        if ((cell.get("file"), cell.get("seed"), cell.get("count")) != (f"{name}.epd", seed, games // 2)
                or not HEX.fullmatch(cell.get("sha256", ""))):
            raise ValueError(f"{path}: {name} derived book identity does not match the schedule")
        lines = cell.get("source_line_numbers", [])
        if (len(set(lines)) != games // 2 or len(lines) != games // 2 or source_lines.intersection(lines)
                or any(not 1 <= line <= source["positions"] for line in lines)):
            raise ValueError(f"{path}: repeated or invalid source book line for {name}")
        source_lines.update(lines)
        keys = cell.get("fen_keys_sha256", [])
        if (len(set(keys)) != games // 2 or len(keys) != games // 2 or reserved_keys.intersection(keys)
                or any(not HEX.fullmatch(key) for key in keys)):
            raise ValueError(f"{path}: repeated or invalid reserved opening key for {name}")
        reserved_keys.update(keys)
    verified = data["verification"]
    counts = ("retained_positions", "distinct_exact_fen", "distinct_first_four_field_keys")
    overlaps = ("prior_exact_fen_overlap", "prior_first_four_field_overlap", "internal_overlap")
    if (any(verified.get(key) != len(reserved_keys) for key in counts)
            or any(verified.get(key) != 0 for key in overlaps)
            or verified.get("epd_readback_matches_source_rows") is not True):
        raise ValueError(f"{path}: manifest does not certify the reserved EPD subsets")
    return {"data": data, "sha256": digest(path)}


def validate_played_openings(name, fens, paired_fens, games, status, manifest):
    reserved = set(manifest["data"]["cells"][name]["fen_keys_sha256"])
    used = set(map(fen_key, fens))
    if len(set(map(fen_key, paired_fens))) != games // 2 or not used <= reserved:
        raise ValueError(f"{name}: repeated paired opening or position outside its reserved book")
    if status == "complete" and used != reserved:
        raise ValueError(f"{name}: finished match did not play each reserved opening once")


def read_meta(directory, name, manifest):
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
        ENGINE_SHA, manifest["data"]["cells"][name]["sha256"], FASTCHESS_REVISION,
    ):
        raise ValueError(f"{path}: wrong executable, book or fastchess provenance")
    cell = manifest["data"]["cells"][name]
    if (data.get("book_source_sha256"), data.get("book_manifest_sha256"), data.get("book_openings_count"),
            data.get("book_source_positions"), Path(data["book"]).name) != (
        BOOK_SHA, manifest["sha256"], cell["count"], SOURCE_POSITIONS, cell["file"],
    ):
        raise ValueError(f"{path}: derived opening provenance differs")
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


def read_match(raw, name, pgn, manifest):
    meta, status, reason = read_meta(raw, name, manifest)
    if meta is None:
        return Match(name, status, note=reason), None, None, None
    requested = MATCHES[name][0]
    groups = parse_games(raw / f"{name}.pgn", pgn, exact_moves=True)
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K15")
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
    fens = {game.start for pair in groups.values() for game in pair}
    paired_fens = {pair[0].start for pair in groups.values() if len(pair) == 2}
    validate_played_openings(name, fens, paired_fens, games, row.status, manifest)
    return row, identical_moves(groups), fens, groups if name in CANDIDATES else None


def gates(raw, pgn, manifest, only_k=False):
    k_result = read_match(raw, "K15", pgn, manifest)
    k, same, _, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K15 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K15 PASS: A and B both accepted the identical PC20 settings on the Job 4 executable, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K15": k_result}
    c_result = read_match(raw, "C15", pgn, manifest)
    c, _, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo >= -100:
        raise ValueError(f"C15 failed: {c.note or c.status}; needs Elo strictly below −100")
    print(f"C15 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K15": k_result, "C15": c_result}


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        name = fields[0]
        if name in CANDIDATES:
            if len(fields) not in (6, 7) or name in forecasts:
                raise ValueError(f"{path}: expected one forecast with Elo range, unequal-pair range and same-move count for {name}")
            elo_values = list(map(Fraction, fields[1:-3]))
            lo, hi = elo_values[-2:]
            if lo > hi or (len(elo_values) == 3 and not lo <= elo_values[0] <= hi):
                raise ValueError(f"{path}: invalid Elo range for {name}")
            low_pairs, high_pairs, identical = map(int, fields[-3:])
            if not (0 <= low_pairs <= high_pairs <= 1000 and 0 <= identical <= 1000):
                raise ValueError(f"{path}: pair forecast outside 0–1000 for {name}")
            center = elo_values[0] if len(elo_values) == 3 else None
            forecasts[name] = center, (lo, hi), (low_pairs, high_pairs), identical
        elif name.upper() == "CALIBRATION":
            verdict = " ".join(fields[1:]).strip().lower()
            if verdict not in ("calibrated", "too narrow") or "calibration" in forecasts:
                raise ValueError(f"{path}: expected one CALIBRATION calibrated|too narrow forecast")
            forecasts["calibration"] = verdict.upper()
    if forecasts.keys() != {*CANDIDATES, "calibration"}:
        raise ValueError(f"{path}: expected five match forecasts and one calibration forecast")
    return forecasts


def z_value(row):
    if row.elo is None or row.width is None:
        return None
    if row.width < 0:
        raise ValueError(f"{row.name}: negative confidence halfwidth")
    if row.width == 0:
        return None if row.elo == 0 else math.copysign(math.inf, row.elo)
    return row.elo * Fraction("1.96") / row.width


def calibration(results):
    included = {name: z_value(results[name][0])
                for name in CALIBRATION if results[name][0].status == "complete"}
    n = len(included)
    q = (sum((value ** 2 for value in included.values()), Fraction(0))
         if all(value is not None for value in included.values()) else None)
    if n not in BOUNDS or q is None:
        return included, q, "NOT JUDGED", None
    q_limit, z_limit = BOUNDS[n]
    calibrated = q <= q_limit and all(abs(value) <= z_limit for value in included.values())
    return included, q, "CALIBRATED" if calibrated else "TOO NARROW", None if calibrated else math.sqrt(q / 4)


def print_grades(results, forecasts, study):
    print("\n## Prediction grades\n")
    print("Ranges include their endpoints. Same-move forecasts are exact counts. Each match forecast is "
          "judged on its full 1,000 complete pairs.\n")
    print("| Match | Elo forecast | Elo observed | Elo grade | Non-1–1 forecast | Non-1–1 observed | "
          "Count grade | Same moves forecast | Same moves observed | Same moves grade | Evidence |")
    print("|---|---|---:|---|---|---:|---|---:|---:|---|---|")
    for name in CANDIDATES:
        row, same, _, _ = results[name]
        center, (lo, hi), (count_lo, count_hi), predicted_same = forecasts[name]
        measure = non_even_pairs(row)
        full = row.status == "complete"
        elo_grade = "ungraded" if not full or row.elo is None else "met" if lo <= row.elo <= hi else "missed"
        count_grade = ("ungraded" if not full or measure is None
                       else "met" if count_lo <= measure <= count_hi else "missed")
        same_grade = "ungraded" if not full or same is None else "met" if predicted_same == same else "missed"
        elo = interval((lo, hi)) if center is None else f"{number(center)} {interval((lo, hi))}"
        print(f"| {name} | {elo} | {number(row.elo)} | {elo_grade} | [{count_lo}, {count_hi}] | "
              f"{measure if measure is not None else 'n/a'} | {count_grade} | {predicted_same} | "
              f"{same if same is not None else 'n/a'} | {same_grade} | {result_status(row)} |")
    verdict = study[2]
    predicted = forecasts["calibration"]
    grade = "ungraded" if verdict == "NOT JUDGED" else "met" if verdict == predicted else "missed"
    print(f"\nCalibration forecast {predicted}. Observed {verdict}. Grade {grade}.")


def print_table_p(results):
    print("\n## Table P. Job 26 paired games\n")
    print("All rows use Job 4, PC20, embedded evaluation, Threads 1 and Hash 16. W-L-D is from A's perspective. "
          "Intervals are symmetric 95% pentanomial Elo ± halfwidth. Only complete color-reversed pairs contribute.\n")
    print("| Match | Nodes A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Non-1–1 |")
    print("|---|---|---|---:|---|---|---|---:|---:|")
    for name in CANDIDATES:
        row, same, _, _ = results[name]
        _, _, nodes_a, nodes_b, *_ = MATCHES[name]
        games = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        identical = f"{same}/{row.games // 2}" if same is not None else "n/a"
        uneven = non_even_pairs(row)
        print(f"| {name} | {nodes_a:,}/{nodes_b:,} | {result_status(row)} | {games} | {wld} | {penta} | "
              f"{number(row.elo)} {interval(row.interval)} | {identical} | {uneven if uneven is not None else 'n/a'} |")


def print_calibration(results, study):
    included, q, verdict, k = study
    print("\n## Calibration\n")
    print("For each complete P match, the standard error is its Table P halfwidth divided by 1.96. "
          "The calculation uses the resulting ratios before display rounding. A zero halfwidth with zero Elo "
          "makes z undefined. A zero halfwidth with nonzero Elo gives the signed infinite limit.\n")
    print("| Match | Halfwidth | Standard error | z arithmetic | Status |")
    print("|---|---:|---:|---|---|")
    for name in CALIBRATION:
        row = results[name][0]
        if name not in included:
            print(f"| {name} | {number(row.width, sign=False)} | n/a | excluded | {result_status(row)} |")
            continue
        z = included[name]
        error = row.width / Fraction("1.96") if row.width is not None else None
        numerator = number(row.elo, digits=8)
        denominator = number(row.width, sign=False, digits=8)
        formatted = number(z, digits=8) if z is not None else "undefined"
        arithmetic = f"`{numerator} / ({denominator} / 1.96) = {formatted}`"
        print(f"| {name} | {number(row.width, sign=False)} | {number(error, sign=False, digits=8)} | "
              f"{arithmetic} | {result_status(row)} |")
    n = len(included)
    terms = " + ".join(f"({number(z, digits=8) if z is not None else 'undefined'})²"
                       for z in included.values()) or "empty sum"
    print(f"\nQ = {terms} = {number(q, sign=False, digits=8) if q is not None else 'undefined'}.")
    if n in BOUNDS:
        q_limit, z_limit = BOUNDS[n]
        print(f"With {n} complete P matches, the bounds are Q ≤ {number(q_limit, sign=False)} and every "
              f"|z| ≤ {number(z_limit, sign=False)}.")
    else:
        print(f"{n} complete P matches. The stated rule needs at least two.")
    if q is None:
        print("An undefined z leaves Q undefined at the stated sample size.")
    print(f"\nCalibration {verdict}.")
    if k is not None:
        print(f"k = sqrt({number(q, sign=False, digits=8)} / 4) = {number(k, sign=False, digits=8)}.")
    e2 = results["E2"][0]
    seen = e2.interval is not None and e2.interval[0] > 0
    print(f"\nE2 {'SEEN' if seen else 'NOT SEEN'}. Elo {number(e2.elo)} {interval(e2.interval)}. "
          f"{result_status(e2)}.")


def print_table_j(results):
    import chess

    print("\n## Table J. P and E pairs with an unequal score\n")
    print("Ply 1 is the supplied opening FEN's first move. Game order follows the PGN within its Round. Repeated "
          "means the position immediately after that move occurred earlier in the recorded game, counting the supplied "
          "FEN as the first known position. Equality uses pieces, side to move, castling rights and legal en passant. "
          "Clocks are ignored. The ended marker gives the engine on move if play had continued.\n")
    print("| Match | Status | Non-1–1 pairs | Complete pairs |")
    print("|---|---|---:|---:|")
    for name in CANDIDATES:
        row = results[name][0]
        count = non_even_pairs(row)
        print(f"| {name} | {result_status(row)} | {count if count is not None else 'n/a'} | "
              f"{row.games // 2 if count is not None else 'n/a'} |")
    print("\n| Match | Round | Score A–B | First divergent ply | Exact pre-move FEN | Game 1 move | Game 1 engine | "
          "Game 1 repeated | Game 2 move | Game 2 engine | Game 2 repeated |")
    print("|---|---:|---|---:|---|---|---|---|---|---|---|")
    for name in CANDIDATES:
        row, _, _, groups = results[name]
        if groups is None:
            continue
        label = name if row.status == "complete" else f"{name} (incomplete)"
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
            else:
                ply, fen, left, right = diff
                print(f"| {label} | {round_} | {score} | {ply} | `{fen}` | {' | '.join(left)} | {' | '.join(right)} |")
        if found != non_even_pairs(row):
            raise ValueError(f"{name}: Table J did not account for every complete unequal-score pair")


WITHIN_HEADING = "### Within Job 26"
HISTORICAL_HEADING = "### Job 26 against every archived PGN"


def read_history(history_root, manifest):
    history = manifest["data"]["historical"]
    archived = {}
    expected = {item["path"]: item for item in history["files"]}
    if len(expected) != history["pgn_count"]:
        raise ValueError("historical manifest repeats a path or has the wrong inventory count")
    found = set()
    for path in history_root.glob("job*/raw/**/*.pgn"):
        relative = path.relative_to(history_root)
        job = relative.parts[0].removeprefix("job")
        if job.isdecimal() and int(job) < 26:
            found.add(relative.as_posix())
    if found != expected.keys():
        missing = sorted(expected.keys() - found)
        extra = sorted(found - expected.keys())
        raise ValueError(f"historical PGN inventory differs, missing {missing[:5]}, unexpected {extra[:5]}")

    exact_union, normalized_union = set(), set()
    seen_tags = 0
    for label, receipt in expected.items():
        path = history_root / label
        checksum = sha256()
        tags = []
        with path.open("rb") as contents:
            for line in contents:
                checksum.update(line)
                if not line.startswith(b"[FEN "):
                    continue
                match = FEN_TAG.fullmatch(line.decode("utf-8").rstrip())
                if match is None:
                    raise ValueError(f"{path}: malformed FEN tag")
                tags.append(match[1])
        if checksum.hexdigest() != receipt["sha256"] or len(tags) != receipt["fen_tags"]:
            raise ValueError(f"{path}: SHA-256 or FEN-tag count differs from manifest")
        exact = set(tags)
        normalized = set(map(fen4, exact))
        archived[label] = len(tags), exact, normalized
        exact_union.update(exact)
        normalized_union.update(normalized)
        seen_tags += len(tags)
    if (seen_tags, len(exact_union), len(normalized_union)) != (
        history["fen_tags"], history["distinct_exact"], history["distinct_first_four"],
    ):
        raise ValueError("archive totals differ from the historical opening manifest")
    reserved = {key for cell in manifest["data"]["cells"].values() for key in cell["fen_keys_sha256"]}
    if reserved & set(map(fen_key, normalized_union)):
        raise ValueError("a reserved Job 26 opening already appears in the archived PGNs")
    return archived


def print_openings(results, archive, manifest):
    print("\n## Shared openings\n")
    history = manifest["data"]["historical"]
    reserved_count = sum(cell["count"] for cell in manifest["data"]["cells"].values())
    print(f"The opening manifest binds {reserved_count:,} distinct reserved positions to the official source book. "
          f"All {history['pgn_count']} earlier PGN checksums were revalidated, including their "
          f"{history['fen_tags']:,} recorded FEN tags and {history['distinct_first_four']:,} distinct position keys. "
          "The reserved keys were disjoint from the complete earlier inventory. Comparisons below use all recorded "
          "FEN tags, including any unpaired games. First-four FEN fields compare piece placement, side to move, "
          "castling and the en-passant field with clocks omitted.\n")
    current = {
        name: (fens, set(map(fen4, fens))) if fens is not None else None
        for name, (_, _, fens, _) in results.items()
    }

    def label(name):
        if name in current and results[name][0].status != "complete":
            return f"{name} (incomplete)"
        return name

    print("| File | Status | FEN tags or distinct current openings | Distinct exact FENs | Distinct first-four FENs |")
    print("|---|---|---:|---:|---:|")
    for name, fens in current.items():
        row = results[name][0]
        values = (len(fens[0]), len(fens[0]), len(fens[1])) if fens is not None else ("n/a", "n/a", "n/a")
        print(f"| {name} | {result_status(row)} | {' | '.join(map(str, values))} |")
    for name, (count, exact, normalized) in archive.items():
        print(f"| {name} | archived | {count} | {len(exact)} | {len(normalized)} |")

    lookup = {**current, **{name: (exact, normalized) for name, (_, exact, normalized) in archive.items()}}
    for heading, pairs in ((WITHIN_HEADING, combinations(current, 2)),
                           (HISTORICAL_HEADING, product(current, archive))):
        print(f"\n{heading}\n")
        print("| File A | File B | Shared exact FENs | Shared first-four FENs |")
        print("|---|---|---:|---:|")
        for left, right in pairs:
            a, b = lookup[left], lookup[right]
            counters = (len(a[0] & b[0]), len(a[1] & b[1])) if a is not None and b is not None else ("n/a", "n/a")
            if any(isinstance(value, int) and value != 0 for value in counters):
                raise ValueError(f"shared opening found between {left} and {right}: {counters}")
            print(f"| {label(left)} | {label(right)} | {counters[0]} | {counters[1]} |")


def audit_openings(path, manifest):
    lines = path.read_text(encoding="utf-8").splitlines()
    prior = tuple(item["path"] for item in manifest["data"]["historical"]["files"])
    columns = ("File", "Status", "FEN tags or distinct current openings", "Distinct exact FENs", "Distinct first-four FENs")
    inventory_rows = list(markdown_rows(section_lines(lines, "## Shared openings"), columns))
    if Counter(row[0] for row in inventory_rows) != Counter((*MATCHES, *prior)):
        raise ValueError(f"{path}: shared-opening inventory dropped or duplicated a file")
    inventory = {name: (status, exact) for name, status, _, exact, _ in inventory_rows}

    def label(name):
        status = inventory[name][0]
        return name if name in prior or status == "complete" or status.startswith("complete:") else f"{name} (incomplete)"

    for heading, pairs in ((WITHIN_HEADING, combinations(MATCHES, 2)),
                           (HISTORICAL_HEADING, product(MATCHES, prior))):
        expected = {
            (label(left), label(right)): "n/a" if "n/a" in (inventory[left][1], inventory[right][1]) else "0"
            for left, right in pairs
        }
        rows = list(markdown_rows(section_lines(lines, heading),
                                  ("File A", "File B", "Shared exact FENs", "Shared first-four FENs")))
        if Counter((left, right) for left, right, _, _ in rows) != Counter(expected.keys()):
            raise ValueError(f"{path}: {heading} has missing, duplicate or mislabeled file pairs")
        if any(exact != expected[left, right] or normalized != exact for left, right, exact, normalized in rows):
            raise ValueError(f"{path}: {heading} has an overlap or misstates an unplayed file")
        print(f"{heading.removeprefix('### ')} verified: {len(rows)} exhaustive disjoint file comparisons.")


def table(raw, history_root, pgn, forecasts, manifest):
    archive = read_history(history_root, manifest)
    results = gates(raw, pgn, manifest)
    results.update((name, read_match(raw, name, pgn, manifest)) for name in CANDIDATES)
    previous_end = None
    for name in MATCHES:
        row = results[name][0]
        if previous_end and row.match_start and row.match_start < previous_end:
            raise ValueError(f"{name}: serial match started before the prior match ended")
        previous_end = row.match_end or previous_end
    study = calibration(results)
    print_grades(results, forecasts, study)
    print_table_p(results)
    print_calibration(results, study)
    print_table_j(results)
    print_openings(results, archive, manifest)
    print("\n## What this check cannot see\n")
    print("The PC's engine, net and settings (your tree plays its embedded evaluation); budgets other than 2,000 nodes; "
          "any spread that comes from the book itself rather than from the pairs.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("gates", "table"):
        option = modes.add_parser(mode)
        option.add_argument("raw", type=Path)
        option.add_argument("--manifest", type=Path, required=True)
        option.add_argument("--python-chess-dir", type=Path)
        if mode == "gates":
            option.add_argument("--only-k", action="store_true")
        else:
            option.add_argument("--history-root", type=Path, required=True)
            option.add_argument("--prediction", type=Path, required=True)
    audit = modes.add_parser("audit-openings")
    audit.add_argument("report", type=Path)
    audit.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = read_manifest(args.manifest)
    if args.mode == "audit-openings":
        audit_openings(args.report, manifest)
        return
    pgn = pgn_module(args.python_chess_dir)
    if args.mode == "gates":
        gates(args.raw, pgn, manifest, args.only_k)
    else:
        table(args.raw, args.history_root, pgn, read_prediction(args.prediction), manifest)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
