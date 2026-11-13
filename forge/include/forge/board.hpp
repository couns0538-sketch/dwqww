#pragma once

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace forge {

enum Color : int { White = 0, Black = 1 };
enum Piece : int {
    Empty = 0,
    WP = 1, WN, WB, WR, WQ, WK,
    BP = 7, BN, BB, BR, BQ, BK
};

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
    std::uint8_t from;
    std::uint8_t to;
    std::uint8_t promotion;
    std::uint8_t flags;

    [[nodiscard]] bool operator==(const Move&) const = default;
    [[nodiscard]] bool is_capture() const { return (flags & Capture) != 0U || (flags & EnPassant) != 0U; }
};


class MoveList {
public:
    static constexpr std::size_t Capacity = 256;
    using iterator = std::array<Move, Capacity>::iterator;
    using const_iterator = std::array<Move, Capacity>::const_iterator;

    void push_back(Move move) { assert(size_ < Capacity); data_[size_++] = move; }
    void reserve(std::size_t) {}
    void resize(std::size_t size) { assert(size <= Capacity); size_ = size; }
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

struct Undo {
    Piece captured = Empty;
    std::uint8_t castling = 0;
    std::int8_t ep_square = -1;
    std::uint16_t halfmove = 0;
    std::uint16_t fullmove = 1;
    std::uint64_t key = 0;
    std::uint64_t pawn_key = 0;
    std::uint64_t repetition_context = 0;
};

struct NullUndo {
    std::int8_t ep_square = -1;
    std::uint64_t key = 0;
};

class Board {
public:
    static constexpr std::string_view StandardStartFen =
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

    Board();

    [[nodiscard]] bool set_fen(std::string_view fen, std::string* error = nullptr);
    [[nodiscard]] std::string fen() const;
    [[nodiscard]] MoveList pseudo_legal_moves(bool captures_only = false) const;
    [[nodiscard]] MoveList legal_moves(bool captures_only = false);
    [[nodiscard]] bool has_legal_move();
    [[nodiscard]] bool make_move(const Move& move, Undo& undo);
    void unmake_move(const Move& move, const Undo& undo);
    void make_null_move(NullUndo& undo);
    void unmake_null_move(const NullUndo& undo);
    [[nodiscard]] bool square_attacked(int square, Color by) const;
    [[nodiscard]] bool in_check(Color color) const;
    [[nodiscard]] std::optional<Move> parse_uci(std::string_view text);
    [[nodiscard]] static std::string move_to_uci(const Move& move);
    [[nodiscard]] std::uint64_t perft(int depth);
    [[nodiscard]] bool is_repetition() const;
    [[nodiscard]] bool is_insufficient_material() const;
    [[nodiscard]] int static_exchange(const Move& move) const;

    [[nodiscard]] Piece piece_at(int square) const { return squares_[static_cast<std::size_t>(square)]; }
    [[nodiscard]] std::uint64_t pieces(Piece piece) const {
        return bitboards_[static_cast<std::size_t>(piece)];
    }
    [[nodiscard]] std::uint64_t occupied(Color color) const {
        return occupied_[static_cast<std::size_t>(color)];
    }
    [[nodiscard]] Color side_to_move() const { return side_; }
    [[nodiscard]] std::uint64_t key() const { return key_; }
    [[nodiscard]] std::uint64_t pawn_key() const { return pawn_key_; }
    // Position key combined with the known reversible legal-history context.
    // Rule-50 and synthetic-null compatibility remain separate TT contexts.
    [[nodiscard]] std::uint64_t transposition_history_key() const;
    [[nodiscard]] int halfmove_clock() const { return halfmove_; }
    [[nodiscard]] const std::vector<std::uint64_t>& key_history() const { return key_history_; }

private:
    std::array<Piece, 64> squares_{};
    std::array<std::uint64_t, 13> bitboards_{};
    std::array<std::uint64_t, 2> occupied_{};
    std::array<int, 2> king_squares_{-1, -1};
    Color side_ = White;
    std::uint8_t castling_ = 0;
    std::int8_t ep_square_ = -1;
    std::uint16_t halfmove_ = 0;
    std::uint16_t fullmove_ = 1;
    std::uint64_t key_ = 0;
    std::uint64_t pawn_key_ = 0;
    std::uint64_t repetition_context_ = 0;
    std::vector<std::uint64_t> key_history_;

    void add_pawn_moves(MoveList& moves, int square, bool captures_only) const;
    void add_slider_moves(MoveList& moves, int square, int first_direction,
                          int count, bool captures_only) const;
    [[nodiscard]] bool is_legal_after(const Move& move) const;
    [[nodiscard]] bool square_attacked_with_occupancy(int square, Color by,
                                                       std::uint64_t occupancy,
                                                       std::uint64_t removed_attackers = 0) const;
    [[nodiscard]] bool has_legal_en_passant_capture() const;
    [[nodiscard]] std::uint64_t compute_key() const;
    [[nodiscard]] int king_square(Color color) const;
};

[[nodiscard]] constexpr Color opposite(Color color) {
    return color == White ? Black : White;
}

[[nodiscard]] constexpr bool is_white(Piece piece) { return piece >= WP && piece <= WK; }
[[nodiscard]] constexpr bool is_black(Piece piece) { return piece >= BP && piece <= BK; }
[[nodiscard]] constexpr int piece_type(Piece piece) { return piece == Empty ? 0 : ((static_cast<int>(piece) - 1) % 6) + 1; }

} // namespace forge
