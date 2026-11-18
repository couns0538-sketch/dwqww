#!/usr/bin/env python3
"""Recount Job 31's complete pairs and published evidence independently."""

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
WORK = HERE.parent
REPO = WORK / "sol-job1/repo"
for candidate in (WORK / "job28", WORK / "sol-job28"):
    if (candidate / "independent_matches28.py").is_file():
        sys.path.insert(0, str(candidate))
        break
from independent_matches28 import FINISHED, digest, pgn_results, symmetric_elo

H_SHA = "3cf1903d4713ed00acf61965bd20ef6fe01c71db994dbc34f3886faba5a4411c"
BOOK_SHA = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
FASTCHESS_SHA = "fb945c0930ff17786ccc1c07267930e1c0a6098f9bb16dcd13be20a11baec72e"
# Seed, pair count, A/B nodes, A/B version names.
SCHEDULE = {
    "K21": (7311, 50, (2000, 2000), "aa"),
    "C21": (7312, 100, (1000, 2000), "bb"),
    "M3b": (7313, 4000, (2000, 2000), "ab"),
    "M4b": (7314, 1000, (20000, 20000), "ab"),
    "M3": (7292, 4000, (2000, 2000), "ab"),
    "M4": (7293, 1000, (20000, 20000), "ab"),
}
PRIOR = {"M3": "7f86a503af5ad9a2ed17e42fd4f150d9df75ad9b", "M4": "3dfa7ce69e3d69a3dfef22219b032441d3e68c4b"}


def blob(commit, job, path):
    return check_output(["git", "-C", str(REPO), "cat-file", "blob", f"{commit}:forge-combo29/sol/job{job}/{path}"])


def settings(lines):
    values = dict(line.removeprefix("setoption name ").split(" value ", 1) for line in lines)
    assert len(values) == len(lines)
    return values


def verify_command(meta, expected):
    command = meta["fastchess_command"]
    starts = [index for index, token in enumerate(command) if token == "-engine"]
    each = command.index("-each")
    assert len(starts) == 2 and starts[1] < each
    common_limit = {token for token in command[each:] if token.startswith("nodes=")}
    for side, nodes, sent, executable, start, end in zip(
        "AB", (meta["nodes_a"], meta["nodes_b"]), expected, (meta["exe"], meta["exe_b"]),
        starts, [starts[1], each], strict=True,
    ):
        tokens = command[start + 1:end]
        assert f"name={side}" in tokens and f"cmd={executable}" in tokens
        options = [tuple(token.removeprefix("option.").split("=", 1)) for token in tokens if token.startswith("option.")]
        assert len(options) == len(sent) and dict(options) == sent
        local_limit = {token for token in tokens if token.startswith("nodes=")}
        assert (local_limit or common_limit) == {f"nodes={nodes}"}
    for flag, value in (("-srand", meta["seed"]), ("-rounds", meta["games_requested"] // 2),
                        ("-games", 2), ("-concurrency", 4), ("-maxmoves", 300), ("-openings", f"file={meta['book']}")):
        assert command[command.index(flag) + 1] == str(value)
    assert "-repeat" in command


def check(name):
    directory = WORK / "sol-job30" if name in PRIOR else HERE
    raw = directory / "raw"
    pgn, out, meta_path = (raw / f"{name}.{suffix}" for suffix in ("pgn", "out", "meta"))
    if not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_bytes())
    manifest_path = directory / "openings/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    cell = manifest["cells"][name]
    seed, pair_limit, nodes, arms = SCHEDULE[name]
    assert meta["match"] == name and (meta["engine_a"], meta["engine_b"]) == ("A", "B")
    assert (meta["seed"], meta["games_requested"], (meta["nodes_a"], meta["nodes_b"])) == (seed, pair_limit * 2, nodes)
    assert meta["exe_sha256"] == meta["exe_sha256_b"] == H_SHA and meta["external_net_file"] is None
    assert meta["evaluation"] == "Forge embedded evaluation" and meta["fastchess_sha256"] == FASTCHESS_SHA
    assert meta["book_source_sha256"] == BOOK_SHA and meta["book_manifest_sha256"] == digest(manifest_path)
    assert (meta["book_sha256"], meta["book_openings_count"]) == (cell["sha256"], pair_limit)
    reference = json.loads(blob(PRIOR["M3"], 30, "raw/M3.meta"))
    expected = [settings(reference[f"settings_{arm}"]) for arm in arms]
    assert [settings(meta[f"settings_{side}"]) for side in "ab"] == expected
    for suffix, sent in zip(("", "_b"), expected, strict=True):
        assert settings(meta[f"preflight_settings_sent{suffix}"]) == sent
        assert meta[f"preflight_reply{suffix}"][-1:] == ["readyok"]
        assert meta[f"preflight_uci{suffix}"][-1:] == ["uciok"]
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
    if name == "K21":
        assert meta["status"] == "complete" and same == even_same == pairs == 50
    if name == "C21":
        assert meta["status"] == "complete" and rating is not None and rating[2] < 0
    better, worse = sum(penta[3:]), sum(penta[:2])
    count = better + worse
    p = min(1, Fraction(2 * sum(comb(count, index) for index in range(min(better, worse) + 1)), 2 ** count))
    fmt = format_rating(rating)
    print(f"{name} {meta['status']} | H PC20, nodes A/B {nodes[0]}/{nodes[1]}, seed {seed} | {2 * pairs} games / {pairs} complete pairs | "
          f"{games - 2 * pairs} games excluded ({unresolved} unresolved) | A W-L-D {scores[2]}-{scores[0]}-{scores[1]} | "
          f"penta {penta} | {same}/{pairs} exact ordered UCI lists ({even_same} even) | {better} better / {worse} worse | "
          f"two-sided exact p {float(p):.10g} | {fmt}")
    return meta["status"], penta, rating, used


def verify_publication(name):
    job = 30 if name in PRIOR else 31
    directory = WORK / "sol-job30" if job == 30 else HERE
    commit = PRIOR[name] if job == 30 else (directory / f"{name}.commit").read_text().strip()
    for suffix in ("out", "meta"):
        filename = f"{name}.{suffix}"
        payload = blob(commit, job, f"raw/{filename}")
        assert payload == (directory / "raw" / filename).read_bytes()
        print(f"{commit} {filename} equals scratch ({len(payload):,} bytes).")
    filename = f"{name}.pgn"
    original = (directory / "raw" / filename).read_bytes()
    if len(original) <= 20_000_000:
        assert original == blob(commit, job, f"raw/{filename}")
        print(f"{commit} {filename} equals scratch ({len(original):,} bytes).")
        return
    manifest = json.loads(blob(commit, job, f"raw/{filename}.manifest.json"))
    offset = 0
    for part in manifest["parts"]:
        payload = blob(commit, job, f"raw/{part['file']}")
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


def format_rating(rating):
    if rating is None:
        return "Elo unavailable"
    center, lo, hi = rating
    return f"{center:+.8f} Elo [{lo:+.8f}, {hi:+.8f}]"


def pool(old_name, new_name):
    old = check(old_name)
    new = check(new_name)
    verify_publication(old_name)
    if new is not None:
        assert not old[3] & new[3], "seed openings overlap"
        verify_publication(new_name)
    included = [(name, stats[1]) for name, stats in ((old_name, old), (new_name, new)) if stats and stats[0] == "complete"]
    excluded = [f"{name} ({stats[0] if stats else 'missing'})" for name, stats in ((old_name, old), (new_name, new))
                if not stats or stats[0] != "complete"]
    penta = [sum(row[index] for _, row in included) for index in range(5)]
    pooled = symmetric_elo(penta)
    # The pool uses complete matches only. The match-alone line uses any complete pairs that were played.
    new_elo = new[2][0] if new and new[2] is not None else None
    reading = "LEVEL"
    if pooled and new_elo is not None:
        if pooled[1] > 0 and new_elo > 0:
            reading = "BETTER"
        if pooled[2] < 0 and new_elo < 0:
            reading = "WORSE"
    print(f"POOL {old_name}/{new_name} | included {', '.join(name for name, _ in included) or 'none'} | "
          f"excluded {', '.join(excluded) or 'none'} | penta {penta} | {format_rating(pooled)} | {reading}")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("match", choices=(*SCHEDULE, "pools"))
    cli.add_argument("--published", action="store_true")
    args = cli.parse_args()
    if args.match == "pools":
        pool("M3", "M3b")
        pool("M4", "M4b")
    else:
        assert check(args.match) is not None
        if args.published:
            verify_publication(args.match)


if __name__ == "__main__":
    main()
