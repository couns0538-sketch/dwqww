"use strict";
/** Transposition table — packed entries; optional SharedArrayBuffer for Lazy SMP */
Object.defineProperty(exports, "__esModule", { value: true });
exports.MATE_BOUND = exports.MATE_SCORE = exports.TranspositionTable = exports.TT_SIZE = void 0;
exports.createSharedTTBundle = createSharedTTBundle;
exports.packMove = packMove;
exports.unpackMove = unpackMove;
exports.scoreToTT = scoreToTT;
exports.scoreFromTT = scoreFromTT;
/** Default 4M entries; shared SMP uses same. */
exports.TT_SIZE = 1 << 22;
function createSharedTTBundle(size = exports.TT_SIZE) {
    return {
        size,
        // Lockless entry: two atomic u64 words. keyXor = positionKey XOR data.
        keyXorSab: new SharedArrayBuffer(size * 8),
        dataSab: new SharedArrayBuffer(size * 8),
        metaSab: new SharedArrayBuffer(4),
    };
}
function posKey(hi, lo) {
    return (BigInt(hi >>> 0) << 32n) | BigInt(lo >>> 0);
}
/** data word: bit63 occupied, 43..50 age, 41..42 flag, 33..40 depth, 17..32 score, 0..16 move. */
function packTTData(depth, score, flag, age, moveCode) {
    const mv = BigInt(moveCode >>> 0) & 0x1ffffn;
    const sc = BigInt(score & 0xffff);
    const dep = BigInt(depth & 0xff);
    const fl = BigInt(flag & 3);
    const ag = BigInt(age & 0xff);
    return (1n << 63n) | (ag << 43n) | (fl << 41n) | (dep << 33n) | (sc << 17n) | mv;
}
function unpackTTData(data) {
    const moveCode = Number(data & 0x1ffffn);
    let score = Number((data >> 17n) & 0xffffn);
    if (score & 0x8000)
        score -= 0x10000;
    return {
        moveCode,
        score,
        depth: Number((data >> 33n) & 0xffn),
        flag: Number((data >> 41n) & 3n),
        age: Number((data >> 43n) & 0xffn),
    };
}
/** Pack from/to/promo; 0 = null. sameMove only needs these fields. */
function packMove(m) {
    if (!m)
        return 0;
    if (typeof m === 'number') {
        const from = m & 63, to = (m >>> 6) & 63, promo = (m >>> 20) & 15;
        return (1 + from + (to << 6) + (promo << 12)) >>> 0;
    }
    return (1 + m.from + (m.to << 6) + ((m.promo & 15) << 12)) >>> 0;
}
function unpackMove(code) {
    if (!code)
        return null;
    const v = (code - 1) >>> 0;
    return {
        from: v & 63,
        to: (v >>> 6) & 63,
        promo: (v >>> 12) & 15,
        piece: 0 /* Piece.None */,
        captured: 0 /* Piece.None */,
        flags: 0,
    };
}
class TranspositionTable {
    constructor(size = exports.TT_SIZE, bundle) {
        /** Optional object cache for local TT only (unused when shared). */
        this.moves = null;
        this.age = 0;
        this.sharedMeta = null;
        this.isShared = false;
        if (bundle) {
            this.size = bundle.size;
            this.xkey64 = new BigUint64Array(bundle.keyXorSab);
            this.data64 = new BigUint64Array(bundle.dataSab);
            this.sharedMeta = new Int32Array(bundle.metaSab);
            this.isShared = true;
            this.age = Atomics.load(this.sharedMeta, 0) & 255;
        }
        else {
            this.size = size;
            this.keysHi = new Int32Array(size);
            this.keysLo = new Int32Array(size);
            this.depths = new Int8Array(size);
            this.scores = new Int16Array(size);
            this.flags = new Uint8Array(size);
            this.ages = new Uint8Array(size);
            this.moveCodes = new Uint32Array(size);
            this.depths.fill(-1);
        }
    }
    clear() {
        if (this.isShared) {
            this.xkey64.fill(0n);
            this.data64.fill(0n);
            this.age = 0;
            Atomics.store(this.sharedMeta, 0, 0);
            return;
        }
        this.depths.fill(-1);
        this.moveCodes.fill(0);
        this.keysHi.fill(0);
        this.keysLo.fill(0);
        this.scores.fill(0);
        this.flags.fill(0);
        this.ages.fill(0);
        this.age = 0;
    }
    index(lo) {
        return lo & (this.size - 1);
    }
    probe(hi, lo) {
        const i = lo & (this.size - 1);
        if (this.isShared)
            return this.probeShared(hi, lo, i);
        if (this.keysLo[i] === lo && this.keysHi[i] === hi && this.depths[i] >= 0) {
            return {
                hi, lo,
                depth: this.depths[i],
                score: this.scores[i],
                flag: this.flags[i],
                bestMove: unpackMove(this.moveCodes[i]),
                age: this.ages[i],
            };
        }
        return null;
    }
    /** Read both words. A tear (key from one writer, data from another) fails the XOR. */
    readShared(i) {
        const k1 = Atomics.load(this.xkey64, i);
        const data = Atomics.load(this.data64, i);
        const k2 = Atomics.load(this.xkey64, i);
        if (k1 !== k2 || data === 0n)
            return null;
        return { key: k1 ^ data, data };
    }
    probeShared(hi, lo, i) {
        const got = this.readShared(i);
        if (!got || got.key !== posKey(hi, lo))
            return null;
        const u = unpackTTData(got.data);
        return {
            hi, lo,
            depth: u.depth,
            score: u.score,
            flag: u.flag,
            bestMove: unpackMove(u.moveCode),
            age: u.age,
        };
    }
    writeShared(i, hi, lo, depth, score, flag, bestMove) {
        const d = depth > 127 ? 127 : depth;
        const sc = score > 32767 ? 32767 : score < -32768 ? -32768 : score;
        const data = packTTData(d, sc, flag, this.age & 255, packMove(bestMove));
        // data first, then the XOR key, so a reader never pairs a new key with an older data word
        Atomics.store(this.data64, i, data);
        Atomics.store(this.xkey64, i, posKey(hi, lo) ^ data);
    }
    store(hi, lo, depth, score, flag, bestMove) {
        const i = lo & (this.size - 1);
        if (this.isShared) {
            this.storeShared(hi, lo, depth, score, flag, bestMove, i);
            return;
        }
        const curD = this.depths[i];
        const same = this.keysLo[i] === lo && this.keysHi[i] === hi && curD >= 0;
        if (same && depth < curD && flag !== 0 /* TTFlag.Exact */) {
            if (!this.moveCodes[i] && bestMove)
                this.moveCodes[i] = packMove(bestMove);
            return;
        }
        if (same && depth < curD) {
            if (!this.moveCodes[i] && bestMove)
                this.moveCodes[i] = packMove(bestMove);
            return;
        }
        // ttkeep: wrap-safe generation distance (age is 8-bit and now persists across go)
        if (!same && curD >= 0 && depth < curD && ((this.age - this.ages[i]) & 255) <= 2 && flag !== 0 /* TTFlag.Exact */) {
            return;
        }
        // Racy writes OK for Lazy SMP — last writer wins
        this.keysHi[i] = hi;
        this.keysLo[i] = lo;
        this.depths[i] = depth > 127 ? 127 : depth;
        this.scores[i] = score > 32767 ? 32767 : score < -32768 ? -32768 : score;
        this.flags[i] = flag;
        this.moveCodes[i] = packMove(bestMove);
        this.ages[i] = this.age & 255;
    }
    storeShared(hi, lo, depth, score, flag, bestMove, i) {
        const got = this.readShared(i);
        const key = posKey(hi, lo);
        const same = !!(got && got.key === key);
        let curD = -1, curMove = 0;
        if (same) {
            const u = unpackTTData(got.data);
            curD = u.depth;
            curMove = u.moveCode;
        }
        else if (got) {
            curD = unpackTTData(got.data).depth;
        }
        if (same && depth < curD) {
            if (!curMove && bestMove)
                this.writeShared(i, hi, lo, curD, unpackTTData(got.data).score, unpackTTData(got.data).flag, bestMove);
            return;
        }
        if (!same && curD >= 0 && depth < curD && ((this.age - (got ? unpackTTData(got.data).age : 0)) & 255) <= 2 && flag !== 0 /* TTFlag.Exact */) {
            return;
        }
        this.writeShared(i, hi, lo, depth, score, flag, bestMove);
    }
    prefetchAge() {
        if (this.sharedMeta) {
            // Approximate age bump; races are fine for replacement policy
            let a = (Atomics.load(this.sharedMeta, 0) + 1) & 255;
            Atomics.store(this.sharedMeta, 0, a);
            this.age = a;
        }
        else {
            this.age = (this.age + 1) & 255;
        }
    }
}
exports.TranspositionTable = TranspositionTable;
exports.MATE_SCORE = 30000;
exports.MATE_BOUND = 29000;
function scoreToTT(score, ply) {
    if (score > exports.MATE_BOUND)
        return score + ply;
    if (score < -exports.MATE_BOUND)
        return score - ply;
    return score;
}
function scoreFromTT(score, ply) {
    if (score > exports.MATE_BOUND)
        return score - ply;
    if (score < -exports.MATE_BOUND)
        return score + ply;
    return score;
}
//# sourceMappingURL=tt.js.map
