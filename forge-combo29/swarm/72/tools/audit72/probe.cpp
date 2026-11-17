// Direct probe for the rules audit: exposes the position key, the rule-50
// clock and the two draw predicates that UCI only reveals indirectly.
//
//   probe fen <FEN>                 -> key/halfmove/castling/ep/flags
//   probe seq <FEN> <m1> <m2> ...   -> per-ply table, incl. is_repetition
//
// Every line is prefixed so the Python driver can parse it unambiguously.

#include "forge/board.hpp"

#include <cstdio>
#include <iostream>
#include <string>
#include <vector>

namespace {

void dump(const forge::Board& board, const char* tag, const std::string& move_text) {
    std::cout << tag << " key=" << std::hex << board.key() << std::dec
              << " halfmove=" << board.halfmove_clock()
              << " side=" << (board.side_to_move() == forge::White ? 'w' : 'b')
              << " fen=\"" << board.fen() << "\""
              << " repetition=" << (board.is_repetition() ? 1 : 0)
              << " insufficient=" << (board.is_insufficient_material() ? 1 : 0)
              << " hist=" << board.key_history().size();
    if (!move_text.empty()) std::cout << " move=" << move_text;
    std::cout << std::endl;
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: probe fen <FEN> | probe seq <FEN> <move...>" << std::endl;
        return 2;
    }
    const std::string mode = argv[1];
    std::string fen = argv[2];

    // For `seq`, the FEN arrives as ONE argument (it contains spaces), and the
    // trailing tokens are moves.
    std::vector<std::string> moves;
    if (mode == "seq") {
        for (int i = 3; i < argc; ++i) moves.emplace_back(argv[i]);
    }

    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        std::cout << "FENREFUSED " << error << std::endl;
        return 1;
    }
    dump(board, "PLY0", "");

    for (const std::string& text : moves) {
        const auto move = board.parse_uci(text);
        if (!move.has_value()) {
            std::cout << "ILLEGAL " << text << std::endl;
            return 1;
        }
        forge::Undo undo;
        (void)board.make_move(*move, undo);
        dump(board, "PLY", text);
    }
    return 0;
}
