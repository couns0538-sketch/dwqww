// qsearch probe v2: window sweep, optional TT seeding via a real search,
// optional direct TT planting, hard deadline. Instrumented build required.
#include "forge/board.hpp"
#include "forge/search.hpp"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <iostream>
#include <sstream>
#include <optional>

namespace forge {
struct SearcherTestProbe {
    static int qsearch(Worker& w, Board& b, SearchStack* ss, int alpha, int beta) { return w.qsearch(b, ss, alpha, beta); }
    static SearchStack* stack_base(Worker& w) { return &w.stack_[0]; }
    static void set_root_history(Worker& w, std::size_t i) { w.root_history_index_ = i; }
    static std::uint64_t local_nodes(const Worker& w) { return w.local_nodes_; }
    static int seldepth(const Worker& w) { return w.seldepth_; }
    static void set_seldepth(Worker& w, int v) { w.seldepth_ = v; }
    static void prepare(Worker& w) {
        for (SearchStack& ss : w.stack_) {
            ss.pv_length = 0; ss.current_move = Move::none(); ss.excluded_move = Move::none();
            ss.moved_piece = Empty; ss.static_eval = ValueNone; ss.raw_eval = ValueNone;
            ss.continuation = nullptr; ss.double_extensions = 0; ss.withheld_plies = 0;
            ss.null_move_allowed = true; ss.arrival_index = 0; ss.killers = {};
            ss.accumulator.valid = false; ss.runtime_psqt.valid = false;
            ss.diff_known = false; ss.entered_null = false; ss.dirty.count = 0;
        }
        for (int i = 0; i < MaxPly + 4; ++i) w.stack_[static_cast<std::size_t>(i)].ply = i - 4;
    }
    // Plant an entry for this exact position at a given depth/bound, the way a
    // deep main-search node would, so the qsearch probe can be tested against it.
    static void plant(Worker& w, Board& b, int score, Move move, int depth, Bound bound, bool pv) {
        TTProbe p = w.shared_.tt.probe(b.key());
        w.shared_.tt.store(p, b.key(), score, ValueNone, move, depth, bound, pv,
                           static_cast<std::uint16_t>(b.halfmove_clock()));
    }
    static void clear_tt(Worker& w) { w.shared_.tt.clear(); }
};
} // namespace forge

using namespace forge;

static void reset_trace() {
#if FORGE_QS_TRACE
    qs_trace = QsTrace{};
    qs_trace.min_clock = 1000;   // the default 0 would read as "a node at clock 0"
#ifdef FORGE_QS_NEST_TRACE
    g_qs_check_depth = 0; g_qs_max_check_depth = 0; g_qs_parent_in_check = false;
#endif
#endif
}

static std::string trace_json() {
#if FORGE_QS_TRACE
    std::ostringstream o;
    o << "{\"nodes\":" << qs_trace.nodes
      << ",\"in_check_nodes\":" << qs_trace.in_check_nodes
      << ",\"in_check_no_captures\":" << qs_trace.in_check_no_captures
      << ",\"terminal_checkmate\":" << qs_trace.terminal_checkmate
      << ",\"terminal_stalemate\":" << qs_trace.terminal_stalemate
      << ",\"clock100_nodes\":" << qs_trace.clock100_nodes
      << ",\"tt_cutoffs\":" << qs_trace.tt_cutoffs
      << ",\"standpat_returns\":" << qs_trace.standpat_returns
      << ",\"mated_returns\":" << qs_trace.mated_returns
      << ",\"stores\":" << qs_trace.stores
      << ",\"max_ply\":" << qs_trace.max_ply << ",\"max_clock\":" << qs_trace.max_clock << ",\"min_clock\":" << qs_trace.min_clock << ",\"leaf_nocap\":" << qs_trace.leaf_no_capture_nodes
      << ",\"c100_inchk\":" << qs_trace.clock100_in_check
      << ",\"c100_outchk\":" << qs_trace.clock100_not_in_check
#ifdef FORGE_QS_NEST_TRACE
      << ",\"max_inchk_ply\":" << qs_trace.max_in_check_ply
      << ",\"nested_inchk\":" << qs_trace.nested_in_check
#endif
#ifdef FORGE_QS_NEST_TRACE
      << ",\"maxchkdepth\":" << g_qs_max_check_depth
#endif
      << "}";
    return o.str();
#else
    return "{}";
#endif
}

int main(int argc, char** argv) {
    // qs_probe2 fen a_lo a_hi [--seed depth] [--ply p] [--plant score depth bound] [--nott] [--novas]
    if (argc < 4) { std::cerr << "usage\n"; return 2; }
    std::string fen = argv[1];
    const int a_lo = std::atoi(argv[2]);
    const int a_hi = std::atoi(argv[3]);
    int seed_depth = 0, start_ply = 0, plant_score = 0, plant_depth = 0;
    std::string plant_bound; bool no_tt = false; std::vector<std::string> after_moves; bool sweep = false;
    for (int i = 4; i < argc; ++i) {
        std::string a = argv[i];
        if (a == "--seed") seed_depth = std::atoi(argv[++i]);
        else if (a == "--after") { after_moves.push_back(argv[++i]); }
        else if (a == "--ply") start_ply = std::atoi(argv[++i]);
        else if (a == "--plant") { plant_score = std::atoi(argv[++i]); plant_depth = std::atoi(argv[++i]); plant_bound = argv[++i]; }
        else if (a == "--nott") no_tt = true;
        else if (a == "--sweep") sweep = true;
    }
    Board b; std::string err;
    if (!b.set_fen(fen, &err)) { std::cout << "{\"refused\":true,\"err\":\"" << err << "\"}\n"; return 3; }
    for (const std::string& mv : after_moves) {
        const std::optional<Move> m = b.parse_uci(mv);
        if (!m) { std::cout << "{\"badmove\":\"" << mv << "\"}\n"; return 4; }
        Undo u; (void)b.make_move(*m, u);
        if (b.fen() == "" ) {}
    }
    const std::size_t hist = b.history_size();

    Searcher searcher(32, 1);
    Worker& w = searcher.main_worker();

    // Optional: warm the table with a real main search on this same position.
    if (seed_depth > 0) {
        SearchLimits lim; lim.depth = seed_depth;
        (void)searcher.search(b, lim, false);
    }
    if (no_tt) SearcherTestProbe::clear_tt(w);

    SearcherTestProbe::prepare(w);
    SearcherTestProbe::set_root_history(w, hist);

    if (!plant_bound.empty()) {
        Bound bd = plant_bound == "lower" ? BoundLower : (plant_bound == "upper" ? BoundUpper : BoundExact);
        SearcherTestProbe::plant(w, b, plant_score, Move::none(), plant_depth, bd, false);
    }

    // INVARIANT: stack_ index k must carry ply k-4, because static_evaluate and
    // record_move index stack_ by ply (ss->ply + 4). Violating it segfaults.
    SearchStack* base = SearcherTestProbe::stack_base(w);
    for (int i = 0; i < forge::MaxPly + 8; ++i) (base + i)->ply = i - 4;
    if (start_ply + 4 >= forge::MaxPly + 8) { std::cout << "{\"error\":\"ply too high\"}\n"; return 6; }
    SearchStack* ss = base + start_ply + 4;
    ss->ply = start_ply;
    // A frame's accumulator must be seeded for the NNUE increment to be valid.
    SearcherTestProbe::set_seldepth(w, start_ply);

    reset_trace();
    const std::uint64_t n0 = SearcherTestProbe::local_nodes(w);
    std::vector<int> scores;
    int lo = a_lo, hi = a_hi;
    if (!sweep) {
        reset_trace();
        SearcherTestProbe::set_seldepth(w, start_ply);
        scores.push_back(SearcherTestProbe::qsearch(w, b, ss, lo, hi));
    } else {
        for (int a = lo; a <= hi; ++a) {
            // A cold table per window point: a TT hit from the previous point
            // would return that point's answer and make the sweep look flat.
            SearcherTestProbe::clear_tt(w);
            if (!plant_bound.empty()) {
                Bound bd = plant_bound == "lower" ? BoundLower : (plant_bound == "upper" ? BoundUpper : BoundExact);
                SearcherTestProbe::plant(w, b, plant_score, Move::none(), plant_depth, bd, false);
            }
            reset_trace();
            SearcherTestProbe::prepare(w);
            SearcherTestProbe::set_root_history(w, hist);
            SearchStack* base2 = SearcherTestProbe::stack_base(w);
            for (int i = 0; i < forge::MaxPly + 8; ++i) (base2 + i)->ply = i - 4;
            SearchStack* ss2 = base2 + start_ply + 4;
            ss2->ply = start_ply;
            SearcherTestProbe::set_seldepth(w, start_ply);
            scores.push_back(SearcherTestProbe::qsearch(w, b, ss2, a, a + 1));
        }
    }
    const std::uint64_t n1 = SearcherTestProbe::local_nodes(w);
    std::cout << "{\"fen\":\"" << fen << "\",\"scores\":[";
    for (std::size_t i = 0; i < scores.size(); ++i) { if (i) std::cout << ","; std::cout << scores[i]; }
    std::cout << "],\"a_lo\":" << lo << ",\"a_hi\":" << hi
              << ",\"nodes\":" << (n1 - n0) << ",\"maxply\":" << SearcherTestProbe::seldepth(w)
              << ",\"trace\":" << trace_json() << "}\n";
    return 0;
}
