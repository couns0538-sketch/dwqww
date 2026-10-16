"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
/**
 * Persistent Lazy-SMP worker (thread 0 + helpers).
 * Loads modules once, then loops on {type:'search'} jobs until {type:'shutdown'}.
 * Thread 0 posts UCI info; helpers only return final results.
 * Search runs OFF the UCI thread so `stop` can set the SAB Atomics flag.
 */
const worker_threads_1 = require("worker_threads");
const board_1 = require("../board/board");
const search_1 = require("./search");
const movegen_1 = require("../move/movegen");
const tt_1 = require("./tt");
const nnue_1 = require("../eval/nnue");
let activeSearch = null;
/**
 * ttkeep: one Search (and its local 1<<22 TT) per worker, reused across `go`.
 * Previously every job did `new Search(board)`, allocating a fresh 4M-entry TT
 * (~20-30 ms) that was discarded after the move. History/killers are still
 * reset per search by Search.search() -> resetHeuristics() (unchanged 1.7.26
 * behaviour); TT age is bumped per search by tt.prefetchAge().
 */
let persistentSearch = null;
let localTT = null;
/** hashmb: local TT size requested by UCI Hash (default = TT_SIZE, the lock's 1<<22). */
let wantEntries = 0;
function applyHash(entries) {
    if (!(entries > 0))
        return;
    wantEntries = entries;
    if (persistentSearch && persistentSearch.tt.size !== entries) {
        localTT = new tt_1.TranspositionTable(entries);
        persistentSearch.tt = localTT;
    }
}
function getSearch(fen) {
    const board = new board_1.Board(fen);
    if (!persistentSearch) {
        persistentSearch = new search_1.Search(board);
        localTT = persistentSearch.tt;
        if (wantEntries > 0 && localTT.size !== wantEntries) {
            localTT = new tt_1.TranspositionTable(wantEntries);
            persistentSearch.tt = localTT;
        }
    }
    else {
        persistentSearch.board = board;
    }
    return persistentSearch;
}
worker_threads_1.parentPort?.on('message', (msg) => {
    if (!msg || typeof msg !== 'object')
        return;
    if (msg.type === 'hash') {
        applyHash(msg.entries);
        return;
    }
    if (msg.type === 'warmup') {
        if (msg.entries)
            wantEntries = msg.entries;
        getSearch('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1');
        worker_threads_1.parentPort?.postMessage({ type: 'ready' });
        return;
    }
    if (msg.type === 'nnue') {
        if (msg.file)
            (0, nnue_1.loadNet)(msg.file);
        (0, nnue_1.setUseNNUE)(msg.use);
        return;
    }
    if (msg.type === 'nnueinfo') {
        worker_threads_1.parentPort?.postMessage({ type: 'nnueinfo', qid: msg.qid, info: (0, nnue_1.nnueInfo)() });
        return;
    }
    if (msg.type === 'newgame') {
        if (localTT)
            localTT.clear();
        return;
    }
    if (msg.type === 'stop') {
        if (activeSearch)
            activeSearch.stop = true;
        return;
    }
    if (msg.type === 'shutdown') {
        if (activeSearch)
            activeSearch.stop = true;
        setImmediate(() => process.exit(0));
        return;
    }
    if (msg.type === 'search') {
        const stopFlag = new Int32Array(msg.stopSab);
        const search = getSearch(msg.fen);
        // accroot: make root accumulator slot valid (eval-cache hits skip NNUE, leaving slot 0 stale -> full refreshes)
        if ((0, nnue_1.nnueActive)()) (0, nnue_1.updateAccumulator)(search.board);
        search.rootHistHi = msg.rootHistHi ?? null;
        search.rootHistLo = msg.rootHistLo ?? null;
        activeSearch = search;
        search.stopFlag = stopFlag;
        search.deadline = msg.deadlineSab ? new BigInt64Array(msg.deadlineSab) : null;
        search.threadId = msg.threadId;
        if (msg.ttBundle) {
            search.tt = new tt_1.TranspositionTable(msg.ttBundle.size, msg.ttBundle);
        }
        else if (localTT) {
            search.tt = localTT;
        }
        const isMain = msg.threadId === 0;
        if (isMain) {
            // A worker that was a helper last go must not keep helper knobs
            // if it is reused as thread 0 (the previous worker died).
            search.skipRootIid = false;
            search.aspirationWindow = 50;
            search.historyNoiseSeed = 0;
            search.rootQuietRotate = 0;
            search.rootDeferPv = false;
        }
        else {
            /*
             * With shared TT, mild diversification only (classic Lazy SMP):
             * skip root IID + slight aspiration skew. Avoid heavy rootDefer/history
             * noise that previously made helpers return deeper-but-worse moves.
             */
            search.skipRootIid = true;
            search.aspirationWindow = 45 + 10 * msg.threadId;
            search.historyNoiseSeed = 0;
            search.rootQuietRotate = 0;
            search.rootDeferPv = false;
        }
        let lastDepth = 0;
        let lastScore = 0;
        let lastPv = [];
        search.onInfo = (info) => {
            lastDepth = info.depth;
            lastScore = info.score;
            lastPv = info.pv;
            if (isMain) {
                worker_threads_1.parentPort?.postMessage({
                    type: 'info',
                    gen: msg.gen,
                    threadId: 0,
                    depth: info.depth,
                    score: info.score,
                    nodes: info.nodes,
                    nps: info.nps,
                    timeMs: info.timeMs,
                    pv: info.pv,
                    bestFrac: rootBestFrac(search),
                });
            }
        };
        try {
            const best = search.search(msg.limits);
            worker_threads_1.parentPort?.postMessage({
                type: 'done',
                gen: msg.gen,
                threadId: msg.threadId,
                best: best ? (0, movegen_1.moveToUci)(best) : null,
                depth: lastDepth,
                score: lastScore,
                nodes: search.nodes,
                pv: lastPv,
            });
        }
        catch (e) {
            worker_threads_1.parentPort?.postMessage({
                type: 'done',
                gen: msg.gen,
                threadId: msg.threadId,
                best: null,
                depth: lastDepth,
                score: lastScore,
                nodes: search.nodes,
                pv: lastPv,
                error: String(e),
            });
        }
        finally {
            activeSearch = null;
            worker_threads_1.parentPort?.postMessage({ type: 'idle', gen: msg.gen, threadId: msg.threadId });
        }
    }
});
worker_threads_1.parentPort?.postMessage({ type: 'boot' });
/** tm-forge-1726: share of root nodes spent under the current best (PV) move; undefined if unknown. */
function rootBestFrac(s) {
    if (s.pvLength[0] <= 0)
        return undefined;
    let total = 0;
    for (const v of s.rootMoveNodes.values())
        total += v;
    if (total <= 0)
        return undefined;
    return (s.rootMoveNodes.get((0, search_1.rootMoveKey)(s.pvTable[0][0])) ?? 0) / total;
}
//# sourceMappingURL=smp_worker.js.map
