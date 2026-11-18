import argparse
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

import chess
import chess.pgn


OPENING_COUNT = 100
GAME_COUNT = 100
PLIES = (20, 50, 80)
BOOK_SHA256 = "7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a"
PGN_COMMIT = "dc44e1a3bfdc6bc348b41095eb343cdcf02bdd65"
PGN_GIT_BLOB = "3fa9e174e46f879c23b39127f2dd89b50ab759b0"
PGN_SHA256 = "dff8e8430de413eacb23bc41506d8028ba3aefa43fd6c2ec76a69f046a349315"


def verified_sha256(path, expected):
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"{path}: expected SHA-256 {expected}, got {actual}")
    return actual


parser = argparse.ArgumentParser(description="Build the fixed Job 3 FEN fixture.")
parser.add_argument("book", type=Path)
parser.add_argument("pgn", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()

book_sha = verified_sha256(args.book, BOOK_SHA256)
pgn_sha = verified_sha256(args.pgn, PGN_SHA256)

with args.book.open("rb") as book:
    openings = list(itertools.islice(book, OPENING_COUNT))
if len(openings) != OPENING_COUNT or any(not line.endswith(b"\n") for line in openings):
    raise ValueError("The book must supply 100 complete lines.")
for number, line in enumerate(openings, 1):
    board = chess.Board(line.decode("ascii").strip())
    if not board.is_valid():
        raise ValueError(f"Invalid opening FEN at book line {number}")

derived = []
counts = Counter({ply: 0 for ply in PLIES})
without_legal_moves = []
game_length_by_game = []
with args.pgn.open(encoding="utf-8") as pgn:
    for game_number in range(1, GAME_COUNT + 1):
        game = chess.pgn.read_game(pgn)
        if game is None or game.errors or "FEN" not in game.headers:
            raise ValueError(f"Missing or invalid PGN game {game_number}")
        board = chess.Board(game.headers["FEN"])
        if not board.is_valid():
            raise ValueError(f"Invalid starting FEN in PGN game {game_number}")
        ply = 0
        for ply, move in enumerate(game.mainline_moves(), 1):
            if move not in board.legal_moves:
                raise ValueError(f"Illegal move in PGN game {game_number}, ply {ply}: {move}")
            board.push(move)
            if ply in PLIES:
                counts[ply] += 1
                derived.append((board.fen(en_passant="fen") + "\n").encode("ascii"))
                if not any(board.legal_moves):
                    without_legal_moves.append({
                        "fixture_line": len(openings) + len(derived),
                        "pgn_game": game_number,
                        "ply": ply,
                    })
        game_length_by_game.append(ply)

fixture = b"".join(openings + derived)
args.output.write_bytes(fixture)
print(json.dumps({
    "book_upstream": "official-stockfish/books@37751b08db745aa02babfa74056dd1168b9da803",
    "book_sha256": book_sha,
    "book_lines_copied_verbatim": len(openings),
    "book_prefix_sha256": hashlib.sha256(b"".join(openings)).hexdigest(),
    "pgn_repo_and_commit": f"couns0538-sketch/dwqww@{PGN_COMMIT}",
    "pgn_path": "forge-combo29/sol/job13/raw/E2.pgn",
    "pgn_git_blob": PGN_GIT_BLOB,
    "pgn_sha256": pgn_sha,
    "pgn_games_in_file_order": GAME_COUNT,
    "pgn_selected_mainlines_verified_legal": True,
    "pgn_shortest_mainline_plies": min(game_length_by_game),
    "pgn_longest_mainline_plies": max(game_length_by_game),
    "derived_lines_by_ply": dict(counts),
    "derived_order": "PGN file order, then increasing ply within each game",
    "derived_en_passant": "FEN convention, with a target after every double pawn push",
    "derived_positions_without_legal_moves": without_legal_moves,
    "python_chess": chess.__version__,
    "fixture_lines": len(openings) + len(derived),
    "fixture_sha256": hashlib.sha256(fixture).hexdigest(),
}, indent=2))
