"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.perft = exports.parseUciMove = exports.moveToUci = exports.generateLegalMoves = exports.evaluate = exports.Search = exports.START_FEN = exports.Board = void 0;
var board_1 = require("./board/board");
Object.defineProperty(exports, "Board", { enumerable: true, get: function () { return board_1.Board; } });
Object.defineProperty(exports, "START_FEN", { enumerable: true, get: function () { return board_1.START_FEN; } });
var search_1 = require("./search/search");
Object.defineProperty(exports, "Search", { enumerable: true, get: function () { return search_1.Search; } });
var evaluate_1 = require("./eval/evaluate");
Object.defineProperty(exports, "evaluate", { enumerable: true, get: function () { return evaluate_1.evaluate; } });
var movegen_1 = require("./move/movegen");
Object.defineProperty(exports, "generateLegalMoves", { enumerable: true, get: function () { return movegen_1.generateLegalMoves; } });
Object.defineProperty(exports, "moveToUci", { enumerable: true, get: function () { return movegen_1.moveToUci; } });
Object.defineProperty(exports, "parseUciMove", { enumerable: true, get: function () { return movegen_1.parseUciMove; } });
Object.defineProperty(exports, "perft", { enumerable: true, get: function () { return movegen_1.perft; } });
//# sourceMappingURL=index.js.map
