/**
 * Dual-u32 bitboard — now the mainline representation in bitboard.ts.
 * Re-exports kept for staged experiment / older imports.
 */
export { BB as BB2, EMPTY as EMPTY2, bbFromBig, bbToBig, or as bb2Or, and as bb2And, xor as bb2Xor, not as bb2Not, isEmpty as bb2IsEmpty, popcount as bb2Popcount, lsb as bb2Lsb, popLsb as bb2PopLsb, bit as bb2Bit, setBit as bb2Set, clearBit as bb2Clear, testBit as bb2Test, north as bb2North, south as bb2South, } from './bitboard';

