"use strict";
/** Incremental material + PST scoring */
Object.defineProperty(exports, "__esModule", { value: true });
exports.putPhase = exports.putEg = exports.putMg = void 0;
exports.scorePut = scorePut;
exports.scoreRemove = scoreRemove;
const types_1 = require("../board/types");
const pst_1 = require("./pst");
const weights_1 = require("./weights");
/** White-relative delta when placing piece on square s */
function scorePut(piece, s) {
    const pt = (0, types_1.pieceType)(piece);
    const white = (0, types_1.isWhite)(piece);
    const sq = white ? s : (0, pst_1.flipSq)(s);
    const sign = white ? 1 : -1;
    return {
        mg: sign * (weights_1.MAT_MG[pt] + pst_1.MG_TABLES[pt][sq]),
        eg: sign * (weights_1.MAT_EG[pt] + pst_1.EG_TABLES[pt][sq]),
        phase: weights_1.PHASE_WT[pt],
    };
}
function scoreRemove(piece, s) {
    const d = scorePut(piece, s);
    return { mg: -d.mg, eg: -d.eg, phase: -d.phase };
}
// allocation-free helpers (same values as scorePut): index into flat tables
const _MG = [], _EG = [];
for (let p = 1; p <= 12; p++) {
    const mg = new Int32Array(64), eg = new Int32Array(64);
    for (let s = 0; s < 64; s++) {
        const d = scorePut(p, s);
        mg[s] = d.mg;
        eg[s] = d.eg;
    }
    _MG[p] = mg;
    _EG[p] = eg;
}
const _PH = new Int32Array(13);
for (let p = 1; p <= 12; p++)
    _PH[p] = scorePut(p, 0).phase;
const putMg = (p, s) => _MG[p][s];
exports.putMg = putMg;
const putEg = (p, s) => _EG[p][s];
exports.putEg = putEg;
const putPhase = (p) => _PH[p];
exports.putPhase = putPhase;
//# sourceMappingURL=incremental.js.map
