#!/usr/bin/env python3
"""Verify fixed-node fastchess games against the opening book and compare their traces."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
from itertools import islice, zip_longest
import io
import json
from pathlib import Path
import re

import chess.pgn


BOOK = Path("/workspace/work/sol-job12/UHO_Lichess_4852_v1.epd")
BASE = {
    "K38": (4001, 10, 20000),
    "C38": (4001, 10, 20000),
    "G20": (4011, 300, 20000),
    "G50": (4311, 150, 50000),
    "G250": (4461, 24, 250000),
}
PAIRS = {
    "K38": ("K38a", "K38b"),
    "C38": ("K38a", "C38"),
    **{stage: (f"{stage}-r15d", f"{stage}-kF") for stage in ("G20", "G50", "G250")},
}
START = re.compile(r"^Started game (\d+) of (\d+) \(([^ ]+) vs ([^ ]+)\)$", re.M)
FINISH = re.compile(r"^Finished game (\d+) \(([^ ]+) vs ([^ ]+)\): (1-0|0-1|1/2-1/2) \{([^\n]*)\}$", re.M)
PGN_RECORD = re.compile(r'(?m)(?=^\[Event ")')
RESULT_END = re.compile(r"(?:^|\s)(1-0|0-1|1/2-1/2)\s*\Z")
NODE = re.compile(r"(?:^|,\s*)n=(\d+)(?=,|$)")


@dataclass(frozen=True)
class Game:
    opening_line: int
    round: int
    fen: str
    moves: tuple
    nodes: tuple


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_bytes(path, length, digest):
    content = path.read_bytes()
    require(len(content) == length and sha256(content).hexdigest() == digest, f"{path}: size or SHA mismatch")
    return content


def pgn_bytes(raw, label, meta):
    pgn = raw / f"{label}.pgn"
    manifest = raw / f"{label}.pgn.manifest.json"
    if manifest.is_file():
        parts = json.loads(manifest.read_text())["parts"]
        require(parts, f"{manifest}: empty parts list")
        chunks = []
        for part in parts:
            name = part["file"]
            require(Path(name).name == name and name.startswith(f"{label}.part") and name.endswith(".pgn"),
                    f"{manifest}: unexpected part {name}")
            chunks.append(checked_bytes(raw / name, part["bytes"], part["sha256"]))
        result = b"".join(chunks)
        require(len(result) == meta["pgn_bytes"] and sha256(result).hexdigest() == meta["pgn_sha256"],
                f"{manifest}: reassembled PGN size or SHA mismatch")
        return result
    if pgn.is_file():
        return checked_bytes(pgn, meta["pgn_bytes"], meta["pgn_sha256"])
    require(meta["status"] != "complete" and "pgn_sha256" not in meta, f"{pgn}: missing")
    return b""


def scheduled(label):
    stage = "K38" if label in ("K38a", "K38b") else label.split("-")[0]
    build = "kF" if label.endswith("-kF") else "r15d"
    return stage, build, 60 if stage == "C38" else 93


def expected_fens(book, base, count):
    with book.open() as source:
        records = list(islice(source, base - 1, base - 1 + count))
    require(len(records) == count, f"{book}: missing selected lines {base}–{base + count - 1}")
    fens = [chess.Board(" ".join(line.split()[:6])).fen() for line in records]
    require(len(set(fens)) == count, f"{book}: duplicate FEN in lines {base}–{base + count - 1}")
    return fens


def transcript_games(out, requested, label):
    starts, ends = set(), {}
    for number, total, white, black in START.findall(out):
        number = int(number)
        require(1 <= number <= requested and number not in starts and int(total) == requested
                and (white, black) == ("X1", "X2"), f"{label}: invalid transcript start {number}")
        starts.add(number)
    for number, white, black, result, reason in FINISH.findall(out):
        number = int(number)
        require(number in starts and number not in ends and (white, black) == ("X1", "X2"),
                f"{label}: invalid transcript finish {number}")
        ends[number] = (result, reason)
    return starts, ends


def parse_game(record, fens, ends, base, label):
    game = chess.pgn.read_game(io.StringIO(record))
    require(game is not None and not game.errors, f"{label}: invalid PGN game {record[:160]!r}")
    header = game.headers
    round_id = int(header["Round"])
    result = header["Result"]
    end = RESULT_END.search(record)
    require(end and end[1] == result and 1 <= round_id <= len(fens) and
            (header["White"], header["Black"]) == ("X1", "X2") and header["Termination"] == "normal" and
            header["TimeControl"] == "-" and round_id in ends and ends[round_id][0] == result,
            f"{label}: invalid headers or transcript mismatch in round {round_id}: {header}")
    board = game.board()
    fen = header["FEN"]
    require(board.fen() == fens[round_id - 1], f"{label}: round {round_id} FEN differs from book line {base + round_id - 1}")
    moves, nodes = [], []
    for position in game.mainline():
        counts = NODE.findall(position.comment)
        require(len(counts) <= 1, f"{label}: duplicate n= fields in round {round_id} ply {len(moves)+1}")
        moves.append(position.move.uci())
        nodes.append(int(counts[0]) if counts else None)
    require(len(moves) == int(header["PlyCount"]), f"{label}: round {round_id} PlyCount mismatch")
    return Game(base + round_id - 1, round_id, fen, tuple(moves), tuple(nodes))


def parse_run(raw, label, book, evidence):
    meta_path = raw / f"{label}.meta"
    if not meta_path.is_file() or meta_path.stat().st_size == 0:
        return {"status": "not played"}, {}
    meta = json.loads(meta_path.read_text())
    stage, build, lmr = scheduled(label)
    base, requested, nodes = BASE[stage]
    status = meta["status"]
    require(status in ("complete", "interrupted", "failed") and meta["match"] == label and
            (meta["opening_start"], meta["games_requested"], meta["nodes"], meta["build"], meta["lmr_quiet_base"]) ==
            (base, requested, nodes, build, lmr), f"{meta_path}: schedule or status mismatch")
    out = checked_bytes(raw / f"{label}.out", meta["out_bytes"], meta["out_sha256"]).decode()
    pgn = pgn_bytes(raw, label, meta).decode()
    starts, ends = transcript_games(out, requested, label)
    fens = expected_fens(book, base, requested)
    games, rounds = {}, set()
    for record in PGN_RECORD.split(pgn):
        if not record.strip():
            continue
        game = parse_game(record, fens, ends, base, label)
        canonical = chess.Board(game.fen).fen()
        require(game.round not in rounds and canonical not in games, f"{label}: repeated round or FEN {game.round}")
        rounds.add(game.round)
        games[canonical] = game
    require(rounds == ends.keys() and (status != "complete" or len(starts) == len(games) == requested),
            f"{label}: PGN and transcript game counts disagree")
    move_bytes = "".join(game.fen + (" " + " ".join(game.moves) if game.moves else "") + "\n"
                         for game in sorted(games.values(), key=lambda game: game.fen)).encode()
    move_path = f"{label}.moves.txt"
    if evidence is not None:
        (evidence / move_path).write_bytes(move_bytes)
    return {
        "status": status, "build": build, "nodes": nodes, "lmr_quiet_base": lmr,
        "opening_start": base, "opening_end": base + requested - 1, "games_requested": requested,
        "games": len(games), "started": len(starts), "unfinished_game_ids": sorted(starts - rounds),
        "plies": sum(len(game.moves) for game in games.values()),
        "missing_node_fields": sum(count is None for game in games.values() for count in game.nodes),
        "zero_node_fields": sum(count == 0 for game in games.values() for count in game.nodes),
        "move_sha256": sha256(move_bytes).hexdigest(), "move_list": move_path,
        "pgn_sha256": meta.get("pgn_sha256"), "out_sha256": meta["out_sha256"],
    }, games


def detail(kind, index, reference, candidate):
    def at(values):
        return values[index] if index < len(values) else None

    return {
        "kind": kind, "fen": reference.fen, "candidate_fen": candidate.fen, "round": reference.round,
        "opening_line": reference.opening_line, "ply": index + 1,
        "absolute_ply": chess.Board(reference.fen).ply() + index + 1,
        "ref_move": at(reference.moves), "candidate_move": at(candidate.moves),
        "ref_nodes": at(reference.nodes), "candidate_nodes": at(candidate.nodes),
    }


def first_mismatch(kind, left, right, reference, candidate):
    for index, (a, b) in enumerate(zip_longest(left, right)):
        if a != b:
            return detail(kind, index, reference, candidate)
    return None


def compare(stage, receipts, games):
    ref_label, cand_label = PAIRS[stage]
    reference, candidate = games[ref_label], games[cand_label]
    rows = []
    common = sorted(reference.keys() & candidate.keys(), key=lambda key: reference[key].opening_line)
    for fen in common:
        a, b = reference[fen], candidate[fen]
        require(a.opening_line == b.opening_line and a.fen == b.fen, f"{stage}: shared opening has inconsistent FEN or line")
        move = first_mismatch("move", a.moves, b.moves, a, b)
        node = first_mismatch("node", a.nodes, b.nodes, a, b)
        if move or node:
            differences = [value for value in (move, node) if value is not None]
            rows.append({"opening_line": a.opening_line, "move": move, "node": node,
                         "first": min(differences, key=lambda value: value["ply"])})
    all_played = receipts[ref_label]["status"] == receipts[cand_label]["status"] == "complete"
    require(not all_played or len(common) == len(reference) == len(candidate) == BASE[stage][1],
            f"{stage}: complete runs lack the same full FEN set")
    reading = ("DIFFERS" if rows else "IDENTICAL") if all_played else "PARTIAL" if common else "NOT PLAYED"
    return {
        "reference": ref_label, "candidate": cand_label, "reading": reading, "all_played": all_played,
        "compared_games": len(common), "differences": len(rows),
        "move_differences": sum(row["move"] is not None for row in rows),
        "node_differences": sum(row["node"] is not None for row in rows),
        "first_difference": rows[0]["first"] if rows else None,
        "first_move_difference": next((row["move"] for row in rows if row["move"] is not None), None),
        "first_node_difference": next((row["node"] for row in rows if row["node"] is not None), None),
        "differing_games": rows,
        "reference_only_opening_lines": sorted(reference[key].opening_line for key in reference.keys() - candidate.keys()),
        "candidate_only_opening_lines": sorted(candidate[key].opening_line for key in candidate.keys() - reference.keys()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--stage", choices=PAIRS)
    parser.add_argument("--book", type=Path, default=BOOK)
    parser.add_argument("--prediction", type=Path)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--evidence", type=Path, help="write FEN-sorted canonical move-list files")
    args = parser.parse_args()
    try:
        require(chess.__version__ == "1.11.2", f"Expected python-chess 1.11.2, got {chess.__version__}")
        if args.evidence is not None:
            args.evidence.mkdir(parents=True, exist_ok=True)
        stages = (args.stage,) if args.stage else tuple(PAIRS)
        labels = dict.fromkeys(label for stage in stages for label in PAIRS[stage])
        receipts, games = {}, {}
        for label in labels:
            receipts[label], games[label] = parse_run(args.raw, label, args.book, args.evidence)
        comparisons = {stage: compare(stage, receipts, games) for stage in stages}
        control = {stage: {"passes": comparisons[stage]["reading"] == expected}
                   for stage, expected in (("K38", "IDENTICAL"), ("C38", "DIFFERS")) if stage in comparisons}
        result = {"control": control, "runs": receipts, "comparisons": comparisons}
        if args.prediction:
            forecast = json.loads(args.prediction.read_text())
            result["prediction"] = {}
            for stage in ("G20", "G50", "G250"):
                if stage in comparisons:
                    expected = forecast[stage]
                    require(isinstance(expected, list) and len(expected) == 2 and
                            0 <= expected[0] <= expected[1] <= BASE[stage][1], f"{stage}: invalid forecast range")
                    observed = comparisons[stage]["differences"] if comparisons[stage]["all_played"] else None
                    grade = "ungraded" if observed is None else "met" if expected[0] <= observed <= expected[1] else "missed"
                    result["prediction"][stage] = {"forecast": expected, "observed": observed, "grade": grade}
        serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.json:
            args.json.write_text(serialized)
        print(serialized, end="")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
