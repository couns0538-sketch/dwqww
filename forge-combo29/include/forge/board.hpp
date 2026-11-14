#pragma once

#include "forge/bitboard.hpp"

// FORGE_SEARCH_SPEED2 (R14 build switch, default 0 = lock code): speed-only, node-identical search changes
// (TT prefetch after every make, MovePicker history / piece hoist, table piece_type). See src/search.cpp.
#ifndef FORGE_SEARCH_SPEED2
#define FORGE_SEARCH_SPEED2 0
#endif

// FORGE_SDK_MOVE_EQ32 (SDK long job 2026-11-06; default 0 = the code before it): Move::operator== compares the
// four bytes as one 32-bit word.
#ifndef FORGE_SDK_MOVE_EQ32
#define FORGE_SDK_MOVE_EQ32 1
#endif

#include <array>
#include <bit>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#ifndef FORGE_SPD_PREFETCH_EARLY
// Build switch, default 0 (= the lock's code): search prefetches the child's TT
// cluster before make_move from Board::key_after where that key is cheap and exact.
#define FORGE_SPD_PREFETCH_EARLY 0
#endif

namespace forge {

enum Piece : int {
    Empty = 0,
    WP = 1, WN, WB, WR, WQ, WK,
    BP = 7, BN, BB, BR, BQ, BK
};

enum PieceType : int { NoPieceType = 0, Pawn = 1, Knight, Bishop, Rook, Queen, King };

enum MoveFlag : std::uint8_t {
    Quiet = 0,
    Capture = 1,
    DoublePush = 2,
    KingCastle = 4,
    QueenCastle = 8,
    EnPassant = 16,
    Promotion = 32
};

// Build switch (default 0 = the lock code). 1: Move has no default member
// initialisers, so the move arrays and lists whose slots are always written
// before they are read are no longer zero-filled at construction (Move{} and
// Move::none() stay all-zero through value-initialisation). 2: in addition a
// quiets-only generation mode for the move picker, which yields the same
// quiet moves in the same order as the lock's full list after its filter.
#ifndef FORGE_SPD_NO_ZERO_MOVELISTS
#define FORGE_SPD_NO_ZERO_MOVELISTS 0
#endif

// Build switch (default 0 = the lock code). 1: the board keeps per-position
// "king lines" - the side to move's pieces that alone block an enemy slider's
// line to their own king (pinned), its pieces that alone block one of its own
// sliders' lines to the enemy king (discovered-check candidates), and the
// squares from which each piece type checks the enemy king. They are computed
// once on first use and kept across make / unmake through Undo. is_legal and
// gives_check answer normal moves from them; en passant, castling, promotions,
// king moves and positions in check keep the lock's full tests. Every answer
// equals the lock's, so the search visits the same nodes.
#ifndef FORGE_SPD_KING_LINES
#define FORGE_SPD_KING_LINES 1
#endif

struct Move {
#if FORGE_SPD_NO_ZERO_MOVELISTS
    std::uint8_t from;
    std::uint8_t to;
    std::uint8_t promotion;
    std::uint8_t flags;
#else
    std::uint8_t from = 0;
    std::uint8_t to = 0;
    std::uint8_t promotion = 0;
    std::uint8_t flags = 0;
#endif

#if FORGE_SDK_MOVE_EQ32
    // The four bytes compared as one 32-bit word: the same predicate as the member-wise default (no padding), which
    // g++ 15 turns into four byte compares and two branches.
    [[nodiscard]] bool operator==(const Move& other) const {
        return std::bit_cast<std::uint32_t>(*this) == std::bit_cast<std::uint32_t>(other);
    }
#else
    [[nodiscard]] bool operator==(const Move&) const = default;
#endif
    [[nodiscard]] bool is_capture() const { return (flags & (Capture | EnPassant)) != 0U; }
    [[nodiscard]] bool is_promotion() const { return (flags & Promotion) != 0U; }
    [[nodiscard]] bool is_castle() const { return (flags & (KingCastle | QueenCastle)) != 0U; }
    [[nodiscard]] bool is_quiet() const { return !is_capture() && !is_promotion(); }
    [[nodiscard]] bool is_none() const { return from == to; }
    [[nodiscard]] static constexpr Move none() { return Move{}; }
};

class MoveList {
public:
    static constexpr std::size_t Capacity = 256;
    using iterator = std::array<Move, Capacity>::iterator;
    using const_iterator = std::array<Move, Capacity>::const_iterator;

    void push_back(Move move) { assert(size_ < Capacity); data_[size_++] = move; }
    void reserve(std::size_t) {}
    void resize(std::size_t size) { assert(size <= Capacity); size_ = size; }
    void clear() { size_ = 0; }
    [[nodiscard]] std::size_t size() const { return size_; }
    [[nodiscard]] bool empty() const { return size_ == 0; }
    [[nodiscard]] Move& operator[](std::size_t index) { return data_[index]; }
    [[nodiscard]] const Move& operator[](std::size_t index) const { return data_[index]; }
    [[nodiscard]] Move& front() { return data_[0]; }
    [[nodiscard]] const Move& front() const { return data_[0]; }
    [[nodiscard]] iterator begin() { return data_.begin(); }
    [[nodiscard]] iterator end() { return data_.begin() + static_cast<std::ptrdiff_t>(size_); }
    [[nodiscard]] const_iterator begin() const { return data_.begin(); }
    [[nodiscard]] const_iterator end() const { return data_.begin() + static_cast<std::ptrdiff_t>(size_); }

private:
    std::array<Move, Capacity> data_;
    std::size_t size_ = 0;
};

#if FORGE_SPD_KING_LINES
// Per-position king lines of the side to move (see the switch comment above).
// Index of check_squares = piece type; King and NoPieceType stay 0.
struct KingLines {
    bool valid = false;
    Bitboard pinned = 0;
    Bitboard discoverers = 0;
    std::array<Bitboard, 7> check_squares{};
};
#endif

struct Undo {
    Piece captured = Empty;
    std::uint8_t castling = 0;
    std::int8_t ep_square = -1;
    std::uint16_t halfmove = 0;
    std::uint16_t fullmove = 1;
    std::uint64_t key = 0;
    std::uint64_t pawn_key = 0;
    Bitboard checkers = 0;
    std::uint16_t plies_from_null = 0;
#if FORGE_SPD_KING_LINES
    KingLines king_lines;
#endif
};

struct NullUndo {
    std::int8_t ep_square = -1;
    std::uint64_t key = 0;
    std::uint16_t halfmove = 0;
    std::uint16_t fullmove = 1;
    std::uint16_t plies_from_null = 0;
    Bitboard checkers = 0;
#if FORGE_SPD_KING_LINES
    KingLines king_lines;
#endif
};

class Board {
public:
    static constexpr std::string_view StandardStartFen =
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    Board();

    [[nodiscard]] bool set_fen(std::string_view fen, std::string* error = nullptr);
    [[nodiscard]] std::string fen() const;

    // Move generation. Pseudo-legal moves may leave the own king in check;
    // is_legal() filters them. Captures-only generation also includes every
    // quiet promotion, so search sees every material-changing move.
    [[nodiscard]] MoveList pseudo_legal_moves(bool captures_only = false) const;
#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
    // Quiets: the non-capturing, non-promoting moves of the full list in the
    // same order. The bool entry stays for the lock's callers.
    enum class GenMode : int { All, Captures, Quiets };
    void generate_pseudo_legal(MoveList& moves, GenMode mode) const;
    void generate_pseudo_legal(MoveList& moves, bool captures_only) const {
        generate_pseudo_legal(moves, captures_only ? GenMode::Captures : GenMode::All);
    }
#else
    void generate_pseudo_legal(MoveList& moves, bool captures_only) const;
#endif
    [[nodiscard]] MoveList legal_moves(bool captures_only = false) const;
    [[nodiscard]] bool has_legal_move() const;
    // Contract with FORGE_SPD_KING_LINES on (self-review K3): the fast path of is_legal is exact only for a move that
    // is already pseudo-legal in this position. Every current caller passes such moves (generated, or checked with
    // is_pseudo_legal first); an unvalidated move may get a different answer than the lock.
    [[nodiscard]] bool is_legal(const Move& move) const;
    [[nodiscard]] bool is_pseudo_legal(const Move& move) const;
    [[nodiscard]] bool gives_check(const Move& move) const;

#if FORGE_SPD_PREFETCH_EARLY
    // Key of the position after `move`, without making it (for an early TT
    // prefetch). Returns true with the exact key, or false when an en-passant
    // term could change it (an en-passant square now, an en-passant capture, or a
    // double push next to an enemy pawn): then the caller prefetches after make_move.
    [[nodiscard]] bool key_after(const Move& move, std::uint64_t& key) const;
#endif
    [[nodiscard]] bool make_move(const Move& move, Undo& undo);
    void unmake_move(const Move& move, const Undo& undo);
    void make_null_move(NullUndo& undo);
    void unmake_null_move(const NullUndo& undo);

    [[nodiscard]] bool square_attacked(int square, Color by) const;
    [[nodiscard]] Bitboard attackers_to(int square, Bitboard occupancy) const;
    [[nodiscard]] Bitboard attackers_to(int square) const { return attackers_to(square, occupied()); }
    [[nodiscard]] bool in_check(Color color) const;
    [[nodiscard]] bool in_check() const { return checkers_ != 0; }
    [[nodiscard]] Bitboard checkers() const { return checkers_; }

    [[nodiscard]] std::optional<Move> parse_uci(std::string_view text);
    [[nodiscard]] static std::string move_to_uci(const Move& move);
    [[nodiscard]] std::uint64_t perft(int depth);

    // Game-level threefold repetition of the current position.
    [[nodiscard]] bool is_repetition() const;
    // Search-level repetition: any earlier occurrence at or after history
    // index root_index counts, otherwise two earlier occurrences are needed.
    [[nodiscard]] bool is_repetition(std::size_t root_index) const;
    [[nodiscard]] bool is_insufficient_material() const;
    [[nodiscard]] bool has_non_pawn_material(Color color) const;

    // Static exchange evaluation. see_ge() answers whether the exchange on the
    // destination square nets at least `threshold` centipawns for the mover.
    [[nodiscard]] int static_exchange(const Move& move) const;
    [[nodiscard]] bool see_ge(const Move& move, int threshold) const;

    [[nodiscard]] Piece piece_at(int square) const { return squares_[static_cast<std::size_t>(square)]; }
    [[nodiscard]] Bitboard pieces(Piece piece) const { return bitboards_[static_cast<std::size_t>(piece)]; }
    [[nodiscard]] Bitboard pieces(Color color, PieceType type) const {
        return bitboards_[static_cast<std::size_t>((color == White ? 0 : 6) + type)];
    }
    [[nodiscard]] Bitboard pieces(PieceType type) const { return pieces(White, type) | pieces(Black, type); }
    [[nodiscard]] Bitboard occupied(Color color) const { return occupied_[static_cast<std::size_t>(color)]; }
    [[nodiscard]] Bitboard occupied() const { return occupied_[0] | occupied_[1]; }
    [[nodiscard]] int king_square(Color color) const { return king_squares_[static_cast<std::size_t>(color)]; }
    [[nodiscard]] Color side_to_move() const { return side_; }
    [[nodiscard]] std::uint64_t key() const { return key_; }
    [[nodiscard]] std::uint64_t pawn_key() const { return pawn_key_; }
    [[nodiscard]] int halfmove_clock() const { return halfmove_; }
    [[nodiscard]] int fullmove_number() const { return fullmove_; }
    [[nodiscard]] int ep_square() const { return ep_square_; }
    [[nodiscard]] std::uint8_t castling_rights() const { return castling_; }
    [[nodiscard]] const std::vector<std::uint64_t>& key_history() const { return key_history_; }
    [[nodiscard]] std::size_t history_size() const { return key_history_.size(); }
    [[nodiscard]] Piece moved_piece(const Move& move) const { return piece_at(move.from); }
    [[nodiscard]] Piece captured_piece(const Move& move) const {
        if ((move.flags & EnPassant) != 0U) return side_ == White ? BP : WP;
        return piece_at(move.to);
    }

private:
    std::array<Piece, 64> squares_{};
    std::array<Bitboard, 13> bitboards_{};
    std::array<Bitboard, 2> occupied_{};
    std::array<int, 2> king_squares_{-1, -1};
    Color side_ = White;
    std::uint8_t castling_ = 0;
    std::int8_t ep_square_ = -1;
    std::uint16_t halfmove_ = 0;
    std::uint16_t fullmove_ = 1;
    std::uint64_t key_ = 0;
    std::uint64_t pawn_key_ = 0;
    Bitboard checkers_ = 0;
    // Plies since the last null move; bounds search-level repetition scans.
    std::uint16_t plies_from_null_ = 1024;
    std::vector<std::uint64_t> key_history_;
#if FORGE_SPD_KING_LINES
    // Lazily computed for the current position; invalidated by every make and
    // restored by every unmake (each search thread owns its Board copy).
    mutable KingLines king_lines_;
    void refresh_king_lines() const;
#endif

    void put_piece(Piece piece, int square);
    void remove_piece(int square);
    void move_piece(int from, int to);
    [[nodiscard]] bool has_legal_en_passant_capture() const;
    [[nodiscard]] std::uint64_t compute_key() const;
    [[nodiscard]] std::uint64_t compute_pawn_key() const;
    [[nodiscard]] Bitboard compute_checkers() const;
    [[nodiscard]] bool square_attacked_with_occupancy(int square, Color by, Bitboard occupancy,
                                                       Bitboard removed = 0) const;
};

[[nodiscard]] constexpr bool is_white(Piece piece) { return piece >= WP && piece <= WK; }
[[nodiscard]] constexpr bool is_black(Piece piece) { return piece >= BP && piece <= BK; }
#if FORGE_SEARCH_SPEED2
namespace detail {
// Piece type for every Piece value: Empty=0 -> 0, WP..WK=1..6 -> 1..6, BP..BK=7..12 -> 1..6. Entries 13..15 only pad
// the table to 16 so the index mask stays in bounds; no valid Piece reaches them (same values as the modulo form).
inline constexpr std::array<std::uint8_t, 16> PieceTypeTable{0, 1, 2, 3, 4, 5, 6, 1, 2, 3, 4, 5, 6, 0, 0, 0};
} // namespace detail
[[nodiscard]] constexpr int piece_type(Piece piece) { return detail::PieceTypeTable[static_cast<unsigned>(piece) & 15U]; }
#else
[[nodiscard]] constexpr int piece_type(Piece piece) { return piece == Empty ? 0 : ((static_cast<int>(piece) - 1) % 6) + 1; }
#endif
[[nodiscard]] constexpr Color color_of(Piece piece) { return piece >= BP ? Black : White; }
[[nodiscard]] constexpr Piece make_piece(Color color, int type) {
    return static_cast<Piece>((color == White ? 0 : 6) + type);
}

} // namespace forge
