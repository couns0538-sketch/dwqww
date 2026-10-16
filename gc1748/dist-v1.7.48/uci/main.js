#!/usr/bin/env node
"use strict";
/** UCI protocol interface */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const readline = __importStar(require("readline"));
const board_1 = require("../board/board");
const smp_1 = require("../search/smp");
const movegen_1 = require("../move/movegen");
const nnue_1 = require("../eval/nnue");
const evaluate_1 = require("../eval/evaluate");
const tt_1 = require("../search/tt");
const timeman_1 = require("../search/timeman");
const ENGINE_NAME = 'GrokChess';
const ENGINE_AUTHOR = 'Couns / Grok';
const board = new board_1.Board();
let searcher = null;
let threads = 1;
let nnueUse = process.env.GROKCHESS_USE_NNUE !== '0';
let moveOverhead = 30;
let searching = false;
let stopPending = false; // 'stop' that arrives after 'go' but before the async search has started (GUI race)
let pondering = false;
let liveSoft = null;
let liveHard = null;
let liveGoStart = 0;
let savedClock = null;
/** Set while a finished ponder or infinite search is waiting to print bestmove. */
let bestmoveGate = null;
let deferredNewGame = false;
let deferredHashMb = null;
/** `position` that arrived while a search owned the root board. */
let deferredPosition = null;
function applyPosition(parts) {
    let idx = 1;
    if (parts[idx] === 'startpos') {
        board.setFen(board_1.START_FEN);
        idx++;
    }
    else if (parts[idx] === 'fen') {
        idx++;
        const fenParts = [];
        while (idx < parts.length && parts[idx] !== 'moves') {
            fenParts.push(parts[idx++]);
        }
        board.setFen(fenParts.join(' '));
    }
    if (parts[idx] === 'moves') {
        idx++;
        while (idx < parts.length) {
            const uci = parts[idx];
            const m = (0, movegen_1.parseUciMove)(board, uci);
            if (m)
                board.makeMove(m);
            else {
                send(`info string warning: ignored illegal move ${uci} (stopping move list)`);
                break;
            }
            idx++;
        }
    }
}
function clearTablesWhenIdle() {
    (0, smp_1.afterWorkersIdle)(() => {
        (0, smp_1.clearSharedTT)();
        (0, smp_1.clearWorkerTTs)();
    });
}
function releaseBestmove() {
    if (!bestmoveGate)
        return;
    const gate = bestmoveGate;
    bestmoveGate = null;
    gate();
}
const GO_WORDS = new Set(['searchmoves', 'ponder', 'depth', 'movetime', 'wtime', 'btime', 'winc', 'binc', 'movestogo', 'infinite', 'perft', 'nodes', 'mate']);
function exitProcess() {
    pondering = false;
    releaseBestmove();
    (0, smp_1.abortSmpSearch)();
    const kill = setTimeout(() => process.exit(0), 400);
    (0, smp_1.shutdownPool)().finally(() => { clearTimeout(kill); process.exit(0); });
}
function armClock(clock) {
    if (liveHard) {
        clearTimeout(liveHard);
        liveHard = null;
    }
    const white = board.side === 0;
    const budget = (0, timeman_1.computeBudget)({
        time: white ? clock.wtime : clock.btime,
        inc: white ? clock.winc : clock.binc,
        movestogo: clock.movestogo,
        moveOverhead,
    });
    liveSoft = new timeman_1.SoftController(budget);
    liveHard = setTimeout(smp_1.abortSmpSearch, budget.hard);
}
function scoreString(score) {
    if (Math.abs(score) > tt_1.MATE_BOUND) {
        const mateIn = score > 0
            ? Math.ceil((30000 - score) / 2)
            : -Math.ceil((30000 + score) / 2);
        return `mate ${mateIn}`;
    }
    return `cp ${score}`;
}
function send(s) {
    process.stdout.write(s + '\n');
}
function handle(line) {
    const cmd = line.trim();
    if (!cmd)
        return;
    const parts = cmd.split(/\s+/);
    const name = parts[0];
    switch (name) {
        case 'uci':
            send(`id name ${ENGINE_NAME}`);
            send(`id author ${ENGINE_AUTHOR}`);
            send('option name Hash type spin default 64 min 1 max 1024');
            send('option name Threads type spin default 1 min 1 max 8');
            send('option name MoveOverhead type spin default 30 min 0 max 5000');
            send(`option name UseNNUE type check default ${nnueUse}`);
            send(`option name EvalFile type string default ${nnue_1.resolvedDefaultPath}`);
            send('uciok');
            break;
        case 'isready':
            // Warm helper pool so short movetimes are not eaten by cold spawn
            (0, smp_1.ensurePool)(threads).then(() => send('readyok')).catch(() => send('readyok'));
            break;
        case 'ucinewgame':
            // The root board is reset now only when no search is validating a move.
            // The shared table is cleared after helpers leave that search, so a
            // tail write cannot refill a table the next game thinks is empty.
            if (searching) {
                deferredNewGame = true;
                break;
            }
            board.setFen(board_1.START_FEN);
            if (searcher)
                searcher.tt.clear();
            clearTablesWhenIdle();
            break;
        case 'position': {
            if (searching) {
                deferredPosition = parts;
                break;
            }
            applyPosition(parts);
            break;
        }
        case 'go': {
            if (searching) {
                send('info string warning: ignored go (search already in progress; send stop first)');
                break;
            }
            const limits = {};
            let movestogo;
            for (let i = 1; i < parts.length; i++) {
                switch (parts[i]) {
                    case 'searchmoves':
                        limits.searchMoves = [];
                        while (i + 1 < parts.length && !GO_WORDS.has(parts[i + 1]))
                            limits.searchMoves.push(parts[++i]);
                        break;
                    case 'ponder':
                        limits.ponder = true;
                        break;
                    case 'depth':
                        limits.maxDepth = parseInt(parts[++i], 10);
                        break;
                    case 'movetime':
                        limits.moveTime = parseInt(parts[++i], 10);
                        break;
                    case 'wtime':
                        limits.wtime = parseInt(parts[++i], 10);
                        break;
                    case 'btime':
                        limits.btime = parseInt(parts[++i], 10);
                        break;
                    case 'winc':
                        limits.winc = parseInt(parts[++i], 10);
                        break;
                    case 'binc':
                        limits.binc = parseInt(parts[++i], 10);
                        break;
                    case 'movestogo':
                        movestogo = parseInt(parts[++i], 10);
                        break;
                    case 'infinite':
                        limits.infinite = true;
                        break;
                    case 'perft': {
                        const d = parseInt(parts[++i], 10);
                        const start = Date.now();
                        const nodes = (0, movegen_1.perft)(board, d);
                        send(`info string perft(${d}) = ${nodes} time ${Date.now() - start}ms`);
                        return;
                    }
                }
            }
            if (limits.ponder)
                limits.infinite = true;
            if (limits.maxDepth === undefined && limits.moveTime === undefined && limits.wtime === undefined && limits.btime === undefined && !limits.infinite) {
                limits.moveTime = 3000;
            }
            // Time management v2: turn the clock into a hard deadline (stop-flag timer) + soft per-iteration limit.
            if (liveHard) {
                clearTimeout(liveHard);
                liveHard = null;
            }
            liveSoft = null;
            pondering = !!limits.ponder;
            savedClock = {
                wtime: limits.wtime, btime: limits.btime, winc: limits.winc, binc: limits.binc, movestogo,
            };
            let searchLimits = limits;
            let armTimer = null;
            if (limits.ponder) {
                searchLimits = { maxDepth: limits.maxDepth, searchMoves: limits.searchMoves, infinite: true };
            }
            else if (limits.moveTime !== undefined) {
                // explicit movetime: honour it minus overhead beyond what search.ts already subtracts (8 ms)
                const mt = Math.max(10, limits.moveTime - Math.max(0, moveOverhead - 8));
                searchLimits = { ...limits, moveTime: mt };
                armTimer = () => { liveHard = setTimeout(smp_1.abortSmpSearch, Math.max(5, mt - 8)); };
            }
            else if (!limits.infinite && (limits.wtime !== undefined || limits.btime !== undefined)) {
                const white = board.side === 0;
                const t = white ? limits.wtime : limits.btime;
                const inc = white ? limits.winc : limits.binc;
                const budget = (0, timeman_1.computeBudget)({ time: t, inc, movestogo, moveOverhead });
                // search-internal limit is a backstop slightly behind the timer-driven stop
                searchLimits = { maxDepth: limits.maxDepth, searchMoves: limits.searchMoves, moveTime: budget.hard + 8 + 30 };
                armTimer = () => {
                    liveSoft = new timeman_1.SoftController(budget);
                    liveHard = setTimeout(smp_1.abortSmpSearch, budget.hard);
                };
            }
            searching = true;
            stopPending = false;
            setImmediate(async () => {
                try {
                    // Finish the previous helpers' tail and any deferred table clear
                    // before the clock starts, so Hash/ucinewgame work is not time-loss.
                    await (0, smp_1.prepareWorkers)();
                    if (stopPending) {
                        searchLimits = { maxDepth: 1, searchMoves: limits.searchMoves };
                        liveSoft = null;
                        pondering = false;
                    }
                    else if (armTimer)
                        armTimer();
                    liveGoStart = Date.now();
                    searchLimits = { ...searchLimits, startTime: liveGoStart };
                    const result = await (0, smp_1.searchLazySmp)(board, searchLimits, threads, (info) => {
                        if (liveSoft && info.pv.length > 0 && liveSoft.onIteration(info.depth, info.score, info.pv[0], Date.now() - liveGoStart, info.bestFrac))
                            (0, smp_1.abortSmpSearch)();
                        const scoreStr = scoreString(info.score);
                        send(`info depth ${info.depth} score ${scoreStr} nodes ${info.nodes} nps ${info.nps} time ${info.timeMs} pv ${info.pv.join(' ')}`);
                    });
                    searcher = null;
                    // Ponder that finishes on its own, and infinite that hits max depth,
                    // must not print bestmove until stop or ponderhit. A clock after
                    // ponderhit (liveSoft) is a normal timed search and is not held.
                    if (!stopPending && !liveSoft && (pondering || (limits.infinite && !limits.ponder))) {
                        await new Promise((resolve) => { bestmoveGate = resolve; });
                    }
                    pondering = false;
                    const pv0 = result.pv && result.pv[0];
                    let best = (pv0 && (0, movegen_1.parseUciMove)(board, pv0)) || result.best;
                    if (best && limits.searchMoves && limits.searchMoves.length && !limits.searchMoves.includes((0, movegen_1.moveToUci)(best)))
                        best = null;
                    if (best)
                        send(`bestmove ${(0, movegen_1.moveToUci)(best)}`);
                    else {
                        const legal = (0, movegen_1.generateLegalMoves)(board).filter((m) => !limits.searchMoves || !limits.searchMoves.length || limits.searchMoves.includes((0, movegen_1.moveToUci)(m)));
                        if (legal.length)
                            send(`bestmove ${(0, movegen_1.moveToUci)(legal[0])}`);
                        else
                            send('bestmove 0000');
                    }
                }
                finally {
                    if (liveHard) {
                        clearTimeout(liveHard);
                        liveHard = null;
                    }
                    liveSoft = null;
                    searching = false;
                    pondering = false;
                    const ng = deferredNewGame;
                    const pos = deferredPosition;
                    const hash = deferredHashMb;
                    deferredNewGame = false;
                    deferredPosition = null;
                    deferredHashMb = null;
                    if (ng) {
                        board.setFen(board_1.START_FEN);
                        if (searcher)
                            searcher.tt.clear();
                    }
                    if (pos)
                        applyPosition(pos);
                    if (ng)
                        clearTablesWhenIdle();
                    if (hash !== null)
                        (0, smp_1.afterWorkersIdle)(() => (0, smp_1.setHashMb)(hash));
                }
            });
            break;
        }
        case 'stop':
            if (searching)
                stopPending = true;
            pondering = false;
            (0, smp_1.abortSmpSearch)();
            if (searcher)
                searcher.stop = true;
            releaseBestmove();
            break;
        case 'ponderhit':
            if (pondering && searching && savedClock && (savedClock.wtime !== undefined || savedClock.btime !== undefined)) {
                pondering = false;
                liveGoStart = Date.now();
                armClock(savedClock);
            }
            else if (pondering && searching) {
                // No clock on the original go: the pondered move is due now.
                pondering = false;
                stopPending = true;
                (0, smp_1.abortSmpSearch)();
            }
            else
                pondering = false;
            releaseBestmove();
            break;
        case 'quit':
            exitProcess();
            break;
        case 'setoption': {
            // setoption name Threads value N
            const ni = parts.indexOf('name');
            const vi = parts.indexOf('value');
            if (ni >= 0 && vi >= 0) {
                const opt = parts[ni + 1];
                const val = parts[vi + 1];
                if (opt === 'MoveOverhead') {
                    moveOverhead = Math.max(0, Math.min(5000, parseInt(val, 10) || 0));
                }
                else if (opt === 'UseNNUE') {
                    const on = String(val).toLowerCase() === 'true';
                    const changed = on !== nnueUse;
                    nnueUse = on;
                    (0, nnue_1.setUseNNUE)(on);
                    process.env.GROKCHESS_USE_NNUE = on ? '1' : '0';
                    (0, smp_1.afterWorkersIdle)(() => {
                        (0, smp_1.setPoolNNUE)(on, null);
                        if (changed) {
                            (0, smp_1.clearSharedTT)();
                            (0, smp_1.clearWorkerTTs)();
                        }
                    });
                    send(`info string ${(0, nnue_1.nnueInfo)()}`);
                }
                else if (opt === 'EvalFile') {
                    const f = vi >= 0 ? parts.slice(vi + 1).join(' ').trim() : '';
                    if (f === '' || f === '<empty>') {
                        send(`info string EvalFile empty: no change. ${(0, nnue_1.nnueInfo)()}`);
                    }
                    else if (!(0, nnue_1.loadNet)(f)) {
                        send(`info string ERROR EvalFile load FAILED for ${f} (${(0, nnue_1.nnueInfo)()}); keeping previous net`);
                    }
                    else {
                        process.env.GROKCHESS_NNUE = f;
                        (0, smp_1.afterWorkersIdle)(() => {
                            (0, smp_1.setPoolNNUE)(nnueUse, f);
                            (0, smp_1.clearSharedTT)();
                            (0, smp_1.clearWorkerTTs)();
                        });
                        send(`info string ${(0, nnue_1.nnueInfo)()}`);
                    }
                }
                else if (opt === 'Hash') {
                    // hashmb: Hash now actually sizes the TT (was ignored; workers always used 1<<22)
                    // Applying it mid-search swaps the shared buffer under live probes.
                    const mb = parseInt(val, 10) || 64;
                    if (searching)
                        deferredHashMb = mb;
                    else
                        (0, smp_1.afterWorkersIdle)(() => (0, smp_1.setHashMb)(mb));
                }
                else if (opt === 'Threads') {
                    threads = Math.max(1, Math.min(8, parseInt(val, 10) || 1));
                    void (0, smp_1.ensurePool)(threads);
                }
            }
            break;
        }
        case 'eval':
            send(`info string eval ${(0, evaluate_1.evaluate)(board)} fen ${board.getFen()}`);
            break;
        case 'nnueinfo':
            send(`info string main: ${(0, nnue_1.nnueInfo)()}`);
            (0, smp_1.queryPoolNNUE)().then((xs) => { for (const x of xs)
                send(`info string ${x}`); });
            break;
        case 'd':
            send(board.toString());
            break;
        default:
            break;
    }
}
const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });
rl.on('line', handle);
// eofexit-1744: stdin EOF (GUI closed pipe) — stop search, shutdown workers, exit (same as quit)
rl.on('close', () => {
    if (searching)
        stopPending = true;
    if (searcher)
        searcher.stop = true;
    exitProcess();
});
//# sourceMappingURL=main.js.map
