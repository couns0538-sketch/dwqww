"use strict";
/** Tactical smoke tests */
Object.defineProperty(exports, "__esModule", { value: true });
const board_1 = require("../board/board");
const search_1 = require("../search/search");
const movegen_1 = require("../move/movegen");
const tt_1 = require("../search/tt");
let pass = 0, fail = 0;
function check(cond, msg) {
    if (cond) {
        pass++;
        console.log(' PASS', msg);
    }
    else {
        fail++;
        console.log(' FAIL', msg);
    }
}
console.log('=== Tactics ===\n');
// Mate in 1
{
    const b = new board_1.Board('6k1/5Q2/6K1/8/8/8/8/8 w - - 0 1');
    const s = new search_1.Search(b);
    let bestScore = 0;
    s.onInfo = (i) => { bestScore = i.score; };
    const m = s.search({ maxDepth: 3 });
    check(!!m && ((0, movegen_1.moveToUci)(m) === 'f7g7' || (0, movegen_1.moveToUci)(m) === 'f7f8' || (0, movegen_1.moveToUci)(m) === 'f7h7' || (0, movegen_1.moveToUci)(m) === 'f7g8'), `mate-in-1 move ${m && (0, movegen_1.moveToUci)(m)} score=${bestScore}`);
    check(bestScore > tt_1.MATE_BOUND, `mate-in-1 score is mate (${bestScore})`);
}
// Mate in 2 (rook)
{
    const b = new board_1.Board('2k5/8/2K5/8/8/8/8/R7 w - - 0 1');
    const s = new search_1.Search(b);
    let bestScore = 0;
    let pv = '';
    s.onInfo = (i) => { bestScore = i.score; pv = i.pv.join(' '); };
    const m = s.search({ maxDepth: 5 });
    check(!!m && (0, movegen_1.moveToUci)(m) === 'a1a8', `mate-in-2 Ra8 ${m && (0, movegen_1.moveToUci)(m)} pv=${pv}`);
    check(bestScore > tt_1.MATE_BOUND, `mate-in-2 score is mate (${bestScore})`);
}
// Hang piece capture
{
    const b = new board_1.Board('4k3/8/8/8/8/8/8/R3K2n w Q - 0 1'); // free knight on h1? h1 is 7, white rook a1 - knight unprotected on h1
    // Better: black knight on a5 unprotected, white can take with something
    const b2 = new board_1.Board('rnbqkbnr/pppppppp/8/8/3N4/8/PPPPPPPP/RNBQKB1R b KQkq - 0 1');
    // White knight on d4 - black can ignore; white left king rook? Skip
    const b3 = new board_1.Board('4k3/8/8/3n4/8/8/8/4K2R w - - 0 1'); // Rh1 can take? no. Rook takes free knight? knight d5, rook h1 doesn't attack
    const b4 = new board_1.Board('4k3/8/8/8/8/8/7n/4K2R w - - 0 1'); // Nh2 hung, Rh2
    const s = new search_1.Search(b4);
    const m = s.search({ maxDepth: 3 });
    check(!!m && (0, movegen_1.moveToUci)(m) === 'h1h2', `capture hung knight ${m && (0, movegen_1.moveToUci)(m)}`);
}
// No crash generating from start
{
    const b = new board_1.Board();
    const n = (0, movegen_1.generateLegalMoves)(b).length;
    check(n === 20, `start legal ${n}`);
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
//# sourceMappingURL=tactics.js.map
