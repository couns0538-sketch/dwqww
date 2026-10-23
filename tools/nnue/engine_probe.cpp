// Read-only inference/data probe over the actual Forge evaluator and NNUE API.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>

namespace {
void features(const forge::Board& board, forge::Color perspective) {
    std::cout << '[';
    bool first = true;
    forge::Bitboard occupied = board.occupied();
    while (occupied != 0) {
        const int square = forge::pop_lsb(occupied);
        if (!first) std::cout << ',';
        first = false;
        std::cout << forge::nnue::feature_index(perspective, board.piece_at(square), square);
    }
    std::cout << ']';
}
}

int main(int argc, char** argv) {
    bool hce_only = false;
    if (argc == 2 && std::string_view(argv[1]) == "--help") {
        std::cout << "usage: forge_nnue_probe [--hce-only] < fens.txt\n";
        return 0;
    }
    if (argc == 2 && std::string_view(argv[1]) == "--hce-only") hce_only = true;
    else if (argc != 1) {
        std::cerr << "usage: forge_nnue_probe [--hce-only] < fens.txt\n";
        return 2;
    }
    if (!hce_only && !forge::nnue::available()) {
        std::cerr << "forge_nnue_probe: no compiled network\n";
        return 2;
    }
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    std::cout << std::boolalpha;
    forge::nnue::enabled = true;
    forge::Board board;
    std::string fen;
    std::uint64_t index = 0;
    while (std::getline(std::cin, fen)) {
        std::string error;
        if (!board.set_fen(fen, &error)) {
            // Engine errors are fixed ASCII text; no untrusted input is echoed.
            std::cerr << "forge_nnue_probe: invalid FEN at index " << index << ": " << error << '\n';
            return 2;
        }
        const auto legal = board.legal_moves();
        bool tactical = false;
        for (const auto move : legal) {
            if (move.is_capture() || move.is_promotion() || board.gives_check(move)) {
                tactical = true;
                break;
            }
        }
        const bool terminal = legal.empty() || board.is_insufficient_material() || board.halfmove_clock() >= 100;
        std::cout << "{\"index\":" << index
                  << ",\"hce_cp_stm\":" << forge::Evaluator::evaluate_uncached(board)
                  << ",\"nnue_cp_stm\":";
        if (hce_only) std::cout << "null";
        else {
            forge::nnue::Accumulator accumulator;
            forge::nnue::refresh(board, accumulator);
            std::cout << forge::nnue::evaluate(board, accumulator);
        }
        std::cout << ",\"nnue_available\":" << forge::nnue::available()
                  << ",\"residual_mode\":" << forge::nnue::residual()
                  << ",\"hidden_size\":" << forge::nnue::HiddenSize
                  << ",\"hce_only\":" << hce_only
                  << ",\"in_check\":" << board.in_check()
                  << ",\"terminal\":" << terminal
                  << ",\"has_tactical_legal_move\":" << tactical
                  << ",\"features\":[";
        features(board, board.side_to_move());
        std::cout << ',';
        features(board, forge::opposite(board.side_to_move()));
        std::cout << "]}\n";
        ++index;
    }
    if (!std::cin.eof() || index == 0) {
        std::cerr << "forge_nnue_probe: incomplete or empty FEN input\n";
        return 2;
    }
    std::cout.flush();
    if (!std::cout) {
        std::cerr << "forge_nnue_probe: output failure\n";
        return 2;
    }
    return 0;
}
