"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.givesCheckQuiet = givesCheckQuiet;
const attacks_1 = require("./../board/attacks");
// ALIGN[a*64+b]: 0 none, 1 orthogonal, 2 diagonal. BTW_*: strictly-between squares. LINE_*: full line through a,b.
const ALIGN = new Uint8Array(4096);
const BTW_LO = new Uint32Array(4096), BTW_HI = new Uint32Array(4096);
const LINE_LO = new Uint32Array(4096), LINE_HI = new Uint32Array(4096);
(function init() {
    for (let a = 0; a < 64; a++)
        for (let b = 0; b < 64; b++) {
            if (a === b)
                continue;
            const df = (b & 7) - (a & 7), dr = (b >> 3) - (a >> 3);
            let t = 0;
            if (df === 0 || dr === 0)
                t = 1;
            else if (Math.abs(df) === Math.abs(dr))
                t = 2;
            if (!t)
                continue;
            const i = a * 64 + b;
            ALIGN[i] = t;
            const sf = Math.sign(df), sr = Math.sign(dr);
            for (let f = (a & 7) + sf, r = (a >> 3) + sr; f !== (b & 7) || r !== (b >> 3); f += sf, r += sr) {
                const s = r * 8 + f;
                if (s < 32)
                    BTW_LO[i] |= (1 << s) >>> 0;
                else
                    BTW_HI[i] |= (1 << (s - 32)) >>> 0;
            }
            for (let k = -7; k <= 7; k++) {
                const f = (a & 7) + sf * k, r = (a >> 3) + sr * k;
                if (f < 0 || f > 7 || r < 0 || r > 7)
                    continue;
                const s = r * 8 + f;
                if (s < 32)
                    LINE_LO[i] |= (1 << s) >>> 0;
                else
                    LINE_HI[i] |= (1 << (s - 32)) >>> 0;
            }
        }
})();
function hasBit(lo, hi, s) {
    return s < 32 ? ((lo >>> s) & 1) !== 0 : ((hi >>> (s - 32)) & 1) !== 0;
}
/** Exact "does m give check" for a legal quiet non-castle non-promo move. Callers must not pass castles/promos/ep. */
function givesCheckQuiet(b, m) {
    const from = typeof m === 'number' ? m & 63 : m.from;
    const to = typeof m === 'number' ? (m >>> 6) & 63 : m.to;
    const piece = typeof m === 'number' ? (m >>> 12) & 15 : m.piece;
    const white = b.side === 0 /* Color.White */;
    const ks = white ? b.blackKingSq : b.whiteKingSq;
    const occ = b.occupied;
    // occ' = occ - from + to (to is empty: quiet)
    const fLo = from < 32 ? (1 << from) >>> 0 : 0, fHi = from < 32 ? 0 : (1 << (from - 32)) >>> 0;
    // 1) direct check by the moved piece from `to`
    const p = piece;
    const pt = white ? p : p - 6;
    if (pt === 2) {
        const a = attacks_1.KNIGHT_ATTACKS[to];
        if (hasBit(a.lo, a.hi, ks))
            return true;
    }
    else if (pt === 1) {
        const a = white ? attacks_1.WHITE_PAWN_ATTACKS[to] : attacks_1.BLACK_PAWN_ATTACKS[to];
        if (hasBit(a.lo, a.hi, ks))
            return true;
    }
    else if (pt >= 3 && pt <= 5) {
        const al = ALIGN[to * 64 + ks];
        if (al !== 0 && (pt === 5 || (pt === 3 ? al === 2 : al === 1))) {
            const i = to * 64 + ks;
            // between squares empty in occ' (from vacated; to is an endpoint)
            if (((BTW_LO[i] & occ.lo & ~fLo) | (BTW_HI[i] & occ.hi & ~fHi)) === 0)
                return true;
        }
    }
    // 2) discovered check: from must be aligned with ks, first blocker from ks, and to off that line
    const fi = from * 64 + ks;
    const al = ALIGN[fi];
    if (al === 0)
        return false;
    if (hasBit(LINE_LO[fi], LINE_HI[fi], to))
        return false;
    if (((BTW_LO[fi] & occ.lo) | (BTW_HI[fi] & occ.hi)) !== 0)
        return false;
    const pb = b.pieceBB;
    const q = white ? pb[5 /* Piece.WQ */] : pb[11 /* Piece.BQ */];
    const s = al === 1 ? (white ? pb[4 /* Piece.WR */] : pb[10 /* Piece.BR */]) : (white ? pb[3 /* Piece.WB */] : pb[9 /* Piece.BB */]);
    // our sliders of the right type on the line beyond from (cheap prefilter)
    const cLo = (q.lo | s.lo) & LINE_LO[fi], cHi = (q.hi | s.hi) & LINE_HI[fi];
    if ((cLo | cHi) === 0)
        return false;
    const tLo = to < 32 ? (1 << to) >>> 0 : 0, tHi = to < 32 ? 0 : (1 << (to - 32)) >>> 0;
    const o = { lo: ((occ.lo & ~fLo) | tLo) >>> 0, hi: ((occ.hi & ~fHi) | tHi) >>> 0 };
    const att = al === 1 ? (0, attacks_1.rookAttacks)(ks, o) : (0, attacks_1.bishopAttacks)(ks, o);
    return ((att.lo & cLo) | (att.hi & cHi)) !== 0;
}
//# sourceMappingURL=givescheck.js.map
