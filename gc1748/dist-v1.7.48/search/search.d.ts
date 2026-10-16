/** Alpha-beta search: PVS, QSearch, NMP, LMR, SEE, futility, razoring, killers, history, aspiration */
import { Board } from '../board/board';
import { Move } from '../board/types';
import { TranspositionTable } from './tt';
export declare const gcDebugStats: {
    checked: number;
    mismatches: number;
};
export interface SearchInfo {
    depth: number;
    nodes: number;
    score: number;
    timeMs: number;
    pv: string[];
    nps: number;
}
export interface SearchLimits {
    maxDepth?: number;
    moveTime?: number;
    wtime?: number;
    btime?: number;
    winc?: number;
    binc?: number;
    infinite?: boolean;
    /** ttkeep: epoch ms of the UCI `go`; search clock starts here instead of at search() entry */
    startTime?: number;
}
export declare class Search {
    board: Board;
    tt: TranspositionTable;
    nodes: number;
    stop: boolean;
    startTime: number;
    timeLimit: number;
    killers: (Move | null)[][];
    history: number[][];
    countermove: (Move | null)[];
    followMove: (Move | null)[];
    contHistory: Int16Array;
    followUpHistory: Int16Array;
    /** [piece][captured][to] — ProbCut capture ordering only */
    capHistory: Int16Array;
    /** Set during the shallow ProbCut verification search so it cannot nest. */
    inProbCut: boolean;
    prevMove: Move | null;
    /** Move from 2 plies ago (same-side previous); keys FUH */
    prev2Move: Move | null;
    pvTable: Move[][];
    pvLength: number[];
    staticAtPly: number[];
    staticKnown: boolean[];
    followPV: boolean;
    onInfo?: (info: SearchInfo) => void;
    moveStack: Move[][];
    scoreStack: number[][];
    /** SharedArrayBuffer-backed stop flag (Atomics); Lazy SMP cooperative abort */
    stopFlag: Int32Array | null;
    /** 0 = main thread; helpers diversify search */
    threadId: number;
    /** Skip root IID (helpers explore different trees) */
    skipRootIid: boolean;
    /** Aspiration half-width; helpers use different values */
    aspirationWindow: number;
    /** Seed for history-table noise (0 = none) */
    historyNoiseSeed: number;
    /** At root, rotate ordered quiet moves by this count (helpers) */
    rootQuietRotate: number;
    /** Helpers: on shallow root depths, push TT/PV move later to explore alts */
    rootDeferPv: boolean;
    constructor(board: Board);
    resetHeuristics(): void;
    shouldStop(): boolean;
    /** Root IID: skip if already spent much of a short movetime (IID ate SF samples). */
    allowIidRoot(): boolean;
    /** Tree/PV IID only when clock has room. */
    allowIidTree(): boolean;
    computeTimeLimit(limits: SearchLimits): number;
    search(limits: SearchLimits): Move | null;
    getPvMove(ply: number): Move | null;
    negamax(ply: number, depth: number, alpha: number, beta: number): number;
    quiescence(ply: number, alpha: number, beta: number): number;
    orderMoves(moves: Move[], ply: number, ttMove: Move | null, depth: number): Move[];
    orderCaptures(moves: Move[], ply?: number): Move[];
    /** Sprinkle low-amplitude history so helpers order quiet moves differently. */
    seedHistoryNoise(seed: number): void;
    /**
     * Rotate non-capture/non-promo moves after the first few forced slots so
     * helpers try different root candidates early (Lazy SMP diversification).
     */
    rotateRootQuiets(moves: Move[], rot: number): Move[];
    sameMove(a: Move | null, b: Move | null): boolean;
    isRepetition(): boolean;
}

