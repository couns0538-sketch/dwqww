// FB2-J4 flag-loss simulator: plays simulated games with the engine's own time-management decision code
// (include/forge/timeman.hpp: allocate / decide_v1 / decide_v2 / check_mask) against a stochastic model of the
// search (iteration node counts with a random effective branching factor, speed jitter per move and per
// iteration, optional scheduler stalls) and a clock model that reads the time only at the engine's check points.
// Usage: forge_timeman_sim [games=2000] [--seed N] [--stall-ms M] [--stall-prob P] [--nps N] [--csv file]
// Exit status 1 when TimeManV2 loses a game on time at any time control.
#include "forge/search.hpp"
#include "forge/timeman.hpp"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

using namespace forge;

namespace {

struct Options {
    int games = 2000;
    std::uint64_t seed = 1;
    double stall_ms = 0.0;      // length of a scheduler stall inserted at a random point of a move
    double stall_prob = 0.0;    // probability per move
    double nps = 1500.0;        // nodes per millisecond, nominal
    double overhead_ms = 10.0;  // UCI Move Overhead
    double latency_ms = 1.0;    // GUI -> engine -> GUI latency charged to the engine
    std::string csv;
};

struct Tc {
    const char* name;
    double base_ms;
    double inc_ms;
};

struct Stats {
    int games = 0, moves = 0, flags = 0, hard_overshoots = 0;
    double max_overshoot_ms = -1e9;   // used - hard (positive: beyond the hard deadline)
    double min_clock_ms = 1e9;        // lowest remaining time after a move
    double sum_fraction = 0.0;        // used / soft budget
    double max_fraction = 0.0;
    double sum_depth = 0.0;
    int max_check_interval = 0;
};

struct MoveResult {
    double used_ms;
    double soft_ms;
    double hard_ms;
    int depth;
    int max_interval;
};

timeman::Scaling scaling_from_tune() {
    timeman::Scaling s;
    s.stable_factor = tune::TmStableFactor;
    s.semi_stable_factor = tune::TmSemiStableFactor;
    s.unstable_factor = tune::TmUnstableFactor;
    s.effort_base = tune::TmEffortBase;
    s.falling_eval_percent = tune::TmFallingEvalPercent;
    s.min_factor_percent = tune::TmMinFactorPercent;
    return s;
}

timeman::Allocation allocation_from_tune() {
    timeman::Allocation a;
    a.soft_divisor = tune::TmSoftDivisor;
    a.increment_percent = tune::TmIncrementPercent;
    a.hard_percent = tune::TmHardPercent;
    a.hard_soft_multiple = tune::TmHardSoftMultiple;
    return a;
}

// One move: iterative deepening with modelled iterations; the clock is read only at the check points.
MoveResult play_move(bool v2, double clock_ms, double inc_ms, const Options& o, std::mt19937_64& rng) {
    const timeman::Budget budget = timeman::allocate(static_cast<std::int64_t>(clock_ms), static_cast<std::int64_t>(inc_ms), 0,
                                                     static_cast<int>(o.overhead_ms), allocation_from_tune());
    const timeman::Scaling scaling = scaling_from_tune();
    std::lognormal_distribution<double> speed_jitter(0.0, 0.25);
    std::lognormal_distribution<double> iter_jitter(0.0, 0.10);
    std::lognormal_distribution<double> ebf_dist(std::log(2.0), 0.35);
    std::uniform_real_distribution<double> uni(0.0, 1.0);
    const double move_nps = o.nps * speed_jitter(rng);
    const bool stall = uni(rng) < o.stall_prob;
    const double stall_at = uni(rng) * static_cast<double>(budget.hard_ms);   // the stall happens at this elapsed time
    double elapsed = o.latency_ms;   // ms of real time consumed so far (the engine sees it through the clock)
    double stall_added = 0.0;
    std::uint64_t nodes = 0;
    std::uint64_t mask = 1023;
    std::uint64_t soft_node_limit = 0;
    int max_interval = 0;
    std::uint64_t iteration_nodes = 0, previous_iteration_nodes = 0;
    int stable = 0, score = 0, previous_score = 32002;
    double nodes_planned = 400.0;
    int depth_reached = 0;
    bool aborted = false;
    for (int depth = 1; depth <= 64 && !aborted; ++depth) {
        const double nps_iter = move_nps * iter_jitter(rng);
        const std::uint64_t target = static_cast<std::uint64_t>(nodes_planned);
        std::uint64_t done = 0;
        while (done < target) {
            // advance to the next check point (a multiple of mask + 1 in the running node count, as in the engine)
            // or to the end of the iteration, whichever comes first
            const std::uint64_t next_check = (nodes / (mask + 1) + 1) * (mask + 1);
            const std::uint64_t chunk = std::min<std::uint64_t>(next_check - nodes, target - done);
            done += chunk;
            nodes += chunk;
            elapsed += static_cast<double>(chunk) / nps_iter;
            if (stall && stall_added == 0.0 && elapsed >= stall_at) { elapsed += o.stall_ms; stall_added = o.stall_ms; }
            max_interval = std::max(max_interval, static_cast<int>(mask + 1));
            if ((nodes & mask) == 0) {
                // the engine's should_stop(): hard deadline, then the v2 adaptive mask and soft node limit
                const std::int64_t el = static_cast<std::int64_t>(elapsed);
                if (el >= budget.hard_ms) { aborted = true; break; }
                if (v2) {
                    mask = timeman::check_mask(static_cast<double>(nodes) / static_cast<double>(std::max<std::int64_t>(el, 1)), budget.hard_ms - el);
                    if (soft_node_limit > 0 && nodes >= soft_node_limit) { aborted = true; break; }
                }
            }
        }
        if (aborted) break;
        depth_reached = depth;
        previous_iteration_nodes = iteration_nodes;
        iteration_nodes = target;
        // modelled search outcome
        const bool changed = uni(rng) < (depth < 8 ? 0.25 : 0.10);
        stable = changed ? 0 : stable + 1;
        const int new_score = score + static_cast<int>((uni(rng) - 0.5) * 60.0);
        previous_score = depth > 1 ? score : 32002;
        score = new_score;
        timeman::Iteration it;
        it.depth = depth;
        it.score = score;
        it.previous_score = previous_score;
        it.stable_iterations = stable;
        it.nodes_total = nodes;
        it.nodes_iteration = iteration_nodes;
        it.nodes_previous_iteration = previous_iteration_nodes;
        it.best_move_nodes = static_cast<std::uint64_t>(static_cast<double>(nodes) * (0.3 + 0.6 * uni(rng)));
        it.elapsed_ms = static_cast<std::int64_t>(elapsed);
        if (v2) {
            const timeman::Decision d = timeman::decide_v2(budget, scaling, it);
            soft_node_limit = d.soft_node_limit;
            if (d.stop) break;
        } else if (timeman::decide_v1(budget, scaling, it)) {
            break;
        }
        nodes_planned *= std::clamp(ebf_dist(rng), 1.3, 4.0);
    }
    return {elapsed + o.latency_ms, static_cast<double>(budget.soft_ms), static_cast<double>(budget.hard_ms), depth_reached, max_interval};
}

Stats simulate(bool v2, const Tc& tc, const Options& o, std::uint64_t seed, std::FILE* csv) {
    Stats st;
    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> uni(0.0, 1.0);
    for (int g = 0; g < o.games; ++g) {
        double clock[2] = {tc.base_ms, tc.base_ms};
        bool lost = false;
        for (int ply = 0; ply < 300; ++ply) {
            const int side = ply & 1;
            const MoveResult m = play_move(v2, clock[side], tc.inc_ms, o, rng);
            ++st.moves;
            st.sum_depth += m.depth;
            const double fraction = m.used_ms / std::max(m.soft_ms, 1.0);
            st.sum_fraction += fraction;
            st.max_fraction = std::max(st.max_fraction, fraction);
            st.max_overshoot_ms = std::max(st.max_overshoot_ms, m.used_ms - m.hard_ms);
            if (m.used_ms > m.hard_ms) ++st.hard_overshoots;
            st.max_check_interval = std::max(st.max_check_interval, m.max_interval);
            if (m.used_ms > clock[side]) { lost = true; ++st.flags; }
            clock[side] = clock[side] - m.used_ms + tc.inc_ms;
            st.min_clock_ms = std::min(st.min_clock_ms, clock[side]);
            if (csv) std::fprintf(csv, "%s,%s,%d,%d,%.3f,%.3f,%.3f,%d,%.3f\n", tc.name, v2 ? "v2" : "v1", g, ply, m.used_ms, m.soft_ms, m.hard_ms, m.depth, clock[side]);
            if (lost) break;
            if (uni(rng) < 1.0 / 80.0) break;   // random game end, about 80 plies on average
        }
        ++st.games;
    }
    return st;
}

} // namespace

int main(int argc, char** argv) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--seed" && i + 1 < argc) o.seed = std::strtoull(argv[++i], nullptr, 10);
        else if (a == "--stall-ms" && i + 1 < argc) o.stall_ms = std::atof(argv[++i]);
        else if (a == "--stall-prob" && i + 1 < argc) o.stall_prob = std::atof(argv[++i]);
        else if (a == "--nps" && i + 1 < argc) o.nps = std::atof(argv[++i]);
        else if (a == "--overhead" && i + 1 < argc) o.overhead_ms = std::atof(argv[++i]);
        else if (a == "--csv" && i + 1 < argc) o.csv = argv[++i];
        else o.games = std::atoi(argv[i]);
    }
    const Tc tcs[] = {{"1+0.01", 1000.0, 10.0}, {"10+0.1", 10000.0, 100.0}};
    std::FILE* csv = o.csv.empty() ? nullptr : std::fopen(o.csv.c_str(), "wb");
    if (csv) std::fputs("tc,version,game,ply,used_ms,soft_ms,hard_ms,depth,clock_after\n", csv);
    int v2_flags = 0;
    std::printf("timeman simulation: games %d per cell, seed %llu, nps %.0f/ms, stall %.1f ms with p=%.3f, overhead %.0f ms, latency %.1f ms\n",
                o.games, static_cast<unsigned long long>(o.seed), o.nps, o.stall_ms, o.stall_prob, o.overhead_ms, o.latency_ms);
    std::printf("%-8s %-3s %6s %7s %6s %10s %12s %10s %9s %9s %9s\n", "tc", "ver", "games", "moves", "flags", "hard_over", "max_over_ms", "min_clock", "mean_frac", "max_frac", "mean_dep");
    for (const Tc& tc : tcs) {
        for (int v = 0; v < 2; ++v) {
            const Stats st = simulate(v == 1, tc, o, o.seed + static_cast<std::uint64_t>(v) * 7919ULL, csv);
            if (v == 1) v2_flags += st.flags;
            std::printf("%-8s %-3s %6d %7d %6d %10d %12.3f %10.1f %9.3f %9.3f %9.2f (max check interval %d nodes)\n", tc.name, v ? "v2" : "v1", st.games, st.moves,
                        st.flags, st.hard_overshoots, st.max_overshoot_ms, st.min_clock_ms, st.sum_fraction / std::max(st.moves, 1), st.max_fraction,
                        st.sum_depth / std::max(st.moves, 1), st.max_check_interval);
        }
    }
    if (csv) std::fclose(csv);
    std::printf(v2_flags == 0 ? "PASS: no flag losses with TimeManV2\n" : "FAIL: %d flag losses with TimeManV2\n", v2_flags);
    return v2_flags == 0 ? 0 : 1;
}
