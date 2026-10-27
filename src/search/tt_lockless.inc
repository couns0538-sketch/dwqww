// Search module: lockless transposition-table access (UCI LocklessTT, default
// off; forge/search_options.hpp). Compiled as part of src/search.cpp, included
// last so that the default functions keep their AL1 s198 code and placement.
//
// An entry (forge/tt.hpp, 16 bytes) is stored as two 64-bit words, each read
// and written with one relaxed atomic access, without the stripe locks:
//   second = bytes 8-15 of the entry (score, eval, depth, generation/bound,
//            rule-50 clock, padding), unchanged;
//   first  = the move (bytes 4-7) in the high half; in the low half the key
//            tag XOR a 32-bit hash of the move and of the second word.
// A read that sees the two words of different writes recovers a key tag that
// is off by the difference of two hashes, so the probe misses (and a store
// sees another position) instead of returning a torn entry; a false match
// needs a 32-bit hash collision. Probe, replacement and store rules are those
// of the locked functions in tt.inc, statement for statement, so a search with
// one thread is unchanged (bench identical with the option on).
// Concurrent writes to one slot can leave its two words from different writes;
// such a slot no longer matches any key and is replaced like any other entry.
//
// Placement: every function here is noinline and in section .text.forge_ltt,
// which the linker places after all .text. probe(), store() and hashfull() in
// tt.inc only gained one test of lockless_ that tail-jumps into this file;
// inlined, the lockless bodies would grow the default functions' frames.
#if defined(__GNUC__) || defined(__clang__)
#define FORGE_LTT_TEXT [[gnu::section(".text.forge_ltt"), gnu::noinline]]
#else
#define FORGE_LTT_TEXT
#endif

namespace forge {

namespace {

static_assert(sizeof(TTEntry) == 16 && offsetof(TTEntry, move) == 4 && offsetof(TTEntry, score) == 8 &&
                  alignof(TTCluster) == 64,
              "the lockless TT encoding assumes the 16-byte entry layout");

// Hash of the 96 data bits (move + second word) that guards the key tag.
[[nodiscard]] inline std::uint32_t lockless_check(std::uint32_t move_bits, std::uint64_t data) {
    std::uint64_t h = data ^ (static_cast<std::uint64_t>(move_bits) * 0x9E3779B97F4A7C15ULL);
    h *= 0xBF58476D1CE4E5B9ULL;
    h ^= h >> 31;
    h *= 0x94D049BB133111EBULL;
    return static_cast<std::uint32_t>(h >> 32);
}

// One 64-bit half of a table entry, accessed atomically. Entries sit at 16-byte
// offsets in 64-byte aligned clusters, so both halves are 8-byte aligned.
#if defined(__GNUC__) || defined(__clang__)
using TTWord [[gnu::may_alias]] = std::uint64_t;

[[nodiscard]] inline std::uint64_t load_word(const TTEntry& slot, std::size_t half) {
    return __atomic_load_n(reinterpret_cast<const TTWord*>(&slot) + half, __ATOMIC_RELAXED);
}

inline void store_word(TTEntry& slot, std::size_t half, std::uint64_t value) {
    __atomic_store_n(reinterpret_cast<TTWord*>(&slot) + half, value, __ATOMIC_RELAXED);
}
#else
[[nodiscard]] inline std::uint64_t load_word(const TTEntry& slot, std::size_t half) {
    auto* words = reinterpret_cast<std::uint64_t*>(const_cast<TTEntry*>(&slot));
    return std::atomic_ref<std::uint64_t>(words[half]).load(std::memory_order_relaxed);
}

inline void store_word(TTEntry& slot, std::size_t half, std::uint64_t value) {
    auto* words = reinterpret_cast<std::uint64_t*>(&slot);
    std::atomic_ref<std::uint64_t>(words[half]).store(value, std::memory_order_relaxed);
}
#endif

[[nodiscard]] inline std::array<std::uint64_t, 2> encode_entry(const TTEntry& entry) {
    std::uint32_t move_bits = 0;
    std::memcpy(&move_bits, &entry.move, sizeof move_bits);
    std::uint64_t second = 0;
    std::memcpy(&second, reinterpret_cast<const unsigned char*>(&entry) + 8, sizeof second);
    const std::uint32_t tag = entry.key32 ^ lockless_check(move_bits, second);
    return {(static_cast<std::uint64_t>(move_bits) << 32U) | tag, second};
}

[[nodiscard]] inline TTEntry decode_entry(std::uint64_t first, std::uint64_t second) {
    TTEntry entry;
    const auto move_bits = static_cast<std::uint32_t>(first >> 32U);
    entry.key32 = static_cast<std::uint32_t>(first) ^ lockless_check(move_bits, second);
    std::memcpy(&entry.move, &move_bits, sizeof move_bits);
    std::memcpy(reinterpret_cast<unsigned char*>(&entry) + 8, &second, sizeof second);
    return entry;
}

[[nodiscard]] inline TTEntry load_lockless(const TTEntry& slot) {
    const std::uint64_t second = load_word(slot, 1);
    const std::uint64_t first = load_word(slot, 0);
    return decode_entry(first, second);
}

inline void save_lockless(TTEntry& slot, const TTEntry& entry) {
    const auto words = encode_entry(entry);
    store_word(slot, 0, words[0]);
    store_word(slot, 1, words[1]);
}

} // namespace

FORGE_LTT_TEXT std::array<std::uint64_t, 2> TranspositionTable::encode_lockless(const TTEntry& entry) {
    return encode_entry(entry);
}

FORGE_LTT_TEXT TTEntry TranspositionTable::decode_lockless(std::uint64_t first, std::uint64_t second) {
    return decode_entry(first, second);
}

FORGE_LTT_TEXT void TranspositionTable::set_lockless(bool lockless) {
    if (lockless == lockless_) return;
    lockless_ = lockless;
    clear();
}

FORGE_LTT_TEXT TTProbe TranspositionTable::probe_lockless(std::uint64_t key) const {
    TTCluster& cluster = cluster_for(key);
    const std::size_t index = static_cast<std::size_t>(&cluster - clusters_.get());
    std::array<TTEntry, 4> entries;
    for (std::size_t i = 0; i < entries.size(); ++i) entries[i] = load_lockless(cluster.entries[i]);
    auto snapshot = [&](std::size_t slot, bool hit) {
        TTProbe result;
        result.entry = entries[slot];
        result.hit = hit;
        result.owner_ = this;
        result.cluster_ = index;
        result.slot_ = static_cast<std::uint8_t>(slot);
        result.epoch_ = epoch_;
        result.key_ = key;
        return result;
    };
    const std::uint32_t key32 = verification_key(key);
    for (std::size_t i = 0; i < entries.size(); ++i) {
        TTEntry& entry = entries[i];
        if (entry.key32 == key32 && entry.occupied()) {
            // Reused entries remain recent even when search returns a TT cutoff.
            if (entry.generation() != generation_) {
                entry.gen_bound = static_cast<std::uint8_t>(
                    (static_cast<unsigned>(generation_) << 3U) | (entry.gen_bound & 7U));
                save_lockless(cluster.entries[i], entry);
            }
            return snapshot(i, true);
        }
    }
    std::size_t replace = 0;
    auto relative_age = [this](const TTEntry& entry) {
        return static_cast<int>((32 + generation_ - entry.generation()) & 31U);
    };
    for (std::size_t i = 0; i < entries.size(); ++i) {
        const TTEntry& entry = entries[i];
        if (!entry.occupied()) return snapshot(i, false);
        if (entry.depth - 4 * relative_age(entry) < entries[replace].depth - 4 * relative_age(entries[replace])) {
            replace = i;
        }
    }
    return snapshot(replace, false);
}

FORGE_LTT_TEXT void TranspositionTable::store_lockless(const TTProbe& probe, std::uint64_t key, int score, int eval, Move move,
                                        int depth, Bound bound, bool pv, std::uint16_t halfmove_clock) {
    // Reject default, foreign or lifecycle-stale handles, as store() does.
    if (probe.owner_ != this || probe.epoch_ != epoch_ || probe.key_ != key ||
        probe.cluster_ >= cluster_count_ || probe.slot_ >= 4) return;
    TTEntry& slot = clusters_[probe.cluster_].entries[probe.slot_];
    TTEntry entry = load_lockless(slot);
    const TTEntry before = entry;
    const std::uint32_t key32 = verification_key(key);
    const bool same_position = entry.key32 == key32 && entry.occupied();
    if (!move.is_none() || !same_position) entry.move = move;
    if (bound == BoundExact || !same_position || depth + 4 > entry.depth || entry.generation() != generation_) {
        entry.key32 = key32;
        entry.score = static_cast<std::int16_t>(std::clamp(score, -32767, 32767));
        entry.rule50_clock = static_cast<std::uint8_t>(std::min<int>(halfmove_clock, 100));
        entry.eval = static_cast<std::int16_t>(std::clamp(eval, -32767, 32767));
        entry.depth = static_cast<std::uint8_t>(std::clamp(depth, 0, 255));
        entry.gen_bound = static_cast<std::uint8_t>((static_cast<unsigned>(generation_) << 3U) | (pv ? 4U : 0U) |
                                                    static_cast<unsigned>(bound));
    }
    if (std::memcmp(&entry, &before, sizeof entry) != 0) save_lockless(slot, entry);
}

FORGE_LTT_TEXT int TranspositionTable::hashfull_lockless() const {
    int count = 0;
    const std::size_t sample = std::min<std::size_t>(1000, cluster_count_);
    for (std::size_t i = 0; i < sample; ++i) {
        for (const TTEntry& slot : clusters_[i].entries) {
            const TTEntry entry = load_lockless(slot);
            if (entry.occupied() && entry.generation() == generation_) ++count;
        }
    }
    return sample == 0 ? 0 : count * 1000 / (4 * static_cast<int>(sample));
}

} // namespace forge

#undef FORGE_LTT_TEXT
