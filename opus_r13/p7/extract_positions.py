#!/usr/bin/env python3
"""extract_positions.py - R13 P7 (own code): sampled positions + game results from the crew's own gate PGNs.

usage: python -I -B extract_positions.py <out_prefix> <pgn> [<pgn> ...] [--every 3] [--min-ply 16] [--max-games 0]
Writes <out_prefix>.fens (one FEN per line, with the real halfmove clock) and <out_prefix>.tsv
(game_id, ply, stm_result (1 / 0.5 / 0 from the side to move), material (E3 formula), clock, pgn file, round).
Rules: games with a 1-0 / 0-1 / 1/2-1/2 result only; positions from ply --min-ply on (past the book), every --every-th
ply, side to move not in check, no checkmate / stalemate positions. Game id = sha1 of (pgn file name, game index): the
80/20 split by game is done in fit_e3.py from that id.
Dedupe (CR R13): a game whose result + full move list was already seen (in any file: gate folders hold reruns
and copies) is skipped and counted; the same opening played twice with colours swapped is two different games. python-chess (installed in the crew venv) is used as a PGN reader
tool only (GPL; nothing copied into Forge).
R14 (CR patch 129d440e): a game the PGN reader flags with errors (illegal or unparsable moves) is skipped and counted.
E3 material (src/search.cpp e3_material): sum of PieceValueMg {P 82, N 337, B 365, R 477, Q 1025} over the pieces of
both sides, kings excluded, capped at the starting total.
"""
import argparse
import hashlib
import os

import chess
import chess.pgn

VALUE = {chess.PAWN: 82, chess.KNIGHT: 337, chess.BISHOP: 365, chess.ROOK: 477, chess.QUEEN: 1025}
START = 2 * (8 * 82 + 2 * 337 + 2 * 365 + 2 * 477 + 1025)


def material(board):
    m = sum(VALUE[p.piece_type] for p in board.piece_map().values() if p.piece_type != chess.KING)
    return min(m, START)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('pgns', nargs='+')
    ap.add_argument('--every', type=int, default=3)
    ap.add_argument('--min-ply', type=int, default=16)
    ap.add_argument('--max-games', type=int, default=0)
    a = ap.parse_args()
    for ext in ('.fens', '.tsv'):
        if os.path.exists(a.out + ext):
            raise SystemExit(f'refusing to overwrite {a.out + ext}')
    games = positions = dups = bad = 0
    seen = set()
    with open(a.out + '.fens', 'w', newline='\n') as ffen, open(a.out + '.tsv', 'w', newline='\n') as ftsv:
        ftsv.write('game_id\tply\tstm_result\tmaterial\tclock\tpgn\tround\n')
        for path in a.pgns:
            name = os.path.basename(path)
            with open(path, encoding='utf-8', errors='replace') as fh:
                index = 0
                while True:
                    game = chess.pgn.read_game(fh)
                    if game is None:
                        break
                    index += 1
                    result = game.headers.get('Result', '*')
                    white = {'1-0': 1.0, '0-1': 0.0, '1/2-1/2': 0.5}.get(result)
                    if white is None:
                        continue
                    if game.errors:
                        bad += 1
                        continue
                    moves = list(game.mainline_moves())
                    key = hashlib.sha1((result + ' ' + game.board().fen() + ' ' + ' '.join(m.uci() for m in moves)).encode()).digest()
                    if key in seen:
                        dups += 1
                        continue
                    seen.add(key)
                    gid = hashlib.sha1(f'{name}#{index}'.encode()).hexdigest()[:16]
                    board = game.board()
                    ply = 0
                    for move in moves:
                        board.push(move)
                        ply += 1
                        if ply < a.min_ply or ply % a.every or board.is_check() or board.is_game_over():
                            continue
                        stm = white if board.turn == chess.WHITE else 1.0 - white
                        ffen.write(board.fen() + '\n')
                        ftsv.write(f'{gid}\t{ply}\t{stm}\t{material(board)}\t{board.halfmove_clock}\t{name}\t{game.headers.get("Round", "")}\n')
                        positions += 1
                    games += 1
                    if a.max_games and games >= a.max_games:
                        break
            if a.max_games and games >= a.max_games:
                break
    if games == 0 or positions == 0:
        raise SystemExit('no games / positions extracted')
    print(f'{games} games ({dups} duplicate games skipped, {bad} games skipped for PGN errors), {positions} positions'
          f' -> {a.out}.fens / .tsv')


if __name__ == '__main__':
    main()
