#!/usr/bin/env python3
"""Regenerate the random openings and verify Job 35's complete derivatives."""

import argparse
from collections import defaultdict
from hashlib import file_digest, sha256
import json
from pathlib import Path
import random
import re
import subprocess

import chess


PHASES = {
    "controls": (1, 20, ("K25a", "K25b", "C25")),
    "U1": (1, 1000, ("U1-r15d", "U1-kF")),
    "U2": (1001, 1500, ("U2-r15d", "U2-kF")),
}
ENGINE_HASHES = {
    "r15d": "9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671",
    "kF": "c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb",
}
NET_SHA = "c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7"
CHECKSUM = "30ab43b4ba5db5f3"


def digest(path):
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest()


def generate(first, last):
    result = {}
    text = []
    for game in range(first, last + 1):
        rng = random.Random(game)
        board = chess.Board()
        status = "ready"
        moves = []
        for _ in range(8):
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            moves.append(move.uci())
            ending = board.outcome(claim_draw=True)
            if ending is not None:
                status = ending.termination.name.lower()
                break
        result[game] = moves, status
        text.append(f"{game}\t{' '.join(moves)}\t{status}\n")
    return result, "".join(text).encode("ascii")


def check_run(root, label, positions, opening_raw, pc20, verified):
    build = "kF" if label.endswith("-kF") else "r15d"
    quiet = 60 if label == "C25" else 93
    opening = root / "openings" / f"{label}.openings.txt"
    records = root / "raw" / f"{label}.records.txt"
    sidecar = Path(f"{records}.meta")
    console = root / "raw" / f"{label}.run.txt"
    meta = json.loads(sidecar.read_bytes())
    raw = records.read_bytes()
    raw_sha = sha256(raw).hexdigest()
    opening_sha = sha256(opening_raw).hexdigest()
    assert opening.read_bytes() == opening_raw, label
    assert (meta["records_sha256"], meta["openings_sha256"]) == (raw_sha, opening_sha), label
    assert (meta["first_game"], meta["last_game"], meta["games_requested"]) == (min(positions), max(positions), len(positions)), label
    assert meta["exe_sha256"] == ENGINE_HASHES[build] == digest(Path(meta["exe"])), label
    assert meta["external_net_sha256"] == NET_SHA == digest(Path(meta["external_net_file"])), label
    assert meta["external_net_checksum_expected"] == CHECKSUM and meta["python_chess"] == "1.11.2", label
    assert meta["search"] == "go softnodes 2000" and meta["max_plies"] == 300 and meta["claim_draw"], label
    assert meta["reset_commands"] == ["ucinewgame", "isready"] and meta["reset_frequency"] == "once per searched game", label
    values = ["setoption name Threads value 1", "setoption name Hash value 16", *pc20,
              f"setoption name NNUEArchFile value {meta['external_net_file']}", "setoption name NNUEArch value true"]
    values[2] = f"setoption name LmrQuietBase value {quiet}"
    assert meta["settings_sent"] == values, label
    transcript = console.read_text().splitlines()
    for key, role in (("load_line", "loaded"), ("active_line", "active")):
        text = meta[key]
        assert text.startswith(f"info string NNUE v3 {role}:") and f" checksum {CHECKSUM} " in text, label
        assert transcript.count(text) == 1 and meta["setup_reply"].count(text) == 1, label

    rows = defaultdict(list)
    total = count = prior = 0
    assert not raw or raw.endswith(b"\n"), label
    for row in raw.decode("ascii").split("\n")[:-1]:
        game, ply, move, nodes = row.split(" ")
        game, ply, nodes = int(game), int(ply), int(nodes)
        assert game in positions and game >= prior and nodes > 0 and ply < 300, (label, row)
        moves, status = positions[game]
        assert status == "ready" and ply == len(moves) + len(rows[game]), (label, row)
        rows[game].append((move, nodes))
        count += 1
        total += nodes
        prior = game
    games = meta["games"]
    finished = [entry["game"] for entry in games]
    assert finished == list(positions)[:len(games)] and rows.keys() <= set(finished), label
    assert (len(games), count, total) == (meta["games_completed"], meta["positions_completed"], meta["last_info_nodes_sum"]), label
    assert meta["info_line_kinds"] == ({"softnodes": count} if count else {}), label
    if meta["status"] == "complete":
        assert len(games) == len(positions) and meta["engine_exit"] == 0, label

    signatures = [(entry["game"], entry["opening_plies"], entry["plies"], entry["termination"]) for entry in games]
    early = []
    for game, opening_plies, searches, termination in signatures:
        moves, status = positions[game]
        assert opening_plies == len(moves) and searches == len(rows[game]), (label, game)
        if status != "ready":
            assert searches == 0 and termination == status, (label, game, status)
            early.append((game, opening_plies, status))
    if raw_sha in verified:
        assert (raw, signatures) == verified[raw_sha], f"{label}: cannot reuse legality without identical bytes and terminals"
    else:
        for game, opening_plies, _searches, termination in signatures:
            board = chess.Board()
            for move in positions[game][0]:
                board.push_uci(move)
            for ply, (move, _nodes) in enumerate(rows[game], opening_plies):
                assert not board.is_game_over(claim_draw=True), (label, game, ply, "continued after terminal")
                board.push_uci(move)
            ending = board.outcome(claim_draw=True)
            expected = ending.termination.name.lower() if ending is not None else "300_ply_limit" if board.ply() == 300 else None
            assert termination == expected, (label, game, termination, expected)
        verified[raw_sha] = raw, signatures

    print(f"{label} {meta['status']} | {build} {meta['exe_sha256']} | PC20 LmrQuietBase {quiet}, "
          f"net768 {CHECKSUM}, go softnodes 2000 | {len(games)} games | {count} records | {total} last-info nodes | "
          f"openings SHA-256 {opening_sha} | records SHA-256 {raw_sha}")
    if early:
        print(f"{label} games ending during randomized moves, with zero engine searches: {early}.")
    return opening_raw, raw, dict(rows), (opening, records, sidecar, console)


def compare(description, left, right, positions):
    book_a, raw_a, a, _ = left
    book_b, raw_b, b, _ = right
    assert book_a == book_b
    common = sorted(a.keys() & b.keys())
    changed = [game for game in common if a[game] != b[game]]
    equal_nodes = a.keys() == b.keys() and all([
        nodes for _, nodes in a[game]
    ] == [nodes for _, nodes in b[game]] for game in common)
    print(f"{description} {'IDENTICAL' if raw_a == raw_b else 'DIFFERS'} | {len(changed)}/{len(common)} differing common games | equal node columns {equal_nodes}")
    if a.keys() != b.keys():
        print(f"Completed only on left {sorted(a.keys()-b.keys())}, only on right {sorted(b.keys()-a.keys())}.")
    if changed:
        game = changed[0]
        ply = next((i for i, (x, y) in enumerate(zip(a[game], b[game])) if x != y), min(len(a[game]), len(b[game])))
        print(f"First common difference at game {game}, ply {len(positions[game][0]) + ply}, "
              f"left {a[game][ply:ply+1]}, right {b[game][ply:ply+1]}.")
    return len(changed), equal_nodes, a.keys() == b.keys() == positions.keys()


def grade(root, comparison, repo):
    forecast = (root / "prediction.txt").read_bytes()
    if repo is not None:
        pin = (root / "prediction.commit").read_text().strip()
        archive = "forge-combo29/sol/job35/prediction.txt"
        commit_files = subprocess.check_output([
            "git", "-C", str(repo), "diff-tree", "--no-commit-id", "--name-only", "-r", pin,
        ], text=True).splitlines()
        assert commit_files == [archive], (pin, commit_files)
        assert forecast == subprocess.check_output(["git", "-C", str(repo), "show", f"{pin}:{archive}"])
    decoded = forecast.decode("utf-8")
    low, high = map(int, re.search(r"(?m)^U1 differing games: (\d+) to (\d+) of 1000$", decoded).groups())
    equal = re.search(r"(?m)^U1 node columns equal: (yes|no)$", decoded)[1] == "yes"
    observed, nodes_equal, complete = comparison
    if complete:
        print(f"U1 prediction from its own unchanged commit. Differing games {observed} within {low} to {high}: "
              f"{'met' if low <= observed <= high else 'missed'}. Node equality {nodes_equal} versus {equal}: "
              f"{'met' if nodes_equal == equal else 'missed'}.")
    else:
        print("U1 prediction ungraded because at least one run did not complete all 1,000 games.")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("phase", choices=PHASES)
    cli.add_argument("--repo", type=Path)
    args = cli.parse_args()
    assert chess.__version__ == "1.11.2"
    root = Path(__file__).resolve().parent
    first, last, labels = PHASES[args.phase]
    positions, opening_raw = generate(first, last)
    pc20 = (root.parent / "sol-job2" / "pc20-options.txt").read_text().splitlines()
    verified = {}
    runs = [check_run(root, label, positions, opening_raw, pc20, verified) for label in labels]
    print("All numbered openings regenerated exactly. All searched moves were legal and stopped at the first claimable terminal or the 300-total-ply cap.")
    reading = compare("K25" if args.phase == "controls" else args.phase, runs[0], runs[1], positions)
    if args.phase == "controls":
        compare("C25 versus K25a", runs[0], runs[2], positions)
    elif args.phase == "U1":
        grade(root, reading, args.repo)
    if args.repo:
        commit = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip()
        for _, _, _, files in runs:
            for path in files:
                archive = f"forge-combo29/sol/job35/{path.relative_to(root)}"
                raw = subprocess.check_output(["git", "-C", str(args.repo), "show", f"{commit}:{archive}"])
                assert raw == path.read_bytes(), archive
        print(f"All {4 * len(runs)} committed raw and opening artifacts match scratch byte for byte at {commit}.")


if __name__ == "__main__":
    main()
