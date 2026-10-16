/** Legal / pseudo-legal move generation */
import { Board } from '../board/board';
import { Move } from '../board/types';
/** Generate all pseudo-legal moves (may leave king in check). Scalar lo/hi + ctz loops, same move order as before. */
export declare function generateMoves(board: Board, capturesOnly?: boolean): Move[];
/** Generate strictly legal moves */
export declare function generateLegalMoves(board: Board, capturesOnly?: boolean): Move[];
export declare function moveToUci(m: Move): string;
export declare function parseUciMove(board: Board, uci: string): Move | null;
/** Perft */
export declare function perft(board: Board, depth: number): number;
export declare function perftDivide(board: Board, depth: number): Map<string, number>;

