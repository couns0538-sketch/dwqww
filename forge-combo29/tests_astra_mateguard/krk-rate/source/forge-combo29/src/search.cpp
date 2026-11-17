#include "forge/search.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <optional>

// FORGE_SDK_BADCAP_PREFIX (SDK long job 2026-11-06; default 0 = the code before it): the move picker keeps its
// losing captures in the already consumed front of moves_ instead of a separate array and generates the quiets
// behind them. Same moves in the same order (bit-exact); 1 KB less per picker, and the losing-capture list can
// never outgrow its storage (it only reuses slots of moves it has already handed out).
#ifndef FORGE_SDK_BADCAP_PREFIX
#define FORGE_SDK_BADCAP_PREFIX 0
#endif

#ifndef FORGE_BARE_KING_MATE_FIX
#define FORGE_BARE_KING_MATE_FIX 1
#endif

namespace forge {

namespace tune {
int LmrQuietBase = 85;
int LmrQuietDivisor = 220;
int LmrNoisyBase = 10;
int LmrNoisyDivisor = 340;
int NullMoveMinDepth = 3;
int NullMoveBase = 3;
int NullMoveDepthDivisor = 3;
int NullMoveEvalDivisor = 200;
int RfpDepth = 8;
int RfpMargin = 72;
int RfpImproving = 40;
int RazorDepth = 2;
int RazorBase = 150;
int RazorMultiplier = 350;
int FutilityDepth = 7;
int FutilityBase = 100;
int FutilityMultiplier = 110;
int LmpBase = 4;
int HistoryPruneDepth = 3;
int HistoryPruneMultiplier = 2048;
int SeeQuietMultiplier = 24;
int SeeNoisyMultiplier = 150;
int SingularDepth = 7;
int SingularMargin = 2;
int IirDepth = 4;
int ProbcutDepth = 5;
int ProbcutMargin = 180;
int QsFutilityMargin = 160;
int QsSeeMargin = 40;
int AspirationDelta = 18;
int HistoryBonusQuadratic = 20;
int HistoryBonusLinear = 48;
int HistoryBonusMax = 2048;
int LmrHistoryDivisor = 6000;
int CheckExtensionDepth = 2;
int LmrCutoffThreshold = 3;
int MaterialCorrectionWeight = 100;
int TmSoftDivisor = 22;
int TmIncrementPercent = 75;
int TmHardPercent = 60;
int TmHardSoftMultiple = 5;
int TmStableFactor = 60;
int TmSemiStableFactor = 80;
int TmUnstableFactor = 140;
int TmEffortBase = 155;
int TmFallingEvalPercent = 100;
int TmMinFactorPercent = 45;
int CaptureFutilityBase = 0;
int CaptureFutilityMultiplier = 250;
int CaptureFutilityDepth = 6;
int FailLowContinuationBonus = 0;
bool ContHist4PlyRead = false;
bool NonPawnCorrection = false;
bool LmrDeeperShallower = false;

const std::vector<Parameter>& parameters() {
    static const std::vector<Parameter> table{
        {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
        {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
        {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
        {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
        {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
        {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
        {"RfpImproving", &RfpImproving, 0, 200},         {"RazorDepth", &RazorDepth, 0, 6},
        {"RazorBase", &RazorBase, 0, 1000},              {"RazorMultiplier", &RazorMultiplier, 0, 1000},
        {"FutilityDepth", &FutilityDepth, 0, 15},        {"FutilityBase", &FutilityBase, 0, 500},
        {"FutilityMultiplier", &FutilityMultiplier, 0, 500},
        {"LmpBase", &LmpBase, 0, 20},                    {"HistoryPruneDepth", &HistoryPruneDepth, 0, 10},
        {"HistoryPruneMultiplier", &HistoryPruneMultiplier, 0, 20000},
        {"SeeQuietMultiplier", &SeeQuietMultiplier, 0, 200},
        {"SeeNoisyMultiplier", &SeeNoisyMultiplier, 0, 1000},
        {"SingularDepth", &SingularDepth, 2, 20},        {"SingularMargin", &SingularMargin, 0, 10},
        {"IirDepth", &IirDepth, 1, 20},                  {"ProbcutDepth", &ProbcutDepth, 1, 20},
        {"ProbcutMargin", &ProbcutMargin, 0, 1000},      {"QsFutilityMargin", &QsFutilityMargin, 0, 1000},
        {"QsSeeMargin", &QsSeeMargin, 0, 500},           {"AspirationDelta", &AspirationDelta, 4, 200},
        {"HistoryBonusQuadratic", &HistoryBonusQuadratic, 0, 100},
        {"HistoryBonusLinear", &HistoryBonusLinear, 0, 500},
        {"HistoryBonusMax", &HistoryBonusMax, 100, 10000},
        {"LmrHistoryDivisor", &LmrHistoryDivisor, 1000, 30000},
        {"CheckExtensionDepth", &CheckExtensionDepth, 1, 30},
        {"LmrCutoffThreshold", &LmrCutoffThreshold, 0, 20},
        {"MaterialCorrectionWeight", &MaterialCorrectionWeight, 0, 300},
        {"TmSoftDivisor", &TmSoftDivisor, 5, 80},            {"TmIncrementPercent", &TmIncrementPercent, 0, 150},
        {"TmHardPercent", &TmHardPercent, 10, 95},           {"TmHardSoftMultiple", &TmHardSoftMultiple, 1, 20},
        {"TmStableFactor", &TmStableFactor, 20, 150},        {"TmSemiStableFactor", &TmSemiStableFactor, 20, 150},
        {"TmUnstableFactor", &TmUnstableFactor, 50, 300},    {"TmEffortBase", &TmEffortBase, 100, 250},
        {"TmFallingEvalPercent", &TmFallingEvalPercent, 0, 400}, {"TmMinFactorPercent", &TmMinFactorPercent, 10, 100},
        {"CaptureFutilityBase", &CaptureFutilityBase, 0, 1000},  {"CaptureFutilityMultiplier", &CaptureFutilityMultiplier, 0, 1000},
        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},
    };
    return table;
}
} // namespace tune

namespace {

constexpr int HistoryMax = 16384;

[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score + ply;
    if (score <= -MateInMaxPly) return score - ply;
    return score;
}

[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= MateInMaxPly) return score - ply;
    if (score <= -MateInMaxPly) return score + ply;
    return score;
}

[[nodiscard]] int mated_in(int ply) { return -MateValue + ply; }
[[nodiscard]] int mate_in(int ply) { return MateValue - ply; }

struct ReductionTable {
    std::array<std::array<std::uint8_t, 64>, 64> quiet{};
    std::array<std::array<std::uint8_t, 64>, 64> noisy{};
    ReductionTable() { refresh(); }
    void refresh() {
        for (int depth = 1; depth < 64; ++depth) {
            for (int moves = 1; moves < 64; ++moves) {
                const double product = std::log(static_cast<double>(depth)) * std::log(static_cast<double>(moves));
                quiet[static_cast<std::size_t>(depth)][static_cast<std::size_t>(moves)] = static_cast<std::uint8_t>(
                    std::max(0.0, tune::LmrQuietBase / 100.0 + product / (tune::LmrQuietDivisor / 100.0)));
                noisy[static_cast<std::size_t>(depth)][static_cast<std::size_t>(moves)] = static_cast<std::uint8_t>(
                    std::max(0.0, tune::LmrNoisyBase / 100.0 + product / (tune::LmrNoisyDivisor / 100.0)));
            }
        }
    }
};
ReductionTable Reductions;

[[nodiscard]] int reduction(bool quiet, int depth, int moves) {
    const std::size_t d = static_cast<std::size_t>(std::min(depth, 63));
    const std::size_t m = static_cast<std::size_t>(std::min(moves, 63));
    return quiet ? Reductions.quiet[d][m] : Reductions.noisy[d][m];
}

[[nodiscard]] int lmp_threshold(int depth, bool improving) {
    return improving ? tune::LmpBase + depth * depth : (tune::LmpBase + depth * depth) / 2;
}

[[nodiscard]] int history_bonus(int depth) {
    return std::min(tune::HistoryBonusMax, tune::HistoryBonusQuadratic * depth * depth + tune::HistoryBonusLinear * depth - 32);
}

void apply_history(std::int16_t& entry, int bonus) {
    const int clamped = std::clamp(bonus, -HistoryMax, HistoryMax);
    entry = static_cast<std::int16_t>(entry + clamped - entry * std::abs(clamped) / HistoryMax);
}

[[nodiscard]] int capture_value(const Board& board, Move move) {
    int value = SeePieceValue[static_cast<std::size_t>(piece_type(board.captured_piece(move)))];
    if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
    return value;
}

#if FORGE_SEARCH_SPEED2
// Quiet history of one move: main history row of the side to move plus the continuation history of the two
// previous plies (and optionally 4 plies back at half weight), summed in this order (= Worker::quiet_history).
[[nodiscard]] inline int quiet_history_sum(const std::array<std::array<std::int16_t, 64>, 64>& main,
                                           const PieceToHistory* cont1, const PieceToHistory* cont2,
                                           const PieceToHistory* cont4, Piece piece, Move move) {
    const std::size_t p = static_cast<std::size_t>(piece);
    int score = main[move.from][move.to];
    if (cont1 != nullptr) score += (*cont1)[p][move.to];
    if (cont2 != nullptr) score += (*cont2)[p][move.to];
    if (cont4 != nullptr) score += (*cont4)[p][move.to] / 2;
    return score;
}
#endif

std::string format_score(int score) {
    if (is_mate_score(score)) {
        const int distance = MateValue - std::abs(score);
        const int mate = (distance + 1) / 2;
        return "mate " + std::to_string(score > 0 ? mate : -mate);
    }
    return "cp " + std::to_string(score);
}

} // namespace

void tune::refresh() { Reductions.refresh(); }

// ---------------------------------------------------------------------------
// Transposition table

thread_local const TranspositionTable::ExclusiveLease* TranspositionTable::active_lease_ = nullptr;

TranspositionTable::ExclusiveLease::ExclusiveLease(TranspositionTable& table)
    : table_(table), previous_(active_lease_), gate_(table.exclusive_gate_, std::defer_lock) {
    if (!table_.has_exclusive_access()) {
        gate_.lock();
        table_.exclusive_requested_.store(true, std::memory_order_release);
        try {
            // A foreign accessor either completes before its stripe drains,
            // or observes the request after acquiring that drained stripe.
            for (std::size_t i = 0; i < StripeCount; ++i) {
                const std::lock_guard<std::mutex> drain(table_.stripes_[i].mutex);
            }
        } catch (...) {
            table_.exclusive_requested_.store(false, std::memory_order_release);
            throw;
        }
    }
    active_lease_ = this;
}

TranspositionTable::ExclusiveLease::~ExclusiveLease() {
    // Publish completed writes before member destruction releases the gate.
    active_lease_ = previous_;
    if (gate_.owns_lock()) table_.exclusive_requested_.store(false, std::memory_order_release);
}

bool TranspositionTable::has_exclusive_access() const {
    for (const ExclusiveLease* lease = active_lease_; lease != nullptr; lease = lease->previous_) {
        if (&lease->table_ == this) return true;
    }
    return false;
}

std::unique_lock<std::mutex> TranspositionTable::lock_stripe(std::size_t index) const {
    std::mutex& stripe = stripes_[index % StripeCount].mutex;
    if (has_exclusive_access()) return std::unique_lock<std::mutex>(stripe, std::defer_lock);
    for (;;) {
        std::unique_lock<std::mutex> lock(stripe);
        if (!exclusive_requested_.load(std::memory_order_acquire)) return lock;
        // Never wait for the gate while holding a stripe: the owner drains it.
        lock.unlock();
        const std::lock_guard<std::mutex> wait(exclusive_gate_);
    }
}

void TranspositionTable::resize(std::size_t mb) {
    const std::size_t bytes = std::max<std::size_t>(1, mb) * 1024U * 1024U;
    const std::size_t new_count = std::max<std::size_t>(1, bytes / sizeof(TTCluster));
    auto new_clusters = std::make_unique<TTCluster[]>(new_count);
    clusters_ = std::move(new_clusters);
    cluster_count_ = new_count;
    generation_ = 0;
    ++epoch_;
}

void TranspositionTable::clear() {
    for (std::size_t i = 0; i < cluster_count_; ++i) clusters_[i] = TTCluster{};
    generation_ = 0;
    ++epoch_;
}

#if FORGE_SPD_TT_NOTLS
template <bool TakeLock>
TTProbe TranspositionTable::probe_body(std::uint64_t key) const {
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    // Owner calls (TakeLock false) skip lock_stripe: under the lease it only hands
    // back a deferred (unlocked) lock, after a thread_local lookup per call.
    const auto lock = TakeLock ? lock_stripe(index) : std::unique_lock<std::mutex>();
    auto snapshot = [&](const TTEntry& entry, bool hit) {
        TTProbe result;
        result.entry = entry;
        result.hit = hit;
        result.owner_ = this;
        result.cluster_ = index;
        result.slot_ = static_cast<std::uint8_t>(&entry - cluster.entries.data());
        result.epoch_ = epoch_;
        result.key_ = key;
        return result;
    };
    const std::uint32_t key32 = verification_key(key);
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            // Reused entries remain recent even when search returns a TT cutoff.
            if (entry.generation() != generation_) {
                entry.gen_bound = static_cast<std::uint8_t>(
                    (static_cast<unsigned>(generation_) << 3U) | (entry.gen_bound & 7U));
            }
            return snapshot(entry, true);
        }
    }
    const TTEntry* replace = &cluster.entries[0];
    auto relative_age = [this](const TTEntry& entry) {
        return static_cast<int>((32 + generation_ - entry.generation()) & 31U);
    };
    for (const TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) return snapshot(entry, false);
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;
    }
    return snapshot(*replace, false);
}

TTProbe TranspositionTable::probe(std::uint64_t key) const { return probe_body<true>(key); }

TTProbe TranspositionTable::probe_owned(std::uint64_t key) const {
    assert(has_exclusive_access());
    return probe_body<false>(key);
}

template <bool TakeLock>
void TranspositionTable::store_body(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth,
                                    Bound bound, bool pv, std::uint16_t halfmove_clock) {
    // Reject default, foreign or lifecycle-stale handles without touching storage.
    // Lifecycle operations themselves must not run concurrently with search.
    if (probe.owner_ != this || probe.epoch_ != epoch_ || probe.key_ != key ||
        probe.cluster_ >= cluster_count_ || probe.slot_ >= 4) return;
    const auto lock = TakeLock ? lock_stripe(probe.cluster_) : std::unique_lock<std::mutex>();
    TTEntry* entry = &clusters_[probe.cluster_].entries[probe.slot_];
    const std::uint32_t key32 = verification_key(key);
    const bool same_position = entry->key32 == key32 && entry->occupied();
    if (!move.is_none() || !same_position) entry->move = move;
    if (bound == BoundExact || !same_position || depth + 4 > entry->depth || entry->generation() != generation_) {
        entry->key32 = key32;
        entry->score = static_cast<std::int16_t>(std::clamp(score, -32767, 32767));
        entry->rule50_clock = static_cast<std::uint8_t>(std::min<int>(halfmove_clock, 100));
        entry->eval = static_cast<std::int16_t>(std::clamp(eval, -32767, 32767));
        entry->depth = static_cast<std::uint8_t>(std::clamp(depth, 0, 255));
        entry->gen_bound = static_cast<std::uint8_t>((static_cast<unsigned>(generation_) << 3U) | (pv ? 4U : 0U) | static_cast<unsigned>(bound));
    }
}

void TranspositionTable::store(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth,
                               Bound bound, bool pv, std::uint16_t halfmove_clock) {
    store_body<true>(probe, key, score, eval, move, depth, bound, pv, halfmove_clock);
}

void TranspositionTable::store_owned(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth,
                                     Bound bound, bool pv, std::uint16_t halfmove_clock) {
    assert(has_exclusive_access());
    store_body<false>(probe, key, score, eval, move, depth, bound, pv, halfmove_clock);
}
#else
TTProbe TranspositionTable::probe(std::uint64_t key) const {
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    const auto lock = lock_stripe(index);
    auto snapshot = [&](const TTEntry& entry, bool hit) {
        TTProbe result;
        result.entry = entry;
        result.hit = hit;
        result.owner_ = this;
        result.cluster_ = index;
        result.slot_ = static_cast<std::uint8_t>(&entry - cluster.entries.data());
        result.epoch_ = epoch_;
        result.key_ = key;
        return result;
    };
    const std::uint32_t key32 = verification_key(key);
    for (TTEntry& entry : cluster.entries) {
        if (entry.key32 == key32 && entry.occupied()) {
            // Reused entries remain recent even when search returns a TT cutoff.
            if (entry.generation() != generation_) {
                entry.gen_bound = static_cast<std::uint8_t>(
                    (static_cast<unsigned>(generation_) << 3U) | (entry.gen_bound & 7U));
            }
            return snapshot(entry, true);
        }
    }
    const TTEntry* replace = &cluster.entries[0];
    auto relative_age = [this](const TTEntry& entry) {
        return static_cast<int>((32 + generation_ - entry.generation()) & 31U);
    };
    for (const TTEntry& entry : cluster.entries) {
        if (!entry.occupied()) return snapshot(entry, false);
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;
    }
    return snapshot(*replace, false);
}

void TranspositionTable::store(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth,
                               Bound bound, bool pv, std::uint16_t halfmove_clock) {
    // Reject default, foreign or lifecycle-stale handles without touching storage.
    // Lifecycle operations themselves must not run concurrently with search.
    if (probe.owner_ != this || probe.epoch_ != epoch_ || probe.key_ != key ||
        probe.cluster_ >= cluster_count_ || probe.slot_ >= 4) return;
    const auto lock = lock_stripe(probe.cluster_);
    TTEntry* entry = &clusters_[probe.cluster_].entries[probe.slot_];
    const std::uint32_t key32 = verification_key(key);
    const bool same_position = entry->key32 == key32 && entry->occupied();
    if (!move.is_none() || !same_position) entry->move = move;
    if (bound == BoundExact || !same_position || depth + 4 > entry->depth || entry->generation() != generation_) {
        entry->key32 = key32;
        entry->score = static_cast<std::int16_t>(std::clamp(score, -32767, 32767));
        entry->rule50_clock = static_cast<std::uint8_t>(std::min<int>(halfmove_clock, 100));
        entry->eval = static_cast<std::int16_t>(std::clamp(eval, -32767, 32767));
        entry->depth = static_cast<std::uint8_t>(std::clamp(depth, 0, 255));
        entry->gen_bound = static_cast<std::uint8_t>((static_cast<unsigned>(generation_) << 3U) | (pv ? 4U : 0U) | static_cast<unsigned>(bound));
    }
}
#endif

int TranspositionTable::hashfull() const {
    int count = 0;
    const std::size_t sample = std::min<std::size_t>(1000, cluster_count_);
    for (std::size_t i = 0; i < sample; ++i) {
        const auto lock = lock_stripe(i);
        for (const TTEntry& entry : clusters_[i].entries) {
            if (entry.occupied() && entry.generation() == generation_) ++count;
        }
    }
    return sample == 0 ? 0 : count * 1000 / (4 * static_cast<int>(sample));
}

// ---------------------------------------------------------------------------
// Move picker

class MovePicker {
public:
    enum class Mode { Main, Quiescence };

    MovePicker(const Board& board, const Worker& searcher, const SearchStack* ss, Move tt_move, Mode mode)
        : board_(board), searcher_(searcher), ss_(ss), tt_move_(tt_move) {
        const bool in_check = board.in_check();
        if (!tt_move_.is_none() && !board_.is_pseudo_legal(tt_move_)) tt_move_ = Move::none();
        if (mode == Mode::Quiescence && !in_check && !tt_move_.is_none() && !tt_move_.is_capture() &&
            !tt_move_.is_promotion()) {
            tt_move_ = Move::none();
        }
        if (in_check) stage_ = tt_move_.is_none() ? EvasionGenerate : EvasionTT;
        else if (mode == Mode::Quiescence) stage_ = tt_move_.is_none() ? QsGenerate : QsTT;
        else stage_ = tt_move_.is_none() ? GenerateCaptures : MainTT;
        if (ss != nullptr) {
            killers_ = ss->killers;
            const SearchStack* previous = ss - 1;
            if (!previous->current_move.is_none() && previous->moved_piece != Empty) {
                counter_ = (*searcher_.counter_moves_)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to];
            }
        }
    }

    [[nodiscard]] Move next(bool skip_quiets) {
        while (true) {
            switch (stage_) {
            case MainTT:
            case QsTT:
            case EvasionTT:
                stage_ = static_cast<Stage>(stage_ + 1);
                return tt_move_;

            case GenerateCaptures:
                generate_captures();
                stage_ = GoodCaptures;
                [[fallthrough]];
            case GoodCaptures:
                while (index_ < count_) {
                    const Move move = pick_best();
                    if (move == tt_move_) continue;
                    if (!board_.see_ge(move, -move_score_threshold(move))) {
#if FORGE_SDK_BADCAP_PREFIX
                        // bad_count_ < index_: this slot's move has already been handed out (or skipped).
                        moves_[bad_count_++].move = move;
#else
                        bad_captures_[bad_count_++] = move;
#endif
                        continue;
                    }
                    return move;
                }
                stage_ = Killer1;
                [[fallthrough]];
            case Killer1:
                stage_ = Killer2;
                if (!skip_quiets && is_valid_quiet(killers_[0])) return killers_[0];
                [[fallthrough]];
            case Killer2:
                stage_ = CounterMove;
                if (!skip_quiets && is_valid_quiet(killers_[1]) && killers_[1] != killers_[0]) return killers_[1];
                [[fallthrough]];
            case CounterMove:
                stage_ = GenerateQuiets;
                if (!skip_quiets && is_valid_quiet(counter_) && counter_ != killers_[0] && counter_ != killers_[1]) {
                    return counter_;
                }
                [[fallthrough]];
            case GenerateQuiets:
                if (!skip_quiets) generate_quiets();
                stage_ = QuietMoves;
                [[fallthrough]];
            case QuietMoves:
                if (!skip_quiets) {
                    while (index_ < count_) {
                        const Move move = pick_best();
                        if (move == tt_move_ || move == killers_[0] || move == killers_[1] || move == counter_) continue;
                        return move;
                    }
                }
                stage_ = BadCaptures;
                bad_index_ = 0;
                [[fallthrough]];
            case BadCaptures:
#if FORGE_SDK_BADCAP_PREFIX
                if (bad_index_ < bad_count_) return moves_[bad_index_++].move;
#else
                if (bad_index_ < bad_count_) return bad_captures_[bad_index_++];
#endif
                return Move::none();

            case QsGenerate:
                generate_captures();
                stage_ = QsCaptures;
                [[fallthrough]];
            case QsCaptures:
                while (index_ < count_) {
                    const Move move = pick_best();
                    if (move == tt_move_) continue;
                    return move;
                }
                return Move::none();

            case EvasionGenerate:
                generate_evasions();
                stage_ = Evasions;
                [[fallthrough]];
            case Evasions:
                while (index_ < count_) {
                    const Move move = pick_best();
                    if (move == tt_move_) continue;
                    return move;
                }
                return Move::none();
            }
        }
    }

    // Valid for the move just returned by next(), until the next next() call.
    // Only Main/GoodCaptures returns after a successful SEE >= 0 test.
    [[nodiscard]] bool last_move_see_nonnegative() const { return stage_ == GoodCaptures; }

private:
    enum Stage : int {
        MainTT, GenerateCaptures, GoodCaptures, Killer1, Killer2, CounterMove, GenerateQuiets, QuietMoves, BadCaptures,
        QsTT, QsGenerate, QsCaptures,
        EvasionTT, EvasionGenerate, Evasions
    };
    struct Scored {
        Move move;
        int score;
    };

    const Board& board_;
    const Worker& searcher_;
    const SearchStack* ss_;
    Move tt_move_;
    std::array<Move, 2> killers_{};
    Move counter_{};
    Stage stage_;
#if FORGE_SPD_NO_ZERO_MOVELISTS
    // Every slot read is written first (moves_[index_ < count_], bad_captures_
    // [bad_index_ < bad_count_], check_squares_[1..6] after init_check_squares):
    // no zero fill at construction.
    std::array<Scored, 256> moves_;
#else
    std::array<Scored, 256> moves_{};
#endif
    std::size_t index_ = 0;
    std::size_t count_ = 0;
#if FORGE_SDK_BADCAP_PREFIX
    // Losing captures live in moves_[0, bad_count_).
#elif FORGE_SPD_NO_ZERO_MOVELISTS
    // Same capacity as the generator. A legal position can have more than 64
    // SEE-losing captures, and every one of them is stored.
    std::array<Move, MoveList::Capacity> bad_captures_;
#else
    std::array<Move, MoveList::Capacity> bad_captures_{};
#endif
    std::size_t bad_count_ = 0;
    std::size_t bad_index_ = 0;
    MoveList buffer_;
    std::size_t list_start_ = 0;
    bool sorted_ = false;
#if FORGE_SPD_NO_ZERO_MOVELISTS
    std::array<Bitboard, 7> check_squares_;
#else
    std::array<Bitboard, 7> check_squares_{};
#endif

    // Quiet/evasion generation are mutually exclusive stages, each reached at most once.
    void init_check_squares() {
        const Color them = opposite(board_.side_to_move());
        const int enemy_king = board_.king_square(them);
        const Bitboard occupancy = board_.occupied();
        check_squares_[Pawn] = attacks::pawn(them, enemy_king);
        check_squares_[Knight] = attacks::knight(enemy_king);
        check_squares_[Bishop] = attacks::bishop(enemy_king, occupancy);
        check_squares_[Rook] = attacks::rook(enemy_king, occupancy);
        check_squares_[Queen] = check_squares_[Bishop] | check_squares_[Rook];
        check_squares_[King] = 0;
    }

    [[nodiscard]] bool direct_check(Move move) const {
        const int type = piece_type(board_.moved_piece(move));
        return (check_squares_[static_cast<std::size_t>(type)] & square_bb(move.to)) != 0;
    }

#if FORGE_SEARCH_SPEED2
    // Quiet score = quiet_history_sum() + 12000 for a direct check; the history row and continuation tables
    // are fixed for one generation, so they are read once, and the moved piece once per move.
    struct QuietScorer {
        const std::array<std::array<std::int16_t, 64>, 64>& main;
        const PieceToHistory* cont1;
        const PieceToHistory* cont2;
        const PieceToHistory* cont4;
        const Board& board;

        QuietScorer(const Board& b, const Worker& searcher, const SearchStack* ss)
            : main((*searcher.main_history_)[static_cast<std::size_t>(b.side_to_move())]),
              cont1(ss != nullptr ? (ss - 1)->continuation : nullptr),
              cont2(ss != nullptr ? (ss - 2)->continuation : nullptr),
              cont4(tune::ContHist4PlyRead && ss != nullptr && !(ss - 4)->current_move.is_none()
                        ? (ss - 4)->continuation : nullptr),
              board(b) {}

        [[nodiscard]] int score(Move move, const std::array<Bitboard, 7>& check_squares) const {
            const Piece piece = board.piece_at(move.from);
            int value = quiet_history_sum(main, cont1, cont2, cont4, piece, move);
            if ((check_squares[static_cast<std::size_t>(piece_type(piece))] & square_bb(move.to)) != 0) value += 12000;
            return value;
        }
    };
#endif

    [[nodiscard]] static int move_score_threshold(Move) { return 0; }

    [[nodiscard]] bool is_valid_quiet(Move move) const {
        return !move.is_none() && move != tt_move_ && !move.is_capture() && !move.is_promotion() &&
               board_.is_pseudo_legal(move);
    }

    // Most nodes need only the first few moves: select those on demand and
    // sort the remainder once if the search gets that far.
    [[nodiscard]] Move pick_best() {
        if (!sorted_) {
            if (index_ - list_start_ < 4) {
                std::size_t best = index_;
                for (std::size_t i = index_ + 1; i < count_; ++i) {
                    if (moves_[i].score > moves_[best].score) best = i;
                }
                std::swap(moves_[index_], moves_[best]);
            } else {
                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_), moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });
                sorted_ = true;
            }
        }
        return moves_[index_++].move;
    }

    void sort_moves() {
        list_start_ = index_;
        sorted_ = false;
    }

    // First slot of the quiet list: behind the losing captures when they share moves_.
    [[nodiscard]] std::size_t quiet_start() const {
#if FORGE_SDK_BADCAP_PREFIX
        return bad_count_;
#else
        return 0;
#endif
    }

    void generate_captures() {
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, true);
        index_ = 0;
        count_ = 0;
#if FORGE_SEARCH_SPEED2
        const CaptureHistory& capture_history = *searcher_.capture_history_;
#endif
        for (const Move move : buffer_) {
#if FORGE_SEARCH_SPEED2
            const std::size_t moved = static_cast<std::size_t>(board_.piece_at(move.from));
            const std::size_t victim = static_cast<std::size_t>(piece_type(board_.captured_piece(move)));
            int value = SeePieceValue[victim];
            if (move.is_promotion()) value += SeePieceValue[move.promotion] - SeePieceValue[Pawn];
            int score = 10 * value + capture_history[moved][move.to][victim];
#else
            int score = 10 * capture_value(board_, move) + searcher_.capture_history_value(board_, move);
#endif
            if (move.is_promotion()) score += move.promotion == Queen ? 20000 : -5000;
            moves_[count_++] = Scored{move, score};
        }
        sort_moves();
    }

    void generate_quiets() {
#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
        // The quiets-only list is the full list minus every capture and
        // promotion, in the same order, so the filter is gone.
        init_check_squares();
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, Board::GenMode::Quiets);
        index_ = quiet_start();
        count_ = quiet_start();
#if FORGE_SEARCH_SPEED2
        const QuietScorer scorer(board_, searcher_, ss_);
        for (const Move move : buffer_) {
            moves_[count_++] = Scored{move, scorer.score(move, check_squares_)};
        }
#else
        for (const Move move : buffer_) {
            int score = searcher_.quiet_history(board_, ss_, move);
            if (direct_check(move)) score += 12000;
            moves_[count_++] = Scored{move, score};
        }
#endif
        sort_moves();
#else
        init_check_squares();
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, false);
        index_ = quiet_start();
        count_ = quiet_start();
#if FORGE_SEARCH_SPEED2
        const QuietScorer scorer(board_, searcher_, ss_);
        for (const Move move : buffer_) {
            if (move.is_capture() || move.is_promotion()) continue;
            moves_[count_++] = Scored{move, scorer.score(move, check_squares_)};
        }
#else
        for (const Move move : buffer_) {
            if (move.is_capture() || move.is_promotion()) continue;
            int score = searcher_.quiet_history(board_, ss_, move);
            if (direct_check(move)) score += 12000;
            moves_[count_++] = Scored{move, score};
        }
#endif
        sort_moves();
#endif
    }

    void generate_evasions() {
        init_check_squares();
        buffer_.clear();
        board_.generate_pseudo_legal(buffer_, false);
        index_ = 0;
        count_ = 0;
#if FORGE_SEARCH_SPEED2
        const QuietScorer scorer(board_, searcher_, ss_);
#endif
        for (const Move move : buffer_) {
            int score;
            if (move.is_capture() || move.is_promotion()) {
                score = 1'000'000 + 10 * capture_value(board_, move) -
                        SeePieceValue[static_cast<std::size_t>(piece_type(board_.moved_piece(move)))] / 10;
            } else {
#if FORGE_SEARCH_SPEED2
                score = scorer.score(move, check_squares_);
#else
                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);
#endif
            }
            moves_[count_++] = Scored{move, score};
        }
        sort_moves();
    }
};

// ---------------------------------------------------------------------------
// Searcher

Worker::Worker(SharedSearchState& shared, int id)
    : shared_(shared),
      id_(id),
      main_history_(std::make_unique<ButterflyHistory>()),
      capture_history_(std::make_unique<CaptureHistory>()),
      continuation_history_(std::make_unique<ContinuationHistory>()),
      counter_moves_(std::make_unique<CounterMoveTable>()),
      correction_history_(std::make_unique<CorrectionHistory>()),
      material_correction_(std::make_unique<CorrectionHistory>()),
      non_pawn_white_correction_(std::make_unique<CorrectionHistory>()),
      non_pawn_black_correction_(std::make_unique<CorrectionHistory>()) {
    clear();
}

Worker::~Worker() = default;

void Worker::clear() {
    evaluator_.clear();
    *main_history_ = ButterflyHistory{};
    *capture_history_ = CaptureHistory{};
    *continuation_history_ = ContinuationHistory{};
    *counter_moves_ = CounterMoveTable{};
    *correction_history_ = CorrectionHistory{};
    *material_correction_ = CorrectionHistory{};
    *non_pawn_white_correction_ = CorrectionHistory{};
    *non_pawn_black_correction_ = CorrectionHistory{};
    for (SearchStack& ss : stack_) ss = SearchStack{};
}

namespace {
// Hash of the piece counts of both sides, for material-indexed statistics.
[[nodiscard]] std::uint64_t material_key(const Board& board) {
    std::uint64_t key = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            key = key * 1099511628211ULL + static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))) + 1);
        }
    }
    return key * 0x9E3779B97F4A7C15ULL;
}

// Hash of non-pawn piece placements of one side, for non-pawn correction history.
[[nodiscard]] std::uint64_t non_pawn_key(const Board& board, Color color) {
    std::uint64_t key = static_cast<std::uint64_t>(color) * 0x517CC1B727220A95ULL;
    for (int type = Knight; type <= King; ++type) {
        const Bitboard bb = board.pieces(color, static_cast<PieceType>(type));
        key ^= bb * (0x9E3779B97F4A7C15ULL + static_cast<std::uint64_t>(type) * 0xBF58476D1CE4E5B9ULL);
        key = (key ^ (key >> 30U)) * 0x94D049BB133111EBULL;
    }
    return key ^ (key >> 31U);
}
} // namespace

int Worker::static_evaluate(const Board& board, SearchStack* ss) {
    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);
    const bool residual = nnue::residual();
    if (!ss->accumulator.valid) {
        // Walk back to the nearest valid accumulator, then replay the moves.
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->accumulator.valid) ++back;
        if (back >= ss->ply && !(ss - back - 1)->accumulator.valid) {
            nnue::refresh(board, ss->accumulator);
            if (residual) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
        } else {
            for (int i = back; i >= 0; --i) {
                nnue::update((ss - i - 1)->accumulator, (ss - i)->accumulator, (ss - i)->dirty);
                if (residual) Evaluator::update_runtime_psqt((ss - i - 1)->runtime_psqt, (ss - i)->runtime_psqt, (ss - i)->dirty);
            }
        }
    }
    const int network = nnue::evaluate(board, ss->accumulator);
    if (!residual) return network;
    if (!ss->runtime_psqt.valid) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    // A residual network is a learned correction on top of the hand-crafted evaluation.
    return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}

void Worker::record_move(SearchStack* ss, const Board& board, const Move& move) {
    // Called before make_move: the child's accumulator becomes stale and the
    // piece changes are remembered for the lazy update.
    if (!nnue::enabled || !nnue::available()) return;
    (ss + 1)->dirty = nnue::dirty_pieces(board, move);
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
}

void Worker::record_null_move(SearchStack* ss) {
    (ss + 1)->dirty.count = 0;
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
}

int Worker::corrected_eval(const Board& board, int raw_eval) const {
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    std::int32_t correction = (*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)];
    if (tune::MaterialCorrectionWeight > 0) {
        correction += (*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)] * tune::MaterialCorrectionWeight / 100;
    }
    if (tune::NonPawnCorrection) {
        const std::int32_t np_w = (*non_pawn_white_correction_)[side][non_pawn_key(board, White) & (CorrectionSize - 1U)];
        const std::int32_t np_b = (*non_pawn_black_correction_)[side][non_pawn_key(board, Black) & (CorrectionSize - 1U)];
        correction += (np_w + np_b) / 2;
    }
    return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);
}

void Worker::update_correction(const Board& board, int depth, int best_score, int static_eval) {
    const std::size_t side = static_cast<std::size_t>(board.side_to_move());
    const int diff = std::clamp((best_score - static_eval) * CorrectionGrain, -CorrectionLimit / 4, CorrectionLimit / 4);
    const int weight = std::min(depth + 1, 16);
    auto apply = [&](std::int32_t& entry) {
        entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);
    };
    apply((*correction_history_)[side][board.pawn_key() & (CorrectionSize - 1U)]);
    if (tune::MaterialCorrectionWeight > 0) apply((*material_correction_)[side][material_key(board) & (CorrectionSize - 1U)]);
    if (tune::NonPawnCorrection) {
        apply((*non_pawn_white_correction_)[side][non_pawn_key(board, White) & (CorrectionSize - 1U)]);
        apply((*non_pawn_black_correction_)[side][non_pawn_key(board, Black) & (CorrectionSize - 1U)]);
    }
}

std::int64_t Worker::elapsed_ms() const {
    auto origin = start_;
    if (pondering_) {
        const std::int64_t hit_ns = shared_.ponder_hit_ns.load(std::memory_order_relaxed);
        if (hit_ns == 0) return 0;
        origin = std::chrono::steady_clock::time_point(
            std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::nanoseconds(hit_ns)));
    }
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - origin).count();
}

std::uint64_t Worker::total_nodes() const {
    std::uint64_t total = local_nodes_;
    if (all_workers_ != nullptr) {
        for (const Worker* worker : *all_workers_) {
            if (worker != this) total += worker->nodes();
        }
    }
    return total;
}

bool Worker::should_stop_with(std::uint64_t pending_nodes) {
    if (shared_.stop.load(std::memory_order_relaxed)) return true;
    if (!is_main()) return false;
    if (node_limit_specified_ && total_nodes() + extra_nodes_ + pending_nodes >= node_limit_) {
        stopped_by_nodes_ = true;
        return true;
    }
    if (hard_limit_ms_ > 0) {
        if (pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0) return false;
        if (elapsed_ms() >= hard_limit_ms_) return true;
    }
    return false;
}

bool Worker::should_stop() {
    // Publish this thread's node count for the others at the same cadence.
    nodes_.store(local_nodes_, std::memory_order_relaxed);
    if (shared_.stop.load(std::memory_order_relaxed)) return true;
    if (parent_worker_ != nullptr) return parent_worker_->should_stop_with(local_nodes_);
    return should_stop_with(0);
}

bool Worker::is_draw(const Board& board, int ply) const {
    (void)ply;
    if (board.halfmove_clock() >= 100) {
        // Checkmate on the hundredth half-move still wins; everything else is a draw.
        return !board.in_check() || board.has_legal_move();
    }
    // Detect stalemate before TT cutoffs, stand pat or forward pruning can
    // replace its terminal draw score with a material evaluation.
    return board.is_repetition(root_history_index_) || board.is_insufficient_material() ||
           (!board.in_check() && !board.has_legal_move());
}

int Worker::quiet_history(const Board& board, const SearchStack* ss, Move move) const {
#if FORGE_SEARCH_SPEED2
    return quiet_history_sum((*main_history_)[static_cast<std::size_t>(board.side_to_move())],
                             ss != nullptr ? (ss - 1)->continuation : nullptr,
                             ss != nullptr ? (ss - 2)->continuation : nullptr,
                             tune::ContHist4PlyRead && ss != nullptr && !(ss - 4)->current_move.is_none()
                                 ? (ss - 4)->continuation : nullptr,
                             board.moved_piece(move), move);
#else
    const Piece piece = board.moved_piece(move);
    int score = (*main_history_)[static_cast<std::size_t>(board.side_to_move())][move.from][move.to];
    if (ss != nullptr) {
        if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[static_cast<std::size_t>(piece)][move.to];
        if ((ss - 2)->continuation != nullptr) score += (*(ss - 2)->continuation)[static_cast<std::size_t>(piece)][move.to];
        if (tune::ContHist4PlyRead && (ss - 4)->continuation != nullptr && !(ss - 4)->current_move.is_none()) {
            score += (*(ss - 4)->continuation)[static_cast<std::size_t>(piece)][move.to] / 2;
        }
    }
    return score;
#endif
}

int Worker::capture_history_value(const Board& board, Move move) const {
    const Piece piece = board.moved_piece(move);
    const int captured = piece_type(board.captured_piece(move));
    return (*capture_history_)[static_cast<std::size_t>(piece)][move.to][static_cast<std::size_t>(captured)];
}

void Worker::update_continuation(SearchStack* ss, Piece piece, int to, int bonus) {
    for (const int back : {1, 2, 4}) {
        const SearchStack* previous = ss - back;
        if (previous->continuation == nullptr || previous->current_move.is_none()) continue;
        apply_history((*previous->continuation)[static_cast<std::size_t>(piece)][static_cast<std::size_t>(to)],
                      back == 4 ? bonus / 2 : bonus);
    }
}

void Worker::update_quiet_stats(const Board& board, SearchStack* ss, Move move, int depth, const Move* quiets,
                                  int quiet_count) {
    const int bonus = history_bonus(depth);
    const Color us = board.side_to_move();
    if (ss->killers[0] != move) {
        ss->killers[1] = ss->killers[0];
        ss->killers[0] = move;
    }
    const SearchStack* previous = ss - 1;
    if (!previous->current_move.is_none() && previous->moved_piece != Empty) {
        (*counter_moves_)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to] = move;
    }
    const Piece piece = board.moved_piece(move);
    apply_history((*main_history_)[static_cast<std::size_t>(us)][move.from][move.to], bonus);
    update_continuation(ss, piece, move.to, bonus);
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -bonus);
    }
}

void Worker::update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count) {
    const int bonus = history_bonus(depth);
    if (best.is_capture()) {
        const Piece piece = board.moved_piece(best);
        const int captured = piece_type(board.captured_piece(best));
        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    for (int i = 0; i < capture_count; ++i) {
        const Move capture = captures[i];
        if (capture == best) continue;
        const Piece piece = board.moved_piece(capture);
        const int captured = piece_type(board.captured_piece(capture));
        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -bonus);
    }
}

// ---------------------------------------------------------------------------
// Quiescence search

int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {
    const bool pv_node = beta - alpha > 1;
    const int ply = ss->ply;
    if (((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
    if (aborted_) return 0;
    ++local_nodes_;
    seldepth_ = std::max(seldepth_, ply);
    ss->pv_length = 0;

    if (is_draw(board, ply)) return 0;
    if (ply >= MaxPly) return board.in_check() ? 0 : static_evaluate(board, ss);

    const bool in_check = board.in_check();
    ss->in_check = in_check;

    if (mate_moves_ > 0) {
        alpha = std::max(alpha, mated_in(ply));
        beta = std::min(beta, mate_in(ply + 1));
        if (alpha >= beta) return alpha;
    }

#if FORGE_SPD_TT_NOTLS
    const TTProbe tt_probe = probe_tt(board.key());
#else
    const TTProbe tt_probe = shared_.tt.probe(board.key());
#endif
    const bool tt_hit = tt_probe.hit;
    const TTEntry& tte = tt_probe.entry;
    const bool near50 = board.halfmove_clock() >= 90;
    const Move tt_move = tt_hit && (!near50 || tte.rule50_clock == board.halfmove_clock()) ? tte.move : Move::none();
    const int tt_score = tt_hit && tte.score_usable(board.halfmove_clock())
                             ? score_from_tt(tte.score, ply) : ValueNone;
    const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;
    const bool tt_pv = pv_node || (tt_hit && !near50 && tte.pv());
    if (!pv_node && !near50 && tt_hit && tt_score != ValueNone &&
        (mate_moves_ == 0 || (!is_mate_score(alpha) && !is_mate_score(beta))) &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;
    }

    int best_score;
    int futility_base;
    if (in_check) {
        ss->static_eval = ValueNone;
        best_score = futility_base = -Infinite;
    } else {
        int eval;
        if (tt_hit && tte.eval != ValueNone) ss->raw_eval = tte.eval;
        else ss->raw_eval = static_evaluate(board, ss);
        eval = ss->static_eval = corrected_eval(board, ss->raw_eval);
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
        best_score = eval;
        if (best_score >= beta) {
#if FORGE_SPD_TT_NOTLS
            if (!tt_hit) store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
#else
            if (!tt_hit) shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
#endif
            return best_score;
        }
        if (best_score > alpha) alpha = best_score;
        futility_base = ss->static_eval + tune::QsFutilityMargin;
    }

    MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
    Move best_move = Move::none();
    int move_count = 0;
    Move move;
    while (!(move = picker.next(false)).is_none()) {
        if (!board.is_legal(move)) continue;
        ++move_count;
        if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {
            const bool gives_check = board.gives_check(move);
            // Futility: even winning the captured piece cannot raise alpha.
            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
                best_score = std::max(best_score, futility_base + capture_value(board, move));
                continue;
            }
            if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
        }
#if FORGE_SPD_PREFETCH_EARLY
        std::uint64_t child_key = 0;
        const bool early_key = board.key_after(move, child_key);
        if (early_key) shared_.tt.prefetch(child_key);
#endif
        ss->current_move = move;
        ss->moved_piece = board.moved_piece(move);
        ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(ss->moved_piece)][move.to];
        (ss + 1)->ply = ply + 1;
        record_move(ss, board, move);
        Undo undo;
        (void)board.make_move(move, undo);
#if FORGE_SPD_PREFETCH_EARLY
        assert(!early_key || child_key == board.key());
        if (!early_key) shared_.tt.prefetch(board.key());
#else
        shared_.tt.prefetch(board.key());
#endif
        const int score = -qsearch(board, ss + 1, -beta, -alpha);
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (score >= beta) break;
                alpha = score;
            }
        }
    }
    if (in_check && move_count == 0) return mated_in(ply);

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
#if FORGE_SPD_TT_NOTLS
    store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
#else
    shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
#endif
    return best_score;
}

// ---------------------------------------------------------------------------
// Main alpha-beta search

int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
    const bool pv_node = beta - alpha > 1;
    const bool root_node = ss->ply == 0;
    const int ply = ss->ply;

    if (depth <= 0) return qsearch(board, ss, alpha, beta);
    // The frame is reused across siblings and same-ply verification searches.
    // Keep this call's inherited path budget independent of those mutations.
    const int inherited_double_extensions = (ss - 1)->double_extensions;
    ss->double_extensions = inherited_double_extensions;
    if (((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
    if (aborted_) return 0;
    ++local_nodes_;
    seldepth_ = std::max(seldepth_, ply);
    ss->pv_length = 0;
    ss->move_count = 0;

    if (!root_node) {
        if (is_draw(board, ply)) return 0;
        if (ply >= MaxPly) return board.in_check() ? 0 : static_evaluate(board, ss);
        // Mate distance pruning.
        alpha = std::max(alpha, mated_in(ply));
        beta = std::min(beta, mate_in(ply + 1));
        if (alpha >= beta) return alpha;
    }

    const bool in_check = board.in_check();
    ss->in_check = in_check;
    const Move excluded = ss->excluded_move;
    (ss + 1)->excluded_move = Move::none();
    (ss + 1)->cutoff_count = 0;
    // Children share killers with their siblings; grandchildren start afresh.
    (ss + 2)->killers = {};

    // Transposition table probe.
#if FORGE_SPD_TT_NOTLS
    const TTProbe tt_probe = probe_tt(board.key());
#else
    const TTProbe tt_probe = shared_.tt.probe(board.key());
#endif
    const bool tt_hit = tt_probe.hit;
    const TTEntry& tte = tt_probe.entry;
    const bool near50 = board.halfmove_clock() >= 90;
    const Move tt_move = tt_hit && (!near50 || tte.rule50_clock == board.halfmove_clock()) ? tte.move : Move::none();
    const int tt_score = tt_hit && tte.score_usable(board.halfmove_clock())
                             ? score_from_tt(tte.score, ply) : ValueNone;
    const int tt_depth = tt_hit ? tte.depth : -1;
    const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;
    const bool tt_capture = !tt_move.is_none() && tt_move.is_capture();
    ss->tt_pv = pv_node || (tt_hit && !near50 && tte.pv());

    if (!pv_node && excluded.is_none() && tt_hit && tt_score != ValueNone && tt_depth >= depth &&
        (mate_moves_ == 0 || (!is_mate_score(alpha) && !is_mate_score(beta))) &&
        board.halfmove_clock() < 90 &&
        (tt_bound == BoundExact || (tt_bound == BoundLower && tt_score >= beta) ||
         (tt_bound == BoundUpper && tt_score <= alpha))) {
        return tt_score;
    }

    // Static evaluation.
    int eval;
    if (in_check) {
        eval = ss->static_eval = ss->raw_eval = ValueNone;
    } else if (!excluded.is_none()) {
        eval = ss->static_eval;
    } else {
        if (tt_hit && tte.eval != ValueNone) ss->raw_eval = tte.eval;
        else ss->raw_eval = static_evaluate(board, ss);
        eval = ss->static_eval = corrected_eval(board, ss->raw_eval);
        if (tt_hit && tt_score != ValueNone &&
            ((tt_bound == BoundLower && tt_score > eval) || (tt_bound == BoundUpper && tt_score < eval) ||
             tt_bound == BoundExact)) {
            eval = tt_score;
        }
    }

    bool improving = false;
    if (!in_check) {
        if ((ss - 2)->static_eval != ValueNone) improving = ss->static_eval > (ss - 2)->static_eval;
        else if ((ss - 4)->static_eval != ValueNone) improving = ss->static_eval > (ss - 4)->static_eval;
        else improving = true;
    }

#if FORGE_BARE_KING_MATE_FIX
    const bool multi_worker = all_workers_ != nullptr && all_workers_->size() > 1;
    const bool bare_king_mode = multi_worker &&
        (board.occupied(White) == board.pieces(White, King) ||
         board.occupied(Black) == board.pieces(Black, King));
#else
    constexpr bool bare_king_mode = false;
#endif

    if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta) && mate_moves_ == 0 &&
        board.halfmove_clock() + depth < 100) {
        // Razoring: hopeless positions fall back to quiescence.
        if (!bare_king_mode && depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {
            const int razor = qsearch(board, ss, alpha - 1, alpha);
            if (aborted_) return 0;
            if (razor < alpha) return razor;
        }
        // Reverse futility pruning.
        if (!bare_king_mode && depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta &&
            eval < MateInMaxPly) {
            return eval;
        }
        // Null move pruning.
        if (!bare_king_mode && depth >= tune::NullMoveMinDepth && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
            ss->null_move_allowed && !(ss - 1)->current_move.is_none() &&
            board.has_non_pawn_material(board.side_to_move()) &&
            !(tt_hit && tt_bound == BoundUpper && tt_score < beta)) {
            ++null_tries_;
            const int reduction = tune::NullMoveBase + depth / tune::NullMoveDepthDivisor +
                                  std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);
            ss->current_move = Move::none();
            ss->moved_piece = Empty;
            ss->continuation = &(*continuation_history_)[Empty][0];
            (ss + 1)->ply = ply + 1;
            record_null_move(ss);
            NullUndo undo;
            board.make_null_move(undo);
#if FORGE_SEARCH_SPEED2
            shared_.tt.prefetch(board.key());
#endif
            int null_score = -search(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
            board.unmake_null_move(undo);
            if (aborted_) return 0;
            if (null_score >= beta) {
                if (is_mate_score(null_score)) null_score = beta;
                if (depth < 14) {
                    ++null_cutoffs_;
                    return null_score;
                }
                // Verification search at high depth guards against zugzwang.
                ss->null_move_allowed = false;
                const int verification = search(board, ss, depth - reduction, beta - 1, beta, false);
                ss->double_extensions = inherited_double_extensions;
                ss->null_move_allowed = true;
                if (aborted_) return 0;
                if (verification >= beta) {
                    ++null_cutoffs_;
                    return null_score;
                }
            }
        }
        // ProbCut: a good capture that beats beta by a margin at reduced depth.
        const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;
        if (depth >= tune::ProbcutDepth && !is_mate_score(beta) &&
            !(tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score < probcut_beta)) {
            MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
            Move move;
            while (!(move = picker.next(false)).is_none()) {
                if (move == excluded || !board.is_legal(move)) continue;
                if (!board.see_ge(move, probcut_beta - ss->static_eval)) continue;
                ss->current_move = move;
                ss->moved_piece = board.moved_piece(move);
                ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(ss->moved_piece)][move.to];
                (ss + 1)->ply = ply + 1;
                record_move(ss, board, move);
                Undo undo;
                (void)board.make_move(move, undo);
#if FORGE_SEARCH_SPEED2
                shared_.tt.prefetch(board.key());
#endif
                int value = -qsearch(board, ss + 1, -probcut_beta, -probcut_beta + 1);
                if (value >= probcut_beta && !aborted_) {
                    value = -search(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);
                }
                board.unmake_move(move, undo);
                if (aborted_) return 0;
                if (value >= probcut_beta) {
#if FORGE_SPD_TT_NOTLS
                    store_tt(tt_probe, board.key(), score_to_tt(value, ply), ss->raw_eval, move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());
#else
                    shared_.tt.store(tt_probe, board.key(), score_to_tt(value, ply), ss->raw_eval, move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());
#endif
                    return value;
                }
            }
        }
    }

    // Internal iterative reduction: no hash move suggests a less important node.
    if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;

    MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Main);
#if FORGE_SPD_NO_ZERO_MOVELISTS
    // Read only below their counts (update_quiet_stats / update_capture_stats).
    std::array<Move, 128> quiets_tried;
    std::array<Move, 64> captures_tried;
#else
    std::array<Move, 128> quiets_tried{};
    std::array<Move, 64> captures_tried{};
#endif
    int quiet_count = 0;
    int capture_count = 0;
    int best_score = -Infinite;
    Move best_move = Move::none();
    int move_count = 0;
    bool skip_quiets = false;
    const bool has_material = board.has_non_pawn_material(board.side_to_move());

    Move move;
    while (!(move = picker.next(skip_quiets)).is_none()) {
        if (move == excluded) continue;
        if (root_node && root_restricted_ &&
            std::none_of(root_moves_.begin(), root_moves_.end(), [&](const Move& m) { return m == move; })) {
            continue;
        }
        if (!board.is_legal(move)) continue;
        ++move_count;
        ss->move_count = move_count;
        const bool capture = move.is_capture();
        const bool quiet = !capture && !move.is_promotion();
        const bool gives_check = board.gives_check(move);
        const Piece moved = board.moved_piece(move);
        const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);

        // Shallow-depth pruning of unpromising moves.
        if (mate_moves_ == 0 && board.halfmove_clock() + depth < 100 && !root_node &&
            best_score > -MateInMaxPly && has_material && !bare_king_mode) {
            if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) skip_quiets = true;
            const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));
            if (quiet && !gives_check) {
                if (!in_check && lmr_depth <= tune::FutilityDepth &&
                    ss->static_eval + tune::FutilityBase + tune::FutilityMultiplier * lmr_depth <= alpha) {
                    skip_quiets = true;
                    continue;
                }
                if (lmr_depth <= tune::HistoryPruneDepth && history < -tune::HistoryPruneMultiplier * depth) continue;
                if (!board.see_ge(move, -tune::SeeQuietMultiplier * lmr_depth * lmr_depth)) continue;
            } else {
                // Futility pruning for captures: even winning the piece cannot
                // bring the position back to alpha.
                if (tune::CaptureFutilityBase > 0 && capture && !in_check && !gives_check &&
                    lmr_depth <= tune::CaptureFutilityDepth &&
                    ss->static_eval + tune::CaptureFutilityBase + tune::CaptureFutilityMultiplier * lmr_depth +
                            capture_value(board, move) + history / 8 <= alpha) {
                    continue;
                }
                const int see_threshold = -tune::SeeNoisyMultiplier * depth;
                if (!(picker.last_move_see_nonnegative() && see_threshold <= 0) &&
                    !board.see_ge(move, see_threshold)) continue;
            }
        }

        // Extensions.
        int extension = 0;
        if (mate_moves_ == 0 && !root_node && depth >= tune::SingularDepth && move == tt_move && excluded.is_none() &&
            tt_bound != BoundUpper && tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {
            const int singular_beta = tt_score - tune::SingularMargin * depth;
            const int singular_depth = (depth - 1) / 2;
            const bool saved_tt_pv = ss->tt_pv;
            ss->excluded_move = move;
            const int singular_score = search(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);
            ss->tt_pv = saved_tt_pv;
            ss->double_extensions = inherited_double_extensions;
            ss->excluded_move = Move::none();
            if (aborted_) return 0;
            if (singular_score < singular_beta) {
                extension = 1;
                if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {
                    extension = 2;
                }
            } else if (singular_beta >= beta) {
                return singular_beta;
            } else if (tt_score >= beta) {
                extension = -2;
            } else if (cut_node) {
                extension = -1;
            }
        } else if (mate_moves_ == 0 && gives_check && depth >= tune::CheckExtensionDepth && !root_node &&
                   (picker.last_move_see_nonnegative() || board.see_ge(move, 0))) {
            extension = 1;
        }
        ss->double_extensions = inherited_double_extensions + (extension == 2);
        int new_depth = depth - 1 + extension;

#if FORGE_SPD_PREFETCH_EARLY
        std::uint64_t child_key = 0;
        const bool early_key = board.key_after(move, child_key);
        if (early_key) shared_.tt.prefetch(child_key);
#endif
        ss->current_move = move;
        ss->moved_piece = moved;
        ss->continuation = &(*continuation_history_)[static_cast<std::size_t>(moved)][move.to];
        (ss + 1)->ply = ply + 1;
        record_move(ss, board, move);
        Undo undo;
        (void)board.make_move(move, undo);
#if FORGE_SPD_PREFETCH_EARLY
        assert(!early_key || child_key == board.key());
        if (!early_key) shared_.tt.prefetch(board.key());
#else
        shared_.tt.prefetch(board.key());
#endif
        const std::uint64_t nodes_before = local_nodes_;
        std::size_t root_effort_index = 0;
        if (root_node) {
            const auto root_effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);
            root_effort_index = static_cast<std::size_t>(std::find(root_effort_moves_.begin(), root_effort_end, move) - root_effort_moves_.begin());
            assert(root_effort_index < root_effort_count_);
        }

        int score = -Infinite;
        bool full_depth_needed = !pv_node || move_count > 1;
        if (mate_moves_ == 0 && board.halfmove_clock() + new_depth < 100 && depth >= 2 &&
            move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&
            (quiet || !ss->tt_pv || move_count > 4)) {
            int r = reduction(quiet, depth, move_count);
            if (ss->tt_pv) r -= 1;
            if (!improving) r += 1;
            if (cut_node) r += 2;
            if (tt_capture && quiet) r += 1;
            if (gives_check) r -= 1;
            if (in_check) r -= 1;
            if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
            const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);
            score = -search(board, ss + 1, reduced_depth, -alpha - 1, -alpha, true);
            full_depth_needed = score > alpha && reduced_depth < new_depth;
            if (full_depth_needed) {
                if (tune::LmrDeeperShallower) {
                    const bool do_deeper = score > best_score + 40 + 2 * new_depth;
                    const bool do_shallower = score < best_score + new_depth;
                    new_depth += static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
                }
                if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {
                    score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
                }
                full_depth_needed = false;
            }
            if (!aborted_ && quiet && score > alpha) {
                // A late quiet move that beat expectations deserves a history boost.
                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
            }
        }
        if (full_depth_needed && !aborted_) {
            score = -search(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
        }
        if (pv_node && !aborted_ && (move_count == 1 || score > alpha)) {
            score = -search(board, ss + 1, new_depth, -beta, -alpha, false);
        }
        board.unmake_move(move, undo);
        if (aborted_) return 0;
        if (root_node && root_effort_index < root_effort_count_)
            root_move_nodes_[root_effort_index] += local_nodes_ - nodes_before;

        if (score > best_score) {
            best_score = score;
            if (score > alpha) {
                best_move = move;
                if (pv_node) {
                    ss->pv[0] = move;
                    std::copy_n((ss + 1)->pv.begin(), (ss + 1)->pv_length, ss->pv.begin() + 1);
                    ss->pv_length = (ss + 1)->pv_length + 1;
                }
                if (score >= beta) {
                    ++ss->cutoff_count;
                    break;
                }
                alpha = score;
            }
        }
        if (quiet && quiet_count < static_cast<int>(quiets_tried.size())) quiets_tried[static_cast<std::size_t>(quiet_count++)] = move;
        else if (!quiet && capture_count < static_cast<int>(captures_tried.size())) captures_tried[static_cast<std::size_t>(capture_count++)] = move;
    }

    if (move_count == 0) {
        if (!excluded.is_none()) return alpha;
        if (root_node && root_restricted_) return 0;
        return in_check ? mated_in(ply) : 0;
    }

    if (best_score >= beta) {
        if (!best_move.is_capture() && !best_move.is_promotion()) {
            update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);
        }
        update_capture_stats(board, best_move, depth, captures_tried.data(), capture_count);
    } else if (!best_move.is_none() && (!best_move.is_capture() && !best_move.is_promotion())) {
        // Even without a cutoff, a new PV move earned its place.
        apply_history((*main_history_)[static_cast<std::size_t>(board.side_to_move())][best_move.from][best_move.to],
                      history_bonus(depth) / 4);
    } else if (tune::FailLowContinuationBonus > 0 && best_move.is_none() && !(ss - 1)->current_move.is_none() &&
               (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_capture() && ply > 0) {
        // Every move failed low: the parent's quiet move refuted this line.
        update_continuation(ss - 1, (ss - 1)->moved_piece, (ss - 1)->current_move.to,
                            history_bonus(depth) * tune::FailLowContinuationBonus / 100);
    }

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (excluded.is_none() && !(root_node && root_restricted_)) {
#if FORGE_SPD_TT_NOTLS
        store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
#else
        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
#endif
    }
    // Teach the static evaluation about this pawn structure when the search
    // result is a usable bound in the direction of the difference.
    if (!in_check && excluded.is_none() && !is_mate_score(best_score) &&
        (best_move.is_none() || !best_move.is_capture()) &&
        !(bound == BoundLower && best_score <= ss->static_eval) &&
        !(bound == BoundUpper && best_score >= ss->static_eval)) {
        update_correction(board, depth, best_score, ss->static_eval);
    }
    return best_score;
}

// ---------------------------------------------------------------------------
// Iterative deepening driver

SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {
    const auto origin = limits.start_time != std::chrono::steady_clock::time_point{}
        ? limits.start_time : limits.request_start;
    start_ = origin == std::chrono::steady_clock::time_point{}
        ? std::chrono::steady_clock::now() : origin;
    local_nodes_ = 0;
    nodes_.store(0, std::memory_order_relaxed);
    all_workers_ = &all;
    seldepth_ = 0;
    aborted_ = false;
    stopped_by_nodes_ = false;
    extra_nodes_ = 0;
    pondering_ = limits.ponder;
    null_tries_ = 0;
    null_cutoffs_ = 0;
    root_moves_ = limits.search_moves;
    root_restricted_ = limits.search_moves_specified;
    root_history_index_ = board.history_size() - 1;
    node_limit_ = limits.nodes;
    node_limit_specified_ = parent_worker_ != nullptr
        ? parent_worker_->node_limit_specified_
        : (is_main() && (limits.nodes_specified || limits.nodes != 0));

    // Time allocation.
    const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
    soft_limit_ms_ = hard_limit_ms_ = 0;
    time_managed_ = false;
    if (limits.infinite) {
        soft_limit_ms_ = hard_limit_ms_ = 0;
    } else if (limits.movetime_ms >= 0) {
        hard_limit_ms_ = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
        soft_limit_ms_ = hard_limit_ms_;
    } else if (limits.time_ms >= 0) {
        const std::int64_t time = limits.time_ms;
        const std::int64_t increment = std::max<std::int64_t>(0, limits.increment_ms);
        const std::int64_t available = std::max<std::int64_t>(1, time - overhead);
        std::int64_t soft;
        std::int64_t hard;
        if (limits.moves_to_go > 0) {
            const std::int64_t mtg = std::min<std::int64_t>(limits.moves_to_go, 50);
            soft = available / (mtg + 1) + increment * 3 / 4;
            hard = std::min(available * 4 / 5, soft * 4);
        } else {
            soft = available / tune::TmSoftDivisor + increment * tune::TmIncrementPercent / 100;
            hard = std::min(available * tune::TmHardPercent / 100, soft * tune::TmHardSoftMultiple);
        }
        soft_limit_ms_ = std::max<std::int64_t>(1, std::min(soft, available));
        hard_limit_ms_ = std::max<std::int64_t>(1, std::min(hard, available));
        time_managed_ = true;
    }
    SearchInfo result;
    const MoveList legal = board.legal_moves();
    MoveList root_candidates;
    for (const Move move : legal) {
        if (!root_restricted_ ||
            std::any_of(root_moves_.begin(), root_moves_.end(), [&](const Move& m) { return m == move; })) {
            root_candidates.push_back(move);
        }
    }
    result.restricted_root_empty = root_restricted_ && !legal.empty() && root_candidates.empty();
    if (result.restricted_root_empty && emit_info) {
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        std::cout << "info string searchmoves restriction has no legal root moves" << std::endl;
    }

    const int mate_moves = std::clamp(limits.mate_moves, 0, 32);
    mate_moves_ = mate_moves;
    const int mate_depth = mate_moves > 0 ? mate_moves * 2 - 1 : 64;
    const int max_depth = std::clamp(std::min(limits.depth, mate_depth), 1, 64);
    const int multipv = std::clamp(limits.multipv, 1, 8);
    // Overrides stay unset on the MultiPV 1 path, so that info line is unchanged.
    int pv_index = 1;
    int seldepth_override = -1;
    int hashfull_override = -1;
    std::uint64_t node_override = 0;
    bool use_node_override = false;

    auto emit = [&](int depth, int score, const std::vector<Move>& pv) {
        if (!emit_info) return;
        const std::int64_t elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count();
        const int shown_seldepth = seldepth_override >= 0 ? seldepth_override : seldepth_;
        const std::uint64_t nodes = use_node_override ? node_override : total_nodes();
        const std::uint64_t nps = elapsed > 0 ? nodes * 1000U / static_cast<std::uint64_t>(elapsed) : 0;
        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());
        const int shown_hash = hashfull_override >= 0 ? hashfull_override : shared_.tt.hashfull();
        std::cout << "info depth " << depth;
        if (multipv > 1) {
            // depth, multipv, score, then the usual fields, then pv.
            std::cout << " multipv " << pv_index << " score " << format_score(score)
                      << " seldepth " << std::max(shown_seldepth, depth);
        } else {
            std::cout << " seldepth " << std::max(shown_seldepth, depth) << " score " << format_score(score);
        }
        std::cout << " nodes " << nodes << " nps " << nps << " hashfull " << shown_hash << " time " << elapsed << " pv";
        for (const Move move : pv) std::cout << ' ' << Board::move_to_uci(move);
        std::cout << std::endl;
    };

    // Terminal or adjudicated roots: report without searching.
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
    if (root_candidates.empty() || root_drawn) {
        int score = 0;
        if (legal.empty() && board.in_check()) score = -MateValue;
        for (int depth = 1; depth <= max_depth; ++depth) {
            result.depth = depth;
            result.score = score;
            emit(depth, score, {});
            if (should_stop()) break;
        }
        if (!root_candidates.empty()) result.best_move = root_candidates.front();
        result.nodes = total_nodes();
        nodes_.store(local_nodes_, std::memory_order_relaxed);
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        return result;
    }

    // An explicit zero node budget is an immediate bounded answer.
    if (limits.nodes_specified && limits.nodes == 0) {
        result.best_move = root_candidates.front();
        result.depth = 0;
        return result;
    }

    // Dispatch and root setup may already have consumed the entire budget.
    // Check helpers too before they switch to the main worker's stop signal.
    if (hard_limit_ms_ > 0 && elapsed_ms() >= hard_limit_ms_) {
        result.best_move = root_candidates.front();
        result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_).count());
        return result;
    }
    if (!is_main()) {
        // Helpers run until the main thread stops them.
        soft_limit_ms_ = hard_limit_ms_ = 0;
        time_managed_ = false;
    }

    for (SearchStack& ss : stack_) {
        ss.pv_length = 0;
        ss.current_move = Move::none();
        ss.excluded_move = Move::none();
        ss.moved_piece = Empty;
        ss.static_eval = ValueNone;
        ss.continuation = &(*continuation_history_)[Empty][0];
        ss.double_extensions = 0;
        ss.null_move_allowed = true;
        ss.killers = {};
    }
    SearchStack* ss = &stack_[4];
    for (int i = 0; i < MaxPly + 4; ++i) stack_[static_cast<std::size_t>(i)].ply = i - 4;
    for (SearchStack& entry : stack_) {
        entry.accumulator.valid = false;
        entry.runtime_psqt.valid = false;
    }
    if (nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    }

    Move previous_best = Move::none();
    int stable_iterations = 0;
    int score = 0;
    int previous_score = ValueNone;
    root_effort_count_ = root_candidates.size();
    assert(root_effort_count_ <= root_effort_moves_.size());
    std::copy(root_candidates.begin(), root_candidates.end(), root_effort_moves_.begin());
    root_move_nodes_.fill(0);
    // Secondary lines use their own table and histories, so the primary
    // iterative deepening stays the MultiPV 1 search.
    std::unique_ptr<SharedSearchState> alt_shared;
    std::unique_ptr<Worker> alt_worker;
    std::vector<Worker*> alt_list;
    if (multipv > 1 && is_main()) {
        const std::size_t hash_mb = std::max<std::size_t>(
            1, shared_.tt.cluster_count() * sizeof(TTCluster) / (1024U * 1024U));
        alt_shared = std::make_unique<SharedSearchState>(hash_mb);
        alt_worker = std::make_unique<Worker>(*alt_shared, 0);
        alt_worker->parent_worker_ = this;
        alt_list.push_back(alt_worker.get());
    }
    for (int depth = 1; depth <= max_depth; ++depth) {
        root_depth_ = depth;
        int delta = tune::AspirationDelta;
        int alpha = -Infinite;
        int beta = Infinite;
        if (depth >= 4) {
            alpha = std::max(score - delta, -Infinite);
            beta = std::min(score + delta, Infinite);
        }
        int iteration_score = score;
        while (true) {
            ss->ply = 0;
            iteration_score = search(board, ss, depth, alpha, beta, false);
            if (aborted_) break;
            if (iteration_score <= alpha) {
                beta = (alpha + beta) / 2;
                alpha = std::max(iteration_score - delta, -Infinite);
            } else if (iteration_score >= beta) {
                beta = std::min(iteration_score + delta, Infinite);
            } else {
                break;
            }
            delta += delta / 2 + 4;
        }
        if (aborted_) {
            // A clock or external stop may keep a root move that already raised
            // alpha in this unfinished iteration, and the score stays the last
            // finished one. A node limit must not do that: training labels from
            // `go nodes` need the move and the score of one finished iteration.
            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
                !(result.pv.size() > 0 && result.pv[0] == ss->pv[0])) {
                result.best_move = ss->pv[0];
                result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }
            break;
        }
        score = iteration_score;
        result.score = score;
        result.depth = depth;
        result.seldepth = std::max(seldepth_, depth);
        result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
        if (!result.pv.empty()) result.best_move = result.pv.front();
        result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
        result.nodes = total_nodes();
        if (alt_worker && !result.pv.empty()) {
            struct PvLine {
                int score = 0;
                int seldepth = 0;
                int hashfull = 0;
                std::uint64_t nodes = 0;
                std::vector<Move> pv;
            };
            std::vector<PvLine> lines;
            lines.push_back(PvLine{score, seldepth_, shared_.tt.hashfull(), total_nodes(), result.pv});
            std::vector<Move> banned{result.pv.front()};
            const int line_count = std::min(multipv, static_cast<int>(root_candidates.size()));
            for (int index = 2; index <= line_count && !aborted_; ++index) {
                if (should_stop()) {
                    aborted_ = true;
                    break;
                }
                std::vector<Move> allowed;
                allowed.reserve(root_candidates.size());
                for (const Move candidate : root_candidates) {
                    if (std::find(banned.begin(), banned.end(), candidate) == banned.end())
                        allowed.push_back(candidate);
                }
                if (allowed.empty()) break;
                SearchLimits narrowed = limits;
                narrowed.multipv = 1;
                narrowed.depth = depth;
                narrowed.nodes = 0;
                narrowed.nodes_specified = false;
                narrowed.movetime_ms = -1;
                narrowed.time_ms = -1;
                narrowed.infinite = false;
                narrowed.ponder = false;
                narrowed.mate_moves = 0;
                narrowed.search_moves = std::move(allowed);
                narrowed.search_moves_specified = true;
                narrowed.start_time = {};
                narrowed.request_start = {};
                alt_shared->stop.store(false, std::memory_order_relaxed);
                alt_shared->ponder_hit_ns.store(0, std::memory_order_relaxed);
                alt_shared->tt.clear();
                alt_worker->clear();
                const SearchInfo alt = alt_worker->search(board, narrowed, false, alt_list);
                extra_nodes_ += alt.nodes;
                if (alt_worker->aborted_ || alt.depth < depth) {
                    aborted_ = true;
                    break;
                }
                if (alt.best_move.is_none()) break;
                if (std::find(banned.begin(), banned.end(), alt.best_move) != banned.end()) break;
                std::vector<Move> pv = alt.pv;
                if (pv.empty() || !(pv.front() == alt.best_move)) pv.insert(pv.begin(), alt.best_move);
                lines.push_back(PvLine{alt.score, alt.seldepth, alt_shared->tt.hashfull(), alt.nodes, std::move(pv)});
                banned.push_back(lines.back().pv.front());
            }
            // Rank by the exact score. Ties keep the primary line first.
            std::stable_sort(lines.begin(), lines.end(), [](const PvLine& a, const PvLine& b) {
                return a.score > b.score;
            });
            std::uint64_t shown_nodes = 0;
            for (std::size_t i = 0; i < lines.size(); ++i) {
                shown_nodes += lines[i].nodes;
                pv_index = static_cast<int>(i + 1);
                seldepth_override = lines[i].seldepth;
                hashfull_override = lines[i].hashfull;
                node_override = shown_nodes;
                use_node_override = true;
                emit(depth, lines[i].score, lines[i].pv);
            }
            pv_index = 1;
            seldepth_override = -1;
            hashfull_override = -1;
            use_node_override = false;
            if (!lines.empty() && !lines.front().pv.empty()) {
                result.score = lines.front().score;
                result.pv = lines.front().pv;
                result.best_move = lines.front().pv.front();
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
            }
            if (aborted_) break;
        } else {
            emit(depth, score, result.pv);
        }

        if (result.best_move == previous_best) ++stable_iterations;
        else stable_iterations = 0;
        previous_best = result.best_move;
        const int iteration_previous_score = previous_score;
        previous_score = score;

        if (mate_moves > 0 && score >= mate_in(mate_moves * 2 - 1)) break;
        if (should_stop()) break;
        if (time_managed_ && !(pondering_ && shared_.ponder_hit_ns.load(std::memory_order_relaxed) == 0)) {
            // Stop early when the best move has been stable; spend longer when it keeps changing.
            double factor = 1.0;
            if (stable_iterations >= 6) factor = tune::TmStableFactor / 100.0;
            else if (stable_iterations >= 3) factor = tune::TmSemiStableFactor / 100.0;
            else if (stable_iterations == 0 && depth >= 6) factor = tune::TmUnstableFactor / 100.0;
            // A best move that absorbed most of the effort is clearly best;
            // spend longer when the alternatives still draw attention.
            if (local_nodes_ > 0 && depth >= 6) {
                const auto effort_end = root_effort_moves_.begin() + static_cast<std::ptrdiff_t>(root_effort_count_);
                const auto best_effort = std::find(root_effort_moves_.begin(), effort_end, result.best_move);
                if (best_effort != effort_end) {
                    const auto index = static_cast<std::size_t>(best_effort - root_effort_moves_.begin());
                    const double effort = static_cast<double>(root_move_nodes_[index]) / static_cast<double>(local_nodes_);
                    factor *= std::clamp(tune::TmEffortBase / 100.0 - effort, 0.6, 1.4);
                }
            }
            // A falling evaluation deserves more thought.
            if (iteration_previous_score != ValueNone && !is_mate_score(score) && score < iteration_previous_score) {
                const int drop = std::min(iteration_previous_score - score, 150);
                factor *= 1.0 + drop * tune::TmFallingEvalPercent / 10000.0;
            }
            factor = std::max(factor, tune::TmMinFactorPercent / 100.0);
            if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_limit_ms_) * factor)) break;
        }
    }

    nodes_.store(local_nodes_, std::memory_order_relaxed);
    result.nodes = total_nodes() + extra_nodes_;
    result.seldepth = std::max(result.seldepth, seldepth_);
    result.elapsed_ms = static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count());
    if (result.best_move.is_none()) result.best_move = root_candidates.front();
    return result;
}

// ---------------------------------------------------------------------------
// Searcher facade

Searcher::Searcher(std::size_t hash_mb, int threads) : shared_(hash_mb) {
    set_threads(threads);
}

Searcher::~Searcher() = default;

void Searcher::set_threads(int threads) {
    const std::size_t count = static_cast<std::size_t>(std::clamp(threads, 1, 256));
    while (workers_.size() > count) workers_.pop_back();
    while (workers_.size() < count) {
        workers_.push_back(std::make_unique<Worker>(shared_, static_cast<int>(workers_.size())));
    }
}

void Searcher::resize_hash(std::size_t hash_mb) { shared_.tt.resize(hash_mb); }

void Searcher::clear_hash() {
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear_caches();
}

void Searcher::clear() {
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear();
}

SearchInfo Searcher::search(Board board, const SearchLimits& limits, bool emit_info, TTAccess table_access) {
    const auto supplied_start = limits.start_time != std::chrono::steady_clock::time_point{}
        ? limits.start_time : limits.request_start;
    const bool clocked = !limits.infinite && !limits.ponder &&
        (limits.time_ms >= 0 || limits.movetime_ms >= 0);
    const auto origin = supplied_start == std::chrono::steady_clock::time_point{} && clocked
        ? std::chrono::steady_clock::now() : supplied_start;
    SearchLimits worker_limits = limits;
    worker_limits.start_time = origin;
    // Above MultiPV 1 the helpers stay idle. Counting only the main worker
    // keeps node totals on the Threads 1 path (idle workers may hold old counts).
    std::vector<Worker*> all;
    if (worker_limits.multipv > 1) {
        all.push_back(workers_.front().get());
    } else {
        all.reserve(workers_.size());
        for (auto& worker : workers_) all.push_back(worker.get());
    }
    // Age the table once per search, before any worker can probe it.
    shared_.tt.new_search();
    std::optional<TranspositionTable::ExclusiveLease> exclusive;
    // MultiPV above 1 does not start helpers, so the main thread may own the
    // table the way a one-thread search does.
    const bool single_threaded = workers_.size() == 1 || worker_limits.multipv > 1;
    if (table_access == TTAccess::Exclusive && single_threaded) {
        exclusive.emplace(shared_.tt);
    }
#if FORGE_SPD_TT_NOTLS
    // This thread holds the lease (if one was taken) and runs the main worker
    // below; helpers exist only without a lease. Saved and restored, so a throw
    // or a nested search leaves the flag as it was.
    struct TtOwnedScope {
        Worker& worker;
        const bool previous;
        TtOwnedScope(Worker& w, bool owned) : worker(w), previous(w.tt_owned_) { worker.tt_owned_ = owned; }
        ~TtOwnedScope() { worker.tt_owned_ = previous; }
        TtOwnedScope(const TtOwnedScope&) = delete;
        TtOwnedScope& operator=(const TtOwnedScope&) = delete;
    } tt_owned_scope(*workers_.front(), exclusive.has_value());
#endif
    std::vector<std::thread> helpers;
    // MultiPV above 1 runs only the main thread. Helper threads search one line
    // and would race the excluded-root passes, so this falls back to Threads 1.
    if (worker_limits.multipv <= 1) {
        for (std::size_t i = 1; i < workers_.size(); ++i) {
            helpers.emplace_back([this, i, board, &worker_limits, &all]() {
                (void)workers_[i]->search(board, worker_limits, false, all);
            });
        }
    }
    SearchInfo result = workers_.front()->search(board, worker_limits, emit_info, all);
    // Wind down the helpers without clobbering an externally requested stop.
    const bool external_stop = shared_.stop.load(std::memory_order_relaxed);
    shared_.stop.store(true, std::memory_order_relaxed);
    for (auto& helper : helpers) helper.join();
    shared_.stop.store(external_stop, std::memory_order_relaxed);
    return result;
}

} // namespace forge
