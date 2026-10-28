#include "forge/bitboard.hpp"

#include <algorithm>
#include <cstddef>

#if defined(FORGE_ATTACKS_INIT_ONCE) && FORGE_ATTACKS_INIT_ONCE
#include <mutex>
#endif

namespace forge::attacks {

std::array<Bitboard, 64> KnightTable{};
std::array<Bitboard, 64> KingTable{};
std::array<std::array<Bitboard, 64>, 2> PawnTable{};
std::array<std::array<Bitboard, 64>, 64> BetweenTable{};
std::array<std::array<Bitboard, 64>, 64> LineTable{};
std::array<std::array<Bitboard, 64>, 2> PassedPawnMask{};
std::array<std::array<Bitboard, 64>, 2> ForwardFileMask{};
std::array<Bitboard, 64> AdjacentFilesMask{};
std::array<std::array<Bitboard, 64>, 2> ForwardRanksMask{};
std::array<Bitboard, 64> KingZoneMask{};
std::array<Magic, 64> RookMagics{};
std::array<Magic, 64> BishopMagics{};

namespace {

std::array<Bitboard, 0x19000> RookAttackTable{};
std::array<Bitboard, 0x1480> BishopAttackTable{};

constexpr bool on_board_step(int square, int file_delta, int rank_delta) {
    const int file = file_of(square) + file_delta;
    const int rank = rank_of(square) + rank_delta;
    return file >= 0 && file < 8 && rank >= 0 && rank < 8;
}

Bitboard sliding_attack(const std::array<std::pair<int, int>, 4>& directions, int square, Bitboard occupancy) {
    Bitboard result = 0;
    for (const auto& [df, dr] : directions) {
        int file = file_of(square);
        int rank = rank_of(square);
        while (true) {
            file += df;
            rank += dr;
            if (file < 0 || file > 7 || rank < 0 || rank > 7) break;
            const int target = make_square(file, rank);
            result |= square_bb(target);
            if ((occupancy & square_bb(target)) != 0) break;
        }
    }
    return result;
}

constexpr std::array<std::pair<int, int>, 4> RookDirections{{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}};
constexpr std::array<std::pair<int, int>, 4> BishopDirections{{{1, 1}, {1, -1}, {-1, 1}, {-1, -1}}};

struct Prng {
    std::uint64_t state;
    std::uint64_t next() {
        state ^= state >> 12;
        state ^= state << 25;
        state ^= state >> 27;
        return state * 2685821657736338717ULL;
    }
    std::uint64_t sparse() { return next() & next() & next(); }
};

void init_magics(bool rook, Bitboard* table, std::array<Magic, 64>& magics) {
    const auto& directions = rook ? RookDirections : BishopDirections;
    static std::array<Bitboard, 4096> occupancies;
    static std::array<Bitboard, 4096> references;
    static std::array<unsigned, 4096> epochs{};
    unsigned epoch = 0;
    std::size_t offset = 0;
    // Seeds chosen per rank keep the search short on 64-bit targets.
    constexpr std::array<std::uint64_t, 8> seeds{728, 10316, 55013, 32803, 12281, 15100, 16645, 255};
    for (int square = 0; square < 64; ++square) {
        const Bitboard edges = ((Rank1BB | Rank8BB) & ~rank_bb(rank_of(square))) |
                               ((FileABB | FileHBB) & ~file_bb(file_of(square)));
        Magic& m = magics[static_cast<std::size_t>(square)];
        m.mask = sliding_attack(directions, square, 0) & ~edges;
        m.shift = 64U - static_cast<unsigned>(popcount(m.mask));
        m.table = table + offset;
        std::size_t size = 0;
        Bitboard subset = 0;
        do {
            occupancies[size] = subset;
            references[size] = sliding_attack(directions, square, subset);
            ++size;
            subset = (subset - m.mask) & m.mask;
        } while (subset != 0);

        Prng rng{seeds[static_cast<std::size_t>(rank_of(square))]};
        for (bool found = false; !found;) {
            do {
                m.magic = rng.sparse();
            } while (popcount((m.mask * m.magic) >> 56) < 6);
            ++epoch;
            found = true;
            for (std::size_t i = 0; i < size; ++i) {
                const std::size_t index = m.index(occupancies[i]);
                if (epochs[index] < epoch) {
                    epochs[index] = epoch;
                    m.table[index] = references[i];
                } else if (m.table[index] != references[i]) {
                    found = false;
                    break;
                }
            }
        }
        offset += size;
    }
}

} // namespace

void init() {
#if defined(FORGE_ATTACKS_INIT_ONCE) && FORGE_ATTACKS_INIT_ONCE
    static std::once_flag initialized_once;
    std::call_once(initialized_once, [] {
#else
    static bool initialized = false;
    if (initialized) return;
    initialized = true;
#endif

    for (int square = 0; square < 64; ++square) {
        const std::size_t s = static_cast<std::size_t>(square);
        for (const auto& [df, dr] : std::array<std::pair<int, int>, 8>{{{1, 2}, {2, 1}, {-1, 2}, {-2, 1},
                                                                        {1, -2}, {2, -1}, {-1, -2}, {-2, -1}}}) {
            if (on_board_step(square, df, dr)) KnightTable[s] |= square_bb(square + dr * 8 + df);
        }
        for (const auto& [df, dr] : std::array<std::pair<int, int>, 8>{{{1, 0}, {-1, 0}, {0, 1}, {0, -1},
                                                                        {1, 1}, {1, -1}, {-1, 1}, {-1, -1}}}) {
            if (on_board_step(square, df, dr)) KingTable[s] |= square_bb(square + dr * 8 + df);
        }
        PawnTable[White][s] = pawn_attacks_bb(White, square_bb(square));
        PawnTable[Black][s] = pawn_attacks_bb(Black, square_bb(square));

        const int file = file_of(square);
        const int rank = rank_of(square);
        AdjacentFilesMask[s] = (file > 0 ? file_bb(file - 1) : 0) | (file < 7 ? file_bb(file + 1) : 0);
        Bitboard north = 0;
        Bitboard south = 0;
        for (int r = rank + 1; r < 8; ++r) north |= rank_bb(r);
        for (int r = rank - 1; r >= 0; --r) south |= rank_bb(r);
        ForwardRanksMask[White][s] = north;
        ForwardRanksMask[Black][s] = south;
        ForwardFileMask[White][s] = north & file_bb(file);
        ForwardFileMask[Black][s] = south & file_bb(file);
        PassedPawnMask[White][s] = north & (file_bb(file) | AdjacentFilesMask[s]);
        PassedPawnMask[Black][s] = south & (file_bb(file) | AdjacentFilesMask[s]);

        const int zone_file = std::clamp(file, 1, 6);
        const int zone_rank = std::clamp(rank, 1, 6);
        const int zone_center = make_square(zone_file, zone_rank);
        Bitboard zone = square_bb(zone_center);
        for (const auto& [df, dr] : std::array<std::pair<int, int>, 8>{{{1, 0}, {-1, 0}, {0, 1}, {0, -1},
                                                                        {1, 1}, {1, -1}, {-1, 1}, {-1, -1}}}) {
            zone |= square_bb(zone_center + dr * 8 + df);
        }
        KingZoneMask[s] = zone | square_bb(square);
    }

    init_magics(true, RookAttackTable.data(), RookMagics);
    init_magics(false, BishopAttackTable.data(), BishopMagics);

    for (int a = 0; a < 64; ++a) {
        for (int b = 0; b < 64; ++b) {
            if (a == b) continue;
            const std::size_t sa = static_cast<std::size_t>(a);
            const std::size_t sb = static_cast<std::size_t>(b);
            if ((rook(a, 0) & square_bb(b)) != 0) {
                LineTable[sa][sb] = (rook(a, 0) & rook(b, 0)) | square_bb(a) | square_bb(b);
                BetweenTable[sa][sb] = rook(a, square_bb(b)) & rook(b, square_bb(a));
            } else if ((bishop(a, 0) & square_bb(b)) != 0) {
                LineTable[sa][sb] = (bishop(a, 0) & bishop(b, 0)) | square_bb(a) | square_bb(b);
                BetweenTable[sa][sb] = bishop(a, square_bb(b)) & bishop(b, square_bb(a));
            }
        }
    }
#if defined(FORGE_ATTACKS_INIT_ONCE) && FORGE_ATTACKS_INIT_ONCE
    });
#endif
}

} // namespace forge::attacks
