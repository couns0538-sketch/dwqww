"use strict";
/** Packed integer moves — avoid object allocation in search hot path
 * Layout (32-bit):
 *  0..5   from
 *  6..11  to
 *  12..15 piece
 *  16..19 captured
 *  20..23 promo
 *  24..27 flags
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.makeMoveInt = makeMoveInt;
exports.fromOf = fromOf;
exports.toOf = toOf;
exports.pieceOf = pieceOf;
exports.capturedOf = capturedOf;
exports.promoOf = promoOf;
exports.flagsOf = flagsOf;
exports.moveIntToUci = moveIntToUci;
exports.sameMoveInt = sameMoveInt;
exports.fromLegacy = fromLegacy;
function makeMoveInt(from, to, piece, captured, promo, flags) {
    return from | (to << 6) | (piece << 12) | (captured << 16) | (promo << 20) | (flags << 24);
}
function fromOf(m) { return m & 63; }
function toOf(m) { return (m >> 6) & 63; }
function pieceOf(m) { return (m >> 12) & 15; }
function capturedOf(m) { return (m >> 16) & 15; }
function promoOf(m) { return (m >> 20) & 15; }
function flagsOf(m) { return (m >> 24) & 15; }
function moveIntToUci(m) {
    const files = 'abcdefgh';
    const from = fromOf(m), to = toOf(m);
    let s = files[from & 7] + (1 + (from >> 3)) + files[to & 7] + (1 + (to >> 3));
    const promo = promoOf(m);
    if (promo) {
        const pt = promo <= 6 ? promo : promo - 6;
        s += '  nbrq'[pt] || '';
    }
    return s;
}
function sameMoveInt(a, b) {
    return (a & 0x0fff0fff) === (b & 0x0fff0fff); // from, to, promo
}
/** Convert legacy Move object fields */
function fromLegacy(from, to, piece, captured, promo, flags) {
    return makeMoveInt(from, to, piece, captured, promo, flags);
}
//# sourceMappingURL=moveint.js.map
