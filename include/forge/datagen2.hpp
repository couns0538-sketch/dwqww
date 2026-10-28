#pragma once
// Self-play data generation v2 (job FB2-J2). Reached only through the UCI command `datagen ...`; nothing here is
// touched by the normal engine paths (bench/perft stay identical).
//
// Game format "FGB1" (Forge game binpack): one file = header, games, FNV-1a 64 trailer.
//   header (48 bytes): "FGB1" | u32 version=1 | u64 games | u64 plies | u64 records | u64 seed | u64 reserved
//   game: u16 fen_len | fen (start position) | u8 white_result_x2 (0/1/2) | u8 termination | u16 opening_plies
//         | u16 plies | plies x { u16 move (from | to << 6 | promo << 12, promo 0 = none, 1..4 = N B R Q)
//                                 | i16 score (side to move; ScoreNone = 32002 for opening plies)
//                                 | u8 flags (Record bits below) }
// Every position is recovered by replaying the moves from the start FEN; a record (training row) is a ply whose
// flags have RecordKept set. The converter (`datagen convert`) replays the games with the engine's own Board and
// writes FPOS/FHCE shards byte-identical to the direct writer (`--pos`), which the tests check.
#include "forge/board.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace forge {
class Searcher;
}

namespace forge::datagen2 {

constexpr std::int16_t ScoreNone = 32002;

enum RecordFlag : std::uint8_t {
    RecordKept = 1,          // written to the training set
    RecordInCheck = 2,       // side to move in check
    RecordNoisyPv = 4,       // a capture / promotion within the first `pv_capture_plies` PV moves
    RecordMateScore = 8,     // mate score
    RecordScoreCap = 16,     // |score| > max_score
    RecordEarly = 32,        // game ply < min_ply
    RecordSubsampled = 64,   // dropped by --skip-prob
    RecordGivesCheck = 128,  // best move gives check (reported, not filtered by default)
};

enum class Termination : std::uint8_t {
    Checkmate = 0, Stalemate, Insufficient, Repetition, FiftyMoves, MaxPly, AdjudicatedWin, AdjudicatedDraw
};
const char* termination_name(Termination t);

struct Config {
    std::string out;                 // output prefix: <out>.fgb, <out>.info.json, optional <out>.pos/.hce/.txt
    std::uint64_t games = 0;         // stop after this many games (0 = no limit)
    std::uint64_t records = 0;       // stop after this many kept records (0 = no limit)
    double max_minutes = 0.0;        // stop after this wall time (0 = no limit)
    std::uint64_t nodes = 5000;      // per-move node limit (depth wins when > 0)
    int depth = 0;
    int hash_mb = 16;
    std::uint64_t seed = 1;
    // opening diversity
    std::string book;                // FEN/EPD lines; a random line starts each game (default: startpos)
    int random_plies = 8;            // uniformly random legal moves
    int random_plies_jitter = 0;     // random plies drawn from [random_plies - j, random_plies + j]
    int temp_plies = 0;              // softmax-sampled plies after the random ones (per-move shallow searches)
    double temperature = 100.0;      // centipawns per unit of softmax logit
    int temp_depth = 3;              // depth of the per-move shallow searches
    int opening_eval_cap = 0;        // redraw the opening when |score| after the opening phase exceeds this (0 = off)
    int opening_attempts = 8;
    // game rules and adjudication
    int max_ply = 300;
    int win_cp = 2000;
    int win_plies = 4;               // 0 = no win adjudication
    int draw_cp = 0;
    int draw_plies = 0;              // 0 = no draw adjudication
    int draw_min_ply = 60;
    // record filters
    int max_score = 3000;
    int min_ply = 0;
    int pv_capture_plies = 2;        // 1 = only the best move itself (the S32 / forge_selfplay rule)
    double skip_prob = 0.0;
    bool filter_in_check = true;
    bool filter_gives_check = false;
    // outputs
    bool write_pos = false;          // also write the direct FPOS/FHCE files (<out>.pos/.hce)
    bool write_text = false;         // also write "<fen> | <score> | <white result>" lines (<out>.txt)
    bool quiet = false;
};

struct Ply {
    Move move{};
    std::int16_t score = ScoreNone;
    std::uint8_t flags = 0;
};

struct Game {
    std::string start_fen;
    std::uint8_t white_result_x2 = 1;
    Termination termination = Termination::MaxPly;
    std::uint16_t opening_plies = 0;
    std::vector<Ply> plies;
};

struct Stats {
    std::uint64_t games = 0, plies = 0, searched = 0, records = 0;
    std::uint64_t opening_redraws = 0, distinct_starts = 0, distinct_after_opening = 0;
    std::uint64_t in_check = 0, noisy_pv = 0, mate = 0, score_cap = 0, early = 0, subsampled = 0, gives_check = 0;
    std::uint64_t results[3] = {0, 0, 0};           // black win, draw, white win
    std::uint64_t terminations[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    std::uint64_t nodes = 0;
    double seconds = 0.0;
};

// Deterministic per-game seed: the same (seed, index) always plays the same game, whatever ran before.
std::uint64_t game_seed(std::uint64_t run_seed, std::uint64_t index);

std::uint16_t encode_move(const Move& move);
// The legal move of `board` matching an encoded (from, to, promotion); none() when there is no such move.
Move decode_move(const Board& board, std::uint16_t code);

// FPOS row of a position: 32 bytes of 4-bit piece codes (two squares per byte, a1 first).
std::array<std::uint8_t, 32> pack_board(const Board& board);

// Serialisation (without the file header / trailer).
void append_game(std::string& out, const Game& game);
bool read_games(const std::string& bytes, std::vector<Game>& games, std::uint64_t& seed, std::string* error);
std::string file_bytes(const std::vector<Game>& games, std::uint64_t seed);   // header + games + checksum

// Replay a game and emit its records as FPOS / FHCE bytes (the converter). Returns false on an illegal move.
bool records_of(const Game& game, std::string& pos_rows, std::string& score_bytes, std::string& meta_bytes,
                std::string& hce_bytes, std::string* text_lines, std::uint64_t& count, std::string* error);
// FPOS / FHCE files from row bytes.
std::string fpos_bytes(const std::string& rows, const std::string& scores, const std::string& metas, std::uint64_t count);
std::string fhce_bytes(const std::string& hces, std::uint64_t count);

// Parse `datagen` arguments (after the command word). Returns false with an error message on bad input.
bool parse_args(const std::vector<std::string>& args, Config& config, std::string* error);
// Generate: plays games with a private Searcher and writes <out>.fgb (+ optional .pos/.hce/.txt) and <out>.info.json.
int run_generate(const Config& config, Stats* stats_out = nullptr);
// Convert: <in.fgb> -> <out>.pos/.hce (+ .txt when text). Returns 0 on success.
int run_convert(const std::string& in_path, const std::string& out_prefix, bool text, std::string* error);
// One game, for tests: deterministic given (config, seed).
bool play_game(Searcher& searcher, const Config& config, const std::string& start_fen, std::uint64_t seed, Game& game,
               Stats& stats, std::string* error);

} // namespace forge::datagen2
