"use strict";
/** Board representation with make/unmake */
Object.defineProperty(exports, "__esModule", { value: true });
exports.Board = exports.START_FEN = void 0;
const types_1 = require("./types");
const bitboard_1 = require("./bitboard");
const attacks_1 = require("./attacks");
const magics_1 = require("./magics");
const zobrist_1 = require("./zobrist");
class Undo {
    constructor(move, castling, epSquare, halfmove, zHi, zLo, captured) {
        this.move = move;
        this.castling = castling;
        this.epSquare = epSquare;
        this.halfmove = halfmove;
        this.zHi = zHi;
        this.zLo = zLo;
        this.captured = captured;
    }
    get zobrist() { return (0, zobrist_1.joinKey)(this.zHi, this.zLo); }
}
/** g1: preallocated undo stack, U_STRIDE Int32 fields per ply (no per-move allocation). */
const U_FROM = 0, U_TO = 1, U_PIECE = 2, U_CAP = 3, U_PROMO = 4, U_FLAGS = 5, U_CASTLING = 6, U_EP = 7, U_HALF = 8, U_ZHI = 9, U_ZLO = 10;
const U_STRIDE = 12;
const U_INIT_PLIES = 512;
const incremental_1 = require("../eval/incremental");
exports.START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
class Board {
    /** 64-bit key as bigint, built on demand (4.1). */
    get zobrist() { return (0, zobrist_1.joinKey)(this.zHi, this.zLo); }
    set zobrist(v) { this.zHi = Number((v >> 32n) & 0xffffffffn) | 0; this.zLo = Number(v & 0xffffffffn) | 0; }
    /** Compat view (allocates; tools/tests only, not for hot paths). */
    get undoStack() {
        const out = [];
        const u = this.undoBuf;
        for (let i = 0; i < this.undoTop; i++) {
            const t = i * U_STRIDE;
            out.push(new Undo({ from: u[t + U_FROM], to: u[t + U_TO], piece: u[t + U_PIECE], captured: u[t + U_CAP], promo: u[t + U_PROMO], flags: u[t + U_FLAGS] }, u[t + U_CASTLING], u[t + U_EP], u[t + U_HALF], u[t + U_ZHI], u[t + U_ZLO], u[t + U_CAP]));
        }
        return out;
    }
    set undoStack(a) {
        this.undoTop = 0;
        for (const x of a) {
            const t = this.undoSlot();
            const u = this.undoBuf;
            u[t + U_FROM] = x.move.from;
            u[t + U_TO] = x.move.to;
            u[t + U_PIECE] = x.move.piece;
            u[t + U_CAP] = x.move.captured;
            u[t + U_PROMO] = x.move.promo;
            u[t + U_FLAGS] = x.move.flags;
            u[t + U_CASTLING] = x.castling;
            u[t + U_EP] = x.epSquare;
            u[t + U_HALF] = x.halfmove;
            u[t + U_ZHI] = x.zHi;
            u[t + U_ZLO] = x.zLo;
        }
    }
    /** Reserve the next undo entry; returns its base offset (grows the buffer when full). */
    undoSlot() {
        const t = this.undoTop * U_STRIDE;
        if (t + U_STRIDE > this.undoBuf.length) {
            const nb = new Int32Array(this.undoBuf.length * 2);
            nb.set(this.undoBuf);
            this.undoBuf = nb;
        }
        this.undoTop++;
        return t;
    }
    /** Repetition scan over the undo stack (same order/semantics as the old search.isRepetition loop). */
    /** magicflat3: true if the top undo entry is a null move (piece None); no allocation. */
    lastMoveIsNull() {
        return this.undoTop > 0 && this.undoBuf[(this.undoTop - 1) * U_STRIDE + U_PIECE] === 0 /* Piece.None */;
    }
    isRepetitionKey(hi, lo) {
        const u = this.undoBuf;
        for (let t = (this.undoTop - 1) * U_STRIDE; t >= 0; t -= U_STRIDE) {
            if (u[t + U_ZLO] === lo && u[t + U_ZHI] === hi)
                return true;
            const pc = u[t + U_PIECE];
            if (u[t + U_CAP] !== 0 /* Piece.None */ || pc === 1 /* Piece.WP */ || pc === 7 /* Piece.BP */)
                break;
        }
        return false;
    }
    constructor(fen) {
        this.squares = new Array(64).fill(0 /* Piece.None */);
        // Dual-u32 bitboards: [piece] / [color]
        this.pieceBB = Array.from({ length: 13 }, () => (0, bitboard_1.emptyBB)());
        this.colorBB = [(0, bitboard_1.emptyBB)(), (0, bitboard_1.emptyBB)()]; // white, black
        this.occupied = (0, bitboard_1.emptyBB)();
        this.whiteKingSq = types_1.SQ_NONE;
        this.blackKingSq = types_1.SQ_NONE;
        this.side = 0 /* Color.White */;
        this.castling = 1 /* Castling.WK */ | 2 /* Castling.WQ */ | 4 /* Castling.BK */ | 8 /* Castling.BQ */;
        this.epSquare = types_1.SQ_NONE;
        this.halfmove = 0;
        this.fullmove = 1;
        this.zHi = 0;
        this.zLo = 0;
        /** Incremental white-relative material+PST */
        this.mgScore = 0;
        this.egScore = 0;
        this.phase = 0;
        /** g1: flat undo stack (see U_* offsets); undoTop = number of entries. */
        this.undoBuf = new Int32Array(U_INIT_PLIES * U_STRIDE);
        this.undoTop = 0;
        this.setFen(fen || exports.START_FEN);
    }
    clone() {
        const b = new Board();
        b.squares = this.squares.slice();
        b.pieceBB = this.pieceBB.map(bitboard_1.cloneBB);
        b.colorBB = this.colorBB.map(bitboard_1.cloneBB);
        b.occupied = (0, bitboard_1.cloneBB)(this.occupied);
        b.whiteKingSq = this.whiteKingSq;
        b.blackKingSq = this.blackKingSq;
        b.side = this.side;
        b.castling = this.castling;
        b.epSquare = this.epSquare;
        b.halfmove = this.halfmove;
        b.fullmove = this.fullmove;
        b.zHi = this.zHi;
        b.zLo = this.zLo;
        b.mgScore = this.mgScore;
        b.egScore = this.egScore;
        b.phase = this.phase;
        b.undoTop = 0;
        return b;
    }
    clear() {
        this.squares.fill(0 /* Piece.None */);
        for (let i = 0; i < 13; i++) {
            this.pieceBB[i].lo = 0;
            this.pieceBB[i].hi = 0;
        }
        this.colorBB[0].lo = this.colorBB[0].hi = 0;
        this.colorBB[1].lo = this.colorBB[1].hi = 0;
        this.occupied.lo = this.occupied.hi = 0;
        this.whiteKingSq = types_1.SQ_NONE;
        this.blackKingSq = types_1.SQ_NONE;
        this.side = 0 /* Color.White */;
        this.castling = 0;
        this.epSquare = types_1.SQ_NONE;
        this.halfmove = 0;
        this.fullmove = 1;
        this.zHi = 0;
        this.zLo = 0;
        this.mgScore = 0;
        this.egScore = 0;
        this.phase = 0;
        this.undoTop = 0;
    }
    putPiece(piece, s) {
        this.squares[s] = piece;
        (0, bitboard_1.setBitMut)(this.pieceBB[piece], s);
        const c = (0, types_1.isWhite)(piece) ? 0 /* Color.White */ : 1 /* Color.Black */;
        (0, bitboard_1.setBitMut)(this.colorBB[c], s);
        (0, bitboard_1.setBitMut)(this.occupied, s);
        if (piece === 6 /* Piece.WK */)
            this.whiteKingSq = s;
        else if (piece === 12 /* Piece.BK */)
            this.blackKingSq = s;
        this.mgScore += (0, incremental_1.putMg)(piece, s);
        this.egScore += (0, incremental_1.putEg)(piece, s);
        this.phase += (0, incremental_1.putPhase)(piece);
    }
    removePiece(s) {
        const piece = this.squares[s];
        if (piece === 0 /* Piece.None */)
            return 0 /* Piece.None */;
        this.mgScore -= (0, incremental_1.putMg)(piece, s);
        this.egScore -= (0, incremental_1.putEg)(piece, s);
        this.phase -= (0, incremental_1.putPhase)(piece);
        this.squares[s] = 0 /* Piece.None */;
        (0, bitboard_1.clearBitMut)(this.pieceBB[piece], s);
        const c = (0, types_1.isWhite)(piece) ? 0 /* Color.White */ : 1 /* Color.Black */;
        (0, bitboard_1.clearBitMut)(this.colorBB[c], s);
        (0, bitboard_1.clearBitMut)(this.occupied, s);
        if (piece === 6 /* Piece.WK */)
            this.whiteKingSq = types_1.SQ_NONE;
        else if (piece === 12 /* Piece.BK */)
            this.blackKingSq = types_1.SQ_NONE;
        return piece;
    }
    movePiece(from, to) {
        const piece = this.squares[from];
        this.removePiece(from);
        // if destination occupied, remove first
        if (this.squares[to] !== 0 /* Piece.None */)
            this.removePiece(to);
        this.putPiece(piece, to);
    }
    setFen(fen) {
        this.clear();
        const parts = fen.trim().split(/\s+/);
        const rows = parts[0].split('/');
        let s = 56; // A8
        for (const row of rows) {
            for (const ch of row) {
                if (ch >= '1' && ch <= '8') {
                    s += parseInt(ch, 10);
                }
                else {
                    const idx = types_1.PIECE_CHARS.indexOf(ch);
                    if (idx > 0)
                        this.putPiece(idx, s);
                    s++;
                }
            }
            s -= 16;
        }
        this.side = parts[1] === 'b' ? 1 /* Color.Black */ : 0 /* Color.White */;
        this.castling = 0;
        if (parts[2] && parts[2] !== '-') {
            if (parts[2].includes('K'))
                this.castling |= 1 /* Castling.WK */;
            if (parts[2].includes('Q'))
                this.castling |= 2 /* Castling.WQ */;
            if (parts[2].includes('k'))
                this.castling |= 4 /* Castling.BK */;
            if (parts[2].includes('q'))
                this.castling |= 8 /* Castling.BQ */;
        }
        this.epSquare = parts[3] ? (0, types_1.parseSq)(parts[3]) : types_1.SQ_NONE;
        this.halfmove = parts[4] ? parseInt(parts[4], 10) : 0;
        this.fullmove = parts[5] ? parseInt(parts[5], 10) : 1;
        this.recomputeZobrist();
    }
    getFen() {
        let fen = '';
        for (let r = 7; r >= 0; r--) {
            let empty = 0;
            for (let f = 0; f < 8; f++) {
                const p = this.squares[(0, types_1.sq)(f, r)];
                if (p === 0 /* Piece.None */)
                    empty++;
                else {
                    if (empty) {
                        fen += empty;
                        empty = 0;
                    }
                    fen += types_1.PIECE_CHARS[p];
                }
            }
            if (empty)
                fen += empty;
            if (r > 0)
                fen += '/';
        }
        fen += this.side === 0 /* Color.White */ ? ' w ' : ' b ';
        let cast = '';
        if (this.castling & 1 /* Castling.WK */)
            cast += 'K';
        if (this.castling & 2 /* Castling.WQ */)
            cast += 'Q';
        if (this.castling & 4 /* Castling.BK */)
            cast += 'k';
        if (this.castling & 8 /* Castling.BQ */)
            cast += 'q';
        fen += cast || '-';
        fen += ' ' + (0, types_1.sqName)(this.epSquare);
        fen += ' ' + this.halfmove + ' ' + this.fullmove;
        return fen;
    }
    recomputeZobrist() {
        let h = 0n;
        for (let s = 0; s < 64; s++) {
            const p = this.squares[s];
            if (p !== 0 /* Piece.None */)
                h ^= (0, zobrist_1.hashPiece)(p, s);
        }
        if (this.side === 1 /* Color.Black */)
            h ^= (0, zobrist_1.hashSide)();
        h ^= (0, zobrist_1.hashCastling)(this.castling);
        h ^= (0, zobrist_1.hashEp)(this.epSquare);
        this.zobrist = h;
    }
    kingSquare(color) {
        return color === 0 /* Color.White */ ? this.whiteKingSq : this.blackKingSq;
    }
    /** Is square attacked by the given color? Scalar lo/hi tests, no intersects/or allocs. */
    isAttacked(s, byColor) {
        if (s < 0 || s > 63)
            return false;
        const occ = this.occupied;
        const pbb = this.pieceBB;
        const o = byColor === 0 /* Color.White */ ? 0 : 6;
        // white attackers use BLACK_PAWN_ATTACKS[s] (squares a white pawn attacks s from), and vice versa
        const pa = byColor === 0 /* Color.White */ ? attacks_1.BLACK_PAWN_ATTACKS[s] : attacks_1.WHITE_PAWN_ATTACKS[s];
        let x = pbb[1 + o];
        if ((pa.lo & x.lo) !== 0 || (pa.hi & x.hi) !== 0)
            return true;
        const kn = attacks_1.KNIGHT_ATTACKS[s];
        x = pbb[2 + o];
        if ((kn.lo & x.lo) !== 0 || (kn.hi & x.hi) !== 0)
            return true;
        const kg = attacks_1.KING_ATTACKS[s];
        x = pbb[6 + o];
        if ((kg.lo & x.lo) !== 0 || (kg.hi & x.hi) !== 0)
            return true;
        const q = pbb[5 + o];
        const oLo = occ.lo, oHi = occ.hi;
        const bi = (0, magics_1.bishopIdx)(s, oLo, oHi);
        const b = pbb[3 + o];
        if ((magics_1.BISHOP_LO[bi] & (b.lo | q.lo)) !== 0 || (magics_1.BISHOP_HI[bi] & (b.hi | q.hi)) !== 0)
            return true;
        const ri = (0, magics_1.rookIdx)(s, oLo, oHi);
        const r = pbb[4 + o];
        if ((magics_1.ROOK_LO[ri] & (r.lo | q.lo)) !== 0 || (magics_1.ROOK_HI[ri] & (r.hi | q.hi)) !== 0)
            return true;
        return false;
    }
    inCheck(color) {
        const c = color === undefined ? this.side : color;
        const ks = this.kingSquare(c);
        return this.isAttacked(ks, c === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */);
    }
    makeMove(m) {
        {
            const t = this.undoSlot();
            const u = this.undoBuf;
            u[t + U_FROM] = m.from;
            u[t + U_TO] = m.to;
            u[t + U_PIECE] = m.piece;
            u[t + U_CAP] = m.captured;
            u[t + U_PROMO] = m.promo;
            u[t + U_FLAGS] = m.flags;
            u[t + U_CASTLING] = this.castling;
            u[t + U_EP] = this.epSquare;
            u[t + U_HALF] = this.halfmove;
            u[t + U_ZHI] = this.zHi;
            u[t + U_ZLO] = this.zLo;
        }
        // Clear EP from hash
        {
            const _i = (0, zobrist_1.epIdx)(this.epSquare);
            this.zHi ^= zobrist_1.ZE_HI[_i];
            this.zLo ^= zobrist_1.ZE_LO[_i];
        }
        this.epSquare = types_1.SQ_NONE;
        const us = this.side;
        const them = us === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */;
        // Update halfmove
        if (m.piece === 1 /* Piece.WP */ || m.piece === 7 /* Piece.BP */ || m.captured !== 0 /* Piece.None */) {
            this.halfmove = 0;
        }
        else {
            this.halfmove++;
        }
        // Remove captured
        if (m.flags & types_1.MOVE_ENPASSANT) {
            const capSq = us === 0 /* Color.White */ ? m.to - 8 : m.to + 8;
            const cap = this.removePiece(capSq);
            {
                const _i = cap * 64 + capSq;
                this.zHi ^= zobrist_1.ZP_HI[_i];
                this.zLo ^= zobrist_1.ZP_LO[_i];
            }
        }
        else if (m.captured !== 0 /* Piece.None */) {
            this.removePiece(m.to);
            {
                const _i = m.captured * 64 + m.to;
                this.zHi ^= zobrist_1.ZP_HI[_i];
                this.zLo ^= zobrist_1.ZP_LO[_i];
            }
        }
        // Move piece
        {
            const _i = m.piece * 64 + m.from;
            this.zHi ^= zobrist_1.ZP_HI[_i];
            this.zLo ^= zobrist_1.ZP_LO[_i];
        }
        this.removePiece(m.from);
        let placed = m.piece;
        if (m.promo !== 0 /* Piece.None */) {
            placed = m.promo;
        }
        this.putPiece(placed, m.to);
        {
            const _i = placed * 64 + m.to;
            this.zHi ^= zobrist_1.ZP_HI[_i];
            this.zLo ^= zobrist_1.ZP_LO[_i];
        }
        // Castling rook move
        if (m.flags & types_1.MOVE_CASTLE) {
            if (m.to === 6) { // white O-O: rook H1->F1
                {
                    const _i = 4 /* Piece.WR */ * 64 + 7;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                {
                    const _i = 4 /* Piece.WR */ * 64 + 5;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                this.movePiece(7, 5);
            }
            else if (m.to === 2) { // white O-O-O
                {
                    const _i = 4 /* Piece.WR */ * 64 + 0;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                {
                    const _i = 4 /* Piece.WR */ * 64 + 3;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                this.movePiece(0, 3);
            }
            else if (m.to === 62) { // black O-O
                {
                    const _i = 10 /* Piece.BR */ * 64 + 63;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                {
                    const _i = 10 /* Piece.BR */ * 64 + 61;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                this.movePiece(63, 61);
            }
            else if (m.to === 58) { // black O-O-O
                {
                    const _i = 10 /* Piece.BR */ * 64 + 56;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                {
                    const _i = 10 /* Piece.BR */ * 64 + 59;
                    this.zHi ^= zobrist_1.ZP_HI[_i];
                    this.zLo ^= zobrist_1.ZP_LO[_i];
                }
                this.movePiece(56, 59);
            }
        }
        // Double pawn push -> set EP
        if (m.flags & types_1.MOVE_DOUBLE) {
            this.epSquare = us === 0 /* Color.White */ ? m.from + 8 : m.from - 8;
        }
        // Update castling rights
        {
            const _i = this.castling & 15;
            this.zHi ^= zobrist_1.ZC_HI[_i];
            this.zLo ^= zobrist_1.ZC_LO[_i];
        }
        if (m.piece === 6 /* Piece.WK */ || m.from === 4) {
            this.castling &= ~(1 /* Castling.WK */ | 2 /* Castling.WQ */);
        }
        if (m.piece === 12 /* Piece.BK */ || m.from === 60) {
            this.castling &= ~(4 /* Castling.BK */ | 8 /* Castling.BQ */);
        }
        if (m.from === 0 || m.to === 0)
            this.castling &= ~2 /* Castling.WQ */;
        if (m.from === 7 || m.to === 7)
            this.castling &= ~1 /* Castling.WK */;
        if (m.from === 56 || m.to === 56)
            this.castling &= ~8 /* Castling.BQ */;
        if (m.from === 63 || m.to === 63)
            this.castling &= ~4 /* Castling.BK */;
        {
            const _i = this.castling & 15;
            this.zHi ^= zobrist_1.ZC_HI[_i];
            this.zLo ^= zobrist_1.ZC_LO[_i];
        }
        {
            const _i = (0, zobrist_1.epIdx)(this.epSquare);
            this.zHi ^= zobrist_1.ZE_HI[_i];
            this.zLo ^= zobrist_1.ZE_LO[_i];
        }
        this.zHi ^= zobrist_1.ZS_HI;
        this.zLo ^= zobrist_1.ZS_LO;
        this.side = them;
        if (us === 1 /* Color.Black */)
            this.fullmove++;
        // legality: own king not in check
        if (this.inCheck(us)) {
            this.unmakeMove();
            return false;
        }
        return true;
    }
    unmakeMove() {
        if (this.undoTop === 0)
            return;
        this.undoTop--;
        const u = this.undoBuf;
        const t = this.undoTop * U_STRIDE;
        const mFrom = u[t + U_FROM], mTo = u[t + U_TO], mPiece = u[t + U_PIECE], mCap = u[t + U_CAP], mFlags = u[t + U_FLAGS];
        const us = this.side === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */; // side that moved
        this.side = us;
        if (us === 1 /* Color.Black */)
            this.fullmove--;
        this.castling = u[t + U_CASTLING];
        this.epSquare = u[t + U_EP];
        this.halfmove = u[t + U_HALF];
        this.zHi = u[t + U_ZHI];
        this.zLo = u[t + U_ZLO];
        // Undo castling rook
        if (mFlags & types_1.MOVE_CASTLE) {
            if (mTo === 6)
                this.movePiece(5, 7);
            else if (mTo === 2)
                this.movePiece(3, 0);
            else if (mTo === 62)
                this.movePiece(61, 63);
            else if (mTo === 58)
                this.movePiece(59, 56);
        }
        // Remove piece from to (promo or normal)
        this.removePiece(mTo);
        this.putPiece(mPiece, mFrom);
        // Restore captured
        if (mFlags & types_1.MOVE_ENPASSANT) {
            const capSq = us === 0 /* Color.White */ ? mTo - 8 : mTo + 8;
            this.putPiece(mCap, capSq);
        }
        else if (mCap !== 0 /* Piece.None */) {
            this.putPiece(mCap, mTo);
        }
    }
    /** Null move for NMP */
    makeNullMove() {
        {
            const t = this.undoSlot();
            const u = this.undoBuf;
            u[t + U_FROM] = 0;
            u[t + U_TO] = 0;
            u[t + U_PIECE] = 0 /* Piece.None */;
            u[t + U_CAP] = 0 /* Piece.None */;
            u[t + U_PROMO] = 0 /* Piece.None */;
            u[t + U_FLAGS] = 0;
            u[t + U_CASTLING] = this.castling;
            u[t + U_EP] = this.epSquare;
            u[t + U_HALF] = this.halfmove;
            u[t + U_ZHI] = this.zHi;
            u[t + U_ZLO] = this.zLo;
        }
        {
            const _i = (0, zobrist_1.epIdx)(this.epSquare);
            this.zHi ^= zobrist_1.ZE_HI[_i];
            this.zLo ^= zobrist_1.ZE_LO[_i];
        }
        this.epSquare = types_1.SQ_NONE;
        {
            const _i = (0, zobrist_1.epIdx)(this.epSquare);
            this.zHi ^= zobrist_1.ZE_HI[_i];
            this.zLo ^= zobrist_1.ZE_LO[_i];
        }
        this.zHi ^= zobrist_1.ZS_HI;
        this.zLo ^= zobrist_1.ZS_LO;
        this.side = this.side === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */;
        this.halfmove++;
    }
    unmakeNullMove() {
        if (this.undoTop === 0)
            return;
        this.undoTop--;
        const u = this.undoBuf;
        const t = this.undoTop * U_STRIDE;
        this.side = this.side === 0 /* Color.White */ ? 1 /* Color.Black */ : 0 /* Color.White */;
        this.castling = u[t + U_CASTLING];
        this.epSquare = u[t + U_EP];
        this.halfmove = u[t + U_HALF];
        this.zHi = u[t + U_ZHI];
        this.zLo = u[t + U_ZLO];
    }
    toString() {
        let s = '';
        for (let r = 7; r >= 0; r--) {
            s += (r + 1) + ' ';
            for (let f = 0; f < 8; f++) {
                s += types_1.PIECE_CHARS[this.squares[(0, types_1.sq)(f, r)]] + ' ';
            }
            s += '\n';
        }
        s += '  a b c d e f g h\n';
        s += this.getFen();
        return s;
    }
}
exports.Board = Board;
// screlu2-1745: exported so eval/nnue.js can assert its hard-coded undo layout at load
exports.U_STRIDE = U_STRIDE;
exports.U_ZHI = U_ZHI;
exports.U_ZLO = U_ZLO;
//# sourceMappingURL=board.js.map
