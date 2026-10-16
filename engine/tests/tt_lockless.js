"use strict";
/** Lockless TT: a torn key/data pair must miss, including under 4 racing writers. */
const { Worker, isMainThread, workerData, parentPort } = require("worker_threads");
const { TranspositionTable, createSharedTTBundle } = require("../search/tt");

if (!isMainThread) {
    const tt = new TranspositionTable(workerData.size, workerData.bundle);
    const id = workerData.id;
    let checks = 0;
    for (let n = 0; n < 250000; n++) {
        const hi = (id + 1) * 0x1000 + ((n >>> 8) & 255);
        const lo = ((n & 255) << 10) | id; // 4 writers, distinct keys, shared index slots
        const move = { from: id, to: n & 63, promo: 0, piece: 1, captured: 0, flags: 0 };
        const score = 1000 + id;
        tt.store(hi, lo, 4, score, 1, move);
        const hit = tt.probe(hi, lo);
        if (!hit)
            continue;
        checks++;
        if (hit.bestMove.from !== id || hit.score !== score || hit.flag !== 1 || hit.depth !== 4) {
            parentPort.postMessage({ bad: { from: hit.bestMove && hit.bestMove.from, score: hit.score, flag: hit.flag, depth: hit.depth, id } });
            return;
        }
    }
    parentPort.postMessage({ done: true, id, checks });
    return;
}

function fail(msg) {
    console.error("FAIL", msg);
    process.exit(1);
}

// Deterministic tear: data from key A, XOR-key from key B.
{
    const size = 1024;
    const tt = new TranspositionTable(size, createSharedTTBundle(size));
    const a = { hi: 11, lo: 5, score: 123, from: 3 };
    const b = { hi: 22, lo: 5 + size, score: 456, from: 6 }; // same slot: lo & 1023 === 5
    const ma = { from: a.from, to: 10, promo: 0, piece: 1, captured: 0, flags: 0 };
    const mb = { from: b.from, to: 20, promo: 0, piece: 1, captured: 0, flags: 0 };
    tt.store(a.hi, a.lo, 6, a.score, 0, ma);
    const i = a.lo & (size - 1);
    const dataA = tt.data64[i];
    const xkA = tt.xkey64[i];
    tt.store(b.hi, b.lo, 7, b.score, 1, mb);
    const dataB = tt.data64[i];
    const xkB = tt.xkey64[i];
    // Publish B's key with A's data. XOR no longer matches either position.
    Atomics.store(tt.data64, i, dataA);
    Atomics.store(tt.xkey64, i, xkB);
    if (tt.probe(a.hi, a.lo) !== null)
        fail("torn entry matched key A");
    if (tt.probe(b.hi, b.lo) !== null)
        fail("torn entry matched key B");
    // Consistent pair still hits and the move belongs to that key.
    Atomics.store(tt.data64, i, dataA);
    Atomics.store(tt.xkey64, i, xkA);
    const hit = tt.probe(a.hi, a.lo);
    if (!hit || hit.score !== a.score || hit.bestMove.from !== a.from || hit.depth !== 6)
        fail("consistent entry was rejected: " + JSON.stringify(hit));
    console.log("deterministic tear: rejected, consistent hit ok");
}

const size = 4096;
const bundle = createSharedTTBundle(size);
const workers = [0, 1, 2, 3].map((id) => new Worker(__filename, { workerData: { bundle, size, id } }));
let bad = 0;
let done = 0;
for (const w of workers) {
    w.on("message", (msg) => {
        if (msg.bad) {
            bad++;
            console.error("torn tuple", msg.bad);
        }
        if (msg.done)
            done++;
    });
    w.on("error", (e) => {
        console.error(e);
        process.exit(1);
    });
}
const started = Date.now();
const timer = setInterval(() => {
    if (done < 4 && Date.now() - started < 60000)
        return;
    clearInterval(timer);
    if (done !== 4)
        fail("workers did not finish: " + done);
    if (bad)
        fail("torn entries observed: " + bad);
    console.log("threads 4: 0 torn entries");
    process.exit(0);
}, 50);
