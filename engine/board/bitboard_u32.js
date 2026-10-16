"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.bb2South = exports.bb2North = exports.bb2Test = exports.bb2Clear = exports.bb2Set = exports.bb2Bit = exports.bb2PopLsb = exports.bb2Lsb = exports.bb2Popcount = exports.bb2IsEmpty = exports.bb2Not = exports.bb2Xor = exports.bb2And = exports.bb2Or = exports.bbToBig = exports.bbFromBig = exports.EMPTY2 = void 0;
/**
 * Dual-u32 bitboard — now the mainline representation in bitboard.ts.
 * Re-exports kept for staged experiment / older imports.
 */
var bitboard_1 = require("./bitboard");
Object.defineProperty(exports, "EMPTY2", { enumerable: true, get: function () { return bitboard_1.EMPTY; } });
Object.defineProperty(exports, "bbFromBig", { enumerable: true, get: function () { return bitboard_1.bbFromBig; } });
Object.defineProperty(exports, "bbToBig", { enumerable: true, get: function () { return bitboard_1.bbToBig; } });
Object.defineProperty(exports, "bb2Or", { enumerable: true, get: function () { return bitboard_1.or; } });
Object.defineProperty(exports, "bb2And", { enumerable: true, get: function () { return bitboard_1.and; } });
Object.defineProperty(exports, "bb2Xor", { enumerable: true, get: function () { return bitboard_1.xor; } });
Object.defineProperty(exports, "bb2Not", { enumerable: true, get: function () { return bitboard_1.not; } });
Object.defineProperty(exports, "bb2IsEmpty", { enumerable: true, get: function () { return bitboard_1.isEmpty; } });
Object.defineProperty(exports, "bb2Popcount", { enumerable: true, get: function () { return bitboard_1.popcount; } });
Object.defineProperty(exports, "bb2Lsb", { enumerable: true, get: function () { return bitboard_1.lsb; } });
Object.defineProperty(exports, "bb2PopLsb", { enumerable: true, get: function () { return bitboard_1.popLsb; } });
Object.defineProperty(exports, "bb2Bit", { enumerable: true, get: function () { return bitboard_1.bit; } });
Object.defineProperty(exports, "bb2Set", { enumerable: true, get: function () { return bitboard_1.setBit; } });
Object.defineProperty(exports, "bb2Clear", { enumerable: true, get: function () { return bitboard_1.clearBit; } });
Object.defineProperty(exports, "bb2Test", { enumerable: true, get: function () { return bitboard_1.testBit; } });
Object.defineProperty(exports, "bb2North", { enumerable: true, get: function () { return bitboard_1.north; } });
Object.defineProperty(exports, "bb2South", { enumerable: true, get: function () { return bitboard_1.south; } });
//# sourceMappingURL=bitboard_u32.js.map
