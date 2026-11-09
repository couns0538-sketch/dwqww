#!/usr/bin/env python3
"""oracle_chess.py - expected values from python-chess 1.11.2 chess.syzygy, a separate test oracle (GPL-3.0, no code
copied; the same use as R13 P6). One JSON line per FEN: wdl and dtz of the root, and for each legal root move: uci, zeroing,
mate, stalemate, child wdl, child dtz (None if the position has no table). Pawn moves, captures and promotions are zeroing.

usage: python -I -B oracle_chess.py <tables dir> <fens file> <out.jsonl>
FEN lines may carry " moves ..." which are played first. rule-50 outcome helpers live in fixture tools, not here.
"""
import json
import os
import sys

import chess
import chess.syzygy


def probe(tb, board):
    if board.castling_rights:
        return None, None
    try:
        return tb.probe_wdl(board), tb.probe_dtz(board)
    except (chess.syzygy.MissingTableError, KeyError):
        return None, None


def main():
    tables, fens, out = sys.argv[1:4]
    if os.path.exists(out):
        print(f'refusing: {out} exists')
        sys.exit(2)
    tb = chess.syzygy.open_tablebase(tables)
    n = 0
    with open(out, 'w', encoding='utf-8') as f:
        for line in open(fens, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split(' moves ')
            board = chess.Board(parts[0])
            if len(parts) > 1:
                for u in parts[1].split():
                    board.push_uci(u)
            wdl, dtz = probe(tb, board)
            row = {'fen': line, 'board_fen': board.fen(), 'wdl': wdl, 'dtz': dtz, 'clock': board.halfmove_clock,
                   'valid': board.is_valid(), 'ep': board.has_legal_en_passant(), 'moves': []}
            for move in board.legal_moves:
                zeroing = board.is_zeroing(move)
                board.push(move)
                w, d = probe(tb, board)
                row['moves'].append({'uci': move.uci(), 'zeroing': zeroing, 'mate': board.is_checkmate(),
                                     'stalemate': board.is_stalemate(), 'child_wdl': w, 'child_dtz': d})
                board.pop()
            f.write(json.dumps(row) + '\n')
            n += 1
    print(f'oracle rows {n}')


if __name__ == '__main__':
    main()
