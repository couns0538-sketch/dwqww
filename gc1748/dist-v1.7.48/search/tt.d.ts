/** Transposition table — packed entries; optional SharedArrayBuffer for Lazy SMP */
import { Move } from '../board/types';
export declare const enum TTFlag {
    Exact = 0,
    Lower = 1,
    Upper = 2
}
export interface TTEntry {
    hi: number;
    lo: number;
    depth: number;
    score: number;
    flag: TTFlag;
    bestMove: Move | null;
    age: number;
}
/** Default 4M entries; shared SMP uses same. */
export declare const TT_SIZE: number;
export interface SharedTTBundle {
    size: number;
    keysHiSab: SharedArrayBuffer;
    keysLoSab: SharedArrayBuffer;
    depthsSab: SharedArrayBuffer;
    scoresSab: SharedArrayBuffer;
    flagsSab: SharedArrayBuffer;
    agesSab: SharedArrayBuffer;
    movesSab: SharedArrayBuffer;
    metaSab: SharedArrayBuffer;
}
export declare function createSharedTTBundle(size?: number): SharedTTBundle;
/** Pack from/to/promo; 0 = null. sameMove only needs these fields. */
export declare function packMove(m: Move | null): number;
export declare function unpackMove(code: number): Move | null;
export declare class TranspositionTable {
    keysHi: Int32Array;
    keysLo: Int32Array;
    depths: Int8Array;
    scores: Int16Array;
    flags: Uint8Array;
    ages: Uint8Array;
    /** Packed moves (shared-safe). Local mode also uses this for one representation. */
    moveCodes: Uint32Array;
    /** Optional object cache for local TT only (unused when shared). */
    moves: (Move | null)[] | null;
    age: number;
    size: number;
    sharedMeta: Int32Array | null;
    isShared: boolean;
    constructor(size?: number, bundle?: SharedTTBundle);
    clear(): void;
    index(lo: number): number;
    probe(hi: number, lo: number): TTEntry | null;
    store(hi: number, lo: number, depth: number, score: number, flag: TTFlag, bestMove: Move | null): void;
    prefetchAge(): void;
}
export declare const MATE_SCORE = 30000;
export declare const MATE_BOUND = 29000;
export declare function scoreToTT(score: number, ply: number): number;
export declare function scoreFromTT(score: number, ply: number): number;

