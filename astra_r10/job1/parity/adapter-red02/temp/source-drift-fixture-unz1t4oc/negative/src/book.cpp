#include "forge/book.hpp"

#include <algorithm>
#include <array>
#include <fstream>
#include <iterator>

#if __has_include("book_data.inc")
#include "book_data.inc"
#define FORGE_HAS_BOOK 1
#else
#define FORGE_HAS_BOOK 0
#endif

namespace forge::book {
namespace {

constexpr std::array<std::uint64_t, 781> Random64{
#include "polyglot_keys.inc"
};

constexpr int CastleOffset = 768;
constexpr int EnPassantOffset = 772;
constexpr int TurnOffset = 780;

[[nodiscard]] constexpr int piece_kind(Piece piece) {
    // Polyglot order: black pawn 0, white pawn 1, black knight 2, ...
    return 2 * (piece_type(piece) - 1) + (is_white(piece) ? 1 : 0);
}

[[nodiscard]] std::uint16_t encode_squares(int from, int to, int promotion) {
    return static_cast<std::uint16_t>(file_of(to) | (rank_of(to) << 3) | (file_of(from) << 6) | (rank_of(from) << 9) |
                                      (promotion << 12));
}

} // namespace

std::uint64_t polyglot_key(const Board& board) {
    std::uint64_t key = 0;
    Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = pop_lsb(occupied);
        const Piece piece = board.piece_at(square);
        key ^= Random64[static_cast<std::size_t>(64 * piece_kind(piece) + 8 * rank_of(square) + file_of(square))];
    }
    const std::uint8_t castling = board.castling_rights();
    if ((castling & 1U) != 0U) key ^= Random64[CastleOffset + 0];
    if ((castling & 2U) != 0U) key ^= Random64[CastleOffset + 1];
    if ((castling & 4U) != 0U) key ^= Random64[CastleOffset + 2];
    if ((castling & 8U) != 0U) key ^= Random64[CastleOffset + 3];
    const int ep = board.ep_square();
    if (ep >= 0) {
        // Polyglot hashes the en-passant file only when a pawn of the side to
        // move stands beside the pawn that just advanced.
        const Color us = board.side_to_move();
        const int pawn_square = ep - pawn_push_delta(us);
        const Bitboard neighbours = ((square_bb(pawn_square) & ~FileABB) >> 1) | ((square_bb(pawn_square) & ~FileHBB) << 1);
        if ((neighbours & board.pieces(us, Pawn)) != 0) key ^= Random64[static_cast<std::size_t>(EnPassantOffset + file_of(ep))];
    }
    if (board.side_to_move() == White) key ^= Random64[TurnOffset];
    return key;
}

std::uint16_t encode_move(const Board& board, const Move& move) {
    int to = move.to;
    if (move.is_castle()) {
        const bool king_side = (move.flags & KingCastle) != 0U;
        to = board.side_to_move() == White ? (king_side ? 7 : 0) : (king_side ? 63 : 56);
    }
    int promotion = 0;
    if (move.is_promotion()) promotion = move.promotion - 1; // knight 1 .. queen 4
    return encode_squares(move.from, to, promotion);
}

Move decode_move(const Board& board, std::uint16_t encoded) {
    const int to_file = encoded & 7;
    const int to_rank = (encoded >> 3) & 7;
    const int from_file = (encoded >> 6) & 7;
    const int from_rank = (encoded >> 9) & 7;
    const int promotion = (encoded >> 12) & 7;
    const int from = make_square(from_file, from_rank);
    int to = make_square(to_file, to_rank);
    // King-takes-rook castling notation.
    const Piece mover = board.piece_at(from);
    if (piece_type(mover) == King && board.piece_at(to) == make_piece(color_of(mover), Rook)) {
        if (to == 7 && from == 4) to = 6;
        else if (to == 0 && from == 4) to = 2;
        else if (to == 63 && from == 60) to = 62;
        else if (to == 56 && from == 60) to = 58;
    }
    for (const Move move : board.legal_moves()) {
        if (move.from != from || move.to != to) continue;
        if (move.is_promotion() != (promotion != 0)) continue;
        if (move.is_promotion() && move.promotion != promotion + 1) continue;
        return move;
    }
    return Move::none();
}

bool Book::load_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return false;
    std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    if (bytes.size() < 16) return false;
    std::vector<Entry> entries;
    entries.reserve(bytes.size() / 16);
    for (std::size_t offset = 0; offset + 16 <= bytes.size(); offset += 16) {
        const unsigned char* b = bytes.data() + offset;
        Entry entry;
        for (int i = 0; i < 8; ++i) entry.key = (entry.key << 8) | b[i];
        entry.move = static_cast<std::uint16_t>((b[8] << 8) | b[9]);
        entry.weight = static_cast<std::uint16_t>((b[10] << 8) | b[11]);
        entry.learn = (static_cast<std::uint32_t>(b[12]) << 24) | (static_cast<std::uint32_t>(b[13]) << 16) |
                      (static_cast<std::uint32_t>(b[14]) << 8) | b[15];
        entries.push_back(entry);
    }
    set_entries(std::move(entries));
    return true;
}

void Book::load_embedded() {
    std::vector<Entry> entries;
#if FORGE_HAS_BOOK
    entries.reserve(BookEntryCount);
    for (std::size_t i = 0; i < BookEntryCount; ++i) {
        entries.push_back(Entry{BookKeys[i], BookMoves[i], BookWeights[i], 0});
    }
#endif
    set_entries(std::move(entries));
}

void Book::clear() { entries_.clear(); }

void Book::set_entries(std::vector<Entry> entries) {
    std::stable_sort(entries.begin(), entries.end(), [](const Entry& a, const Entry& b) { return a.key < b.key; });
    entries_ = std::move(entries);
}

std::vector<Book::Candidate> Book::candidates(const Board& board) const {
    std::vector<Candidate> result;
    const std::uint64_t key = polyglot_key(board);
    auto it = std::lower_bound(entries_.begin(), entries_.end(), key,
                               [](const Entry& entry, std::uint64_t value) { return entry.key < value; });
    for (; it != entries_.end() && it->key == key; ++it) {
        const Move move = decode_move(board, it->move);
        if (move.is_none()) continue;
        bool merged = false;
        for (Candidate& existing : result) {
            if (existing.move == move) {
                existing.weight = static_cast<std::uint16_t>(std::min<int>(65535, existing.weight + it->weight));
                merged = true;
            }
        }
        if (!merged) result.push_back(Candidate{move, it->weight});
    }
    std::stable_sort(result.begin(), result.end(), [](const Candidate& a, const Candidate& b) { return a.weight > b.weight; });
    return result;
}

Move Book::probe(const Board& board, int variety_percent, std::uint64_t& rng_state) const {
    const std::vector<Candidate> moves = candidates(board);
    if (moves.empty()) return Move::none();
    const int best = moves.front().weight;
    if (variety_percent <= 0 || best == 0) return moves.front().move;
    const int threshold = std::max(1, best * (100 - variety_percent) / 100);
    std::uint64_t total = 0;
    for (const Candidate& candidate : moves) {
        if (candidate.weight >= threshold) total += candidate.weight;
    }
    // xorshift64*
    rng_state ^= rng_state >> 12;
    rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27;
    std::uint64_t pick = (rng_state * 2685821657736338717ULL) % std::max<std::uint64_t>(1, total);
    for (const Candidate& candidate : moves) {
        if (candidate.weight < threshold) continue;
        if (pick < candidate.weight) return candidate.move;
        pick -= candidate.weight;
    }
    return moves.front().move;
}

bool embedded_available() { return FORGE_HAS_BOOK != 0; }

std::size_t embedded_size() {
#if FORGE_HAS_BOOK
    return BookEntryCount;
#else
    return 0;
#endif
}

} // namespace forge::book
