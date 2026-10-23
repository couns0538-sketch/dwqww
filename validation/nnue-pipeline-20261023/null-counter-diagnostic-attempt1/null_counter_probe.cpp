// Evidence-only wrapper; original tests and engine sources are unchanged.
#define main forge_unchanged_tests_original_main
#include "/workspace/.cloud-setup/nnue-final-linux-a52efa5f7864-attempt1/source/tests/tests.cpp"
#undef main

namespace {
bool emit_counter_result(const char* label, forge::Board& board,
                         forge::Searcher& searcher, const forge::SearchInfo& info,
                         const std::string& original_fen) {
    const auto move = forge::Board::move_to_uci(info.best_move);
    const bool legal = board.parse_uci(move).has_value();
    const bool unchanged = board.fen() == original_fen;
    std::cout << "{\"case\":\"" << label << "\",\"depth\":" << info.depth
              << ",\"score_cp\":" << info.score << ",\"nodes\":" << info.nodes
              << ",\"bestmove\":\"" << move << "\",\"legal_bestmove\":"
              << (legal ? "true" : "false") << ",\"board_unchanged\":"
              << (unchanged ? "true" : "false") << ",\"null_tries\":"
              << forge::SearcherTestProbe::null_tries(searcher)
              << ",\"null_cutoffs\":" << forge::SearcherTestProbe::null_cutoffs(searcher)
              << "}\n";
    return legal && unchanged;
}
}

int main() {
    forge::Board board;
    forge::SearchLimits limits;
    limits.depth = 8;
    forge::Searcher searcher(8);
    if (!board.set_fen("8/8/8/3k4/8/4K3/4P3/8 w - - 0 1")) return 2;
    auto original_fen = board.fen();
    auto info = searcher.search(board, limits);
    bool valid = emit_counter_result("original_pawn_only_depth8", board, searcher, info, original_fen);
    if (!board.set_fen(forge::Board::StandardStartFen)) return 2;
    searcher.clear();
    original_fen = board.fen();
    info = searcher.search(board, limits);
    valid = emit_counter_result("original_start_after_pawn_depth8", board, searcher, info, original_fen) && valid;

    forge::Board deeper_board;
    if (!deeper_board.set_fen(forge::Board::StandardStartFen)) return 2;
    forge::Searcher deeper_searcher(8);
    limits.depth = 10;
    original_fen = deeper_board.fen();
    info = deeper_searcher.search(deeper_board, limits);
    valid = emit_counter_result("predefined_fresh_start_depth10", deeper_board, deeper_searcher, info, original_fen) && valid;
    return valid ? 0 : 3;
}
