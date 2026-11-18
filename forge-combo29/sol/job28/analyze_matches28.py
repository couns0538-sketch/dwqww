#!/usr/bin/env python3
"""Verify Job 28 controls and readouts from paired PGNs and raw fastchess logs."""

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
for directory in (HERE.parent / "job27", HERE.parent / "sol-job27"):
    if (directory / "analyze_matches27.py").is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit("Missing Job 27 analyzer in adjacent job27 or sol-job27 directory")

from analyze_matches27 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, HEX, SOURCE_POSITIONS, fen_key, interval,
    number, p_text, penta_estimate, pgn_module, sign_test, status, summarize,
)
from analyze_matches26 import parse_games, tally_pairs
from analyze_matches24 import REFUSAL
from run_match16 import BASE, FASTCHESS_VERSION

FASTCHESS_SHA = "fb945c0930ff17786ccc1c07267930e1c0a6098f9bb16dcd13be20a11baec72e"
KEEP = "HistoryAgeKeep"
SCHEDULE = {
    # games, seed, nodes per move, HistoryAgeKeep on A/B (None means no option)
    "K17": (100, 7281, 2000, None, None),
    "K18": (100, 7282, 2000, 1024, None),
    "M1": (4000, 7283, 2000, 896, 1024),
    "M2": (2000, 7284, 20000, 896, 1024),
}
CONTROLS = ("K17", "K18")
MEASURED = ("M1", "M2")
READINGS = ("BETTER", "WORSE", "LEVEL")
FEN_HEADER = re.compile(rb'(?m)^\[FEN "([^"]+)"\]\r?$')


def read_manifest(path):
    data = path.read_bytes()
    manifest = json.loads(data)
    source, cells = manifest["source"], manifest["cells"]
    if (source["sha256"], source["positions"]) != (BOOK_SHA, SOURCE_POSITIONS) or cells.keys() != SCHEDULE.keys():
        raise ValueError(f"{path}: pinned opening source or cell grid differs")
    all_lines, all_keys = set(), set()
    for name, (games, seed, *_) in SCHEDULE.items():
        cell = cells[name]
        count = games // 2
        if (cell["count"], cell["seed"], cell["file"]) != (count, seed, f"{name}.epd") or not HEX.fullmatch(cell["sha256"]):
            raise ValueError(f"{name}: book cell identity differs from the schedule")
        lines, keys = cell["source_line_numbers"], cell["fen_keys_sha256"]
        if any(len(values) != count or len(set(values)) != count or prior.intersection(values)
               for values, prior in ((lines, all_lines), (keys, all_keys))):
            raise ValueError(f"{name}: book uses duplicate or missing source lines or opening keys")
        if any(not 1 <= line <= SOURCE_POSITIONS for line in lines) or any(not HEX.fullmatch(key) for key in keys):
            raise ValueError(f"{name}: invalid source line or opening key")
        all_lines.update(lines)
        all_keys.update(keys)
    proof = manifest["verification"]
    counts = ("retained_positions", "distinct_exact_fen", "distinct_first_four_field_keys")
    zeroes = ("prior_exact_fen_overlap", "prior_first_four_field_overlap", "internal_overlap")
    if (any(proof[k] != len(all_keys) for k in counts) or any(proof[k] for k in zeroes)
            or proof["epd_readback_matches_source_rows"] is not True):
        raise ValueError(f"{path}: incomplete source readback or opening overlap")
    return manifest, sha256(data).hexdigest()


def verify_history(root, manifest):
    recorded = manifest["historical"]
    expected = {file["path"]: file for file in recorded["files"]}
    files = set()
    for path in root.glob("job*/raw/**/*.pgn"):
        relative = path.relative_to(root)
        number = relative.parts[0].removeprefix("job")
        if number.isdecimal() and int(number) < 28:
            files.add(relative.as_posix())
    if len(expected) != recorded["pgn_count"] or files != expected.keys():
        raise ValueError("the archived PGN inventory differs from the opening manifest")
    raw_tags, exact, keys = 0, set(), set()
    for name, receipt in expected.items():
        contents = (root / name).read_bytes()
        tags = FEN_HEADER.findall(contents)
        if sha256(contents).hexdigest() != receipt["sha256"] or len(tags) != receipt["fen_tags"]:
            raise ValueError(f"{name}: archived PGN hash or FEN tag count differed")
        raw_tags += len(tags)
        exact.update(b" ".join(tag.split()) for tag in tags)
        keys.update(fen_key(tag.decode("utf-8")) for tag in set(tags))
    if (raw_tags, len(exact), len(keys)) != (recorded["fen_tags"], recorded["distinct_exact"], recorded["distinct_first_four"]):
        raise ValueError("archived FEN totals differ from the opening manifest")
    reserved = {key for cell in manifest["cells"].values() for key in cell["fen_keys_sha256"]}
    if reserved & keys:
        raise ValueError("a reserved Job 28 opening was played earlier")
    print(f"Opening audit verified {len(files)} earlier PGN files, {raw_tags:,} FEN tags and {len(reserved):,} disjoint new positions. The archive includes both D2s parts.")


def preflights(meta, keep_a, keep_b):
    for side, suffix, keep in (("A", "", keep_a), ("B", "_b", keep_b)):
        options = BASE if keep is None else (*BASE, (KEEP, str(keep)))
        settings = [f"setoption name {key} value {value}" for key, value in options]
        uci, reply = meta[f"preflight_uci{suffix}"], meta[f"preflight_reply{suffix}"]
        if (meta[f"settings_{side.lower()}"] != settings or meta[f"preflight_settings_sent{suffix}"] != settings
                or uci[-1:] != ["uciok"] or reply[-1:] != ["readyok"]
                or any(REFUSAL.search(line) for line in (*uci, *reply))):
            raise ValueError(f"{meta['match']} {side}: options differ or UCI preflight failed")
        if keep is not None and not any(line.startswith(f"option name {KEEP} type spin default 1024 ") for line in uci):
            raise ValueError(f"{meta['match']} {side}: H did not advertise the default skip option")
        yield [f"option.{key}={value}" for key, value in options]


def audit_match(raw, name, receipt, h_sha, pgn_path):
    path = raw / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        played = any((raw / f"{name}.{suffix}").is_file() for suffix in ("pgn", "out"))
        if played:
            raise ValueError(f"{name}: raw evidence exists but the finalized sidecar is absent")
        return None, "not played"
    meta = json.loads(path.read_bytes())
    manifest, manifest_sha = receipt
    games, seed, nodes, keep_a, keep_b = SCHEDULE[name]
    cell = manifest["cells"][name]
    variant = None if keep_a is None else {"name": KEEP, "value": str(keep_a)}
    key_values = {
        "match": name, "games_requested": games, "seed": seed, "nodes_a": nodes, "nodes_b": nodes,
        "concurrency": 4, "engine_a": "A", "engine_b": "B", "maxmoves": 300, "variant": variant,
        "exe_sha256": ENGINE_SHA if name == "K17" else h_sha,
        "exe_sha256_b": ENGINE_SHA if name in CONTROLS else h_sha,
        "fastchess_sha256": FASTCHESS_SHA, "fastchess_revision": FASTCHESS_REVISION,
        "fastchess_version": FASTCHESS_VERSION, "evaluation": "Forge embedded evaluation", "external_net_file": None,
        "book_sha256": cell["sha256"], "book_openings_count": cell["count"], "book_source_sha256": BOOK_SHA,
        "book_source_positions": SOURCE_POSITIONS, "book_manifest_sha256": manifest_sha,
    }
    for key, value in key_values.items():
        if meta[key] != value:
            raise ValueError(f"{name}: {key} recorded {meta[key]!r}, expected {value!r}")
    if Path(meta["book"]).name != cell["file"]:
        raise ValueError(f"{name}: configured opening filename differs from the manifest")
    if meta["status"] not in ("complete", "interrupted"):
        return None, f"{meta['status']} ({meta.get('error', 'no final match')})"
    if meta["status"] == "complete" and meta["fastchess_exit"] != 0:
        raise ValueError(f"{name}: complete match recorded a nonzero fastchess exit")
    opts_a, opts_b = preflights(meta, keep_a, keep_b)
    expected_argv = [
        meta["fastchess"], "-engine", f"cmd={meta['exe']}", "name=A", *opts_a,
        "-engine", f"cmd={meta['exe_b']}", "name=B", *opts_b,
        "-each", "proto=uci", f"nodes={nodes}", "-openings", f"file={meta['book']}", "format=epd", "order=random",
        "-srand", str(seed), "-rounds", str(games // 2), "-games", "2", "-repeat", "-concurrency", "4",
        "-maxmoves", "300", "-pgnout", f"file={meta['pgn']}",
    ]
    expected_argv.extend(("-ratinginterval", "1"))
    if meta["rating_interval_pairs"] != 1:
        raise ValueError(f"{name}: one-pair output cadence missing from sidecar")
    if meta["fastchess_command"] != expected_argv:
        raise ValueError(f"{name}: executable, opening, node budget or options differ in fastchess argv")

    pgn_path = pgn_path or raw / f"{name}.pgn"
    if not meta.get("pgn_sha256"):
        if meta["status"] == "interrupted" and not pgn_path.exists():
            return None, "cut with no PGN or complete pair"
        raise ValueError(f"{name}: missing PGN SHA-256")
    row = summarize(raw, name, meta, pgn_path)
    if row.status == "complete" and row.note:
        raise ValueError(f"{name}: no final fastchess summary matches all completed pairs")
    reserved, played = set(cell["fen_keys_sha256"]), set(map(fen_key, row.fens))
    if (not played <= reserved or len(set(map(fen_key, row.paired_fens))) != row.pairs
            or (row.status == "complete" and played != reserved)):
        raise ValueError(f"{name}: missing, reused or unassigned opening")
    return row, ""


def control(raw, name, receipt, h_sha, parser):
    row, reason = audit_match(raw, name, receipt, h_sha, None)
    if (row is None or row.status != "complete" or row.pairs != 50 or row.same_moves != 50
            or row.penta != (0, 0, 50, 0, 0) or row.elo != 0 or row.width != 0):
        observed = reason if row is None else f"{status(row)}, {row.same_moves}/{row.pairs} exact, penta {row.penta}"
        raise ValueError(f"{name} failed its 50 exact 1–1 pairs gate. {observed}.")
    # Reparse full moves as UCI and compare those independent of the rating parser.
    groups = parse_games(raw / f"{name}.pgn", parser, exact_moves=True)
    wld, penta, abnormal = tally_pairs(groups, exact_moves=True)
    if (wld, penta, abnormal) != ((row.wins, row.losses, row.draws), row.penta, 0):
        raise ValueError(f"{name}: independent UCI tally differs or a game ended abnormally")
    builds = "Job 4 vs Job 4" if name == "K17" else "H at HistoryAgeKeep 1024 vs Job 4"
    print(f"{name} PASS. {builds}, PC20, embedded evaluation, Threads 1, Hash 16, 2,000 nodes per move. "
          f"All {row.pairs} reversed-color pairs had identical ordered UCI moves and scored 1–1. "
          f"A W-L-D {row.wins}-{row.losses}-{row.draws}, pentanomial {row.penta}, Elo {number(row.elo)} {interval(row.bounds)}.")


def reading(row):
    if row is None or row.bounds is None:
        return "unavailable"
    lo, hi = row.bounds
    if 0 in (lo, hi):
        center, width = penta_estimate(row.penta, deterministic=True)
        # A displayed endpoint of 0.00 can hide the true sign of the bound.
        lo, hi = center - width, center + width
        print(f"{row.name} unrounded symmetric interval, used at rounding boundary: {interval((lo, hi), digits=8)}.")
    if lo > 0:
        return "BETTER"
    if hi < 0:
        return "WORSE"
    return "LEVEL"


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.partition("#")[0].split()
        if not fields:
            continue
        if len(fields) != 6 or fields[0] not in MEASURED or fields[0] in forecasts:
            raise ValueError(f"{path}: expected NAME ELO_MIN ELO_MAX UNEQUAL_MIN UNEQUAL_MAX READING")
        name, elo_lo, elo_hi, pairs_lo, pairs_hi, expected = fields
        elo_lo, elo_hi = Fraction(elo_lo), Fraction(elo_hi)
        pairs_lo, pairs_hi = int(pairs_lo), int(pairs_hi)
        if elo_lo > elo_hi or not 0 <= pairs_lo <= pairs_hi <= SCHEDULE[name][0] // 2 or expected not in READINGS:
            raise ValueError(f"{path}: invalid range or reading for {name}")
        forecasts[name] = ((elo_lo, elo_hi), (pairs_lo, pairs_hi), expected)
    if forecasts.keys() != set(MEASURED):
        raise ValueError(f"{path}: expected one forecast for each measured match")
    return forecasts


def predictions(rows, forecasts, readings):
    print("## Prediction grades\n")
    print("Ranges are inclusive. A cut uses the complete pairs actually played.\n")
    print("| Match | Forecast Elo | Observed / grade | Forecast unequal pairs | Observed / grade | Forecast reading | Observed / grade |")
    print("|---|---|---|---|---|---|---|")
    for name in MEASURED:
        elo, unequal, expected = forecasts[name]
        row, _ = rows[name]
        rating, unequal_count = (row.elo, row.better + row.worse) if row and row.pairs else (None, None)
        verdict = readings[name]
        a = "ungraded" if rating is None else "met" if elo[0] <= rating <= elo[1] else "missed"
        b = "ungraded" if unequal_count is None else "met" if unequal[0] <= unequal_count <= unequal[1] else "missed"
        c = "ungraded" if verdict == "unavailable" else "met" if verdict == expected else "missed"
        print(f"| {name} | {interval(elo)} | {number(rating)} / {a} | [{unequal[0]}, {unequal[1]}] | "
              f"{unequal_count if unequal_count is not None else 'n/a'} / {b} | {expected} | {verdict} / {c} |")


def match_table(rows, readings):
    print("\n## Part B. HistoryAgeKeep games\n")
    print("Both sides used H with PC20, embedded evaluation, Threads 1, Hash 16 and OwnBook false. "
          "A used HistoryAgeKeep 896 and B 1024. The two-sided exact sign test is descriptive. The reading uses the symmetric 95% Elo interval.\n")
    print("| Match | Nodes per move | Status | Games | A W-L-D | Pentanomial | Exact same moves / pairs | Better | Worse | Exact two-sided p | Elo [95%] | Reading |")
    print("|---|---:|---|---:|---|---|---|---:|---:|---:|---|---|")
    for name, (row, reason) in rows.items():
        nodes = SCHEDULE[name][2]
        if row is None or not row.pairs:
            note = reason if row is None else f"{status(row)}, no complete pair"
            print(f"| {name} | {nodes:,} | {note} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | unavailable |")
            continue
        penta = ", ".join(map(str, row.penta))
        exact = p_text(sign_test(row.better, row.worse))
        print(f"| {name} | {nodes:,} | {status(row)} | {2 * row.pairs} | {row.wins}-{row.losses}-{row.draws} | {penta} | "
              f"{row.same_moves}/{row.pairs} | {row.better} | {row.worse} | {exact} | "
              f"{number(row.elo)} {interval(row.bounds)} | **{readings[name]}** |")
    print("\n## What this check cannot see\n")
    print("The PC's engine (its net, its build, its other settings), keep values other than 896, budgets other than 2,000 and\n"
          "20,000 nodes, games longer than your book's.")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("raw", type=Path)
    cli.add_argument("--manifest", required=True, type=Path)
    cli.add_argument("--h-sha")
    cli.add_argument("--match", choices=SCHEDULE)
    cli.add_argument("--prediction", type=Path)
    cli.add_argument("--history-root", type=Path)
    cli.add_argument("--m1-pgn", type=Path)
    cli.add_argument("--m2-pgn", type=Path)
    cli.add_argument("--python-chess-dir", type=Path)
    args = cli.parse_args()
    if args.match != "K17" and (args.h_sha is None or not HEX.fullmatch(args.h_sha) or args.h_sha == ENGINE_SHA):
        cli.error("H's full, distinct executable SHA-256 is required except for K17 standalone")
    receipt = read_manifest(args.manifest)
    if args.history_root:
        verify_history(args.history_root, receipt[0])
    if args.match in CONTROLS or args.match is None:
        parser = pgn_module(args.python_chess_dir)
        for name in (args.match,) if args.match else CONTROLS:
            control(args.raw, name, receipt, args.h_sha, parser)
    if args.match in CONTROLS:
        return
    pgns = {"M1": args.m1_pgn, "M2": args.m2_pgn}
    names = (args.match,) if args.match else MEASURED
    rows = {name: audit_match(args.raw, name, receipt, args.h_sha, pgns[name]) for name in names}
    readings = {name: reading(row) for name, (row, _) in rows.items()}
    if args.prediction:
        if args.match:
            cli.error("grade the complete frozen prediction by omitting --match")
        print()
        predictions(rows, read_prediction(args.prediction), readings)
    match_table(rows, readings)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error)) from error
