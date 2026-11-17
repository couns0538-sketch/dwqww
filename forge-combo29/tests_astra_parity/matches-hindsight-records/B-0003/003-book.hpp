#pragma once

#include "forge/board.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace forge::book {

// One Polyglot-compatible book entry.
struct Entry {
    std::uint64_t key = 0;
    std::uint16_t move = 0;
    std::uint16_t weight = 0;
    std::uint32_t learn = 0;
};

// Polyglot Zobrist key of a position (castling and en-passant per the format).
[[nodiscard]] std::uint64_t polyglot_key(const Board& board);
// Polyglot 16-bit move encoding; castling is stored as king-takes-rook.
[[nodiscard]] std::uint16_t encode_move(const Board& board, const Move& move);
// Decodes to a legal move of `board`, or Move::none() when absent/illegal.
[[nodiscard]] Move decode_move(const Board& board, std::uint16_t encoded);

class Book {
public:
    // Loads a Polyglot .bin file; returns false and leaves the book unchanged on failure.
    bool load_file(const std::string& path);
    // Loads the book compiled into the engine (empty if none).
    void load_embedded();
    void clear();
    [[nodiscard]] bool empty() const { return entries_.empty(); }
    [[nodiscard]] std::size_t size() const { return entries_.size(); }

    // All legal book moves for the position, best weight first.
    struct Candidate {
        Move move;
        std::uint16_t weight;
    };
    [[nodiscard]] std::vector<Candidate> candidates(const Board& board) const;
    // Picks a move: the heaviest, or a weight-proportional random choice among
    // moves within `variety_percent` of the best weight.
    [[nodiscard]] Move probe(const Board& board, int variety_percent, std::uint64_t& rng_state) const;

    // Sorted entry access for tools.
    [[nodiscard]] const std::vector<Entry>& entries() const { return entries_; }
    void set_entries(std::vector<Entry> entries);

private:
    std::vector<Entry> entries_;
};

// Whether a built-in book is compiled into this binary.
[[nodiscard]] bool embedded_available();
[[nodiscard]] std::size_t embedded_size();

} // namespace forge::book
