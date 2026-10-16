"use strict";
/** Attack tables — leaper tables + magic bitboard sliders (dual-u32) */
Object.defineProperty(exports, "__esModule", { value: true });
exports.BLACK_PAWN_ATTACKS = exports.WHITE_PAWN_ATTACKS = exports.KING_ATTACKS = exports.KNIGHT_ATTACKS = void 0;
exports.bishopAttacks = bishopAttacks;
exports.rookAttacks = rookAttacks;
exports.queenAttacks = queenAttacks;
exports.msb = msb;
const bitboard_1 = require("./bitboard");
const magics_1 = require("./magics");
exports.KNIGHT_ATTACKS = new Array(64);
exports.KING_ATTACKS = new Array(64);
exports.WHITE_PAWN_ATTACKS = new Array(64);
exports.BLACK_PAWN_ATTACKS = new Array(64);
function msb(bb) {
    if (bb.hi) {
        let x = bb.hi >>> 0;
        let n = 32;
        if (x >= 0x10000) {
            n += 16;
            x >>>= 16;
        }
        if (x >= 0x100) {
            n += 8;
            x >>>= 8;
        }
        if (x >= 0x10) {
            n += 4;
            x >>>= 4;
        }
        if (x >= 0x4) {
            n += 2;
            x >>>= 2;
        }
        if (x >= 0x2) {
            n += 1;
        }
        return n;
    }
    if (bb.lo) {
        let x = bb.lo >>> 0;
        let n = 0;
        if (x >= 0x10000) {
            n += 16;
            x >>>= 16;
        }
        if (x >= 0x100) {
            n += 8;
            x >>>= 8;
        }
        if (x >= 0x10) {
            n += 4;
            x >>>= 4;
        }
        if (x >= 0x4) {
            n += 2;
            x >>>= 2;
        }
        if (x >= 0x2) {
            n += 1;
        }
        return n;
    }
    return -1;
}
function initAttacks() {
    for (let s = 0; s < 64; s++) {
        const b = (0, bitboard_1.bit)(s);
        // Knight: deltas ±17,±15,±10,±6 with file masks
        // Rebuild via square arithmetic for correctness (init-only)
        let kn = (0, bitboard_1.emptyBB)();
        const deltas = [
            [1, 2], [-1, 2], [2, 1], [-2, 1],
            [1, -2], [-1, -2], [2, -1], [-2, -1],
        ];
        const f0 = s & 7, r0 = s >> 3;
        for (const [df, dr] of deltas) {
            const f = f0 + df, r = r0 + dr;
            if (f >= 0 && f < 8 && r >= 0 && r < 8) {
                const t = r * 8 + f;
                if (t < 32)
                    kn.lo = (kn.lo | (1 << t)) >>> 0;
                else
                    kn.hi = (kn.hi | (1 << (t - 32))) >>> 0;
            }
        }
        exports.KNIGHT_ATTACKS[s] = kn;
        exports.KING_ATTACKS[s] = (0, bitboard_1.or)((0, bitboard_1.or)((0, bitboard_1.or)((0, bitboard_1.or)((0, bitboard_1.or)((0, bitboard_1.or)((0, bitboard_1.or)((0, bitboard_1.north)(b), (0, bitboard_1.south)(b)), (0, bitboard_1.east)(b)), (0, bitboard_1.west)(b)), (0, bitboard_1.ne)(b)), (0, bitboard_1.nw)(b)), (0, bitboard_1.se)(b)), (0, bitboard_1.sw)(b));
        exports.WHITE_PAWN_ATTACKS[s] = (0, bitboard_1.or)((0, bitboard_1.ne)(b), (0, bitboard_1.nw)(b));
        exports.BLACK_PAWN_ATTACKS[s] = (0, bitboard_1.or)((0, bitboard_1.se)(b), (0, bitboard_1.sw)(b));
    }
}
initAttacks();
(0, magics_1.initMagics)();
function bishopAttacks(s, occ) {
    return (0, magics_1.bishopAttacksMagic)(s, occ);
}
function rookAttacks(s, occ) {
    return (0, magics_1.rookAttacksMagic)(s, occ);
}
function queenAttacks(s, occ) {
    return (0, magics_1.queenAttacksMagic)(s, occ);
}
//# sourceMappingURL=attacks.js.map
