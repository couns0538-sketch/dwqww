#!/usr/bin/env python3
"""Split fastchess PGN evidence under a file-size cap without changing its bytes."""

import argparse
from bisect import bisect_right
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sys


EVENT = re.compile(rb'^\[Event "[^\r\n]*"\]\r?$', re.M)
ROUND = re.compile(rb'^\[Round "(\d+)"\]\r?$', re.M)
RESULT = re.compile(rb'^\[Result "(1-0|0-1|1/2-1/2)"\]\r?$', re.M)
FINISH = re.compile(rb'(?:^|\s)(1-0|0-1|1/2-1/2)\s*\Z')


@dataclass(frozen=True, slots=True)
class Game:
    end: int
    round: int


def games_in(data):
    starts = [match.start() for match in EVENT.finditer(data)]
    if not starts or data[:starts[0]].strip():
        raise ValueError("expected a fastchess [Event ...] header at the start of the PGN")
    games = []
    for start, end in zip(starts, [*starts[1:], len(data)], strict=True):
        round_tag = ROUND.search(data, start, end)
        result_tag = RESULT.search(data, start, end)
        finish = FINISH.search(data, start, end)
        if not round_tag or not result_tag or not finish or finish[1] != result_tag[1]:
            raise ValueError(f"game {len(games) + 1} is missing a numeric round or matching final result")
        games.append(Game(end, int(round_tag[1])))
    return games


def round_counts(games):
    counts = Counter(game.round for game in games)
    if any(count > 2 for count in counts.values()):
        raise ValueError("PGN has more than two games in a [Round] pair")
    return counts


def partition(games, cap):
    ends = [0, *(game.end for game in games)]
    closed = [0]
    open_rounds = set()
    for index, game in enumerate(games, 1):
        if game.round in open_rounds:
            open_rounds.remove(game.round)
        else:
            open_rounds.add(game.round)
        if not open_rounds:
            closed.append(index)

    # Fastchess may write games for later rounds before closing an earlier pair.
    # Prefer a prefix where all rounds are closed, falling back to a game
    # boundary if the cap cannot hold the entire interleaved group.
    start = 0
    while start < len(games):
        last_game = bisect_right(ends, ends[start] + cap) - 1
        if last_game == start:
            raise ValueError(f"game {start + 1} exceeds {cap} bytes")
        last_closed = closed[bisect_right(closed, last_game) - 1]
        stop = last_closed if start < last_closed and last_game < len(games) else last_game
        yield start, stop, ends[start], ends[stop]
        start = stop


def part_entry(name, data, games):
    return {
        "file": name,
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "games": len(games),
        "complete_pairs": sum(count == 2 for count in round_counts(games).values()),
    }


def verify(directory, manifest):
    cap = manifest["max_part_bytes"]
    if type(cap) is not int or cap <= 0:
        raise ValueError("invalid manifest cap")
    entries = manifest["parts"]
    if not entries:
        raise ValueError("manifest has no parts")
    chunks = []
    names = set()
    actual_counts = Counter()
    full_sha = sha256()
    for entry in entries:
        name = entry["file"]
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."} or name in names:
            raise ValueError(f"invalid or repeated relative filename {name!r}")
        names.add(name)
        chunk = (directory / name).read_bytes()
        games = games_in(chunk)
        if len(chunk) > cap or entry != part_entry(name, chunk, games):
            raise ValueError(f"{name}: size, SHA-256, or PGN counts differ from manifest")
        chunks.append(chunk)
        full_sha.update(chunk)
        actual_counts.update(round_counts(games))

    original = manifest["original"]
    actual_pairs = sum(count == 2 for count in actual_counts.values())
    split_pairs = actual_pairs - sum(entry["complete_pairs"] for entry in entries)
    if (
        any(count > 2 for count in actual_counts.values())
        or full_sha.hexdigest() != original["sha256"]
        or sum(map(len, chunks)) != original["bytes"]
        or sum(actual_counts.values()) != original["games"]
        or actual_pairs != original["complete_pairs"]
        or sum(count == 1 for count in actual_counts.values()) != original["orphan_rounds"]
        or split_pairs != manifest["rounds_split_across_parts"]
        or bool(split_pairs) != manifest["join_required_for_pair_analysis"]
    ):
        raise ValueError("ordered PGN parts do not reconstruct the manifest's original evidence")
    return chunks


def split(source, directory, cap):
    if source.suffix.lower() != ".pgn":
        raise ValueError("expected a .pgn input")
    data = source.read_bytes()
    games = games_in(data)
    counts = round_counts(games)
    boundaries = list(partition(games, cap))
    complete_pairs = sum(count == 2 for count in counts.values())
    orphan_rounds = sum(count == 1 for count in counts.values())
    directory.mkdir(parents=True, exist_ok=True)
    manifest_path = directory / f"{source.name}.manifest.json"
    targets = []
    for part, (first, last, start, stop) in enumerate(boundaries, 1):
        name = source.name if len(boundaries) == 1 else f"{source.stem}.part{part:02d}{source.suffix}"
        path = directory / name
        chunk = data[start:stop]
        same_as_source = path.resolve() == source.resolve()
        targets.append((path, chunk, same_as_source, part_entry(name, chunk, games[first:last])))
    for path in [manifest_path, *(path for path, _, same, _ in targets if not same)]:
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")

    entries = [entry for _, _, _, entry in targets]
    split_pairs = complete_pairs - sum(entry["complete_pairs"] for entry in entries)
    manifest = {
        "original": {
            "file": source.name,
            "sha256": sha256(data).hexdigest(),
            "bytes": len(data),
            "games": len(games),
            "complete_pairs": complete_pairs,
            "orphan_rounds": orphan_rounds,
        },
        "max_part_bytes": cap,
        "rounds_split_across_parts": split_pairs,
        "join_required_for_pair_analysis": bool(split_pairs),
        "join_instruction": "Concatenate parts in the order listed, without adding or removing bytes.",
        "parts": entries,
    }
    created = []
    try:
        for path, chunk, same, _ in targets:
            if not same:
                with path.open("xb") as stream:
                    created.append(path)
                    stream.write(chunk)
        verify(directory, manifest)
        with manifest_path.open("x", encoding="utf-8") as stream:
            created.append(manifest_path)
            json.dump(manifest, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError):
        for path in reversed(created):
            path.unlink()
        raise
    for entry in entries:
        print(f"{entry['file']}: {entry['bytes']} bytes, {entry['games']} games, "
              f"{entry['complete_pairs']} complete pairs, SHA-256 {entry['sha256']}.")
    print(f"{manifest_path.name}: {len(games)} games, {complete_pairs} complete pairs, "
          f"{orphan_rounds} orphan rounds, {split_pairs} pairs split across parts.")
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    splitter = commands.add_parser("split", help="write capped ordered parts and validate their readback")
    splitter.add_argument("source", type=Path)
    splitter.add_argument("directory", type=Path)
    splitter.add_argument("--max-bytes", type=int, default=20_000_000)
    verifier = commands.add_parser("verify", help="verify part hashes, games, and logical original hash")
    verifier.add_argument("manifest", type=Path)
    joiner = commands.add_parser("join", help="verify and rebuild the original PGN")
    joiner.add_argument("manifest", type=Path)
    joiner.add_argument("output", type=Path)
    args = parser.parse_args()

    try:
        if args.mode == "split":
            if args.max_bytes <= 0:
                raise ValueError("--max-bytes must be positive")
            split(args.source, args.directory, args.max_bytes)
            return 0
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        chunks = verify(args.manifest.parent, manifest)
        if args.mode == "join":
            with args.output.open("xb") as stream:
                for chunk in chunks:
                    stream.write(chunk)
        original = manifest["original"]
        print(f"Verified {len(chunks)} ordered parts, {original['bytes']} bytes, "
              f"{original['games']} games, SHA-256 {original['sha256']}.")
        return 0
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"PGN evidence split failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
