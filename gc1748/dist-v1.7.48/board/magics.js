"use strict";
/** Magic bitboards — dual-u32 tables; index via u32 mul64 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.BISHOP_OFF = exports.ROOK_OFF = exports.BISHOP_HI = exports.BISHOP_LO = exports.ROOK_HI = exports.ROOK_LO = exports.BISHOP_ATTACKS = exports.ROOK_ATTACKS = exports.BISHOP_SHIFT = exports.ROOK_SHIFT = exports.BISHOP_MAGIC = exports.ROOK_MAGIC = exports.BISHOP_MASK = exports.ROOK_MASK = void 0;
exports.initMagics = initMagics;
exports.rookIdx = rookIdx;
exports.bishopIdx = bishopIdx;
exports.rookAttacksMagic = rookAttacksMagic;
exports.bishopAttacksMagic = bishopAttacksMagic;
exports.queenAttacksMagic = queenAttacksMagic;
const bitboard_1 = require("./bitboard");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
exports.ROOK_MASK = new Array(64);
exports.BISHOP_MASK = new Array(64);
exports.ROOK_MAGIC = new Array(64);
exports.BISHOP_MAGIC = new Array(64);
exports.ROOK_SHIFT = new Array(64).fill(0);
exports.BISHOP_SHIFT = new Array(64).fill(0);
exports.ROOK_ATTACKS = new Array(64);
exports.BISHOP_ATTACKS = new Array(64);
/** Flat tables: entry i of square sq lives at ROOK_OFF[sq] + i. */
exports.ROOK_LO = new Uint32Array(0);
exports.ROOK_HI = new Uint32Array(0);
exports.BISHOP_LO = new Uint32Array(0);
exports.BISHOP_HI = new Uint32Array(0);
exports.ROOK_OFF = new Int32Array(64);
exports.BISHOP_OFF = new Int32Array(64);
const RM_LO = new Uint32Array(64), RM_HI = new Uint32Array(64), RG_LO = new Uint32Array(64), RG_HI = new Uint32Array(64);
const BM_LO = new Uint32Array(64), BM_HI = new Uint32Array(64), BG_LO = new Uint32Array(64), BG_HI = new Uint32Array(64);
const R_SH = new Int32Array(64), B_SH = new Int32Array(64);
let ready = false;
function initMagics() {
    if (ready)
        return;
    const candidates = [
        path.join(__dirname, 'magic_data.json'),
        path.join(__dirname, '..', '..', 'src', 'board', 'magic_data.json'),
        path.join(process.cwd(), 'src', 'board', 'magic_data.json'),
        path.join(process.cwd(), 'dist', 'board', 'magic_data.json'),
    ];
    let raw = null;
    for (const c of candidates) {
        try {
            raw = fs.readFileSync(c, 'utf8');
            break;
        }
        catch { /* continue */ }
    }
    if (!raw)
        throw new Error('magic_data.json not found');
    const data = JSON.parse(raw);
    for (const e of data.rook) {
        exports.ROOK_MASK[e.sq] = (0, bitboard_1.bbFromBig)(BigInt(e.mask));
        exports.ROOK_MAGIC[e.sq] = (0, bitboard_1.bbFromBig)(BigInt(e.magic));
        exports.ROOK_SHIFT[e.sq] = 64 - e.bits;
        exports.ROOK_ATTACKS[e.sq] = e.attacks.map((a) => (0, bitboard_1.bbFromBig)(BigInt(a)));
    }
    for (const e of data.bishop) {
        exports.BISHOP_MASK[e.sq] = (0, bitboard_1.bbFromBig)(BigInt(e.mask));
        exports.BISHOP_MAGIC[e.sq] = (0, bitboard_1.bbFromBig)(BigInt(e.magic));
        exports.BISHOP_SHIFT[e.sq] = 64 - e.bits;
        exports.BISHOP_ATTACKS[e.sq] = e.attacks.map((a) => (0, bitboard_1.bbFromBig)(BigInt(a)));
    }
    let rn = 0, bn = 0;
    for (let q = 0; q < 64; q++) {
        exports.ROOK_OFF[q] = rn;
        rn += exports.ROOK_ATTACKS[q].length;
        exports.BISHOP_OFF[q] = bn;
        bn += exports.BISHOP_ATTACKS[q].length;
    }
    exports.ROOK_LO = new Uint32Array(rn);
    exports.ROOK_HI = new Uint32Array(rn);
    exports.BISHOP_LO = new Uint32Array(bn);
    exports.BISHOP_HI = new Uint32Array(bn);
    for (let q = 0; q < 64; q++) {
        const ra = exports.ROOK_ATTACKS[q], ba = exports.BISHOP_ATTACKS[q];
        for (let i = 0; i < ra.length; i++) {
            exports.ROOK_LO[exports.ROOK_OFF[q] + i] = ra[i].lo;
            exports.ROOK_HI[exports.ROOK_OFF[q] + i] = ra[i].hi;
        }
        for (let i = 0; i < ba.length; i++) {
            exports.BISHOP_LO[exports.BISHOP_OFF[q] + i] = ba[i].lo;
            exports.BISHOP_HI[exports.BISHOP_OFF[q] + i] = ba[i].hi;
        }
        RM_LO[q] = exports.ROOK_MASK[q].lo;
        RM_HI[q] = exports.ROOK_MASK[q].hi;
        RG_LO[q] = exports.ROOK_MAGIC[q].lo;
        RG_HI[q] = exports.ROOK_MAGIC[q].hi;
        R_SH[q] = exports.ROOK_SHIFT[q];
        BM_LO[q] = exports.BISHOP_MASK[q].lo;
        BM_HI[q] = exports.BISHOP_MASK[q].hi;
        BG_LO[q] = exports.BISHOP_MAGIC[q].lo;
        BG_HI[q] = exports.BISHOP_MAGIC[q].hi;
        B_SH[q] = exports.BISHOP_SHIFT[q];
    }
    ready = true;
}
/** Magic index on scalars (same arithmetic as magicIndex). */
function magicIdx(lo, hi, mLo, mHi, shift) {
    const ah = lo >>> 16, al = lo & 0xffff;
    const bh = mLo >>> 16, bl = mLo & 0xffff;
    const p0 = al * bl;
    const p1 = ah * bl;
    const p2 = al * bh;
    const p3 = ah * bh;
    const mid = (p0 >>> 16) + (p1 & 0xffff) + (p2 & 0xffff);
    const pLo = ((p0 & 0xffff) | ((mid & 0xffff) << 16)) >>> 0;
    const lh = (p3 + (p1 >>> 16) + (p2 >>> 16) + (mid >>> 16)) >>> 0;
    const pHi = (lh + ((Math.imul(lo, mHi) + Math.imul(hi, mLo)) >>> 0)) >>> 0;
    if (shift >= 32)
        return pHi >>> (shift - 32);
    if (shift === 0)
        return pLo;
    return ((pLo >>> shift) | (pHi << (32 - shift))) >>> 0;
}
/** Flat index into ROOK_LO/ROOK_HI for sq with occupancy (oLo,oHi). Allocation-free. */
function rookIdx(sq, oLo, oHi) {
    return exports.ROOK_OFF[sq] + magicIdx((oLo & RM_LO[sq]) >>> 0, (oHi & RM_HI[sq]) >>> 0, RG_LO[sq], RG_HI[sq], R_SH[sq]);
}
/** Flat index into BISHOP_LO/BISHOP_HI. Allocation-free. */
function bishopIdx(sq, oLo, oHi) {
    return exports.BISHOP_OFF[sq] + magicIdx((oLo & BM_LO[sq]) >>> 0, (oHi & BM_HI[sq]) >>> 0, BG_LO[sq], BG_HI[sq], B_SH[sq]);
}
/** 32×32 → 64 unsigned multiply. */
function umul32(a, b) {
    a >>>= 0;
    b >>>= 0;
    const ah = a >>> 16, al = a & 0xffff;
    const bh = b >>> 16, bl = b & 0xffff;
    const p0 = al * bl;
    const p1 = ah * bl;
    const p2 = al * bh;
    const p3 = ah * bh;
    const mid = (p0 >>> 16) + (p1 & 0xffff) + (p2 & 0xffff);
    const lo = ((p0 & 0xffff) | ((mid & 0xffff) << 16)) >>> 0;
    const hi = (p3 + (p1 >>> 16) + (p2 >>> 16) + (mid >>> 16)) >>> 0;
    return [lo, hi];
}
/** Low 64 bits of 64×64 unsigned multiply (no BigInt). */
function mul64lo(aLo, aHi, bLo, bHi) {
    const [ll, lh] = umul32(aLo, bLo);
    const cross = (Math.imul(aLo >>> 0, bHi >>> 0) + Math.imul(aHi >>> 0, bLo >>> 0)) >>> 0;
    return [ll, (lh + cross) >>> 0];
}
/** Magic index via dual-u32 multiply + shift (allocation-free: no tuple returns). */
function magicIndex(occ, mask, magic, shift) {
    const lo = (occ.lo & mask.lo) >>> 0;
    const hi = (occ.hi & mask.hi) >>> 0;
    const mLo = magic.lo >>> 0;
    // umul32(lo, mLo) inline
    const ah = lo >>> 16, al = lo & 0xffff;
    const bh = mLo >>> 16, bl = mLo & 0xffff;
    const p0 = al * bl;
    const p1 = ah * bl;
    const p2 = al * bh;
    const p3 = ah * bh;
    const mid = (p0 >>> 16) + (p1 & 0xffff) + (p2 & 0xffff);
    const pLo = ((p0 & 0xffff) | ((mid & 0xffff) << 16)) >>> 0;
    const lh = (p3 + (p1 >>> 16) + (p2 >>> 16) + (mid >>> 16)) >>> 0;
    // cross terms = high word of mul64lo (same as Math.imul(aLo, bHi) + Math.imul(aHi, bLo))
    const pHi = (lh + ((Math.imul(lo, magic.hi >>> 0) + Math.imul(hi, mLo)) >>> 0)) >>> 0;
    if (shift >= 32)
        return pHi >>> (shift - 32);
    if (shift === 0)
        return pLo;
    return ((pLo >>> shift) | (pHi << (32 - shift))) >>> 0;
}
function rookAttacksMagic(sq, occ) {
    const idx = magicIndex(occ, exports.ROOK_MASK[sq], exports.ROOK_MAGIC[sq], exports.ROOK_SHIFT[sq]);
    return exports.ROOK_ATTACKS[sq][idx];
}
function bishopAttacksMagic(sq, occ) {
    const idx = magicIndex(occ, exports.BISHOP_MASK[sq], exports.BISHOP_MAGIC[sq], exports.BISHOP_SHIFT[sq]);
    return exports.BISHOP_ATTACKS[sq][idx];
}
function queenAttacksMagic(sq, occ) {
    return (0, bitboard_1.or)(rookAttacksMagic(sq, occ), bishopAttacksMagic(sq, occ));
}
// Eager init
initMagics();
//# sourceMappingURL=magics.js.map
