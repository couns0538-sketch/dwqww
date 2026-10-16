"use strict";
/** Unit tests for move generation legality */
Object.defineProperty(exports, "__esModule", { value: true });
const board_1 = require("../board/board");
const movegen_1 = require("../move/movegen");
const types_1 = require("../board/types");
const evaluate_1 = require("../eval/evaluate");
let passed = 0;
let failed = 0;
function assert(cond, msg) {
    if (cond) {
        passed++;
        console.log(`  PASS: ${msg}`);
    }
    else {
        failed++;
        console.log(`  FAIL: ${msg}`);
    }
}
console.log('=== Move Generation Unit Tests ===\n');
{
    console.log('Start position legality');
    const b = new board_1.Board(board_1.START_FEN);
    const legal = (0, movegen_1.generateLegalMoves)(b);
    assert(legal.length === 20, `start has 20 legal moves (got ${legal.length})`);
    const ucis = new Set(legal.map(movegen_1.moveToUci));
    assert(ucis.has('e2e4'), 'e2e4 is legal');
    assert(ucis.has('g1f3'), 'g1f3 is legal');
    assert(!ucis.has('e2e5'), 'e2e5 is illegal');
}
{
    console.log('\nCastling');
    const b = new board_1.Board('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');
    const legal = (0, movegen_1.generateLegalMoves)(b);
    const ucis = legal.map(movegen_1.moveToUci);
    assert(ucis.includes('e1g1'), 'White O-O legal');
    assert(ucis.includes('e1c1'), 'White O-O-O legal');
    const castleMoves = legal.filter(m => m.flags & types_1.MOVE_CASTLE);
    assert(castleMoves.length === 2, `2 castling moves (got ${castleMoves.length})`);
    const oo = legal.find(m => m.from === 4 && m.to === 6 && (m.flags & types_1.MOVE_CASTLE));
    b.makeMove(oo);
    assert(b.squares[5] === 4 /* Piece.WR */, 'rook on f1 after O-O');
    assert(b.squares[6] === 6 /* Piece.WK */, 'king on g1 after O-O');
    assert(b.squares[7] === 0 /* Piece.None */, 'h1 empty after O-O');
    assert(b.squares[4] === 0 /* Piece.None */, 'e1 empty after O-O');
    b.unmakeMove();
    assert(b.squares[4] === 6 /* Piece.WK */, 'king restored on e1');
    assert(b.squares[7] === 4 /* Piece.WR */, 'rook restored on h1');
}
{
    console.log('\nCastling through check');
    const b3 = new board_1.Board('4k3/8/8/8/8/5r2/8/R3K2R w KQ - 0 1');
    const legal = (0, movegen_1.generateLegalMoves)(b3);
    const ucis = legal.map(movegen_1.moveToUci);
    assert(!ucis.includes('e1g1'), 'O-O illegal when f1 attacked');
}
{
    console.log('\nEn passant');
    const b = new board_1.Board('rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3');
    const legal = (0, movegen_1.generateLegalMoves)(b);
    const ep = legal.filter(m => m.flags & types_1.MOVE_ENPASSANT);
    assert(ep.length === 1, `1 en passant move (got ${ep.length})`);
    assert((0, movegen_1.moveToUci)(ep[0]) === 'e5f6', 'EP is e5f6');
    b.makeMove(ep[0]);
    assert(b.squares[37] === 0 /* Piece.None */, 'pawn on f5 gone');
    assert(b.squares[45] === 1 /* Piece.WP */, 'white pawn on f6');
    b.unmakeMove();
    assert(b.squares[37] === 7 /* Piece.BP */, 'EP capture restored');
    assert(b.squares[36] === 1 /* Piece.WP */, 'white pawn back on e5');
}
{
    console.log('\nPromotion');
    const b = new board_1.Board('8/P7/8/8/8/8/8/4K2k w - - 0 1');
    const legal = (0, movegen_1.generateLegalMoves)(b);
    const promos = legal.filter(m => m.from === 48 && m.to === 56);
    assert(promos.length === 4, `4 promotions a7a8 (got ${promos.length})`);
    const types = new Set(promos.map(m => m.promo));
    assert(types.has(5 /* Piece.WQ */) && types.has(4 /* Piece.WR */) && types.has(3 /* Piece.WB */) && types.has(2 /* Piece.WN */), 'QRBN promos');
}
{
    console.log('\nZobrist make/unmake');
    const b = new board_1.Board(board_1.START_FEN);
    const z0 = b.zobrist;
    const moves = (0, movegen_1.generateLegalMoves)(b);
    for (const m of moves) {
        b.makeMove(m);
        b.unmakeMove();
    }
    assert(b.zobrist === z0, 'zobrist restored after all make/unmake');
    assert(b.getFen() === board_1.START_FEN, 'FEN restored');
}
{
    console.log('\nParse UCI');
    const b = new board_1.Board(board_1.START_FEN);
    const m = (0, movegen_1.parseUciMove)(b, 'e2e4');
    assert(m !== null && m.from === 12 && m.to === 28, 'parse e2e4');
    assert((0, movegen_1.parseUciMove)(b, 'e2e5') === null, 'reject illegal e2e5');
}
{
    console.log('\nEval basics');
    const b = new board_1.Board(board_1.START_FEN);
    const e = (0, evaluate_1.evaluate)(b);
    assert(Math.abs(e) < 80, `start eval near 0 (got ${e})`);
}
{
    console.log('\nCheck detection');
    const b = new board_1.Board('4k3/8/8/8/8/8/4R3/4K3 b - - 0 1');
    assert(b.inCheck(), 'black in check from rook');
    const legal = (0, movegen_1.generateLegalMoves)(b);
    for (const m of legal) {
        b.makeMove(m);
        assert(!b.inCheck(1 /* Color.Black */), `after ${(0, movegen_1.moveToUci)(m)} black not in check`);
        b.unmakeMove();
    }
}
{
    console.log('\nFEN roundtrip');
    const fens = [
        board_1.START_FEN,
        'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
        '8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
    ];
    for (const f of fens) {
        const b = new board_1.Board(f);
        assert(b.getFen() === f, `FEN roundtrip: ${f.slice(0, 30)}...`);
    }
}
{
    console.log('\nPinned piece cannot leave pin');
    // White king e1, white knight e2, black rook e8 — knight pinned
    const b = new board_1.Board('4r3/8/8/8/8/8/4N3/4K3 w - - 0 1');
    const legal = (0, movegen_1.generateLegalMoves)(b);
    const knightMoves = legal.filter(m => m.from === 12);
    assert(knightMoves.length === 0, `pinned knight has no moves (got ${knightMoves.length})`);
}
console.log(`\nResults: ${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
//# sourceMappingURL=movegen.test.js.map
