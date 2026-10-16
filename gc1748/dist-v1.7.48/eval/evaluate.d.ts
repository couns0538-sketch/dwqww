/** Static evaluation — incremental material/PST + pawns/mobility/king/space */
import { Board } from '../board/board';
/** Clear eval + pawn caches (needed when weights change at runtime, e.g. tuning/tests) */
export declare function clearEvalCaches(): void;
export declare function evaluate(board: Board): number;
/** Qsearch eval: incremental + pawns + king shelter (no mobility) */
export declare function evaluateQ(board: Board): number;
export declare const evaluateFast: typeof evaluateQ;

