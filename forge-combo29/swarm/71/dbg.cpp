// Minimal debug: one board, compare the four accumulator producers.
//   A = refresh()            (scalar, from pieces, no cache)
//   B = refresh_cached()     (per-worker cache, cold)
//   C = incremental from parent via apply_changes under the same king key
//   D = incremental via make_valid/replay_ply, as the search does it
// usage: dbg <net> <fen> <move>
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v3.hpp"

#include <cstdio>
#include <cstdlib>
#include <string>

using namespace forge;
using namespace forge::nnue::v3;
using forge::nnue::DirtyPieces;

void dump(const char* label, const Accumulator& a, int hidden) {
    long long sum[2] = {0, 0};
    int mn[2] = {32767, 32767};
    int mx[2] = {-32768, -32768};
    for (int p = 0; p < 2; ++p) {
        for (int h = 0; h < hidden; ++h) {
            const int v = a.values[static_cast<std::size_t>(p)][static_cast<std::size_t>(h)];
            sum[p] += v;
            if (v < mn[p]) mn[p] = v;
            if (v > mx[p]) mx[p] = v;
        }
    }
    std::printf("%-10s keyW %d/%d keyB %d/%d ksqW %d ksqB %d sumW %lld sumB %lld rangeW [%d,%d] rangeB [%d,%d]\n",
                label, a.keys[0].bucket, a.keys[0].flip, a.keys[1].bucket, a.keys[1].flip,
                static_cast<int>(a.king_sq[0]), static_cast<int>(a.king_sq[1]), sum[0], sum[1],
                mn[0], mx[0], mn[1], mx[1]);
}

int compare(const char* x, const Accumulator& a, const char* y, const Accumulator& b, int hidden) {
    int diffs = 0;
    int worst = 0;
    int first = -1;
    for (int p = 0; p < 2; ++p) {
        for (int h = 0; h < hidden; ++h) {
            const int d = a.values[static_cast<std::size_t>(p)][static_cast<std::size_t>(h)] -
                          b.values[static_cast<std::size_t>(p)][static_cast<std::size_t>(h)];
            if (d != 0) {
                if (first < 0) first = p * hidden + h;
                ++diffs;
                if (std::abs(d) > std::abs(worst)) worst = d;
            }
        }
    }
    std::printf("COMPARE %s vs %s : differing units %d worst %d first_index %d\n", x, y, diffs, worst, first);
    return diffs;
}

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    std::string error;
    if (!load(argv[1], &error)) {
        std::fprintf(stderr, "load: %s\n", error.c_str());
        return 1;
    }
    const Net& net = *loaded();
    const std::string fen = argc > 2 ? argv[2] : std::string(Board::StandardStartFen);
    const std::string move_text = argc > 3 ? argv[3] : std::string("g1f3");

    Board board;
    if (!board.set_fen(fen)) {
        std::fprintf(stderr, "bad fen\n");
        return 1;
    }
    const Move move = *board.parse_uci(move_text);

    Accumulator a;
    refresh(net, board, a);
    dump("refresh", a, net.hidden);

    WorkerState state;
    prepare(net, state, 64);
    Accumulator b;
    refresh_cached(net, state.cache, board, b);
    dump("cached", b, net.hidden);
    std::printf("eval refresh %d cached %d\n", evaluate_reference(net, board), evaluate(net, board, b));

    // Incremental: apply the move's change list under the parent's key.
    const DirtyPieces dirty = nnue::dirty_from_move(move, board.piece_at(move.from), board.captured_piece(move),
                                                    board.side_to_move());
    std::printf("dirty count %d:", dirty.count);
    for (int i = 0; i < dirty.count; ++i) {
        std::printf(" [%s %d sq %d]", dirty.changes[static_cast<std::size_t>(i)].add ? "add" : "del",
                    static_cast<int>(dirty.changes[static_cast<std::size_t>(i)].piece),
                    static_cast<int>(dirty.changes[static_cast<std::size_t>(i)].square));
    }
    std::printf("\n");

    Board child = board;
    Undo undo;
    if (!child.make_move(move, undo)) {
        std::fprintf(stderr, "illegal move\n");
        return 1;
    }
    Accumulator c;
    for (const Color p : {White, Black}) {
        const auto pi = static_cast<std::size_t>(p);
        c.king_sq[pi] = static_cast<std::uint8_t>(child.king_square(p));
        c.keys[pi] = king_key(net, p, child.king_square(p));
        if (c.keys[pi] == a.keys[pi]) {
            apply_changes(net, a.values[pi].data(), c.values[pi].data(), c.keys[pi], p, dirty);
        } else {
            std::printf("king key changed for perspective %d on a %s\n", static_cast<int>(p), move_text.c_str());
            refresh_perspective(net, child, p, c);
        }
    }
    dump("increm", c, net.hidden);

    Accumulator d;
    refresh(net, child, d);
    dump("child-ref", d, net.hidden);

    int bad = 0;
    bad += compare("refresh", a, "cached", b, net.hidden) != 0;
    bad += compare("increm", c, "child-ref", d, net.hidden) != 0;
    std::printf("eval increm %d child-reference %d\n", evaluate(net, child, c), evaluate_reference(net, child));
    return bad == 0 ? 0 : 3;
}
