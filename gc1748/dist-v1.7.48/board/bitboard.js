"use strict";
/** Dual-u32 bitboard utilities — {lo,hi} storage (bits 0..31 / 32..63) */
Object.defineProperty(exports, "__esModule", { value: true });
exports.NOT_GH_FILE = exports.NOT_AB_FILE = exports.NOT_H_FILE = exports.NOT_A_FILE = exports.RANK_MASKS = exports.FILE_MASKS = exports.BIT_TABLE = exports.UNIVERSE = exports.EMPTY = void 0;
exports.bb = bb;
exports.bit = bit;
exports.cloneBB = cloneBB;
exports.setBit = setBit;
exports.clearBit = clearBit;
exports.setBitMut = setBitMut;
exports.clearBitMut = clearBitMut;
exports.testBit = testBit;
exports.and = and;
exports.or = or;
exports.xor = xor;
exports.not = not;
exports.isEmpty = isEmpty;
exports.intersects = intersects;
exports.bbEq = bbEq;
exports.popcount = popcount;
exports.trailingZeros = trailingZeros;
exports.lsb = lsb;
exports.popLsb = popLsb;
exports.forEachBit = forEachBit;
exports.bitsToArray = bitsToArray;
exports.bbToBig = bbToBig;
exports.bbFromBig = bbFromBig;
exports.north = north;
exports.south = south;
exports.east = east;
exports.west = west;
exports.ne = ne;
exports.nw = nw;
exports.se = se;
exports.sw = sw;
exports.emptyBB = emptyBB;
exports.EMPTY = { lo: 0, hi: 0 };
exports.UNIVERSE = { lo: 0xffffffff, hi: 0xffffffff };
/** Precomputed square bits (immutable after init) */
exports.BIT_TABLE = new Array(64);
for (let i = 0; i < 64; i++) {
    exports.BIT_TABLE[i] = i < 32
        ? { lo: (1 << i) >>> 0, hi: 0 }
        : { lo: 0, hi: (1 << (i - 32)) >>> 0 };
}
function bb(lo, hi) {
    return { lo: lo >>> 0, hi: hi >>> 0 };
}
function bit(sq) {
    return exports.BIT_TABLE[sq];
}
function cloneBB(a) {
    return { lo: a.lo, hi: a.hi };
}
function setBit(bb, sq) {
    if (sq < 32)
        return { lo: (bb.lo | (1 << sq)) >>> 0, hi: bb.hi };
    return { lo: bb.lo, hi: (bb.hi | (1 << (sq - 32))) >>> 0 };
}
function clearBit(bb, sq) {
    if (sq < 32)
        return { lo: (bb.lo & ~(1 << sq)) >>> 0, hi: bb.hi };
    return { lo: bb.lo, hi: (bb.hi & ~(1 << (sq - 32))) >>> 0 };
}
/** In-place set (mutates bb). */
function setBitMut(bb, sq) {
    if (sq < 32)
        bb.lo = (bb.lo | (1 << sq)) >>> 0;
    else
        bb.hi = (bb.hi | (1 << (sq - 32))) >>> 0;
}
/** In-place clear (mutates bb). */
function clearBitMut(bb, sq) {
    if (sq < 32)
        bb.lo = (bb.lo & ~(1 << sq)) >>> 0;
    else
        bb.hi = (bb.hi & ~(1 << (sq - 32))) >>> 0;
}
function testBit(bb, sq) {
    if (sq < 32)
        return ((bb.lo >>> sq) & 1) !== 0;
    return ((bb.hi >>> (sq - 32)) & 1) !== 0;
}
function and(a, b) {
    return { lo: (a.lo & b.lo) >>> 0, hi: (a.hi & b.hi) >>> 0 };
}
function or(a, b) {
    return { lo: (a.lo | b.lo) >>> 0, hi: (a.hi | b.hi) >>> 0 };
}
function xor(a, b) {
    return { lo: (a.lo ^ b.lo) >>> 0, hi: (a.hi ^ b.hi) >>> 0 };
}
function not(a) {
    return { lo: (~a.lo) >>> 0, hi: (~a.hi) >>> 0 };
}
function isEmpty(a) {
    return a.lo === 0 && a.hi === 0;
}
/** True if a & b is nonempty. */
function intersects(a, b) {
    return ((a.lo & b.lo) !== 0) || ((a.hi & b.hi) !== 0);
}
function bbEq(a, b) {
    return a.lo === b.lo && a.hi === b.hi;
}
function pop32(v) {
    v = v - ((v >>> 1) & 0x55555555);
    v = (v & 0x33333333) + ((v >>> 2) & 0x33333333);
    return (((v + (v >>> 4)) & 0x0f0f0f0f) * 0x01010101) >>> 24;
}
function ctz32(v) {
    return 31 - Math.clz32(v & -v);
}
function popcount(bb) {
    return pop32(bb.lo) + pop32(bb.hi);
}
function trailingZeros(bb) {
    if (bb.lo)
        return ctz32(bb.lo >>> 0);
    if (bb.hi)
        return 32 + ctz32(bb.hi >>> 0);
    return 64;
}
function lsb(bb) {
    return trailingZeros(bb);
}
function popLsb(bb) {
    if (bb.lo) {
        const bit = bb.lo & -bb.lo;
        return { sq: ctz32(bit), bb: { lo: (bb.lo ^ bit) >>> 0, hi: bb.hi } };
    }
    if (bb.hi) {
        const bit = bb.hi & -bb.hi;
        return { sq: 32 + ctz32(bit), bb: { lo: 0, hi: (bb.hi ^ bit) >>> 0 } };
    }
    return { sq: 64, bb: { lo: 0, hi: 0 } };
}
function forEachBit(bb, fn) {
    let lo = bb.lo >>> 0;
    let hi = bb.hi >>> 0;
    while (lo) {
        const b = lo & -lo;
        fn(31 - Math.clz32(b));
        lo ^= b;
    }
    while (hi) {
        const b = hi & -hi;
        fn(32 + (31 - Math.clz32(b)));
        hi ^= b;
    }
}
function bitsToArray(bb) {
    const arr = [];
    forEachBit(bb, (s) => arr.push(s));
    return arr;
}
/** Convert dual-u32 ↔ bigint (pawn hash / debug). */
function bbToBig(b) {
    return BigInt(b.lo >>> 0) | (BigInt(b.hi >>> 0) << 32n);
}
function bbFromBig(v) {
    return {
        lo: Number(v & 0xffffffffn) >>> 0,
        hi: Number((v >> 32n) & 0xffffffffn) >>> 0,
    };
}
// File/rank masks
exports.FILE_MASKS = [];
exports.RANK_MASKS = [];
for (let f = 0; f < 8; f++) {
    let lo = 0, hi = 0;
    for (let r = 0; r < 8; r++) {
        const s = r * 8 + f;
        if (s < 32)
            lo |= (1 << s) >>> 0;
        else
            hi |= (1 << (s - 32)) >>> 0;
    }
    exports.FILE_MASKS[f] = { lo: lo >>> 0, hi: hi >>> 0 };
}
for (let r = 0; r < 8; r++) {
    let lo = 0, hi = 0;
    for (let f = 0; f < 8; f++) {
        const s = r * 8 + f;
        if (s < 32)
            lo |= (1 << s) >>> 0;
        else
            hi |= (1 << (s - 32)) >>> 0;
    }
    exports.RANK_MASKS[r] = { lo: lo >>> 0, hi: hi >>> 0 };
}
exports.NOT_A_FILE = not(exports.FILE_MASKS[0]);
exports.NOT_H_FILE = not(exports.FILE_MASKS[7]);
exports.NOT_AB_FILE = not(or(exports.FILE_MASKS[0], exports.FILE_MASKS[1]));
exports.NOT_GH_FILE = not(or(exports.FILE_MASKS[6], exports.FILE_MASKS[7]));
function north(a) {
    const lo = (a.lo << 8) >>> 0;
    const spill = a.lo >>> 24;
    const hi = ((a.hi << 8) | spill) >>> 0;
    return { lo, hi };
}
function south(a) {
    const hi = a.hi >>> 8;
    const spill = (a.hi & 0xff) << 24;
    const lo = ((a.lo >>> 8) | spill) >>> 0;
    return { lo, hi };
}
function east(a) {
    // << 1 then clear A-file
    const lo = (a.lo << 1) >>> 0;
    const spill = a.lo >>> 31;
    const hi = ((a.hi << 1) | spill) >>> 0;
    return and({ lo, hi }, exports.NOT_A_FILE);
}
function west(a) {
    const hi = a.hi >>> 1;
    const spill = (a.hi & 1) << 31;
    const lo = ((a.lo >>> 1) | spill) >>> 0;
    return and({ lo, hi }, exports.NOT_H_FILE);
}
function ne(a) { return east(north(a)); }
function nw(a) { return west(north(a)); }
function se(a) { return east(south(a)); }
function sw(a) { return west(south(a)); }
/** Empty BB factory (mutable). */
function emptyBB() {
    return { lo: 0, hi: 0 };
}
//# sourceMappingURL=bitboard.js.map
