"use strict";
/** Zobrist hashing */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ZS_LO = exports.ZS_HI = exports.ZE_LO = exports.ZE_HI = exports.ZC_LO = exports.ZC_HI = exports.ZP_LO = exports.ZP_HI = exports.ZOBRIST_EP = exports.ZOBRIST_CASTLING = exports.ZOBRIST_SIDE = exports.ZOBRIST_PIECE = void 0;
exports.hashPiece = hashPiece;
exports.hashSide = hashSide;
exports.hashCastling = hashCastling;
exports.hashEp = hashEp;
exports.epIdx = epIdx;
exports.joinKey = joinKey;
const types_1 = require("./types");
// Deterministic PRNG (xorshift64*) for reproducible keys
function makeRng(seed) {
    let s = seed;
    return () => {
        s ^= s >> 12n;
        s ^= s << 25n;
        s ^= s >> 27n;
        s = (s * 0x2545f4914f6cdd1dn) & 0xffffffffffffffffn;
        return s;
    };
}
const rng = makeRng(0x123456789abcdefn);
exports.ZOBRIST_PIECE = [];
for (let p = 0; p <= 12; p++) {
    exports.ZOBRIST_PIECE[p] = [];
    for (let sq = 0; sq < 64; sq++) {
        exports.ZOBRIST_PIECE[p][sq] = rng();
    }
}
exports.ZOBRIST_SIDE = rng();
exports.ZOBRIST_CASTLING = [];
for (let i = 0; i < 16; i++)
    exports.ZOBRIST_CASTLING[i] = rng();
exports.ZOBRIST_EP = [];
for (let i = 0; i < 8; i++)
    exports.ZOBRIST_EP[i] = rng();
function hashPiece(piece, sq) {
    return exports.ZOBRIST_PIECE[piece][sq];
}
function hashSide() {
    return exports.ZOBRIST_SIDE;
}
function hashCastling(rights) {
    return exports.ZOBRIST_CASTLING[rights & 15];
}
function hashEp(epSquare) {
    if (epSquare === types_1.SQ_NONE)
        return 0n;
    return exports.ZOBRIST_EP[epSquare & 7];
}
// 4.1: u32 halves of every key (same 64-bit values), for BigInt-free incremental hashing.
function splitHi(a) { const r = new Int32Array(a.length); for (let i = 0; i < a.length; i++)
    r[i] = Number((a[i] >> 32n) & 0xffffffffn) | 0; return r; }
function splitLo(a) { const r = new Int32Array(a.length); for (let i = 0; i < a.length; i++)
    r[i] = Number(a[i] & 0xffffffffn) | 0; return r; }
const flatPiece = [];
for (let p = 0; p <= 12; p++)
    for (let sq = 0; sq < 64; sq++)
        flatPiece.push(exports.ZOBRIST_PIECE[p][sq]);
/** index = piece*64 + sq */
exports.ZP_HI = splitHi(flatPiece), exports.ZP_LO = splitLo(flatPiece);
exports.ZC_HI = splitHi(exports.ZOBRIST_CASTLING), exports.ZC_LO = splitLo(exports.ZOBRIST_CASTLING);
const epArr = [...exports.ZOBRIST_EP, 0n]; // index 8 = no ep
exports.ZE_HI = splitHi(epArr), exports.ZE_LO = splitLo(epArr);
exports.ZS_HI = Number((exports.ZOBRIST_SIDE >> 32n) & 0xffffffffn) | 0, exports.ZS_LO = Number(exports.ZOBRIST_SIDE & 0xffffffffn) | 0;
function epIdx(epSquare) { return epSquare === types_1.SQ_NONE ? 8 : (epSquare & 7); }
function joinKey(hi, lo) { return (BigInt(hi >>> 0) << 32n) | BigInt(lo >>> 0); }
//# sourceMappingURL=zobrist.js.map
