#pragma once

// S32 self-play datagen v2: fixed-node self-play inside the engine process, written directly in the
// residual trainer's .pos (FPOS v1) / .hce (FHCE v1) format (record layout: fen2bin.cpp and
// hce_dump.cpp of the lock archive, read by train_resid_v3b.py load_set/load_set_mmap).
//
// The code is part of forge_core. The engine executable exposes it only when it is compiled with
// FORGE_DATAGEN (command line "forge datagen ..."); the UCI loop is identical with or without it.
// Game rules, record filters and labels follow nnue/forge-nnue-tools/forge_selfplay.py (play_game,
// terminal_result, decisive_side, eligible_score), so the same opening gives the same game.

#include "forge/board.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace forge {
class Searcher;
}

namespace forge::datagen {

// FPOS board: 64 nibbles, square s (a1 = 0 .. h8 = 63) in byte s >> 1, low nibble for even s;
// 0 empty, 1..6 white P N B R Q K, 7..12 black p n b r q k (the forge::Piece values).
using PackedBoard = std::array<std::uint8_t, 32>;
[[nodiscard]] PackedBoard pack_board(const Board& board);

// FPOS meta byte: bit 0 = black to move, bits 1-2 = White's result * 2 (0 loss, 1 draw, 2 win).
[[nodiscard]] constexpr std::uint8_t pack_meta(Color side_to_move, int white_result_x2) {
    return static_cast<std::uint8_t>((side_to_move == Black ? 1 : 0) | (white_result_x2 << 1));
}

struct Record {
    PackedBoard board{};
    std::int16_t score = 0; // search score, side to move's view, centipawns
    std::int16_t hce = 0;   // Evaluator::evaluate_uncached, side to move's view, clamped to +-32767
    std::uint8_t meta = 0;  // pack_meta(); the result bits are filled in when the game ends
    std::string fen;        // kept only for the optional text output
};

enum class Termination { Checkmate, Stalemate, Insufficient, Repetition, FiftyMoves, MaxPly, AdjudicatedWin, AdjudicatedDraw };
[[nodiscard]] const char* termination_name(Termination termination);

struct Config {
    std::uint64_t nodes = 5000;     // fixed-node search per move ("go nodes"), used when depth == 0
    int depth = 0;                  // fixed-depth search per move ("go depth") when > 0
    int random_plies = 8;           // uniformly random legal opening moves before the first search
    int max_ply = 300;              // game ply (from the move counters) that ends the game as a draw
    int win_cp = 2000;              // win adjudication: |White-view score| >= win_cp ...
    int win_plies = 4;              // ... for this many consecutive searched plies, same side (0 = off)
    int draw_cp = 0;                // draw adjudication: |score| <= draw_cp ...
    int draw_plies = 0;             // ... for this many consecutive searched plies (0 = off, the default)
    int draw_min_ply = 0;           // ... once the game ply is at least this
    int max_score = 3000;           // positions with |score| > max_score are not recorded
    std::uint64_t games = 0;        // stop after this many completed games (0 = no game limit)
    std::uint64_t positions = 0;    // stop after the game that reaches this many records (0 = no limit)
    std::uint64_t seed = 1;
    std::size_t hash_mb = 16;
    std::uint64_t positions_per_file = 1000000; // a shard is closed after the game that reaches this
    std::string out;                // output prefix: <out>_NNN.pos/.hce[/.txt]/.info, <out>.games
    bool text = false;              // also write "FEN | score | result" lines (forge_selfplay.py text)
    std::string openings;           // optional EPD/FEN start positions, one per line (default startpos)
    std::string convert;            // convert mode: "FEN | score | result" text file -> .pos/.hce
};

struct Game {
    std::vector<Move> opening;      // the random plies
    std::vector<Move> moves;        // the searched plies
    std::vector<Record> records;    // eligible positions, meta result bits already set
    int white_result_x2 = 1;
    Termination termination = Termination::MaxPly;
};

// SplitMix64 (Steele, Lea, Flood 2014); fully specified, so a seed reproduces on every platform.
class Rng {
public:
    explicit Rng(std::uint64_t seed) : state_(seed) {}
    std::uint64_t next();
    // Uniform enough for move choice (n <= 256): next() % n.
    std::uint64_t below(std::uint64_t n) { return next() % n; }
private:
    std::uint64_t state_;
};

// Seed of game attempt `index`: games are independent of each other and of the process count.
[[nodiscard]] std::uint64_t game_seed(std::uint64_t run_seed, std::uint64_t index);

// Ply implied by the move counters (forge_selfplay.py uses python-chess Board.ply()).
[[nodiscard]] int game_ply(const Board& board);

// forge_selfplay.py terminal_result(): White's result * 2 and why, or nullopt while the game goes on.
[[nodiscard]] std::optional<std::pair<int, Termination>> terminal(const Board& board, int max_ply);

// Plays one game from `start`. nullopt when the random opening already ended the game (such an
// attempt yields no samples, as in forge_selfplay.py). Throws std::runtime_error on an engine fault.
[[nodiscard]] std::optional<Game> play_game(Searcher& searcher, const Config& config, const Board& start, Rng& rng);

// Shard output. Each file is written as "<name>.part" (exclusive create, fails if it exists),
// then renamed to "<name>" without replacing an existing file; the .pos is published last, so a
// .pos without .part means a complete shard. Several processes may write into one directory as
// long as their prefixes differ; a reused prefix fails before any data is written.
class ShardWriter {
public:
    ShardWriter(std::string prefix, std::uint64_t positions_per_file, bool text, std::string info);
    void add(Record record);
    // Closes the current shard if it reached positions_per_file (call between games).
    void maybe_close();
    // Closes the current shard if it holds any record.
    void close();
    [[nodiscard]] std::uint64_t written() const { return written_; }
    [[nodiscard]] std::uint64_t shards() const { return shard_index_; }
    [[nodiscard]] std::size_t pending() const { return records_.size(); }
private:
    std::string prefix_;
    std::uint64_t positions_per_file_;
    bool text_;
    std::string info_;
    std::vector<Record> records_;
    std::uint64_t shard_index_ = 0;
    std::uint64_t written_ = 0;
};

[[nodiscard]] std::string shard_name(const std::string& prefix, std::uint64_t index);
// Bytes of the .pos / .hce file for these records (little endian, as fen2bin / hce_dump).
[[nodiscard]] std::string pos_bytes(const std::vector<Record>& records);
[[nodiscard]] std::string hce_bytes(const std::vector<Record>& records);
// Writes `bytes` to `path` via "<path>.part"; throws std::runtime_error if either name exists.
void write_new_file(const std::string& path, const std::string& bytes);

// One "FEN | score | result" line -> record (fen2bin + hce_dump semantics); nullopt if invalid.
[[nodiscard]] std::optional<Record> parse_text_record(const std::string& line);

// "forge datagen <options>" (argv excludes the program name and "datagen"); returns the exit code.
int run(int argc, const char* const* argv);

} // namespace forge::datagen
