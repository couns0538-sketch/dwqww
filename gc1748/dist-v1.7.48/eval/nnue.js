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
// screlu2-1745 (undofast): updateAccumulator hard-codes the board undo layout (stride 12, zHi@9, zLo@10).
{
    const b_ = require("../board/board");
    if (b_.U_STRIDE !== 12 || b_.U_ZHI !== 9 || b_.U_ZLO !== 10)
        throw new Error(`nnue.js: board undo layout changed (U_STRIDE=${b_.U_STRIDE}, U_ZHI=${b_.U_ZHI}, U_ZLO=${b_.U_ZLO}; expected 12/9/10) - update updateAccumulator offsets`);
}
let HID = 128;
function hiddenSize() { return HID; }
const NFEAT = 768;
const QA = 255, QB = 64, SCALE = 400;
const MAGIC = 0x4E4E4B47;
let ftW = new Int16Array(NFEAT * HID);
let ftB = new Int16Array(HID);
let outW = new Int16Array(2 * HID);

let outB = 0;
// screlu-1743: GKNN v3 header (act flag + NB output buckets). v1 path unchanged (NBK=1, ACT=0).
let NBK = 1; // output buckets
let BKDIV = 32; // screlu2ob8-1745: bucket divisor = floor(32/NB)
let ACT = 0; // 0 = CReLU, 1 = SCReLU
let outBs = new Int32Array(1); // per-bucket outB (v3)
let wasmFwdSc = null;
function popc32(x) { x = x - ((x >>> 1) & 0x55555555); x = (x & 0x33333333) + ((x >>> 2) & 0x33333333); return (((x + (x >>> 4)) & 0x0F0F0F0F) * 0x01010101) >>> 24; }
// nnsimd2-1741: WASM SIMD forward + SIMD accumulator delta (i16x8); ftW+acc+outW in WASM memory.
// Fallback to lock scalar loops if SIMD unavailable, GROKCHESS_NNUE_SIMD=0, H%8!=0, or overflow gate fails.
let simdWanted = process.env.GROKCHESS_NNUE_SIMD !== '0';
let simdReady = false; // module + memory bound
let simdActive = false; // used for forward this net
let simdSumFit = false; // overflow gate
let wasmMem = null, wasmFwd = null, wasmUpd11x2 = null, wasmUpd12x2 = null, wasmUpd22x2 = null;
let accWOff = 0, accBOff = 0, outWOff = 0, ftWOff = 0; // byte offsets into wasmMem
const WASM_PAGE = 65536;
// Embedded kernel (also shipped as nnue_fwd.wasm next to this file for cp -rp / Windows Node)
const NNUE_FWD_WASM_B64 = 'AGFzbQEAAAABVghgBH9/f38Bf2AFf39/f38AYAZ/f39/f38AYAd/f39/f39/AGAJf39/f39/f39/AGALf39/f39/f39/f38AYA1/f39/f39/f39/f39/AGAEf39/fwF8AwkIAAECAwQFBgcFAwEAAQYHAX8BQf8BCwdPCQZtZW1vcnkCAANmd2QAAAV1cGQxMQABBXVwZDEyAAIFdXBkMjIAAwd1cGQxMXgyAAQHdXBkMTJ4MgAFB3VwZDIyeDIABgZmd2Rfc2MABwrJBwjQAQICfwd7IwD9ECEG/QwAAAAAAAAAAAAAAAAAAAAAIQf9DAAAAAAAAAAAAAAAAAAAAAAhDEEAIQQCQANAIAQgA08NASAGIAcgACAEQQF0av0ABAD9mAH9lgEhCCAGIAcgASAEQQF0av0ABAD9mAH9lgEhCSACIARBAXRq/QAEACEKIAIgAyAEakEBdGr9AAQAIQsgDCAIIAr9ugEgCSAL/boB/a4B/a4BIQwgBEEIaiEEDAALCyAM/RsAIAz9GwFqIAz9GwIgDP0bA2pqIQUgBQtaAgF/AXtBACEFAkADQCAFIARPDQEgASAFQQF0av0ABAAgAiAFQQF0av0ABAD9jgEgAyAFQQF0av0ABAD9kQEhBiAAIAVBAXRqIAb9CwQAIAVBCGohBQwACwsLaQIBfwF7QQAhBgJAA0AgBiAFTw0BIAEgBkEBdGr9AAQAIAIgBkEBdGr9AAQA/Y4BIAMgBkEBdGr9AAQA/ZEBIAQgBkEBdGr9AAQA/ZEBIQcgACAGQQF0aiAH/QsEACAGQQhqIQYMAAsLC3gCAX8Be0EAIQcCQANAIAcgBk8NASABIAdBAXRq/QAEACACIAdBAXRq/QAEAP2OASADIAdBAXRq/QAEAP2OASAEIAdBAXRq/QAEAP2RASAFIAdBAXRq/QAEAP2RASEIIAAgB0EBdGogCP0LBAAgB0EIaiEHDAALCwsaACAAIAEgBCAFIAgQASACIAMgBiAHIAgQAQseACAAIAEgBCAFIAYgChACIAIgAyAHIAggCSAKEAILIgAgACABIAQgBSAGIAcgDBADIAIgAyAIIAkgCiALIAwQAwvZAgIBfwh7IwD9ECEF/QwAAAAAAAAAAAAAAAAAAAAAIQb9DAAAAAAAAAAAAAAAAAAAAAAhB0EAIQQCQANAIAQgA08NASAFIAYgACAEQQF0av0ABAD9mAH9lgEhCCACIARBAXRq/QAEACEJIAj9pwEhCyAI/agBIQwgCyAL/bUBIAn9pwH9tQEhCiAHIAr9xwEgCv3IAf3OAf3OASEHIAwgDP21ASAJ/agB/bUBIQogByAK/ccBIAr9yAH9zgH9zgEhByAFIAYgASAEQQF0av0ABAD9mAH9lgEhCCACIAMgBGpBAXRq/QAEACEJIAj9pwEhCyAI/agBIQwgCyAL/bUBIAn9pwH9tQEhCiAHIAr9xwEgCv3IAf3OAf3OASEHIAwgDP21ASAJ/agB/bUBIQogByAK/ccBIAr9yAH9zgH9zgEhByAEQQhqIQQMAAsLIAf9HQAgB/0dAXy5Cw==';
function wasmBytes() {
    try {
        const p = path.join(__dirname, 'nnue_fwd.wasm');
        if (fs.existsSync(p)) return fs.readFileSync(p);
    } catch (_) {}
    return Buffer.from(NNUE_FWD_WASM_B64, 'base64');
}
function initWasm() {
    if (!simdWanted) { simdReady = false; return; }
    try {
        const buf = wasmBytes();
        if (!WebAssembly.validate(buf)) { simdReady = false; return; }
        const mod = new WebAssembly.Module(buf);
        const inst = new WebAssembly.Instance(mod, {});
        // Module exports its own memory; grow for ftW+acc+outW (H=128 CAP=1024 ~721KiB -> 16+ pages)
        wasmMem = inst.exports.memory;
        wasmFwd = inst.exports.fwd;
        wasmUpd11x2 = inst.exports.upd11x2;
        wasmUpd12x2 = inst.exports.upd12x2;
        wasmUpd22x2 = inst.exports.upd22x2;
        wasmFwdSc = typeof inst.exports.fwd_sc === 'function' ? inst.exports.fwd_sc : null;
        const needPages = 24;
        const have = wasmMem.buffer.byteLength / WASM_PAGE;
        if (have < needPages) wasmMem.grow(needPages - have);
        simdReady = typeof wasmFwd === 'function' && typeof wasmUpd11x2 === 'function';
    } catch (e) {
        simdReady = false;
        wasmMem = null;
        wasmFwd = null;
        wasmUpd11x2 = wasmUpd12x2 = wasmUpd22x2 = null;
    }
}
function layoutOffs() {
    // Fixed: ftW[NFEAT*HID], outW[2*HID]; Growing: accW[CAP*HID], accB[CAP*HID]
    ftWOff = 0;
    outWOff = NFEAT * HID * 2;
    accWOff = outWOff + NBK * 2 * HID * 2;
    accBOff = accWOff + CAP * HID * 2;
}
function ensureWasmCapacity() {
    if (!wasmMem) return false;
    layoutOffs();
    const need = accBOff + CAP * HID * 2 + 64;
    const have = wasmMem.buffer.byteLength;
    if (need > have) {
        const add = Math.ceil((need - have) / WASM_PAGE);
        wasmMem.grow(add);
    }
    return true;
}
function bindAccViews() {
    if (!wasmMem) {
        accW = new Int16Array(CAP * HID);
        accB = new Int16Array(CAP * HID);
        // ftW/outW kept as their own buffers when no wasm
        return;
    }
    layoutOffs();
    const buf = wasmMem.buffer;
    ftW = new Int16Array(buf, ftWOff, NFEAT * HID);
    outW = new Int16Array(buf, outWOff, NBK * 2 * HID);
    accW = new Int16Array(buf, accWOff, CAP * HID);
    accB = new Int16Array(buf, accBOff, CAP * HID);
}
initWasm();
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
    if (simdReady) ensureWasmCapacity();
    bindAccViews();
    keyHi = new Int32Array(CAP);
    keyLo = new Int32Array(CAP);
    valid = new Uint8Array(CAP);
}
let CAP = 1024;
let accW; let accB;
if (simdReady) ensureWasmCapacity();
bindAccViews();
let keyHi = new Int32Array(CAP);
let keyLo = new Int32Array(CAP);
let valid = new Uint8Array(CAP);
function grow(need) {
    let n = CAP;
    while (n <= need)
        n *= 2;
    // snapshot BEFORE memory.grow (TypedArray views detach on grow)
    const snapW = new Int16Array(accW);
    const snapB = new Int16Array(accB);
    CAP = n;
    if (simdReady) ensureWasmCapacity();
    bindAccViews();
    accW.set(snapW);
    accB.set(snapB);
    const kh = new Int32Array(n);
    kh.set(keyHi);
    keyHi = kh;
    const kl = new Int32Array(n);
    kl.set(keyLo);
    keyLo = kl;
    const v = new Uint8Array(n);
    v.set(valid);
    valid = v;
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
        if (buf.byteLength < 12 || dv.getUint32(0, true) !== MAGIC)
            return false;
        const ver = dv.getUint32(4, true);
        if (ver !== 1 && ver !== 2 && ver !== 3)
            return false;
        const H = dv.getUint32(8, true);
        let nb = 1, act = 0, o = 12;
        if (ver === 1) {
            if (H < 8 || H > 1024 || buf.byteLength !== 12 + (NFEAT * H + H + 2 * H) * 2 + 4)
                return false;
        }
        else if (ver === 2) {
            // screlu2-1743: v2 (live bucket nets): magic, 2, H, NB; payload as v3; act = 0 (CReLU); NB must divide 32 (as v6 loader)
            if (buf.byteLength < 16)
                return false;
            nb = dv.getUint32(12, true);
            if (H < 8 || H > 1024 || nb < 1 || nb > 32 || (32 % nb) !== 0 || buf.byteLength !== 16 + 2 * NFEAT * H + 2 * H + 4 * nb * H + 4 * nb)
                return false;
            o = 16;
        }
        else {
            // v3: magic, 3, H, NB, act; payload ftW[768H] ftB[H] outW[NB*2H] i16, outB[NB] i32
            if (buf.byteLength < 20)
                return false;
            nb = dv.getUint32(12, true);
            act = dv.getUint32(16, true);
            if (act !== 0 && act !== 1) { lastError = `unknown act ${act}`; return false; }
            if (H < 8 || H > 1024 || nb < 1 || nb > 32 || buf.byteLength !== 20 + 2 * NFEAT * H + 2 * H + 4 * nb * H + 4 * nb)
                return false;
            o = 20;
        }
        const rd = (a) => { for (let i = 0; i < a.length; i++, o += 2)
            a[i] = dv.getInt16(o, true); };
        const w = new Int16Array(NFEAT * H), b = new Int16Array(H), ow = new Int16Array(nb * 2 * H);
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
        ftB = b;
        const obs = new Int32Array(nb);
        for (let i = 0; i < nb; i++, o += 4)
            obs[i] = dv.getInt32(o, true);
        outBs = obs;
        outB = obs[0];
        // nnsimd: Int32/SIMD forward only when every partial sum provably fits int32 (exact => bit-identical)
        let mx = 0;
        for (let j = 0; j < ow.length; j++) { const a = ow[j] < 0 ? -ow[j] : ow[j]; if (a > mx) mx = a; }
        simdSumFit = 2 * H * QA * mx < 2147483647;
        NBK = nb;
        BKDIV = Math.max(1, (32 / nb) | 0); // trainer: 32 // NB
        ACT = act;
        if (H !== HID) {
            HID = H;
            buildTables();
            allocAcc();
        } else if (simdReady) {
            ensureWasmCapacity();
            bindAccViews();
        }
        // copy ftW + outW into WASM-backed views (or plain heap buffers if no wasm)
        if (!simdReady) {
            ftW = w;
            outW = new Int16Array(ow.length);
            outW.set(ow);
        } else {
            if (ftW.length !== w.length || outW.length !== ow.length) { ensureWasmCapacity(); bindAccViews(); }
            ftW.set(w);
            outW.set(ow);
        }
        // SCReLU forward needs fwd_sc (exact i64 lanes, no int32 sum gate)
        simdActive = simdReady && simdWanted && (H & 7) === 0 && (act === 1 ? wasmFwdSc !== null : simdSumFit);
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
function nnueInfo() { return (lastError ? `last EvalFile load failed (${lastError}); ` : '') + (loaded ? `NNUE ${enabled ? 'on' : 'off'} file ${loadedPath} simd ${simdActive ? 'on' : 'off'}` : 'NNUE no net loaded (HCE)'); }
function nnueSimdActive() { return simdActive; }
exports.nnueSimdActive = nnueSimdActive;
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
    // nnsimd2: run delta in WASM (i16x8 wrap = Int16Array store) when SIMD active; else JS loops
    if (simdActive) {
        const dW = accWOff + dst * 2, sW = accWOff + src * 2;
        const dB = accBOff + dst * 2, sB = accBOff + src * 2;
        const H = HID;
        if (na === 1 && ns === 1) {
            wasmUpd11x2(dW, sW, dB, sB,
                ftWOff + addW[0] * 2, ftWOff + subW[0] * 2,
                ftWOff + addB[0] * 2, ftWOff + subB[0] * 2, H);
        } else if (na === 1) {
            wasmUpd12x2(dW, sW, dB, sB,
                ftWOff + addW[0] * 2, ftWOff + subW[0] * 2, ftWOff + subW[1] * 2,
                ftWOff + addB[0] * 2, ftWOff + subB[0] * 2, ftWOff + subB[1] * 2, H);
        } else {
            wasmUpd22x2(dW, sW, dB, sB,
                ftWOff + addW[0] * 2, ftWOff + addW[1] * 2, ftWOff + subW[0] * 2, ftWOff + subW[1] * 2,
                ftWOff + addB[0] * 2, ftWOff + addB[1] * 2, ftWOff + subB[0] * 2, ftWOff + subB[1] * 2, H);
        }
        return;
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
    // undofast: read the flat undo buffer directly (undoStack getter allocates); stride 12, ZHI=9, ZLO=10
    const ub = board.undoBuf;
    const d = board.undoTop;
    if (d >= CAP)
        grow(d);
    if (valid[d] && keyHi[d] === board.zHi && keyLo[d] === board.zLo)
        return d;
    // find nearest valid ancestor k whose key matches the position at depth k
    let k = d - 1;
    const LIMIT = d - 64;
    while (k >= 0 && k > LIMIT) {
        const t = k * 12;
        if (valid[k] && keyHi[k] === ub[t + 9] && keyLo[k] === ub[t + 10])
            break;
        k--;
    }
    if (k < 0 || k <= LIMIT) {
        refresh(board, d);
    }
    else {
        for (let c = k + 1; c <= d; c++) {
            const t = (c - 1) * 12;
            applyMove(c, ub[t], ub[t + 1], ub[t + 2], ub[t + 3], ub[t + 4], ub[t + 5]);
            if (c < d) {
                const t2 = c * 12;
                keyHi[c] = ub[t2 + 9];
                keyLo[c] = ub[t2 + 10];
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
    let bk = 0;
    if (NBK > 1) {
        // screlu2ob8-1745: output bucket = min(NB-1, (pieces-2) / (32/NB)), pieces incl. kings (= train_ob.py; NB=8 -> (pc-2)>>2)
        const oc = board.occupied;
        bk = ((popc32(oc.lo | 0) + popc32(oc.hi | 0) - 2) / BKDIV) | 0;
        bk = bk < 0 ? 0 : bk >= NBK ? NBK - 1 : bk;
    }
    if (ACT === 1) {
        const ob = bk * 2 * H;
        if (simdActive) {
            const stmOff = (board.side === 0 ? accWOff : accBOff) + o * 2;
            const nstOff = (board.side === 0 ? accBOff : accWOff) + o * 2;
            sum = wasmFwdSc(stmOff, nstOff, outWOff + ob * 2, H);
        }
        else {
            // exact in JS Number: |sum| <= 2*1024*65025*32768 < 2^53
            for (let j = 0; j < H; j++) {
                let v = stm[o + j];
                v = v < 0 ? 0 : v > QA ? QA : v;
                let x = nst[o + j];
                x = x < 0 ? 0 : x > QA ? QA : x;
                sum += v * v * ow[ob + j] + x * x * ow[ob + H + j];
            }
        }
        // (sum + outB*QA)*SCALE < 2^53; quotient distance-to-integer >= 1/(QA*QA*QB) >> fp error, so trunc is exact
        const e = Math.trunc(((sum + outBs[bk] * QA) * SCALE) / (QA * QA * QB));
        return e > 28000 ? 28000 : e < -28000 ? -28000 : e;
    }
    if (NBK > 1) {
        const ob = bk * 2 * H;
        for (let j = 0; j < H; j++) {
            let v = stm[o + j];
            v = v < 0 ? 0 : v > QA ? QA : v;
            let x = nst[o + j];
            x = x < 0 ? 0 : x > QA ? QA : x;
            sum += v * ow[ob + j] + x * ow[ob + H + j];
        }
        const e = ((sum + outBs[bk]) * SCALE / (QA * QB)) | 0;
        return e > 28000 ? 28000 : e < -28000 ? -28000 : e;
    }
    if (simdActive) {
        // zero-copy: stm/nst/outW are views on wasmMem; pass byte offsets
        const stmOff = (board.side === 0 ? accWOff : accBOff) + o * 2;
        const nstOff = (board.side === 0 ? accBOff : accWOff) + o * 2;
        sum = wasmFwd(stmOff, nstOff, outWOff, H);
    }
    else {
        for (let j = 0; j < H; j++) {
            let v = stm[o + j];
            v = v < 0 ? 0 : v > QA ? QA : v;
            let x = nst[o + j];
            x = x < 0 ? 0 : x > QA ? QA : x;
            sum += v * ow[j] + x * ow[H + j];
        }
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
// nnsimd2-1741 startup path line (UCI-safe info string)
try { console.log('info string nnue simd ' + (simdActive ? 'on' : 'off')); } catch (_) {}
//# sourceMappingURL=nnue.js.map
