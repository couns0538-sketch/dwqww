// Original deterministic opening corpus generator. Licensed under the project's MIT license.
// No imported games, books, evaluation weights, or external source code are used.
#include "forge/board.hpp"

#include <charconv>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
std::uint64_t next_random(std::uint64_t& state) {
    state ^= state << 13;
    state ^= state >> 7;
    state ^= state << 17;
    return state;
}

std::uint64_t number(std::string_view text) {
    std::uint64_t value = 0;
    const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
    if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) {
        throw std::runtime_error("invalid unsigned integer");
    }
    return value;
}
}

int main(int argc, char** argv) {
    try {
        if (argc != 5) {
            std::cerr << "usage: forge_openings COUNT SEED OUTPUT.epd OUTPUT.moves\n";
            return 2;
        }
        const std::uint64_t count = number(argv[1]);
        std::uint64_t state = number(argv[2]);
        if (count == 0 || count > 100000 || state == 0) throw std::runtime_error("invalid count/seed");
        std::ofstream epd(argv[3]);
        std::ofstream provenance(argv[4]);
        if (!epd || !provenance) throw std::runtime_error("cannot open output files");
        std::set<std::string> seen;
        const std::uint64_t max_attempts = count * 100;
        for (std::uint64_t attempt = 0; seen.size() < count && attempt < max_attempts; ++attempt) {
            forge::Board board;
            std::string moves;
            bool complete = true;
            for (int ply = 0; ply < 12; ++ply) {
                std::vector<forge::Move> choices;
                for (const forge::Move move : board.legal_moves()) {
                    const int type = forge::piece_type(board.piece_at(move.from));
                    const bool castle = (move.flags & (forge::KingCastle | forge::QueenCastle)) != 0U;
                    // A deliberately simple, material-balanced development corpus, not
                    // sampled human games or a candidate-evaluation-selected book.
                    if (move.is_capture() || (move.flags & forge::Promotion) != 0U) continue;
                    if (type == 4 || type == 5 || (type == 6 && !castle)) continue;
                    const int home_rank = board.side_to_move() == forge::White ? 0 : 7;
                    if ((type == 2 || type == 3) && static_cast<int>(move.from) / 8 != home_rank) continue;
                    // End with an irreversible move: EPD then loses neither reversible
                    // history nor the rule-50 counter when replayed by a match runner.
                    if (ply == 11 && type != 1 && !move.is_capture()) continue;
                    const int file = static_cast<int>(move.to) % 8;
                    int weight = 1;
                    if (type == 1 && file >= 2 && file <= 5) weight = 4;
                    if (type == 2 || type == 3 || castle) weight = 3;
                    for (int repeat = 0; repeat < weight; ++repeat) choices.push_back(move);
                }
                if (choices.empty()) { complete = false; break; }
                const auto index = static_cast<std::size_t>(next_random(state) % choices.size());
                const forge::Move move = choices[index];
                if (!moves.empty()) moves += ' ';
                moves += forge::Board::move_to_uci(move);
                forge::Undo undo;
                if (!board.make_move(move, undo)) throw std::runtime_error("legal move rejected");
            }
            if (!complete || board.halfmove_clock() != 0 || board.in_check(board.side_to_move()) ||
                !board.has_legal_move()) continue;
            std::string position = board.fen();
            const auto fullmove = position.rfind(' ');
            const auto halfmove = position.rfind(' ', fullmove - 1);
            position.resize(halfmove);
            if (!seen.insert(position).second) continue;
            epd << position << " id \"Forge-" << seen.size() << "\";\n";
            provenance << seen.size() << '\t' << board.fen() << '\t' << moves << '\n';
        }
        if (seen.size() != count) throw std::runtime_error("insufficient unique openings");
        epd.flush();
        provenance.flush();
        if (!epd || !provenance) throw std::runtime_error("output write failed");
        std::cout << "generated " << count << " unique 12-ply openings\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
