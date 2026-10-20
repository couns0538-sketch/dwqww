// Identical source is linked separately with each frozen core; no search.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/eval_params.hpp"
#include <iostream>
#include <string>

int main() {
    forge::Evaluator cached;
    std::string fen;
    unsigned count = 0;
    while (std::getline(std::cin, fen)) {
        if (fen.empty() || ++count > 128) return 2;
        forge::Board board;
        if (!board.set_fen(fen)) return 3;
        const int first = cached.evaluate(board);
        const int hot = cached.evaluate(board);
        const int full = forge::Evaluator::evaluate_uncached(board);
        forge::EvalTrace trace;
        const int white = forge::evaluate_traced(board, trace);
        if (first != hot || first != full || white != trace.white_eval ||
            first != (board.side_to_move() == forge::White ? white : -white)) return 4;
        std::cout << count << ' ' << first << ' ' << hot << ' ' << full << ' '
                  << white << ' ' << trace.phase << ' ' << trace.scale << ' '
                  << static_cast<int>(trace.side_to_move);
        for (auto coefficient : trace.coefficients) std::cout << ' ' << coefficient;
        std::cout << '\n';
    }
    return count == 0 ? 5 : 0;
}
