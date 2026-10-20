// Differential Boolean oracle, not a chess strength/search benchmark.
// Usage: legal_witness_tests fixtures.tsv tools/openings/forge-10000.epd
#include "forge/board.hpp"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <sstream>
#include <string>
#include <string_view>

namespace {
std::uint64_t comparisons = 0;
std::uint64_t random_state = 0x243f6a8885a308d3ULL;
void require(bool value, const std::string& text) {
    if (!value) throw std::runtime_error(text);
}
std::uint64_t random_word() {
    random_state = random_state * 6364136223846793005ULL + 1442695040888963407ULL;
    return random_state;
}

// Exact old implementation, held independent of the new early witness.
bool old_full_generator(const forge::Board& board) {
    forge::MoveList moves;
    board.generate_pseudo_legal(moves, false);
    for (const auto move : moves) if (board.is_legal(move)) return true;
    return false;
}

// Independent legality check after actual make/unmake, without is_legal().
// Castling transit-square filtering is already part of the full generator.
bool full_make_oracle(const forge::Board& original) {
    forge::Board board = original;
    const auto side = board.side_to_move();
    const auto before = board.fen();
    const auto key = board.key();
    const auto pawn_key = board.pawn_key();
    const auto moves = board.pseudo_legal_moves();
    for (const auto move : moves) {
        forge::Undo undo;
        require(board.make_move(move, undo), "generated pseudo move was rejected");
        const bool legal = !board.in_check(side);
        board.unmake_move(move, undo);
        require(board.fen() == before && board.key() == key && board.pawn_key() == pawn_key,
                "make oracle failed to restore board");
        if (legal) return true;
    }
    return false;
}

void compare(const forge::Board& board, const std::string& label) {
    const auto before = board.fen();
    const auto key = board.key();
    const auto pawn_key = board.pawn_key();
    const auto checkers = board.checkers();
    const bool actual = board.has_legal_move();
    require(actual == old_full_generator(board), "old generator mismatch: " + label + " " + before);
    require(actual == full_make_oracle(board), "make oracle mismatch: " + label + " " + before);
    require(board.fen() == before && board.key() == key && board.pawn_key() == pawn_key &&
            board.checkers() == checkers, "Boolean query mutated state: " + label);
    ++comparisons;
}

void curated(const char* filename) {
    std::ifstream input(filename);
    require(input.good(), "cannot open fixture TSV");
    std::string line;
    unsigned count = 0;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        const auto first = line.find('\t'), second = line.find('\t', first + 1);
        require(first != std::string::npos && second != std::string::npos, "malformed fixture TSV");
        const auto name = line.substr(0, first);
        forge::Board board;
        require(board.set_fen(line.substr(second + 1)), "invalid fixture: " + name);
        const bool expected = line.substr(first + 1, second - first - 1) == "1";
        compare(board, name);
        require(board.has_legal_move() == expected, "fixture terminal result mismatch: " + name);
        if (name == "white-pinned-pawn-stalemate" || name == "white-checkmate-with-pseudo-push") {
            const forge::Move witness{14, 22, 0, forge::Quiet}; // g2g3
            require(board.is_pseudo_legal(witness) && !board.is_legal(witness),
                    "terminal fixture lacks required illegal quiet-push witness");
        }
        if (name == "black-pinned-pawn-stalemate") {
            const forge::Move witness{54, 46, 0, forge::Quiet}; // g7g6
            require(board.is_pseudo_legal(witness) && !board.is_legal(witness),
                    "black fixture lacks required illegal quiet-push witness");
        }
        ++count;
    }
    require(count >= 20, "curated cases did not execute");
}

void corpus(const char* filename) {
    std::ifstream input(filename);
    require(input.good(), "cannot open corpus");
    std::string line;
    unsigned count = 0;
    while (std::getline(input, line)) {
        if (line.empty()) continue;
        forge::Board board;
        std::istringstream epd(line);
        std::string placement, side, castling, target;
        require(static_cast<bool>(epd >> placement >> side >> castling >> target), "malformed corpus EPD");
        require(board.set_fen(placement + " " + side + " " + castling + " " + target + " 0 1"),
                "invalid corpus FEN at line " + std::to_string(count + 1));
        compare(board, "corpus-" + std::to_string(++count));
    }
    require(count == 10000, "expected exact frozen 10000-position corpus");
}

void legal_walks() {
    constexpr std::array<std::string_view, 6> starts{
        forge::Board::StandardStartFen,
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
        "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"};
    for (const auto fen : starts) for (int walk = 0; walk < 12; ++walk) {
        forge::Board board;
        require(board.set_fen(fen), "invalid legal-walk seed");
        for (int ply = 0; ply < 128; ++ply) {
            compare(board, "legal-walk");
            const auto legal = board.legal_moves();
            if (legal.empty()) break;
            const auto move = legal[static_cast<std::size_t>((random_word() >> 32U) % legal.size())];
            forge::Undo undo;
            require(board.make_move(move, undo), "legal walk move rejected");
        }
    }
}
} // namespace

int main(int argc, char** argv) {
    if (argc != 3) { std::cerr << "usage: legal_witness_tests fixtures.tsv corpus.epd\n"; return 2; }
    try {
        curated(argv[1]);
        corpus(argv[2]);
        legal_walks();
        std::cout << "All " << comparisons << " legal-witness Boolean comparisons passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
