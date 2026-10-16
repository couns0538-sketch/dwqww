/** Incremental material + PST scoring */
import { Piece } from '../board/types';
/** White-relative delta when placing piece on square s */
export declare function scorePut(piece: Piece, s: number): {
    mg: number;
    eg: number;
    phase: number;
};
export declare function scoreRemove(piece: Piece, s: number): {
    mg: number;
    eg: number;
    phase: number;
};
export declare const putMg: (p: number, s: number) => number;
export declare const putEg: (p: number, s: number) => number;
export declare const putPhase: (p: number) => number;

