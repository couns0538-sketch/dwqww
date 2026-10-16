#!/usr/bin/env node
"use strict";
/** Simple CLI: play a move from FEN, perft, eval, interactive */
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
const board_1 = require("../board/board");
const search_1 = require("../search/search");
const movegen_1 = require("../move/movegen");
const evaluate_1 = require("../eval/evaluate");
const tt_1 = require("../search/tt");
function usage() {
    console.log(`GrokChess CLI

Usage:
  node dist/cli/main.js move [--fen FEN] [--depth N] [--time MS]
  node dist/cli/main.js perft [--fen FEN] [--depth N]
  node dist/cli/main.js eval [--fen FEN]
  node dist/cli/main.js legal [--fen FEN]
  node dist/cli/main.js play [--fen FEN] [--depth N]   # interactive human vs engine

Examples:
  npm run cli -- move --depth 6
  npm run cli -- move --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1" --time 2000
  npm run cli -- perft --depth 5
`);
}
function parseArgs(argv) {
    const out = { _: '' };
    const positional = [];
    for (let i = 0; i < argv.length; i++) {
        if (argv[i].startsWith('--')) {
            const key = argv[i].slice(2);
            out[key] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : 'true';
        }
        else {
            positional.push(argv[i]);
        }
    }
    out._ = positional[0] || '';
    if (positional[1])
        out._2 = positional[1];
    return out;
}
function formatScore(s) {
    if (Math.abs(s) > tt_1.MATE_BOUND) {
        const mateIn = s > 0 ? Math.ceil((30000 - s) / 2) : -Math.ceil((30000 + s) / 2);
        return `M${mateIn}`;
    }
    return (s / 100).toFixed(2);
}
async function main() {
    const args = parseArgs(process.argv.slice(2));
    const cmd = args._;
    const fen = args.fen || board_1.START_FEN;
    const board = new board_1.Board(fen);
    if (!cmd || cmd === 'help') {
        usage();
        return;
    }
    if (cmd === 'move') {
        const depth = parseInt(args.depth || '0', 10);
        const time = parseInt(args.time || '0', 10);
        const search = new search_1.Search(board);
        search.onInfo = (info) => {
            console.error(`depth ${info.depth} score ${formatScore(info.score)} nodes ${info.nodes} nps ${info.nps} pv ${info.pv.join(' ')}`);
        };
        const limits = depth > 0
            ? { maxDepth: depth }
            : { moveTime: time > 0 ? time : 2000 };
        const best = search.search(limits);
        if (!best) {
            console.log('none');
            process.exit(1);
        }
        console.log((0, movegen_1.moveToUci)(best));
        board.makeMove(best);
        console.error(`fen ${board.getFen()}`);
        console.error(`eval ${formatScore((0, evaluate_1.evaluate)(board))}`);
        return;
    }
    if (cmd === 'perft') {
        const depth = parseInt(args.depth || '4', 10);
        const start = Date.now();
        if (args.divide === 'true') {
            const div = (0, movegen_1.perftDivide)(board, depth);
            let total = 0;
            for (const [m, n] of [...div.entries()].sort()) {
                console.log(`${m}: ${n}`);
                total += n;
            }
            console.log(`\nTotal: ${total} (${Date.now() - start}ms)`);
        }
        else {
            const n = (0, movegen_1.perft)(board, depth);
            console.log(`perft(${depth}) = ${n} (${Date.now() - start}ms)`);
        }
        return;
    }
    if (cmd === 'eval') {
        console.log(board.toString());
        console.log(`eval: ${(0, evaluate_1.evaluate)(board)} cp (${formatScore((0, evaluate_1.evaluate)(board))})`);
        return;
    }
    if (cmd === 'legal') {
        const moves = (0, movegen_1.generateLegalMoves)(board);
        console.log(moves.map(movegen_1.moveToUci).sort().join('\n'));
        console.log(`(${moves.length} moves)`);
        return;
    }
    if (cmd === 'play') {
        const readline = await Promise.resolve().then(() => __importStar(require('readline')));
        const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
        const depth = parseInt(args.depth || '5', 10);
        const ask = (q) => new Promise(res => rl.question(q, res));
        console.log(board.toString());
        console.log('Enter UCI moves (e.g. e2e4), or "go" for engine, "quit" to exit.');
        while (true) {
            const legal = (0, movegen_1.generateLegalMoves)(board);
            if (legal.length === 0) {
                console.log(board.inCheck() ? 'Checkmate!' : 'Stalemate!');
                break;
            }
            const line = (await ask(`${board.side === 0 ? 'White' : 'Black'}> `)).trim();
            if (line === 'quit' || line === 'exit')
                break;
            if (line === 'go' || line === '') {
                const search = new search_1.Search(board);
                search.onInfo = (info) => {
                    process.stderr.write(`  d${info.depth} ${formatScore(info.score)} pv ${info.pv.join(' ')}\n`);
                };
                const best = search.search({ maxDepth: depth });
                if (best) {
                    console.log(`Engine plays: ${(0, movegen_1.moveToUci)(best)}`);
                    board.makeMove(best);
                    console.log(board.toString());
                }
                continue;
            }
            if (line === 'fen') {
                console.log(board.getFen());
                continue;
            }
            const m = (0, movegen_1.parseUciMove)(board, line);
            if (!m) {
                console.log('Illegal move. Legal:', legal.map(movegen_1.moveToUci).join(' '));
                continue;
            }
            board.makeMove(m);
            console.log(board.toString());
            // Engine replies
            const replyLegal = (0, movegen_1.generateLegalMoves)(board);
            if (replyLegal.length === 0) {
                console.log(board.inCheck() ? 'Checkmate!' : 'Stalemate!');
                break;
            }
            const search = new search_1.Search(board);
            search.onInfo = (info) => {
                process.stderr.write(`  d${info.depth} ${formatScore(info.score)} pv ${info.pv.join(' ')}\n`);
            };
            const best = search.search({ maxDepth: depth });
            if (best) {
                console.log(`Engine plays: ${(0, movegen_1.moveToUci)(best)}`);
                board.makeMove(best);
                console.log(board.toString());
            }
        }
        rl.close();
        return;
    }
    usage();
    process.exit(1);
}
main().catch((e) => {
    console.error(e);
    process.exit(1);
});
//# sourceMappingURL=main.js.map
