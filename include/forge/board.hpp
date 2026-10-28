#pragma once

#include "forge/bitboard.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

// FORGE_NOZERO_MOVE_BUFFERS (default 0 = the AL1 lock code): leave the MoveList and MovePicker
// move buffers uninitialised instead of zero-filling them on every construction (S14 follow-up).
#ifndef FORGE_NOZERO_MOVE_BUFFERS
#define FORGE_NOZERO_MOVE_BUFFERS 0
#endif
#if FORGE_NOZERO_MOVE_BUFFERS
#include <new>
#include <type_traits>
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

struct Move {
    std::uint8_t from = 0;
    std::uint8_t to = 0;
    std::uint8_t promotion = 0;
    std::uint8_t flags = 0;

    [[nodiscard]] bool operator==(const Move&) const = default;
    [[nodiscard]] bool is_capture() const { return (flags & (Capture | EnPassant)) != 0U; }
    [[nodiscard]] bool is_promotion() const { return (flags & Promotion) != 0U; }
    [[nodiscard]] bool is_castle() const { return (flags & (KingCastle | QueenCastle)) != 0U; }
    [[nodiscard]] bool is_quiet() const { return !is_capture() && !is_promotion(); }
    [[nodiscard]] bool is_none() const { return from == to; }
    [[nodiscard]] static constexpr Move none() { return Move{}; }
};

#if FORGE_NOZERO_MOVE_BUFFERS
// Storage for N objects of type T that is not initialised when its owner is constructed. A
// default-initialised std::array<Move, N> is zero-filled because Move has default member
// initializers; the move buffers below never read an element they have not written, so that fill
// is wasted work on every construction. The std::byte array implicitly creates the T[N] array when
// its lifetime begins ([intro.object], C++20, P0593R6) and std::launder yields a pointer to its
// first element, so element access and pointer arithmetic are well defined. Owners must write an
// element before reading it and must not value-initialise the storage (no `{}` initializer).
template <typename T, std::size_t N>
struct UninitArray {
    static_assert(std::is_trivially_copyable_v<T> && std::is_trivially_destructible_v<T>);
    alignas(T) std::byte bytes[N * sizeof(T)];

    [[nodiscard]] T* data() { return std::launder(reinterpret_cast<T*>(bytes)); }
    [[nodiscard]] const T* data() const { return std::launder(reinterpret_cast<const T*>(bytes)); }
    [[nodiscard]] T* begin() { return data(); }
    [[nodiscard]] const T* begin() const { return data(); }
    [[nodiscard]] T& operator[](std::size_t index) { return data()[index]; }
    [[nodiscard]] const T& operator[](std::size_t index) const { return data()[index]; }
    [[nodiscard]] static constexpr std::size_t size() { return N; }
};
#endif

class MoveList {
public:
    static constexpr std::size_t Capacity = 256;
#if FORGE_NOZERO_MOVE_BUFFERS
    using iterator = Move*;
    using const_iterator = const Move*;
#else
    using iterator = std::array<Move, Capacity>::iterator;
    using const_iterator = std::array<Move, Capacity>::const_iterator;
#endif

    void push_back(Move move) { assert(size_ < Capacity); data_[size_++] = move; }
    void reserve(std::size_t) {}
#if FORGE_NOZERO_MOVE_BUFFERS
    // Shrink only: elements at or past size_ have never been written.
    void resize(std::size_t size) { assert(size <= size_); size_ = size; }
#else
    void resize(std::size_t size) { assert(size <= Capacity); size_ = size; }
#endif
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
#if FORGE_NOZERO_MOVE_BUFFERS
    UninitArray<Move, Capacity> data_;  // only [0, size_) is ever read
#else
    std::array<Move, Capacity> data_;
#endif
    std::size_t size_ = 0;
};

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
};

struct NullUndo {
    std::int8_t ep_square = -1;
    std::uint64_t key = 0;
    std::uint16_t halfmove = 0;
    std::uint16_t plies_from_null = 0;
    Bitboard checkers = 0;
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
    void generate_pseudo_legal(MoveList& moves, bool captures_only) const;
    [[nodiscard]] MoveList legal_moves(bool captures_only = false) const;
    [[nodiscard]] bool has_legal_move() const;
    [[nodiscard]] bool is_legal(const Move& move) const;
    [[nodiscard]] bool is_pseudo_legal(const Move& move) const;
    [[nodiscard]] bool gives_check(const Move& move) const;

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
    // Upcoming repetition (UCI CuckooRep): true when the side to move has a
    // legal reversible move after which is_repetition(root_index) holds, i.e.
    // it can reach a search-level repetition draw at once. Answered from the
    // key history and the cuckoo table of reversible-move keys (namespace
    // cuckoo below) without generating moves. Cold: used only with CuckooRep.
    [[nodiscard, gnu::cold]] bool upcoming_repetition(std::size_t root_index) const;
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
[[nodiscard]] constexpr int piece_type(Piece piece) { return piece == Empty ? 0 : ((static_cast<int>(piece) - 1) % 6) + 1; }
[[nodiscard]] constexpr Color color_of(Piece piece) { return piece >= BP ? Black : White; }
[[nodiscard]] constexpr Piece make_piece(Color color, int type) {
    return static_cast<Piece>((color == White ? 0 : 6) + type);
}

// Cuckoo table behind Board::upcoming_repetition (UCI CuckooRep). It holds one
// entry per reversible move of a knight, bishop, rook, queen or king of either
// colour between two squares {a, b} (a < b) that the piece connects on an
// empty board: 2 x (168 + 280 + 448 + 728 + 210) = 3668 entries. The key of an
// entry is the Zobrist difference of the two positions the move connects:
// piece-on-a ^ piece-on-b ^ side-to-move. The table is a constant built at
// compile time; these accessors exist for tests and diagnostics.
namespace cuckoo {

inline constexpr std::size_t Slots = 8192;

struct Entry {
    Piece piece = Empty;
    int a = 0;  // the lower square
    int b = 0;  // the higher square
};

// Number of stored entries (3668).
[[nodiscard, gnu::cold]] std::size_t entry_count();
// Zobrist key difference of `piece` moving between squares a and b.
[[nodiscard, gnu::cold]] std::uint64_t move_key(Piece piece, int a, int b);
// Exact lookup: the entry whose key is `key`, if any.
[[nodiscard, gnu::cold]] std::optional<Entry> lookup(std::uint64_t key);
// Slot contents for table-level tests (key 0 = empty slot).
[[nodiscard, gnu::cold]] std::uint64_t slot_key(std::size_t slot);

} // namespace cuckoo

} // namespace forge
