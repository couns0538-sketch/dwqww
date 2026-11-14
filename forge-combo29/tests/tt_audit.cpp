// Transposition-table audit. Links the engine without uci.cpp.
// score_from_tt takes the halfmove clock; search.cpp has no two-argument overload.

#include "forge/search.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <vector>

namespace forge {
struct TTAuditAccess {
    static std::size_t cluster_index(const TranspositionTable& tt, std::uint64_t key) {
        return static_cast<std::size_t>(&tt.cluster_for(key) - tt.clusters_.get());
    }
    static std::uint32_t tag(std::uint64_t key) { return TranspositionTable::verification_key(key); }
};
} // namespace forge

namespace {

int g_fails = 0;

void expect(bool cond, const std::string& msg) {
    if (cond) {
        std::cout << "PASS " << msg << "\n";
        return;
    }
    std::cout << "FAIL " << msg << "\n";
    ++g_fails;
}

forge::Move make_move(int from, int to) {
    forge::Move move{};
    move.from = static_cast<std::uint8_t>(from);
    move.to = static_cast<std::uint8_t>(to);
    move.promotion = 0;
    move.flags = 0;
    return move;
}

std::vector<std::uint64_t> keys_in_one_cluster(const forge::TranspositionTable& tt, int count) {
    const std::uint64_t base = 0x1234ULL << 50;
    const std::size_t cluster = forge::TTAuditAccess::cluster_index(tt, base);
    std::vector<std::uint64_t> keys;
    for (std::uint32_t tag = 1; keys.size() < static_cast<std::size_t>(count) && tag < 100000; ++tag) {
        const std::uint64_t key = base | tag;
        if (forge::TTAuditAccess::cluster_index(tt, key) == cluster && forge::TTAuditAccess::tag(key) == tag)
            keys.push_back(key);
    }
    return keys;
}

void test_score_conversion() {
    using namespace forge;
    expect(score_from_tt(100, 4, 0) == 100, "cp score is unchanged");
    expect(score_from_tt(ValueNone, 4, 50) == ValueNone, "ValueNone stays ValueNone");
    expect(score_to_tt(MateValue - 5, 4) == MateValue - 1, "mate in 1 at ply 4 stores distance 1");
    expect(score_from_tt(MateValue - 1, 4, 0) == MateValue - 5, "distance 1 restores the ply-adjusted mate");
    expect(score_from_tt(MateValue - 10, 0, 0) == MateValue - 10, "distance 10 fits in a fresh 50-move clock");
    expect(score_from_tt(MateValue - 10, 0, 95) == ValueNone, "distance 10 does not fit in 5 halfmoves");
    expect(score_from_tt(MateValue - 1, 0, 99) == MateValue - 1, "mate in 1 fits at clock 99");
    expect(score_from_tt(MateValue - 1, 4, 99) == MateValue - 5, "mate in 1 at ply 4 still fits at clock 99");
    expect(score_from_tt(MateValue - 1, 0, 100) == ValueNone, "mate in 1 does not fit at clock 100");
    expect(score_from_tt(-MateValue, 3, 100) == -MateValue + 3, "already-mated score is kept at clock 100");
    expect(score_from_tt(-(MateValue - 10), 2, 95) == ValueNone, "loss in 10 does not fit in 5 halfmoves");
    expect(score_from_tt(-(MateValue - 10), 2, 0) == -(MateValue - 10) + 2, "loss in 10 fits at clock 0");
    expect(score_from_tt(MateValue - 100, 0, 0) == MateValue - 100, "distance 100 fits in 100 halfmoves");
    expect(score_from_tt(MateValue - 101, 0, 0) == ValueNone, "distance 101 does not fit in 100 halfmoves");
}

void test_round_trip_and_bounds() {
    using namespace forge;
    TranspositionTable tt(1);
    const auto keys = keys_in_one_cluster(tt, 1);
    expect(keys.size() == 1, "one audit key");
    const std::uint64_t key = keys[0];
    auto probe = tt.probe(key);
    tt.store(probe, key, ValueNone, ValueNone, Move::none(), 1, BoundExact, true, 0);
    auto hit = tt.probe(key);
    expect(hit.hit && hit.entry.score == ValueNone && hit.entry.eval == ValueNone,
           "ValueNone score and eval survive the int16 store");
    expect(hit.entry.bound() == BoundExact && hit.entry.pv(), "exact and PV bits round-trip");

    probe = tt.probe(key);
    tt.store(probe, key, MateValue, -MateValue, make_move(1, 2), 2, BoundLower, false, 0);
    hit = tt.probe(key);
    expect(hit.hit && hit.entry.score == MateValue && hit.entry.eval == -MateValue, "MateValue round-trips");
    expect(hit.entry.bound() == BoundLower && !hit.entry.pv(), "lower bound clears the PV bit");

    probe = tt.probe(key);
    tt.store(probe, key, 40000, -40000, Move::none(), 3, BoundUpper, false, 150);
    hit = tt.probe(key);
    expect(hit.hit && hit.entry.score == 32767 && hit.entry.eval == -32767, "scores outside int16 clamp to 32767");
    expect(hit.entry.rule50_clock == 100, "halfmove clock above 100 is stored as 100");
    expect(hit.entry.score_usable(150) && !hit.entry.score_usable(90),
           "capped clocks compare equal, and 100 does not match 90");
}

void test_distinct_tags_and_alias() {
    using namespace forge;
    TranspositionTable tt(1);
    const std::uint64_t key = (0x1234ULL << 50) | (1ULL << 40) | 0xABCDULL;
    const std::uint64_t alias = key ^ (1ULL << 40);
    const std::uint64_t other = key ^ 1ULL;
    expect(TTAuditAccess::cluster_index(tt, key) == TTAuditAccess::cluster_index(tt, alias),
           "middle key bit shares the 1 MB cluster");
    expect(TTAuditAccess::tag(key) == TTAuditAccess::tag(alias), "middle key bit shares the 32-bit tag");
    expect(TTAuditAccess::cluster_index(tt, key) == TTAuditAccess::cluster_index(tt, other),
           "low bit stays in the same cluster");
    expect(TTAuditAccess::tag(key) != TTAuditAccess::tag(other), "low bit changes the tag");

    auto probe = tt.probe(key);
    tt.store(probe, key, 11, 1, make_move(0, 1), 6, BoundExact, false, 0);
    probe = tt.probe(other);
    tt.store(probe, other, 22, 1, make_move(2, 3), 7, BoundLower, false, 0);
    auto hit_key = tt.probe(key);
    auto hit_other = tt.probe(other);
    auto hit_alias = tt.probe(alias);
    expect(hit_key.hit && hit_key.entry.score == 11, "original key is stored");
    expect(hit_other.hit && hit_other.entry.score == 22, "different tag in the same cluster is stored");
    expect(hit_alias.hit && hit_alias.entry.score == 11, "known limitation: unchecked middle key bits alias");
}

void test_replacement_policy() {
    using namespace forge;
    TranspositionTable tt(1);
    const auto keys = keys_in_one_cluster(tt, 5);
    expect(keys.size() == 5, "five keys in one cluster");
    const int depths[] = {10, 40, 7, 25};
    for (int i = 0; i < 4; ++i) {
        auto probe = tt.probe(keys[static_cast<std::size_t>(i)]);
        tt.store(probe, keys[static_cast<std::size_t>(i)], 100 + i, 1, make_move(i, i + 8), depths[i], BoundLower, false, 0);
    }
    auto fifth = tt.probe(keys[4]);
    tt.store(fifth, keys[4], 555, 1, make_move(4, 12), 1, BoundUpper, false, 0);
    auto kept10 = tt.probe(keys[0]);
    auto kept40 = tt.probe(keys[1]);
    auto victim = tt.probe(keys[2]);
    auto kept25 = tt.probe(keys[3]);
    auto inserted = tt.probe(keys[4]);
    expect(kept10.hit && kept10.entry.depth == 10, "depth 10 survives a full cluster");
    expect(kept40.hit && kept40.entry.depth == 40, "depth 40 survives a full cluster");
    expect(kept25.hit && kept25.entry.depth == 25, "depth 25 survives a full cluster");
    expect(!victim.hit, "the lowest depth is the replacement victim");
    expect(inserted.hit && inserted.entry.score == 555, "the new key occupies the victim slot");

    auto deep = tt.probe(keys[1]);
    tt.store(deep, keys[1], 5, 1, make_move(9, 17), 1, BoundUpper, false, 0);
    auto after = tt.probe(keys[1]);
    expect(after.hit && after.entry.score == 101 && after.entry.depth == 40 && after.entry.bound() == BoundLower,
           "a shallow non-exact store does not replace depth or score");
    expect(after.entry.move == make_move(9, 17), "a rejected shallow store still updates a real move");

    auto exact = tt.probe(keys[1]);
    tt.store(exact, keys[1], 7, 1, make_move(10, 18), 1, BoundExact, false, 0);
    after = tt.probe(keys[1]);
    expect(after.hit && after.entry.score == 7 && after.entry.depth == 1 && after.entry.bound() == BoundExact,
           "an exact store replaces a deeper entry");
}

void test_age_and_generation_wrap() {
    using namespace forge;
    TranspositionTable tt(1);
    const auto keys = keys_in_one_cluster(tt, 5);
    expect(keys.size() == 5, "five keys for the age test");
    auto probe = tt.probe(keys[0]);
    tt.store(probe, keys[0], 10, 1, make_move(0, 1), 10, BoundLower, false, 0);
    tt.new_search();
    tt.new_search();
    tt.new_search();
    for (int i = 1; i <= 3; ++i) {
        probe = tt.probe(keys[static_cast<std::size_t>(i)]);
        tt.store(probe, keys[static_cast<std::size_t>(i)], 20 + i, 1, make_move(i, i + 8), 0, BoundLower, false, 0);
    }
    probe = tt.probe(keys[4]);
    tt.store(probe, keys[4], 30, 1, make_move(4, 12), 0, BoundUpper, false, 0);
    auto aged = tt.probe(keys[0]);
    auto fresh = tt.probe(keys[1]);
    auto newest = tt.probe(keys[4]);
    expect(!aged.hit, "three searches make a depth-10 entry lose to a fresh depth-0 entry");
    expect(fresh.hit && fresh.entry.score == 21, "the fresh depth-0 entry stays");
    expect(newest.hit && newest.entry.score == 30, "the replacing entry is stored");

    TranspositionTable wrapped(1);
    const auto wrap_keys = keys_in_one_cluster(wrapped, 5);
    probe = wrapped.probe(wrap_keys[0]);
    wrapped.store(probe, wrap_keys[0], 77, 1, make_move(0, 1), 10, BoundExact, false, 0);
    for (int i = 0; i < 32; ++i) wrapped.new_search();
    for (int i = 1; i <= 3; ++i) {
        probe = wrapped.probe(wrap_keys[static_cast<std::size_t>(i)]);
        wrapped.store(probe, wrap_keys[static_cast<std::size_t>(i)], i, 1, Move::none(), 0, BoundUpper, false, 0);
    }
    probe = wrapped.probe(wrap_keys[4]);
    wrapped.store(probe, wrap_keys[4], 5, 1, Move::none(), 0, BoundUpper, false, 0);
    auto old = wrapped.probe(wrap_keys[0]);
    auto young = wrapped.probe(wrap_keys[1]);
    expect(old.hit && old.entry.score == 77, "known limitation: 32 searches wrap generation and preserve the old entry");
    expect(!young.hit, "after a generation wrap the fresh shallow entry is replaced first");
}

void test_stale_probe_keeps_deeper_entry() {
    using namespace forge;
    TranspositionTable tt(1);
    const auto keys = keys_in_one_cluster(tt, 2);
    expect(keys.size() == 2, "two keys for the stale-probe test");
    expect(TTAuditAccess::cluster_index(tt, keys[0]) == TTAuditAccess::cluster_index(tt, keys[1]),
           "stale-probe keys share a cluster");
    auto stale_a = tt.probe(keys[0]);
    auto stale_b = tt.probe(keys[1]);
    expect(!stale_a.hit && !stale_b.hit, "both probes miss on an empty cluster");
    tt.store(stale_b, keys[1], 222, 1, make_move(8, 16), 30, BoundExact, false, 0);
    tt.store(stale_a, keys[0], 111, 1, make_move(0, 1), 1, BoundUpper, false, 0);
    auto hit_b = tt.probe(keys[1]);
    auto hit_a = tt.probe(keys[0]);
    expect(hit_b.hit && hit_b.entry.score == 222 && hit_b.entry.depth == 30 && hit_b.entry.bound() == BoundExact,
           "a stale probe does not destroy the deeper entry");
    expect(hit_a.hit && hit_a.entry.score == 111 && hit_a.entry.depth == 1, "the shallow key is stored in a free slot");

    TranspositionTable full(1);
    const auto full_keys = keys_in_one_cluster(full, 5);
    auto stale = full.probe(full_keys[4]);
    const int depths[] = {30, 29, 28, 27};
    for (int i = 0; i < 4; ++i) {
        auto probe = full.probe(full_keys[static_cast<std::size_t>(i)]);
        full.store(probe, full_keys[static_cast<std::size_t>(i)], 300 + i, 1, make_move(i, i + 8), depths[i], BoundExact,
                   false, 0);
    }
    full.store(stale, full_keys[4], 111, 1, make_move(4, 12), 1, BoundUpper, false, 0);
    auto deep = full.probe(full_keys[0]);
    auto inserted = full.probe(full_keys[4]);
    expect(deep.hit && deep.entry.score == 300 && deep.entry.depth == 30,
           "a stale probe does not overwrite the deepest entry of a full cluster");
    expect(inserted.hit && inserted.entry.score == 111, "the stale store replaces the least valuable slot");
}

bool child_is_checkmate(forge::Board board, forge::Move move) {
    forge::Undo undo;
    if (!board.make_move(move, undo)) return false;
    return board.in_check() && !board.has_legal_move();
}

void test_search_mates_and_terminal_store() {
    using namespace forge;
    const char* fen = "7k/8/6K1/5Q2/8/8/8/8 w - - ";
    const int clocks[] = {0, 50, 99};
    for (int clock : clocks) {
        Searcher searcher(16);
        Board board;
        const std::string position = std::string(fen) + std::to_string(clock) + " 1";
        expect(board.set_fen(position), "mate-in-1 fen at clock " + std::to_string(clock));
        SearchLimits limits;
        limits.depth = 3;
        const SearchInfo info = searcher.search(board, limits, false);
        expect(is_mate_score(info.score) && info.score > 0, "mate in 1 is found at clock " + std::to_string(clock));
        expect(child_is_checkmate(board, info.best_move), "best move is checkmate at clock " + std::to_string(clock));
    }

    Searcher qsearch(16);
    Board board;
    expect(board.set_fen("7k/8/6K1/5Q2/8/8/8/8 w - - 0 1"), "qsearch mate fen");
    SearchLimits limits;
    limits.depth = 1;
    SearchInfo info = qsearch.search(board, limits, false);
    expect(child_is_checkmate(board, info.best_move), "depth 1 plays the mating move");
    Board child = board;
    Undo undo;
    expect(child.make_move(info.best_move, undo), "make the depth-1 mating move");
    auto hit = qsearch.transposition_table().probe(child.key());
    expect(hit.hit && hit.entry.score == -MateValue && hit.entry.bound() == BoundExact && hit.entry.eval == ValueNone,
           "qsearch stores the checkmate position as an exact mate");

    Searcher main(16);
    Board again;
    expect(again.set_fen("7k/8/6K1/5Q2/8/8/8/8 w - - 0 1"), "main-search mate fen");
    limits.depth = 2;
    info = main.search(again, limits, false);
    Board mated = again;
    expect(mated.make_move(info.best_move, undo), "make the depth-2 mating move");
    hit = main.transposition_table().probe(mated.key());
    expect(hit.hit && hit.entry.score == -MateValue && hit.entry.bound() == BoundExact && hit.entry.depth >= 1,
           "main search stores the checkmate position as an exact mate");
}

void test_poisoned_mate_is_not_reported() {
    using namespace forge;
    auto search_kqk = [](bool poison) {
        Searcher searcher(16);
        Board board;
        const bool ok = board.set_fen("4k3/8/8/8/8/8/8/3QK3 w - - 85 40");
        if (!ok) return SearchInfo{};
        if (poison) {
            auto put = [&](Board& current, int score, int depth, int clock) {
                auto probe = searcher.transposition_table().probe(current.key());
                searcher.transposition_table().store(probe, current.key(), score, ValueNone, Move::none(), depth,
                                                     BoundExact, false, static_cast<std::uint16_t>(clock));
            };
            put(board, MateValue - 30, 40, 0);
            for (Move move : Board(board).legal_moves()) {
                Board child = board;
                Undo undo;
                if (!child.make_move(move, undo)) continue;
                put(child, -(MateValue - 29), 39, 1);
            }
        }
        SearchLimits limits;
        limits.depth = 5;
        return searcher.search(board, limits, false);
    };
    const SearchInfo clean = search_kqk(false);
    const SearchInfo poisoned = search_kqk(true);
    std::cout << "INFO kqk clean score " << clean.score << " nodes " << clean.nodes << "\n";
    std::cout << "INFO kqk poisoned score " << poisoned.score << " nodes " << poisoned.nodes << "\n";
    expect(clean.score != 0 && !is_mate_score(clean.score), "clean KQK depth 5 is a centipawn score");
    expect(poisoned.score == clean.score && poisoned.nodes == clean.nodes,
           "impossible mate entries do not change the depth-5 score or node count");
}

} // namespace

int main() {
    test_score_conversion();
    test_round_trip_and_bounds();
    test_distinct_tags_and_alias();
    test_replacement_policy();
    test_age_and_generation_wrap();
    test_stale_probe_keeps_deeper_entry();
    test_search_mates_and_terminal_store();
    test_poisoned_mate_is_not_reported();
    std::cout << (g_fails == 0 ? "ALL PASS\n" : "FAILS " + std::to_string(g_fails) + "\n");
    return g_fails == 0 ? 0 : 1;
}
