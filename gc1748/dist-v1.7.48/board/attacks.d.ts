/** Attack tables — leaper tables + magic bitboard sliders (dual-u32) */
import { BB } from './bitboard';
import { Square } from './types';
export declare const KNIGHT_ATTACKS: BB[];
export declare const KING_ATTACKS: BB[];
export declare const WHITE_PAWN_ATTACKS: BB[];
export declare const BLACK_PAWN_ATTACKS: BB[];
declare function msb(bb: BB): number;
export declare function bishopAttacks(s: Square, occ: BB): BB;
export declare function rookAttacks(s: Square, occ: BB): BB;
export declare function queenAttacks(s: Square, occ: BB): BB;
export { msb };

