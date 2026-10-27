#pragma once

// Syzygy endgame tablebases (WDL .rtbw and DTZ .rtbz files), own reader.
//
// Written from the public description of the Syzygy file format and probing
// rules (R. de Man's format notes, CPW "Syzygy Bases"; see
// opus_round1/C1/IDEA_SOURCE.md); no third-party probing code is used.
// Implementation: src/search/syzygy.inc (table files, indexing, decompression,
// WDL/DTZ probes, root ranking) and src/search/tablebase.inc (search glue).
//
// Everything is inactive until load() finds tables (UCI SyzygyPath). Tables
// are memory-mapped read-only; probes may run concurrently from any number of
// search threads, but never concurrently with load().

#include "forge/board.hpp"
#include "forge/search_types.hpp"

#include <atomic>
#include <cstdint>
#include <string>
#include <vector>

namespace forge::syzygy {

// Game-theoretic value from the side to move's point of view. A cursed win
// (blessed loss) is a win (loss) that the 50-move rule turns into a draw.
enum Wdl : int { WdlLoss = -2, WdlBlessedLoss = -1, WdlDraw = 0, WdlCursedWin = 1, WdlWin = 2 };

struct LoadSummary {
    int wdl_tables = 0;   // .rtbw files accepted
    int dtz_tables = 0;   // .rtbz files accepted (only for materials that also have a WDL table)
    int rejected = 0;     // files with a table name that failed validation (empty, truncated, corrupt)
    int max_pieces = 0;   // largest piece count (kings included) with a WDL table; 0 = none
};

// Replaces the loaded tables by those found in `paths`: directories separated
// by ';' on Windows and ':' elsewhere. An empty string or "<empty>" unloads
// everything. Missing folders, empty folders and invalid files are skipped.
// Must not run while any search or probe runs.
LoadSummary load(const std::string& paths);

// Largest piece count with a loaded WDL table (0 when nothing is loaded).
[[nodiscard]] int max_pieces();

// WDL probe. Returns false if the position cannot be probed: castling rights,
// more pieces than max_pieces(), or a needed table is missing or invalid. The
// value assumes the 50-move counter is zero (exact right after a capture or a
// pawn move). The board is restored before returning.
[[nodiscard]] bool probe_wdl(Board& board, int& wdl);

// DTZ probe, in plies, Syzygy convention: dtz > 0 win (dtz > 100: cursed win),
// dtz < 0 loss (dtz < -100: blessed loss), 0 draw, -1 the side to move is
// mated. Same failure rules as probe_wdl. A table that stores a value in moves
// instead of plies rounds it: then `rounded` is set and the true distance is
// |dtz| or |dtz| + 1 plies (DTZ50'' rounding).
[[nodiscard]] bool probe_dtz(Board& board, int& dtz);
[[nodiscard]] bool probe_dtz(Board& board, int& dtz, bool& rounded);

// Outcome of the position with its current 50-move counter: like the WDL
// value, but a win/loss whose zeroing move cannot come before the 50-move rule
// is reported as cursed/blessed. Needs the DTZ table. Returns false also when
// DTZ rounding leaves the outcome undecided (rounded distance + counter = 100).
[[nodiscard]] bool probe_wdl_with_counter(Board& board, int& wdl);

struct RootRank {
    Move move{};
    int rank = 0;          // larger is better; equal ranks are equivalent for the tablebase
    int value = 0;         // DTZ of the move (counted from the root position) or its WDL
    bool rounded = false;  // the DTZ value is rounded (see probe_dtz)
};

// Ranks every legal root move with DTZ (falls back to WDL when a DTZ probe
// fails). rule50 = honour the 50-move rule. Returns false if the root cannot be
// probed at all. used_dtz reports which tables ranked the moves.
[[nodiscard]] bool rank_root_moves(Board& board, bool rule50, std::vector<RootRank>& ranks, bool& used_dtz);

// Search-time state, written by the search driver before the worker threads
// start (src/search/tablebase.inc) and read by the workers:
//  - search_cardinality > 0 enables WDL probes inside the search for
//    positions with at most that many pieces;
//  - root_display != 0 means the root was ranked by the tablebase and the
//    reported (non-mate) score is replaced by root_display_score.
extern std::atomic<int> search_cardinality;
extern std::atomic<int> root_display;
extern std::atomic<int> root_display_score;
extern std::atomic<std::uint64_t> probe_hits;

// Tablebase scores, below the mate scores: a TB win found at ply p scores
// TbWin - p; a cursed win (blessed loss) scores +/-TbCursed while the 50-move
// rule is honoured.
constexpr int TbWin = MateInMaxPly - 1;
constexpr int TbCursed = 2;

// Search driver hooks (src/search/tablebase.inc), only called while tables are
// loaded. prepare_root runs before the workers start: it sets
// search_cardinality, and if the root is a tablebase position it restricts
// limits.search_moves to the best-ranked moves (intersected with a given
// searchmoves list) and sets the reported score. display_score maps a search
// score to the reported one.
void prepare_root(const Board& root, SearchLimits& limits);
[[nodiscard]] int display_score(int search_score);

// Test hook: read table files into exact-size heap buffers instead of mapping
// them (lets AddressSanitizer see every out-of-bounds read). Default false.
void set_heap_loading(bool enabled);

// Loaded files, for diagnostics and tests: `tail` is the number of bytes after
// the last compressed block (the format ends with a 16-byte checksum).
struct TableInfo {
    std::string name;  // e.g. "KRPvKR.rtbz"
    std::uint64_t file_size = 0;
    std::uint64_t tail = 0;
};
[[nodiscard]] std::vector<TableInfo> loaded_tables();
// True if both the WDL and the DTZ table of `name` (e.g. "KRPvKR") are loaded.
[[nodiscard]] bool has_table(const std::string& name);

} // namespace forge::syzygy
