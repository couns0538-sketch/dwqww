#pragma once

#include <array>
#include <bit>
#include <cstdint>

namespace forge {

using Bitboard = std::uint64_t;

enum Color : int { White = 0, Black = 1 };

[[nodiscard]] constexpr Color opposite(Color color) { return color == White ? Black : White; }

constexpr Bitboard FileABB = 0x0101010101010101ULL;
constexpr Bitboard FileBBB = FileABB << 1;
constexpr Bitboard FileCBB = FileABB << 2;
constexpr Bitboard FileDBB = FileABB << 3;
constexpr Bitboard FileEBB = FileABB << 4;
constexpr Bitboard FileFBB = FileABB << 5;
constexpr Bitboard FileGBB = FileABB << 6;
constexpr Bitboard FileHBB = FileABB << 7;

constexpr Bitboard Rank1BB = 0xFFULL;
constexpr Bitboard Rank2BB = Rank1BB << 8;
constexpr Bitboard Rank3BB = Rank1BB << 16;
constexpr Bitboard Rank4BB = Rank1BB << 24;
constexpr Bitboard Rank5BB = Rank1BB << 32;
constexpr Bitboard Rank6BB = Rank1BB << 40;
constexpr Bitboard Rank7BB = Rank1BB << 48;
constexpr Bitboard Rank8BB = Rank1BB << 56;

constexpr Bitboard DarkSquares = 0xAA55AA55AA55AA55ULL;
constexpr Bitboard LightSquares = ~DarkSquares;
constexpr Bitboard CenterSquares = (FileDBB | FileEBB) & (Rank4BB | Rank5BB);
constexpr Bitboard QueenSide = FileABB | FileBBB | FileCBB | FileDBB;
constexpr Bitboard KingSide = FileEBB | FileFBB | FileGBB | FileHBB;

[[nodiscard]] constexpr Bitboard square_bb(int square) { return 1ULL << square; }
[[nodiscard]] constexpr Bitboard file_bb(int file) { return FileABB << file; }
[[nodiscard]] constexpr Bitboard rank_bb(int rank) { return Rank1BB << (8 * rank); }
[[nodiscard]] constexpr int file_of(int square) { return square & 7; }
[[nodiscard]] constexpr int rank_of(int square) { return square >> 3; }
[[nodiscard]] constexpr int make_square(int file, int rank) { return rank * 8 + file; }
[[nodiscard]] constexpr int relative_rank(Color color, int square) {
    return color == White ? rank_of(square) : 7 - rank_of(square);
}
[[nodiscard]] constexpr int relative_square(Color color, int square) {
    return color == White ? square : square ^ 56;
}
[[nodiscard]] constexpr int flip_square(int square) { return square ^ 56; }

[[nodiscard]] inline int lsb(Bitboard bb) { return std::countr_zero(bb); }
[[nodiscard]] inline int msb(Bitboard bb) { return 63 - std::countl_zero(bb); }
[[nodiscard]] inline int popcount(Bitboard bb) { return std::popcount(bb); }
[[nodiscard]] inline int pop_lsb(Bitboard& bb) {
    const int square = lsb(bb);
    bb &= bb - 1;
    return square;
}
[[nodiscard]] constexpr bool more_than_one(Bitboard bb) { return (bb & (bb - 1)) != 0; }

[[nodiscard]] constexpr Bitboard shift_north(Bitboard bb) { return bb << 8; }
[[nodiscard]] constexpr Bitboard shift_south(Bitboard bb) { return bb >> 8; }
[[nodiscard]] constexpr Bitboard shift_east(Bitboard bb) { return (bb & ~FileHBB) << 1; }
[[nodiscard]] constexpr Bitboard shift_west(Bitboard bb) { return (bb & ~FileABB) >> 1; }
[[nodiscard]] constexpr Bitboard shift_north_east(Bitboard bb) { return (bb & ~FileHBB) << 9; }
[[nodiscard]] constexpr Bitboard shift_north_west(Bitboard bb) { return (bb & ~FileABB) << 7; }
[[nodiscard]] constexpr Bitboard shift_south_east(Bitboard bb) { return (bb & ~FileHBB) >> 7; }
[[nodiscard]] constexpr Bitboard shift_south_west(Bitboard bb) { return (bb & ~FileABB) >> 9; }

// Include every square ahead on the same file, retaining the input squares.
[[nodiscard]] constexpr Bitboard forward_fill(Color color, Bitboard squares) {
    if (color == White) {
        squares |= squares << 8;
        squares |= squares << 16;
        squares |= squares << 32;
    } else {
        squares |= squares >> 8;
        squares |= squares >> 16;
        squares |= squares >> 32;
    }
    return squares;
}

[[nodiscard]] constexpr Bitboard pawn_push(Color color, Bitboard bb) {
    return color == White ? shift_north(bb) : shift_south(bb);
}
[[nodiscard]] constexpr Bitboard pawn_attacks_bb(Color color, Bitboard pawns) {
    return color == White ? shift_north_east(pawns) | shift_north_west(pawns)
                          : shift_south_east(pawns) | shift_south_west(pawns);
}
[[nodiscard]] constexpr int pawn_push_delta(Color color) { return color == White ? 8 : -8; }

[[nodiscard]] constexpr int square_distance(int a, int b) {
    const int df = file_of(a) - file_of(b);
    const int dr = rank_of(a) - rank_of(b);
    const int adf = df < 0 ? -df : df;
    const int adr = dr < 0 ? -dr : dr;
    return adf > adr ? adf : adr;
}

namespace attacks {

// Precomputed attack tables. Initialisation is idempotent and cheap; the Board
// constructor guarantees it has run before any position is created.
void init();

extern std::array<Bitboard, 64> KnightTable;
extern std::array<Bitboard, 64> KingTable;
extern std::array<std::array<Bitboard, 64>, 2> PawnTable;
extern std::array<std::array<Bitboard, 64>, 64> BetweenTable;
extern std::array<std::array<Bitboard, 64>, 64> LineTable;
extern std::array<std::array<Bitboard, 64>, 2> PassedPawnMask;
extern std::array<std::array<Bitboard, 64>, 2> ForwardFileMask;
extern std::array<Bitboard, 64> AdjacentFilesMask;
extern std::array<std::array<Bitboard, 64>, 2> ForwardRanksMask;
extern std::array<Bitboard, 64> KingZoneMask;

struct Magic {
    Bitboard mask = 0;
    Bitboard magic = 0;
    Bitboard* table = nullptr;
    unsigned shift = 0;

    [[nodiscard]] std::size_t index(Bitboard occupancy) const {
        return static_cast<std::size_t>(((occupancy & mask) * magic) >> shift);
    }
};

extern std::array<Magic, 64> RookMagics;
extern std::array<Magic, 64> BishopMagics;

[[nodiscard]] inline Bitboard knight(int square) { return KnightTable[static_cast<std::size_t>(square)]; }
[[nodiscard]] inline Bitboard king(int square) { return KingTable[static_cast<std::size_t>(square)]; }
[[nodiscard]] inline Bitboard pawn(Color color, int square) {
    return PawnTable[static_cast<std::size_t>(color)][static_cast<std::size_t>(square)];
}
[[nodiscard]] inline Bitboard bishop(int square, Bitboard occupancy) {
    const Magic& m = BishopMagics[static_cast<std::size_t>(square)];
    return m.table[m.index(occupancy)];
}
[[nodiscard]] inline Bitboard rook(int square, Bitboard occupancy) {
    const Magic& m = RookMagics[static_cast<std::size_t>(square)];
    return m.table[m.index(occupancy)];
}
[[nodiscard]] inline Bitboard queen(int square, Bitboard occupancy) {
    return bishop(square, occupancy) | rook(square, occupancy);
}
[[nodiscard]] inline Bitboard between(int a, int b) {
    return BetweenTable[static_cast<std::size_t>(a)][static_cast<std::size_t>(b)];
}
[[nodiscard]] inline Bitboard line(int a, int b) {
    return LineTable[static_cast<std::size_t>(a)][static_cast<std::size_t>(b)];
}
[[nodiscard]] inline bool aligned(int a, int b, int c) { return (line(a, b) & square_bb(c)) != 0; }
[[nodiscard]] inline Bitboard passed_pawn_mask(Color color, int square) {
    return PassedPawnMask[static_cast<std::size_t>(color)][static_cast<std::size_t>(square)];
}
[[nodiscard]] inline Bitboard forward_file(Color color, int square) {
    return ForwardFileMask[static_cast<std::size_t>(color)][static_cast<std::size_t>(square)];
}
[[nodiscard]] inline Bitboard forward_ranks(Color color, int square) {
    return ForwardRanksMask[static_cast<std::size_t>(color)][static_cast<std::size_t>(square)];
}
[[nodiscard]] inline Bitboard adjacent_files(int square) { return AdjacentFilesMask[static_cast<std::size_t>(square)]; }
[[nodiscard]] inline Bitboard king_zone(int square) { return KingZoneMask[static_cast<std::size_t>(square)]; }

} // namespace attacks

} // namespace forge
