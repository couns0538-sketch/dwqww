#!/usr/bin/env python3
"""Read back Job 34 raw game records independently of the run and diff drivers."""

import argparse
from collections import defaultdict
from hashlib import file_digest, sha256
from itertools import islice
import json
from pathlib import Path
import subprocess

import chess


PHASES = {
    "controls": ("K24a", "K24b", "C24"),
    "T1": ("T1-r15d", "T1-kF"),
    "T2": ("T2-r15d", "T2-kF"),
}


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def expected_config(label):
    build = "kF" if label.endswith("-kF") else "r15d"
    quiet = 60 if label == "C24" else 93
    if label.startswith("T1"):
        return build, quiet, "softnodes", 1001, 2000
    if label.startswith("T2"):
        return build, quiet, "nodes", 2001, 2200
    return build, quiet, "softnodes", 1001, 1020


def check_run(root, book, book_hash, net_hash, pc20, label, verified):
    build, quiet, mode, first, last = expected_config(label)
    records = root / "raw" / f"{label}.records.txt"
    metadata = Path(f"{records}.meta")
    output = root / "raw" / f"{label}.run.txt"
    raw = records.read_bytes()
    meta = json.loads(metadata.read_bytes())
    lines = output.read_text().splitlines()
    checksum = "30ab43b4ba5db5f3"
    assert meta["search"] == f"go {mode} 2000", label
    assert (meta["first_line"], meta["last_line"], meta["games_requested"]) == (first, last, last - first + 1), label
    assert meta["book_sha256"] == book_hash == "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a", label
    assert meta["external_net_sha256"] == net_hash == "c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7", label
    assert meta["external_net_checksum_expected"] == checksum, label
    assert meta["exe_sha256"] == digest(root / build / "forge"), label
    settings = ["setoption name Threads value 1", "setoption name Hash value 16", *pc20,
                f"setoption name NNUEArchFile value {meta['external_net_file']}", "setoption name NNUEArch value true"]
    settings[2] = f"setoption name LmrQuietBase value {quiet}"
    assert meta["settings_sent"] == settings, label
    for state, key in (("loaded", "load_line"), ("active", "active_line")):
        text = meta[key]
        assert text.startswith(f"info string NNUE v3 {state}:") and f" checksum {checksum} " in text, label
        assert lines.count(text) == 1 and meta["setup_reply"].count(text) == 1, label
    assert meta["claim_draw"] and meta["max_plies"] == 300, label
    assert meta["reset_commands"] == ["ucinewgame", "isready"] and meta["reset_frequency"] == "once per game", label
    records_hash = sha256(raw).hexdigest()
    assert meta["records_sha256"] == records_hash, label
    assert not raw or raw[-1:] == b"\n", label
    grouped = defaultdict(list)
    total = 0
    row_count = 0
    prior_line = 0
    for row in raw.decode("ascii").splitlines():
        book_line, ply, move, nodes = row.split(" ")
        book_line, ply, nodes = int(book_line), int(ply), int(nodes)
        assert first <= book_line <= last and prior_line <= book_line, (label, row)
        assert ply == len(grouped[book_line]) and nodes > 0, (label, row)
        grouped[book_line].append((move, nodes))
        total += nodes
        row_count += 1
        prior_line = book_line
    game_count = len(meta["games"])
    finished = list(range(first, first + game_count))
    assert [game["book_line"] for game in meta["games"]] == finished, label
    assert set(grouped) <= set(finished), label
    assert (meta["games_completed"], meta["positions_completed"], meta["last_info_nodes_sum"]) == (game_count, row_count, total), label
    if meta["status"] == "complete":
        assert game_count == last - first + 1 and meta["engine_exit"] == 0, label
    assert sum(meta["info_line_kinds"].values()) == row_count, label
    if mode == "softnodes" and row_count:
        assert meta["info_line_kinds"] == {"softnodes": row_count}, label
    signatures = [(game["book_line"], game["plies"], game["termination"]) for game in meta["games"]]
    if records_hash in verified:
        assert (raw, signatures) == verified[records_hash], f"{label}: reused check requires identical bytes and terminals"
    else:
        for book_line, plies, expected_termination in signatures:
            moves = grouped[book_line]
            assert len(moves) == plies <= 300, (label, book_line, plies)
            board = chess.Board(book[book_line])
            assert board.is_valid(), (label, book_line)
            for ply, (move, _nodes) in enumerate(moves):
                assert not board.is_game_over(claim_draw=True), (label, book_line, ply, "game continued past its terminal")
                board.push_uci(move)
            outcome = board.outcome(claim_draw=True)
            termination = outcome.termination.name.lower() if outcome is not None else "300_ply_limit" if len(moves) == 300 else None
            assert termination == expected_termination, (label, book_line, termination, expected_termination)
        verified[records_hash] = raw, signatures
    print(f"{label} {meta['status']} | build {build} {meta['exe_sha256']} | PC20 (LmrQuietBase {quiet}), "
          f"net768 {checksum}, {meta['search']} | {game_count} completed games | {row_count} records | "
          f"{total} last-info nodes | {records_hash}")
    return raw, dict(grouped), (records, metadata, output)


def compare(left, right, description):
    left_bytes, left_games, _ = left
    right_bytes, right_games, _ = right
    common = sorted(left_games.keys() & right_games.keys())
    changed = [game for game in common if left_games[game] != right_games[game]]
    same_nodes = all([nodes for _, nodes in left_games[game]] == [nodes for _, nodes in right_games[game]] for game in common)
    same_coverage = left_games.keys() == right_games.keys()
    print(f"{description} {'IDENTICAL' if left_bytes == right_bytes else 'DIFFERS'} | "
          f"{len(changed)}/{len(common)} differing common games | identical node columns {same_nodes and same_coverage}")
    if not same_coverage:
        print(f"Coverage only in left: {sorted(left_games.keys() - right_games.keys())}; "
              f"only in right: {sorted(right_games.keys() - left_games.keys())}")
    if changed:
        game = changed[0]
        a, b = left_games[game], right_games[game]
        ply = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        print(f"First common difference book line {game} ply {ply}: "
              f"left {a[ply] if ply < len(a) else None}; right {b[ply] if ply < len(b) else None}")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("phase", choices=PHASES)
    cli.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    cli.add_argument("--repo", type=Path, help="compare the currently committed archive bytes")
    args = cli.parse_args()
    root = args.root.resolve()
    book_path = root.parent / "sol-job12" / "UHO_Lichess_4852_v1.epd"
    with book_path.open(encoding="ascii") as source:
        book = dict(enumerate(islice(source, 2200), start=1))
    book_hash = digest(book_path)
    net_hash = digest(root / "net768.nnue")
    pc20 = (root.parent / "sol-job2" / "pc20-options.txt").read_text().splitlines()
    verified = {}
    runs = [check_run(root, book, book_hash, net_hash, pc20, label, verified) for label in PHASES[args.phase]]
    print("All completed games' ordered moves are legal and stop at the first claimable terminal or the 300-ply cap.")
    compare(runs[0], runs[1], "K24" if args.phase == "controls" else args.phase)
    if args.phase == "controls":
        compare(runs[0], runs[2], "C24 against K24a")
    if args.repo:
        commit = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip()
        for _, _, files in runs:
            for path in files:
                archive = f"forge-combo29/sol/job34/{path.relative_to(root)}"
                committed = subprocess.check_output(["git", "-C", str(args.repo), "show", f"{commit}:{archive}"])
                assert committed == path.read_bytes(), archive
        print(f"All {3 * len(runs)} raw artifact blobs match scratch byte for byte at {commit}.")


if __name__ == "__main__":
    main()
