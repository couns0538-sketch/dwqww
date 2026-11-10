// evaldump.cpp - static-evaluation transcript of ONE source tree over a FEN file (own code, job fable4cpu).
//
// Links the engine's own units (bitboard, board, book, eval, eval_params, nnue, search) and, for every FEN,
// writes what the search would see as static evaluation:
//   net on : the root through Worker::static_evaluate on the refresh path, the raw network output, every legal
//            child through the incremental path (record_move, make_move, static_evaluate), and for each child up to
//            two grandchildren, alternately with the child's accumulator kept (one update) and dropped (the
//            walk-back replays two updates);
//   net off: the root and every legal child through Worker::static_evaluate with UseNNUE false.
// Children and grandchildren are folded into one hash per FEN. Two builds must write identical lines.
// This is a test binary: it shows that two SOURCE TREES evaluate alike. It is separate evidence and not a
// statement about what a release exe exposes (the lock exe has no static-eval command).
//
// usage: evaldump FENS OUT_NET_ON OUT_NET_OFF
// Row format (tab separated, 5 columns, as rows.py expects): index, root value, raw net (or -),
// children "count:hash", grandchildren "count:hash" (or -).
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <cstdint>
#include <cstdio>
#include <fstream>
#include <memory>
#include <string>

namespace forge {
struct SearcherTestProbe {
    static SearchStack* slot(Worker& w, int i) { return &w.stack_[static_cast<std::size_t>(i)]; }
    static int static_eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void record(Worker& w, SearchStack* ss, const Board& b, const Move& m) { w.record_move(ss, b, m); }
};
} // namespace forge

namespace {
using namespace forge;

void mix(std::uint64_t& h, std::uint64_t v) {
    for (int i = 0; i < 8; ++i) {
        h ^= (v >> (8 * i)) & 0xFFU;
        h *= 1099511628211ULL;
    }
}

std::uint64_t move_bits(Move m) {
    return static_cast<std::uint64_t>(m.from) | (static_cast<std::uint64_t>(m.to) << 8) |
           (static_cast<std::uint64_t>(m.promotion) << 16) | (static_cast<std::uint64_t>(m.flags) << 24);
}

constexpr int BaseSlot = 4;
constexpr std::uint64_t Seed = 1469598103934665603ULL;
} // namespace

int main(int argc, char** argv) {
    if (argc < 4) {
        std::fprintf(stderr, "usage: evaldump FENS OUT_NET_ON OUT_NET_OFF\n");
        return 2;
    }
    std::ifstream in(argv[1]);
    std::FILE* on = std::fopen(argv[2], "wb");
    std::FILE* off = std::fopen(argv[3], "wb");
    if (!in || on == nullptr || off == nullptr) {
        std::fprintf(stderr, "cannot open files\n");
        return 2;
    }
    if (!nnue::available()) {
        std::fprintf(stderr, "no network compiled in\n");
        return 2;
    }
    SharedSearchState shared{1};
    auto worker = std::make_unique<Worker>(shared, 0);
    Worker& w = *worker;
    std::string fen;
    long long index = 0, bad = 0;
    while (std::getline(in, fen)) {
        while (!fen.empty() && (fen.back() == '\r' || fen.back() == ' ')) fen.pop_back();
        if (fen.empty()) continue;
        ++index;
        Board b;
        if (!b.set_fen(fen)) {
            ++bad;
            std::fprintf(on, "%lld\tBADFEN\t-\t-\t-\n", index);
            std::fprintf(off, "%lld\tBADFEN\t-\t-\t-\n", index);
            continue;
        }
        SearchStack* ss = SearcherTestProbe::slot(w, BaseSlot);
        for (int mode = 0; mode < 2; ++mode) {
            nnue::enabled = (mode == 0);
            ss->ply = 0;
            ss->accumulator.valid = false;
            ss->runtime_psqt.valid = false;
            (ss - 1)->accumulator.valid = false;
            const int root = SearcherTestProbe::static_eval(w, b, ss);
            int raw = 0;
            if (mode == 0) {
                auto acc = std::make_unique<nnue::Accumulator>();
                nnue::refresh(b, *acc);
                raw = nnue::evaluate(b, *acc);
            }
            std::uint64_t ch = Seed, gh = Seed;
            long long nc = 0, ng = 0;
            for (const Move m : b.legal_moves()) {
                Board x = b;
                (ss + 1)->ply = 1;
                SearcherTestProbe::record(w, ss, b, m);
                Undo undo;
                (void)x.make_move(m, undo);
                const int child = SearcherTestProbe::static_eval(w, x, ss + 1);
                mix(ch, move_bits(m));
                mix(ch, static_cast<std::uint64_t>(static_cast<std::int64_t>(child)));
                ++nc;
                if (mode == 0) {
                    int k = 0;
                    for (const Move g : x.legal_moves()) {
                        if (k >= 2) break;
                        Board y = x;
                        (ss + 2)->ply = 2;
                        if ((nc + k) % 2 == 1) {
                            // drop the child's accumulator: the walk-back must replay both updates
                            (ss + 1)->accumulator.valid = false;
                            (ss + 1)->runtime_psqt.valid = false;
                        }
                        SearcherTestProbe::record(w, ss + 1, x, g);
                        Undo undo2;
                        (void)y.make_move(g, undo2);
                        const int grand = SearcherTestProbe::static_eval(w, y, ss + 2);
                        mix(gh, move_bits(g));
                        mix(gh, static_cast<std::uint64_t>(static_cast<std::int64_t>(grand)));
                        ++ng;
                        ++k;
                    }
                }
            }
            if (mode == 0) {
                std::fprintf(on, "%lld\t%d\t%d\t%lld:%016llx\t%lld:%016llx\n", index, root, raw, nc,
                             static_cast<unsigned long long>(ch), ng, static_cast<unsigned long long>(gh));
            } else {
                std::fprintf(off, "%lld\t%d\t-\t%lld:%016llx\t-\n", index, root, nc, static_cast<unsigned long long>(ch));
            }
        }
    }
    nnue::enabled = true;
    std::fclose(on);
    std::fclose(off);
    std::printf("evaldump positions %lld bad %lld\n", index, bad);
    return bad == 0 ? 0 : 3;
}
