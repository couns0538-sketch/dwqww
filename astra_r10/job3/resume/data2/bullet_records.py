"""Original bulletformat encoder with an explicit lossless sidecar contract.

IDEA_SOURCE: MIT bulletformat ChessBoard wire layout at eddd9a2d77dbc1391d68f23ba524657e91bd9a73.
The native 32-byte layout cannot encode original STM, rights, EP or clocks.
Keep the aligned six-field FEN sidecar; never claim standalone FEN recovery.
"""
from __future__ import annotations
import struct

PACK = struct.Struct('<Q16shBBB3s')


def encode(record):
    stm = record.meta & 1
    squares = []
    for sq in range(64):
        pc = (record.board[sq // 2] >> (4 * (sq % 2))) & 15
        if pc:
            color, piece = divmod(pc - 1, 6)
            squares.append((sq ^ (56 if stm else 0), ((color ^ stm) << 3) | piece))
    if len(squares) > 32:
        raise ValueError('bulletformat permits at most32pieces')
    squares.sort()
    ours = [sq for sq, pc in squares if pc == 5]
    theirs = [sq for sq, pc in squares if pc == 13]
    if len(ours) != 1 or len(theirs) != 1:
        raise ValueError('exactly one king per side required')
    pieces = bytearray(16)
    occ = 0
    for i, (sq, pc) in enumerate(squares):
        occ |= 1 << sq
        pieces[i // 2] |= pc << (4 * (i % 2))
    white_result = record.meta >> 1
    result = 2 - white_result if stm else white_result
    return PACK.pack(occ, pieces, record.score, result, ours[0], theirs[0] ^ 56, b'\0' * 3)


def verify_record(raw, record):
    if len(raw) != 32 or raw != encode(record):
        raise ValueError('bullet record differs from sidecar board/STM/score/result')
