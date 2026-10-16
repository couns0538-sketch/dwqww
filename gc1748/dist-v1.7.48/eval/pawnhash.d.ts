/** Pawn structure hash cache (exact-compare, u32 keys, no BigInt, no allocation on probe).
 *  Also caches the pawn attack sets used by eval5 safe-square mobility. */
import { BB } from '../board/bitboard';
/** pawn attack sets (white / black), lo/hi words */
export declare const aWL: Int32Array<ArrayBuffer>, aWH: Int32Array<ArrayBuffer>, aBL: Int32Array<ArrayBuffer>, aBH: Int32Array<ArrayBuffer>;
export interface PawnData {
    mg: number;
    eg: number;
    wpa: BB;
    bpa: BB;
}
/** returns slot index if cached else -(slot+1) */
export declare function probePawnIdx(wl: number, wh: number, bl: number, bh: number): number;
export declare function storePawnIdx(neg: number, wl: number, wh: number, bl: number, bh: number, mg: number, eg: number, wpa: BB, bpa: BB): void;
export declare function pawnMg(i: number): number;
export declare function pawnEg(i: number): number;
export declare function clearPawnCache(): void;

