// Standalone, read-only baseline predicate probe; never linked into production.
#include "forge/board.hpp"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
using namespace forge;
struct Counts {
    std::uint64_t positions=0, checked=0, double_checked=0, moves=0, checked_moves=0;
    std::uint64_t eligible=0, rejected=0, double_rejected=0, survivors=0, survivor_illegal=0;
    std::uint64_t king_bypass=0, ep_bypass=0, legal_ep_bypass=0, legal=0, mismatches=0;
} counts;
void require(bool condition, const char* message) { if (!condition) throw std::runtime_error(message); }
bool reject(const Board& b, const Move& m) {
    const Bitboard checkers=b.checkers();
    if (!checkers || piece_type(b.piece_at(m.from))==King || (m.flags & EnPassant)) return false;
    if (checkers & (checkers-1)) return true;
    return ((checkers | attacks::between(b.king_square(b.side_to_move()), lsb(checkers))) & square_bb(m.to))==0;
}
void visit(Board& b, int depth, unsigned& budget) {
    if (!budget) return;
    --budget; ++counts.positions;
    const auto checkers=b.checkers();
    const bool multiple=checkers && (checkers & (checkers-1));
    counts.checked+=checkers!=0; counts.double_checked+=multiple;
    // Independently reconstruct checker identity, including after make/unmake.
    require(checkers==(b.attackers_to(b.king_square(b.side_to_move())) & b.occupied(opposite(b.side_to_move()))),"stale checkers cache");
    const auto moves=b.pseudo_legal_moves();
    for (auto m:moves) {
        require(b.is_pseudo_legal(m),"invalid generated move");
        const bool original=b.is_legal(m), rejected=reject(b,m);
        const bool candidate=!rejected && original;
        ++counts.moves; counts.legal+=original; counts.mismatches+=original!=candidate;
        if (checkers) {
            ++counts.checked_moves;
            if (piece_type(b.piece_at(m.from))==King) ++counts.king_bypass;
            else if (m.flags & EnPassant) { ++counts.ep_bypass; counts.legal_ep_bypass+=original; }
            else {
                ++counts.eligible;
                counts.rejected+=rejected;
                counts.double_rejected+=rejected && multiple;
                counts.survivors+=!rejected;
                counts.survivor_illegal+=!rejected && !original;
            }
        }
        if (original && depth>0 && budget) {
            const auto before=b.fen();
            Undo undo; require(b.make_move(m,undo),"legal move make failed");
            visit(b,depth-1,budget); b.unmake_move(m,undo);
            require(b.fen()==before && b.checkers()==checkers,"unmake identity failure");
        }
    }
}
int main(int argc,char**argv) {
    try {
        require(argc==2,"usage: probe fixture-file");
        std::ifstream input(argv[1]); require(bool(input),"open fixtures");
        std::string fen; unsigned roots=0;
        while (std::getline(input,fen)) {
            if (fen.empty() || fen[0]=='#') continue;
            Board b; require(b.set_fen(fen),"fixture rejected"); unsigned budget=300;
            visit(b,2,budget); ++roots;
        }
        require(counts.checked && counts.double_checked && counts.rejected && counts.legal_ep_bypass,"missing required coverage");
        require(counts.mismatches==0,"prefilter changed legality");
        std::cout << "{\n  \"roots\": " << roots;
#define EMIT(field) std::cout << ",\n  \"" #field "\": " << counts.field
        EMIT(positions); EMIT(checked); EMIT(double_checked); EMIT(moves); EMIT(checked_moves);
        EMIT(eligible); EMIT(rejected); EMIT(double_rejected); EMIT(survivors); EMIT(survivor_illegal);
        EMIT(king_bypass); EMIT(ep_bypass); EMIT(legal_ep_bypass); EMIT(legal); EMIT(mismatches);
        std::cout << "\n}\n";
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
