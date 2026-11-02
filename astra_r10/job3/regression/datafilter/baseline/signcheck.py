"""Sign-convention guard. Stored `score` MUST be WHITE POV (cp, + = good for White).
check(recs, feats=None, n=1000) raises AssertionError if:
  (a) corr(material_white, score) <= 0.1   (White-POV material must correlate positively), or
  (b) mirror test fails: board.mirror() (vertical flip + colour swap + stm swap) re-encoded with score' = -score
      must give the same STM-relative target, and (if feats given) identical features for each perspective swapped."""
import numpy as np, chess
REC = np.dtype([('occ','<u8'),('pcs','u1',16),('stm','u1'),('castle','u1'),('score','<i2'),('ep','u1'),('rsv','u1',3)])
VAL = [1, 3, 3, 5, 9, 0]
def decode(r):
    b = chess.Board(None); occ = int(r['occ']); p = r['pcs']; i = 0
    for sq in range(64):
        if occ >> sq & 1:
            c = (p[i >> 1] >> (4 * (i & 1))) & 15; i += 1
            b.set_piece_at(sq, chess.Piece((c & 7) + 1, not (c >> 3)))
    b.turn = r['stm'] == 0; return b
def encode(b, score):
    r = np.zeros(1, REC); occ = int(b.occupied); nib = []
    for sq in chess.SquareSet(occ):
        q = b.piece_at(sq); nib.append((q.piece_type - 1) | (0 if q.color else 8))
    nib += [0] * (32 - len(nib)); r['occ'] = occ
    r['pcs'] = [nib[2*i] | (nib[2*i+1] << 4) for i in range(16)]; r['stm'] = 0 if b.turn else 1; r['score'] = score
    return r
def check(recs, feats=None, n=1000, min_corr=0.1):
    recs = np.asarray(recs[:n]); mat = []; mir = []
    for r in recs:
        b = decode(r)
        mat.append(sum(VAL[q.piece_type - 1] * (1 if q.color else -1) for q in b.piece_map().values()))
        mir.append(encode(b.mirror(), -int(r['score']))[0])
    sc = recs['score'].astype(float); corr = float(np.corrcoef(mat, sc)[0, 1])
    assert corr > min_corr, f'SIGN GUARD: corr(white material, score)={corr:.3f}; score is probably STM POV, not WHITE POV'
    mir = np.array(mir, REC)
    stm_t = lambda x: np.where(x['stm'] == 0, x['score'], -x['score'].astype(int))
    assert np.all(mir['score'] == -recs['score']) and np.all(mir['stm'] != recs['stm'])
    assert np.array_equal(stm_t(recs), stm_t(mir)), 'SIGN GUARD: mirror changed STM-relative target'
    if feats is not None:
        f0, f1 = feats(recs), feats(mir)  # (wi, bi, row, stm, tgt)
        assert np.array_equal(f0[4].numpy(), f1[4].numpy()), 'SIGN GUARD: trainer target not mirror-invariant'
        k = lambda wi, row: sorted(zip(row.tolist(), wi.tolist()))
        assert k(f0[0], f0[2]) == k(f1[1], f1[2]) and k(f0[1], f0[2]) == k(f1[0], f1[2]), 'SIGN GUARD: features not mirror-symmetric'
    return dict(n=len(recs), corr_white_material=round(corr, 3), mirror='ok')
