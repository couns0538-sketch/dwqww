#!/usr/bin/env python3
"""Recount Job 32's games and compare committed evidence with scratch bytes."""

import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from math import comb
from pathlib import Path
from subprocess import check_output
import sys

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "job31", HERE.parent / "sol-job31"):
    if (candidate / "independent_matches31.py").is_file():
        sys.path.insert(0, str(candidate))
        break
from independent_matches31 import (
    BOOK_SHA, FASTCHESS_SHA, FINISHED, digest, format_rating, pgn_results,
    settings, symmetric_elo, verify_command,
)

HG_SHA = "626cd562ddd9a64364d45adb92f7cd21f5bd8cbae5a24ca5908e8bd5585f8d97"
MANIFEST_SHA = "b7a888b21bcb6b571dd540e08183165bd0e4672980d053ae5df3f82a6a29abc7"
C21_COMMIT = "9246482a0c0f8f68e1447a84d8649912d921b51f"
GUARD_OPTION = "option name NullMateGuard type spin default 0 min 0 max 2"
# Seed, scheduled pairs, A/B nodes, A/B guards.
SCHEDULE = {
    "K22": (7321, 50, (2000, 2000), (0, 0)),
    "C22": (7322, 100, (1000, 2000), (0, 0)),
    "M5": (7323, 4000, (2000, 2000), (2, 0)),
    "M6": (7324, 1000, (20000, 20000), (2, 0)),
}


def blob(repo, commit, path):
    return check_output(["git", "-C", str(repo), "cat-file", "blob", f"{commit}:{path}"])


def check(args):
    name = args.match
    pgn = args.pgn or args.raw / f"{name}.pgn"
    out, meta_path = (args.raw / f"{name}.{suffix}" for suffix in ("out", "meta"))
    meta = json.loads(meta_path.read_bytes())
    manifest = json.loads(args.manifest.read_bytes())
    cell = manifest["cells"][name]
    seed, pair_limit, nodes, guards = SCHEDULE[name]
    assert meta["match"] == name and (meta["engine_a"], meta["engine_b"]) == ("A", "B")
    assert (meta["seed"], meta["games_requested"], (meta["nodes_a"], meta["nodes_b"])) == (seed, pair_limit * 2, nodes)
    assert meta["exe_sha256"] == meta["exe_sha256_b"] == HG_SHA and meta["external_net_file"] is None
    assert meta["evaluation"] == "Forge embedded evaluation" and meta["fastchess_sha256"] == FASTCHESS_SHA
    assert meta["book_source_sha256"] == BOOK_SHA and meta["book_manifest_sha256"] == digest(args.manifest) == MANIFEST_SHA
    assert (meta["book_sha256"], meta["book_openings_count"]) == (cell["sha256"], pair_limit)
    reference = json.loads(blob(args.repo, C21_COMMIT, "forge-combo29/sol/job31/raw/C21.meta"))
    pc20 = settings(reference["settings_a"])
    assert pc20 == settings(reference["settings_b"]) and pc20["HistoryAgeKeep"] == "1024"
    expected = [dict(pc20, NullMateGuard=str(guard)) for guard in guards]
    assert [settings(meta[f"settings_{side}"]) for side in "ab"] == expected
    for suffix, sent in zip(("", "_b"), expected, strict=True):
        assert settings(meta[f"preflight_settings_sent{suffix}"]) == sent
        assert meta[f"preflight_reply{suffix}"][-1:] == ["readyok"]
        assert meta[f"preflight_uci{suffix}"][-1:] == ["uciok"]
        assert meta[f"preflight_uci{suffix}"].count(GUARD_OPTION) == 1
        assert not any("unknown option" in line.lower() or "invalid value" in line.lower()
                       for line in meta[f"preflight_reply{suffix}"])
    verify_command(meta, expected)
    assert meta["status"] in ("complete", "interrupted")
    assert digest(pgn) == meta["pgn_sha256"] and digest(out) == meta["out_sha256"]
    reserved = set(cell["fen_keys_sha256"])
    games, unresolved, results, used, scores, penta, same, even_same = pgn_results(pgn, reserved)
    pairs = sum(penta)
    logs = FINISHED.findall(out.read_text())
    assert len({index for index, *_ in logs}) == len(logs)
    assert not (results - Counter((w, b, score) for _, w, b, score in logs))
    if meta["status"] == "complete":
        assert (games, pairs, unresolved, used, len(logs)) == (pair_limit * 2, pair_limit, 0, reserved, games)
    rating = symmetric_elo(penta)
    if name == "K22":
        assert meta["status"] == "complete" and same == even_same == pairs == 50
    if name == "C22":
        assert meta["status"] == "complete" and rating is not None and rating[2] < 0
    better, worse = sum(penta[3:]), sum(penta[:2])
    count = better + worse
    p = min(1, Fraction(2 * sum(comb(count, index) for index in range(min(better, worse) + 1)), 2 ** count))
    reading = "unavailable" if rating is None else "BETTER" if rating[1] > 0 else "WORSE" if rating[2] < 0 else "LEVEL"
    print(f"{name} {meta['status']} | HG PC20, embedded AL1, Keep 1024, guards {guards[0]}/{guards[1]}, "
          f"nodes A/B {nodes[0]}/{nodes[1]}, seed {seed} | {2 * pairs} games / {pairs} complete pairs | "
          f"{games - 2 * pairs} games excluded ({unresolved} unresolved) | A W-L-D {scores[2]}-{scores[0]}-{scores[1]} | "
          f"penta {penta} | {same}/{pairs} exact ordered UCI lists ({even_same} even) | {better} better / {worse} worse | "
          f"two-sided exact p {float(p):.10g} | {format_rating(rating)} | {reading}")
    print(f"Raw PGN SHA-256 {meta['pgn_sha256']}, fastchess output SHA-256 {meta['out_sha256']}.")


def verify_publication(args, commit):
    name = args.match
    prefix = "forge-combo29/sol/job32/raw"
    for suffix in ("out", "meta"):
        filename = f"{name}.{suffix}"
        payload = blob(args.repo, commit, f"{prefix}/{filename}")
        assert payload == (args.raw / filename).read_bytes()
        print(f"{commit} {filename} equals scratch ({len(payload):,} bytes).")
    filename = f"{name}.pgn"
    original = (args.pgn or args.raw / filename).read_bytes()
    if len(original) <= 20_000_000:
        assert original == blob(args.repo, commit, f"{prefix}/{filename}")
        print(f"{commit} {filename} equals scratch ({len(original):,} bytes).")
        return
    manifest = json.loads(blob(args.repo, commit, f"{prefix}/{filename}.manifest.json"))
    offset = 0
    for part in manifest["parts"]:
        payload = blob(args.repo, commit, f"{prefix}/{part['file']}")
        assert 0 < len(payload) == part["bytes"] <= 20_000_000
        assert sha256(payload).hexdigest() == part["sha256"]
        assert payload == original[offset:offset + len(payload)]
        print(f"{commit} {part['file']} equals original slice ({len(payload):,} bytes).")
        offset += len(payload)
    assert offset == len(original) == manifest["original"]["bytes"]
    assert sha256(original).hexdigest() == manifest["original"]["sha256"]
    print(f"All {len(original):,} {name} PGN bytes reassemble in manifest order. "
          f"The manifest records {manifest['original']['complete_pairs']:,} complete pairs and "
          f"{manifest['rounds_split_across_parts']} split pairs.")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("match", choices=SCHEDULE)
    cli.add_argument("--published", action="store_true")
    cli.add_argument("--commit")
    cli.add_argument("--raw", type=Path, default=HERE / "raw")
    cli.add_argument("--manifest", type=Path, default=HERE / "openings/manifest.json")
    cli.add_argument("--pgn", type=Path)
    repo = HERE.parent / "sol-job1/repo"
    cli.add_argument("--repo", type=Path, default=repo if repo.is_dir() else HERE.parents[2])
    args = cli.parse_args()
    check(args)
    if args.published or args.commit:
        commit = args.commit or (HERE / f"{args.match}.commit").read_text().strip()
        verify_publication(args, commit)


if __name__ == "__main__":
    main()
