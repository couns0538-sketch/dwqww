/** Magic bitboards — dual-u32 tables; index via u32 mul64 */
import { BB } from './bitboard';
export declare const ROOK_MASK: BB[];
export declare const BISHOP_MASK: BB[];
export declare const ROOK_MAGIC: BB[];
export declare const BISHOP_MAGIC: BB[];
export declare const ROOK_SHIFT: number[];
export declare const BISHOP_SHIFT: number[];
export declare const ROOK_ATTACKS: BB[][];
export declare const BISHOP_ATTACKS: BB[][];
export declare function initMagics(): void;
export declare function rookAttacksMagic(sq: number, occ: BB): BB;
export declare function bishopAttacksMagic(sq: number, occ: BB): BB;
export declare function queenAttacksMagic(sq: number, occ: BB): BB;

