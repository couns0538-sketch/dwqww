/** Dual-u32 bitboard utilities — {lo,hi} storage (bits 0..31 / 32..63) */
export interface BB {
    lo: number;
    hi: number;
}
export declare const EMPTY: BB;
export declare const UNIVERSE: BB;
/** Precomputed square bits (immutable after init) */
export declare const BIT_TABLE: BB[];
export declare function bb(lo: number, hi: number): BB;
export declare function bit(sq: number): BB;
export declare function cloneBB(a: BB): BB;
export declare function setBit(bb: BB, sq: number): BB;
export declare function clearBit(bb: BB, sq: number): BB;
/** In-place set (mutates bb). */
export declare function setBitMut(bb: BB, sq: number): void;
/** In-place clear (mutates bb). */
export declare function clearBitMut(bb: BB, sq: number): void;
export declare function testBit(bb: BB, sq: number): boolean;
export declare function and(a: BB, b: BB): BB;
export declare function or(a: BB, b: BB): BB;
export declare function xor(a: BB, b: BB): BB;
export declare function not(a: BB): BB;
export declare function isEmpty(a: BB): boolean;
/** True if a & b is nonempty. */
export declare function intersects(a: BB, b: BB): boolean;
export declare function bbEq(a: BB, b: BB): boolean;
export declare function popcount(bb: BB): number;
export declare function trailingZeros(bb: BB): number;
export declare function lsb(bb: BB): number;
export declare function popLsb(bb: BB): {
    sq: number;
    bb: BB;
};
export declare function forEachBit(bb: BB, fn: (sq: number) => void): void;
export declare function bitsToArray(bb: BB): number[];
/** Convert dual-u32 ↔ bigint (pawn hash / debug). */
export declare function bbToBig(b: BB): bigint;
export declare function bbFromBig(v: bigint): BB;
export declare const FILE_MASKS: BB[];
export declare const RANK_MASKS: BB[];
export declare const NOT_A_FILE: BB;
export declare const NOT_H_FILE: BB;
export declare const NOT_AB_FILE: BB;
export declare const NOT_GH_FILE: BB;
export declare function north(a: BB): BB;
export declare function south(a: BB): BB;
export declare function east(a: BB): BB;
export declare function west(a: BB): BB;
export declare function ne(a: BB): BB;
export declare function nw(a: BB): BB;
export declare function se(a: BB): BB;
export declare function sw(a: BB): BB;
/** Empty BB factory (mutable). */
export declare function emptyBB(): BB;

