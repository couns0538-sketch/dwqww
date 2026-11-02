"""Shared 32-byte record encoder (identical to filter_lichess.py inline encoding)."""
import numpy as np, chess
REC = np.dtype([('occ','<u8'),('pcs','u1',16),('stm','u1'),('castle','u1'),('score','<i2'),('ep','u1'),('rsv','u1',3)])
def encode_board(b, w):
    r = np.zeros(1, REC); occ = int(b.occupied); nib = []
    for sq in chess.SquareSet(occ):
        p = b.piece_at(sq); nib.append((p.piece_type - 1) | (0 if p.color else 8))
    nib += [0] * (32 - len(nib)); r['occ'] = occ; r['pcs'] = [nib[2*i] | (nib[2*i+1] << 4) for i in range(16)]
    r['stm'] = 0 if b.turn else 1
    r['castle'] = (b.has_kingside_castling_rights(1) | b.has_queenside_castling_rights(1) << 1 |
                   b.has_kingside_castling_rights(0) << 2 | b.has_queenside_castling_rights(0) << 3)
    r['ep'] = b.ep_square if b.ep_square is not None else 255; r['score'] = w; return r
