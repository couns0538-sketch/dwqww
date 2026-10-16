"use strict";
/** Chess engine core types */
Object.defineProperty(exports, "__esModule", { value: true });
exports.PIECE_VALUES = exports.PIECE_CHARS = exports.RANK_8 = exports.RANK_7 = exports.RANK_6 = exports.RANK_5 = exports.RANK_4 = exports.RANK_3 = exports.RANK_2 = exports.RANK_1 = exports.FILE_H = exports.FILE_G = exports.FILE_F = exports.FILE_E = exports.FILE_D = exports.FILE_C = exports.FILE_B = exports.FILE_A = exports.SQ_NONE = exports.MOVE_DOUBLE = exports.MOVE_ENPASSANT = exports.MOVE_CASTLE = void 0;
exports.sq = sq;
exports.fileOf = fileOf;
exports.rankOf = rankOf;
exports.sqName = sqName;
exports.parseSq = parseSq;
exports.isWhite = isWhite;
exports.isBlack = isBlack;
exports.pieceColor = pieceColor;
exports.pieceType = pieceType;
exports.makePiece = makePiece;
exports.MOVE_CASTLE = 1;
exports.MOVE_ENPASSANT = 2;
exports.MOVE_DOUBLE = 4;
exports.SQ_NONE = 64;
exports.FILE_A = 0, exports.FILE_B = 1, exports.FILE_C = 2, exports.FILE_D = 3;
exports.FILE_E = 4, exports.FILE_F = 5, exports.FILE_G = 6, exports.FILE_H = 7;
exports.RANK_1 = 0, exports.RANK_2 = 1, exports.RANK_3 = 2, exports.RANK_4 = 3;
exports.RANK_5 = 4, exports.RANK_6 = 5, exports.RANK_7 = 6, exports.RANK_8 = 7;
function sq(file, rank) {
    return rank * 8 + file;
}
function fileOf(s) {
    return s & 7;
}
function rankOf(s) {
    return s >> 3;
}
function sqName(s) {
    if (s === exports.SQ_NONE)
        return '-';
    return String.fromCharCode(97 + fileOf(s)) + (rankOf(s) + 1);
}
function parseSq(name) {
    if (name === '-' || name.length < 2)
        return exports.SQ_NONE;
    const f = name.charCodeAt(0) - 97;
    const r = name.charCodeAt(1) - 49;
    if (f < 0 || f > 7 || r < 0 || r > 7)
        return exports.SQ_NONE;
    return sq(f, r);
}
function isWhite(p) {
    return p >= 1 /* Piece.WP */ && p <= 6 /* Piece.WK */;
}
function isBlack(p) {
    return p >= 7 /* Piece.BP */ && p <= 12 /* Piece.BK */;
}
function pieceColor(p) {
    return isWhite(p) ? 0 /* Color.White */ : 1 /* Color.Black */;
}
function pieceType(p) {
    // 1=P,2=N,3=B,4=R,5=Q,6=K
    return p <= 6 /* Piece.WK */ ? p : p - 6;
}
function makePiece(color, type) {
    return (color === 0 /* Color.White */ ? type : type + 6);
}
exports.PIECE_CHARS = '.PNBRQKpnbrqk';
exports.PIECE_VALUES = [0, 100, 320, 330, 500, 900, 20000, 100, 320, 330, 500, 900, 20000];
//# sourceMappingURL=types.js.map
