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
                  offsetof(TTEntry, depth) == 12 && offsetof(TTEntry, gen_bound) == 13 && alignof(TTCluster) == 64,
              "the lockless TT encoding assumes the 16-byte entry layout");
static_assert(std::endian::native == std::endian::little, "the lockless TT reads entry fields from its words");

// Hash of the 96 data bits (move + second word) that guards the key tag: the
// high half of one 64-bit product. Two writes with different data give
// different products (the multiplier is odd), so a mixed slot keeps its tag
// only if the products' high halves collide (about 2^-32 for TT data).
[[nodiscard]] inline std::uint32_t lockless_check(std::uint32_t move_bits, std::uint64_t data) {
    const std::uint64_t spread = (static_cast<std::uint64_t>(move_bits) << 32U) | move_bits;
    const std::uint64_t h = (data ^ spread) * 0x9E3779B97F4A7C15ULL;
    return static_cast<std::uint32_t>(h >> 32);
}

// Fields of the payload word (entry bytes 8-15) used without decoding.
[[nodiscard]] inline unsigned payload_depth(std::uint64_t second) { return static_cast<unsigned>(second >> 32U) & 0xFFU; }
[[nodiscard]] inline unsigned payload_gen_bound(std::uint64_t second) { return static_cast<unsigned>(second >> 40U) & 0xFFU; }

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
    // Raw words of the four slots. Occupancy, depth and generation sit in the
    // payload word; the key check is computed only for occupied slots, in slot
    // order, until one matches (the locked probe's order of decisions).
    std::array<std::uint64_t, 4> first{};
    std::array<std::uint64_t, 4> second{};
    for (std::size_t i = 0; i < 4; ++i) {
        second[i] = load_word(cluster.entries[i], 1);
        first[i] = load_word(cluster.entries[i], 0);
    }
    auto snapshot = [&](std::size_t slot, const TTEntry& entry, bool hit) {
        TTProbe result;
        result.entry = entry;
        result.hit = hit;
        result.owner_ = this;
        result.cluster_ = index;
        result.slot_ = static_cast<std::uint8_t>(slot);
        result.epoch_ = epoch_;
        result.key_ = key;
        return result;
    };
    const std::uint32_t key32 = verification_key(key);
    for (std::size_t i = 0; i < 4; ++i) {
        if ((payload_gen_bound(second[i]) & 3U) == BoundNone) continue;
        const auto move_bits = static_cast<std::uint32_t>(first[i] >> 32U);
        if ((static_cast<std::uint32_t>(first[i]) ^ lockless_check(move_bits, second[i])) != key32) continue;
        TTEntry entry = decode_entry(first[i], second[i]);
        // Reused entries remain recent even when search returns a TT cutoff.
        if (entry.generation() != generation_) {
            entry.gen_bound = static_cast<std::uint8_t>(
                (static_cast<unsigned>(generation_) << 3U) | (entry.gen_bound & 7U));
            save_lockless(cluster.entries[i], entry);
        }
        return snapshot(i, entry, true);
    }
    auto priority = [this](std::uint64_t payload) {
        const unsigned gen_bound = payload_gen_bound(payload);
        const int relative_age = static_cast<int>((32 + generation_ - (gen_bound >> 3U)) & 31U);
        return static_cast<int>(payload_depth(payload)) - 4 * relative_age;
    };
    std::size_t replace = 0;
    for (std::size_t i = 0; i < 4; ++i) {
        if ((payload_gen_bound(second[i]) & 3U) == BoundNone) return snapshot(i, decode_entry(first[i], second[i]), false);
        if (priority(second[i]) < priority(second[replace])) replace = i;
    }
    return snapshot(replace, decode_entry(first[replace], second[replace]), false);
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
