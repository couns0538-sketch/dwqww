#!/usr/bin/env python3
"""Compare complete Job 34 four-field game records without replaying the engines."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
from itertools import islice, zip_longest
import json
from pathlib import Path
import re


ROW = re.compile(rb"([1-9][0-9]*) (0|[1-9][0-9]*) ([a-h][1-8][a-h][1-8][qrbn]?) (0|[1-9][0-9]*)")


@dataclass
class Records:
    path: Path
    raw: bytes
    games: dict
    rows: int
    nodes: int
    metadata: dict | None

    def receipt(self):
        result = {
            "path": str(self.path),
            "games": len(self.games),
            "records": self.rows,
            "bytes": len(self.raw),
            "sha256": sha256(self.raw).hexdigest(),
            "node_sum": self.nodes,
        }
        if self.metadata:
            for field in ("status", "search", "exe_sha256", "external_net_sha256"):
                result[field] = self.metadata[field]
        return result


def load(path):
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        raise ValueError(f"{path}: unfinished final record")
    games = {}
    nodes = 0
    row_count = 0
    previous_game = 0
    for number, line in enumerate(raw.split(b"\n")[:-1], 1):
        row = ROW.fullmatch(line)
        if not row:
            raise ValueError(f"{path}:{number}: malformed four-field record {line!r}")
        game, ply, move, count = row.groups()
        game, ply, count = int(game), int(ply), int(count)
        if game < previous_game:
            raise ValueError(f"{path}:{number}: book line went backwards")
        previous_game = game
        moves = games.setdefault(game, [])
        if ply != len(moves) or ply >= 300:
            raise ValueError(f"{path}:{number}: invalid ply {ply} for book line {game}")
        moves.append((move.decode("ascii"), count))
        row_count += 1
        nodes += count
    sidecar = path.with_name(path.name + ".meta")
    metadata = json.loads(sidecar.read_bytes()) if sidecar.is_file() else None
    if metadata is not None:
        finished = metadata["games"]
        finished_keys = [entry["book_line"] for entry in finished]
        first, last = metadata["first_line"], metadata["last_line"]
        if (metadata["records_sha256"], metadata["positions_completed"],
            metadata["last_info_nodes_sum"], metadata["games_completed"]) != (
            sha256(raw).hexdigest(), row_count, nodes, len(finished)
        ):
            raise ValueError(f"{sidecar}: count or digest disagrees with records")
        if finished_keys != list(range(first, first + len(finished))) or first + len(finished) > last + 1:
            raise ValueError(f"{sidecar}: completed games do not form the requested prefix")
        if metadata["status"] == "complete" and len(finished) != last - first + 1:
            raise ValueError(f"{sidecar}: complete status disagrees with requested range")
        if not games.keys() <= set(finished_keys) or any(
            entry["plies"] != len(games.get(entry["book_line"], ())) for entry in finished
        ):
            raise ValueError(f"{sidecar}: per-game completed plies disagree with records")
        games = {game: games.get(game, []) for game in finished_keys}
    return Records(path, raw, games, row_count, nodes, metadata)


def game_difference(left, right):
    for ply, (row_left, row_right) in enumerate(zip(left, right)):
        if row_left != row_right:
            return ply, row_left, row_right
    if len(left) != len(right):
        ply = min(len(left), len(right))
        return ply, left[ply] if ply < len(left) else None, right[ply] if ply < len(right) else None
    return None


def book_line(book, game):
    with book.open(encoding="ascii") as source:
        fen = next(islice(source, game - 1, game), None)
    if fen is None or len(fen.split()) != 6:
        raise ValueError(f"{book}:{game}: missing six-field FEN")
    return fen.rstrip("\r\n")


def raw_record(game, ply, row):
    return f"{game} {ply} {row[0]} {row[1]}" if row is not None else None


def summarize(book, left, right, first, last):
    for run in (left, right):
        if run.metadata is None:
            continue
        pinned_range = run.metadata["first_line"], run.metadata["last_line"]
        if first is None:
            first, last = pinned_range
        elif (first, last) != pinned_range:
            raise ValueError(f"{run.path}: requested range disagrees with metadata")
    left_keys, right_keys = set(left.games), set(right.games)
    expected = set(range(first, last + 1)) if first is not None else left_keys | right_keys
    if not (left_keys | right_keys) <= expected:
        raise ValueError("records contain a book line outside the requested range")
    common = sorted(left_keys & right_keys)
    differences = []
    equal_nodes = True
    for game in common:
        rows_left, rows_right = left.games[game], right.games[game]
        if (delta := game_difference(rows_left, rows_right)) is not None:
            differences.append((game, *delta))
        equal_nodes = equal_nodes and (
            len(rows_left) == len(rows_right)
            and all(a[1] == b[1] for a, b in zip(rows_left, rows_right, strict=True))
        )
    first_difference = None
    if differences:
        game, ply, row_left, row_right = differences[0]
        prefix = left.games[game][:ply]
        assert prefix == right.games[game][:ply]
        first_difference = {
            "book_line": game,
            "ply": ply,
            "fen": book_line(book, game),
            "prior_moves": [row[0] for row in prefix],
            "left_record": raw_record(game, ply, row_left),
            "right_record": raw_record(game, ply, row_right),
            "left_result": row_left,
            "right_result": row_right,
        }
    first_stream_record = None
    if left.raw != right.raw:
        # A cutoff can change file length without changing any common game's records.
        stream = zip_longest(left.raw.decode("ascii").splitlines(), right.raw.decode("ascii").splitlines())
        for number, (a, b) in enumerate(stream, 1):
            if a != b:
                first_stream_record = {"record_number": number, "left_record": a, "right_record": b}
                break
    return {
        "left": left.receipt(),
        "right": right.receipt(),
        "reading": "IDENTICAL" if left.raw == right.raw else "DIFFERS",
        "complete_coverage": left_keys == right_keys == expected,
        "common_game_count": len(common),
        "differing_common_game_count": len(differences),
        "differing_common_book_lines": [delta[0] for delta in differences],
        "left_only_book_lines": sorted(left_keys - right_keys),
        "right_only_book_lines": sorted(right_keys - left_keys),
        "missing_from_both": sorted(expected - (left_keys | right_keys)),
        "node_columns_equal": left_keys == right_keys and equal_nodes,
        "common_node_columns_equal": equal_nodes,
        "first_differing_common_record": first_difference,
        "first_differing_stream_record": first_stream_record,
    }


def position(fen, moves):
    return "position fen " + fen + (" moves " + " ".join(moves) if moves else "")


def display(summary):
    print("| Record file | Status | Completed games | Records | Bytes | SHA-256 | Node-column sum |")
    print("|---|---|---:|---:|---:|---|---:|")
    for name in ("left", "right"):
        entry = summary[name]
        print(f"| `{entry['path']}` | {entry.get('status', 'no metadata')} | {entry['games']} | "
              f"{entry['records']} | {entry['bytes']} | "
              f"`{entry['sha256']}` | {entry['node_sum']} |")
    print(f"\n**{summary['reading']}.** Compared {summary['common_game_count']} common games. "
          f"Differing common games {summary['differing_common_game_count']}. "
          f"Equal node columns {'yes' if summary['node_columns_equal'] else 'no'}.")
    if not summary["complete_coverage"]:
        print("\nIncomplete coverage. The difference count uses common recorded games only.")
        for name in ("left_only_book_lines", "right_only_book_lines", "missing_from_both"):
            print(f"- {name.replace('_', ' ').capitalize()} {summary[name]}.")
    first = summary["first_differing_common_record"]
    if first is not None:
        print(f"\nFirst differing common record at book line {first['book_line']}, ply {first['ply']}.")
        for name in ("left", "right"):
            print(f"- {name.capitalize()} `{first[f'{name}_record'] or '<no record>'}`")
        print(f"- Opening `{first['fen']}`")
        print(f"- Moves already played `{(' '.join(first['prior_moves'])) or '<none>'}`")
    elif (stream := summary["first_differing_stream_record"]) is not None:
        print(f"\nFirst differing record-file line {stream['record_number']} reflects incomplete coverage.")
        for name in ("left", "right"):
            print(f"- {name.capitalize()} `{stream[f'{name}_record'] or '<no record>'}`")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("book", type=Path)
    cli.add_argument("left", type=Path)
    cli.add_argument("right", type=Path)
    cli.add_argument("--first", type=int)
    cli.add_argument("--last", type=int)
    cli.add_argument("--json", type=Path)
    cli.add_argument("--prefix", type=Path, help="write just the divergent position command, if any")
    args = cli.parse_args()
    if (args.first is None) != (args.last is None) or args.first is not None and not 1 <= args.first <= args.last:
        cli.error("--first and --last must together name a positive, increasing book range")
    summary = summarize(args.book, load(args.left), load(args.right), args.first, args.last)
    display(summary)
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.prefix and (difference := summary["first_differing_common_record"]) is not None:
        args.prefix.write_text(position(difference["fen"], difference["prior_moves"]) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
