/** prune2fast: pre-make gives-check test for quiet, non-castle, non-promo moves (LMP only). */
import { Board } from '../board/board';
import { Move } from '../board/types';
/** Exact "does m give check" for a legal quiet non-castle non-promo move. Callers must not pass castles/promos/ep. */
export declare function givesCheckQuiet(b: Board, m: Move): boolean;

