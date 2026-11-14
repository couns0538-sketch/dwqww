#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>

namespace {

std::uint64_t rng_state = 0xC0FFEE1234ULL;

std::uint64_t next_rng() {
    rng_state ^= rng_state >> 12;
    rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27;
    return rng_state * 2685821657736338717ULL;
}

void write_pod(const void* data, std::size_t size) {
    if (std::fwrite(data, size, 1, stdout) != 1) std::exit(2);
}

struct EvalRecord {
    std::int32_t uncached = 0;
    std::int32_t cached = 0;
    std::int32_t hce = 0;
    std::int32_t nnue = 0;
    std::int32_t total = 0;
    std::int32_t in_check = 0;
};

struct SearchRecord {
    char move[8]{};
    std::int32_t score = 0;
    std::uint64_t nodes = 0;
};

void emit_eval(forge::Board& board, forge::Evaluator& evaluator) {
    EvalRecord record;
    record.uncached = forge::Evaluator::evaluate_uncached(board);
    record.cached = evaluator.evaluate(board);
    const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
    record.hce = parts.hce;
    record.nnue = parts.nnue;
    record.total = parts.total;
    record.in_check = parts.in_check ? 1 : 0;
    write_pod(&record, sizeof record);
}

void play_random(forge::Board& board, int& ply) {
    const forge::MoveList legal = board.legal_moves();
    if (legal.empty() || ply >= 80 || (next_rng() % 64ULL) == 0ULL) {
        if (!board.set_fen(forge::Board::StandardStartFen)) std::exit(3);
        ply = 0;
        return;
    }
    const forge::Move move = legal[static_cast<std::size_t>(next_rng() % legal.size())];
    forge::Undo undo;
    (void)board.make_move(move, undo);
    ++ply;
}

void walk_hce(int count) {
    forge::Board board;
    int ply = 0;
    std::int64_t sum = 0;
    for (int i = 0; i < count; ++i) {
        sum += forge::Evaluator::evaluate_uncached(board);
        play_random(board, ply);
    }
    std::fprintf(stderr, "hce_sum %lld\n", static_cast<long long>(sum));
}

void walk_eval(int count) {
    forge::Board board;
    forge::Evaluator evaluator;
    int ply = 0;
    for (int i = 0; i < count; ++i) {
        emit_eval(board, evaluator);
        play_random(board, ply);
    }
}

void walk_search(int count) {
    forge::Searcher searcher(16, 1);
    forge::Board board;
    int ply = 0;
    forge::SearchLimits limits;
    limits.depth = 8;
    for (int i = 0; i < count; ++i) {
        const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        SearchRecord record;
        const std::string text = forge::Board::move_to_uci(info.best_move);
        for (std::size_t c = 0; c < text.size() && c < sizeof record.move; ++c) record.move[c] = text[c];
        record.score = info.score;
        record.nodes = info.nodes;
        write_pod(&record, sizeof record);
        play_random(board, ply);
    }
}

} // namespace

int main(int argc, char** argv) {
    const std::string mode = argc > 1 ? argv[1] : "eval";
    const int count = argc > 2 ? std::atoi(argv[2]) : 1000000;
    if (mode == "search") walk_search(count);
    else if (mode == "hce") walk_hce(count);
    else walk_eval(count);
    return 0;
}
