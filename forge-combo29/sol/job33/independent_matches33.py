#!/usr/bin/env python3
"""Recount Job 33's games, verify the published bytes, and build POOL20."""

import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import sys
from unittest.mock import patch

import chess


HERE = Path(__file__).resolve().parent
for directory in (HERE.parent / "job32", HERE.parent / "sol-job32"):
    if (directory / "independent_matches32.py").is_file():
        sys.path.insert(0, str(directory))
        break
from independent_matches32 import (
    BOOK_SHA, FASTCHESS_SHA, FINISHED, GUARD_OPTION, HG_SHA, blob, digest, format_rating,
    pgn_results, settings, symmetric_elo, verify_command,
)
from independent_matches28 import opening_key


M6_COMMIT = "ec0dd36b04e4facc8279371f390a2367973f9ffa"
# Seed, pair cap, nodes for A/B, guards for A/B.
SCHEDULE = {
    "K23": (7331, 25, (20000, 20000), (0, 0)),
    "C23": (7332, 50, (40000, 80000), (0, 0)),
    "M7": (7333, 1000, (20000, 20000), (2, 0)),
    "M8": (7334, 250, (80000, 80000), (2, 0)),
    "M6": (7324, 1000, (20000, 20000), (2, 0)),
}


def canonical_key(fen):
    fields = fen.split()
    if fields[3] != "-" and not chess.Board(fen).has_legal_en_passant():
        fields[3] = "-"
    return opening_key(" ".join(fields))


def check_settings(meta, baseline, guards):
    expected = []
    for side, suffix, guard in zip("ab", ("", "_b"), guards, strict=True):
        declared = [option for option in baseline if not option.startswith("setoption name NullMateGuard ")]
        declared.append(f"setoption name NullMateGuard value {guard}")
        assert meta[f"settings_{side}"] == meta[f"preflight_settings_sent{suffix}"] == declared
        advertised, reply = meta[f"preflight_uci{suffix}"], meta[f"preflight_reply{suffix}"]
        assert advertised[-1:] == ["uciok"] and advertised.count(GUARD_OPTION) == 1
        assert reply[-1:] == ["readyok"]
        assert not any("unknown option" in line.lower() or "invalid value" in line.lower() for line in reply)
        expected.append(settings(declared))
    verify_command(meta, expected)


def check_match(root, name, baseline):
    raw = root / "raw"
    pgn, out, metadata = (raw / f"{name}.{suffix}" for suffix in ("pgn", "out", "meta"))
    if not metadata.is_file() or not metadata.stat().st_size:
        return None
    meta = json.loads(metadata.read_bytes())
    if meta["status"] not in ("complete", "interrupted"):
        print(f"{name} {meta['status']} | no usable completed-pair archive")
        return None
    manifest_path = root / "openings/manifest.json"
    cell = json.loads(manifest_path.read_bytes())["cells"][name]
    seed, pairs_requested, nodes, guards = SCHEDULE[name]
    assert meta["match"] == name and (meta["engine_a"], meta["engine_b"]) == ("A", "B")
    assert (meta["seed"], meta["games_requested"], (meta["nodes_a"], meta["nodes_b"])) == (seed, pairs_requested * 2, nodes)
    assert meta["exe_sha256"] == meta["exe_sha256_b"] == HG_SHA and meta["external_net_file"] is None
    assert meta["evaluation"] == "Forge embedded evaluation" and meta["fastchess_sha256"] == FASTCHESS_SHA
    assert meta["book_source_sha256"] == BOOK_SHA and meta["book_manifest_sha256"] == digest(manifest_path)
    assert (meta["book_sha256"], meta["book_openings_count"]) == (cell["sha256"], pairs_requested)
    assert meta["rating_interval_pairs"] == 1
    check_settings(meta, baseline, guards)
    assert digest(pgn) == meta["pgn_sha256"] and digest(out) == meta["out_sha256"]

    book = root / "openings" / cell["file"]
    assert Path(meta["book"]).name == book.name and digest(book) == cell["sha256"]
    positions = book.read_text().splitlines()
    assert list(map(opening_key, positions)) == cell["fen_keys_sha256"]
    reserved = set(map(canonical_key, positions))
    assert len(reserved) == pairs_requested
    with patch("independent_matches28.opening_key", canonical_key):
        games, unresolved, results, used, scores, penta, same, even_same = pgn_results(pgn, reserved)
    pairs = sum(penta)
    logs = FINISHED.findall(out.read_text())
    assert 2 * pairs <= games <= pairs_requested * 2 and len(logs) <= pairs_requested * 2
    assert len({index for index, *_ in logs}) == len(logs)
    log_results = Counter((white, black, score) for _, white, black, score in logs)
    assert not results - log_results
    if meta["status"] == "complete":
        assert meta["fastchess_exit"] == 0
        assert (games, pairs, unresolved, used, results) == (pairs_requested * 2, pairs_requested, 0, reserved, log_results)

    rating = symmetric_elo(penta)
    if name == "K23":
        assert meta["status"] == "complete" and same == even_same == pairs == 25
    if name == "C23":
        assert meta["status"] == "complete" and rating is not None and rating[2] < 0
    better, worse = sum(penta[3:]), sum(penta[:2])
    unequal = better + worse
    p = min(Fraction(1), Fraction(2 * sum(comb(unequal, index) for index in range(min(better, worse) + 1)), 2 ** unequal))
    reading = "unavailable" if rating is None else "BETTER" if rating[1] > 0 else "WORSE" if rating[2] < 0 else "LEVEL"
    print(f"{name} {meta['status']} | HG PC20, embedded AL1 s198, Keep 1024, guards {guards[0]}/{guards[1]}, "
          f"nodes A/B {nodes[0]}/{nodes[1]}, seed {seed} | {2 * pairs} games / {pairs} complete pairs | "
          f"{games - 2 * pairs} PGN games excluded ({unresolved} unresolved) | A W-L-D {scores[2]}-{scores[0]}-{scores[1]} | "
          f"penta {penta} | {same}/{pairs} exact ordered UCI lists ({even_same} even) | {better} better / {worse} worse | "
          f"two-sided exact p {float(p):.10g} | {format_rating(rating)} | {reading}")
    print(f"Raw PGN SHA-256 {meta['pgn_sha256']}, fastchess output SHA-256 {meta['out_sha256']}.")
    return meta["status"], penta, rating, used


def check_publication(repo, root, name, job, commit):
    path = f"forge-combo29/sol/job{job}"
    manifest = blob(repo, commit, f"{path}/openings/manifest.json")
    assert manifest == (root / "openings/manifest.json").read_bytes()
    for suffix in ("out", "meta"):
        filename = f"{name}.{suffix}"
        published = blob(repo, commit, f"{path}/raw/{filename}")
        assert published == (root / "raw" / filename).read_bytes()
        print(f"{commit} {filename} equals scratch ({len(published):,} bytes).")
    filename = f"{name}.pgn"
    original = (root / "raw" / filename).read_bytes()
    if len(original) <= 20_000_000:
        assert original == blob(repo, commit, f"{path}/raw/{filename}")
        print(f"{commit} {filename} equals scratch ({len(original):,} bytes).")
        return
    split = json.loads(blob(repo, commit, f"{path}/raw/{filename}.manifest.json"))
    offset = 0
    for part in split["parts"]:
        published = blob(repo, commit, f"{path}/raw/{part['file']}")
        assert 0 < len(published) == part["bytes"] <= 20_000_000
        assert sha256(published).hexdigest() == part["sha256"]
        assert published == original[offset:offset + len(published)]
        print(f"{commit} {part['file']} equals original slice ({len(published):,} bytes).")
        offset += len(published)
    assert offset == len(original) == split["original"]["bytes"]
    assert sha256(original).hexdigest() == split["original"]["sha256"]
    print(f"All {offset:,} {name} PGN bytes reassemble in manifest order. "
          f"Reported {split['original']['complete_pairs']:,} complete pairs and {split['rounds_split_across_parts']} split pairs.")


def pool20(repo, work, baseline):
    old_root, new_root = work / "sol-job32", work / "sol-job33"
    old = check_match(old_root, "M6", baseline)
    assert old is not None
    check_publication(repo, old_root, "M6", 32, M6_COMMIT)
    new = check_match(new_root, "M7", baseline)
    if new is not None:
        assert not old[3] & new[3], "M6/M7 canonical opening overlap"
        check_publication(repo, new_root, "M7", 33, (new_root / "M7.commit").read_text().strip())
        print("Canonical M6/M7 opening overlap: zero.")

    rows = (("M6", old), ("M7", new))
    included = [(name, result[1]) for name, result in rows if result is not None and result[0] == "complete"]
    excluded = [f"{name} ({result[0] if result is not None else 'missing'})" for name, result in rows
                if result is None or result[0] != "complete"]
    penta = [sum(row[index] for _, row in included) for index in range(5)]
    rating = symmetric_elo(penta)
    standalone_m7 = new[2][0] if new and new[2] is not None else None
    reading = "LEVEL"
    if rating and standalone_m7 is not None:
        if rating[1] > 0 and standalone_m7 > 0:
            reading = "BETTER"
        elif rating[2] < 0 and standalone_m7 < 0:
            reading = "WORSE"
    print(f"POOL20 M6/M7 | HG PC20, AL1 s198, Keep 1024, guards 2/0, 20,000 nodes | "
          f"included {', '.join(name for name, _ in included) or 'none'} | "
          f"excluded {', '.join(excluded) or 'none'} | {sum(penta):,} pairs | penta {penta} | {format_rating(rating)} | {reading}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match", choices=(*SCHEDULE, "pool20"))
    parser.add_argument("--published", action="store_true")
    parser.add_argument("--work", type=Path, default=HERE.parent)
    parser.add_argument("--repo", type=Path, default=Path("/workspace/work/sol-job1/repo"))
    args = parser.parse_args()
    ref = json.loads(blob(args.repo, M6_COMMIT, "forge-combo29/sol/job32/raw/M6.meta"))
    baseline = ref["settings_b"]
    assert settings(baseline)["HistoryAgeKeep"] == "1024" and settings(baseline)["NullMateGuard"] == "0"
    if args.match == "pool20":
        pool20(args.repo, args.work, baseline)
        return
    job = 32 if args.match == "M6" else 33
    root = args.work / f"sol-job{job}"
    assert check_match(root, args.match, baseline) is not None
    if args.published:
        commit = M6_COMMIT if job == 32 else (root / f"{args.match}.commit").read_text().strip()
        check_publication(args.repo, root, args.match, job, commit)


if __name__ == "__main__":
    main()
