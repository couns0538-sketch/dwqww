"use strict";
/** Perft tests against known positions */
Object.defineProperty(exports, "__esModule", { value: true });
const board_1 = require("../board/board");
const movegen_1 = require("../move/movegen");
const CASES = [
    {
        name: 'Start Position',
        fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
        depths: [
            { depth: 1, nodes: 20 },
            { depth: 2, nodes: 400 },
            { depth: 3, nodes: 8902 },
            { depth: 4, nodes: 197281 },
            { depth: 5, nodes: 4865609 },
        ],
    },
    {
        name: 'Kiwipete',
        fen: 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
        depths: [
            { depth: 1, nodes: 48 },
            { depth: 2, nodes: 2039 },
            { depth: 3, nodes: 97862 },
            { depth: 4, nodes: 4085603 },
        ],
    },
    {
        name: 'Position 3 (CPW)',
        fen: '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
        depths: [
            { depth: 1, nodes: 14 },
            { depth: 2, nodes: 191 },
            { depth: 3, nodes: 2812 },
            { depth: 4, nodes: 43238 },
            { depth: 5, nodes: 674624 },
        ],
    },
    {
        name: 'Position 4 (CPW)',
        fen: 'r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1',
        depths: [
            { depth: 1, nodes: 6 },
            { depth: 2, nodes: 264 },
            { depth: 3, nodes: 9467 },
            { depth: 4, nodes: 422333 },
        ],
    },
    {
        name: 'Position 5 (CPW)',
        fen: 'rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8',
        depths: [
            { depth: 1, nodes: 44 },
            { depth: 2, nodes: 1486 },
            { depth: 3, nodes: 62379 },
            { depth: 4, nodes: 2103487 },
        ],
    },
    {
        name: 'Position 6 (CPW)',
        fen: 'r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10',
        depths: [
            { depth: 1, nodes: 46 },
            { depth: 2, nodes: 2079 },
            { depth: 3, nodes: 89890 },
        ],
    },
];
let passed = 0;
let failed = 0;
console.log('=== Perft Tests ===\n');
for (const c of CASES) {
    console.log(`--- ${c.name} ---`);
    console.log(`FEN: ${c.fen}`);
    const board = new board_1.Board(c.fen);
    for (const { depth, nodes: expected } of c.depths) {
        // Skip very deep tests if env FAST=1
        if (process.env.FAST === '1' && expected > 500000) {
            console.log(`  depth ${depth}: SKIPPED (FAST)`);
            continue;
        }
        const start = Date.now();
        const got = (0, movegen_1.perft)(board, depth);
        const ms = Date.now() - start;
        const ok = got === expected;
        if (ok) {
            passed++;
            console.log(`  depth ${depth}: ${got} OK (${ms}ms)`);
        }
        else {
            failed++;
            console.log(`  depth ${depth}: FAIL got ${got} expected ${expected} (${ms}ms)`);
        }
    }
    console.log('');
}
console.log(`Results: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
//# sourceMappingURL=perft.test.js.map
