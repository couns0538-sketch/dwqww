/** Chess engine core types */
export declare const enum Piece {
    None = 0,
    WP = 1,
    WN = 2,
    WB = 3,
    WR = 4,
    WQ = 5,
    WK = 6,
    BP = 7,
    BN = 8,
    BB = 9,
    BR = 10,
    BQ = 11,
    BK = 12
}
export declare const enum Color {
    White = 0,
    Black = 1
}
export declare const enum Castling {
    WK = 1,
    WQ = 2,
    BK = 4,
    BQ = 8
}
export type Square = number;
export interface Move {
    from: Square;
    to: Square;
    piece: Piece;
    captured: Piece;
    promo: Piece;
    flags: number;
    see?: number;
}
export declare const MOVE_CASTLE = 1;
export declare const MOVE_ENPASSANT = 2;
export declare const MOVE_DOUBLE = 4;
export interface UndoInfo {
    move: Move;
    castling: number;
    epSquare: Square;
    halfmove: number;
    zHi: number;
    zLo: number;
    /** 64-bit key as bigint, built on demand from zHi/zLo (4.1 compat for repetition check). */
    readonly zobrist: bigint;
    captured: Piece;
}
export declare const SQ_NONE = 64;
export declare const FILE_A = 0, FILE_B = 1, FILE_C = 2, FILE_D = 3;
export declare const FILE_E = 4, FILE_F = 5, FILE_G = 6, FILE_H = 7;
export declare const RANK_1 = 0, RANK_2 = 1, RANK_3 = 2, RANK_4 = 3;
export declare const RANK_5 = 4, RANK_6 = 5, RANK_7 = 6, RANK_8 = 7;
export declare function sq(file: number, rank: number): Square;
export declare function fileOf(s: Square): number;
export declare function rankOf(s: Square): number;
export declare function sqName(s: Square): string;
export declare function parseSq(name: string): Square;
export declare function isWhite(p: Piece): boolean;
export declare function isBlack(p: Piece): boolean;
export declare function pieceColor(p: Piece): Color;
export declare function pieceType(p: Piece): number;
export declare function makePiece(color: Color, type: number): Piece;
export declare const PIECE_CHARS = ".PNBRQKpnbrqk";
export declare const PIECE_VALUES: number[];

