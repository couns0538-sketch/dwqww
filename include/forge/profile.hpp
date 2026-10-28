#pragma once

#ifdef FORGE_PROF
#include <array>
#include <cstddef>
#include <cstdint>
#include <iosfwd>

namespace forge::prof {

enum class Counter : std::size_t {
    Nodes, MainNodes, QsNodes, EvalRequests, HceComputations, NnueForward,
    NnueRefresh, TtProbes, TtHits, TtMisses, PickerVisits,
    PickerMainTT, PickerGenerateCaptures, PickerGoodCaptures, PickerKiller1,
    PickerKiller2, PickerCounterMove, PickerGenerateQuiets, PickerQuietMoves,
    PickerBadCaptures, PickerQsTT, PickerQsGenerate, PickerQsCaptures,
    PickerEvasionTT, PickerEvasionGenerate, PickerEvasions,
    RazorChecks, RazorSearches, RazorCutoffs,
    ProbCutChecks, ProbCutSearches, ProbCutCutoffs,
    IirChecks, IirReductions, LmpChecks, LmpActivations,
    FutilityChecks, FutilityPrunes, CaptureFutilityChecks, CaptureFutilityPrunes,
    HistoryChecks, HistoryPrunes, QuietSeeChecks, QuietSeePrunes,
    NoisySeeChecks, NoisySeePrunes, QsFutilityChecks, QsFutilityPrunes,
    QsSeeChecks, QsSeePrunes, SingularChecks, SingularSearches,
    SingularExtensions, SingularDoubleExtensions, SingularCutoffs,
    Count
};
constexpr std::size_t CounterCount=static_cast<std::size_t>(Counter::Count);
struct Snapshot {
    std::array<std::uint64_t,CounterCount> values{};
    bool overflow=false;
};

// One bank per search worker (S08-2). Only the owning worker's thread calls add() while a
// search runs, so the counters are plain integers: no shared atomics, no cache line written by
// two threads, so Threads>1 searches are not serialized or slowed by profiling. The bank is
// cache-line aligned so neighbouring data never shares its lines. reset/snapshot follow
// Searcher's quiescent controller contract (before helpers start / after they are joined);
// Searcher::profile_snapshot() merges the worker banks. Unsigned wrap is defined modulo 2^64
// and sets a sticky flag: wrapped totals are not valid frequencies.
class alignas(64) Bank {
public:
    void add(Counter event,std::uint64_t amount=1) noexcept {
        auto& value=values_[static_cast<std::size_t>(event)];
        const std::uint64_t previous=value;
        value=previous+amount;
        overflow_=overflow_ || value<previous;
    }
    void reset_quiescent() noexcept {
        values_.fill(0);
        overflow_=false;
    }
    [[nodiscard]] Snapshot snapshot_quiescent() const noexcept {
        Snapshot result;
        result.values=values_;
        result.overflow=overflow_;
        return result;
    }
private:
    std::array<std::uint64_t,CounterCount> values_{};
    bool overflow_=false;
};

// Constant initialization must be visible to every TU using this TLS slot.
extern thread_local constinit Bank* current_bank;
class Scope {
public:
    explicit Scope(Bank* bank) noexcept:previous_(current_bank) {current_bank=bank;}
    ~Scope() {current_bank=previous_;}
    Scope(const Scope&)=delete;
    Scope& operator=(const Scope&)=delete;
private:
    Bank* previous_;
};
inline void count(Counter event,std::uint64_t amount=1) noexcept {
    if (current_bank!=nullptr) current_bank->add(event,amount);
}
inline void picker_stage(std::size_t stage) noexcept {
    count(Counter::PickerVisits);
    count(static_cast<Counter>(static_cast<std::size_t>(Counter::PickerMainTT)+stage));
}
void merge(Snapshot& total,const Snapshot& delta) noexcept;
void write_snapshot(std::ostream& output,const Snapshot& snapshot);

} // namespace forge::prof
#endif
