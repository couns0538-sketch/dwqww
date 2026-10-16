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
exports.afterWorkersIdle = afterWorkersIdle;
exports.prepareWorkers = prepareWorkers;
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
/**
 * Helpers keep running for a short tail after bestmove. ucinewgame / Hash / the
 * next go must wait until that tail has posted `idle`, or they clear or reuse
 * the shared table while those workers are still storing.
 */
const idleSlot = new WeakMap();
let idleChain = Promise.resolve();
function markBusy(w, gen) {
    let resolve;
    const promise = new Promise((r) => { resolve = r; });
    idleSlot.set(w, { promise, resolve, busy: true, gen });
}
function markIdle(w, gen) {
    const slot = idleSlot.get(w);
    if (!slot || !slot.busy)
        return;
    if (gen != null && slot.gen !== gen)
        return;
    slot.busy = false;
    slot.resolve();
}
function sleepMs(ms) {
    return new Promise((r) => setTimeout(r, ms));
}
async function drainWorkers(ms = 1000) {
    // A search that has not been asked to stop must run to completion.
    // The tail after bestmove has already raised the stop flag (or cleared it
    // on the way out); a worker that ignores that is terminated.
    const live = activeStopFlag && Atomics.load(activeStopFlag, 0) === 0;
    const pending = pool.slice();
    for (const w of pending) {
        const slot = idleSlot.get(w);
        if (!slot || !slot.busy)
            continue;
        const finished = live
            ? await slot.promise.then(() => true)
            : await Promise.race([
                slot.promise.then(() => true),
                sleepMs(ms).then(() => false),
            ]);
        if (!finished) {
            markIdle(w, null);
            const i = pool.indexOf(w);
            if (i >= 0) {
                pool.splice(i, 1);
                poolReady.splice(i, 1);
            }
            try {
                w.terminate();
            }
            catch { /* */ }
        }
    }
}
async function prepareWorkers() {
    await idleChain;
    await drainWorkers();
}
/** Run fn only after every worker has left its current search. */
function afterWorkersIdle(fn) {
    idleChain = idleChain.then(async () => {
        await drainWorkers();
        await fn();
    }).catch(() => { /* keep the chain alive */ });
}
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
async function clearSharedTT() {
    if (!sharedBundle)
        return;
    const tt = new tt_1.TranspositionTable(sharedBundle.size, sharedBundle);
    const n = tt.data64.length;
    // Yield so quit/stop are not stuck behind a large atomic wipe.
    for (let i = 0; i < n;) {
        const end = Math.min(n, i + 65536);
        for (; i < end; i++) {
            Atomics.store(tt.data64, i, 0n);
            Atomics.store(tt.xkey64, i, 0n);
        }
        await new Promise((r) => setImmediate(r));
    }
    tt.age = 0;
    Atomics.store(tt.sharedMeta, 0, 0);
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
        w.on('message', (msg) => {
            if (msg && msg.type === 'idle')
                markIdle(w, msg.gen);
        });
        w.on('exit', () => {
            markIdle(w, null);
            const i = pool.indexOf(w);
            if (i >= 0) {
                pool.splice(i, 1);
                poolReady.splice(i, 1);
            }
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
let searchGen = 0;
/** bestmove is always the main thread's last completed iteration (the PV already printed). */
function pickBest(results) {
    const main = results.find(r => r.threadId === 0);
    if (main)
        return main;
    return { threadId: 0, best: null, depth: 0, score: 0, nodes: 0, pv: [] };
}
/** One generation per go, before any worker runs. Local tables still bump themselves. */
function bumpSharedAge(bundle) {
    if (!bundle)
        return;
    const meta = new Int32Array(bundle.metaSab);
    Atomics.store(meta, 0, (Atomics.load(meta, 0) + 1) & 255);
}
/**
 * Lazy SMP: ALL threads (including main/thread 0) run in warm workers.
 * UCI stays on the Node event loop so `stop` can set the SAB flag / postMessage.
 * Thread 0 posts info; helpers share TT and diversify mildly.
 */
async function searchLazySmp(board, limits, threads, onInfo) {
    const n = Math.max(1, Math.min(8, threads | 0));
    await prepareWorkers();
    const gen = ++searchGen;
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
    bumpSharedAge(bundle);
    let mainDepth = 0, mainScore = 0, mainPv = [];
    let mainNodes = 0;
    let bestMainUci = null;
    const cleanups = [];
    const donePromises = workers.map((w, threadId) => {
        return new Promise((resolve) => {
            let settled = false;
            const finish = () => { if (!settled) {
                settled = true;
                resolve();
            } };
            const onMsg = (msg) => {
                if (!msg || msg.gen !== gen)
                    return;
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
                    if (settled)
                        return;
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
            const onDead = () => {
                if (settled)
                    return;
                results.push({ threadId, best: null, depth: 0, score: 0, nodes: 0, pv: [] });
                finish();
            };
            w.on('exit', onDead);
            w.on('message', onMsg);
            cleanups.push(() => {
                try { w.off('message', onMsg); } catch { /* */ }
                try { w.off('exit', onDead); } catch { /* */ }
            });
            const job = {
                type: 'search',
                gen,
                fen,
                rootHistHi,
                rootHistLo,
                limits: { ...limits },
                threadId,
                stopSab: sab,
            };
            if (bundle)
                job.ttBundle = bundle;
            markBusy(w, gen);
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
    // Helpers were already told to stop. Do not block bestmove on them (infinite/depth used to wait 180s).
    if (n > 1)
        await Promise.race([
            Promise.all(donePromises.slice(1)).catch(() => { }),
            new Promise((resolve) => setTimeout(resolve, 40)),
        ]);
    for (const off of cleanups)
        off();
    clearActive();
    const pick = pickBest(results);
    if (!pick.best && bestMainUci) {
        pick.best = bestMainUci;
        pick.depth = mainDepth;
        pick.score = mainScore;
        pick.nodes = mainNodes;
        pick.pv = mainPv;
    }
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
