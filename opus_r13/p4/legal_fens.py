"""legal_fens.py - R14 (CR R13 delta for P4): write a legal-only copy of a FEN file for the parity runs.

A FEN is kept only when python-chess (GPL-3.0, run-only test oracle; nothing of it goes into Forge) parses it and
Board.status() is STATUS_VALID (kings, pawns on the back rank, side not to move in check, castling rights that match the
king/rook squares, a valid en-passant square, possible checkers). Kept lines are written unchanged and in order.
usage: legal_fens.py <in.txt> <out.txt>   -> prints counts per reject reason; exit 1 when nothing is kept or out exists.
"""
import collections
import pathlib
import sys

import chess


def main() -> int:
    src, dst = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if dst.exists():
        print(f'refusing to overwrite {dst}')
        return 1
    kept, reasons = [], collections.Counter()
    lines = src.read_text(encoding='utf-8').splitlines()
    for line in lines:
        fen = line.strip()
        if not fen:
            reasons['empty line'] += 1
            continue
        try:
            status = chess.Board(fen).status()
        except ValueError:
            reasons['unparsable'] += 1
            continue
        if status != chess.STATUS_VALID:
            names = [n for n in dir(chess) if n.startswith('STATUS_') and n != 'STATUS_VALID' and status & getattr(chess, n)]
            reasons['+'.join(names) or str(int(status))] += 1
            continue
        kept.append(fen)
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(fen + '\n' for fen in kept)
    print(f'{src}: {len(lines)} lines, kept {len(kept)} legal, rejected {sum(reasons.values())}')
    for reason, count in sorted(reasons.items()):
        print(f'  rejected {count}: {reason}')
    return 0 if kept else 1


if __name__ == '__main__':
    sys.exit(main())
