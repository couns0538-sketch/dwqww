/** Time management v2 (UCI layer). Pure functions, no search.ts dependency.
 *  hard limit: enforced by a main-thread timer through the shared stop flag (precise, not 4096-node polling).
 *  soft limit: checked after each completed iteration (info callback); scaled by best-move stability and score drop. */
export interface TimeInput {
    /** remaining ms for the side to move; undefined if not given */
    time?: number;
    inc?: number;
    movestogo?: number;
    moveOverhead: number;
}
export interface TimeBudget {
    soft: number;
    hard: number;
}
/** Overhead per move: UCI option plus extra allowance at short time controls (process scheduling, pipe latency). */
export declare function effectiveOverhead(time: number, moveOverhead: number): number;
export declare function computeBudget(inp: TimeInput): TimeBudget;
/** Per-search dynamic soft-limit state. Feed it each completed iteration. */
export declare class SoftController {
    private budget;
    private prevMove;
    private stable;
    private prevScore;
    private dropBonus;
    constructor(budget: TimeBudget);
    /** returns true if the search should stop now (after this completed iteration). */
    onIteration(depth: number, score: number, bestUci: string, elapsed: number): boolean;
}

