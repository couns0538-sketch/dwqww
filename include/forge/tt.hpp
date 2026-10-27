#pragma once

#include "forge/search_types.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>

namespace forge {

struct TTEntry {
    std::uint32_t key32 = 0;
    Move move{};
    std::int16_t score = 0;
    std::int16_t eval = 0;
    std::uint8_t depth = 0;
    // Bits 0..1 bound, bit 2 was-PV, bits 3..7 generation.
    std::uint8_t gen_bound = 0;
    std::uint8_t rule50_clock = 0; // Capped at100; belongs to admitted score payload.
    std::uint8_t padding = 0;

    [[nodiscard]] Bound bound() const { return static_cast<Bound>(gen_bound & 3U); }
    [[nodiscard]] bool pv() const { return (gen_bound & 4U) != 0; }
    [[nodiscard]] std::uint8_t generation() const { return static_cast<std::uint8_t>(gen_bound >> 3U); }
    [[nodiscard]] bool occupied() const { return bound() != BoundNone; }
    // Existing below90 policy, plus exact near50 context; not a repetition key.
    [[nodiscard]] bool score_usable(std::uint16_t current_clock) const {
        const int capped = current_clock < 100 ? current_clock : 100;
        return (rule50_clock < 90 && capped < 90) || rule50_clock == capped;
    }
};

struct alignas(64) TTCluster {
    std::array<TTEntry, 4> entries{};
};
static_assert(sizeof(TTEntry) == 16);
static_assert(sizeof(TTCluster) == 64);

class TranspositionTable;

// Immutable entry copy plus an opaque probe-time replacement destination.
struct TTProbe {
    TTEntry entry{};
    bool hit = false;
private:
    friend class TranspositionTable;
    const TranspositionTable* owner_ = nullptr;
    std::size_t cluster_ = 0;
    std::uint8_t slot_ = 0;
    std::uint64_t epoch_ = 0;
    std::uint64_t key_ = 0;
};

// Search reads and writes are coherent under striped locks (with LocklessTT:
// without locks, torn entries detected by their key check). clear/resize/
// new_search/destruction require all accessors quiescent (including diagnostic
// readers and prefetch callers) and invalidate old probes. Handles must not
// outlive the table; lifecycle operations are not safe concurrently with search.
class TranspositionTable {
public:
    explicit TranspositionTable(std::size_t mb = 32) { resize(mb); }
    void resize(std::size_t mb);
    void clear();
    void new_search() { generation_ = static_cast<std::uint8_t>((generation_ + 1U) & 31U); ++epoch_; }
    // Pinned to 64-byte boundaries, as the search functions (forge/search.hpp).
    [[nodiscard, gnu::aligned(64)]] TTProbe probe(std::uint64_t key) const;
    [[gnu::aligned(64)]] void store(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound, bool pv, std::uint16_t halfmove_clock);
    [[nodiscard]] int hashfull() const;
    [[nodiscard]] std::uint8_t generation() const { return generation_; }
    [[nodiscard]] std::size_t cluster_count() const { return cluster_count_; }
    // UCI LocklessTT (src/search/tt_lockless.inc): probe/store/hashfull without
    // the stripe locks. Lifecycle operation: all accessors quiescent. The two
    // modes store entries differently, so a change clears the table.
    void set_lockless(bool lockless);
    [[nodiscard]] bool lockless() const { return lockless_; }
    // The lockless form of one entry: {move << 32 | key tag ^ check, bytes 8-15}.
    [[nodiscard]] static std::array<std::uint64_t, 2> encode_lockless(const TTEntry& entry);
    [[nodiscard]] static TTEntry decode_lockless(std::uint64_t first, std::uint64_t second);
    void prefetch(std::uint64_t key) const {
#if defined(__GNUC__) || defined(__clang__)
        __builtin_prefetch(&cluster_for(key));
#else
        (void)key;
#endif
    }

private:
    friend class Searcher;
    static constexpr std::size_t StripeCount = 1024;
    struct alignas(64) Stripe { std::mutex mutex; };
    // Opt-in controller ownership: request exclusive access, drain each stripe,
    // then publish TLS. Lifecycle mutations still require all users quiescent.
    class ExclusiveLease {
    public:
        explicit ExclusiveLease(TranspositionTable& table);
        ~ExclusiveLease();
        ExclusiveLease(const ExclusiveLease&) = delete;
        ExclusiveLease& operator=(const ExclusiveLease&) = delete;
        ExclusiveLease(ExclusiveLease&&) = delete;
        ExclusiveLease& operator=(ExclusiveLease&&) = delete;
    private:
        friend class TranspositionTable;
        TranspositionTable& table_;
        const ExclusiveLease* previous_;
        std::unique_lock<std::mutex> gate_;
    };
    static thread_local const ExclusiveLease* active_lease_;
    [[nodiscard]] bool has_exclusive_access() const;
    [[nodiscard]] std::unique_lock<std::mutex> lock_stripe(std::size_t index) const;
    mutable std::array<Stripe, StripeCount> stripes_{};
    mutable std::mutex exclusive_gate_;
    std::atomic<bool> exclusive_requested_{false};
    std::uint64_t epoch_ = 0;
    std::unique_ptr<TTCluster[]> clusters_;
    std::size_t cluster_count_ = 0;
    std::uint8_t generation_ = 0;
    bool lockless_ = false;

    [[nodiscard]] TTProbe probe_lockless(std::uint64_t key) const;
    void store_lockless(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move, int depth, Bound bound,
                        bool pv, std::uint16_t halfmove_clock);
    [[nodiscard]] int hashfull_lockless() const;

    [[nodiscard]] static constexpr std::uint32_t verification_key(std::uint64_t key) {
#if defined(__SIZEOF_INT128__)
        // Multiply-high indexing consumes high key bits. Keep the independent
        // low bits as the tag, rather than reusing the bucket's index bits.
        return static_cast<std::uint32_t>(key);
#else
        // Modulo indexing consumes low bits for power-of-two table sizes.
        return static_cast<std::uint32_t>(key >> 32U);
#endif
    }

    [[nodiscard]] TTCluster& cluster_for(std::uint64_t key) const {
#if defined(__SIZEOF_INT128__)
        __extension__ using u128 = unsigned __int128;
        return clusters_[static_cast<std::size_t>((static_cast<u128>(key) * cluster_count_) >> 64U)];
#else
        return clusters_[static_cast<std::size_t>(key % cluster_count_)];
#endif
    }
};

} // namespace forge
