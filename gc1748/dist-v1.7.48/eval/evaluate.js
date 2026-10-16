"use strict";
/** Static evaluation — incremental material/PST + pawns/mobility/king/space */
Object.defineProperty(exports, "__esModule", { value: true });
exports.evaluateFast = void 0;
exports.clearEvalCaches = clearEvalCaches;
exports.evaluate = evaluate;
exports.evaluateQ = evaluateQ;
const bitboard_1 = require("../board/bitboard");
const attacks_1 = require("../board/attacks");
const magics_1 = require("../board/magics");
const weights_1 = require("./weights");
const nnue_1 = require("./nnue");
const pawnhash_1 = require("./pawnhash");
const SM_BASE_N = 4, SM_BASE_B = 6, SM_BASE_R = 7, SM_BASE_Q = 13; // eval5-A mobility baselines (constants)
const EVAL_CACHE_MASK = (1 << 18) - 1;
const evalKeysHi = new Int32Array(1 << 18);
const evalKeysLo = new Int32Array(1 << 18);
const evalScores = new Int32Array(1 << 18);
let evalCacheGen = -1;
/** Clear eval + pawn caches (needed when weights change at runtime, e.g. tuning/tests) */
function clearEvalCaches() {
    evalKeysHi.fill(0);
    evalKeysLo.fill(0);
    evalScores.fill(0);
    (0, pawnhash_1.clearPawnCache)();
}
function oneBit(x) {
    const l = x.lo | 0, h = x.hi | 0;
    return (l === 0 && h !== 0 && (h & (h - 1)) === 0) || (h === 0 && l !== 0 && (l & (l - 1)) === 0);
}
function bareKing(board) {
    return oneBit(board.colorBB[0]) || oneBit(board.colorBB[1]);
}
function evaluate(board) {
    // nnue-bk: bare-king endings (one side has only its king) use the HCE (mop-up / mate distance); UNPROVEN
    // nncache: NNUE result goes through the same eval cache (cache dropped when net/UseNNUE changes); UNPROVEN
    const g = (0, nnue_1.nnueGen)();
    if (g !== evalCacheGen) {
        evalKeysHi.fill(0);
        evalKeysLo.fill(0);
        evalCacheGen = g;
    }
    const kHi = board.zHi, kLo = board.zLo;
    const idx = kLo & EVAL_CACHE_MASK;
    const nz = (kHi | kLo) !== 0;
    if (nz && evalKeysLo[idx] === kLo && evalKeysHi[idx] === kHi)
        return evalScores[idx];
    if ((0, nnue_1.nnueActive)() && !bareKing(board)) {
        const nv = (0, nnue_1.nnueEvaluate)(board);
        if (nz) {
            evalKeysHi[idx] = kHi;
            evalKeysLo[idx] = kLo;
            evalScores[idx] = nv;
        }
        return nv;
    }
    let mg = board.mgScore;
    let eg = board.egScore;
    let phase = board.phase;
    if (phase > 24)
        phase = 24;
    if (phase < 0)
        phase = 0;
    const wPawns = board.pieceBB[1 /* Piece.WP */];
    const bPawns = board.pieceBB[7 /* Piece.BP */];
    // Bishop pair
    if ((0, bitboard_1.popcount)(board.pieceBB[3 /* Piece.WB */]) >= 2) {
        mg += weights_1.W.bishopPairMg;
        eg += weights_1.W.bishopPairEg;
    }
    if ((0, bitboard_1.popcount)(board.pieceBB[9 /* Piece.BB */]) >= 2) {
        mg -= weights_1.W.bishopPairMg;
        eg -= weights_1.W.bishopPairEg;
    }
    const wl = wPawns.lo, wh = wPawns.hi, bl = bPawns.lo, bh = bPawns.hi;
    const pi = (0, pawnhash_1.probePawnIdx)(wl, wh, bl, bh);
    let waL, waH, baL, baH;
    if (pi < 0) {
        const pr = evalPawns(wPawns, bPawns);
        (0, pawnhash_1.storePawnIdx)(pi, wl, wh, bl, bh, pr.mg, pr.eg, pr.wpa, pr.bpa);
        mg += pr.mg;
        eg += pr.eg;
        waL = pr.wpa.lo;
        waH = pr.wpa.hi;
        baL = pr.bpa.lo;
        baH = pr.bpa.hi;
    }
    else {
        mg += (0, pawnhash_1.pawnMg)(pi);
        eg += (0, pawnhash_1.pawnEg)(pi);
        waL = pawnhash_1.aWL[pi];
        waH = pawnhash_1.aWH[pi];
        baL = pawnhash_1.aBL[pi];
        baH = pawnhash_1.aBH[pi];
    }
    evalRest(board, wPawns, bPawns, waL, waH, baL, baH);
    mg += restMg;
    eg += restEg;
    let score = ((mg * phase + eg * (24 - phase)) / 24) | 0;
    score += board.side === 0 /* Color.White */ ? weights_1.W.tempo : -weights_1.W.tempo;
    const stm = board.side === 0 /* Color.White */ ? score : -score;
    if (nz) {
        evalKeysHi[idx] = kHi;
        evalKeysLo[idx] = kLo;
        evalScores[idx] = stm;
    }
    return stm;
}
function evalPawns(wPawns, bPawns) {
    let mg = 0, eg = 0;
    let waL = 0, waH = 0, baL = 0, baH = 0;
    const pMg = P_MG, pEg = P_EG;
    pMg[1] = weights_1.W.passedMg1;
    pMg[2] = weights_1.W.passedMg2;
    pMg[3] = weights_1.W.passedMg3;
    pMg[4] = weights_1.W.passedMg4;
    pMg[5] = weights_1.W.passedMg5;
    pMg[6] = weights_1.W.passedMg6;
    pEg[1] = weights_1.W.passedEg1;
    pEg[2] = weights_1.W.passedEg2;
    pEg[3] = weights_1.W.passedEg3;
    pEg[4] = weights_1.W.passedEg4;
    pEg[5] = weights_1.W.passedEg5;
    pEg[6] = weights_1.W.passedEg6;
    const wl = wPawns.lo, wh = wPawns.hi, bl = bPawns.lo, bh = bPawns.hi;
    for (let l = wl, h = wh; (l | h) !== 0;) {
        let sq;
        if (l !== 0) {
            const t = l & -l;
            sq = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            sq = 63 - Math.clz32(t);
            h ^= t;
        }
        const pa = attacks_1.WHITE_PAWN_ATTACKS[sq];
        waL |= pa.lo;
        waH |= pa.hi;
        const f = sq & 7, r = sq >> 3;
        const bh_ = BEHIND_W[sq];
        if (((wl & bh_.lo) | (wh & bh_.hi)) !== 0) {
            mg -= weights_1.W.doubledMg;
            eg -= weights_1.W.doubledEg;
        }
        const nb = ADJ_FILES[f];
        if (((wl & nb.lo) | (wh & nb.hi)) === 0) {
            mg -= weights_1.W.isolatedMg;
            eg -= weights_1.W.isolatedEg;
        }
        else if ((f > 0 && hasSq(wl, wh, sq - 1)) || (f < 7 && hasSq(wl, wh, sq + 1))) {
            mg += weights_1.W.connectedMg;
            eg += weights_1.W.connectedEg;
        }
        const fs = FP_PASS_W[sq];
        if (((bl & fs.lo) | (bh & fs.hi)) === 0) {
            mg += pMg[r];
            eg += pEg[r];
        }
        if (r >= 4)
            mg += weights_1.W.spacePerSq;
    }
    for (let l = bl, h = bh; (l | h) !== 0;) {
        let sq;
        if (l !== 0) {
            const t = l & -l;
            sq = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            sq = 63 - Math.clz32(t);
            h ^= t;
        }
        const pa = attacks_1.BLACK_PAWN_ATTACKS[sq];
        baL |= pa.lo;
        baH |= pa.hi;
        const f = sq & 7, r = sq >> 3;
        const ab = BEHIND_B[sq];
        if (((bl & ab.lo) | (bh & ab.hi)) !== 0) {
            mg += weights_1.W.doubledMg;
            eg += weights_1.W.doubledEg;
        }
        const nb = ADJ_FILES[f];
        if (((bl & nb.lo) | (bh & nb.hi)) === 0) {
            mg += weights_1.W.isolatedMg;
            eg += weights_1.W.isolatedEg;
        }
        else if ((f > 0 && hasSq(bl, bh, sq - 1)) || (f < 7 && hasSq(bl, bh, sq + 1))) {
            mg -= weights_1.W.connectedMg;
            eg -= weights_1.W.connectedEg;
        }
        const fs = FP_PASS_B[sq];
        if (((wl & fs.lo) | (wh & fs.hi)) === 0) {
            mg -= pMg[7 - r];
            eg -= pEg[7 - r];
        }
        if (r <= 3)
            mg -= weights_1.W.spacePerSq;
    }
    return { mg, eg, wpa: { lo: waL >>> 0, hi: waH >>> 0 }, bpa: { lo: baL >>> 0, hi: baH >>> 0 } };
}
function hasSq(lo, hi, sq) { return sq < 32 ? ((lo >>> sq) & 1) === 1 : ((hi >>> (sq - 32)) & 1) === 1; }
function pop32(v) { v = v - ((v >>> 1) & 0x55555555); v = (v & 0x33333333) + ((v >>> 2) & 0x33333333); return (((v + (v >>> 4)) & 0x0f0f0f0f) * 0x01010101) >>> 24; }
// precomputed pawn-structure masks (identical semantics to the former per-pawn loops)
const P_MG = new Int32Array(8), P_EG = new Int32Array(8);
const FP_PASS_W = [], FP_PASS_B = [], BEHIND_W = [], BEHIND_B = [], ADJ_FILES = [];
(function initPawnMasks() {
    const mk = (sq, dir, adj) => {
        let lo = 0, hi = 0;
        const f = sq & 7;
        for (let r = (sq >> 3) + dir; r >= 0 && r < 8; r += dir)
            for (let ff = adj ? Math.max(0, f - 1) : f; ff <= (adj ? Math.min(7, f + 1) : f); ff++) {
                const q = r * 8 + ff;
                if (q < 32)
                    lo |= 1 << q;
                else
                    hi |= 1 << (q - 32);
            }
        return { lo: lo >>> 0, hi: hi >>> 0 };
    };
    for (let sq = 0; sq < 64; sq++) {
        FP_PASS_W[sq] = mk(sq, 1, true);
        FP_PASS_B[sq] = mk(sq, -1, true);
        BEHIND_W[sq] = mk(sq, -1, false);
        BEHIND_B[sq] = mk(sq, 1, false);
    }
    for (let f = 0; f < 8; f++) {
        let lo = 0, hi = 0;
        for (const ff of [f - 1, f + 1])
            if (ff >= 0 && ff <= 7)
                for (let r = 0; r < 8; r++) {
                    const q = r * 8 + ff;
                    if (q < 32)
                        lo |= 1 << q;
                    else
                        hi |= 1 << (q - 32);
                }
        ADJ_FILES[f] = { lo: lo >>> 0, hi: hi >>> 0 };
    }
})();
// evalfast-1729: allocation-free evalRest (u32 halves, no BB temporaries, results via module scratch)
let restMg = 0, restEg = 0;
// king zone (king attacks + king square) per square, as u32 halves
const KZ_LO = new Int32Array(64), KZ_HI = new Int32Array(64);
// king shelter masks: near rank (r+dir) and far rank (r+2*dir) on files f-1..f+1, per [dir][sq]
const SH_NEAR_LO = new Int32Array(128), SH_NEAR_HI = new Int32Array(128), SH_FAR_LO = new Int32Array(128), SH_FAR_HI = new Int32Array(128);
const FM_LO = new Int32Array(8), FM_HI = new Int32Array(8);
(function initRestTables() {
    for (let f = 0; f < 8; f++) {
        FM_LO[f] = bitboard_1.FILE_MASKS[f].lo | 0;
        FM_HI[f] = bitboard_1.FILE_MASKS[f].hi | 0;
    }
    for (let sq = 0; sq < 64; sq++) {
        const ka = attacks_1.KING_ATTACKS[sq], b = (0, bitboard_1.bit)(sq);
        KZ_LO[sq] = (ka.lo | b.lo) | 0;
        KZ_HI[sq] = (ka.hi | b.hi) | 0;
        const f = sq & 7, r = sq >> 3;
        for (let di = 0; di < 2; di++) {
            const dir = di === 0 ? 1 : -1;
            const k = di * 64 + sq;
            for (let df = -1; df <= 1; df++) {
                const ff = f + df;
                if (ff < 0 || ff > 7)
                    continue;
                const s1 = (r + dir) * 8 + ff, s2 = (r + 2 * dir) * 8 + ff;
                if (s1 >= 0 && s1 < 64) {
                    if (s1 < 32)
                        SH_NEAR_LO[k] |= 1 << s1;
                    else
                        SH_NEAR_HI[k] |= 1 << (s1 - 32);
                }
                if (s2 >= 0 && s2 < 64) {
                    if (s2 < 32)
                        SH_FAR_LO[k] |= 1 << s2;
                    else
                        SH_FAR_HI[k] |= 1 << (s2 - 32);
                }
            }
        }
    }
})();
function evalRest(board, wPawns, bPawns, waL, waH, baL, baH) {
    let mg = 0, eg = 0;
    const occ = board.occupied;
    const wKing = board.whiteKingSq;
    const bKing = board.blackKingSq;
    const wKZl = wKing < 64 ? KZ_LO[wKing] : 0, wKZh = wKing < 64 ? KZ_HI[wKing] : 0;
    const bKZl = bKing < 64 ? KZ_LO[bKing] : 0, bKZh = bKing < 64 ? KZ_HI[bKing] : 0;
    const cw = board.colorBB[0 /* Color.White */], cb = board.colorBB[1 /* Color.Black */];
    const nWl = ~cw.lo, nWh = ~cw.hi, nBl = ~cb.lo, nBh = ~cb.hi;
    const act5 = (weights_1.W.safeMobNMg | weights_1.W.safeMobNEg | weights_1.W.safeMobBMg | weights_1.W.safeMobBEg | weights_1.W.safeMobRMg | weights_1.W.safeMobREg | weights_1.W.safeMobQMg | weights_1.W.safeMobQEg |
        weights_1.W.crampedNMg | weights_1.W.crampedNEg | weights_1.W.crampedBMg | weights_1.W.crampedBEg | weights_1.W.crampedRMg | weights_1.W.crampedREg | weights_1.W.crampedQMg | weights_1.W.crampedQEg) !== 0;
    // eval5-A: mobility over squares not occupied by own pieces and not attacked by enemy pawns
    const mWl = act5 ? nWl & ~baL : nWl, mWh = act5 ? nWh & ~baH : nWh;
    const mBl = act5 ? nBl & ~waL : nBl, mBh = act5 ? nBh & ~waH : nBh;
    const wpl = wPawns.lo, wph = wPawns.hi, bpl = bPawns.lo, bph = bPawns.hi;
    let wAttackers = 0, bAttackers = 0;
    let wAttW = 0, bAttW = 0;
    const pb = board.pieceBB;
    // Knights + outposts
    for (let l = pb[2 /* Piece.WN */].lo, h = pb[2 /* Piece.WN */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const att = attacks_1.KNIGHT_ATTACKS[s];
        const al = att.lo, ah = att.hi;
        const mob = pop32(al & nWl) + pop32(ah & nWh);
        if (act5) {
            const sm = pop32(al & mWl) + pop32(ah & mWh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg += (sm - SM_BASE_N) * weights_1.W.safeMobNMg + cr * weights_1.W.crampedNMg;
            eg += (sm - SM_BASE_N) * weights_1.W.safeMobNEg + cr * weights_1.W.crampedNEg;
        }
        mg += mob * weights_1.W.mobNMg;
        eg += mob * weights_1.W.mobNEg;
        if (((al & bKZl) | (ah & bKZh)) !== 0) {
            wAttackers++;
            wAttW += 2;
        }
        const r = s >> 3, f = s & 7;
        if (r >= 3 && r <= 5) {
            // squares (r+1)*8+f±1 are in 32..55 -> hi half
            const b0 = (r + 1) * 8 + f - 32;
            const canBeAttacked = (f > 0 && ((bph >>> (b0 - 1)) & 1) !== 0) || (f < 7 && ((bph >>> (b0 + 1)) & 1) !== 0);
            if (!canBeAttacked) {
                const pa = attacks_1.WHITE_PAWN_ATTACKS[s];
                if (((pa.lo & wpl) | (pa.hi & wph)) !== 0) {
                    mg += weights_1.W.knightOutpostMg;
                    eg += weights_1.W.knightOutpostEg;
                }
            }
        }
    }
    for (let l = pb[8 /* Piece.BN */].lo, h = pb[8 /* Piece.BN */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const att = attacks_1.KNIGHT_ATTACKS[s];
        const al = att.lo, ah = att.hi;
        const mob = pop32(al & nBl) + pop32(ah & nBh);
        if (act5) {
            const sm = pop32(al & mBl) + pop32(ah & mBh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg -= (sm - SM_BASE_N) * weights_1.W.safeMobNMg + cr * weights_1.W.crampedNMg;
            eg -= (sm - SM_BASE_N) * weights_1.W.safeMobNEg + cr * weights_1.W.crampedNEg;
        }
        mg -= mob * weights_1.W.mobNMg;
        eg -= mob * weights_1.W.mobNEg;
        if (((al & wKZl) | (ah & wKZh)) !== 0) {
            bAttackers++;
            bAttW += 2;
        }
        const r = s >> 3, f = s & 7;
        if (r >= 2 && r <= 4) {
            // squares (r-1)*8+f±1 are in 8..31 -> lo half
            const b0 = (r - 1) * 8 + f;
            const canBeAttacked = (f > 0 && ((wpl >>> (b0 - 1)) & 1) !== 0) || (f < 7 && ((wpl >>> (b0 + 1)) & 1) !== 0);
            if (!canBeAttacked) {
                const pa = attacks_1.BLACK_PAWN_ATTACKS[s];
                if (((pa.lo & bpl) | (pa.hi & bph)) !== 0) {
                    mg -= weights_1.W.knightOutpostMg;
                    eg -= weights_1.W.knightOutpostEg;
                }
            }
        }
    }
    for (let l = pb[3 /* Piece.WB */].lo, h = pb[3 /* Piece.WB */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const _i = (0, magics_1.bishopIdx)(s, occ.lo, occ.hi);
        const al = magics_1.BISHOP_LO[_i], ah = magics_1.BISHOP_HI[_i];
        const mob = pop32(al & nWl) + pop32(ah & nWh);
        if (act5) {
            const sm = pop32(al & mWl) + pop32(ah & mWh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg += (sm - SM_BASE_B) * weights_1.W.safeMobBMg + cr * weights_1.W.crampedBMg;
            eg += (sm - SM_BASE_B) * weights_1.W.safeMobBEg + cr * weights_1.W.crampedBEg;
        }
        mg += mob * weights_1.W.mobBMg;
        eg += mob * weights_1.W.mobBEg;
        if (((al & bKZl) | (ah & bKZh)) !== 0) {
            wAttackers++;
            wAttW += 2;
        }
    }
    for (let l = pb[9 /* Piece.BB */].lo, h = pb[9 /* Piece.BB */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const _i = (0, magics_1.bishopIdx)(s, occ.lo, occ.hi);
        const al = magics_1.BISHOP_LO[_i], ah = magics_1.BISHOP_HI[_i];
        const mob = pop32(al & nBl) + pop32(ah & nBh);
        if (act5) {
            const sm = pop32(al & mBl) + pop32(ah & mBh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg -= (sm - SM_BASE_B) * weights_1.W.safeMobBMg + cr * weights_1.W.crampedBMg;
            eg -= (sm - SM_BASE_B) * weights_1.W.safeMobBEg + cr * weights_1.W.crampedBEg;
        }
        mg -= mob * weights_1.W.mobBMg;
        eg -= mob * weights_1.W.mobBEg;
        if (((al & wKZl) | (ah & wKZh)) !== 0) {
            bAttackers++;
            bAttW += 2;
        }
    }
    for (let l = pb[4 /* Piece.WR */].lo, h = pb[4 /* Piece.WR */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const _i = (0, magics_1.rookIdx)(s, occ.lo, occ.hi);
        const al = magics_1.ROOK_LO[_i], ah = magics_1.ROOK_HI[_i];
        const mob = pop32(al & nWl) + pop32(ah & nWh);
        if (act5) {
            const sm = pop32(al & mWl) + pop32(ah & mWh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg += (sm - SM_BASE_R) * weights_1.W.safeMobRMg + cr * weights_1.W.crampedRMg;
            eg += (sm - SM_BASE_R) * weights_1.W.safeMobREg + cr * weights_1.W.crampedREg;
        }
        mg += mob * weights_1.W.mobRMg;
        eg += mob * weights_1.W.mobREg;
        const f = s & 7;
        const fl = FM_LO[f], fh = FM_HI[f];
        const fpWe = ((wpl & fl) | (wph & fh)) === 0, fpBe = ((bpl & fl) | (bph & fh)) === 0;
        if (fpWe && fpBe) {
            mg += weights_1.W.rookOpenMg;
            eg += weights_1.W.rookOpenEg;
        }
        else if (fpWe) {
            mg += weights_1.W.rookSemiMg;
            eg += weights_1.W.rookSemiEg;
        }
        if ((s >> 3) === 6) {
            mg += weights_1.W.rook7thMg;
            eg += weights_1.W.rook7thEg;
        }
        if (((al & bKZl) | (ah & bKZh)) !== 0) {
            wAttackers++;
            wAttW += 3;
        }
    }
    for (let l = pb[10 /* Piece.BR */].lo, h = pb[10 /* Piece.BR */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const _i = (0, magics_1.rookIdx)(s, occ.lo, occ.hi);
        const al = magics_1.ROOK_LO[_i], ah = magics_1.ROOK_HI[_i];
        const mob = pop32(al & nBl) + pop32(ah & nBh);
        if (act5) {
            const sm = pop32(al & mBl) + pop32(ah & mBh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg -= (sm - SM_BASE_R) * weights_1.W.safeMobRMg + cr * weights_1.W.crampedRMg;
            eg -= (sm - SM_BASE_R) * weights_1.W.safeMobREg + cr * weights_1.W.crampedREg;
        }
        mg -= mob * weights_1.W.mobRMg;
        eg -= mob * weights_1.W.mobREg;
        const f = s & 7;
        const fl = FM_LO[f], fh = FM_HI[f];
        const fpWe = ((wpl & fl) | (wph & fh)) === 0, fpBe = ((bpl & fl) | (bph & fh)) === 0;
        if (fpWe && fpBe) {
            mg -= weights_1.W.rookOpenMg;
            eg -= weights_1.W.rookOpenEg;
        }
        else if (fpBe) {
            mg -= weights_1.W.rookSemiMg;
            eg -= weights_1.W.rookSemiEg;
        }
        if ((s >> 3) === 1) {
            mg -= weights_1.W.rook7thMg;
            eg -= weights_1.W.rook7thEg;
        }
        if (((al & wKZl) | (ah & wKZh)) !== 0) {
            bAttackers++;
            bAttW += 3;
        }
    }
    for (let l = pb[5 /* Piece.WQ */].lo, h = pb[5 /* Piece.WQ */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const _i = (0, magics_1.rookIdx)(s, occ.lo, occ.hi), _j = (0, magics_1.bishopIdx)(s, occ.lo, occ.hi);
        const al = (magics_1.ROOK_LO[_i] | magics_1.BISHOP_LO[_j]) >>> 0, ah = (magics_1.ROOK_HI[_i] | magics_1.BISHOP_HI[_j]) >>> 0;
        const mob = pop32(al & nWl) + pop32(ah & nWh);
        if (act5) {
            const sm = pop32(al & mWl) + pop32(ah & mWh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg += (sm - SM_BASE_Q) * weights_1.W.safeMobQMg + cr * weights_1.W.crampedQMg;
            eg += (sm - SM_BASE_Q) * weights_1.W.safeMobQEg + cr * weights_1.W.crampedQEg;
        }
        mg += mob * weights_1.W.mobQMg;
        eg += mob * weights_1.W.mobQEg;
        if (((al & bKZl) | (ah & bKZh)) !== 0) {
            wAttackers++;
            wAttW += 5;
        }
    }
    for (let l = pb[11 /* Piece.BQ */].lo, h = pb[11 /* Piece.BQ */].hi; (l | h) !== 0;) {
        let s;
        if (l !== 0) {
            const t = l & -l;
            s = 31 - Math.clz32(t);
            l ^= t;
        }
        else {
            const t = h & -h;
            s = 63 - Math.clz32(t);
            h ^= t;
        }
        const _i = (0, magics_1.rookIdx)(s, occ.lo, occ.hi), _j = (0, magics_1.bishopIdx)(s, occ.lo, occ.hi);
        const al = (magics_1.ROOK_LO[_i] | magics_1.BISHOP_LO[_j]) >>> 0, ah = (magics_1.ROOK_HI[_i] | magics_1.BISHOP_HI[_j]) >>> 0;
        const mob = pop32(al & nBl) + pop32(ah & nBh);
        if (act5) {
            const sm = pop32(al & mBl) + pop32(ah & mBh);
            const cr = sm < 3 ? 3 - sm : 0;
            mg -= (sm - SM_BASE_Q) * weights_1.W.safeMobQMg + cr * weights_1.W.crampedQMg;
            eg -= (sm - SM_BASE_Q) * weights_1.W.safeMobQEg + cr * weights_1.W.crampedQEg;
        }
        mg -= mob * weights_1.W.mobQMg;
        eg -= mob * weights_1.W.mobQEg;
        if (((al & wKZl) | (ah & wKZh)) !== 0) {
            bAttackers++;
            bAttW += 5;
        }
    }
    mg += kingShelter(wpl, wph, wKing, 0);
    mg -= kingShelter(bpl, bph, bKing, 64);
    if (wAttackers >= 2)
        mg += Math.min(wAttW * wAttackers * weights_1.W.attackUnit / 2, weights_1.W.attackCap);
    if (bAttackers >= 2)
        mg -= Math.min(bAttW * bAttackers * weights_1.W.attackUnit / 2, weights_1.W.attackCap);
    // Material imbalance: prefer minors when pawns many (simple)
    const imMg = weights_1.W.imbalanceMg, imEg = weights_1.W.imbalanceEg;
    if (imMg !== 0 || imEg !== 0) {
        const wn = pb[2 /* Piece.WN */], wb = pb[3 /* Piece.WB */], bn = pb[8 /* Piece.BN */], bb = pb[9 /* Piece.BB */];
        const wMin = pop32(wn.lo) + pop32(wn.hi) + pop32(wb.lo) + pop32(wb.hi);
        const bMin = pop32(bn.lo) + pop32(bn.hi) + pop32(bb.lo) + pop32(bb.hi);
        const wP = pop32(wpl) + pop32(wph), bP = pop32(bpl) + pop32(bph);
        if (wMin > bMin && wP >= bP) {
            mg += imMg;
            eg += imEg;
        }
        if (bMin > wMin && bP >= wP) {
            mg -= imMg;
            eg -= imEg;
        }
    }
    restMg = mg;
    restEg = eg;
}
/** dirOff: 0 = white (shelter on ranks above), 64 = black (ranks below) */
function kingShelter(pl, ph, ks, dirOff) {
    if (ks >= 64)
        return 0;
    const k = dirOff + ks;
    let score = (pop32(pl & SH_NEAR_LO[k]) + pop32(ph & SH_NEAR_HI[k])) * weights_1.W.shelterNear
        + (pop32(pl & SH_FAR_LO[k]) + pop32(ph & SH_FAR_HI[k])) * weights_1.W.shelterFar;
    const f = ks & 7;
    const open = weights_1.W.openFileNearKing;
    if (f > 0 && ((pl & FM_LO[f - 1]) | (ph & FM_HI[f - 1])) === 0)
        score -= open;
    if (((pl & FM_LO[f]) | (ph & FM_HI[f])) === 0)
        score -= open;
    if (f < 7 && ((pl & FM_LO[f + 1]) | (ph & FM_HI[f + 1])) === 0)
        score -= open;
    return score;
}
/** Qsearch eval: incremental + pawns + king shelter (no mobility) */
function evaluateQ(board) {
    let mg = board.mgScore;
    let eg = board.egScore;
    let phase = board.phase;
    if (phase > 24)
        phase = 24;
    if (phase < 0)
        phase = 0;
    if ((0, bitboard_1.popcount)(board.pieceBB[3 /* Piece.WB */]) >= 2) {
        mg += weights_1.W.bishopPairMg;
        eg += weights_1.W.bishopPairEg;
    }
    if ((0, bitboard_1.popcount)(board.pieceBB[9 /* Piece.BB */]) >= 2) {
        mg -= weights_1.W.bishopPairMg;
        eg -= weights_1.W.bishopPairEg;
    }
    const qwp = board.pieceBB[1 /* Piece.WP */], qbp = board.pieceBB[7 /* Piece.BP */];
    const qwl = qwp.lo, qwh = qwp.hi, qbl = qbp.lo, qbh = qbp.hi;
    const qpi = (0, pawnhash_1.probePawnIdx)(qwl, qwh, qbl, qbh);
    if (qpi < 0) {
        const pr = evalPawns(qwp, qbp);
        (0, pawnhash_1.storePawnIdx)(qpi, qwl, qwh, qbl, qbh, pr.mg, pr.eg, pr.wpa, pr.bpa);
        mg += pr.mg;
        eg += pr.eg;
    }
    else {
        mg += (0, pawnhash_1.pawnMg)(qpi);
        eg += (0, pawnhash_1.pawnEg)(qpi);
    }
    mg += kingShelter(qwl, qwh, board.whiteKingSq, 0);
    mg -= kingShelter(qbl, qbh, board.blackKingSq, 64);
    let score = ((mg * phase + eg * (24 - phase)) / 24) | 0;
    score += board.side === 0 /* Color.White */ ? weights_1.W.tempo : -weights_1.W.tempo;
    return board.side === 0 /* Color.White */ ? score : -score;
}
exports.evaluateFast = evaluateQ;
//# sourceMappingURL=evaluate.js.map
