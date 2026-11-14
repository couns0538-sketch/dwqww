#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <array>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace forge {

struct SearcherTestProbe {
    static int static_evaluate(Worker& worker, const Board& board) {
        // ply 0 and an invalid ancestor: static_evaluate refreshes from the position.
        std::array<SearchStack, 2> frames{};
        return worker.static_evaluate(board, &frames[1]);
    }
};

} // namespace forge

namespace {

struct Case {
    std::string fen;
    std::string expected;
};

void trim_cr(std::string& text) {
    if (!text.empty() && text.back() == '\r') text.pop_back();
}

bool load_cases(const std::string& path, std::vector<Case>& cases, std::string& error) {
    std::ifstream input(path);
    if (!input) {
        error = "cannot open " + path;
        return false;
    }
    std::string line;
    while (std::getline(input, line)) {
        trim_cr(line);
        if (line.empty() || line[0] == '#') continue;
        Case item;
        item.fen = line;
        if (!std::getline(input, item.expected)) {
            error = "missing expected line after " + item.fen;
            return false;
        }
        trim_cr(item.expected);
        cases.push_back(std::move(item));
    }
    return true;
}

std::string format_line(const forge::EvalComponents& parts) {
    std::string line = "info string eval hce " + std::to_string(parts.hce) + " nnue " + std::to_string(parts.nnue) +
                       " total " + std::to_string(parts.total);
    if (parts.in_check) line += " incheck 1";
    return line;
}

std::string swap_piece_case(std::string_view rank) {
    std::string out;
    out.reserve(rank.size());
    for (const char c : rank) {
        if (c >= 'a' && c <= 'z') out.push_back(static_cast<char>(c - 'a' + 'A'));
        else if (c >= 'A' && c <= 'Z') out.push_back(static_cast<char>(c - 'A' + 'a'));
        else out.push_back(c);
    }
    return out;
}

// Colour swap plus a vertical flip. Side-to-move evaluation is unchanged when
// the evaluation is symmetric.
std::string mirror_fen(const std::string& fen) {
    std::istringstream input(fen);
    std::string placement;
    std::string side;
    std::string castling;
    std::string ep;
    std::string halfmove;
    std::string fullmove;
    input >> placement >> side >> castling >> ep >> halfmove >> fullmove;
    std::vector<std::string> ranks;
    std::string rank;
    for (const char c : placement) {
        if (c == '/') {
            ranks.push_back(rank);
            rank.clear();
        } else {
            rank.push_back(c);
        }
    }
    ranks.push_back(rank);
    std::string flipped;
    for (int i = 0; i < 8; ++i) {
        if (i != 0) flipped.push_back('/');
        flipped += swap_piece_case(ranks[static_cast<std::size_t>(7 - i)]);
    }
    std::string castle_out;
    if (castling == "-") {
        castle_out = "-";
    } else {
        std::string letters;
        for (const char c : castling) {
            if (c >= 'a' && c <= 'z') letters.push_back(static_cast<char>(c - 'a' + 'A'));
            else if (c >= 'A' && c <= 'Z') letters.push_back(static_cast<char>(c - 'A' + 'a'));
        }
        for (const char c : {'K', 'Q', 'k', 'q'}) {
            if (letters.find(c) != std::string::npos) castle_out.push_back(c);
        }
        if (castle_out.empty()) castle_out = "-";
    }
    std::string ep_out = "-";
    if (ep != "-" && ep.size() == 2) {
        const char new_rank = static_cast<char>('8' - (ep[1] - '1'));
        ep_out = std::string{ep[0], new_rank};
    }
    const std::string side_out = side == "w" ? "b" : "w";
    return flipped + " " + side_out + " " + castle_out + " " + ep_out + " " + halfmove + " " + fullmove;
}

int network_centipawns(const forge::Board& board) {
    if (!forge::nnue::enabled || !forge::nnue::available()) return 0;
    forge::nnue::Accumulator accumulator{};
    forge::nnue::refresh(board, accumulator);
    return forge::nnue::evaluate(board, accumulator);
}

bool has_promotion(const forge::Board& board) {
    for (const forge::Move move : board.legal_moves()) {
        if (move.is_promotion()) return true;
    }
    return false;
}

void fail(const std::string& message) {
    std::cerr << message << '\n';
}

} // namespace

int main(int argc, char** argv) {
    const char* path = argc > 1 ? argv[1] : "forge-combo29/tests_t14/eval_cases.txt";
    std::vector<Case> cases;
    std::string error;
    if (!load_cases(path, cases, error)) {
        fail(error);
        return 1;
    }
    if (cases.size() != 30) {
        fail("expected 30 positions, got " + std::to_string(cases.size()));
        return 1;
    }

    forge::Searcher searcher(1);
    forge::Worker& worker = searcher.main_worker();
    int mirrors = 0;
    int white_promotions = 0;
    int black_promotions = 0;
    int checks = 0;
    bool saw_white = false;
    bool saw_black = false;

    for (std::size_t i = 0; i < cases.size(); ++i) {
        const Case& item = cases[i];
        forge::Board board;
        if (!board.set_fen(item.fen, &error)) {
            fail("rejected FEN: " + error + " | " + item.fen);
            return 1;
        }
        if (board.side_to_move() == forge::White) saw_white = true;
        else saw_black = true;
        if (board.in_check()) ++checks;
        if (has_promotion(board)) {
            if (board.side_to_move() == forge::White) ++white_promotions;
            else ++black_promotions;
        }

        const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
        const std::string line = format_line(parts);
        if (line != item.expected) {
            fail("output mismatch at " + std::to_string(i) + "\n fen " + item.fen + "\n got  " + line + "\n want " +
                 item.expected);
            return 1;
        }
        if (parts.hce != forge::Evaluator::evaluate_uncached(board)) {
            fail("hce is not evaluate_uncached at " + item.fen);
            return 1;
        }
        if (parts.nnue != network_centipawns(board)) {
            fail("nnue is not the network output at " + item.fen);
            return 1;
        }
        if (parts.in_check != board.in_check()) {
            fail("incheck flag mismatch at " + item.fen);
            return 1;
        }
        worker.clear_caches();
        const int search_total = forge::SearcherTestProbe::static_evaluate(worker, board);
        if (search_total != parts.total) {
            fail("total " + std::to_string(parts.total) + " != static_evaluate " + std::to_string(search_total) +
                 " at " + item.fen);
            return 1;
        }

        if (i < 10) {
            const std::string flipped_fen = mirror_fen(item.fen);
            forge::Board flipped;
            if (!flipped.set_fen(flipped_fen, &error)) {
                fail("mirror rejected: " + error + " | " + flipped_fen);
                return 1;
            }
            const forge::EvalComponents mirrored = forge::Evaluator::static_eval_components(flipped);
            if (mirrored.hce != parts.hce || mirrored.nnue != parts.nnue || mirrored.total != parts.total) {
                fail("mirror mismatch at " + item.fen + "\n flip " + flipped_fen + "\n orig " + line + "\n flip " +
                     format_line(mirrored));
                return 1;
            }
            worker.clear_caches();
            const int flipped_search = forge::SearcherTestProbe::static_evaluate(worker, flipped);
            if (flipped_search != mirrored.total) {
                fail("mirror total != static_evaluate at " + flipped_fen);
                return 1;
            }
            forge::Board round_trip;
            if (!round_trip.set_fen(mirror_fen(flipped_fen), &error)) {
                fail("mirror is not reversible: " + error);
                return 1;
            }
            if (round_trip.key() != board.key()) {
                fail("mirror twice changed the position key\n from " + item.fen + "\n back " + round_trip.fen());
                return 1;
            }
            ++mirrors;
        }
    }

    if (!saw_white || !saw_black) {
        fail("positions must include both sides to move");
        return 1;
    }
    if (checks < 1) {
        fail("positions must include one side to move in check");
        return 1;
    }
    if (white_promotions < 1 || black_promotions < 1) {
        fail("positions must include a pending promotion for each colour");
        return 1;
    }
    if (mirrors != 10) {
        fail("mirror checks: " + std::to_string(mirrors));
        return 1;
    }

    // The shipped network is residual and on by default. Also check the
    // search's no-network path, which adds nothing and keeps the hand-crafted score.
    const bool nnue_was = forge::nnue::enabled;
    forge::nnue::enabled = false;
    for (const Case& item : cases) {
        forge::Board board;
        if (!board.set_fen(item.fen, &error)) {
            forge::nnue::enabled = nnue_was;
            fail("rejected FEN with NNUE off: " + error);
            return 1;
        }
        worker.clear_caches();
        const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
        const int search_total = forge::SearcherTestProbe::static_evaluate(worker, board);
        if (parts.nnue != 0 || parts.total != search_total || parts.total != parts.hce ||
            parts.hce != forge::Evaluator::evaluate_uncached(board)) {
            forge::nnue::enabled = nnue_was;
            fail("NNUE off mismatch at " + item.fen + " hce " + std::to_string(parts.hce) + " nnue " +
                 std::to_string(parts.nnue) + " total " + std::to_string(parts.total) + " search " +
                 std::to_string(search_total));
            return 1;
        }
    }
    forge::nnue::enabled = nnue_was;

    std::cout << "ok 30 positions, " << mirrors << " mirrors, " << checks << " in check, promotions white "
              << white_promotions << " black " << black_promotions << '\n';
    return 0;
}
