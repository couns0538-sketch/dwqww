"use strict";
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
exports.buildRootHist = buildRootHist;
exports.hashMbToEntries = hashMbToEntries;
exports.setHashMb = setHashMb;
exports.clearSharedTT = clearSharedTT;
exports.clearWorkerTTs = clearWorkerTTs;
exports.abortSmpSearch = abortSmpSearch;
exports.setPoolNNUE = setPoolNNUE;
exports.queryPoolNNUE = queryPoolNNUE;
exports.ensurePool = ensurePool;
exports.shutdownPool = shutdownPool;
exports.searchLazySmp = searchLazySmp;
/** Lazy SMP manager — warm persistent worker pool + cooperative stop. */
const worker_threads_1 = require("worker_threads");
const path = __importStar(require("path"));
const movegen_1 = require("../move/movegen");
const tt_1 = require("./tt");
/**
 * rephist3: keys of game positions before the root that can still repeat, i.e. positions reached
 * AFTER the last capture or pawn move (halfmove clock 0). The position before an irreversible move
 * is excluded, as is everything earlier. Ordered newest first.
 */
function buildRootHist(board) {
    const histHi = [], histLo = [];
    for (let i = board.undoStack.length - 1; i >= 0; i--) {
        const u = board.undoStack[i];
        const m = u.move;
        if (m.captured !== 0 /* Piece.None */ || m.piece === 1 /* Piece.WP */ || m.piece === 7 /* Piece.BP */)
            break;
        histHi.push(u.zHi);
        histLo.push(u.zLo);
    }
    return { hi: Int32Array.from(histHi), lo: Int32Array.from(histLo) };
}
const WORKER_PATH = path.join(__dirname, 'smp_worker.js');
/** Persistent helper pool (reused across go commands). */
let pool = [];
let poolReady = [];
let activeStopFlag = null;
let activeMain = null;
let busyWorkers = [];
/** One shared TT for Lazy SMP (persists across go; cleared on ucinewgame). */
let sharedBundle = null;
/** hashmb: TT entries from UCI Hash (16 nominal bytes/entry, rounded down to a power of two; Hash=64 -> 1<<22 = old default). */
let hashEntries = tt_1.TT_SIZE;
function hashMbToEntries(mb) {
    const m = Math.max(1, Math.min(1024, mb | 0));
    const want = Math.floor((m * 1024 * 1024) / 16);
    let e = 1;
    while (e * 2 <= want)
        e *= 2;
    return e;
}
/** hashmb: apply UCI Hash to the shared SMP table and every worker's local table. Call between searches. */
function setHashMb(mb) {
    const e = hashMbToEntries(mb);
    if (e === hashEntries)
        return;
    hashEntries = e;
    sharedBundle = null; // recreated lazily at the new size
    for (const w of pool) {
        try {
            w.postMessage({ type: 'hash', entries: e });
        }
        catch { /* */ }
    }
}
function getSharedBundle() {
    if (!sharedBundle)
        sharedBundle = (0, tt_1.createSharedTTBundle)(hashEntries);
    return sharedBundle;
}
function clearSharedTT() {
    if (!sharedBundle)
        return;
    const tt = new tt_1.TranspositionTable(sharedBundle.size, sharedBundle);
    tt.clear();
}
/** ttkeep: clear each worker's persistent local TT (ucinewgame). Message order guarantees it lands before the next job. */
function clearWorkerTTs() {
    for (const w of pool) {
        try {
            w.postMessage({ type: 'newgame' });
        }
        catch { /* */ }
    }
}
function abortSmpSearch() {
    if (activeStopFlag) {
        try {
            Atomics.store(activeStopFlag, 0, 1);
        }
        catch { /* */ }
    }
    if (activeMain)
        activeMain.stop = true;
    for (const w of busyWorkers) {
        try {
            w.postMessage({ type: 'stop' });
        }
        catch { /* */ }
    }
}
function clearActive() {
    activeStopFlag = null;
    activeMain = null;
    busyWorkers = [];
}
/** NNUE config pushed to every worker (current + future). */
let nnueCfg = null;
function setPoolNNUE(use, file) {
    file = file ?? nnueCfg?.file ?? null;
    nnueCfg = { use, file };
    for (const w of pool) {
        try {
            w.postMessage({ type: 'nnue', use, file });
        }
        catch { /* */ }
    }
}
/** Ask every worker for its nnueInfo (testing / `nnueinfo` UCI debug command). */
let nnueQueryId = 0;
function queryPoolNNUE() {
    const qid = ++nnueQueryId;
    return Promise.all(pool.map((w, i) => new Promise((resolve) => {
        const onMsg = (msg) => {
            if (msg && msg.type === 'nnueinfo' && msg.qid === qid) {
                w.off('message', onMsg);
                resolve(`worker ${i}: ${msg.info}`);
            }
        };
        w.on('message', onMsg);
        try {
            w.postMessage({ type: 'nnueinfo', qid });
        }
        catch {
            resolve(`worker ${i}: unreachable`);
        }
    })));
}
/** Ensure at least `n` warm workers (all search threads, including main). */
async function ensurePool(n) {
    const need = Math.max(0, Math.min(8, n | 0));
    while (pool.length < need) {
        const idx = pool.length;
        const w = new worker_threads_1.Worker(WORKER_PATH);
        const ready = new Promise((resolve, reject) => {
            const onMsg = (msg) => {
                if (msg && (msg.type === 'boot' || msg.type === 'ready')) {
                    w.off('message', onMsg);
                    resolve();
                }
            };
            w.on('message', onMsg);
            w.on('error', reject);
            // Ask for explicit ready after boot
            if (nnueCfg)
                w.postMessage({ type: 'nnue', use: nnueCfg.use, file: nnueCfg.file });
            w.postMessage({ type: 'warmup', entries: hashEntries });
        });
        pool.push(w);
        poolReady.push(ready);
    }
    await Promise.all(poolReady.slice(0, need));
}
async function shutdownPool() {
    const ws = pool.slice();
    pool = [];
    poolReady = [];
    for (const w of ws) {
        try {
            w.postMessage({ type: 'shutdown' });
        }
        catch { /* */ }
        try {
            w.removeAllListeners();
        }
        catch { /* */ }
        try {
            await w.terminate();
        }
        catch { /* */ }
    }
}
/**
 * Prefer main (thread 0). Take a helper only if strictly deeper and not a
 * clear score regression — avoids Lazy-SMP "deeper-but-wrong" blunders at short TC.
 */
function pickBest(results) {
    const main = results.find(r => r.threadId === 0) || results[0];
    let best = main;
    for (const r of results) {
        if (r.threadId === 0)
            continue;
        const deepEnough = r.depth >= main.depth + 2;
        const deeperOkScore = r.depth > main.depth && r.score >= main.score - 30;
        if (!deepEnough && !deeperOkScore)
            continue;
        if (r.depth > best.depth || (r.depth === best.depth && r.score > best.score)) {
            best = r;
        }
    }
    return best;
}
function helperGraceMs(limits) {
    if (limits.moveTime !== undefined) {
        return Math.min(400, Math.max(80, Math.floor(limits.moveTime * 0.25) + 50));
    }
    return 300;
}
/**
 * Lazy SMP: ALL threads (including main/thread 0) run in warm workers.
 * UCI stays on the Node event loop so `stop` can set the SAB flag / postMessage.
 * Thread 0 posts info; helpers share TT and diversify mildly.
 */
async function searchLazySmp(board, limits, threads, onInfo) {
    const n = Math.max(1, Math.min(8, threads | 0));
    const sab = new SharedArrayBuffer(4);
    const stopFlag = new Int32Array(sab);
    Atomics.store(stopFlag, 0, 0);
    activeStopFlag = stopFlag;
    activeMain = null;
    await ensurePool(n);
    const fen = board.getFen();
    // rephist3: game-history keys strictly after the last irreversible move (capture or pawn move)
    const { hi: rootHistHi, lo: rootHistLo } = buildRootHist(board);
    const workers = pool.slice(0, n);
    busyWorkers = workers.slice();
    const results = [];
    const useSharedTT = n > 1;
    const bundle = useSharedTT ? getSharedBundle() : null;
    let mainDepth = 0, mainScore = 0, mainPv = [];
    let mainNodes = 0;
    let bestMainUci = null;
    const donePromises = workers.map((w, threadId) => {
        return new Promise((resolve) => {
            let settled = false;
            const finish = () => { if (!settled) {
                settled = true;
                resolve();
            } };
            const onMsg = (msg) => {
                if (msg.type === 'info' && threadId === 0) {
                    mainDepth = msg.depth;
                    mainScore = msg.score;
                    mainPv = msg.pv || [];
                    mainNodes = msg.nodes;
                    onInfo?.({
                        depth: msg.depth,
                        score: msg.score,
                        nodes: msg.nodes,
                        nps: msg.nps || 0,
                        timeMs: msg.timeMs || 0,
                        pv: msg.pv || [],
                        bestFrac: msg.bestFrac,
                    });
                    return;
                }
                if (msg.type === 'done' && msg.threadId === threadId) {
                    w.off('message', onMsg);
                    results.push({
                        threadId: msg.threadId,
                        best: msg.best,
                        depth: msg.depth,
                        score: msg.score,
                        nodes: msg.nodes,
                        pv: msg.pv || [],
                    });
                    if (threadId === 0) {
                        bestMainUci = msg.best;
                        mainDepth = msg.depth;
                        mainScore = msg.score;
                        mainPv = msg.pv || [];
                        mainNodes = msg.nodes;
                    }
                    finish();
                }
            };
            w.on('message', onMsg);
            const job = {
                type: 'search',
                fen,
                rootHistHi,
                rootHistLo,
                limits: { ...limits },
                threadId,
                stopSab: sab,
            };
            if (bundle)
                job.ttBundle = bundle;
            w.postMessage(job);
        });
    });
    // Await main (thread 0) — required for a legal bestmove
    try {
        await donePromises[0];
    }
    finally {
        Atomics.store(stopFlag, 0, 1);
        for (const w of workers) {
            try {
                w.postMessage({ type: 'stop' });
            }
            catch { /* */ }
        }
    }
    if (n > 1) {
        const timed = limits.moveTime !== undefined || limits.wtime !== undefined || limits.btime !== undefined;
        const waitMs = timed ? helperGraceMs(limits) : 180000;
        await new Promise((resolve) => {
            let done = false;
            const finish = () => {
                if (done)
                    return;
                done = true;
                clearTimeout(timer);
                resolve();
            };
            const timer = setTimeout(finish, waitMs);
            Promise.all(donePromises.slice(1)).then(finish).catch(finish);
        });
    }
    clearActive();
    const pick = pickBest(results.length ? results : [{
            threadId: 0,
            best: bestMainUci,
            depth: mainDepth,
            score: mainScore,
            nodes: mainNodes,
            pv: mainPv,
        }]);
    const totalNodes = results.reduce((s, r) => s + (r.nodes || 0), 0);
    let best = null;
    if (pick.best)
        best = (0, movegen_1.parseUciMove)(board, pick.best);
    if (!best && bestMainUci)
        best = (0, movegen_1.parseUciMove)(board, bestMainUci);
    return {
        best,
        nodes: totalNodes || mainNodes,
        depth: pick.depth,
        score: pick.score,
        pv: pick.pv,
    };
}
//# sourceMappingURL=smp.js.map
