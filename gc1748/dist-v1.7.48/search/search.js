"use strict";
/** Alpha-beta search: PVS, QSearch, NMP, LMR, SEE, futility, razoring, killers, history, aspiration */
Object.defineProperty(exports, "__esModule", { value: true });
exports.Search = exports.gcDebugStats = void 0;
exports.rootMoveKey = rootMoveKey;
const types_1 = require("../board/types");
const movegen_1 = require("../move/movegen");
const evaluate_1 = require("../eval/evaluate");
const tt_1 = require("./tt");
const bitboard_1 = require("../board/bitboard");
const attacks_1 = require("../board/attacks");
const see_1 = require("./see");
const givescheck_1 = require("./givescheck");
const types_2 = require("../board/types");
/** prune2fast debug: GROK_GC_DEBUG=1 asserts givesCheckQuiet == makeMove+inCheck for every legal quiet move seen in search. */
const GC_DEBUG = typeof process !== 'undefined' && process.env.GROK_GC_DEBUG === '1';
exports.gcDebugStats = { checked: 0, mismatches: 0 };
if (GC_DEBUG)
    process.on('exit', () => { process.stderr.write(`GC_DEBUG checked=${exports.gcDebugStats.checked} mismatches=${exports.gcDebugStats.mismatches}\n`); });
const MAX_PLY = 128;
/** Pseudo-legal check for one unpacked TT move. Shared table only. */
function sharedMoveOk(board, mv) {
    const from = mv.from | 0;
    const to = mv.to | 0;
    if (from < 0 || from > 63 || to < 0 || to > 63 || from === to)
        return false;
    const piece = board.squares[from];
    if (!piece)
        return false;
    const white = board.side === 0;
    if (white ? piece > 6 : piece < 7)
        return false;
    const promo = mv.promo | 0;
    const pt = piece <= 6 ? piece : piece - 6;
    const dest = board.squares[to];
    if (dest && (white ? dest <= 6 : dest >= 7))
        return false;
    if (pt === 1) {
        const last = white ? 7 : 0;
        const onLast = (to >> 3) === last;
        if (onLast) {
            const good = white
                ? promo === 2 || promo === 3 || promo === 4 || promo === 5
                : promo === 8 || promo === 9 || promo === 10 || promo === 11;
            if (!good)
                return false;
        }
        else if (promo)
            return false;
        const step = white ? 8 : -8;
        const occ = board.occupied;
        if (to === from + step) {
            return dest === 0;
        }
        const start = white ? (from >= 8 && from <= 15) : (from >= 48 && from <= 55);
        if (start && to === from + step * 2 && dest === 0)
            return !(0, bitboard_1.testBit)(occ, from + step);
        const pa = white ? attacks_1.WHITE_PAWN_ATTACKS[from] : attacks_1.BLACK_PAWN_ATTACKS[from];
        if (!(0, bitboard_1.testBit)(pa, to))
            return false;
        if (dest)
            return true;
        return board.epSquare === to;
    }
    if (promo)
        return false;
    if (pt === 6 && Math.abs(to - from) === 2 && (from === 4 || from === 60)) {
        const sq = board.squares;
        if (white && from === 4 && to === 6)
            return (board.castling & 1) !== 0 && sq[5] === 0 && sq[6] === 0
                && !board.isAttacked(4, 1) && !board.isAttacked(5, 1) && !board.isAttacked(6, 1);
        if (white && from === 4 && to === 2)
            return (board.castling & 2) !== 0 && sq[1] === 0 && sq[2] === 0 && sq[3] === 0
                && !board.isAttacked(4, 1) && !board.isAttacked(3, 1) && !board.isAttacked(2, 1);
        if (!white && from === 60 && to === 62)
            return (board.castling & 4) !== 0 && sq[61] === 0 && sq[62] === 0
                && !board.isAttacked(60, 0) && !board.isAttacked(61, 0) && !board.isAttacked(62, 0);
        if (!white && from === 60 && to === 58)
            return (board.castling & 8) !== 0 && sq[57] === 0 && sq[58] === 0 && sq[59] === 0
                && !board.isAttacked(60, 0) && !board.isAttacked(59, 0) && !board.isAttacked(58, 0);
        return false;
    }
    let attacks;
    const occ = board.occupied;
    if (pt === 2)
        attacks = attacks_1.KNIGHT_ATTACKS[from];
    else if (pt === 3)
        attacks = (0, attacks_1.bishopAttacks)(from, occ);
    else if (pt === 4)
        attacks = (0, attacks_1.rookAttacks)(from, occ);
    else if (pt === 5)
        attacks = (0, attacks_1.queenAttacks)(from, occ);
    else
        attacks = attacks_1.KING_ATTACKS[from];
    return (0, bitboard_1.testBit)(attacks, to);
}
function cloneMove(m) {
    return { from: m.from, to: m.to, piece: m.piece, captured: m.captured, promo: m.promo, flags: m.flags };
}
const INF = 32000;
const FUTILITY_MARGIN = [0, 100, 200, 300, 400];
const RAZOR_MARGIN = [0, 0, 150, 300, 500];
/** Cooler main-history gravity (STC ACCEPTED strength @100ms 58% vs v1.6). Drop ad-hoc >>=1. */
const MAX_HIST = 8192;
function histUpdate(table, idx, bonus) {
    const b = Math.max(-MAX_HIST, Math.min(MAX_HIST, bonus));
    const v = table[idx] | 0;
    table[idx] = v + b - (((v * Math.abs(b)) / MAX_HIST) | 0);
}
function mainHistBonus(d) {
    // Cooler short-TC: keep bonus modest; malus clearly < bonus.
    return Math.min(180 * d - 90, 1600);
}
function mainHistMalus(d) {
    // ~55% of bonus scale — avoid over-malus under 100ms.
    return Math.min(100 * d - 50, 900);
}
/** Continuation history (1-ply CMH). Index: ((prevPc*64+prevTo)*13+pc)*64+to */
const CMH_SIZE = 13 * 64 * 13 * 64;
const CMH_MAX = 16384;
function cmhIndex(prevPc, prevTo, pc, to) {
    return ((prevPc * 64 + prevTo) * 13 + pc) * 64 + to;
}
function histGravity(table, idx, bonus) {
    const b = Math.max(-CMH_MAX, Math.min(CMH_MAX, bonus | 0));
    const v = table[idx] | 0;
    table[idx] = (v + b - (((v * Math.abs(b)) / CMH_MAX) | 0)) | 0;
}
/** Quadratic CMH gravity (strength ACCEPTED ordering-only @61% vs 1.7.2-nocmh). */
function cmhBonus(d) {
    return Math.min(160 * d * d + 80 * d, 2400);
}
function cmhMalus(d) {
    return Math.min(120 * d * d + 40 * d, 1800);
}
/** Follow-up history (2-ply FUH). Same index shape as CMH; own gravity (not CMH_MAX / main hist). */
const FUH_SIZE = CMH_SIZE;
/** Softer than CMH — first cut FUH_MAX=16384 quad failed 35% vs 1.7.3 */
const FUH_MAX = 8192;
function fuhIndex(prev2Pc, prev2To, pc, to) {
    return cmhIndex(prev2Pc, prev2To, pc, to);
}
function fuhGravity(table, idx, bonus) {
    const b = Math.max(-FUH_MAX, Math.min(FUH_MAX, bonus | 0));
    const v = table[idx] | 0;
    table[idx] = (v + b - (((v * Math.abs(b)) / FUH_MAX) | 0)) | 0;
}
function fuhBonus(d) {
    return Math.min(80 * d * d + 40 * d, 1200);
}
function fuhMalus(d) {
    return Math.min(60 * d * d + 20 * d, 900);
}
/** Capture history for ProbCut ordering only (§8). Not used in quiet ordering or LMR. */
const CAP_SIZE = 13 * 13 * 64;
const CAP_MAX = 8192;
function capIndex(pc, captured, to) {
    return (pc * 13 + captured) * 64 + to;
}
function capGravity(table, idx, bonus) {
    const b = Math.max(-CAP_MAX, Math.min(CAP_MAX, bonus | 0));
    const v = table[idx] | 0;
    table[idx] = (v + b - (((v * Math.abs(b)) / CAP_MAX) | 0)) | 0;
}
/** Smaller than CMH/FUH — ProbCut capture bonus. */
function capBonus(d) {
    return Math.min(40 * d * d + 20 * d, 600);
}
/** Encode a root move for Search.rootMoveNodes lookups. */
function rootMoveKey(m) {
    return m.from | (m.to << 6) | ((m.promo ?? 0) << 12);
}
class Search {
    constructor(board) {
        this.tt = new tt_1.TranspositionTable();
        this.nodes = 0;
        /** Nodes spent under each root move in the current search (all iterations summed).
         *  Key = rootMoveKey(m) = from | to<<6 | promo<<12. Reset at the start of search(). Read-only for callers (timeman). */
        this.rootMoveNodes = new Map();
        this.stop = false;
        this.startTime = 0;
        this.timeLimit = Infinity;
        this.killers = Array.from({ length: MAX_PLY }, () => [null, null]);
        this.history = Array.from({ length: 13 }, () => new Array(64).fill(0));
        this.countermove = new Array(4096).fill(null);
        this.followMove = new Array(4096).fill(null);
        this.contHistory = new Int16Array(CMH_SIZE);
        this.followUpHistory = new Int16Array(FUH_SIZE);
        /** [piece][captured][to] — ProbCut capture ordering only */
        this.capHistory = new Int16Array(CAP_SIZE);
        /** Set during the shallow ProbCut verification search so it cannot nest. */
        this.inProbCut = false;
        this.prevMove = null;
        /** Move from 2 plies ago (same-side previous); keys FUH */
        this.prev2Move = null;
        this.pvTable = Array.from({ length: MAX_PLY }, () => new Array(MAX_PLY));
        this.pvLength = new Array(MAX_PLY).fill(0);
        this.staticAtPly = new Array(MAX_PLY).fill(0);
        this.staticKnown = new Array(MAX_PLY).fill(false);
        this.followPV = false;
        // Reusable move buffers per ply
        this.moveStack = Array.from({ length: MAX_PLY }, () => []);
        this.scoreStack = Array.from({ length: MAX_PLY }, () => []);
        /** SharedArrayBuffer-backed stop flag (Atomics); Lazy SMP cooperative abort */
        this.stopFlag = null;
        /** 0 = main thread; helpers diversify search */
        this.threadId = 0;
        /** Skip root IID (helpers explore different trees) */
        this.skipRootIid = false;
        /** rephist: game position keys before the root (back to last irreversible move), set per job by the worker */
        this.rootHistHi = null;
        this.rootHistLo = null;
        /** Aspiration half-width; helpers use different values */
        this.aspirationWindow = 50;
        /** Seed for history-table noise (0 = none) */
        this.historyNoiseSeed = 0;
        /** At root, rotate ordered quiet moves by this count (helpers) */
        this.rootQuietRotate = 0;
        /** Helpers: on shallow root depths, push TT/PV move later to explore alts */
        this.rootDeferPv = false;
        this.board = board;
    }
    resetHeuristics() {
        for (let i = 0; i < MAX_PLY; i++) {
            this.killers[i][0] = null;
            this.killers[i][1] = null;
        }
        for (let p = 0; p < 13; p++)
            this.history[p].fill(0);
        this.countermove.fill(null);
        this.followMove.fill(null);
        this.contHistory.fill(0);
        this.followUpHistory.fill(0);
        this.capHistory.fill(0);
        this.inProbCut = false;
        this.prevMove = null;
        this.prev2Move = null;
    }
    /**
     * Shared TT only: drop a hit whose best move is not pseudo-legal in this
     * position. Honest entries pass, so fixed-depth node counts stay the same.
     * The local table is returned unchanged.
     */
    acceptSharedTt(entry) {
        if (!entry || !this.tt.isShared || !entry.bestMove)
            return entry;
        // One-move test. Generating the full list here dominated Threads>1 time
        // because every TT hit paid for it. Honest entries still pass.
        if (!sharedMoveOk(this.board, entry.bestMove))
            return null;
        return entry;
    }
    shouldStop() {
        if (this.stop)
            return true;
        if (this.stopFlag && Atomics.load(this.stopFlag, 0) !== 0) {
            this.stop = true;
            return true;
        }
        if ((this.nodes & 4095) === 0) {
            if (this.stopFlag && Atomics.load(this.stopFlag, 0) !== 0) {
                this.stop = true;
                return true;
            }
            if (Date.now() - this.startTime >= this.timeLimit) {
                this.stop = true;
                return true;
            }
        }
        return false;
    }
    /** Root IID: skip if already spent much of a short movetime (IID ate SF samples). */
    allowIidRoot() {
        if (this.skipRootIid)
            return false;
        if (!Number.isFinite(this.timeLimit))
            return true;
        const elapsed = Date.now() - this.startTime;
        if (this.timeLimit < 90)
            return false;
        if (elapsed > this.timeLimit * 0.22)
            return false;
        return true;
    }
    /** Tree/PV IID only when clock has room. */
    allowIidTree() {
        if (!Number.isFinite(this.timeLimit))
            return true;
        const elapsed = Date.now() - this.startTime;
        const remain = this.timeLimit - elapsed;
        if (remain < 45)
            return false;
        if (elapsed > this.timeLimit * 0.55)
            return false;
        return true;
    }
    computeTimeLimit(limits) {
        if (limits.moveTime !== undefined)
            return Math.max(8, limits.moveTime - 8);
        if (limits.infinite)
            return Infinity;
        // Fixed depth without clock: no time cutoff
        if (limits.maxDepth !== undefined && limits.wtime === undefined && limits.btime === undefined && limits.moveTime === undefined) {
            return Infinity;
        }
        const us = this.board.side;
        const time = us === 0 /* Color.White */ ? (limits.wtime ?? 0) : (limits.btime ?? 0);
        const inc = us === 0 /* Color.White */ ? (limits.winc ?? 0) : (limits.binc ?? 0);
        if (time > 0) {
            return Math.max(20, Math.min(time / 25 + inc * 0.7, time * 0.4) - 20);
        }
        return 5000;
    }
    search(limits) {
        this.nodes = 0;
        this.rootMoveNodes.clear();
        this.stop = false;
        // ttkeep: count from the UCI `go` timestamp when provided (same clock as main-thread timers)
        this.startTime = limits.startTime ?? Date.now();
        this.timeLimit = this.computeTimeLimit(limits);
        this.rootAllow = (limits.searchMoves && limits.searchMoves.length) ? limits.searchMoves : null;
        this.tt.prefetchAge();
        this.resetHeuristics();
        if (this.historyNoiseSeed)
            this.seedHistoryNoise(this.historyNoiseSeed);
        const maxDepth = limits.maxDepth ?? 64;
        let bestMove = null;
        let bestScore = 0;
        const ASP = this.aspirationWindow;
        for (let depth = 1; depth <= maxDepth; depth++) {
            this.followPV = true;
            let score;
            let alpha = depth >= 4 ? bestScore - ASP : -INF;
            let beta = depth >= 4 ? bestScore + ASP : INF;
            let delta = ASP;
            while (true) {
                score = this.negamax(0, depth, alpha, beta);
                if (this.stop)
                    break;
                if (score <= alpha) {
                    alpha = Math.max(-INF, alpha - delta);
                    delta *= 2;
                    continue;
                }
                if (score >= beta) {
                    beta = Math.min(INF, beta + delta);
                    delta *= 2;
                    continue;
                }
                break;
            }
            if (this.stop && depth > 1)
                break;
            bestScore = score;
            if (this.pvLength[0] > 0)
                bestMove = this.pvTable[0][0];
            const elapsed = Math.max(1, Date.now() - this.startTime);
            const pv = [];
            for (let i = 0; i < this.pvLength[0]; i++)
                pv.push((0, movegen_1.moveToUci)(this.pvTable[0][i]));
            if (this.onInfo) {
                this.onInfo({
                    depth, nodes: this.nodes, score: bestScore,
                    timeMs: elapsed, pv, nps: Math.floor(this.nodes * 1000 / elapsed),
                });
            }
            // matestop: keep deepening after the first mate score until depth >= mate plies + 4
            if (Math.abs(bestScore) > tt_1.MATE_BOUND && depth >= (tt_1.MATE_SCORE - Math.abs(bestScore)) + 4)
                break;
            if (Number.isFinite(this.timeLimit) && Date.now() - this.startTime > this.timeLimit * 0.90)
                break;
        }
        return bestMove;
    }
    getPvMove(ply) {
        if (!this.followPV)
            return null;
        if (ply >= this.pvLength[0]) {
            this.followPV = false;
            return null;
        }
        return this.pvTable[0][ply];
    }
    negamax(ply, depth, alpha, beta) {
        this.pvLength[ply] = ply;
        if (ply >= MAX_PLY - 1)
            return (0, evaluate_1.evaluate)(this.board);
        this.nodes++;
        if (ply > 0 && this.isRepetition())
            return 0;
        // drawfix: 50-move rule only if the side to move is not checkmated (mate takes precedence)
        if (this.board.halfmove >= 100) {
            if (this.board.inCheck() && (0, movegen_1.generateLegalMoves)(this.board).length === 0)
                return -tt_1.MATE_SCORE + ply;
            return 0;
        }
        alpha = Math.max(alpha, -tt_1.MATE_SCORE + ply);
        beta = Math.min(beta, tt_1.MATE_SCORE - ply - 1);
        if (alpha >= beta)
            return alpha;
        const inCheck = this.board.inCheck();
        const depthOnEntry = depth;
        if (inCheck && ply < 64 && depth <= 6)
            depth++;
        if (depth <= 0)
            return this.quiescence(ply, alpha, beta);
        if (this.shouldStop())
            return 0;
        const isPV = beta - alpha > 1;
        let ttEntry = this.acceptSharedTt(this.tt.probe(this.board.zHi, this.board.zLo));
        let ttMove = null;
        if (ttEntry) {
            ttMove = ttEntry.bestMove;
            if (!isPV && ttEntry.depth >= depth) {
                const ttScore = (0, tt_1.scoreFromTT)(ttEntry.score, ply);
                if (ttEntry.flag === 0 /* TTFlag.Exact */)
                    return ttScore;
                if (ttEntry.flag === 1 /* TTFlag.Lower */ && ttScore >= beta)
                    return ttScore;
                if (ttEntry.flag === 2 /* TTFlag.Upper */ && ttScore <= alpha)
                    return ttScore;
            }
        }
        // Internal iterative deepening: root/PV time-gated (short TC skips root IID)
        if (!ttMove && depth >= 6 && !inCheck && (isPV || ply === 0)) {
            const doIid = ply === 0 ? this.allowIidRoot() : this.allowIidTree();
            if (doIid) {
                this.negamax(ply, depth - 2, alpha, beta);
                if (this.stop)
                    return 0;
                const iid = this.tt.probe(this.board.zHi, this.board.zLo);
                if (iid && iid.bestMove)
                    ttMove = iid.bestMove;
            }
        }
        // prune2: static eval at PV nodes too, so improving is correct two plies below a PV node.
        const staticEval = inCheck ? 0 : (0, evaluate_1.evaluate)(this.board);
        if (!inCheck) {
            this.staticAtPly[ply] = staticEval;
            this.staticKnown[ply] = true;
        }
        else {
            this.staticKnown[ply] = false;
        }
        // tteval: refine the pruning eval by the TT bound (SF search.cpp:862); improving stays on raw staticEval
        let ev = staticEval;
        if (!inCheck && ttEntry) {
            const tts = (0, tt_1.scoreFromTT)(ttEntry.score, ply);
            if (Math.abs(tts) < tt_1.MATE_BOUND && (ttEntry.flag === 0 /* TTFlag.Exact */
                || (ttEntry.flag === 1 /* TTFlag.Lower */ && tts > ev) || (ttEntry.flag === 2 /* TTFlag.Upper */ && tts < ev)))
                ev = tts;
        }
        // Razoring (conservative)
        if (!isPV && !inCheck && depth <= 2 && ev + RAZOR_MARGIN[depth] + 50 < alpha) {
            const razor = this.quiescence(ply, alpha, beta);
            if (razor < alpha - 50)
                return razor;
        }
        // Reverse futility (Forge 6.0.0 search.cpp:680): depth<=8, margin 72*d - 40*improving.
        // improving = eval above eval two plies ago; unknown history counts as improving (Forge :665-670).
        if (!isPV && !inCheck && depth <= 8 && Math.abs(beta) < tt_1.MATE_BOUND && ev < tt_1.MATE_BOUND) {
            const rfpImproving = !(ply >= 2 && this.staticKnown[ply - 2]) || staticEval > this.staticAtPly[ply - 2];
            if (ev - (72 * depth - (rfpImproving ? 40 : 0)) >= beta)
                return ev;
        }
        // Null-move pruning
        if (!isPV && !inCheck && depth >= 3 && ev >= beta && ply > 0) {
            const nonPawn = (0, bitboard_1.popcount)(this.board.occupied)
                - (0, bitboard_1.popcount)(this.board.pieceBB[1 /* Piece.WP */])
                - (0, bitboard_1.popcount)(this.board.pieceBB[7 /* Piece.BP */]);
            // pickerlazy2: no null move for a side with only king (+pawns), as in Forge/Stockfish
            // (non_pawn_material(us)); a bare king's null cutoff returns a cp bound that hides the shortest mate.
            const us = this.board.side;
            const usPieces = (0, bitboard_1.popcount)(this.board.colorBB[us])
                - (0, bitboard_1.popcount)(this.board.pieceBB[us === 0 /* Color.White */ ? 1 /* Piece.WP */ : 7 /* Piece.BP */]);
            // prune2: no two null moves in a row (nullfix-1727 method: top of undoStack is a null move).
            const lastWasNull = this.board.lastMoveIsNull(); // magicflat3: typed undo read, no undoStack rebuild
            if (nonPawn > 2 && usPieces > 1 && !lastWasNull) {
                // prune2: R = 4 + depth/4 + min(3, (staticEval - beta)/200), integer math
                const R = 4 + Math.floor(depth / 4) + Math.min(3, Math.floor((ev - beta) / 200));
                this.board.makeNullMove();
                const score = -this.negamax(ply + 1, depth - 1 - R, -beta, -beta + 1);
                this.board.unmakeNullMove();
                if (this.stop)
                    return 0;
                // Fail-soft NMP (Stockfish-style): return score, not beta, on null-move fail-high
                // prune2: return beta on a null cutoff (never a mate score)
                if (score >= beta)
                    return beta;
            }
        }
        // §8 ProbCut — one depth pair only. Only when side to move is improving.
        // Non-PV, not in check, depth>=5, margin 180, verify at depth-4, <=3 SEE>=0 captures.
        // Shallow search sets inProbCut so ProbCut cannot nest. No check-extension change.
        if (!this.inProbCut && !isPV && !inCheck && depth >= 5
            && Math.abs(beta) < tt_1.MATE_BOUND - 100
            && (ply < 2 || !this.staticKnown[ply] || !this.staticKnown[ply - 2] || staticEval > this.staticAtPly[ply - 2])) {
            const margin = 180;
            const pcBeta = beta + margin;
            const pcDepth = depth - 4;
            let ttBlocks = false;
            if (ttEntry && pcDepth >= 1 && ttEntry.depth >= pcDepth && ttEntry.flag !== 1 /* TTFlag.Lower */) {
                const ts = (0, tt_1.scoreFromTT)(ttEntry.score, ply);
                if (ts < pcBeta)
                    ttBlocks = true;
            }
            if (!ttBlocks && pcDepth >= 1 && pcBeta < tt_1.MATE_BOUND - 50 && ev >= pcBeta) {
                const ranked = [];
                for (const m of (0, movegen_1.generateMoves)(this.board)) {
                    if (m.captured === 0 /* Piece.None */ && m.promo === 0 /* Piece.None */)
                        continue;
                    const see = (0, see_1.seeClassic)(this.board, m.from, m.to, m.promo);
                    if (see < 0)
                        continue;
                    const ch = this.capHistory[capIndex(m.piece, m.captured, m.to)] | 0;
                    ranked.push({ m, s: (ch >> 2) + see });
                }
                ranked.sort((a, b) => b.s - a.s);
                const tries = ranked.length < 3 ? ranked.length : 3;
                for (let i = 0; i < tries; i++) {
                    const m = ranked[i].m;
                    if (!this.board.makeMove(m))
                        continue;
                    const sp = this.prevMove;
                    const sp2 = this.prev2Move;
                    this.prev2Move = sp;
                    this.prevMove = m;
                    this.inProbCut = true;
                    const sc = -this.negamax(ply + 1, pcDepth, -pcBeta, -pcBeta + 1);
                    this.inProbCut = false;
                    this.board.unmakeMove();
                    this.prevMove = sp;
                    this.prev2Move = sp2;
                    if (this.stop)
                        return 0;
                    if (sc >= pcBeta) {
                        capGravity(this.capHistory, capIndex(m.piece, m.captured, m.to), capBonus(depth));
                        return sc;
                    }
                }
            }
        }
        // Singular extension — strict gates (v1.3)
        let seExtend = 0;
        if (!isPV && depth >= 10 && ply > 0 && ttMove && ttEntry
            && ttEntry.depth >= depth - 2
            && ttEntry.flag === 1 /* TTFlag.Lower */
            && Math.abs(ttEntry.score) < tt_1.MATE_BOUND - 100) {
            const ttScore = (0, tt_1.scoreFromTT)(ttEntry.score, ply);
            const singularBeta = ttScore - (2 * depth);
            const reduced = ((depth - 1) >> 1);
            if (reduced >= 1) {
                let seBest = -INF;
                const all = (0, movegen_1.generateMoves)(this.board);
                let tried = 0;
                for (const m of all) {
                    if (this.sameMove(m, ttMove))
                        continue;
                    if (!this.board.makeMove(m))
                        continue;
                    tried++;
                    const sc = -this.negamax(ply + 1, reduced, -singularBeta - 1, -singularBeta);
                    this.board.unmakeMove();
                    if (this.stop)
                        return 0;
                    if (sc > seBest)
                        seBest = sc;
                    if (seBest >= singularBeta)
                        break; // not singular
                }
                if (tried > 0 && seBest < singularBeta)
                    seExtend = 2;
            }
        }
        let moves = (0, movegen_1.generateMoves)(this.board);
        if (ply === 0 && this.rootAllow) {
            const allow = this.rootAllow;
            moves = moves.filter((m) => allow.includes((0, movegen_1.moveToUci)(m)));
        }
        // Ignore a TT move that was not generated. A hit that is already in the
        // list is unchanged, and the depth-9 bench stays on the 1.7.48 node total.
        if (ttMove && !moves.some((m) => this.sameMove(m, ttMove)))
            ttMove = null;
        moves = this.orderMoves(moves, ply, ttMove, depth);
        // TT moves are unpacked without a captured piece; resolve capture-ness from the generated move.
        const ttIsCapture = ttMove !== null && moves.some(mm => this.sameMove(mm, ttMove) && mm.captured !== 0 /* Piece.None */);
        if (ply === 0 && this.rootQuietRotate > 0) {
            moves = this.rotateRootQuiets(moves, this.rootQuietRotate);
        }
        if (ply === 0 && this.rootDeferPv && depth <= 4 && moves.length > 2) {
            // Move leading candidate to index threadId (mod) so helpers widen early
            const defer = 1 + (this.threadId % Math.min(3, moves.length - 1));
            const head = moves[0];
            moves = moves.slice(1);
            moves.splice(Math.min(defer, moves.length), 0, head);
        }
        let bestScore = -INF;
        let bestMove = null;
        let legalCount = 0;
        let quietCount = 0;
        let flag = 2 /* TTFlag.Upper */;
        const quietsSearched = [];
        // Futility pruning threshold
        const canFutility = !isPV && !inCheck && depth <= 4 && Math.abs(alpha) < tt_1.MATE_BOUND;
        // prune2: late-move pruning (non-PV, not in check, depth<=7); never TT/killer/countermove/check-giving.
        // Skip LMP when the opponent has only king+pawns (mating nets need quiet non-checks).
        const themBB = this.board.colorBB[this.board.side ^ 1];
        const themPawns = this.board.pieceBB[this.board.side === 0 ? 7 /* Piece.BP */ : 1 /* Piece.WP */];
        const canLmp = !isPV && !inCheck && depth <= 7 && ply > 0 && (0, bitboard_1.popcount)(themBB) - (0, bitboard_1.popcount)(themPawns) > 1;
        const lmpImproving = !(ply >= 2 && this.staticKnown[ply - 2]) || staticEval > this.staticAtPly[ply - 2];
        const lmpLimit = Math.floor((3 + depth * depth) / (lmpImproving ? 1 : 2));
        const lmpCm = this.prevMove ? this.countermove[this.prevMove.from * 64 + this.prevMove.to] : null;
        for (let i = 0; i < moves.length; i++) {
            const m = moves[i];
            // SEE pruning of clearly bad captures (skip first 2 captures for safety)
            if (!isPV && !inCheck && m.captured !== 0 /* Piece.None */ && depth <= 3 && m.promo === 0 /* Piece.None */ && legalCount >= 2) {
                const see = m.see !== undefined ? m.see : (0, see_1.seeClassic)(this.board, m.from, m.to);
                if (see < -100 * depth)
                    continue;
            }
            // Futility: skip late quiet moves that can't raise alpha
            if (canFutility && m.captured === 0 /* Piece.None */ && m.promo === 0 /* Piece.None */ && legalCount > 3) {
                if (ev + FUTILITY_MARGIN[Math.min(depth, 3)] <= alpha) {
                    quietCount++;
                    if (quietCount > 4 + depth * depth)
                        continue;
                }
            }
            // Tight recapture: SEE>=0, previous move was a capture, same to-square,
            // depth on entry <=4, and this node was not check-extended. Singular wins if both apply.
            let recaptureExt = 0;
            if (depthOnEntry <= 2
                && !(inCheck && ply < 64 && depthOnEntry <= 6)
                && m.captured !== 0 /* Piece.None */
                && this.prevMove
                && this.prevMove.captured !== 0 /* Piece.None */
                && m.to === this.prevMove.to
                && (0, see_1.seeClassic)(this.board, m.from, m.to, m.promo) >= 0)
                recaptureExt = 1;
            if (GC_DEBUG && m.captured === 0 /* Piece.None */ && m.promo === 0 /* Piece.None */ && !(m.flags & types_2.MOVE_CASTLE)) {
                const gc = (0, givescheck_1.givesCheckQuiet)(this.board, m);
                if (this.board.makeMove(m)) {
                    exports.gcDebugStats.checked++;
                    if (gc !== this.board.inCheck()) {
                        exports.gcDebugStats.mismatches++;
                        process.stderr.write(`GC_MISMATCH ${this.board.getFen()} ${m.from}-${m.to}\n`);
                    }
                    this.board.unmakeMove();
                }
            }
            // prune2fast: LMP decision before makeMove (identical result: illegal and pruned moves are both skipped).
            let made = false;
            if (canLmp && bestMove !== null && Math.abs(bestScore) < tt_1.MATE_BOUND
                && m.captured === 0 /* Piece.None */ && m.promo === 0 /* Piece.None */
                && quietsSearched.length >= lmpLimit
                && !(ttMove && this.sameMove(m, ttMove))
                && !(this.killers[ply][0] && this.sameMove(m, this.killers[ply][0]))
                && !(this.killers[ply][1] && this.sameMove(m, this.killers[ply][1]))
                && !(lmpCm && this.sameMove(m, lmpCm))) {
                if (!(m.flags & types_2.MOVE_CASTLE)) {
                    if (!(0, givescheck_1.givesCheckQuiet)(this.board, m))
                        continue;
                }
                else {
                    // castling: fall back to make + inCheck
                    if (!this.board.makeMove(m))
                        continue;
                    if (!this.board.inCheck()) {
                        this.board.unmakeMove();
                        continue;
                    }
                    made = true;
                }
            }
            if (!made && !this.board.makeMove(m))
                continue;
            legalCount++;
            const rootNodes0 = this.nodes;
            const savedPrev = this.prevMove;
            const savedPrev2 = this.prev2Move;
            this.prev2Move = savedPrev;
            this.prevMove = m;
            const isQuiet = m.captured === 0 /* Piece.None */ && m.promo === 0 /* Piece.None */;
            let score;
            // LMR (countermove keyed by parent = savedPrev, not current m)
            if (depth >= 3 && legalCount > (isPV ? 4 : 2) && isQuiet && !inCheck && !this.board.inCheck()) {
                let R = 1 + Math.floor(Math.log(depth) * Math.log(legalCount) / 2.47);
                const isKiller = (this.killers[ply][0] && this.sameMove(m, this.killers[ply][0]))
                    || (this.killers[ply][1] && this.sameMove(m, this.killers[ply][1]));
                const cm = savedPrev ? this.countermove[savedPrev.from * 64 + savedPrev.to] : null;
                const fu = savedPrev2 ? this.followMove[savedPrev2.from * 64 + savedPrev2.to] : null;
                if (isKiller || (cm && this.sameMove(m, cm)) || (fu && this.sameMove(m, fu)))
                    R = Math.max(1, R - 1);
                if (ply >= 2 && this.staticKnown[ply] && this.staticKnown[ply - 2] && staticEval <= this.staticAtPly[ply - 2]) {
                    R = R + 1;
                }
                // No histScore/CMH/FUH in LMR (ordering-only SPRTs)
                if (ttIsCapture)
                    R = R + 1;
                if (ttEntry && ttEntry.flag === 1 /* TTFlag.Lower */)
                    R = R + 1;
                if (isPV)
                    R -= 1;
                if (R < 1)
                    R = 1;
                if (R > depth - 2)
                    R = Math.max(1, depth - 2);
                score = -this.negamax(ply + 1, depth - 1 - R + recaptureExt, -alpha - 1, -alpha);
                if (score > alpha && R > 0) {
                    score = -this.negamax(ply + 1, depth - 1 + recaptureExt, -alpha - 1, -alpha);
                }
                if (score > alpha && score < beta) {
                    score = -this.negamax(ply + 1, depth - 1 + recaptureExt, -beta, -alpha);
                }
            }
            else {
                const singularHere = (legalCount === 1 && seExtend && ttMove && this.sameMove(m, ttMove)) ? seExtend : 0;
                const newDepth = depth - 1 + (singularHere ? singularHere : recaptureExt);
                if (!isPV || legalCount > 1) {
                    score = -this.negamax(ply + 1, newDepth, -alpha - 1, -alpha);
                    if (score > alpha && score < beta) {
                        score = -this.negamax(ply + 1, newDepth, -beta, -alpha);
                    }
                }
                else {
                    score = -this.negamax(ply + 1, newDepth, -beta, -alpha);
                }
            }
            this.board.unmakeMove();
            this.prevMove = savedPrev;
            this.prev2Move = savedPrev2;
            if (ply === 0) {
                const k = rootMoveKey(m);
                this.rootMoveNodes.set(k, (this.rootMoveNodes.get(k) ?? 0) + (this.nodes - rootNodes0));
            }
            if (this.stop)
                return 0;
            if (isQuiet)
                quietsSearched.push(m);
            if (score > bestScore) {
                bestScore = score;
                bestMove = m;
                this.pvTable[ply][ply] = cloneMove(m);
                for (let j = ply + 1; j < this.pvLength[ply + 1]; j++) {
                    this.pvTable[ply][j] = this.pvTable[ply + 1][j];
                }
                this.pvLength[ply] = this.pvLength[ply + 1];
                if (score > alpha) {
                    alpha = score;
                    flag = 0 /* TTFlag.Exact */;
                    if (score >= beta) {
                        flag = 1 /* TTFlag.Lower */;
                        // ProbCut capHistory: smaller bonus on ordinary capture cutoffs (not quiets, not LMR).
                        if (m.captured !== 0 /* Piece.None */ || m.promo !== 0 /* Piece.None */) {
                            capGravity(this.capHistory, capIndex(m.piece, m.captured, m.to), capBonus(depth) >> 1);
                        }
                        if (isQuiet) {
                            if (!this.sameMove(m, this.killers[ply][0])) {
                                this.killers[ply][1] = this.killers[ply][0];
                                this.killers[ply][0] = cloneMove(m);
                            }
                            if (savedPrev) {
                                this.countermove[savedPrev.from * 64 + savedPrev.to] = cloneMove(m);
                            }
                            if (savedPrev2) {
                                this.followMove[savedPrev2.from * 64 + savedPrev2.to] = cloneMove(m);
                            }
                            // Cooler main-history gravity: bonus best quiet, malus prior quiets
                            {
                                const bonus = mainHistBonus(depth);
                                const malus = mainHistMalus(depth);
                                histUpdate(this.history[m.piece], m.to, bonus);
                                for (const q of quietsSearched) {
                                    if (q.from === m.from && q.to === m.to && q.promo === m.promo)
                                        continue;
                                    histUpdate(this.history[q.piece], q.to, -malus);
                                }
                            }
                            // CMH quadratic gravity (ordering-only; no LMR histScore)
                            if (savedPrev) {
                                const cb = cmhBonus(depth);
                                const cm = cmhMalus(depth);
                                histGravity(this.contHistory, cmhIndex(savedPrev.piece, savedPrev.to, m.piece, m.to), cb);
                                for (const q of quietsSearched) {
                                    if (q.from === m.from && q.to === m.to && q.promo === m.promo)
                                        continue;
                                    histGravity(this.contHistory, cmhIndex(savedPrev.piece, savedPrev.to, q.piece, q.to), -cm);
                                }
                            }
                            // FUH ordering-only: own FUH_MAX gravity keyed by prev2Move (savedPrev2)
                            if (savedPrev2) {
                                const fb = fuhBonus(depth);
                                const fm = fuhMalus(depth);
                                fuhGravity(this.followUpHistory, fuhIndex(savedPrev2.piece, savedPrev2.to, m.piece, m.to), fb);
                                for (const q of quietsSearched) {
                                    if (q.from === m.from && q.to === m.to && q.promo === m.promo)
                                        continue;
                                    fuhGravity(this.followUpHistory, fuhIndex(savedPrev2.piece, savedPrev2.to, q.piece, q.to), -fm);
                                }
                            }
                        }
                        break;
                    }
                }
            }
        }
        if (legalCount === 0) {
            return inCheck ? -tt_1.MATE_SCORE + ply : 0;
        }
        this.tt.store(this.board.zHi, this.board.zLo, depth, (0, tt_1.scoreToTT)(bestScore, ply), flag, bestMove ? cloneMove(bestMove) : null);
        return bestScore;
    }
    quiescence(ply, alpha, beta) {
        this.nodes++;
        if (this.shouldStop())
            return 0;
        if (ply >= MAX_PLY - 1)
            return (0, evaluate_1.evaluate)(this.board);
        // Probe-only TT: reuse deeper search bounds; never store from qsearch
        const ttQ = this.acceptSharedTt(this.tt.probe(this.board.zHi, this.board.zLo));
        if (ttQ && ttQ.depth >= 1) {
            const ttScore = (0, tt_1.scoreFromTT)(ttQ.score, ply);
            if (ttQ.flag === 0 /* TTFlag.Exact */)
                return ttScore;
            if (ttQ.flag === 1 /* TTFlag.Lower */ && ttScore >= beta)
                return ttScore;
            if (ttQ.flag === 2 /* TTFlag.Upper */ && ttScore <= alpha)
                return ttScore;
        }
        const inCheck = this.board.inCheck();
        let standPat = 0;
        if (!inCheck) {
            standPat = (0, evaluate_1.evaluate)(this.board);
            if (standPat >= beta)
                return standPat; // fail-soft
            if (standPat > alpha)
                alpha = standPat;
        }
        const moves = inCheck ? (0, movegen_1.generateMoves)(this.board) : (0, movegen_1.generateMoves)(this.board, true);
        const ordered = this.orderCaptures(moves, ply);
        let legalCount = 0;
        for (const m of ordered) {
            if (!inCheck && m.captured !== 0 /* Piece.None */) {
                const gain = types_1.PIECE_VALUES[m.captured] + (m.promo !== 0 /* Piece.None */ ? 800 : 0);
                if (standPat + gain + 180 < alpha)
                    continue;
                if (m.promo === 0 /* Piece.None */
                    && types_1.PIECE_VALUES[this.board.squares[m.to]] < types_1.PIECE_VALUES[m.piece]
                    && (0, see_1.seeClassic)(this.board, m.from, m.to) < 0)
                    continue;
            }
            if (!this.board.makeMove(m))
                continue;
            legalCount++;
            const score = -this.quiescence(ply + 1, -beta, -alpha);
            this.board.unmakeMove();
            if (this.stop)
                return 0;
            if (score >= beta)
                return score; // fail-soft
            if (score > alpha)
                alpha = score;
        }
        if (inCheck && legalCount === 0)
            return -tt_1.MATE_SCORE + ply;
        return alpha;
    }
    orderMoves(moves, ply, ttMove, depth) {
        const n = moves.length;
        const scores = this.scoreStack[ply];
        while (scores.length < n)
            scores.push(0);
        const pvMove = this.getPvMove(ply);
        // orderfast: hoist loop invariants; identical scores to the lock's per-move expression.
        const pvF = pvMove ? pvMove.from : -1, pvT = pvMove ? pvMove.to : -1, pvP = pvMove ? pvMove.promo : -1;
        const ttF = ttMove ? ttMove.from : -1, ttT = ttMove ? ttMove.to : -1, ttP = ttMove ? ttMove.promo : -1;
        const kl = this.killers[ply];
        const k0 = kl[0], k1 = kl[1];
        const k0F = k0 ? k0.from : -1, k0T = k0 ? k0.to : -1, k0P = k0 ? k0.promo : -1;
        const k1F = k1 ? k1.from : -1, k1T = k1 ? k1.to : -1, k1P = k1 ? k1.promo : -1;
        const prev = this.prevMove, prev2 = this.prev2Move;
        const cm = prev ? this.countermove[prev.from * 64 + prev.to] : null;
        const cmF = cm ? cm.from : -1, cmT = cm ? cm.to : -1, cmP = cm ? cm.promo : -1;
        const fu = prev2 ? this.followMove[prev2.from * 64 + prev2.to] : null;
        const fuF = fu ? fu.from : -1, fuT = fu ? fu.to : -1, fuP = fu ? fu.promo : -1;
        const cmhBase = prev ? (prev.piece * 64 + prev.to) * 13 * 64 : 0;
        const fuhBase = prev2 ? (prev2.piece * 64 + prev2.to) * 13 * 64 : 0;
        const cont = this.contHistory, fuh = this.followUpHistory, hist = this.history;
        const board = this.board;
        for (let i = 0; i < n; i++) {
            const m = moves[i];
            const f = m.from, t = m.to, pr = m.promo;
            let s = 0;
            if (f === pvF && t === pvT && pr === pvP)
                s = 2000000;
            else if (f === ttF && t === ttT && pr === ttP)
                s = 1500000;
            else if (m.captured !== 0 /* Piece.None */) {
                s = 1000000 + types_1.PIECE_VALUES[m.captured] * 16 - types_1.PIECE_VALUES[m.piece];
                if (pr === 0 /* Piece.None */) {
                    const see = (0, see_1.seeClassic)(board, f, t);
                    m.see = see;
                    s += see;
                    // badcap: SEE<0 captures go after killers/countermove/quiets (Forge-style bad-capture stage)
                    if (see < 0)
                        s -= 3000000;
                }
            }
            else if (pr !== 0 /* Piece.None */) {
                s = 900000 + types_1.PIECE_VALUES[pr];
            }
            else if (f === k0F && t === k0T && pr === k0P)
                s = 800000;
            else if (f === k1F && t === k1T && pr === k1P)
                s = 700000;
            else if (f === cmF && t === cmT && pr === cmP)
                s = 650000;
            else if (f === fuF && t === fuT && pr === fuP)
                s = 640000;
            else {
                const pc = m.piece;
                s = hist[pc][t];
                if (prev)
                    s += cont[cmhBase + pc * 64 + t];
                if (prev2)
                    s += fuh[fuhBase + pc * 64 + t] >> 1;
            }
            scores[i] = s;
        }
        // Insertion sort by score descending (in-place on moves)
        for (let i = 1; i < n; i++) {
            const m = moves[i], sc = scores[i];
            let j = i - 1;
            while (j >= 0 && scores[j] < sc) {
                moves[j + 1] = moves[j];
                scores[j + 1] = scores[j];
                j--;
            }
            moves[j + 1] = m;
            scores[j + 1] = sc;
        }
        return moves;
    }
    orderCaptures(moves, ply = 0) {
        const n = moves.length;
        const scores = this.scoreStack[ply];
        while (scores.length < n)
            scores.push(0);
        for (let i = 0; i < n; i++) {
            const m = moves[i];
            let s = 0;
            if (m.captured !== 0 /* Piece.None */) {
                s = 1000000 + types_1.PIECE_VALUES[m.captured] * 16 - types_1.PIECE_VALUES[m.piece];
            }
            if (m.promo !== 0 /* Piece.None */)
                s += 900000 + types_1.PIECE_VALUES[m.promo];
            scores[i] = s;
        }
        for (let i = 1; i < n; i++) {
            const m = moves[i], sc = scores[i];
            let j = i - 1;
            while (j >= 0 && scores[j] < sc) {
                moves[j + 1] = moves[j];
                scores[j + 1] = scores[j];
                j--;
            }
            moves[j + 1] = m;
            scores[j + 1] = sc;
        }
        return moves;
    }
    /** Sprinkle low-amplitude history so helpers order quiet moves differently. */
    seedHistoryNoise(seed) {
        let s = seed | 0;
        for (let p = 1; p < 13; p++) {
            for (let sq = 0; sq < 64; sq++) {
                s = (Math.imul(s, 1664525) + 1013904223) | 0;
                this.history[p][sq] = (s & 0xff) - 128; // -128..127
            }
        }
    }
    /**
     * Rotate non-capture/non-promo moves after the first few forced slots so
     * helpers try different root candidates early (Lazy SMP diversification).
     */
    rotateRootQuiets(moves, rot) {
        if (rot <= 0 || moves.length < 4)
            return moves;
        // Preserve leading TT/PV/captures (scores already ordered); rotate among quiet tail
        let firstQuiet = 0;
        while (firstQuiet < moves.length) {
            const m = moves[firstQuiet];
            if (m.captured === 0 /* Piece.None */ && m.promo === 0 /* Piece.None */)
                break;
            firstQuiet++;
        }
        // Keep one quiet at front for stability; rotate the rest
        const head = moves.slice(0, Math.min(firstQuiet + 1, moves.length));
        const tail = moves.slice(head.length);
        if (tail.length < 2)
            return moves;
        const r = rot % tail.length;
        return head.concat(tail.slice(r), tail.slice(0, r));
    }
    sameMove(a, b) {
        if (!a || !b)
            return false;
        return a.from === b.from && a.to === b.to && a.promo === b.promo;
    }
    isRepetition() {
        // g4g1g5+rephist3: in-tree scan via typed undo (board.isRepetitionKey); then true 3-fold via rootHist.
        // isRepetitionKey returns false on irreversible-in-tree OR no match; either way rootHist is safe
        // (irreversible changes material/pawns so current key cannot match pre-root hist).
        const hi = this.board.zHi, lo = this.board.zLo;
        if (this.board.isRepetitionKey(hi, lo))
            return true;
        // rephist3 (Stockfish rule): no in-tree repeat -> pre-root game position is draw only at true 3-fold.
        const rh = this.rootHistHi, rl = this.rootHistLo;
        if (rh && rl) {
            let cnt = 0;
            for (let i = 0; i < rh.length; i++)
                if (rh[i] === hi && rl[i] === lo && ++cnt >= 2)
                    return true;
        }
        return false;
    }
}
exports.Search = Search;
//# sourceMappingURL=search.js.map
