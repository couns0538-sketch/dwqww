// Mate oracle: forge's movegen (independently pinned by `go perft 5` = 4,865,609)
// plus its OWN plain alpha-beta minimax. No search code from forge is used:
// the verdict is exact minimax over legal_moves with no pruning heuristics,
// no TT, no quiescence and no eval.
#include "forge/board.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
using namespace forge;

static long long g_nodes = 0, g_cap = 4000000;
static bool g_capped = false;

// Returns a mate score: +(1000 - ply) if the side to move forces mate in <= limit,
// -(1000 - ply) if it is mated, 0 otherwise/unknown.
static int solve(Board& b, int ply, int limit, int alpha, int beta) {
    if (++g_nodes > g_cap) { g_capped = true; return 0; }
    const MoveList moves = b.legal_moves(false);
    if (moves.size() == 0) return b.in_check() ? -(1000 - ply) : 0;
    if (ply >= limit) return 0;             // horizon: claim nothing
    int best = -9999;
    for (const Move m : moves) {
        Undo u; (void)b.make_move(m, u);
        const int s = -solve(b, ply + 1, limit, -beta, -alpha);
        b.unmake_move(m, u);
        if (s > best) best = s;
        if (best > alpha) alpha = best;
        if (alpha >= beta) break;
    }
    return best;
}

int main(int argc, char** argv) {
    if (argc < 3) { std::fprintf(stderr, "usage: mateoracle fen limit [cap]\n"); return 2; }
    Board b; std::string err;
    if (!b.set_fen(argv[1], &err)) { std::printf("REFUSED %s\n", err.c_str()); return 3; }
    const int limit = std::atoi(argv[2]);
    if (argc > 3) g_cap = std::atoll(argv[3]);
    const int s = solve(b, 0, limit, -3000, 3000);
    if (g_capped) { std::printf("CAPPED\n"); return 5; }
    if (s <= -900) std::printf("MATED %d nodes %lld\n", 1000 + s, g_nodes);
    else if (s >= 900) std::printf("MATE %d nodes %lld\n", 1000 - s, g_nodes);
    else std::printf("NOMATE nodes %lld\n", g_nodes);
    return 0;
}
