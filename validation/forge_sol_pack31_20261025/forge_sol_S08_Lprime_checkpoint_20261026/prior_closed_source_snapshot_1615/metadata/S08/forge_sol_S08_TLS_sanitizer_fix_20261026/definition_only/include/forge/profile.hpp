#pragma once

#ifdef FORGE_PROF
#include <array>
#include <atomic>
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

// Lifetime/reset/read follow Searcher's quiescent controller contract.
// Only add() is called by active workers. Unsigned wrap is defined modulo
// 2^64 and sets a sticky flag: wrapped totals are not valid frequencies.
class Bank {
public:
    void add(Counter event,std::uint64_t amount=1) noexcept {
        const auto previous=values_[static_cast<std::size_t>(event)].fetch_add(amount,std::memory_order_relaxed);
        if (previous+amount<previous) overflow_.store(true,std::memory_order_relaxed);
    }
    void reset_quiescent() noexcept {
        for (auto& value:values_) value.store(0,std::memory_order_relaxed);
        overflow_.store(false,std::memory_order_relaxed);
    }
    [[nodiscard]] Snapshot snapshot_quiescent() const noexcept {
        Snapshot result;
        for (std::size_t i=0;i<CounterCount;++i) result.values[i]=values_[i].load(std::memory_order_relaxed);
        result.overflow=overflow_.load(std::memory_order_relaxed);
        return result;
    }
private:
    std::array<std::atomic<std::uint64_t>,CounterCount> values_{};
    std::atomic<bool> overflow_{false};
};

extern thread_local Bank* current_bank;
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
