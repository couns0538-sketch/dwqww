#include "forge/board.hpp"
#include "forge/search.hpp"
#include <iostream>
#include <string_view>
namespace forge {
struct SearcherTestProbe {
    static int ab(Searcher& s, Board& b, int depth) {
        return s.alpha_beta(b, depth, 1, -32000, 32000);
    }
    static int qs(Searcher& s, Board& b) { return s.quiescence(b, 0, -32000, 32000); }
};
}
int main() {
    using namespace forge;
    Board b;
    if (!b.set_fen("4k3/4n3/8/3p4/8/8/8/K2QR3 w - - 0 1")) return 2;
    const auto m = b.parse_uci("d1d5");
    if (!m) return 3;
    std::cout << "pinned_knight SEE=" << b.static_exchange(*m) << " expected=100\n";
    Searcher q(4);
    const int qscore = SearcherTestProbe::qs(q,b);
    const int eval = Searcher::evaluate(b);
    Undo u; (void)b.make_move(*m,u);
    std::cout << "pinned_recapture_is_legal=" << b.parse_uci("e7d5").has_value() << " expected=0\n";
    Searcher child(4);
    std::cout << "qscore=" << qscore << " standpat=" << eval
              << " legal_capture_qscore=" << -SearcherTestProbe::qs(child,b) << '\n';
    Board fresh, near;
    if (!fresh.set_fen("7k/8/8/8/8/8/8/KR6 w - - 0 1") ||
        !near.set_fen("7k/8/8/8/8/8/8/KR6 w - - 99 1")) return 4;
    Searcher warm(4), cold(4);
    std::cout << "same_key_different_halfmove=" << (fresh.key()==near.key()) << '\n';
    const int normal = SearcherTestProbe::ab(warm, fresh, 2);
    const int cached = SearcherTestProbe::ab(warm, near, 2);
    const int correct = SearcherTestProbe::ab(cold, near, 2);
    std::cout << "rule50 normal=" << normal << " warm99=" << cached << " cold99=" << correct << '\n';
}
