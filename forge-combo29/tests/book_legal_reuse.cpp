#include "forge/book.hpp"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <random>
using namespace forge;
static std::vector<book::Book::Candidate> reference(const book::Book& b, const Board& board) {
    std::vector<book::Book::Candidate> result;
    const auto key = book::polyglot_key(board);
    for (const auto& e : b.entries()) {
        if (e.key != key) continue;
        Move m = book::decode_move(board, e.move);
        if (m.is_none()) continue;
        bool merged = false;
        for (auto& c : result) if (c.move == m) {
            c.weight = static_cast<std::uint16_t>(std::min<int>(65535, c.weight + e.weight));
            merged = true;
        }
        if (!merged) result.push_back({m, e.weight});
    }
    std::stable_sort(result.begin(), result.end(), [](auto a, auto b) { return a.weight > b.weight; });
    return result;
}
static size_t cases = 0;
static void check(Board& board, bool exhaustive, std::mt19937& rng) {
    book::Book b;
    auto key = book::polyglot_key(board);
    std::vector<book::Entry> entries;
    for (unsigned i = 0; i < (exhaustive ? 65536U : 256U); ++i)
        entries.push_back({key, static_cast<std::uint16_t>(exhaustive ? i : rng()), static_cast<std::uint16_t>(i%5 == 0 ? 0 : 17), 0});
    for (auto m : board.legal_moves()) {
        auto enc = book::encode_move(board, m);
        entries.push_back({key,enc,40000,0});
        entries.push_back({key,enc,40000,0}); // saturate duplicates and exercise stable ties
    }
    entries.push_back({key ^ 1,0,65535,0});
    b.set_entries(entries);
    auto got = b.candidates(board), expected = reference(b,board);
    if (got.size()!=expected.size()) std::abort();
    for (size_t i=0;i<got.size();++i)
        if (!(got[i].move==expected[i].move) || got[i].weight!=expected[i].weight) std::abort();
    b.clear(); if (!b.candidates(board).empty()) std::abort();
    b.set_entries({{key ^ 1,0,1,0}}); if (!b.candidates(board).empty()) std::abort();
    ++cases;
}
int main() {
    Board b; std::mt19937 rng(20261110);
    const char* fens[]={Board::StandardStartFen.data(),
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
        "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
        "4k3/P7/8/8/8/8/7p/4K3 b - - 0 1",
        "4k3/8/8/3pP3/4K3/8/8/8 w - d6 0 1",
        "8/8/8/r4pPK/8/8/8/4k3 w - f6 0 1",
        "4r2k/8/8/8/1b6/8/8/4K3 w - - 0 1",
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"};
    for(auto f:fens) { if(!b.set_fen(f)) return 2; check(b,true,rng); }
    for(int g=0;g<5;++g){if(!b.set_fen(Board::StandardStartFen))return 3;for(int p=0;p<100;++p){check(b,false,rng);auto moves=b.legal_moves();if(moves.empty())break;Undo u;(void)b.make_move(moves[rng()%moves.size()],u);}}
    std::cout << "PASS book candidate/reference cases=" << cases << " exhaustive_encoding_positions=9 seed=20261110\n";
}
