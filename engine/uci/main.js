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
            board.setFen(board_1.START_FEN);
            if (searcher)
                searcher.tt.clear();
            (0, smp_1.clearSharedTT)();
            (0, smp_1.clearWorkerTTs)();
            break;
        case 'position': {
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
                        // Stop applying further moves — continuing desyncs vs the GUI move list
                        send(`info string warning: ignored illegal move ${uci} (stopping move list)`);
                        break;
                    }
                    idx++;
                }
            }
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
            if (limits.maxDepth === undefined && limits.moveTime === undefined && limits.wtime === undefined && limits.btime === undefined && !limits.infinite) {
                limits.moveTime = 3000;
            }
            // Time management v2: turn the clock into a hard deadline (stop-flag timer) + soft per-iteration limit.
            let soft = null;
            let hardTimer = null;
            const goStart = Date.now();
            let searchLimits = limits;
            if (limits.moveTime !== undefined) {
                // explicit movetime: honour it minus overhead beyond what search.ts already subtracts (8 ms)
                const mt = Math.max(10, limits.moveTime - Math.max(0, moveOverhead - 8));
                searchLimits = { ...limits, moveTime: mt };
                hardTimer = setTimeout(smp_1.abortSmpSearch, Math.max(5, mt - 8));
            }
            else if (!limits.infinite && (limits.wtime !== undefined || limits.btime !== undefined)) {
                const white = board.side === 0;
                const t = white ? limits.wtime : limits.btime;
                const inc = white ? limits.winc : limits.binc;
                const budget = (0, timeman_1.computeBudget)({ time: t, inc, movestogo, moveOverhead });
                soft = new timeman_1.SoftController(budget);
                // search-internal limit is a backstop slightly behind the timer-driven stop
                searchLimits = { maxDepth: limits.maxDepth, moveTime: budget.hard + 8 + 30 };
                hardTimer = setTimeout(smp_1.abortSmpSearch, budget.hard);
            }
            searching = true;
            stopPending = false;
            setImmediate(async () => {
                try {
                    if (stopPending) {
                        searchLimits = { maxDepth: 1 };
                        if (hardTimer) {
                            clearTimeout(hardTimer);
                            hardTimer = null;
                        }
                        soft = null;
                    }
                    searchLimits = { ...searchLimits, startTime: goStart };
                    const result = await (0, smp_1.searchLazySmp)(board, searchLimits, threads, (info) => {
                        if (soft && info.pv.length > 0 && soft.onIteration(info.depth, info.score, info.pv[0], Date.now() - goStart, info.bestFrac))
                            (0, smp_1.abortSmpSearch)();
                        const scoreStr = scoreString(info.score);
                        send(`info depth ${info.depth} score ${scoreStr} nodes ${info.nodes} nps ${info.nps} time ${info.timeMs} pv ${info.pv.join(' ')}`);
                    });
                    searcher = null;
                    const best = result.best;
                    if (best)
                        send(`bestmove ${(0, movegen_1.moveToUci)(best)}`);
                    else {
                        const legal = (0, movegen_1.generateLegalMoves)(board);
                        if (legal.length)
                            send(`bestmove ${(0, movegen_1.moveToUci)(legal[0])}`);
                        else
                            send('bestmove 0000');
                    }
                }
                finally {
                    if (hardTimer)
                        clearTimeout(hardTimer);
                    searching = false;
                }
            });
            break;
        }
        case 'stop':
            if (searching)
                stopPending = true;
            (0, smp_1.abortSmpSearch)();
            if (searcher)
                searcher.stop = true;
            break;
        case 'quit':
            (0, smp_1.shutdownPool)().finally(() => process.exit(0));
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
                    (0, smp_1.setPoolNNUE)(on, null);
                    if (changed) {
                        (0, smp_1.clearSharedTT)();
                        (0, smp_1.clearWorkerTTs)();
                    }
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
                        (0, smp_1.setPoolNNUE)(nnueUse, f);
                        (0, smp_1.clearSharedTT)();
                        (0, smp_1.clearWorkerTTs)();
                        send(`info string ${(0, nnue_1.nnueInfo)()}`);
                    }
                }
                else if (opt === 'Hash') {
                    // hashmb: Hash now actually sizes the TT (was ignored; workers always used 1<<22)
                    (0, smp_1.setHashMb)(parseInt(val, 10) || 64);
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
//# sourceMappingURL=main.js.map
