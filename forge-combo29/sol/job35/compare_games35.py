#!/usr/bin/env python3
"""Compare numbered random-opening Forge move records after an opening byte gate."""

import argparse
from hashlib import sha256
from itertools import zip_longest
import json
from pathlib import Path
import re


MOVE = re.compile(r"[a-h][1-8][a-h][1-8][qrbn]?")


def openings(path, first, last):
    data = path.read_bytes()
    if not data.endswith(b"\n"):
        raise ValueError(f"{path}: unfinished opening line")
    positions = {}
    for row in data.decode("ascii").split("\n")[:-1]:
        game, words, status = row.split("\t")
        moves = words.split()
        number = int(game)
        if number != first + len(positions) or not all(MOVE.fullmatch(move) for move in moves):
            raise ValueError(f"{path}: unexpected game or UCI moves: {row}")
        if len(moves) > 8 or (status == "ready" and len(moves) != 8):
            raise ValueError(f"{path}: unexpected opening length: {row}")
        positions[number] = moves, status
    if list(positions) != list(range(first, last + 1)):
        raise ValueError(f"{path}: openings do not cover requested games {first} through {last}")
    return data, positions


def load(path, positions, opening_hash):
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError(f"{path}: unfinished record")
    data = json.loads(Path(f"{path}.meta").read_bytes())
    hashes = sha256(raw).hexdigest(), opening_hash
    if (data["records_sha256"], data["openings_sha256"]) != hashes:
        raise ValueError(f"{path}: source or record digest differs from sidecar")
    if (data["first_game"], data["last_game"], data["games_requested"]) != (min(positions), max(positions), len(positions)):
        raise ValueError(f"{path}: requested game range differs from sidecar")
    groups = {}
    count = 0
    total = 0
    prior = 0
    for row in raw.decode("ascii").split("\n")[:-1]:
        game_text, ply_text, move, node_text = row.split(" ")
        game, ply, nodes = int(game_text), int(ply_text), int(node_text)
        if game < prior or game not in positions or not MOVE.fullmatch(move) or nodes <= 0:
            raise ValueError(f"{path}: malformed record {row}")
        prior = game
        series = groups.setdefault(game, [])
        if ply != len(positions[game][0]) + len(series) or ply >= 300 or positions[game][1] != "ready":
            raise ValueError(f"{path}: invalid searched ply in {row}")
        series.append((move, nodes))
        count += 1
        total += nodes
    finished = [item["game"] for item in data["games"]]
    if finished != list(positions)[:len(finished)] or (data["status"] == "complete" and len(finished) != len(positions)):
        raise ValueError(f"{path}: completed games do not form the expected prefix")
    if not groups.keys() <= set(finished):
        raise ValueError(f"{path}: record without a completed game")
    for meta in data["games"]:
        game = meta["game"]
        if (meta["opening_plies"], meta["plies"]) != (len(positions[game][0]), len(groups.get(game, []))):
            raise ValueError(f"{path}: completed game {game} has unexpected ply counts")
    if (data["positions_completed"], data["last_info_nodes_sum"], data["games_completed"]) != (count, total, len(finished)):
        raise ValueError(f"{path}: record totals differ from metadata")
    receipt = dict(path=str(path), status=data["status"], games=len(finished), records=count, bytes=len(raw),
                   records_sha256=hashes[0], openings_sha256=hashes[1], node_sum=total,
                   search=data["search"], exe_sha256=data["exe_sha256"], external_net_sha256=data["external_net_sha256"])
    return raw, {game: groups.get(game, []) for game in finished}, receipt


def format_record(game, ply, value):
    return f"{game} {ply} {value[0]} {value[1]}" if value is not None else None


def summarize(left, right, positions):
    raw_a, games_a, receipt_a = left
    raw_b, games_b, receipt_b = right
    common = sorted(games_a.keys() & games_b.keys())
    differing = [game for game in common if games_a[game] != games_b[game]]
    nodes_equal = games_a.keys() == games_b.keys() and all(
        [nodes for _, nodes in games_a[game]] == [nodes for _, nodes in games_b[game]] for game in common
    )
    first = None
    if differing:
        game = differing[0]
        a, b = games_a[game], games_b[game]
        offset, row_a, row_b = next((i, va, vb) for i, (va, vb) in enumerate(zip_longest(a, b)) if va != vb)
        random_plies = positions[game][0]
        searched_prefix = [move for move, _ in a[:offset]]
        ply = len(random_plies) + offset
        first = dict(game=game, ply=ply, random_plies=random_plies, preceding_searched_moves=searched_prefix,
                     position="position startpos moves " + " ".join(random_plies + searched_prefix),
                     left_record=format_record(game, ply, row_a), right_record=format_record(game, ply, row_b),
                     left_result=row_a, right_result=row_b)
    return dict(left=receipt_a, right=receipt_b, reading="IDENTICAL" if raw_a == raw_b else "DIFFERS",
                full_coverage=games_a.keys() == games_b.keys() == positions.keys(),
                common_games=len(common), differing_games=len(differing), differing_game_ids=differing,
                node_columns_equal=nodes_equal, left_only=sorted(games_a.keys() - games_b.keys()),
                right_only=sorted(games_b.keys() - games_a.keys()),
                missing_from_both=sorted(positions.keys() - (games_a.keys() | games_b.keys())),
                first_difference=first)


def display(result):
    print("| Record file | Status | Completed games | Records | Opening SHA-256 | Record SHA-256 | Last-info node sum |")
    print("|---|---|---:|---:|---|---|---:|")
    for name in ("left", "right"):
        row = result[name]
        print(f"| `{row['path']}` | {row['status']} | {row['games']} | {row['records']} | `{row['openings_sha256']}` | "
              f"`{row['records_sha256']}` | {row['node_sum']} |")
    print(f"\n**{result['reading']}.** Openings passed byte comparison first. "
          f"{result['differing_games']} of {result['common_games']} common completed games differ. "
          f"Equal node columns {'yes' if result['node_columns_equal'] else 'no'}.")
    if not result["full_coverage"]:
        print(f"\nIncomplete coverage. Games only on the left {result['left_only']}, only on the right "
              f"{result['right_only']}, and absent on both {result['missing_from_both']}.")
    if (first := result["first_difference"]) is not None:
        print(f"\nFirst differing common record at game {first['game']}, zero-based ply {first['ply']}.")
        print(f"- Left `{first['left_record'] or '<no record>'}`")
        print(f"- Right `{first['right_record'] or '<no record>'}`")
        print(f"- Random opening `{' '.join(first['random_plies'])}`")
        print(f"- Prior searched moves `{' '.join(first['preceding_searched_moves']) or '<none>'}`")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("left_openings", type=Path)
    cli.add_argument("right_openings", type=Path)
    cli.add_argument("left_records", type=Path)
    cli.add_argument("right_records", type=Path)
    cli.add_argument("--first", type=int, required=True)
    cli.add_argument("--last", type=int, required=True)
    cli.add_argument("--json", type=Path)
    cli.add_argument("--prefix", type=Path)
    args = cli.parse_args()
    if not 1 <= args.first <= args.last:
        cli.error("--first and --last must name a positive, increasing game range")
    opening_data, positions = openings(args.left_openings, args.first, args.last)
    if opening_data != args.right_openings.read_bytes():
        cli.error("the opening files differ byte for byte, so the record comparison is invalid")
    digest = sha256(opening_data).hexdigest()
    result = summarize(load(args.left_records, positions, digest), load(args.right_records, positions, digest), positions)
    display(result)
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.prefix and result["first_difference"]:
        args.prefix.write_text(result["first_difference"]["position"] + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
