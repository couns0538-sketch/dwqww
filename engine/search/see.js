"use strict";
/** Static Exchange Evaluation */
Object.defineProperty(exports, "__esModule", { value: true });
exports.see = see;
exports.seeClassic = seeClassic;
exports.seeGe = seeGe;
const types_1 = require("../board/types");
const bitboard_1 = require("../board/bitboard");
const attacks_1 = require("../board/attacks");
const magics_1 = require("../board/magics");
const VAL = [0, 100, 320, 330, 500, 900, 20000, 100, 320, 330, 500, 900, 20000];
const GAIN = new Array(32);
/** SEE for move from→to. Returns net material for side to move. */
function see(board, from, to, promo = 0 /* Piece.None */) {
    return seeClassic(board, from, to, promo);
}
/** Classic iterative SEE with reusable gain buffer; scalar lo/hi, no bitboard object allocation */
function seeClassic(board, from, to, promo = 0 /* Piece.None */) {
    const gain = GAIN;
    let d = 0;
    const captured = board.squares[to];
    gain[d] = captured !== 0 /* Piece.None */ ? VAL[captured] : 0;
    if (promo)
        gain[d] += VAL[promo] - 100;
    const bt = bitboard_1.BIT_TABLE;
    const occ0 = board.occupied;
    let oLo = occ0.lo, oHi = occ0.hi;
    const fb = bt[from];
    oLo = (oLo ^ fb.lo) >>> 0;
    oHi = (oHi ^ fb.hi) >>> 0;
    if (captured !== 0 /* Piece.None */) {
        const tb = bt[to];
        oLo = (oLo ^ tb.lo) >>> 0;
        oHi = (oHi ^ tb.hi) >>> 0;
    }
    let side = board.side === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */;
    const pbb = board.pieceBB, cbb = board.colorBB;
    // static (occupancy independent) attackers
    const sp1 = attacks_1.BLACK_PAWN_ATTACKS[to], sp2 = attacks_1.WHITE_PAWN_ATTACKS[to], kn = attacks_1.KNIGHT_ATTACKS[to], kg = attacks_1.KING_ATTACKS[to];
    const wp = pbb[1 /* Piece.WP */], bp = pbb[7 /* Piece.BP */], wn = pbb[2 /* Piece.WN */], bn = pbb[8 /* Piece.BN */], wk = pbb[6 /* Piece.WK */], bk = pbb[12 /* Piece.BK */];
    const stLo = ((sp1.lo & wp.lo) | (sp2.lo & bp.lo) | (kn.lo & (wn.lo | bn.lo)) | (kg.lo & (wk.lo | bk.lo))) >>> 0;
    const stHi = ((sp1.hi & wp.hi) | (sp2.hi & bp.hi) | (kn.hi & (wn.hi | bn.hi)) | (kg.hi & (wk.hi | bk.hi))) >>> 0;
    const diagLo = (pbb[3 /* Piece.WB */].lo | pbb[9 /* Piece.BB */].lo | pbb[5 /* Piece.WQ */].lo | pbb[11 /* Piece.BQ */].lo) >>> 0;
    const diagHi = (pbb[3 /* Piece.WB */].hi | pbb[9 /* Piece.BB */].hi | pbb[5 /* Piece.WQ */].hi | pbb[11 /* Piece.BQ */].hi) >>> 0;
    const orthLo = (pbb[4 /* Piece.WR */].lo | pbb[10 /* Piece.BR */].lo | pbb[5 /* Piece.WQ */].lo | pbb[11 /* Piece.BQ */].lo) >>> 0;
    const orthHi = (pbb[4 /* Piece.WR */].hi | pbb[10 /* Piece.BR */].hi | pbb[5 /* Piece.WQ */].hi | pbb[11 /* Piece.BQ */].hi) >>> 0;
    const BL = magics_1.BISHOP_LO, BH = magics_1.BISHOP_HI, RL = magics_1.ROOK_LO, RH = magics_1.ROOK_HI;
    let aLo, aHi;
    {
        const bi = (0, magics_1.bishopIdx)(to, oLo, oHi), ri = (0, magics_1.rookIdx)(to, oLo, oHi);
        aLo = (stLo | (BL[bi] & diagLo) | (RL[ri] & orthLo)) >>> 0;
        aHi = (stHi | (BH[bi] & diagHi) | (RH[ri] & orthHi)) >>> 0;
    }
    let movedPiece = promo || board.squares[from];
    while (true) {
        d++;
        gain[d] = VAL[movedPiece] - gain[d - 1];
        aLo = (aLo & oLo) >>> 0;
        aHi = (aHi & oHi) >>> 0;
        const c = cbb[side];
        const myLo = (aLo & c.lo) >>> 0, myHi = (aHi & c.hi) >>> 0;
        if (myLo === 0 && myHi === 0)
            break;
        let bestSq = -1;
        let bestPiece = 0;
        for (let pt = 1; pt <= 6; pt++) {
            const p = side === 0 /* Color.White */ ? pt : pt + 6;
            const pb = pbb[p];
            const l = (myLo & pb.lo) >>> 0, h = (myHi & pb.hi) >>> 0;
            if (l !== 0 || h !== 0) {
                bestSq = l !== 0 ? 31 - Math.clz32(l & -l) : 32 + 31 - Math.clz32(h & -h);
                bestPiece = p;
                break;
            }
        }
        if (bestSq < 0)
            break;
        const bb2 = bt[bestSq];
        oLo = (oLo ^ bb2.lo) >>> 0;
        oHi = (oHi ^ bb2.hi) >>> 0;
        // X-rays: always recompute sliders
        const bi = (0, magics_1.bishopIdx)(to, oLo, oHi), ri = (0, magics_1.rookIdx)(to, oLo, oHi);
        aLo = (stLo | (BL[bi] & diagLo) | (RL[ri] & orthLo)) >>> 0;
        aHi = (stHi | (BH[bi] & diagHi) | (RH[ri] & orthHi)) >>> 0;
        side = 1 - side;
        movedPiece = bestPiece;
        if ((0, types_1.pieceType)(bestPiece) === 6)
            break;
        if (d >= 31)
            break;
    }
    while (--d) {
        gain[d - 1] = -Math.max(-gain[d - 1], gain[d]);
    }
    return gain[0];
}
/** True if SEE >= threshold (avoids full fold when possible via early reject). */
function seeGe(board, from, to, threshold, promo = 0 /* Piece.None */) {
    return seeClassic(board, from, to, promo) >= threshold;
}
//# sourceMappingURL=see.js.map
