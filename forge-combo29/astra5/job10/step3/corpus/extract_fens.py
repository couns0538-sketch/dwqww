"""Replay Fastchess PGN in source PGN record order. Requires chess==1.11.2."""
import argparse
import csv
import hashlib
from pathlib import Path
import re

import chess
import chess.pgn


SCORE = re.compile(r"^Finished game (\d+) \(([^()]+) vs ([^()]+)\): (1-0|0-1|1/2-1/2) ")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schedule(path):
    records = {}
    for line in path.read_text().splitlines():
        m = SCORE.match(line)
        if m:
            i = int(m[1])
            if i in records:
                raise ValueError(f"Duplicate game number {i} in runner output")
            records[i] = m.groups()[1:]
    if sorted(records) != list(range(1, len(records)+1)) or not records:
        raise ValueError("Game IDs in runner output are missing or nonconsecutive")
    return records


def index_headers(stream, records, first):
    games = {}
    physical = 0
    while True:
        loc = stream.tell()
        headers = chess.pgn.read_headers(stream)
        if headers is None:
            break
        physical += 1
        number = 2 * int(headers["Round"]) - (headers["White"] == first)
        triplet = tuple(headers[key] for key in ("White","Black","Result"))
        if number in games or records.get(number) != triplet:
            raise ValueError(f"PGN record {physical} disagrees with runner for game {number}")
        games[number] = (loc, physical)
    if games.keys() != records.keys():
        raise ValueError("PGN and runner contain different game IDs")
    return games


def sample(pgn, runner_output, first, amount, output):
    output.mkdir(exist_ok=True, parents=True)
    records = schedule(runner_output)
    positions = []
    mapping = []
    visited = 0
    no_legal = 0
    terminal_records = 0
    with pgn.open(encoding="utf-8") as stream:
        games = index_headers(stream, records, first)
        for game_id in sorted(games, key=lambda n: games[n][1]):
            offset, physical = games[game_id]
            stream.seek(offset)
            game = chess.pgn.read_game(stream)
            if game.errors:
                raise ValueError(f"Illegal or unreadable game {game_id}: {game.errors}")
            board = game.board()
            if not board.is_valid():
                raise ValueError(f"Invalid starting board in game {game_id}")
            moves = list(game.mainline_moves())
            if len(moves) != int(game.headers["PlyCount"]):
                raise ValueError(f"PlyCount disagrees with movetext in game {game_id}")
            visited += 1
            for ply, move in enumerate(moves, start=1):
                if not board.is_legal(move):
                    raise ValueError(f"Illegal move {move} in game {game_id} at played ply {ply}")
                board.push(move)
                if ply % 10:
                    continue
                fen = board.fen(en_passant="fen")
                reconstructed = chess.Board(fen)
                if not reconstructed.is_valid() or fen != reconstructed.fen(en_passant="fen"):
                    raise ValueError(f"FEN failed round-trip in game {game_id} at played ply {ply}")
                final = ply == len(moves)
                immobile = not any(board.legal_moves)
                no_legal += immobile
                terminal_records += final
                positions.append(fen)
                mapping.append((len(positions), game_id, game.headers["Round"], game.headers["White"], physical,
                                ply, len(moves), move.uci(), int(final), int(immobile)))
                if len(positions) == amount:
                    break
            if len(positions) == amount:
                break
    if len(positions) != amount:
        raise ValueError(f"Only {len(positions)} positions available, requested {amount}")
    fenpath = output/"game_positions.fen"
    with fenpath.open("x", newline="\n") as f:
        for fen in positions:
            print(fen,file=f)
    with (output/"source-map.tsv").open("x", newline="") as f:
        writer=csv.writer(f,delimiter="\t",lineterminator="\n")
        writer.writerow(("index","scheduled_game","round","white","physical_pgn_record","played_ply","plies_in_game","last_move_uci","pgn_game_ends_here","no_legal_move"))
        writer.writerows(mapping)
    (output/"game_positions.sha256").write_text(f"{digest(fenpath)}  {fenpath.name}\n")
    lines = [
        f"FEN count {len(positions)}; distinct six-field FENs {len(set(positions))}. Duplicate rows were retained.",
        f"SHA-256 {digest(fenpath)}  {fenpath.name}",
        f"sha256 {digest(pgn)}  {pgn.name}",f"sha256 {digest(runner_output)}  {runner_output.name}",
        f"Validated every one of {len(records)} scheduled IDs against the PGN round, White, Black and result. Games replayed {visited}.",
        f"Order is the physical record sequence in the committed PGN. Fastchess finished concurrent games out of scheduled order. The mapping also records scheduled game ID (2*Round-1 for White={first}, 2*Round otherwise); no reordering by that ID.",
        "Replay starts at each game's supplied opening FEN. Sample the board after played plies 10, 20, 30, ... . The opening FEN is ply zero and is not sampled.",
        "Write six standard FEN fields, including a double-push en-passant target even when no pawn can capture. Preserve castling, move clocks, counters, repeats and game-end positions.",
        f"Selected PGN final positions {terminal_records}; selected positions with no legal move {no_legal}.",
        f"First sample PGN record {mapping[0][4]}, scheduled game {mapping[0][1]}, played ply {mapping[0][5]}; last sample PGN record {mapping[-1][4]}, scheduled game {mapping[-1][1]}, played ply {mapping[-1][5]}.",
        f"Parser chess=={chess.__version__}; ordered mainline legal moves only; exported FENs validated by parse and reserialization.",
    ]
    (output/"extraction.txt").write_text("\n".join(lines)+"\n")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pgn",type=Path)
    parser.add_argument("fastchess_output",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--first-engine",default="M1-A")
    parser.add_argument("--count",type=int,default=2000)
    args=parser.parse_args()
    if args.count <= 0:
        parser.error("--count must be positive")
    sample(args.pgn,args.fastchess_output,args.first_engine,args.count,args.output)

if __name__=="__main__":
    main()
