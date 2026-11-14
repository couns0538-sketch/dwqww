// Supplemental, artificial TT-seeded search witnesses. They prove move reachability,
// not mate soundness or original-root reproduction. Run only in a gate=1 build.
#include "forge/search.hpp"
#include <chrono>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#if !defined(FORGE_MATE_ALPHA_GUARD) || !FORGE_MATE_ALPHA_GUARD
#error "This supplemental test requires FORGE_MATE_ALPHA_GUARD=1 in every translation unit"
#endif

namespace forge {
struct SearchSample { int score; std::uint64_t nodes; bool aborted; };
struct SearcherTestProbe {
    static void prepare(Worker& w) {
        w.start_ = std::chrono::steady_clock::now();
        w.root_depth_ = 13;
        w.root_history_index_ = 0;
        for (std::size_t i = 0; i < w.stack_.size(); ++i) {
            auto& ss = w.stack_[i];
            ss.ply = static_cast<int>(i) - 4;
            ss.continuation = &(*w.continuation_history_)[Empty][0];
        }
    }
    static void history_edge(Worker& w, const Board& b, Move m, int ply) {
        auto& ss = w.stack_[static_cast<std::size_t>(ply + 4)];
        ss.current_move = m;
        ss.moved_piece = b.moved_piece(m);
        ss.continuation = &(*w.continuation_history_)[ss.moved_piece][m.to];
    }
    static SearchSample enter(Worker& w, Board& b, int depth, int alpha, int raw_eval,
                              Move first_killer, Move second_killer, Move target,
                              int target_history) {
        auto* ss = &w.stack_[12]; // Logical ply 8, with four prefix stack entries.
        ss->killers = {first_killer, second_killer};
        (ss - 2)->static_eval = raw_eval; // Controlled non-improving context.
        (*w.main_history_)[b.side_to_move()][target.from][target.to] =
            static_cast<std::int16_t>(target_history);
        const int score = w.search(b, ss, depth, alpha, alpha + 1, false);
        return {score, w.local_nodes_, w.aborted_};
    }
};
} // namespace forge

namespace {
using namespace forge;
constexpr int Low = 31979;
constexpr int Marker = 31987; // 32000 - (logical ply 8 + forced-line length 5).
constexpr std::string_view Root = "8/8/8/8/8/1R6/2k5/5K2 w - - 0 1";
constexpr std::string_view Internal = "8/8/8/8/8/3R4/8/k2K4 w - - 8 5";
constexpr std::string_view Ancestry[] = {
    "b3f3", "c2b2", "f1e2", "b2c2", "f3d3", "c2b2", "e2d1", "b2a1"
};
enum class Mode { Off, Narrow, BroadMateAlpha };
struct Fixture {
    std::string_view fen, first, target;
    int depth = 5;
    int raw_eval = 0;
    bool known_history = false;
    std::string_view intervening_quiet{};
    int target_history = 0;
};
struct IntSetting {
    int& value; int saved;
    IntSetting(int& ref, int next) : value(ref), saved(ref) { value = next; }
    ~IntSetting() { value = saved; }
};
void require(bool ok, std::string_view what) {
    if (!ok) throw std::runtime_error(std::string(what));
}
Move legal(Board& b, std::string_view text) {
    auto move = b.parse_uci(text);
    require(move.has_value() && b.is_legal(*move), "fixture move is not legal: " + std::string(text));
    return *move;
}
void play(Board& b, Move m) {
    Undo undo;
    require(b.make_move(m, undo), "fixture make_move failed");
}
Board position(const Fixture& f, Worker* worker = nullptr) {
    Board b;
    require(b.set_fen(f.known_history ? Root : f.fen), "fixture FEN rejected");
    if (f.known_history) {
        int ply = 0;
        for (auto text : Ancestry) {
            const auto m = legal(b, text);
            if (worker) SearcherTestProbe::history_edge(*worker, b, m, ply);
            play(b, m);
            ++ply;
        }
        require(b.fen() == Internal, "replayed ancestry does not reach proven node");
        require(!b.is_repetition(0), "fixture history unexpectedly repeats");
    }
    return b;
}
int stored_score(int local, int ply) {
    if (local >= MateInMaxPly) return local + ply;
    if (local <= -MateInMaxPly) return local - ply;
    return local;
}
void seed(TranspositionTable& tt, const Board& b, int raw_score, int raw_eval,
          Move move, int depth, Bound bound) {
    const auto probe = tt.probe(b.key());
    tt.store(probe, b.key(), raw_score, raw_eval, move, depth, bound, false, b.halfmove_clock());
}
SearchSample run(const Fixture& f, Mode mode, int alpha = 31982,
                 int low = Low, int marker = Marker) {
    tune::MateAlphaGuard = mode == Mode::Narrow;
    tune::SoundMatePruning = false;
    tune::SoundArmPv = tune::SoundArmInCheck = tune::SoundPruneArm::ForceOff;
    tune::SoundArmMateAlpha = mode == Mode::BroadMateAlpha ? tune::SoundPruneArm::ForceOn : tune::SoundPruneArm::ForceOff;
    SharedSearchState shared(16);
    auto worker = std::make_unique<Worker>(shared, 0);
    SearcherTestProbe::prepare(*worker);
    Board b = position(f, worker.get());
    const auto original_fen = b.fen();
    const auto first = legal(b, f.first), target = legal(b, f.target);
    require(first != target && !b.in_check(), "fixture must start out of check with distinct moves");
    require(!b.gives_check(target), "target must exercise non-checking futility/SEE path");

    // Every direct child answers immediately through its exact TT entry. Only
    // the target returns the marker. Therefore a marker from Worker::search
    // proves that target was made and searched; no production trace hook is used.
    for (const auto move : b.legal_moves()) {
        Board child = b;
        play(child, move);
        const int answer = move == target ? marker : low;
        seed(shared.tt, child, stored_score(-answer, 9), ValueNone, Move::none(), 32, BoundExact);
    }
    // Check all seeds after all insertions: detect accidental cluster eviction.
    for (const auto move : b.legal_moves()) {
        Board child = b;
        play(child, move);
        const auto probe = shared.tt.probe(child.key());
        const int answer = move == target ? marker : low;
        require(probe.hit && probe.entry.score == stored_score(-answer, 9), "child seed was lost");
    }
    // The invalid score supplies only move ordering and ordinary static eval.
    // A TT move also prevents IIR from reducing the requested internal depth 5.
    seed(shared.tt, b, ValueNone, f.raw_eval, first, 0, BoundUpper);
    const auto killer1 = f.intervening_quiet.empty() ? target : legal(b, f.intervening_quiet);
    const auto killer2 = f.intervening_quiet.empty() ? Move::none() : target;
    auto result = SearcherTestProbe::enter(*worker, b, f.depth, alpha, f.raw_eval,
                                         killer1, killer2, target, f.target_history);
    require(!result.aborted && b.fen() == original_fen, "search aborted or failed to restore board");
    return result;
}
void score_is(std::string_view label, const SearchSample& r, int expected) {
    std::cout << label << " score=" << r.score << " nodes=" << r.nodes << '\n';
    require(r.score == expected, "unexpected search result: " + std::string(label));
}
void prove_legal_mate_line(const Fixture& quiet) {
    Board b = position(quiet);
    constexpr std::string_view line[] = {"d1c1", "a1a2", "c1c2", "a2a1", "d3a3"};
    for (std::size_t i = 0; i < 5; ++i) {
        const auto m = legal(b, line[i]);
        if (i % 2 == 1) {
            const auto replies = b.legal_moves();
            require(replies.size() == 1 && replies[0] == m, "black reply was not forced");
        }
        play(b, m);
        require(!b.is_repetition(0), "forced continuation repeats");
    }
    require(b.in_check() && b.legal_moves().empty() && b.halfmove_clock() == 13,
            "known five-ply continuation did not finish in mate");
}
void exclusion_control(std::string_view label, const Fixture& f) {
    score_is(std::string(label) + " narrow retains pruning", run(f, Mode::Narrow), Low);
    score_is(std::string(label) + " broad arm reaches target", run(f, Mode::BroadMateAlpha), Marker);
}
} // namespace

int main() {
    try {
        nnue::enabled = false;
        dead_material_enabled = false;
        require(!tune::MateAlphaGuard, "MateAlphaGuard must default false");
        const Fixture quiet{Internal, "d3d2", "d1c1", 5, 521, true};
        prove_legal_mate_line(quiet);
        score_is("quiet mate-alpha off", run(quiet, Mode::Off), Low);
        score_is("quiet mate-alpha narrow", run(quiet, Mode::Narrow), Marker);
        {
            IntSetting capture_futility(tune::CaptureFutilityBase, 100);
            const Fixture capture{"7k/8/8/3p4/8/3R4/8/4K3 w - - 0 1", "e1f1", "d3d5", 3};
            auto b = position(capture);
            const auto target = legal(b, capture.target);
            require(target.is_capture() && b.see_ge(target, 0), "capture witness must pass SEE");
            score_is("capture mate-alpha off", run(capture, Mode::Off), Low);
            score_is("capture mate-alpha narrow", run(capture, Mode::Narrow), Marker);
            for (const auto& f : {quiet, capture}) {
                const auto off = run(f, Mode::Off, 2000, 100, 5000);
                const auto on = run(f, Mode::Narrow, 2000, 100, 5000);
                score_is("ordinary-alpha off", off, 100);
                score_is("ordinary-alpha narrow", on, 100);
                require(off.nodes == on.nodes, "ordinary-alpha node count changed");
            }
        }
        {
            Fixture lmp = quiet;
            lmp.depth = 1;
            lmp.intervening_quiet = "d1e1";
            exclusion_control("LMP", lmp);
            IntSetting later_lmp(tune::LmpBase, 20);
            score_is("LMP positive reachability control", run(lmp, Mode::Narrow), Marker);
        }
        {
            Fixture history = quiet;
            history.depth = 2;
            history.target_history = -16384;
            exclusion_control("history", history);
            history.target_history = 0;
            score_is("history positive reachability control", run(history, Mode::Narrow), Marker);
        }
        {
            const Fixture quiet_see{"k2r4/8/8/8/8/3R4/8/4K3 w - - 0 1", "d3d8", "d3d5", 3};
            auto b = position(quiet_see);
            const auto target = legal(b, quiet_see.target);
            require(!b.see_ge(target, -96) && b.see_ge(target, -600), "quiet SEE geometry changed");
            exclusion_control("quiet SEE", quiet_see);
            IntSetting looser_see(tune::SeeQuietMultiplier, 150);
            score_is("quiet SEE positive reachability control", run(quiet_see, Mode::Narrow), Marker);
        }
        {
            const Fixture noisy_see{"3r3k/8/8/3p4/8/3Q4/8/4K3 w - - 0 1", "e1f1", "d3d5", 2};
            auto b = position(noisy_see);
            const auto target = legal(b, noisy_see.target);
            require(target.is_capture() && !b.see_ge(target, -300) && b.see_ge(target, -1000),
                    "noisy SEE geometry changed");
            exclusion_control("noisy SEE", noisy_see);
            IntSetting looser_see(tune::SeeNoisyMultiplier, 500);
            score_is("noisy SEE positive reachability control", run(noisy_see, Mode::Narrow), Marker);
        }
        std::cout << "PASS supplemental seeded search witnesses; original-root trace still required\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "FAIL " << e.what() << '\n';
        return 1;
    }
}
