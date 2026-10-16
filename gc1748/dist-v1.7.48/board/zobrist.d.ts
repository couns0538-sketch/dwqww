/** Zobrist hashing */
import { Piece, Square } from './types';
export declare const ZOBRIST_PIECE: bigint[][];
export declare const ZOBRIST_SIDE: bigint;
export declare const ZOBRIST_CASTLING: bigint[];
export declare const ZOBRIST_EP: bigint[];
export declare function hashPiece(piece: Piece, sq: Square): bigint;
export declare function hashSide(): bigint;
export declare function hashCastling(rights: number): bigint;
export declare function hashEp(epSquare: Square): bigint;
/** index = piece*64 + sq */
export declare const ZP_HI: Int32Array<ArrayBufferLike>, ZP_LO: Int32Array<ArrayBufferLike>;
export declare const ZC_HI: Int32Array<ArrayBufferLike>, ZC_LO: Int32Array<ArrayBufferLike>;
export declare const ZE_HI: Int32Array<ArrayBufferLike>, ZE_LO: Int32Array<ArrayBufferLike>;
export declare const ZS_HI: number, ZS_LO: number;
export declare function epIdx(epSquare: Square): number;
export declare function joinKey(hi: number, lo: number): bigint;

