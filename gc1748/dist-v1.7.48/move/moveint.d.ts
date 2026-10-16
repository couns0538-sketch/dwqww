/** Packed integer moves — avoid object allocation in search hot path
 * Layout (32-bit):
 *  0..5   from
 *  6..11  to
 *  12..15 piece
 *  16..19 captured
 *  20..23 promo
 *  24..27 flags
 */
export type MoveInt = number;
export declare function makeMoveInt(from: number, to: number, piece: number, captured: number, promo: number, flags: number): MoveInt;
export declare function fromOf(m: MoveInt): number;
export declare function toOf(m: MoveInt): number;
export declare function pieceOf(m: MoveInt): number;
export declare function capturedOf(m: MoveInt): number;
export declare function promoOf(m: MoveInt): number;
export declare function flagsOf(m: MoveInt): number;
export declare function moveIntToUci(m: MoveInt): string;
export declare function sameMoveInt(a: MoveInt, b: MoveInt): boolean;
/** Convert legacy Move object fields */
export declare function fromLegacy(from: number, to: number, piece: number, captured: number, promo: number, flags: number): MoveInt;

