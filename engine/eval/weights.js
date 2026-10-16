"use strict";
/** Tunable evaluation weights — v1.2.1 closer to v1.1 proven set */
Object.defineProperty(exports, "__esModule", { value: true });
exports.W = exports.PHASE_WT = exports.MAT_EG = exports.MAT_MG = void 0;
exports.MAT_MG = [0, 82, 305, 311, 390, 1004, 0];
exports.MAT_EG = [0, 94, 271, 276, 487, 917, 0];
exports.PHASE_WT = [0, 0, 1, 1, 2, 4, 0];
exports.W = {
    bishopPairMg: 20,
    bishopPairEg: 54,
    doubledMg: 22,
    doubledEg: 23,
    isolatedMg: 16,
    isolatedEg: 21,
    connectedMg: 0,
    connectedEg: 3,
    tempo: 19,
    mobNMg: 3,
    mobNEg: 5,
    mobBMg: 6,
    mobBEg: 7,
    mobRMg: 6,
    mobREg: 5,
    mobQMg: 2,
    mobQEg: 0,
    rookOpenMg: 38,
    rookOpenEg: 7,
    rookSemiMg: 23,
    rookSemiEg: 7,
    rook7thMg: 23,
    rook7thEg: 27,
    shelterNear: 19,
    shelterFar: 10,
    openFileNearKing: 28,
    attackUnit: 14,
    attackCap: 220,
    spacePerSq: 10,
    knightOutpostMg: 20,
    knightOutpostEg: 15,
    // Previously hard-coded in evaluate.ts (identical defaults): passed-pawn bonus by relative rank 2..7 (index = rank-1)
    passedMg1: 0, passedMg2: 0, passedMg3: 1, passedMg4: 20, passedMg5: 54, passedMg6: 74,
    passedEg1: 14, passedEg2: 23, passedEg3: 37, passedEg4: 53, passedEg5: 80, passedEg6: 93,
    // minor-piece imbalance bonus (more minors with >= pawns)
    imbalanceMg: 0,
    imbalanceEg: 0,
    // --- eval5-A: safe-square mobility (squares not attacked by enemy pawns, centred by baseline) + cramped penalty (default 0 = neutral) ---
    safeMobNMg: 0, safeMobNEg: 0, crampedNMg: 0, crampedNEg: 0,
    safeMobBMg: 0, safeMobBEg: 0, crampedBMg: 0, crampedBEg: 0,
    safeMobRMg: 0, safeMobREg: 0, crampedRMg: 0, crampedREg: 0,
    safeMobQMg: 0, safeMobQEg: 0, crampedQMg: 0, crampedQEg: 0,
};
//# sourceMappingURL=weights.js.map
