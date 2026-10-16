"use strict";
/** Legal / pseudo-legal move generation */
Object.defineProperty(exports, "__esModule", { value: true });
exports.generateMoves = generateMoves;
exports.generateLegalMoves = generateLegalMoves;
exports.moveToUci = moveToUci;
exports.parseUciMove = parseUciMove;
exports.perft = perft;
exports.perftDivide = perftDivide;
const types_1 = require("../board/types");
const attacks_1 = require("../board/attacks");
const magics_1 = require("../board/magics");
function addMove(moves, from, to, piece, captured, promo, flags) {
    moves.push({ from, to, piece, captured, promo, flags });
}
function addPromotions(moves, from, to, piece, captured, color) {
    const q = (0, types_1.makePiece)(color, 5);
    const r = (0, types_1.makePiece)(color, 4);
    const b = (0, types_1.makePiece)(color, 3);
    const n = (0, types_1.makePiece)(color, 2);
    addMove(moves, from, to, piece, captured, q, 0);
    addMove(moves, from, to, piece, captured, r, 0);
    addMove(moves, from, to, piece, captured, b, 0);
    addMove(moves, from, to, piece, captured, n, 0);
}
/** Generate all pseudo-legal moves (may leave king in check). Scalar lo/hi + ctz loops, same move order as before. */
function generateMoves(board, capturesOnly = false) {
    const moves = [];
    const us = board.side;
    const them = us === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */;
    const enemyKing = them === 0 /* Color.White */ ? 6 /* Piece.WK */ : 12 /* Piece.BK */;
    const sq = board.squares;
    const our = board.colorBB[us], their = board.colorBB[them], ek = board.pieceBB[enemyKing];
    const occ = board.occupied;
    const occLo = occ.lo, occHi = occ.hi;
    const nekLo = ~ek.lo, nekHi = ~ek.hi;
    // Never generate king captures
    const theirLo = (their.lo & nekLo) >>> 0, theirHi = (their.hi & nekHi) >>> 0;
    const notOursLo = (~our.lo & nekLo) >>> 0, notOursHi = (~our.hi & nekHi) >>> 0;
    const epSq = board.epSquare;
    // Pawns
    {
        const white = us === 0 /* Color.White */;
        const P = white ? 1 /* Piece.WP */ : 7 /* Piece.BP */;
        const pb = board.pieceBB[P];
        const PA = white ? attacks_1.WHITE_PAWN_ATTACKS : attacks_1.BLACK_PAWN_ATTACKS;
        for (let half = 0; half < 2; half++) {
            let w = half === 0 ? pb.lo : pb.hi;
            while (w) {
                const lsb = w & -w;
                w ^= lsb;
                const from = (half === 0 ? 0 : 32) + 31 - Math.clz32(lsb);
                const push = white ? from + 8 : from - 8;
                if (push >= 0 && push < 64 && !(((push < 32 ? occLo >>> push : occHi >>> (push - 32)) & 1) !== 0)) {
                    if (white ? push >= 56 : push <= 7) {
                        if (!capturesOnly)
                            addPromotions(moves, from, push, P, 0 /* Piece.None */, us);
                    }
                    else if (!capturesOnly) {
                        addMove(moves, from, push, P, 0 /* Piece.None */, 0 /* Piece.None */, 0);
                        if (white ? (from >= 8 && from <= 15) : (from >= 48 && from <= 55)) {
                            const dbl = white ? from + 16 : from - 16;
                            if (!((dbl < 32 ? occLo >>> dbl : occHi >>> (dbl - 32)) & 1)) {
                                addMove(moves, from, dbl, P, 0 /* Piece.None */, 0 /* Piece.None */, types_1.MOVE_DOUBLE);
                            }
                        }
                    }
                }
                const pa = PA[from];
                // Captures
                let cl = (pa.lo & theirLo) >>> 0, ch = (pa.hi & theirHi) >>> 0;
                while (cl) {
                    const b = cl & -cl;
                    cl ^= b;
                    const to = 31 - Math.clz32(b);
                    const cap = sq[to];
                    if (white ? to >= 56 : to <= 7)
                        addPromotions(moves, from, to, P, cap, us);
                    else
                        addMove(moves, from, to, P, cap, 0 /* Piece.None */, 0);
                }
                while (ch) {
                    const b = ch & -ch;
                    ch ^= b;
                    const to = 63 - Math.clz32(b);
                    const cap = sq[to];
                    if (white ? to >= 56 : to <= 7)
                        addPromotions(moves, from, to, P, cap, us);
                    else
                        addMove(moves, from, to, P, cap, 0 /* Piece.None */, 0);
                }
                // En passant
                if (epSq !== types_1.SQ_NONE && (epSq < 32 ? ((pa.lo >>> epSq) & 1) : ((pa.hi >>> (epSq - 32)) & 1)) !== 0) {
                    addMove(moves, from, epSq, P, white ? 7 /* Piece.BP */ : 1 /* Piece.WP */, 0 /* Piece.None */, types_1.MOVE_ENPASSANT);
                }
            }
        }
    }
    const nOff = us === 0 /* Color.White */ ? 0 : 6;
    // Knights, bishops, rooks, queens
    emitTargets(moves, sq, board.pieceBB[2 + nOff], 0, attacks_1.KNIGHT_ATTACKS, 2 + nOff, capturesOnly, theirLo, theirHi, notOursLo, notOursHi, occ);
    emitTargets(moves, sq, board.pieceBB[3 + nOff], 1, null, 3 + nOff, capturesOnly, theirLo, theirHi, notOursLo, notOursHi, occ);
    emitTargets(moves, sq, board.pieceBB[4 + nOff], 2, null, 4 + nOff, capturesOnly, theirLo, theirHi, notOursLo, notOursHi, occ);
    emitTargets(moves, sq, board.pieceBB[5 + nOff], 3, null, 5 + nOff, capturesOnly, theirLo, theirHi, notOursLo, notOursHi, occ);
    // King
    const king = us === 0 /* Color.White */ ? 6 /* Piece.WK */ : 12 /* Piece.BK */;
    const kb = board.pieceBB[king];
    emitTargets(moves, sq, kb, 4, attacks_1.KING_ATTACKS, king, capturesOnly, theirLo, theirHi, notOursLo, notOursHi, occ);
    if (!capturesOnly && (kb.lo | kb.hi)) {
        // Castling (same conditions as before; king bitboard non-empty)
        if (us === 0 /* Color.White */) {
            if ((board.castling & 1 /* Castling.WK */) &&
                sq[5] === 0 /* Piece.None */ && sq[6] === 0 /* Piece.None */ &&
                !board.isAttacked(4, 1 /* Color.Black */) &&
                !board.isAttacked(5, 1 /* Color.Black */) &&
                !board.isAttacked(6, 1 /* Color.Black */)) {
                addMove(moves, 4, 6, 6 /* Piece.WK */, 0 /* Piece.None */, 0 /* Piece.None */, types_1.MOVE_CASTLE);
            }
            if ((board.castling & 2 /* Castling.WQ */) &&
                sq[3] === 0 /* Piece.None */ && sq[2] === 0 /* Piece.None */ && sq[1] === 0 /* Piece.None */ &&
                !board.isAttacked(4, 1 /* Color.Black */) &&
                !board.isAttacked(3, 1 /* Color.Black */) &&
                !board.isAttacked(2, 1 /* Color.Black */)) {
                addMove(moves, 4, 2, 6 /* Piece.WK */, 0 /* Piece.None */, 0 /* Piece.None */, types_1.MOVE_CASTLE);
            }
        }
        else {
            if ((board.castling & 4 /* Castling.BK */) &&
                sq[61] === 0 /* Piece.None */ && sq[62] === 0 /* Piece.None */ &&
                !board.isAttacked(60, 0 /* Color.White */) &&
                !board.isAttacked(61, 0 /* Color.White */) &&
                !board.isAttacked(62, 0 /* Color.White */)) {
                addMove(moves, 60, 62, 12 /* Piece.BK */, 0 /* Piece.None */, 0 /* Piece.None */, types_1.MOVE_CASTLE);
            }
            if ((board.castling & 8 /* Castling.BQ */) &&
                sq[59] === 0 /* Piece.None */ && sq[58] === 0 /* Piece.None */ && sq[57] === 0 /* Piece.None */ &&
                !board.isAttacked(60, 0 /* Color.White */) &&
                !board.isAttacked(59, 0 /* Color.White */) &&
                !board.isAttacked(58, 0 /* Color.White */)) {
                addMove(moves, 60, 58, 12 /* Piece.BK */, 0 /* Piece.None */, 0 /* Piece.None */, types_1.MOVE_CASTLE);
            }
        }
    }
    return moves;
}
/** kind: 0 knight table, 1 bishop, 2 rook, 3 queen, 4 king table. */
function emitTargets(moves, sq, pieces, kind, table, piece, capturesOnly, theirLo, theirHi, notOursLo, notOursHi, occ) {
    // orderfast: target mask chosen once per call; leaper table checked by null (kind 0/4 always pass a table).
    const maskLo = capturesOnly ? theirLo : notOursLo, maskHi = capturesOnly ? theirHi : notOursHi;
    if ((pieces.lo | pieces.hi) === 0)
        return;
    for (let half = 0; half < 2; half++) {
        let w = half === 0 ? pieces.lo : pieces.hi;
        while (w) {
            const lsb = w & -w;
            w ^= lsb;
            const from = (half === 0 ? 0 : 32) + 31 - Math.clz32(lsb);
            let tl, th;
            if (table !== null) {
                const a = table[from];
                tl = a.lo;
                th = a.hi;
            }
            else if (kind === 1) {
                const i = (0, magics_1.bishopIdx)(from, occ.lo, occ.hi);
                tl = magics_1.BISHOP_LO[i];
                th = magics_1.BISHOP_HI[i];
            }
            else if (kind === 2) {
                const i = (0, magics_1.rookIdx)(from, occ.lo, occ.hi);
                tl = magics_1.ROOK_LO[i];
                th = magics_1.ROOK_HI[i];
            }
            else {
                const i = (0, magics_1.rookIdx)(from, occ.lo, occ.hi), j = (0, magics_1.bishopIdx)(from, occ.lo, occ.hi);
                tl = magics_1.ROOK_LO[i] | magics_1.BISHOP_LO[j];
                th = magics_1.ROOK_HI[i] | magics_1.BISHOP_HI[j];
            }
            tl = (tl & maskLo) >>> 0;
            th = (th & maskHi) >>> 0;
            while (tl) {
                const b = tl & -tl;
                tl ^= b;
                const to = 31 - Math.clz32(b);
                moves.push({ from, to, piece, captured: sq[to], promo: 0 /* Piece.None */, flags: 0 });
            }
            while (th) {
                const b = th & -th;
                th ^= b;
                const to = 63 - Math.clz32(b);
                moves.push({ from, to, piece, captured: sq[to], promo: 0 /* Piece.None */, flags: 0 });
            }
        }
    }
}
/** Generate strictly legal moves */
function generateLegalMoves(board, capturesOnly = false) {
    const pseudo = generateMoves(board, capturesOnly);
    const legal = [];
    for (const m of pseudo) {
        if (board.makeMove(m)) {
            legal.push(m);
            board.unmakeMove();
        }
    }
    return legal;
}
function moveToUci(m) {
    const files = 'abcdefgh';
    let s = files[m.from & 7] + (1 + (m.from >> 3)) + files[m.to & 7] + (1 + (m.to >> 3));
    if (m.promo !== 0 /* Piece.None */) {
        const pt = (0, types_1.pieceType)(m.promo);
        s += '  nbrq'[pt]; // 1=P skip, 2=n, 3=b, 4=r, 5=q
    }
    return s;
}
function parseUciMove(board, uci) {
    if (uci.length < 4)
        return null;
    const from = (uci.charCodeAt(0) - 97) + (uci.charCodeAt(1) - 49) * 8;
    const to = (uci.charCodeAt(2) - 97) + (uci.charCodeAt(3) - 49) * 8;
    let promo = 0 /* Piece.None */;
    if (uci.length >= 5) {
        const ch = uci[4].toLowerCase();
        const us = board.side;
        if (ch === 'q')
            promo = (0, types_1.makePiece)(us, 5);
        else if (ch === 'r')
            promo = (0, types_1.makePiece)(us, 4);
        else if (ch === 'b')
            promo = (0, types_1.makePiece)(us, 3);
        else if (ch === 'n')
            promo = (0, types_1.makePiece)(us, 2);
    }
    const legal = generateLegalMoves(board);
    for (const m of legal) {
        if (m.from === from && m.to === to && m.promo === promo)
            return m;
    }
    // Also match if promo not specified but only one promo exists
    if (promo === 0 /* Piece.None */) {
        for (const m of legal) {
            if (m.from === from && m.to === to)
                return m;
        }
    }
    return null;
}
/** Perft */
function perft(board, depth) {
    if (depth === 0)
        return 1;
    const moves = generateMoves(board);
    let nodes = 0;
    for (const m of moves) {
        if (board.makeMove(m)) {
            if (depth === 1)
                nodes++;
            else
                nodes += perft(board, depth - 1);
            board.unmakeMove();
        }
    }
    return nodes;
}
function perftDivide(board, depth) {
    const result = new Map();
    const moves = generateMoves(board);
    for (const m of moves) {
        if (board.makeMove(m)) {
            const n = depth === 1 ? 1 : perft(board, depth - 1);
            result.set(moveToUci(m), n);
            board.unmakeMove();
        }
    }
    return result;
}
//# sourceMappingURL=movegen.js.map
