#!/usr/bin/env python3
"""Audit and pool Job 30 and Job 31 paired fixed-node chess matches."""

import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
for directory in (HERE.parent / "job30", HERE.parent / "sol-job30"):
    if (directory / "analyze_matches30.py").is_file():
        sys.path.insert(0, str(directory))
        break
else:
    raise SystemExit("Missing the adjacent Job 30 analyzer")

from analyze_matches30 import (
    BOOK_SHA, FASTCHESS_REVISION, FASTCHESS_SHA, FASTCHESS_VERSION, FEN_HEADER,
    HEX, H_SHA, KEEP, PC20_MULTIPLIER, READINGS, SOURCE_POSITIONS,
    audit_match as audit30_match, digest, fen_key, interval, number, parse_games,
    p_text, penta_estimate, pgn_module, preflights, read_manifest as manifest30,
    sign_test, status, summarize, tally_pairs,
)
from split_pgn import verify as verify_pgn_parts


M_STAR = 1200
SCHEDULE = {
    # games, seed, nodes for A/B, HistoryAgeKeep for A/B
    "K21": (100, 7311, 2000, 2000, 896, 896),
    "C21": (200, 7312, 1000, 2000, 1024, 1024),
    "M3b": (8000, 7313, 2000, 2000, 896, 1024),
    "M4b": (2000, 7314, 20000, 20000, 896, 1024),
}
CONTROLS = ("K21", "C21")
MEASURED = ("M3b", "M4b")
PRIOR = {
    "M3": (
        "7f86a50", "0db59fcb17542ccac056676123489ee0af8c07e11b2f4e2d78bddbc2fa74a9f1",
        "bfcfff089500cd2b3d579e7ad7f9ad7cf0a391a238c30fe83ae17c86b37a9c6a",
        "62e602b434f075b392425478fabe83c17f7578275d8a9d79ebd31edb5d4c0960",
    ),
    "M4": (
        "3dfa7ce", "d31a0150949bb153cfdc9e4a848627b17164d4c8615d061167b8aa02da39c1d6",
        "e8e70eccd9adac5ec88d158c6dd4d76296f4a9713a44915402bc627e3b51e977",
        "c245b03de4582e4b72b277828da252abbfd1b68a7d243022cb3e124aaa0cb43b",
    ),
}
PRIOR_MANIFEST_SHA = "bfed2e7ceddd12783af2da7c87f11cc7560e5ed92eb19f9d62583e0db7884e50"


def read_manifest(path):
    data = path.read_bytes()
    manifest = json.loads(data)
    source, cells = manifest["source"], manifest["cells"]
    if (source["sha256"], source["positions"]) != (BOOK_SHA, SOURCE_POSITIONS) or cells.keys() != SCHEDULE.keys():
        raise ValueError(f"{path}: pinned opening source or cell grid differs")
    lines_seen, fens_seen = set(), set()
    for name, (games, seed, *_) in SCHEDULE.items():
        cell = cells[name]
        count = games // 2
        if (cell["count"], cell["seed"], cell["file"]) != (count, seed, f"{name}.epd") or not HEX.fullmatch(cell["sha256"]):
            raise ValueError(f"{name}: book cell identity differs from the schedule")
        lines, fens = cell["source_line_numbers"], cell["fen_keys_sha256"]
        if any(len(values) != count or len(set(values)) != count or prior.intersection(values)
               for values, prior in ((lines, lines_seen), (fens, fens_seen))):
            raise ValueError(f"{name}: opening source line or FEN repeated or missing")
        if any(type(line) is not int or not 1 <= line <= SOURCE_POSITIONS for line in lines) or any(not HEX.fullmatch(key) for key in fens):
            raise ValueError(f"{name}: invalid source line or FEN key")
        lines_seen.update(lines)
        fens_seen.update(fens)
    proof = manifest["verification"]
    count_names = ("retained_positions", "distinct_exact_fen", "distinct_first_four_field_keys")
    overlap_names = ("prior_exact_fen_overlap", "prior_first_four_field_overlap", "internal_overlap")
    if (any(proof[key] != len(fens_seen) for key in count_names) or any(proof[key] for key in overlap_names)
            or proof["epd_readback_matches_source_rows"] is not True):
        raise ValueError(f"{path}: incomplete opening readback or opening overlap")
    return manifest, sha256(data).hexdigest()


def verify_history(root, manifest):
    recorded = manifest["historical"]
    expected = {entry["path"]: entry for entry in recorded["files"]}
    paths = (path.relative_to(root) for path in root.glob("job*/raw/**/*.pgn"))
    files = {path.as_posix() for path in paths if path.parts[0][3:].isdecimal() and int(path.parts[0][3:]) < 31}
    if len(expected) != recorded["pgn_count"] or files != expected.keys():
        raise ValueError("the archived PGN inventory differs from the opening manifest")
    tags_found, starts, fens = 0, set(), set()
    for name, entry in expected.items():
        data = (root / name).read_bytes()
        tags = FEN_HEADER.findall(data)
        if sha256(data).hexdigest() != entry["sha256"] or len(tags) != entry["fen_tags"]:
            raise ValueError(f"{name}: archived PGN hash or FEN tag count differs")
        tags_found += len(tags)
        starts.update(b" ".join(tag.split()) for tag in tags)
        fens.update(fen_key(tag.decode("utf-8")) for tag in set(tags))
    if (tags_found, len(starts), len(fens)) != (recorded["fen_tags"], recorded["distinct_exact"], recorded["distinct_first_four"]):
        raise ValueError("archived FEN totals differ from the opening manifest")
    reserved = {key for cell in manifest["cells"].values() for key in cell["fen_keys_sha256"]}
    if reserved & fens:
        raise ValueError("a reserved Job 31 opening was played earlier")
    print(f"Opening audit verified {len(files)} earlier PGN files, {tags_found:,} FEN tags and {len(reserved):,} disjoint new positions, including independent Job 30 and Job 31 opening sets.")


def pgn_file(raw, name, explicit, temp):
    if explicit is not None:
        return explicit
    full = raw / f"{name}.pgn"
    parts = raw / f"{name}.pgn.manifest.json"
    if full.exists() or not parts.exists():
        return full
    manifest = json.loads(parts.read_bytes())
    if manifest["original"]["file"] != full.name or manifest["max_part_bytes"] > 20_000_000:
        raise ValueError(f"{parts}: split PGN name or byte cap differs")
    joined = temp / full.name
    with joined.open("xb") as output:
        for chunk in verify_pgn_parts(raw, manifest):
            output.write(chunk)
    return joined


def audit_match(raw, name, receipt, m_star, pgn_path):
    path = raw / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        if pgn_path.is_file() or (raw / f"{name}.out").exists():
            raise ValueError(f"{name}: raw evidence exists but the finalized sidecar is absent")
        return None, "not played"
    meta = json.loads(path.read_bytes())
    manifest, manifest_sha = receipt
    games, seed, nodes_a, nodes_b, keep_a, keep_b = SCHEDULE[name]
    cell = manifest["cells"][name]
    multiplier_a = m_star if keep_a == 896 else PC20_MULTIPLIER
    multiplier_b = m_star if keep_b == 896 else PC20_MULTIPLIER
    variant = None if name in CONTROLS else {"name": KEEP, "value": str(keep_a)}
    expected = {
        "match": name, "games_requested": games, "seed": seed, "nodes_a": nodes_a, "nodes_b": nodes_b,
        "concurrency": 4, "engine_a": "A", "engine_b": "B", "maxmoves": 300, "variant": variant,
        "exe_sha256": H_SHA, "exe_sha256_b": H_SHA, "history_prune_multiplier_a": multiplier_a,
        "history_prune_multiplier_b": multiplier_b, "fastchess_sha256": FASTCHESS_SHA,
        "fastchess_revision": FASTCHESS_REVISION, "fastchess_version": FASTCHESS_VERSION,
        "evaluation": "Forge embedded evaluation", "external_net_file": None, "book_sha256": cell["sha256"],
        "book_openings_count": cell["count"], "book_source_sha256": BOOK_SHA,
        "book_source_positions": SOURCE_POSITIONS, "book_manifest_sha256": manifest_sha, "rating_interval_pairs": 1,
    }
    for key, value in expected.items():
        if meta.get(key) != value:
            raise ValueError(f"{name}: {key} recorded {meta.get(key)!r}, expected {value!r}")
    if Path(meta["book"]).name != cell["file"]:
        raise ValueError(f"{name}: configured opening filename differs from the manifest")
    if meta["status"] not in ("complete", "interrupted"):
        return None, f"{meta['status']} ({meta.get('error', 'no final match')})"
    if meta["status"] == "complete" and meta["fastchess_exit"] != 0:
        raise ValueError(f"{name}: complete match recorded a nonzero fastchess exit")
    argv = [meta["fastchess"]]
    options = preflights(meta, keep_a, keep_b, multiplier_a, multiplier_b)
    for side, path, configured, nodes in zip(("A", "B"), (meta["exe"], meta["exe_b"]), options, (nodes_a, nodes_b), strict=True):
        argv.extend(("-engine", f"cmd={path}", f"name={side}", *configured))
        if nodes_a != nodes_b:
            argv.append(f"nodes={nodes}")
    argv.extend(("-each", "proto=uci"))
    if nodes_a == nodes_b:
        argv.append(f"nodes={nodes_a}")
    argv.extend(("-openings", f"file={meta['book']}", "format=epd", "order=random", "-srand", str(seed),
                 "-rounds", str(games // 2), "-games", "2", "-repeat", "-concurrency", "4", "-maxmoves",
                 "300", "-pgnout", f"file={meta['pgn']}", "-ratinginterval", "1"))
    if meta["fastchess_command"] != argv:
        raise ValueError(f"{name}: executable, opening, node budget, or options differ in fastchess argv")
    if not meta.get("pgn_sha256") and meta["status"] == "interrupted" and not pgn_path.exists():
        return None, "cut without a PGN or a complete pair"
    row = summarize(raw, name, meta, pgn_path)
    if row.status == "complete" and row.note:
        raise ValueError(f"{name}: no final fastchess summary matches all completed pairs")
    reserved, used = set(cell["fen_keys_sha256"]), set(map(fen_key, row.fens))
    if (not used <= reserved or len(set(map(fen_key, row.paired_fens))) != row.pairs
            or (row.status == "complete" and used != reserved)):
        raise ValueError(f"{name}: missing, reused, or unassigned opening")
    return unround(row), ""


def unround(row):
    if row.bounds is not None:
        row.elo, row.width = penta_estimate(row.penta, deterministic=True)
    return row


def control(raw, name, receipt, m_star, path, parser):
    row, reason = audit_match(raw, name, receipt, m_star, path)
    if row is None or row.status != "complete" or row.bounds is None:
        raise ValueError(f"{name} gate failed. {reason or status(row)}.")
    if name == "K21" and (row.pairs, row.same_moves, row.penta, row.elo, row.width) != (50, 50, (0, 0, 50, 0, 0), 0, 0):
        raise ValueError(f"{name} gate failed. Identical 1–1 pairs {row.equal_same}/{row.pairs}, penta {row.penta}.")
    if name == "C21" and (row.pairs != 100 or row.bounds[1] >= 0):
        raise ValueError(f"{name} gate failed. Found {row.pairs} reversed-color pairs and Elo {number(row.elo)} {interval(row.bounds)}.")
    independent = parse_games(path, parser, exact_moves=True)
    wld, penta, abnormal = tally_pairs(independent, exact_moves=name == "K21")
    if (wld, penta, abnormal) != ((row.wins, row.losses, row.draws), row.penta, 0):
        raise ValueError(f"{name}: second UCI tally differs or a game ended abnormally")
    settings = f"HistoryAgeKeep 896 and HistoryPruneMultiplier {m_star}" if name == "K21" else "HistoryAgeKeep 1024 and HistoryPruneMultiplier 2220"
    condition = "All 50 reversed-color pairs scored 1–1 with identical ordered UCI moves." if name == "K21" else "The upper end of the Elo interval is below zero."
    _, _, nodes_a, nodes_b, *_ = SCHEDULE[name]
    print(f"{name} PASS. H on both sides with PC20, {settings}, embedded evaluation, Threads 1, Hash 16, and A/B fixed budgets of {nodes_a:,}/{nodes_b:,} nodes per move. "
          f"{condition} A W-L-D {row.wins}-{row.losses}-{row.draws}, pentanomial {row.penta}, Elo {number(row.elo)} {interval(row.bounds)}.")


def read_prior(history_root, m_star, explicit_m3_pgn, temp):
    job30 = history_root / "job30"
    receipt = manifest30(job30 / "openings/manifest.json")
    if receipt[1] != PRIOR_MANIFEST_SHA or int((job30 / "mstar.txt").read_text()) != m_star:
        raise ValueError("pinned Job 30 opening manifest or selected multiplier differs")
    rows = {}
    for name, (commit, meta_sha, out_sha, pgn_sha) in PRIOR.items():
        raw = job30 / "raw"
        pgn = pgn_file(raw, name, explicit_m3_pgn if name == "M3" else None, temp)
        for path, expected in ((raw / f"{name}.meta", meta_sha), (raw / f"{name}.out", out_sha), (pgn, pgn_sha)):
            if digest(path) != expected:
                raise ValueError(f"{path}: SHA-256 differs from checkpoint {commit}")
        row, reason = audit30_match(raw, name, receipt, H_SHA, m_star, pgn)
        rows[name] = (unround(row), "") if row is not None else (None, reason)
    return rows


def pooled_result(previous, fresh):
    if previous is not None and fresh is not None and set(map(fen_key, previous.fens)) & set(map(fen_key, fresh.fens)):
        raise ValueError(f"{previous.name} and {fresh.name} opened from an overlapping position")
    included = tuple(row for row in (previous, fresh) if row is not None and row.status == "complete")
    if not included:
        return included, (), None, None, "LEVEL"
    penta = tuple(sum(bucket) for bucket in zip(*(row.penta for row in included), strict=True))
    estimate = penta_estimate(penta, deterministic=True)
    if estimate is None:
        return included, penta, None, None, "LEVEL"
    elo, width = estimate
    bounds = elo - width, elo + width
    fresh_elo = fresh.elo if fresh is not None else None
    if fresh_elo is not None and bounds[0] > 0 and fresh_elo > 0:
        return included, penta, elo, bounds, "BETTER"
    if fresh_elo is not None and bounds[1] < 0 and fresh_elo < 0:
        return included, penta, elo, bounds, "WORSE"
    return included, penta, elo, bounds, "LEVEL"


def read_prediction(path):
    forecasts = {}
    used_job30 = None
    for line in path.read_text().splitlines():
        note = re.fullmatch(r"\s*#\s*Used Job 30 numbers:\s*(yes|no)\b.*", line, re.IGNORECASE)
        if note:
            if used_job30 is not None:
                raise ValueError(f"{path}: repeated Job 30 use disclosure")
            used_job30 = note[1].lower()
        fields = line.partition("#")[0].split()
        if not fields:
            continue
        if len(fields) != 4 or fields[0] not in MEASURED or fields[0] in forecasts:
            raise ValueError(f"{path}: expected NAME ELO_MIN ELO_MAX READING")
        name, low, high, expected = fields
        low, high = Fraction(low), Fraction(high)
        if low > high or expected not in READINGS:
            raise ValueError(f"{path}: invalid Elo range or reading for {name}")
        forecasts[name] = ((low, high), expected)
    if forecasts.keys() != set(MEASURED) or used_job30 is None:
        raise ValueError(f"{path}: add both fresh forecasts and a '# Used Job 30 numbers: yes|no' line")
    return forecasts, used_job30


def predictions(rows, forecasts, pools):
    values, used = forecasts
    print("\n## Prediction grades\n")
    disclosure = "used" if used == "yes" else "did not use"
    print(f"The frozen forecast {disclosure} Job 30’s numbers. The ranges are inclusive and apply to the fresh match. The forecast reading applies to the declared pooled rule.\n")
    print("| Match | Forecast Elo | Observed / grade | Forecast pooled reading | Observed / grade |")
    print("|---|---|---|---|---|")
    for name in MEASURED:
        predicted_range, expected = values[name]
        row, _ = rows[name]
        rating = row.elo if row else None
        verdict = pools[name][-1]
        grade = "ungraded" if rating is None else "met" if predicted_range[0] <= rating <= predicted_range[1] else "missed"
        verdict_grade = "met" if verdict == expected else "missed"
        print(f"| {name} | {interval(predicted_range)} | {number(rating)} / {grade} | {expected} | {verdict} / {verdict_grade} |")


def match_table(rows, m_star):
    print("\n## Job 31 matches\n")
    print("Both sides used H with PC20, embedded evaluation, Threads 1, Hash 16 and OwnBook false. "
          f"A used HistoryAgeKeep 896 with HistoryPruneMultiplier {m_star}, and B 1024 with 2220. "
          "Elo uses the symmetric 95% interval computed at full precision from the pentanomial counts. "
          "The two-sided exact sign test is descriptive.\n")
    print("| Match | Nodes per move | Status | Games in complete pairs | A W-L-D | Pentanomial | Exact same moves / pairs | Better | Worse | Exact two-sided p | Elo [95%] |")
    print("|---|---:|---|---:|---|---|---|---:|---:|---:|---|")
    for name, (row, reason) in rows.items():
        nodes = SCHEDULE[name][2]
        if row is None or not row.pairs:
            note = reason if row is None else f"{status(row)}, no complete pair"
            print(f"| {name} | {nodes:,} | {note} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        penta = ", ".join(map(str, row.penta))
        exact = p_text(sign_test(row.better, row.worse))
        print(f"| {name} | {nodes:,} | {status(row)} | {2 * row.pairs:,} | {row.wins}-{row.losses}-{row.draws} | {penta} | "
              f"{row.same_moves}/{row.pairs} | {row.better} | {row.worse} | {exact} | {number(row.elo)} {interval(row.bounds)} |")


def pool_table(prior, fresh, pools):
    print("\n## Pooled reading\n")
    print("For each node count: POOL = job 30's match plus job 31's match at that node count (pentanomial counts added; a cut "
          "or missing match is left out and named), Elo with its 95 % interval from the pooled counts. BETTER when the pooled "
          "interval lies wholly above 0 AND the job 31 match alone has a positive Elo; WORSE when it lies wholly below 0 AND "
          "the job 31 match alone has a negative Elo; LEVEL otherwise.\n")
    if any(row is not None and row.status == "interrupted" for row, _ in fresh.values()):
        print("A cut Job 31 match supplies a standalone Elo from its complete pairs when estimable. Its pentanomial counts are omitted from the pool.\n")
    print("| Nodes per move | Job 30 Elo [95%] | Job 31 Elo [95%] | Included | Omitted | Pairs | Pooled pentanomial | Pooled Elo [95%] | Reading |")
    print("|---:|---|---|---|---|---:|---|---|---|")
    for name, (included, penta, elo, bounds, reading) in pools.items():
        previous_name = name.removesuffix("b")
        observations = ((previous_name, *prior[previous_name]), (name, *fresh[name]))
        omitted = [f"{label} ({reason if row is None else status(row)})" for label, row, reason in observations
                   if row is None or row.status != "complete"]
        estimates = [f"{number(row.elo)} {interval(row.bounds)}" if row else "n/a" for _, row, _ in observations]
        all_penta = ", ".join(map(str, penta)) if penta else "n/a"
        print(f"| {SCHEDULE[name][2]:,} | {estimates[0]} | {estimates[1]} | {', '.join(row.name for row in included) or 'none'} | "
              f"{', '.join(omitted) or 'none'} | {sum(penta):,} | {all_penta} | {number(elo)} {interval(bounds)} | **{reading}** |")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("raw", type=Path)
    cli.add_argument("--manifest", required=True, type=Path)
    cli.add_argument("--m-star", required=True, choices=(M_STAR,), type=int)
    cli.add_argument("--match", choices=SCHEDULE)
    cli.add_argument("--prediction", type=Path)
    cli.add_argument("--history-root", type=Path)
    cli.add_argument("--m3b-pgn", type=Path)
    cli.add_argument("--m4b-pgn", type=Path)
    cli.add_argument("--m3-pgn", type=Path)
    cli.add_argument("--python-chess-dir", type=Path)
    args = cli.parse_args()
    if args.match is None and args.history_root is None:
        cli.error("--history-root is required for the complete report and the Job 30 pools")
    if args.match and args.prediction:
        cli.error("omit --match to grade the complete frozen prediction")

    receipt = read_manifest(args.manifest)
    if args.history_root:
        verify_history(args.history_root, receipt[0])
    with TemporaryDirectory(prefix="sol-job31-joined-") as temp_path:
        temp = Path(temp_path)
        if args.match in CONTROLS or args.match is None:
            parser = pgn_module(args.python_chess_dir)
            for name in (args.match,) if args.match else CONTROLS:
                control(args.raw, name, receipt, args.m_star, pgn_file(args.raw, name, None, temp), parser)
            if args.match:
                return
        names = (args.match,) if args.match else MEASURED
        explicit = {"M3b": args.m3b_pgn, "M4b": args.m4b_pgn}
        rows = {name: audit_match(args.raw, name, receipt, args.m_star, pgn_file(args.raw, name, explicit[name], temp)) for name in names}
        if args.match:
            match_table(rows, args.m_star)
            return
        prior = read_prior(args.history_root, args.m_star, args.m3_pgn, temp)
        pools = {name: pooled_result(prior[name.removesuffix("b")][0], row) for name, (row, _) in rows.items()}
        if args.prediction:
            predictions(rows, read_prediction(args.prediction), pools)
        match_table(rows, args.m_star)
        pool_table(prior, rows, pools)
        print("\n## What this check cannot see\n")
        print("The PC's engine (its net, its build, its other settings), keep values other than 896, budgets other than 2,000 and\n20,000 nodes.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error)) from error
