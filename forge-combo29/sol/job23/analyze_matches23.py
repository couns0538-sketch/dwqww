#!/usr/bin/env python3
"""Audit Job 23 controls, paired PGN tables, and EvalSwing evidence across seeds."""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
for job22 in (HERE.parent / "job22", HERE.parent / "sol-job22"):
    if (job22 / "analyze_matches22.py").is_file():
        sys.path.insert(0, str(job22))
        break
else:
    raise SystemExit("Job 22's analyze_matches22.py is missing from adjacent job22 or sol-job22.")

from analyze_matches22 import (
    BOOK_SHA, CANDIDATES as PRIOR22, ENGINE_SHA, FASTCHESS_REVISION, Match,
    PRIOR as PRIOR_JOBS, check_match_preflight, digest, exploratory_read, historical_openings,
    identical_moves, interval, markdown_rows, match_status, number, parse_games, penta_estimate,
    pgn_module, pool_results, read_match as read_job22_match, read_pca_sha, replicated,
    replicated_loss, section_lines, summarized_output, tally_pairs, yes_no,
)
from analyze_matches16 import check_preflight
from analyze_matches21 import verify_prior_cut

MATCHES = {
    # games, seed, nodes A, nodes B, workers, side extras Mult/(W Max or PCA FHB), variant
    "K12": (100, 7231, 2000, 2000, 4, ("128", "200"), ("128", "200"), None),
    "C12": (200, 7232, 10000, 20000, 4, ("0", "200"), ("0", "200"), None),
    "F5kr": (2000, 7233, 2000, 2000, 2, ("0", "5"), ("0", "0"), ("FailHighBlend", "5")),
    "M128k": (2000, 7234, 2000, 2000, 2, ("128", "200"), ("64", "200"), ("EvalSwingMult", "128")),
    "X400k": (2000, 7235, 2000, 2000, 2, ("64", "400"), ("64", "200"), ("EvalSwingMax", "400")),
    "M96k": (2000, 7236, 2000, 2000, 2, ("96", "200"), ("64", "200"), ("EvalSwingMult", "96")),
    "M128w": (1600, 7237, 20000, 20000, 2, ("128", "200"), ("64", "200"), ("EvalSwingMult", "128")),
}
CONTROLS = ("K12", "C12")
SLOTS = (("F5kr", "M128k", "X400k", "M96k"), ("M128w",))
CANDIDATES = (*SLOTS[0], *SLOTS[1])
PRIOR = {**PRIOR_JOBS, 22: PRIOR22}
W_ADVERTISEMENT = "option name EvalSwingMult type spin default 0 min 0 max 128"


def read_w_sha(path, pca_sha):
    fields = path.read_text(encoding="utf-8").split()
    if not fields or not re.fullmatch(r"[0-9a-f]{64}", fields[0]) or fields[0] in (ENGINE_SHA, pca_sha):
        raise ValueError(f"{path}: expected the distinct W executable SHA-256")
    return fields[0]


def check_w_preflight(meta, a_options, b_options):
    check_preflight(meta, a_options, b_options)
    command = meta["fastchess_command"]
    sections = [index for index, arg in enumerate(command) if arg == "-engine"]
    if len(sections) != 2 or command.count("-each") != 1:
        raise ValueError("fastchess argv is missing expected engine sections")
    for side, suffix, start, end in (
        ("A", "", sections[0], sections[1]), ("B", "_b", sections[1], command.index("-each")),
    ):
        uci = meta[f"preflight_uci{suffix}"]
        if (W_ADVERTISEMENT not in uci
                or any(line.startswith("option name FailHighBlend ") for line in uci)):
            raise ValueError(f"engine {side}: preflight did not advertise the isolated W range")
        argv = command[start + 1:end]
        settings = meta[f"settings_{side.lower()}"]
        expected_args = ["option." + line.removeprefix("setoption name ").replace(" value ", "=", 1)
                         for line in settings]
        if (f"cmd={meta['exe']}" not in argv or f"name={side}" not in argv
                or [arg for arg in argv if arg.startswith("option.")] != expected_args):
            raise ValueError(f"engine {side}: fastchess argv differs from the W preflight")


def read_meta(directory, name, pca_sha, w_sha):
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
    expected_exe = pca_sha if name == "F5kr" else w_sha
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
        if name == "F5kr":
            check_match_preflight(data, a_extras, b_extras)
        else:
            check_w_preflight(data, a_extras, b_extras)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{path}: {error}") from error
    return data, ""


def read_match(raw, name, pgn, pca_sha, w_sha):
    meta, reason = read_meta(raw, name, pca_sha, w_sha)
    if meta is None:
        return Match(name, "unavailable", note=reason), None, None
    requested = MATCHES[name][0]
    groups = parse_games(raw / f"{name}.pgn", pgn, exact_moves=True)
    raw_games = sum(map(len, groups.values()))
    (w, l, d), penta, abnormal = tally_pairs(groups, exact_moves=name == "K12")
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


def gates(raw, pgn, pca_sha, w_sha, only_k=False):
    k_result = read_match(raw, "K12", pgn, pca_sha, w_sha)
    k, same, _ = k_result
    if k.status != "complete" or k.penta != (0, 0, 50, 0, 0) or same != 50:
        raise ValueError(f"K12 failed: {k.note or k.status}; expected 50 identical equal-point pairs")
    print("K12 PASS: A and B both accepted explicit EvalSwingMult 128 and EvalSwingMax 200 on W, and 50/50 pairs matched exact moves and 1–1 points.")
    if only_k:
        return {"K12": k_result}
    c_result = read_match(raw, "C12", pgn, pca_sha, w_sha)
    c, _, _ = c_result
    if c.status != "complete" or c.elo is None or c.elo > -100 or c.interval[1] >= 0:
        raise ValueError(f"C12 failed: {c.note or c.status}; needs Elo at most −100 and upper 95% bound below zero")
    print(f"C12 PASS: Elo {number(c.elo)}, upper 95% bound {number(c.interval[1])}.")
    return {"K12": k_result, "C12": c_result}


def read_prediction(path):
    forecasts = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields or fields[0] not in CANDIDATES:
            continue
        name = fields[0]
        if len(fields) != 4 or name in forecasts:
            raise ValueError(f"{path}: expected one NAME SIGNED_ELO LOWER UPPER row for {name}")
        point, low, high = map(Fraction, fields[1:])
        if low > point or point > high:
            raise ValueError(f"{path}: range for {name} must contain its point forecast")
        forecasts[name] = point, low, high
    if forecasts.keys() != set(CANDIDATES):
        raise ValueError(f"{path}: expected five signed Elo forecasts with ranges")
    return forecasts


def print_grades(results, forecasts):
    print("\n## Prediction grades\n")
    print("Sign and inclusive forecast range are checked separately. The combined forecast survives only when "
          "both checks pass. A zero sign forecast requires observed zero.\n")
    print("| Match | Forecast | Predicted range | Observed | Sign | Range | Overall | Evidence status |")
    print("|---|---:|---|---:|---|---|---|---|")
    sign_count = range_count = complete = survives = 0
    for name in CANDIDATES:
        point, low, high = forecasts[name]
        row = results[name][0]
        if row.elo is None:
            sign = inside = overall = "ungraded"
        else:
            signed = (point > 0) == (row.elo > 0) and (point < 0) == (row.elo < 0)
            covered = low <= row.elo <= high
            sign_count += signed
            range_count += covered
            complete += 1
            survives += signed and covered
            sign = "met" if signed else "missed"
            inside = "met" if covered else "missed"
            overall = "survives" if signed and covered else "KILLED"
        print(f"| {name} | {number(point)} | {interval((low, high))} | {number(row.elo)} | "
              f"{sign} | {inside} | {overall} | {match_status(row)} |")
    print(f"\n{sign_count}/{complete} signs and {range_count}/{complete} ranges met. "
          f"{survives} survive, {complete - survives} KILLED, {len(CANDIDATES) - complete} ungraded.")


def print_table_p(rows):
    print("\n## Table P. Job 23 paired games\n")
    print("All rows use PC20, embedded evaluation, Threads 1, Hash 16 and the pinned opening book. W-L-D is from A's "
          "perspective. Identical pairs share the complete ordered UCI move sequence.\n")
    print("| Match | Build, nodes per move, options A/B | Status | Games | W-L-D | Pentanomial | "
          "Elo [95%] | Same moves / pairs | Reading |")
    print("|---|---|---|---:|---|---|---|---:|---|")
    for row, same in rows:
        games = row.games if row.penta else "n/a"
        wld = f"{row.wins}-{row.losses}-{row.draws}" if row.penta else "n/a"
        penta = ", ".join(map(str, row.penta)) or "n/a"
        sequence = f"{same}/{row.games // 2}" if same is not None else "n/a"
        if row.name.startswith("F5"):
            build = "PCA, 2,000, FailHighBlend 5/0 and EvalSwingMult 0/0"
            reading = "two-seed loss comparison"
        else:
            _, _, nodes, _, _, a_options, b_options, _ = MATCHES[row.name]
            build = (f"W, {nodes:,}, EvalSwingMult {a_options[0]}/{b_options[0]} "
                     f"and EvalSwingMax {a_options[1]}/{b_options[1]}")
            reading = exploratory_read(row)
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


WITHIN_HEADING = "### Within Job 23"
HISTORICAL_HEADING = "### Job 23 against Jobs 17–22"


def print_openings(results, prior_dirs, pgn, f5k):
    print("\n## Shared openings\n")
    print("Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct "
          "FEN strings. The two tables cover every new-file pair and every new file against every prior measurement.\n")
    known = {
        name: (row.status, (row.games // 2, fens) if fens is not None else None)
        for name, (row, _, fens) in {**results, "Job 22 F5k": f5k}.items()
    }
    historic = {}
    for job, names in PRIOR.items():
        for name in names:
            label = f"Job {job} {name}"
            historic[label] = (known[label] if label in known
                               else historical_openings(prior_dirs[job], name, pgn))
    all_files = {**{name: known[name] for name in results}, **historic}

    def label(name):
        status, _ = all_files[name]
        return name if status == "complete" else f"{name} (incomplete)"

    def share(left, right):
        a, b = all_files[left][1], all_files[right][1]
        return len(a[1] & b[1]) if a is not None and b is not None else "n/a"

    print(f"{label('Job 22 F5k')} and {label('F5kr')} distinct shared exact FENs = {share('Job 22 F5k', 'F5kr')}.\n")
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
    if len(MATCHES) != 7 or len(historic) != 33 or "Job 20 F7k" not in historic:
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


EVALSWING_NAMES = {
    17: ("X400r", "E24kr", "X400m3", "X100m3", "E48k", "X400w"),
    18: ("E48kr", "D48v24", "E64k", "X400k48", "X100k48", "E48t", "E24t"),
    19: ("E64kr", "E48tr", "E64t", "E48w"),
    20: ("E64tr",),
    21: ("E64tr2", "E64w"),
    22: ("E64wr",),
    23: ("M128k", "X400k", "M96k", "M128w"),
}
EVALSWING_POOLS = (
    (17, "loss", ((16, "X400"), (17, "X400r"))),
    (17, "gain", ((16, "E24k"), (17, "E24kr"))),
    (18, "gain", ((17, "E48k"), (18, "E48kr"))),
    (19, "gain", ((18, "E64k"), (19, "E64kr"))),
    (19, "gain", ((18, "E48t"), (19, "E48tr"))),
    (21, "gain", ((19, "E64t"), (20, "E64tr"), (21, "E64tr2"))),
    (22, "gain", ((21, "E64w"), (22, "E64wr"))),
)


def old_metadata(directory, job, name, pca_sha):
    import analyze_matches16 as job16
    import analyze_matches17 as job17
    import analyze_matches18 as job18
    import analyze_matches19 as job19
    import analyze_matches20 as job20
    import analyze_matches21 as job21
    import analyze_matches22 as job22

    readers = {16: job16, 17: job17, 18: job18, 19: job19, 20: job20, 21: job21, 22: job22}
    reader = readers[job].read_meta
    meta, reason = reader(directory, name, pca_sha) if job >= 20 else reader(directory, name)
    if meta is None:
        raise ValueError(f"Job {job} {name}: historical comparison unavailable: {reason}")
    return meta


def read_eval_archive(directory, job, name, pgn, pca_sha):
    meta = old_metadata(directory, job, name, pca_sha)
    groups = parse_games(directory / f"{name}.pgn", pgn, exact_moves=False)
    raw_count = sum(map(len, groups.values()))
    (wins, losses, draws), penta, abnormal = tally_pairs(groups, exact_moves=False)
    games = 2 * sum(penta)
    if raw_count > meta["games_requested"] or max(groups, default=0) > meta["games_requested"] // 2:
        raise ValueError(f"Job {job} {name}: archive has excess games or rounds")
    if meta["status"] == "complete" and games != meta["games_requested"]:
        raise ValueError(f"Job {job} {name}: archive marked complete without all pairs")
    row = Match(
        name, meta["status"], raw_count, games, wins, losses, draws, penta, abnormal=abnormal,
        match_start=meta.get("match_start_utc"), match_end=meta.get("match_end_utc"),
        provenance=(meta["exe_sha256"], meta["fastchess_sha256"], meta["book_sha256"], tuple(meta["settings_b"])),
    )
    output = [
        item for item in summarized_output(directory / f"{name}.out")
        if (item["games"], item["wins"], item["losses"], item["draws"], item["penta"])
        == (games, wins, losses, draws, penta)
    ]
    exact = penta_estimate(penta, deterministic=bool(output))
    if output:
        report = output[-1]
        reported = report["elo"], report["margin"]
        if exact is None or any(abs(float(a - b)) > 0.0050001 for a, b in zip(reported, exact, strict=True)):
            raise ValueError(f"Job {job} {name}: printed Elo or interval differs from paired PGN reconstruction")
        row.elo, row.width = reported
    elif exact is not None:
        row.elo, row.width = exact
        row.note = "interval reconstructed from paired PGN counts"
    if meta["exe_sha256"] != ENGINE_SHA or meta["nodes_a"] != meta["nodes_b"]:
        raise ValueError(f"Job {job} {name}: wrong build or unmatched node budgets for Table Q")

    def option(side, name, default):
        prefix = f"setoption name {name} value "
        lines = [line.removeprefix(prefix) for line in meta[f"settings_{side}"] if line.startswith(prefix)]
        return lines[-1] if lines else default

    a = tuple(option("a", key, default) for key, default in (("EvalSwingMult", "0"), ("EvalSwingMax", "200")))
    b = tuple(option("b", key, default) for key, default in (("EvalSwingMult", "0"), ("EvalSwingMax", "200")))
    if a == b:
        raise ValueError(f"Job {job} {name}: identical EvalSwing settings on both sides")
    descriptor = (f"Job 4 ({ENGINE_SHA[:8]})", meta["nodes_a"], a, b)
    return row, descriptor, meta["seed"]


def job16_location(prior_dirs):
    root = prior_dirs[17].parent.parent
    for directory in (root / "job16/raw", root / "sol-job16/raw"):
        if (directory / "E24k.meta").is_file() and (directory / "X400.meta").is_file():
            return directory
    raise ValueError("missing Job 16 raw seed inputs required for the two Job 17 pools")


def print_table_q(results, prior_dirs, pgn, pca_sha, w_sha, job16_raw=None):
    directories = {16: job16_raw or job16_location(prior_dirs), **prior_dirs}
    scope = [(job, name) for job, names in EVALSWING_NAMES.items() for name in names]
    historical = [(16, "X400"), (16, "E24k"), *(key for key in scope if key[0] < 23)]
    values = {
        (job, name): read_eval_archive(directories[job], job, name, pgn, pca_sha)
        for job, name in historical
    }
    for _, name in (key for key in scope if key[0] == 23):
        _, seed, nodes, _, _, a, b, _ = MATCHES[name]
        values[23, name] = results[name][0], (f"W ({w_sha[:8]})", nodes, a, b), seed

    replication = {}
    pool_rows = []
    for job, direction, keys in EVALSWING_POOLS:
        items = [values[key] for key in keys]
        descriptor = items[0][1]
        if any(other != descriptor for _, other, _ in items):
            raise ValueError(f"Job {job} {keys}: pooled options, executable or node budgets differ")
        for (source_job, _), (row, _, _) in zip(keys, items, strict=True):
            verify_prior_cut(directories[source_job], row)
        *_, (fresh, _, _) = items
        if fresh.status != "complete":
            raise ValueError(f"Job {job} {fresh.name}: historical pool needs a complete fresh seed")
        # Table Q prints no move-identity statistic. The exact move comparison is reserved for Table P.
        pooled, _ = pool_results([(row, 0, None) for row, _, _ in items])
        check = replicated if direction == "gain" else replicated_loss
        result = check(fresh, pooled)
        verdict = f"yes ({direction})" if result is True else "no" if result is False else "unavailable"
        pool_rows.append((job, pooled, descriptor, tuple(seed for _, _, seed in items), verdict))
        for key in keys:
            replication[key] = f"{verdict}, in Job {job} pool"

    print("\n## Table Q. EvalSwing comparisons in Jobs 17–23\n")
    print("Both sides use PC20, built-in evaluation, Threads 1 and Hash 16. Each Mult and Max column reads A/B. "
          "Max 200 is the effective default when omitted. Each physical measurement appears once. Pools add raw "
          "pentanomial counts and list all contributing seed IDs, including the two Job 16 ingredients of Job 17 pools.\n")
    print("| Job | Comparison | Build | Node budget | Mult A/B | Max A/B | Games | Elo [95%] | Seeds | Replicated | Status |")
    print("|---:|---|---|---:|---|---|---:|---|---|---|---|")

    def render(job, row, descriptor, seeds, verdict):
        build, nodes, a, b = descriptor
        games = row.games if row.penta else "n/a"
        seed_list = ", ".join(map(str, seeds))
        seed_column = f"{len(seeds)} ({seed_list})" if row.games else f"0 measured (planned {seed_list})"
        print(f"| {job} | {row.name} | {build} | {nodes:,} | {a[0]}/{b[0]} | {a[1]}/{b[1]} | {games} | "
              f"{number(row.elo)} {interval(row.interval)} | {seed_column} | {verdict} | {match_status(row)} |")

    for (job, name) in scope:
        row, descriptor, seed = values[job, name]
        label = "one seed" if row.games else "unavailable"
        render(job, row, descriptor, (seed,), replication.get((job, name), label))
    for item in pool_rows:
        render(*item)


def table(raw, prior_dirs, pgn, forecasts, pca_sha, w_sha, job16_raw=None):
    results = gates(raw, pgn, pca_sha, w_sha)
    old = read_job22_match(prior_dirs[22], "F5k", pgn, pca_sha)
    if old[0].status != "complete":
        raise ValueError("the prior complete Job 22 F5k seed is unavailable")
    results.update((name, read_match(raw, name, pgn, pca_sha, w_sha)) for name in CANDIDATES)
    verify_slots(results)
    fresh = results["F5kr"]
    rows = [results[name][:2] for name in CANDIDATES]
    rows.append(old[:2])
    pooled = None
    if fresh[0].status == "complete":
        pooled = pool_results([old, fresh])
        rows.append(pooled)

    print_grades(results, forecasts)
    print_table_p(rows)
    print_openings(results, prior_dirs, pgn, old)
    print_table_q(results, prior_dirs, pgn, pca_sha, w_sha, job16_raw)
    print("\n## Declared verdict\n")
    print("F5kr, only if complete, gives F5k its verdict: REPLICATED (a loss) when F5kr alone gives Elo below 0 AND "
          "the pool of F5k and F5kr (pentanomial counts added) has a 95 % interval whose upper end is below 0.")
    print("M128k, X400k, M96k and M128w are exploratory, one seed each: no verdict, a row each; one whose 95 % interval "
          "lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.")
    print("A cut match gives no verdict.\n")
    if pooled is None:
        print(f"F5k verdict withheld. F5kr {match_status(fresh[0])}.")
    else:
        row = pooled[0]
        upper = row.interval[1] if row.interval is not None else None
        print(f"F5k REPLICATED {yes_no(replicated_loss(fresh[0], row))}. Fresh Elo {number(fresh[0].elo, digits=4)}, "
              f"pooled upper 95% bound {number(upper, digits=4)}. Evidence {match_status(row)}.")
    print("\n## What this check cannot see\n")
    print("The PC's own net, exe and tune; doses above 128; EvalSwingMax values other than 200 and 400; time controls.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("gates", "table"):
        option = modes.add_parser(mode)
        option.add_argument("raw", type=Path)
        option.add_argument("--pca-sha256", type=Path, required=True)
        option.add_argument("--w-sha256", type=Path, required=True)
        option.add_argument("--python-chess-dir", type=Path)
        if mode == "gates":
            option.add_argument("--only-k", action="store_true")
        else:
            option.add_argument("--job16-raw", type=Path)
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
    pca_sha = read_pca_sha(args.pca_sha256)
    w_sha = read_w_sha(args.w_sha256, pca_sha)
    if args.mode == "gates":
        gates(args.raw, pgn, pca_sha, w_sha, args.only_k)
    else:
        prior_dirs = {job: getattr(args, f"job{job}_raw") for job in PRIOR}
        table(args.raw, prior_dirs, pgn, read_prediction(args.prediction), pca_sha, w_sha, args.job16_raw)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
