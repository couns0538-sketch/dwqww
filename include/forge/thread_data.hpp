#pragma once

#include "forge/board.hpp"
#include "forge/correction_plus.hpp"
#include "forge/eval.hpp"
#include "forge/fb2.hpp"
#include "forge/hist_rework.hpp"
#ifdef FORGE_PROF
#include "forge/profile.hpp"
#endif
#include "forge/history.hpp"
#include "forge/nnue.hpp"
#include "forge/search_types.hpp"
#include "forge/tt.hpp"

#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

namespace forge {

struct SearchStack {
    std::array<Move, MaxPly + 1> pv{};
    int pv_length = 0;
    int ply = 0;
    Move current_move{};
    Move excluded_move{};
    std::array<Move, 2> killers{};
    Piece moved_piece = Empty;
    int static_eval = ValueNone;
    int raw_eval = ValueNone;
    int move_count = 0;
    int cutoff_count = 0;
    int double_extensions = 0;
    bool in_check = false;
    bool tt_pv = false;
    bool null_move_allowed = true;
    PieceToHistory* continuation = nullptr;
    // NNUE state: the accumulator is refreshed lazily from the nearest valid
    // ancestor using the piece changes recorded for each ply.
    nnue::Accumulator accumulator{};
    Evaluator::RuntimePsqt runtime_psqt{};
    nnue::DirtyPieces dirty{};
#if FORGE_NNUE_LAZY_ACC
    // Null edges may borrow a physical valid ancestor. Never a descendant or
    // another alias: valid remains false here until a real update materializes.
    SearchStack* accumulator_owner = nullptr;
#endif
};

// Move <-> 32-bit word, for publishing moves through one atomic.
[[nodiscard]] constexpr std::uint32_t pack_move(Move move) {
    return static_cast<std::uint32_t>(move.from) | static_cast<std::uint32_t>(move.to) << 8U |
           static_cast<std::uint32_t>(move.promotion) << 16U | static_cast<std::uint32_t>(move.flags) << 24U;
}
[[nodiscard]] constexpr Move unpack_move(std::uint32_t bits) {
    return Move{static_cast<std::uint8_t>(bits), static_cast<std::uint8_t>(bits >> 8U),
                static_cast<std::uint8_t>(bits >> 16U), static_cast<std::uint8_t>(bits >> 24U)};
}

// State shared by every worker of one Searcher.
struct SharedSearchState {
    explicit SharedSearchState(std::size_t hash_mb) : tt(hash_mb) {}
    TranspositionTable tt;
#ifdef FORGE_S13_TT_CHILD_PREFETCH
    std::atomic<bool> s13_tt_child_prefetch{false};
    std::atomic<bool> s13_tt_child_prefetch_announced{false};
#endif
    std::atomic<bool> stop{false};
    // HardDeadline (C3; R3 fix): set by the watchdog under uci_output_mutex right before it sends
    // the bestmove of a starved go; every search-side output checks it under the same mutex, so
    // nothing of that go is printed after its bestmove. Cleared at each go (Searcher::reset_stop).
    std::atomic<bool> output_closed{false};
#if FORGE_NNUE_LAZY_ACC
    // Immutable from before worker creation until every helper has joined.
    bool lazy_acc_enabled = false;
#endif
    // 0 means pondering has not been converted into a timed search.
    std::atomic<std::int64_t> ponder_hit_ns{0};
    // R5C: syzygy::probe_hits at the start of the current search (set by Searcher::search before any worker starts,
    // read-only while they run); the info lines report the difference as `tbhits` while tables are loaded.
    std::uint64_t tb_hits_base = 0;
#ifdef FORGE_PROF
    // The counters themselves live in one bank per Worker (S08-2).
    std::atomic<bool> profile_requested{false};
    bool profile_active=false; // Immutable while workers are active.
#endif
};

class Worker;

// Everything one search worker owns (Worker inherits this privately; the
// members keep the AL1 s198 Worker names and order, so the Worker layout and
// the test probes that befriend Worker are unchanged).
// Thread ownership while a search runs:
//   - shared_ refers to the only state all workers share (TT, stop flag,
//     ponderhit time): SharedSearchState above;
//   - nodes_ is this worker's published node count: written by the owner,
//     read by any worker (total_nodes()), hence atomic;
//   - all_workers_ points at the caller's worker list (read-only, valid for
//     the duration of one Searcher::search);
//   - every other member is read and written only by the owning thread.
struct ThreadData {
    ThreadData(SharedSearchState& shared, int id) : shared_(shared), id_(id) {}
    // Out of line (src/search/worker.inc) so the destruction path, and with it
    // the placement of the search functions, is generated as in AL1 s198.
    ~ThreadData();

    SharedSearchState& shared_;
    int id_ = 0;
    Evaluator evaluator_;
    HistoryTables histories_;
    std::unique_ptr<CorrectionHistory> correction_history_ = std::make_unique<CorrectionHistory>();
    std::unique_ptr<CorrectionHistory> material_correction_ = std::make_unique<CorrectionHistory>();
    std::array<SearchStack, MaxPly + 8> stack_{};
    std::array<Move, 256> root_effort_moves_{};
    std::array<std::uint64_t, 256> root_move_nodes_{};
    std::size_t root_effort_count_ = 0;

#ifdef FORGE_S13_TT_CHILD_PREFETCH
    bool s13_tt_child_prefetch_ = false;
#endif
    bool pondering_ = false;
    std::chrono::steady_clock::time_point start_{};
    std::atomic<std::uint64_t> nodes_{0};
    std::uint64_t local_nodes_ = 0;
    const std::vector<Worker*>* all_workers_ = nullptr;
    std::uint64_t node_limit_ = 0;
    bool node_limit_specified_ = false;
    std::int64_t soft_limit_ms_ = 0;
    std::int64_t hard_limit_ms_ = 0;
    bool time_managed_ = false;
    bool aborted_ = false;
    int seldepth_ = 0;
    int root_depth_ = 0;
    std::size_t root_history_index_ = 0;
    std::vector<Move> root_moves_;
    bool root_restricted_ = false;
    std::uint64_t null_tries_ = 0;
    std::uint64_t null_cutoffs_ = 0;
    // CorrHistPlus tables (forge/correction_plus.hpp), owned by this worker.
    // Null until the option is on and the first update allocates them; freed
    // by Worker::clear(). Last member, no initialiser: the members above keep
    // their AL1 s198 offsets.
    std::unique_ptr<corrplus::Tables> correction_plus_;
    // UCI HistRework (forge/hist_rework.hpp; A1). Last members, so every member above keeps its offset; read
    // and written only while the option is on. threat_maps_[ply] holds the lesser-attacker maps of the node at ply.
    std::unique_ptr<LesserThreatHistory> threat_history_ = std::make_unique<LesserThreatHistory>();
    std::unique_ptr<CorrectionHistory> joint_correction_ = std::make_unique<CorrectionHistory>();
    std::array<hist_rework::LesserThreats, MaxPly + 8> threat_maps_{};
    // FB2-J3 (forge/fb2.hpp; forge-bundle-int). Last members, so every member above keeps its offset.
    // fb2_ is this worker's per-search snapshot of the options (set at the start of Worker::search, read-only
    // during the search); continuation_correction_ is CorrHistV2's own table (CorrHistPlus never touches it).
    fb2::Options fb2_{};
    std::unique_ptr<fb2::ContinuationCorrection> continuation_correction_ = std::make_unique<fb2::ContinuationCorrection>();
#if FORGE_NNUE_LAZY_ACC
    LazyAccStats lazy_acc_stats_{};   // S12 NnueLazyAcc counters
#endif
#ifdef FORGE_PROF
    prof::Bank profile_bank_;   // S08fix profile counters
#endif
};

} // namespace forge
