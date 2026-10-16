"use strict";
/** Pawn structure hash cache (exact-compare, u32 keys, no BigInt, no allocation on probe).
 *  Also caches the pawn attack sets used by eval5 safe-square mobility. */
Object.defineProperty(exports, "__esModule", { value: true });
exports.aBH = exports.aBL = exports.aWH = exports.aWL = void 0;
exports.probePawnIdx = probePawnIdx;
exports.storePawnIdx = storePawnIdx;
exports.pawnMg = pawnMg;
exports.pawnEg = pawnEg;
exports.clearPawnCache = clearPawnCache;
const SIZE = 1 << 16;
const MASK = SIZE - 1;
const wLo = new Int32Array(SIZE), wHi = new Int32Array(SIZE), bLo = new Int32Array(SIZE), bHi = new Int32Array(SIZE);
const used = new Uint8Array(SIZE);
const mgArr = new Int32Array(SIZE);
const egArr = new Int32Array(SIZE);
/** pawn attack sets (white / black), lo/hi words */
exports.aWL = new Int32Array(SIZE), exports.aWH = new Int32Array(SIZE), exports.aBL = new Int32Array(SIZE), exports.aBH = new Int32Array(SIZE);
function slot(wl, wh, bl, bh) {
    let h = Math.imul(wl ^ Math.imul(wh, 0x85ebca6b), 0x9e3779b1);
    h = Math.imul(h ^ (h >>> 15) ^ bl, 0xc2b2ae35);
    h = Math.imul(h ^ (h >>> 13) ^ Math.imul(bh, 0x27d4eb2f), 0x165667b1);
    return (h ^ (h >>> 16)) & MASK;
}
/** returns slot index if cached else -(slot+1) */
function probePawnIdx(wl, wh, bl, bh) {
    const i = slot(wl, wh, bl, bh);
    if (used[i] === 1 && wLo[i] === (wl | 0) && wHi[i] === (wh | 0) && bLo[i] === (bl | 0) && bHi[i] === (bh | 0))
        return i;
    return -i - 1;
}
function storePawnIdx(neg, wl, wh, bl, bh, mg, eg, wpa, bpa) {
    const i = -neg - 1;
    used[i] = 1;
    wLo[i] = wl;
    wHi[i] = wh;
    bLo[i] = bl;
    bHi[i] = bh;
    mgArr[i] = mg;
    egArr[i] = eg;
    exports.aWL[i] = wpa.lo;
    exports.aWH[i] = wpa.hi;
    exports.aBL[i] = bpa.lo;
    exports.aBH[i] = bpa.hi;
}
function pawnMg(i) { return mgArr[i]; }
function pawnEg(i) { return egArr[i]; }
function clearPawnCache() { used.fill(0); }
//# sourceMappingURL=pawnhash.js.map
