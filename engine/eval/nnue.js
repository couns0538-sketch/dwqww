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
exports.resolvedDefaultPath = void 0;
exports.hiddenSize = hiddenSize;
exports.resetAccumulators = resetAccumulators;
exports.loadNet = loadNet;
exports.setUseNNUE = setUseNNUE;
exports.nnueActive = nnueActive;
exports.nnueInfo = nnueInfo;
exports.updateAccumulator = updateAccumulator;
exports.nnueEvaluate = nnueEvaluate;
exports.checkAccumulator = checkAccumulator;
exports.nnueGen = nnueGen;
/** NNUE 768->Hx2->1 (clipped ReLU, matches /workspace/chess-tools/nnue/train.py export), int16 weights, lazy incremental accumulator stack. UNPROVEN experiment.
 * Net file (little-endian):
 *   magic 'GKNN' (u32 0x4E4E4B47), version u32 = 1, hidden u32 = H (any 8..1024),
 *   ftW int16[768*H] (feature-major: w[f*H+j]), ftB int16[H],
 *   outW int16[2H] (first H = side-to-move half, next H = other half), outB int32 (scaled QA*QB).
 * Feature (white persp.) = (type + 6*color)*64 + sq, type 0..5 = P..K, color 0=W;
 * black persp. = (type + 6*(1-color))*64 + (sq^56).
 * eval_cp = (sum_j clamp(acc,0,QA)*w + outB) * SCALE / (QA*QB), QA=255, QB=64, SCALE=400.
 *
 * The accumulator stack is indexed by board.undoStack.length and tagged with the position key
 * (zHi/zLo). On eval it walks back to the nearest valid ancestor and replays the undo moves, so
 * board/move/tt code is untouched (no hooks in makeMove/unmakeMove).
 */
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
let HID = 128;
function hiddenSize() { return HID; }
const NFEAT = 768;
const QA = 255, QB = 64, SCALE = 400;
const MAGIC = 0x4E4E4B47;
let ftW = new Int16Array(NFEAT * HID);
let ftB = new Int16Array(HID);
let outW = new Int16Array(2 * HID);
let outB = 0;
let loaded = false;
let enabled = true;
let loadedPath = '';
let lastError = '';
// nncache: bumped on net load / UseNNUE toggle so evaluate.js drops cached scores from the other evaluator; UNPROVEN
let evalGen = 1;
function nnueGen() { return evalGen; }
exports.resolvedDefaultPath = '';
// feature index tables: FW[piece*64+sq], FB[piece*64+sq] -> feature offset (already * HID)
const FW = new Int32Array(13 * 64);
const FB = new Int32Array(13 * 64);
function buildTables() {
    for (let p = 1; p <= 12; p++) {
        const type = p <= 6 ? p - 1 : p - 7;
        const color = p <= 6 ? 0 : 1;
        for (let s = 0; s < 64; s++) {
            FW[p * 64 + s] = ((type + 6 * color) * 64 + s) * HID;
            FB[p * 64 + s] = ((type + 6 * (1 - color)) * 64 + (s ^ 56)) * HID;
        }
    }
}
buildTables();
function allocAcc() {
    accW = new Int16Array(CAP * HID);
    accB = new Int16Array(CAP * HID);
    keyHi = new Int32Array(CAP);
    keyLo = new Int32Array(CAP);
    valid = new Uint8Array(CAP);
}
let CAP = 1024;
let accW = new Int16Array(CAP * HID);
let accB = new Int16Array(CAP * HID);
let keyHi = new Int32Array(CAP);
let keyLo = new Int32Array(CAP);
let valid = new Uint8Array(CAP);
function grow(need) {
    let n = CAP;
    while (n <= need)
        n *= 2;
    const nw = new Int16Array(n * HID);
    nw.set(accW);
    accW = nw;
    const nb = new Int16Array(n * HID);
    nb.set(accB);
    accB = nb;
    const kh = new Int32Array(n);
    kh.set(keyHi);
    keyHi = kh;
    const kl = new Int32Array(n);
    kl.set(keyLo);
    keyLo = kl;
    const v = new Uint8Array(n);
    v.set(valid);
    valid = v;
    CAP = n;
}
function resetAccumulators() { valid.fill(0); }
/** Load a net; on any failure the previous net is dropped (HCE fallback) and lastError is set. */
function loadNet(file) {
    // v6: on failure keep the previously loaded net (state is only replaced on success)
    return loadNetInner(file);
}
function loadNetInner(file) {
    try {
        const buf = fs.readFileSync(file);
        const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
        lastError = 'bad header/size';
        if (buf.byteLength < 12 || dv.getUint32(0, true) !== MAGIC || dv.getUint32(4, true) !== 1)
            return false;
        const H = dv.getUint32(8, true);
        if (H < 8 || H > 1024 || buf.byteLength !== 12 + (NFEAT * H + H + 2 * H) * 2 + 4)
            return false;
        let o = 12;
        const rd = (a) => { for (let i = 0; i < a.length; i++, o += 2)
            a[i] = dv.getInt16(o, true); };
        const w = new Int16Array(NFEAT * H), b = new Int16Array(H), ow = new Int16Array(2 * H);
        rd(w);
        rd(b);
        rd(ow);
        // int16 accumulator safety: |ftB| + 32*max|ftW| < 32767 (at most 32 pieces active)
        let mw = 0, mb = 0;
        for (let i = 0; i < w.length; i++) {
            const a = w[i] < 0 ? -w[i] : w[i];
            if (a > mw)
                mw = a;
        }
        for (let i = 0; i < b.length; i++) {
            const a = b[i] < 0 ? -b[i] : b[i];
            if (a > mb)
                mb = a;
        }
        if (mb + 32 * mw >= 32767) {
            lastError = `weight bound violated: max|ftB| ${mb} + 32*max|ftW| ${mw} >= 32767`;
            return false;
        }
        ftW = w;
        ftB = b;
        outW = ow;
        outB = dv.getInt32(o, true);
        if (H !== HID) {
            HID = H;
            buildTables();
            allocAcc();
        }
        loaded = true;
        evalGen++;
        loadedPath = file;
        lastError = '';
        resetAccumulators();
        return true;
    }
    catch (e) {
        lastError = String(e.message || e);
        return false;
    }
}
function setUseNNUE(on) { if (enabled !== on) evalGen++; enabled = on; }
function nnueActive() { return enabled && loaded; }
function nnueInfo() { return (lastError ? `last EvalFile load failed (${lastError}); ` : '') + (loaded ? `NNUE ${enabled ? 'on' : 'off'} file ${loadedPath}` : 'NNUE no net loaded (HCE)'); }
/** Full refresh of slot d from the board. */
function refresh(board, d) {
    const ow = d * HID;
    for (let j = 0; j < HID; j++) {
        accW[ow + j] = ftB[j];
        accB[ow + j] = ftB[j];
    }
    const sqs = board.squares;
    for (let s = 0; s < 64; s++) {
        const p = sqs[s];
        if (p === 0)
            continue;
        const fw = FW[p * 64 + s], fb = FB[p * 64 + s];
        for (let j = 0; j < HID; j++) {
            accW[ow + j] += ftW[fw + j];
            accB[ow + j] += ftW[fb + j];
        }
    }
}
// scratch for deltas
const addW = new Int32Array(2), addB = new Int32Array(2), subW = new Int32Array(2), subB = new Int32Array(2);
/** child slot c = parent slot c-1 + delta of move (from undo info). */
function applyMove(c, from, to, piece, captured, promo, flags) {
    const src = (c - 1) * HID, dst = c * HID;
    if (piece === 0) { // null move
        accW.copyWithin(dst, src, src + HID);
        accB.copyWithin(dst, src, src + HID);
        return;
    }
    const white = piece <= 6;
    const placed = promo !== 0 ? promo : piece;
    let na = 1, ns = 1;
    addW[0] = FW[placed * 64 + to];
    addB[0] = FB[placed * 64 + to];
    subW[0] = FW[piece * 64 + from];
    subB[0] = FB[piece * 64 + from];
    if (flags & 2) { // en passant
        const cs = white ? to - 8 : to + 8;
        subW[1] = FW[captured * 64 + cs];
        subB[1] = FB[captured * 64 + cs];
        ns = 2;
    }
    else if (captured !== 0) {
        subW[1] = FW[captured * 64 + to];
        subB[1] = FB[captured * 64 + to];
        ns = 2;
    }
    else if (flags & 1) { // castle: rook
        let rf = 0, rt = 0;
        if (to === 6) {
            rf = 7;
            rt = 5;
        }
        else if (to === 2) {
            rf = 0;
            rt = 3;
        }
        else if (to === 62) {
            rf = 63;
            rt = 61;
        }
        else {
            rf = 56;
            rt = 59;
        }
        const r = white ? 4 : 10;
        addW[1] = FW[r * 64 + rt];
        addB[1] = FB[r * 64 + rt];
        subW[1] = FW[r * 64 + rf];
        subB[1] = FB[r * 64 + rf];
        na = 2;
        ns = 2;
    }
    const W = ftW, aw = accW, ab = accB;
    if (na === 1 && ns === 1) {
        const a0 = addW[0], s0 = subW[0], b0 = addB[0], t0 = subB[0];
        for (let j = 0; j < HID; j++) {
            aw[dst + j] = aw[src + j] + W[a0 + j] - W[s0 + j];
            ab[dst + j] = ab[src + j] + W[b0 + j] - W[t0 + j];
        }
    }
    else if (na === 1) {
        const a0 = addW[0], s0 = subW[0], s1 = subW[1], b0 = addB[0], t0 = subB[0], t1 = subB[1];
        for (let j = 0; j < HID; j++) {
            aw[dst + j] = aw[src + j] + W[a0 + j] - W[s0 + j] - W[s1 + j];
            ab[dst + j] = ab[src + j] + W[b0 + j] - W[t0 + j] - W[t1 + j];
        }
    }
    else {
        const a0 = addW[0], a1 = addW[1], s0 = subW[0], s1 = subW[1];
        const b0 = addB[0], b1 = addB[1], t0 = subB[0], t1 = subB[1];
        for (let j = 0; j < HID; j++) {
            aw[dst + j] = aw[src + j] + W[a0 + j] + W[a1 + j] - W[s0 + j] - W[s1 + j];
            ab[dst + j] = ab[src + j] + W[b0 + j] + W[b1 + j] - W[t0 + j] - W[t1 + j];
        }
    }
}
/** Make slot d (= board.undoStack.length) current, incrementally where possible. Returns d. */
function updateAccumulator(board) {
    const us = board.undoStack;
    const d = us.length;
    if (d >= CAP)
        grow(d);
    if (valid[d] && keyHi[d] === board.zHi && keyLo[d] === board.zLo)
        return d;
    // find nearest valid ancestor k whose key matches the position at depth k
    let k = d - 1;
    const LIMIT = d - 64;
    while (k >= 0 && k > LIMIT) {
        const u = us[k];
        if (valid[k] && keyHi[k] === u.zHi && keyLo[k] === u.zLo)
            break;
        k--;
    }
    if (k < 0 || k <= LIMIT) {
        refresh(board, d);
    }
    else {
        for (let c = k + 1; c <= d; c++) {
            const m = us[c - 1].move;
            applyMove(c, m.from, m.to, m.piece, m.captured, m.promo, m.flags);
            if (c < d) {
                const u = us[c];
                keyHi[c] = u.zHi;
                keyLo[c] = u.zLo;
                valid[c] = 1;
            }
        }
    }
    keyHi[d] = board.zHi;
    keyLo[d] = board.zLo;
    valid[d] = 1;
    return d;
}
/** Side-to-move-relative eval in centipawns. */
function nnueEvaluate(board) {
    const d = updateAccumulator(board);
    const o = d * HID;
    const stm = board.side === 0 ? accW : accB;
    const nst = board.side === 0 ? accB : accW;
    const ow = outW, H = HID;
    let sum = 0;
    for (let j = 0; j < H; j++) {
        let v = stm[o + j];
        v = v < 0 ? 0 : v > QA ? QA : v;
        let x = nst[o + j];
        x = x < 0 ? 0 : x > QA ? QA : x;
        sum += v * ow[j] + x * ow[H + j];
    }
    const v = ((sum + outB) * SCALE / (QA * QB)) | 0;
    // v6: clamp below MATE_BOUND / TT int16 range
    return v > 28000 ? 28000 : v < -28000 ? -28000 : v;
}
/** Testing: full-refresh eval vs incremental slot, returns true if accumulators match. */
function checkAccumulator(board) {
    const d = updateAccumulator(board);
    const tmp = CAP - 1; // use last slot as scratch
    if (d >= tmp)
        return true;
    refresh(board, tmp);
    const a = d * HID, b = tmp * HID;
    for (let j = 0; j < HID; j++)
        if (accW[a + j] !== accW[b + j] || accB[a + j] !== accB[b + j]) {
            valid[tmp] = 0;
            return false;
        }
    valid[tmp] = 0;
    return true;
}
// Default net: $GROKCHESS_NNUE, else <dist>/net.nnue. Missing file -> HCE fallback.
{
    const def = path.resolve(process.env.GROKCHESS_NNUE || path.join(__dirname, '..', 'net.nnue'));
    exports.resolvedDefaultPath = def;
    if (process.env.GROKCHESS_USE_NNUE === '0')
        enabled = false;
    if (fs.existsSync(def))
        loadNet(def);
}
//# sourceMappingURL=nnue.js.map
