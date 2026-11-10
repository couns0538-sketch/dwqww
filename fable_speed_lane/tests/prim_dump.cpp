// prim_dump.cpp - differential harness of the fable2 speed lane (own code).
//
// Links the engine's own units (bitboard, board, eval, eval_params, nnue, search) of ONE source tree and
// walks every FEN of a file: the position, every legal child, two grandchildren per child and the null-move
// child. For each visited position it hashes what the search can observe from the board and the evaluation:
//   gen  the three generated move lists (All, Captures, Quiets) in order
//   leg  is_legal of every generated move
//   chk  gives_check of every legal move
//   see  see_ge of every legal move at seven thresholds
//   st   key, pawn key, checkers, clocks, has_legal_move, insufficient material, repetition, key_after
//   ev   hand-crafted eval without cache, eval through the worker's pawn cache, net output, static eval,
//        and the traced evaluation (its value, phase, scale and every coefficient)
// One line of hashes per FEN goes to the output file. Two builds (lock source and candidate source) must write
// byte-identical files: that is the eval and primitive parity proof of a candidate.
//
// The harness also checks each build against itself (exit 3 on any failure):
//   - has_legal_move() equals "the legal list is not empty", asked before and after the king lines exist;
//   - every generated move, legal or not, of every visited position (grandchildren and the null-move child too)
//     is played on a copy whose king lines were built by ONE earlier query (is_legal for even list positions,
//     gives_check for odd ones): is_legal must equal "the mover's king is not attacked afterwards", and the
//     checkers make_move left must equal attackers_to(the other king) & the mover's pieces;
//   - checkers() after the make of every legal child move, on the board that answered every query and on a
//     twin whose king lines were never built;
//   - is_legal / gives_check give the same answers in the other call order on a copy without king lines;
//   - key_after equals the key after make; unmake and null unmake restore the position;
//   - eval through the pawn cache equals eval without cache; static eval through the incremental path equals
//     the refresh path; static eval equals the clamp of hand-crafted eval plus net output.
// The worker's caches are cleared every 997 FENs, so cached values are also met on a just-cleared cache.
//
// If the engine itself aborts (the =2 verify builds of the candidates do that on purpose), the harness prints the
// root FEN, the position and the move it was working on.
//
// usage: prim_dump FENS OUT [first] [count]
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/eval_params.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <csignal>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static SearchStack* slot(Worker& w, int i) { return &w.stack_[static_cast<std::size_t>(i)]; }
    static int static_eval(Worker& w, const Board& b, SearchStack* ss) { return w.static_evaluate(b, ss); }
    static void record(Worker& w, SearchStack* ss, const Board& b, const Move& m) { w.record_move(ss, b, m); }
    static void clear(Worker& w) { w.clear_caches(); }
};
} // namespace forge

namespace {

using namespace forge;

constexpr int Thresholds[7] = {-300, -100, -40, 0, 1, 100, 300};
constexpr int BaseSlot = 4;
constexpr int RefreshSlot = 40;

struct Hashes {
    std::uint64_t gen = 1469598103934665603ULL, leg = gen, chk = gen, see = gen, st = gen, ev = gen;
    std::uint64_t positions = 0, moves = 0;
};

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

long long g_errors = 0;
unsigned long long g_lined_legal = 0, g_lined_illegal = 0;   // makes of generated moves on copies with king lines
std::string g_fen;

void fail(const char* what, const Board& b, Move m = Move::none()) {
    if (++g_errors <= 20) {
        std::fprintf(stderr, "CHECK FAILED: %s | root %s | at %s | move %s\n", what, g_fen.c_str(), b.fen().c_str(),
                     m.is_none() ? "-" : Board::move_to_uci(m).c_str());
    }
}

// What the harness is doing right now, for the report of an abort raised inside the engine. `g_at` always points
// to an unmodified copy of the position being visited.
const Board* g_at = nullptr;
Move g_at_move = Move::none();
const char* g_at_what = "";

void at(const char* what, const Board* b, Move m = Move::none()) {
    g_at_what = what;
    g_at = b;
    g_at_move = m;
}

void on_abort(int) {
    std::fprintf(stderr, "ENGINE ABORT during: %s | root %s | at %s | move %s\n", g_at_what, g_fen.c_str(),
                 g_at != nullptr ? g_at->fen().c_str() : "-",
                 g_at_move.is_none() ? "-" : Board::move_to_uci(g_at_move).c_str());
    std::fflush(stderr);
}

struct Walker {
    SharedSearchState shared{1};
    std::unique_ptr<Worker> worker = std::make_unique<Worker>(shared, 0);
    Hashes h;

    // Evaluations of one position; `inc` is the static eval the incremental path produced (ValueNone = none).
    void evals(const Board& x, int inc) {
        const int hce = Evaluator::evaluate_uncached(x);
        SearchStack* rs = SearcherTestProbe::slot(*worker, RefreshSlot);
        const bool was = nnue::enabled;
        nnue::enabled = false;
        const int cached = SearcherTestProbe::static_eval(*worker, x, rs);       // evaluator_.evaluate: pawn cache path
        nnue::enabled = was;
        if (cached != hce) fail("eval through the pawn cache != eval without cache", x);
        int net = 0, stat = hce;
        if (nnue::available()) {
            auto acc = std::make_unique<nnue::Accumulator>();
            nnue::refresh(x, *acc);
            net = nnue::evaluate(x, *acc);
            rs->ply = 0;
            rs->accumulator.valid = false;
            rs->runtime_psqt.valid = false;
            (rs - 1)->accumulator.valid = false;
            nnue::enabled = true;
            stat = SearcherTestProbe::static_eval(*worker, x, rs);                // refresh path, runtime psqt + cache
            nnue::enabled = was;
            const int want = nnue::residual() ? std::clamp(hce + net, -MateInMaxPly + 1, MateInMaxPly - 1) : net;
            if (stat != want) fail("static eval != clamp(hand-crafted + net)", x);
            if (inc != ValueNone && inc != stat) fail("incremental static eval != refresh static eval", x);
        }
        mix(h.ev, static_cast<std::uint64_t>(static_cast<std::int64_t>(hce)));
        mix(h.ev, static_cast<std::uint64_t>(static_cast<std::int64_t>(net)));
        mix(h.ev, static_cast<std::uint64_t>(static_cast<std::int64_t>(stat)));
        // traced evaluation (the tuner's path): value and every coefficient, folded into one word
        EvalTrace trace;
        const int traced = evaluate_traced(x, trace);
        std::uint64_t fold = 1469598103934665603ULL;
        for (const std::int16_t c : trace.coefficients) fold = (fold ^ static_cast<std::uint16_t>(c)) * 1099511628211ULL;
        mix(h.ev, static_cast<std::uint64_t>(static_cast<std::int64_t>(traced)));
        mix(h.ev, fold);
        mix(h.ev, (static_cast<std::uint64_t>(static_cast<std::uint32_t>(trace.phase)) << 32) |
                      static_cast<std::uint32_t>(trace.scale));
        mix(h.ev, static_cast<std::uint64_t>(static_cast<std::int64_t>(trace.white_eval)));
    }

    // depth 0 = FEN position, 1 = child, 2 = grandchild, 3 = null-move child (no recursion from 2 and 3).
    void visit(Board& x, int depth, SearchStack* ss, int inc) {
        ++h.positions;
        const Board pristine = x;   // never queried: every copy of it starts without king lines
        Board fresh = x;        // has_legal_move() is asked on it before any king lines exist
        Board twin = x;         // twin for make_move without king lines
        at("has_legal_move, generation", &pristine);
        const bool has_before = fresh.has_legal_move();

        MoveList all, caps, quiets;
        x.generate_pseudo_legal(all, Board::GenMode::All);
        x.generate_pseudo_legal(caps, Board::GenMode::Captures);
        x.generate_pseudo_legal(quiets, Board::GenMode::Quiets);
        for (const Move m : all) mix(h.gen, move_bits(m));
        mix(h.gen, 0xA11ULL + all.size());
        for (const Move m : caps) mix(h.gen, move_bits(m));
        mix(h.gen, 0xCA9ULL + caps.size());
        for (const Move m : quiets) mix(h.gen, move_bits(m));
        mix(h.gen, 0x901ULL + quiets.size());

        std::vector<Move> legal;
        std::size_t index = 0;
        for (const Move m : all) {
            ++h.moves;
            at("is_legal, gives_check, see_ge, key_after of one generated move", &pristine, m);
            const bool ok = x.is_legal(m);
            mix(h.leg, (move_bits(m) << 1) | (ok ? 1U : 0U));
            {
                // Play the generated move, legal or not, on a copy whose king lines come from one earlier query,
                // as in the search (is_legal alone for even list positions, gives_check alone for odd ones).
                // Two checks that need no engine rule: is_legal equals "the mover's king is not attacked
                // afterwards", and the checkers make_move left equal attackers_to of the other king.
                Board played = pristine;
                if ((index & 1U) == 0U) (void)played.is_legal(m);
                else (void)played.gives_check(m);
                Undo pu;
                const Color mover = played.side_to_move();
                at("make of a generated move on a copy with king lines", &pristine, m);
                (void)played.make_move(m, pu);
                const Color other = played.side_to_move();
                const bool king_safe = !played.square_attacked(played.king_square(mover), other);
                if (king_safe != ok) fail("is_legal != (own king not attacked after the move)", x, m);
                if ((played.attackers_to(played.king_square(other)) & played.occupied(mover)) != played.checkers())
                    fail("checkers() after the make of a generated move != attackers of the king", x, m);
                ++(ok ? g_lined_legal : g_lined_illegal);
                at("is_legal, gives_check, see_ge, key_after of one generated move", &pristine, m);
            }
            // the other call order, on a copy that has no king lines yet
            if ((index++ & 1U) == 0U) {
                Board f2 = pristine;
                const bool chk2 = f2.gives_check(m);
                const bool ok2 = f2.is_legal(m);
                if (ok2 != ok) fail("is_legal differs with the call order", x, m);
                if (ok && chk2 != x.gives_check(m)) fail("gives_check differs with the call order", x, m);
            }
            if (!ok) continue;
            legal.push_back(m);
            mix(h.chk, (move_bits(m) << 1) | (x.gives_check(m) ? 1U : 0U));
            std::uint64_t bits = 0;
            for (int t = 0; t < 7; ++t) bits |= (x.see_ge(m, Thresholds[t]) ? 1ULL : 0ULL) << t;
            mix(h.see, (move_bits(m) << 8) | bits);
            std::uint64_t early = 0;
            if (x.key_after(m, early)) mix(h.st, early);
        }
        at("has_legal_move after the king lines exist, evaluation", &pristine);
        const bool has_after = x.has_legal_move();
        if (has_before != !legal.empty() || has_after != !legal.empty()) fail("has_legal_move != (legal list not empty)", x);

        const Color us = x.side_to_move();
        const Bitboard real_checkers = x.attackers_to(x.king_square(us)) & x.occupied(opposite(us));
        if (real_checkers != x.checkers()) fail("checkers() != attackers of the own king", x);
        mix(h.st, x.key());
        mix(h.st, x.pawn_key());
        mix(h.st, x.checkers());
        mix(h.st, static_cast<std::uint64_t>(x.halfmove_clock()) | (static_cast<std::uint64_t>(x.ep_square() + 1) << 16) |
                      (static_cast<std::uint64_t>(x.castling_rights()) << 24) | (has_after ? 1ULL << 40 : 0ULL) |
                      (x.is_insufficient_material() ? 1ULL << 41 : 0ULL) | (x.is_repetition(0) ? 1ULL << 42 : 0ULL) |
                      (static_cast<std::uint64_t>(legal.size()) << 48));

        evals(x, inc);
        if (depth >= 2) return;

        // the incremental static-eval path needs this position's own slot to hold a valid accumulator
        int own_static = ValueNone;
        if (nnue::available() && nnue::enabled) {
            if (depth == 0) {
                ss->ply = 0;
                ss->accumulator.valid = false;
                ss->runtime_psqt.valid = false;
                (ss - 1)->accumulator.valid = false;
            }
            own_static = SearcherTestProbe::static_eval(*worker, x, ss);
        }
        const std::uint64_t key0 = x.key(), pawn0 = x.pawn_key();
        const Bitboard chk0 = x.checkers();
        std::size_t n = 0;
        for (const Move m : legal) {
            Undo u, u2;
            int child_inc = ValueNone;
            if (own_static != ValueNone) {
                SearcherTestProbe::record(*worker, ss, x, m);
                (ss + 1)->ply = ss->ply + 1;
            }
            at("make of a legal move on the board with king lines", &pristine, m);
            (void)x.make_move(m, u);
            at("make of a legal move on the twin without king lines", &pristine, m);
            (void)twin.make_move(m, u2);
            if (twin.checkers() != x.checkers() || twin.key() != x.key()) fail("make_move differs without king lines", x, m);
            const Color them = x.side_to_move();
            if ((x.attackers_to(x.king_square(them)) & x.occupied(opposite(them))) != x.checkers())
                fail("checkers() after make != attackers of the king", x, m);
            if (own_static != ValueNone) child_inc = SearcherTestProbe::static_eval(*worker, x, ss + 1);
            if (depth == 0 || n < 2) visit(x, depth + 1, ss + 1, child_inc);
            else {
                mix(h.st, x.key());
                mix(h.st, x.checkers());
                mix(h.ev, static_cast<std::uint64_t>(static_cast<std::int64_t>(child_inc)));
            }
            at("unmake of a legal move", &pristine, m);
            x.unmake_move(m, u);
            twin.unmake_move(m, u2);
            if (x.key() != key0 || x.pawn_key() != pawn0 || x.checkers() != chk0) fail("unmake did not restore", x, m);
            ++n;
        }
        if (!x.in_check() && depth == 0) {
            NullUndo nu;
            at("null move", &pristine);
            x.make_null_move(nu);
            if (x.checkers() != 0) fail("null move child has checkers", x);
            visit(x, 3, ss + 1, ValueNone);
            at("null unmake", &pristine);
            x.unmake_null_move(nu);
            if (x.key() != key0 || x.checkers() != chk0) fail("null unmake did not restore", x);
        }
    }
};

} // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::fprintf(stderr, "usage: prim_dump FENS OUT [first] [count]\n");
        return 1;
    }
    const long first = argc > 3 ? std::atol(argv[3]) : 0;
    const long count = argc > 4 ? std::atol(argv[4]) : -1;
    std::ifstream in(argv[1]);
    if (!in) { std::fprintf(stderr, "cannot read %s\n", argv[1]); return 1; }
    std::FILE* out = std::fopen(argv[2], "wb");
    if (out == nullptr) { std::fprintf(stderr, "cannot write %s\n", argv[2]); return 1; }
    std::signal(SIGABRT, on_abort);
    Walker walker;
    Hashes total;
    std::string line;
    long index = -1, done = 0;
    while (std::getline(in, line)) {
        while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
        if (line.empty() || line[0] == '#') continue;
        ++index;
        if (index < first) continue;
        if (count >= 0 && done >= count) break;
        Board board;
        std::string error;
        if (!board.set_fen(line, &error)) {
            std::fprintf(stderr, "FEN %ld rejected: %s (%s)\n", index, line.c_str(), error.c_str());
            ++g_errors;
            continue;
        }
        g_fen = line;
        walker.h = Hashes{};
        if (done % 997 == 499) forge::SearcherTestProbe::clear(*walker.worker);
        walker.visit(board, 0, forge::SearcherTestProbe::slot(*walker.worker, BaseSlot), ValueNone);
        at("between FENs", nullptr);
        const Hashes& h = walker.h;
        std::fprintf(out, "%ld\t%016llx\t%016llx\t%016llx\t%016llx\t%016llx\t%016llx\t%llu\t%llu\n", index,
                     static_cast<unsigned long long>(h.gen), static_cast<unsigned long long>(h.leg),
                     static_cast<unsigned long long>(h.chk), static_cast<unsigned long long>(h.see),
                     static_cast<unsigned long long>(h.st), static_cast<unsigned long long>(h.ev),
                     static_cast<unsigned long long>(h.positions), static_cast<unsigned long long>(h.moves));
        mix(total.gen, h.gen); mix(total.leg, h.leg); mix(total.chk, h.chk);
        mix(total.see, h.see); mix(total.st, h.st); mix(total.ev, h.ev);
        total.positions += h.positions;
        total.moves += h.moves;
        ++done;
    }
    std::fprintf(out, "TOTAL\t%016llx\t%016llx\t%016llx\t%016llx\t%016llx\t%016llx\t%llu\t%llu\n",
                 static_cast<unsigned long long>(total.gen), static_cast<unsigned long long>(total.leg),
                 static_cast<unsigned long long>(total.chk), static_cast<unsigned long long>(total.see),
                 static_cast<unsigned long long>(total.st), static_cast<unsigned long long>(total.ev),
                 static_cast<unsigned long long>(total.positions), static_cast<unsigned long long>(total.moves));
    std::fclose(out);
    std::printf("generated moves played on copies with king lines: %llu legal, %llu illegal\n", g_lined_legal, g_lined_illegal);
    std::printf("prim_dump: %ld FENs, %llu positions, %llu generated moves, %lld self-check failures\n", done,
                static_cast<unsigned long long>(total.positions), static_cast<unsigned long long>(total.moves), g_errors);
    return g_errors == 0 ? 0 : 3;
}
