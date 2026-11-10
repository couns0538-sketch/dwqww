#include "forge/board.hpp"
#include <cstdint>
#include <vector>
#define private public
#include "forge/eval.hpp"
#undef private
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <random>
#include <type_traits>
#include <unordered_map>

using namespace forge;
using Entry = Evaluator::PawnEntry;
static_assert(std::is_standard_layout_v<Entry> && std::is_trivially_copyable_v<Entry>);
static_assert(alignof(Entry) == 8 && offsetof(Entry, key) == 0 && offsetof(Entry, score) == 8);
static_assert(offsetof(Entry, passed) == 16);
#if FORGE_SPD_COMPACT_PAWN_CACHE
static_assert(sizeof(Entry) == 32 && offsetof(Entry, valid) == 12);
#else
static_assert(sizeof(Entry) == 40 && offsetof(Entry, valid) == 32);
#endif

void require(bool condition, const char* message) {
    if (!condition) { std::cerr << "FAIL: " << message << '\n'; std::exit(1); }
}
std::size_t slot(const Board& board) { return board.pawn_key() & ((1U << 15U) - 1U); }
std::uint64_t checks = 0;
void check(Evaluator& evaluator, const Board& board) {
    const int oracle = Evaluator::evaluate_uncached(board);
    require(evaluator.evaluate(board) == oracle, "Cached HCE differs from uncached oracle");
    require(evaluator.evaluate(board) == oracle, "Repeated cache hit differs");
    const auto state = Evaluator::refresh_runtime_psqt(board);
    require(evaluator.evaluate_runtime(board, state) == oracle, "Runtime PSQT HCE differs");
    const auto& entry = evaluator.pawn_cache_[slot(board)];
    require(entry.valid && entry.key == board.pawn_key(), "Slot not populated for current full key");
    ++checks;
}
void verify_clear(Evaluator& evaluator) {
    evaluator.clear();
    for (const auto& entry : evaluator.pawn_cache_)
        require(!entry.valid && entry.key == 0 && entry.score == 0 && entry.passed[0] == 0 && entry.passed[1] == 0,
                "Clear/value initialization did not reset every named field");
}
int main() {
    constexpr std::uint32_t Seed = 20261110;
    Evaluator evaluator;
    verify_clear(evaluator);
    Board board;
    check(evaluator, board);
    auto& entry = evaluator.pawn_cache_[slot(board)];
    const Entry saved = entry;
    // Deliberate poison proves matching valid key uses the cached entry rather
    // than rewriting it. Do not compare poisoned evaluation to the oracle.
    entry.score = S(123, 123);
    (void)evaluator.evaluate(board);
    require(entry.score == S(123, 123), "Expected matching-key cache hit");
    entry = saved;
    check(evaluator, board);
    // Same slot, wrong high key bit: a full-key miss must replace poison.
    entry.key ^= 1ULL << 63;
    entry.score = S(123, 123);
    entry.passed = {~0ULL, ~0ULL};
    check(evaluator, board);
    require(entry.score == saved.score && entry.passed == saved.passed, "Full-key miss did not rebuild pawn data");
    entry.valid = false;
    entry.score = S(123, 123);
    check(evaluator, board);
    require(entry.score == saved.score, "Invalid matching key incorrectly hit");
    require(board.set_fen("4k3/8/8/8/8/8/8/R3K3 w - - 0 1"), "Key-zero fixture");
    require(board.pawn_key() == 0, "Pawnless board must exercise real zero key");
    evaluator.pawn_cache_[0].key = 0;
    evaluator.pawn_cache_[0].valid = false;
    evaluator.pawn_cache_[0].score = S(123, 123);
    evaluator.pawn_cache_[0].passed = {~0ULL, ~0ULL};
    check(evaluator, board);
    require(evaluator.pawn_cache_[0].score == 0 && evaluator.pawn_cache_[0].passed == std::array<Bitboard,2>{},
            "Zero-key invalid entry was not rebuilt");
    verify_clear(evaluator);
    check(evaluator, board);

    struct Seen { std::uint64_t key; std::string fen; };
    std::unordered_map<std::size_t, Seen> seen;
    std::string collision_a, collision_b;
    std::mt19937 rng(Seed);
    require(board.set_fen(Board::StandardStartFen), "Start fixture");
    for (int ply = 0; ply < 4096; ++ply) {
        check(evaluator, board);
        const auto index = slot(board);
        const auto it = seen.find(index);
        if (collision_a.empty() && it != seen.end() && it->second.key != board.pawn_key()) {
            collision_a = it->second.fen;
            collision_b = board.fen();
        } else if (it == seen.end()) seen.emplace(index, Seen{board.pawn_key(), board.fen()});
        if (ply % 127 == 0) verify_clear(evaluator);
        const auto moves = board.legal_moves();
        if (moves.empty() || ply % 256 == 255) {
            require(board.set_fen(Board::StandardStartFen), "Restart fixture");
        } else {
            Undo undo;
            require(board.make_move(moves[rng() % moves.size()], undo), "Legal random move rejected");
        }
    }
    require(!collision_a.empty(), "No actual pawn-hash index collision found");
    Board a, b;
    require(a.set_fen(collision_a) && b.set_fen(collision_b), "Collision fixtures parse");
    require(slot(a) == slot(b) && a.pawn_key() != b.pawn_key(), "Not a real different-key slot collision");
    verify_clear(evaluator);
    check(evaluator, a);
    check(evaluator, b);
    check(evaluator, a);
    const Entry copy = evaluator.pawn_cache_[slot(a)];
    Entry assigned;
    assigned = copy;
    require(assigned.key == copy.key && assigned.score == copy.score && assigned.valid == copy.valid && assigned.passed == copy.passed,
            "Named-field copying differs");
    std::cout << "{\"passed\":true,\"seed\":" << Seed << ",\"checks\":" << checks
              << ",\"compact\":" << FORGE_SPD_COMPACT_PAWN_CACHE << ",\"entry_size\":" << sizeof(Entry)
              << ",\"valid_offset\":" << offsetof(Entry, valid) << ",\"collision_slot\":" << slot(a)
              << ",\"collision_a\":\"" << collision_a << "\",\"collision_b\":\"" << collision_b << "\"}\n";
}
