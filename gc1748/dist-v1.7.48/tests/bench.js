"use strict";
/** Benchmark: NPS and search depth */
Object.defineProperty(exports, "__esModule", { value: true });
const board_1 = require("../board/board");
const search_1 = require("../search/search");
const movegen_1 = require("../move/movegen");
console.log('=== GrokChess Benchmark ===\n');
const board = new board_1.Board(board_1.START_FEN);
console.log('Perft speed:');
for (const d of [4, 5]) {
    const t0 = Date.now();
    const n = (0, movegen_1.perft)(board, d);
    const ms = Math.max(1, Date.now() - t0);
    console.log(`  perft(${d}) = ${n} in ${ms}ms (${Math.floor((n / ms) * 1000)} nps)`);
}
console.log('\nSearch (startpos, depth 7):');
const search = new search_1.Search(board);
search.onInfo = (info) => {
    console.log(`  depth ${info.depth} score ${info.score} nodes ${info.nodes} nps ${info.nps} pv ${info.pv.join(' ')}`);
};
const t0 = Date.now();
const best = search.search({ maxDepth: 7 });
console.log(`Best: ${best ? (0, movegen_1.moveToUci)(best) : 'none'} in ${Date.now() - t0}ms`);
console.log('\nSearch (Kiwipete, depth 6):');
const k = new board_1.Board('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1');
const s2 = new search_1.Search(k);
s2.onInfo = (info) => {
    console.log(`  depth ${info.depth} score ${info.score} nodes ${info.nodes} nps ${info.nps} pv ${info.pv.join(' ')}`);
};
const best2 = s2.search({ maxDepth: 6 });
console.log(`Best: ${best2 ? (0, movegen_1.moveToUci)(best2) : 'none'}`);
console.log('\nMate in 1:');
const mate1 = new board_1.Board('6k1/5Q2/6K1/8/8/8/8/8 w - - 0 1');
const s5 = new search_1.Search(mate1);
const bm5 = s5.search({ maxDepth: 3 });
console.log(`Best: ${bm5 ? (0, movegen_1.moveToUci)(bm5) : 'none'}`);
//# sourceMappingURL=bench.js.map
