"use strict";
/** Self-play sanity / weak baseline match (fixed depth) */
Object.defineProperty(exports, "__esModule", { value: true });
const board_1 = require("../board/board");
const search_1 = require("../search/search");
const movegen_1 = require("../move/movegen");
const evaluate_1 = require("../eval/evaluate");
/** Random-legal baseline (very weak) */
function randomMove(board) {
    const moves = (0, movegen_1.generateLegalMoves)(board);
    if (!moves.length)
        return null;
    return moves[Math.floor(Math.random() * moves.length)];
}
/** Material-only shallow search baseline */
function materialGreedy(board) {
    const moves = (0, movegen_1.generateLegalMoves)(board);
    if (!moves.length)
        return null;
    let best = moves[0];
    let bestS = -Infinity;
    for (const m of moves) {
        board.makeMove(m);
        // evaluate returns STM perspective; after move it's opponent
        const s = -(0, evaluate_1.evaluate)(board);
        board.unmakeMove();
        // Prefer captures lightly
        const bonus = m.captured ? 50 : 0;
        if (s + bonus > bestS) {
            bestS = s + bonus;
            best = m;
        }
    }
    return best;
}
function playGame(white, black, maxPlies = 200) {
    const board = new board_1.Board(board_1.START_FEN);
    for (let ply = 0; ply < maxPlies; ply++) {
        const moves = (0, movegen_1.generateLegalMoves)(board);
        if (!moves.length) {
            if (board.inCheck())
                return board.side === 0 /* Color.White */ ? '0-1' : '1-0';
            return '1/2-1/2';
        }
        if (board.halfmove >= 100)
            return '1/2-1/2';
        const player = board.side === 0 /* Color.White */ ? white : black;
        const m = player(board);
        if (!m)
            return '1/2-1/2';
        board.makeMove(m);
    }
    return '1/2-1/2';
}
function engineAtDepth(depth) {
    return (board) => {
        const s = new search_1.Search(board);
        return s.search({ maxDepth: depth });
    };
}
console.log('=== Match Harness (sanity, not Elo) ===\n');
const games = parseInt(process.env.GAMES || '10', 10);
const depth = parseInt(process.env.DEPTH || '3', 10);
console.log(`GrokChess depth ${depth} vs Random (${games} games)`);
let w = 0, l = 0, d = 0;
for (let i = 0; i < games; i++) {
    const engineWhite = i % 2 === 0;
    const result = engineWhite
        ? playGame(engineAtDepth(depth), randomMove)
        : playGame(randomMove, engineAtDepth(depth));
    const engineWon = (engineWhite && result === '1-0') || (!engineWhite && result === '0-1');
    const engineLost = (engineWhite && result === '0-1') || (!engineWhite && result === '1-0');
    if (engineWon)
        w++;
    else if (engineLost)
        l++;
    else
        d++;
    process.stdout.write(`  game ${i + 1}: ${result} (engine ${engineWhite ? 'W' : 'B'}) -> ${engineWon ? 'win' : engineLost ? 'loss' : 'draw'}\n`);
}
console.log(`Score: +${w} =${d} -${l} (${((w + d * 0.5) / games * 100).toFixed(0)}%)\n`);
console.log(`GrokChess depth ${depth} vs Material-greedy (${games} games)`);
w = 0;
l = 0;
d = 0;
for (let i = 0; i < games; i++) {
    const engineWhite = i % 2 === 0;
    const result = engineWhite
        ? playGame(engineAtDepth(depth), materialGreedy)
        : playGame(materialGreedy, engineAtDepth(depth));
    const engineWon = (engineWhite && result === '1-0') || (!engineWhite && result === '0-1');
    const engineLost = (engineWhite && result === '0-1') || (!engineWhite && result === '1-0');
    if (engineWon)
        w++;
    else if (engineLost)
        l++;
    else
        d++;
    process.stdout.write(`  game ${i + 1}: ${result} (engine ${engineWhite ? 'W' : 'B'}) -> ${engineWon ? 'win' : engineLost ? 'loss' : 'draw'}\n`);
}
console.log(`Score: +${w} =${d} -${l} (${((w + d * 0.5) / games * 100).toFixed(0)}%)`);
console.log('\nNote: These are sanity checks, NOT FIDE Elo measurements.');
//# sourceMappingURL=match.js.map
