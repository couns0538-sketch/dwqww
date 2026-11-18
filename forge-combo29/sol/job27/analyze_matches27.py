#!/usr/bin/env python3
"""Audit paired Forge PGNs and exact sign and Fisher tests for Job 27."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
for job26 in (HERE.parent / "job26", HERE.parent / "sol-job26"):
    if (job26 / "analyze_matches26.py").is_file():
        sys.path.insert(0, str(job26))
        break
else:
    raise SystemExit("Job 26's analyze_matches26.py is missing from adjacent job26 or sol-job26.")

from analyze_matches26 import (
    BOOK_SHA, ENGINE_SHA, FASTCHESS_REVISION, HEX, SOURCE_POSITIONS, check_match_preflight,
    digest, fen4, fen_key, interval, number, penta_estimate, pgn_module, summarized_output,
)

ALPHA = Fraction(1, 20)
HISTORICAL_COUNTS = (8, 9, 6, 6, 7, 9, 7, 7, 6, 7)
EVENTS = re.compile(rb'(?m)(?=^\[Event ")')
HEADER = re.compile(rb'^\[([A-Za-z0-9]+) "(.*)"\]$')
COMMENT = re.compile(rb'\{[^}]*\}')
MOVENUM = re.compile(rb'[0-9]+\.{1,3}')
SAN = re.compile(rb'(?:O-O(?:-O)?|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?)[+#]?')
WHITE_POINTS = {b"1-0": 2, b"0-1": 0, b"1/2-1/2": 1}
NEW_MATCHES = {
    # games, seed, options appended to PC20 on A/B, workers
    "K16": (100, 7271, (), (), 4),
    "D2s": (8000, 7272, (("DrawJitter", "8"),), (("DrawJitter", "0"),), 4),
}


@dataclass
class Paired:
    name: str
    status: str
    raw_games: int
    pairs: int
    wins: int
    losses: int
    draws: int
    penta: tuple
    same_moves: int
    equal_same: int
    equal_different: int
    fens: set
    paired_fens: set
    elo: Fraction | None = None
    width: Fraction | None = None
    note: str = ""

    @property
    def better(self):
        return sum(self.penta[3:])

    @property
    def worse(self):
        return sum(self.penta[:2])

    @property
    def bounds(self):
        return None if self.elo is None else (self.elo - self.width, self.elo + self.width)


def binomial_lower(n, k):
    choose = subtotal = 1
    for i in range(1, k + 1):
        choose = choose * (n - i + 1) // i
        subtotal += choose
    return Fraction(subtotal, 1 << n)


def sign_test(better, worse, one_sided=False):
    n = better + worse
    if one_sided:
        return binomial_lower(n, worse)
    return min(Fraction(1), 2 * binomial_lower(n, min(better, worse)))


def fisher_two_sided(a, b, c, d):
    left, right, successes = a + b, c + d, a + c
    observed = comb(left, a) * comb(right, c)
    favorable = 0
    for x in range(max(0, successes - right), min(left, successes) + 1):
        weight = comb(left, x) * comb(right, successes - x)
        if weight <= observed:
            favorable += weight
    return Fraction(favorable, comb(left + right, successes))


def p_text(value, digits=6):
    if value == 1:
        return "1.000"
    with localcontext() as context:
        context.prec = digits + 8
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
        return format(decimal, f".{digits}g")


def parse_pgn(path, expected_sha):
    """Read the official fastchess PGN dialect and compare its canonical SAN tokens."""
    original = path.read_bytes()
    if sha256(original).hexdigest() != expected_sha:
        raise ValueError(f"{path}: PGN SHA-256 differs from the sidecar")
    contents = original.replace(b"\r\n", b"\n")
    groups, fens = defaultdict(list), set()
    raw_games = 0
    for frame in EVENTS.split(contents):
        if not frame.strip():
            continue
        tags, gap, movetext = frame.partition(b"\n\n")
        if not gap:
            raise ValueError(f"{path}: PGN record has no header separator")
        headers = {}
        for line in tags.splitlines():
            field = HEADER.fullmatch(line)
            if field is None or field[1] in headers:
                raise ValueError(f"{path}: malformed or repeated PGN tag")
            headers[field[1]] = field[2]
        raw_games += 1
        round_ = int(headers[b"Round"])
        white, black = headers[b"White"], headers[b"Black"]
        if round_ < 1 or (white, black) not in ((b"A", b"B"), (b"B", b"A")):
            raise ValueError(f"{path}: nonpositive round or unexpected engine names")
        start = headers[b"FEN"].decode("utf-8")
        fens.add(start)
        result = headers[b"Result"]
        if result == b"*":
            continue
        points = WHITE_POINTS[result]
        if white == b"B":
            points = 2 - points
        tokens = COMMENT.sub(b" ", movetext).split()
        if not tokens or tokens[-1] != result:
            raise ValueError(f"{path}: PGN result and final move token disagree in round {round_}")
        moves = tuple(token for token in tokens[:-1] if not MOVENUM.fullmatch(token))
        if len(moves) != int(headers[b"PlyCount"]) or any(not SAN.fullmatch(token) for token in moves):
            raise ValueError(f"{path}: unsupported canonical SAN or PlyCount mismatch in round {round_}")
        groups[round_].append((white, start, points, moves))
    return groups, fens, raw_games


def summarize(raw, name, meta, pgn_path=None):
    pgn_path = pgn_path or raw / f"{name}.pgn"
    groups, fens, raw_games = parse_pgn(pgn_path, meta["pgn_sha256"])
    penta = [0] * 5
    scores = [0, 0, 0]
    paired_fens = set()
    same = equal_same = 0
    for round_, games in groups.items():
        if len(games) == 1:
            continue
        if len(games) != 2:
            raise ValueError(f"{pgn_path}: round {round_} includes more than two games")
        (white1, fen1, points1, moves1), (white2, fen2, points2, moves2) = games
        if white1 == white2 or fen1 != fen2:
            raise ValueError(f"{pgn_path}: round {round_} lacks reversed colors or a shared opening")
        paired_fens.add(fen1)
        score = points1 + points2
        penta[score] += 1
        scores[points1] += 1
        scores[points2] += 1
        identical = moves1 == moves2
        same += identical
        equal_same += identical and score == 2
    pairs = sum(penta)
    requested = meta["games_requested"]
    if raw_games > requested or max(groups, default=0) > requested // 2:
        raise ValueError(f"{pgn_path}: excess games or rounds")
    if meta["status"] == "complete" and (2 * pairs != requested or raw_games != requested):
        raise ValueError(f"{pgn_path}: finished match lacks scheduled complete pairs")
    row = Paired(name, meta["status"], raw_games, pairs, scores[2], scores[0], scores[1], tuple(penta),
                 same, equal_same, penta[2] - equal_same, fens, paired_fens)
    out = raw / f"{name}.out"
    if digest(out) != meta["out_sha256"]:
        raise ValueError(f"{out}: SHA-256 differs from the sidecar")
    summaries = [
        block for block in summarized_output(out)
        if (block["games"], block["wins"], block["losses"], block["draws"], block["penta"])
        == (2 * pairs, row.wins, row.losses, row.draws, row.penta)
    ]
    recomputed = penta_estimate(row.penta, deterministic=bool(summaries))
    if summaries:
        last = summaries[-1]
        observed = last["elo"], last["margin"]
        if recomputed is None or any(abs(float(a - b)) > 0.0050001 for a, b in zip(observed, recomputed, strict=True)):
            raise ValueError(f"{name}: official symmetric interval differs from paired PGN reconstruction")
        row.elo, row.width = observed
    elif recomputed is not None:
        row.elo, row.width = recomputed
        row.note = "interval reconstructed from final paired counts"
    else:
        row.note = "interval unavailable"
    return row


def old_metadata(raw, name):
    path = raw / f"{name}.meta"
    meta = json.loads(path.read_text(encoding="utf-8"))
    if (meta["match"] != name or meta["status"] not in ("complete", "interrupted")
            or meta["engine_a"] != "A" or meta["engine_b"] != "B"
            or meta["fastchess_revision"] != FASTCHESS_REVISION):
        raise ValueError(f"{path}: unexpected recorded match identity or status")
    return meta


def known_answers(rows):
    first, fresh = rows[24, "D2"], rows[25, "D2r"]
    observed = (first.better, first.worse, fresh.better, fresh.worse)
    if observed != (12, 2, 5, 4):
        raise ValueError(f"D2 and D2r known counts differ: {observed}")
    probabilities = (
        sign_test(12, 2), sign_test(5, 4), sign_test(17, 6), fisher_two_sided(12, 2, 5, 4),
    )
    expected = ("0.0129", "1.000", "0.0347", "0.162")
    if (readback := tuple(p_text(value, 3) for value in probabilities)) != expected:
        raise ValueError(f"known exact probabilities differ: {readback}")
    return probabilities


def status(row):
    if row.status == "complete":
        description = "complete"
    elif row.status == "interrupted":
        description = "cut (incomplete)"
    else:
        description = row.status
    if row.raw_games > 2 * row.pairs:
        description += f", {row.raw_games - 2 * row.pairs} unpaired or unfinished excluded"
    if row.note:
        description += f", {row.note}"
    return description


def describe_settings(meta):
    from run_match16 import BASE

    baseline = [f"setoption name {name} value {value}" for name, value in BASE]
    a, b = meta["settings_a"], meta["settings_b"]
    if a[:len(baseline)] != baseline or b[:len(baseline)] != baseline:
        raise ValueError(f"{meta['match']}: historical PC20 options differ")

    def options(lines):
        return dict(line.removeprefix("setoption name ").split(" value ", 1) for line in lines)

    effective_a, effective_b = options(a), options(b)
    extras = dict.fromkeys((*options(a[len(baseline):]), *options(b[len(baseline):])))
    defaults = {}
    for line in meta["preflight_uci"]:
        if support := re.match(r"option name (.*?) type \w+ default (\S+)", line):
            defaults[support[1]] = support[2]
    return ", ".join(
        f"{name} {effective_a.get(name, defaults.get(name, 'default'))}/{effective_b.get(name, defaults.get(name, 'default'))}"
        for name in extras
    ) or "PC20"


def part_a(history_root):
    rows, metadata = {}, {}
    for job, count in zip(range(17, 27), HISTORICAL_COUNTS, strict=True):
        raw = history_root / f"job{job}" / "raw"
        matches = sorted(path.stem for path in raw.glob("*.pgn"))
        if len(matches) != count:
            raise ValueError(f"{raw}: expected {count} historical matches, found {len(matches)}")
        for name in matches:
            meta = old_metadata(raw, name)
            rows[job, name] = summarize(raw, name, meta)
            metadata[job, name] = meta

    known = known_answers(rows)
    print("## Part A. Exact historical pair tests\n")
    print("Jobs 17–26 use PC20, embedded evaluation, Threads 1 and Hash 16. The interval is symmetric "
          "pentanomial Elo ± halfwidth. The exact two-sided sign test uses the counts above and below 1–1. "
          "Equal-score pairs are split into identical and differing canonical move sequences. Cut rows use "
          "their completed color-reversed pairs.\n")
    print(f"Known answers passed. D2 12 better / 2 worse, p = {p_text(known[0], 3)}. D2r 5 / 4, "
          f"p = {p_text(known[1], 3)}. Their pool 17 / 6, p = {p_text(known[2], 3)}. "
          f"Two-sided Fisher p = {p_text(known[3], 3)}.\n")
    print("| Job | Match | Build SHA prefix | Nodes A/B | Explicit options A/B | Status | Pairs | Better | Worse | "
          "1–1 same | 1–1 different | Elo [95%] | Exact two-sided p | Discordance |")
    print("|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---|---:|---|")
    flagged = []
    for (job, name), row in rows.items():
        meta = metadata[job, name]
        settings = describe_settings(meta)
        nodes = f"{meta['nodes_a']:,}/{meta['nodes_b']:,}"
        p = sign_test(row.better, row.worse)
        disagreement = None
        if row.bounds is not None:
            lower, upper = row.bounds
            excludes = lower > 0 or upper < 0
            if excludes != (p < ALPHA):
                disagreement = "interval only" if excludes else "exact sign test only"
                flagged.append((job, name, disagreement))
        print(f"| {job} | {name} | {meta['exe_sha256'][:8]} | {nodes} | {settings} | {status(row)} | {row.pairs} | "
              f"{row.better} | {row.worse} | {row.equal_same} | {row.equal_different} | "
              f"{number(row.elo)} {interval(row.bounds)} | {p_text(p)} | "
              f"{disagreement or ('none' if row.bounds is not None else 'interval unavailable')} |")
    print(f"\nDiscordances **{len(flagged)} of {len(rows)}**.")
    for job, name, disagreement in flagged:
        print(f"- Job {job} {name}, {disagreement}.")
    return rows


def read_manifest(path):
    contents = path.read_bytes()
    manifest = json.loads(contents)
    source = manifest["source"]
    if (source.get("sha256"), source.get("positions")) != (BOOK_SHA, SOURCE_POSITIONS):
        raise ValueError(f"{path}: official opening book identity or size differs")
    if manifest["cells"].keys() != NEW_MATCHES.keys():
        raise ValueError(f"{path}: derived book cells differ from the Job 27 schedule")
    keys, lines = set(), set()
    for name, (games, seed, _, _, _) in NEW_MATCHES.items():
        cell = manifest["cells"][name]
        if ((cell["file"], cell["seed"], cell["count"]) != (f"{name}.epd", seed, games // 2)
                or not HEX.fullmatch(cell["sha256"])):
            raise ValueError(f"{path}: {name} derived book identity differs")
        selected, openings = cell["source_line_numbers"], cell["fen_keys_sha256"]
        if (len(selected) != games // 2 or len(set(selected)) != games // 2 or lines.intersection(selected)
                or any(not 1 <= line <= SOURCE_POSITIONS for line in selected)):
            raise ValueError(f"{path}: {name} has invalid or repeated official book line numbers")
        if (len(openings) != games // 2 or len(set(openings)) != games // 2 or keys.intersection(openings)
                or any(not HEX.fullmatch(value) for value in openings)):
            raise ValueError(f"{path}: {name} has invalid or repeated FEN keys")
        lines.update(selected)
        keys.update(openings)
    proof = manifest["verification"]
    counts = ("retained_positions", "distinct_exact_fen", "distinct_first_four_field_keys")
    overlaps = ("prior_exact_fen_overlap", "prior_first_four_field_overlap", "internal_overlap")
    if (any(proof.get(key) != len(keys) for key in counts)
            or any(proof.get(key) != 0 for key in overlaps)
            or proof.get("epd_readback_matches_source_rows") is not True):
        raise ValueError(f"{path}: manifest lacks successful official EPD disjointness verification")
    return manifest, sha256(contents).hexdigest()


def new_match(raw, name, receipt, pgn_path=None):
    manifest, receipt_sha = receipt
    path = raw / f"{name}.meta"
    if not path.is_file() or not path.stat().st_size:
        return None, "no final match sidecar"
    meta = json.loads(path.read_text(encoding="utf-8"))
    games, seed, a_opts, b_opts, workers = NEW_MATCHES[name]
    variant = {"name": "DrawJitter", "value": "8"} if name == "D2s" else None
    expected = (name, games, seed, 2000, 2000, workers, "A", "B", variant, 300)
    keys = ("match", "games_requested", "seed", "nodes_a", "nodes_b", "concurrency",
            "engine_a", "engine_b", "variant", "maxmoves")
    if tuple(meta.get(key) for key in keys) != expected:
        raise ValueError(f"{path}: wrong match identity, fixed node budgets or worker count")
    cell = manifest["cells"][name]
    provenance = (
        meta["exe_sha256"], meta["fastchess_revision"], meta["book_sha256"], meta["book_source_sha256"],
        meta["book_manifest_sha256"], meta["book_openings_count"], meta["book_source_positions"], Path(meta["book"]).name,
    )
    pins = (ENGINE_SHA, FASTCHESS_REVISION, cell["sha256"], BOOK_SHA, receipt_sha, cell["count"],
            SOURCE_POSITIONS, cell["file"])
    if provenance != pins:
        raise ValueError(f"{path}: executable, fastchess or derived book provenance differs")
    if name == "D2s" and (meta["rating_interval_pairs"] != 1 or meta["fastchess_command"][-2:] != ["-ratinginterval", "1"]):
        raise ValueError(f"{path}: missing one-pair rating output cadence")
    if meta["status"] == "refused":
        return None, f"refused: {meta.get('error', 'option refusal')}"
    if not meta.get("pgn_sha256") or not meta.get("out_sha256"):
        return None, f"{meta['status']}: saved PGN or rating output unavailable"
    if meta["status"] == "complete" and meta.get("fastchess_exit") != 0:
        raise ValueError(f"{path}: complete match has a nonzero exit code")
    if meta["status"] not in ("complete", "interrupted"):
        raise ValueError(f"{path}: unexpected result status {meta['status']}")
    check_match_preflight(meta, a_opts, b_opts)
    row = summarize(raw, name, meta, pgn_path)
    reserved = set(cell["fen_keys_sha256"])
    played = set(map(fen_key, row.fens))
    if not played <= reserved or len(set(map(fen_key, row.paired_fens))) != row.pairs:
        raise ValueError(f"{path}: a game used an unassigned opening or a pair repeated an opening")
    if row.status == "complete" and played != reserved:
        raise ValueError(f"{path}: complete match did not play every assigned opening")
    return row, ""


def checked_k16(raw, receipt):
    row, reason = new_match(raw, "K16", receipt)
    if (row is None or row.status != "complete" or row.pairs != 50 or row.same_moves != 50
            or row.penta != (0, 0, 50, 0, 0) or row.elo != 0 or row.width != 0):
        observed = reason or (status(row) if row is not None else "result unavailable")
        raise ValueError(f"K16 failed: {observed}, requires 50 exact 1–1 pairs and zero Elo")
    return row


def gates(raw, receipt):
    row = checked_k16(raw, receipt)
    print("## K16 known-answer control\n")
    print(f"K16 PASS. Job 4 {ENGINE_SHA[:8]}, PC20, embedded evaluation, Threads 1, Hash 16, 2,000 nodes "
          f"per move on both sides. All {row.pairs} fresh reversed-color pairs had exactly the same moves "
          f"and scored 1–1. W-L-D {row.wins}-{row.losses}-{row.draws}, pentanomial {row.penta}, "
          f"Elo {number(row.elo)} {interval(row.bounds)}.")
    return row


def verify_history(root, receipt):
    manifest, _ = receipt
    history = manifest["historical"]
    expected = {item["path"]: item for item in history["files"]}
    found = set()
    for path in root.glob("job*/raw/**/*.pgn"):
        relative = path.relative_to(root)
        job = relative.parts[0].removeprefix("job")
        if job.isdecimal() and int(job) < 27:
            found.add(relative.as_posix())
    if len(expected) != history["pgn_count"] or found != expected.keys():
        raise ValueError("freshness replay cannot account for every prior PGN in the frozen manifest")
    tags, total = set(), 0
    for name, expected_file in expected.items():
        path = root / name
        data = path.read_bytes()
        if sha256(data).hexdigest() != expected_file["sha256"]:
            raise ValueError(f"{path}: archived PGN checksum differs")
        matches = re.findall(rb'(?m)^\[FEN "([^"]+)"\]\r?$', data)
        if len(matches) != expected_file["fen_tags"]:
            raise ValueError(f"{path}: archived FEN tag count differs")
        total += len(matches)
        tags.update(record.decode("utf-8") for record in matches)
    keys = set(map(fen4, tags))
    if (total, len(tags), len(keys)) != (history["fen_tags"], history["distinct_exact"], history["distinct_first_four"]):
        raise ValueError("archived FEN replay differs from the frozen manifest")
    reserved = {key for item in manifest["cells"].values() for key in item["fen_keys_sha256"]}
    if reserved.intersection(map(fen_key, keys)):
        raise ValueError("a Job 27 reserved opening occurs in the historical PGNs")
    return len(expected), total, len(reserved)


def read_prediction(path):
    forecast = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if not fields:
            continue
        name = fields[0].upper()
        if name == "D2S":
            if len(fields) != 5 or name in forecast:
                raise ValueError(f"{path}: expected D2s BETTER_MIN BETTER_MAX WORSE_MIN WORSE_MAX")
            a, b, c, d = map(int, fields[1:])
            if not (0 <= a <= b <= 4000 and 0 <= c <= d <= 4000):
                raise ValueError(f"{path}: each forecast range must lie within 0–4,000 pairs")
            forecast[name] = (a, b), (c, d)
        elif name == "CONFIRMED":
            if len(fields) != 2 or name in forecast or fields[1].lower() not in ("yes", "no"):
                raise ValueError(f"{path}: expected one CONFIRMED yes|no forecast")
            forecast[name] = fields[1].lower() == "yes"
    if forecast.keys() != {"D2S", "CONFIRMED"}:
        raise ValueError(f"{path}: missing D2s ranges or CONFIRMED forecast")
    return forecast


def print_grades(forecast, row, confirmed):
    print("## Prediction grades\n")
    print("The inclusive ranges are compared with the complete pairs actually played. A cut remains marked as cut.\n")
    print("| Forecast | Predicted | Observed | Grade |")
    print("|---|---|---|---|")
    for label, (low, high), observed in (
        ("D2s better pairs", forecast["D2S"][0], row.better if row is not None and row.pairs else None),
        ("D2s worse pairs", forecast["D2S"][1], row.worse if row is not None and row.pairs else None),
    ):
        grade = "ungraded" if observed is None else "met" if low <= observed <= high else "missed"
        print(f"| {label} | [{low}, {high}] | {observed if observed is not None else 'n/a'} | {grade} |")
    choice = {True: "CONFIRMED", False: "NOT CONFIRMED", None: "not done"}
    prediction = forecast["CONFIRMED"]
    grade = "ungraded" if confirmed is None else "met" if confirmed == prediction else "missed"
    print(f"| D2s exact verdict | {choice[prediction]} | {choice[confirmed]} | {grade} |")


def part_b(raw, history_root, receipt, forecast, pgn_path=None):
    checked_k16(raw, receipt)
    prior = {}
    for job, name in ((24, "D2"), (25, "D2r")):
        earlier_raw = history_root / f"job{job}" / "raw"
        prior[job, name] = summarize(earlier_raw, name, old_metadata(earlier_raw, name))
    known_answers(prior)
    files, tags, reserved = verify_history(history_root, receipt)
    row, reason = new_match(raw, "D2s", receipt, pgn_path)
    exact = sign_test(row.better, row.worse, one_sided=True) if row is not None and row.pairs else None
    confirmed = exact < ALPHA if exact is not None else None
    print_grades(forecast, row, confirmed)
    print("\n## Part B. D2s exact fresh-seed test\n")
    print(f"The {reserved:,} assigned openings for K16 and D2s are disjoint from {tags:,} historical FEN tags "
          f"in {files} earlier checksum-verified PGNs. Every recorded game used its own assigned opening set.\n")
    if row is None:
        print(f"D2s not done. {reason}.")
    elif not row.pairs:
        print(f"D2s not done. {status(row)}. No complete pair was available.")
    else:
        print("D2s used Job 4, PC20, embedded evaluation, Threads 1, Hash 16, 2,000 nodes per move and "
              "DrawJitter 8 for A and 0 for B. Only complete reversed-color pairs enter the exact test.\n")
        print("| Match | Status | Games | W-L-D | Pentanomial | Same move pairs / played | Better | Worse | "
              "1–1 same | 1–1 different | Elo [95%] |")
        print("|---|---|---:|---|---|---|---:|---:|---:|---:|---|")
        print(f"| D2s | {status(row)} | {2 * row.pairs} | {row.wins}-{row.losses}-{row.draws} | "
              f"{', '.join(map(str, row.penta))} | {row.same_moves}/{row.pairs} | {row.better} | {row.worse} | "
              f"{row.equal_same} | {row.equal_different} | {number(row.elo)} {interval(row.bounds)} |")
        print(f"\nThe one-sided exact sign-test p is **{p_text(exact)}** for at least {row.better} better pairs "
              f"out of {row.better + row.worse} unequal pairs. "
              f"D2s **{'CONFIRMED' if confirmed else 'NOT CONFIRMED'}** at p < 0.05.\n")
        old_better = sum(value.better for value in prior.values())
        old_worse = sum(value.worse for value in prior.values())
        all_better, all_worse = old_better + row.better, old_worse + row.worse
        pooled = sign_test(all_better, all_worse)
        fisher = fisher_two_sided(row.better, row.worse, old_better, old_worse)
        print(f"Descriptive pool D2 + D2r + D2s gives {all_better} better / {all_worse} worse, "
              f"exact two-sided sign-test p = {p_text(pooled)}.")
        print(f"Two-sided Fisher for D2s {row.better} / {row.worse} against D2 + D2r "
              f"{old_better} / {old_worse} gives p = {p_text(fisher)}.")
    print("\n## What this check cannot see\n")
    print("The PC's engine, net and settings (your tree plays its embedded evaluation); budgets other than 2,000 nodes.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("part-a", "gates", "part-b"):
        sub = modes.add_parser(mode)
        sub.add_argument("--python-chess-dir", type=Path)
        if mode != "part-a":
            sub.add_argument("raw", type=Path)
            sub.add_argument("--manifest", type=Path, required=True)
        if mode != "gates":
            sub.add_argument("--history-root", type=Path, required=True)
        if mode == "part-b":
            sub.add_argument("--prediction", type=Path, required=True)
            sub.add_argument("--d2s-pgn", type=Path)
    args = parser.parse_args()
    pgn_module(args.python_chess_dir)
    if args.mode == "part-a":
        part_a(args.history_root)
    elif args.mode == "gates":
        gates(args.raw, read_manifest(args.manifest))
    else:
        part_b(args.raw, args.history_root, read_manifest(args.manifest), read_prediction(args.prediction), args.d2s_pgn)


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise SystemExit(str(error))
