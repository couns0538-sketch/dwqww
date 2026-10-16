/** Board representation with make/unmake */
import { Piece, Color, Square, Move, UndoInfo } from './types';
import { BB } from './bitboard';
export declare const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
export declare class Board {
    squares: Piece[];
    pieceBB: BB[];
    colorBB: BB[];
    occupied: BB;
    whiteKingSq: Square;
    blackKingSq: Square;
    side: Color;
    castling: number;
    epSquare: Square;
    halfmove: number;
    fullmove: number;
    zHi: number;
    zLo: number;
    /** 64-bit key as bigint, built on demand (4.1). */
    get zobrist(): bigint;
    set zobrist(v: bigint);
    /** Incremental white-relative material+PST */
    mgScore: number;
    egScore: number;
    phase: number;
    undoStack: UndoInfo[];
    constructor(fen?: string);
    clone(): Board;
    clear(): void;
    putPiece(piece: Piece, s: Square): void;
    removePiece(s: Square): Piece;
    movePiece(from: Square, to: Square): void;
    setFen(fen: string): void;
    getFen(): string;
    recomputeZobrist(): void;
    kingSquare(color: Color): Square;
    /** Is square attacked by the given color? */
    isAttacked(s: Square, byColor: Color): boolean;
    inCheck(color?: Color): boolean;
    makeMove(m: Move): boolean;
    unmakeMove(): void;
    /** Null move for NMP */
    makeNullMove(): void;
    unmakeNullMove(): void;
    toString(): string;
}

