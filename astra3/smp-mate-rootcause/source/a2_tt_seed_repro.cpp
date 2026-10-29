// IDEA_SOURCE: Round 3 A2 handoff and Forge's public Worker/TT interfaces.
// Test-only experiment; no engine behavior or source modifications.
#include "forge/search.hpp"
#include "forge/nnue.hpp"
#include <algorithm>
#include <atomic>
#include <charconv>
#include <chrono>
#include <condition_variable>
#include <exception>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#ifdef __linux__
#include <sched.h>
#endif

namespace fs = std::filesystem;
using namespace forge;
using Clock = std::chrono::steady_clock;
constexpr const char* Fen = "4R3/8/8/k2K4/8/8/8/8 w - - 0 1";
struct Config {
    std::string mode = "serial";
    fs::path output;
    unsigned trials = 1, max_seed_depth = 14, main_depth = 14;
    unsigned max_seed_nodes = 16384, max_seconds = 120, trial_seconds = 10;
    std::uint64_t seed = 20261029;
    bool smp_v2 = true;
    int cpu = -1;
};
std::uint64_t number(const std::string& value) {
    std::uint64_t n = 0;
    const auto [end, error] = std::from_chars(value.data(), value.data() + value.size(), n);
    if (error != std::errc{} || end != value.data() + value.size()) throw std::runtime_error("invalid integer: " + value);
    return n;
}
Config parse(int argc, char** argv) {
    Config c;
    for (int i = 1; i < argc; i += 2) {
        if (i + 1 >= argc) throw std::runtime_error("every argument requires a value");
        const std::string key = argv[i], value = argv[i + 1];
        if (key == "--out") c.output = value;
        else if (key == "--mode") c.mode = value;
        else if (key == "--seed") c.seed = number(value);
        else {
            const auto n = number(value);
            if (n > 1000000) throw std::runtime_error("argument exceeds numeric safety bound: " + key);
            if (key == "--trials") c.trials = static_cast<unsigned>(n);
            else if (key == "--max-seed-depth") c.max_seed_depth = static_cast<unsigned>(n);
            else if (key == "--main-depth") c.main_depth = static_cast<unsigned>(n);
            else if (key == "--max-seed-nodes") c.max_seed_nodes = static_cast<unsigned>(n);
            else if (key == "--max-seconds") c.max_seconds = static_cast<unsigned>(n);
            else if (key == "--trial-seconds") c.trial_seconds = static_cast<unsigned>(n);
            else if (key == "--cpu") c.cpu = static_cast<int>(n);
            else if (key == "--smp-v2" && n <= 1) c.smp_v2 = n != 0;
            else throw std::runtime_error("unknown or invalid argument: " + key);
        }
    }
    if (c.output.empty() || (c.mode != "serial" && c.mode != "concurrent") || c.trials < 1 || c.trials > 5000 ||
        c.max_seed_depth < 1 || c.max_seed_depth > 14 || c.main_depth < 1 || c.main_depth > 32 ||
        c.max_seconds < 1 || c.max_seconds > 1800 || c.trial_seconds < 1 || c.trial_seconds > 60)
        throw std::runtime_error("invalid bounds: trials 1..5000, seed depth 1..14, main depth 1..32, wall 1..1800, trial 1..60; --out required");
    return c;
}
std::string affinity(int requested_cpu) {
#ifdef __linux__
    cpu_set_t allowed;
    if (sched_getaffinity(0, sizeof(allowed), &allowed) != 0) throw std::runtime_error("sched_getaffinity failed");
    if (requested_cpu >= 0) {
        if (requested_cpu >= CPU_SETSIZE || !CPU_ISSET(requested_cpu, &allowed)) throw std::runtime_error("requested CPU is not allowed");
        cpu_set_t chosen;
        CPU_ZERO(&chosen); CPU_SET(requested_cpu, &chosen);
        if (sched_setaffinity(0, sizeof(chosen), &chosen) != 0) throw std::runtime_error("sched_setaffinity failed");
    }
    if (sched_getaffinity(0, sizeof(allowed), &allowed) != 0) throw std::runtime_error("affinity verification failed");
    std::ostringstream out;
    for (int i = 0; i < CPU_SETSIZE; ++i) if (CPU_ISSET(i, &allowed)) out << i << ',';
    return out.str();
#else
    if (requested_cpu >= 0) throw std::runtime_error("--cpu is supported only on Linux");
    return "UNVERIFIED_non_linux";
#endif
}
Board root_board() {
    Board b;
    if (!b.set_fen(Fen)) throw std::runtime_error("root FEN rejected");
    return b;
}
struct Watched { std::uint64_t key; int ply; std::string fen, path; };
void watch_tree(Board& board, int ply, const std::string& path, std::map<std::uint64_t, Watched>& watched) {
    const auto it = watched.find(board.key());
    if (it == watched.end() || ply < it->second.ply) watched.insert_or_assign(board.key(), Watched{board.key(), ply, board.fen(), path});
    if (ply == 3) return;
    for (const Move move : board.legal_moves()) {
        Undo undo;
        if (!board.make_move(move, undo)) throw std::runtime_error("legal move rejected building watched keys");
        watch_tree(board, ply + 1, path.empty() ? Board::move_to_uci(move) : path + " " + Board::move_to_uci(move), watched);
        board.unmake_move(move, undo);
    }
}
class TrialDeadline {
    SharedSearchState& state_;
    std::mutex mutex_;
    std::condition_variable cv_;
    bool cancelled_ = false;
    std::thread thread_;
public:
    std::atomic<bool> expired{false};
    TrialDeadline(SharedSearchState& state, Clock::time_point deadline) : state_(state), thread_([this, deadline] {
        std::unique_lock lock(mutex_);
        if (!cv_.wait_until(lock, deadline, [this] { return cancelled_; })) {
            expired.store(true, std::memory_order_release);
            state_.stop.store(true, std::memory_order_relaxed);
        }
    }) {}
    ~TrialDeadline() {
        { std::lock_guard lock(mutex_); cancelled_ = true; }
        cv_.notify_one();
        thread_.join();
    }
};
std::string pv_text(const SearchInfo& result) {
    std::ostringstream out;
    for (const auto move : result.pv) out << Board::move_to_uci(move) << ' ';
    return out.str();
}
struct Counts { unsigned main_results = 0, main_cp = 0, exact_mate = 0, other_mate = 0, helper_cp = 0, timeouts = 0, trials = 0; };
void record(std::ofstream& out, Counts& counts, const std::string& condition, unsigned trial, unsigned k, int round,
            const std::string& role, const SearchInfo& r, std::uint64_t local_nodes, unsigned target_nodes,
            std::uint64_t observed_nodes, std::int64_t delay_us, bool helper_done, bool expired) {
    const bool cp = r.score > -MateInMaxPly && r.score < MateInMaxPly;
    const bool exact = r.score == MateValue - 5 && Board::move_to_uci(r.best_move) == "d5c5";
    if (role == "main") {
        ++counts.main_results; counts.main_cp += cp; counts.exact_mate += exact; counts.other_mate += !cp && !exact;
    } else counts.helper_cp += cp;
    out << condition << '\t' << trial << '\t' << k << '\t' << round << '\t' << role << '\t' << r.depth << '\t'
        << r.nominal_depth << '\t' << r.score << '\t' << Board::move_to_uci(r.best_move) << '\t' << pv_text(r) << '\t'
        << r.nodes << '\t' << local_nodes << '\t' << r.elapsed_ms << '\t' << target_nodes << '\t' << observed_nodes
        << '\t' << delay_us << '\t' << helper_done << '\t' << expired << '\t'
        << (cp ? "CP" : exact ? "EXPECTED_EXACT" : "OTHER_MATE_UNVERIFIED") << '\n';
    out.flush();
}
void snapshot(std::ofstream& out, SharedSearchState& shared, const std::map<std::uint64_t, Watched>& watched,
              const std::string& condition, unsigned trial, unsigned k) {
    // probe() ages hits. This runs only after BOTH searches, with no later search
    // in this trial; it must never move between measured searches.
    for (const auto& [key, pos] : watched) {
        const auto p = shared.tt.probe(key);
        const auto& e = p.entry;
        out << condition << '\t' << trial << '\t' << k << '\t' << pos.ply << '\t' << key << '\t' << pos.path << '\t'
            << pos.fen << '\t' << p.hit << '\t';
        if (p.hit) out << e.score << '\t' << static_cast<int>(e.depth) << '\t' << static_cast<int>(e.bound()) << '\t'
                       << e.pv() << '\t' << static_cast<int>(e.rule50_clock) << '\t' << Board::move_to_uci(e.move)
                       << '\t' << static_cast<int>(e.generation());
        else out << "NA\tNA\tNA\tNA\tNA\tNA\tNA";
        out << '\n';
    }
    out.flush();
}
void run_trial(const Config& config, const std::string& condition, unsigned trial, unsigned k, std::mt19937_64& rng,
               Clock::time_point wall_end, const std::map<std::uint64_t, Watched>& watched,
               std::ofstream& results, std::ofstream& snapshots, Counts& counts) {
    SharedSearchState shared(16);
    auto main_worker = std::make_unique<Worker>(shared, 0);
    auto helper = std::make_unique<Worker>(shared, 1);
    const bool empty = condition == "empty_control";
    const bool concurrent = condition == "concurrent";
    const std::vector<Worker*> all = empty ? std::vector<Worker*>{main_worker.get()} : std::vector<Worker*>{main_worker.get(), helper.get()};
    TrialDeadline deadline(shared, std::min(wall_end, Clock::now() + std::chrono::seconds(config.trial_seconds)));
    for (int round = 1; round <= 2; ++round) {
        shared.tt.new_search();
        main_worker->reset_published_nodes(); helper->reset_published_nodes();
        SearchLimits limits;
        limits.depth = static_cast<int>(config.main_depth);
        limits.fb2.smp_v2 = config.smp_v2;
        SearchLimits helper_limits = limits;
        if (!concurrent) helper_limits.depth = static_cast<int>(k);
        SearchInfo helper_result, main_result;
        std::atomic<bool> helper_done{empty};
        std::exception_ptr helper_error;
        std::thread helper_thread;
        const auto begin = Clock::now();
        const unsigned target = concurrent ? static_cast<unsigned>(rng() % (static_cast<std::uint64_t>(config.max_seed_nodes) + 1)) : 0;
        if (!empty) {
            const auto run_helper = [&] {
                try { helper_result = helper->search(root_board(), helper_limits, false, all); }
                catch (...) { helper_error = std::current_exception(); shared.stop.store(true, std::memory_order_relaxed); }
                helper->end_search();
                helper_done.store(true, std::memory_order_release);
            };
            if (concurrent) {
                helper_thread = std::thread(run_helper);
                while (helper->nodes() < target && !helper_done.load(std::memory_order_acquire) &&
                       !deadline.expired.load(std::memory_order_acquire)) std::this_thread::yield();
            } else run_helper();
        }
        const auto observed_nodes = helper->nodes();
        const bool done_at_main_start = helper_done.load(std::memory_order_acquire);
        const auto delay_us = std::chrono::duration_cast<std::chrono::microseconds>(Clock::now() - begin).count();
        try {
            if (!deadline.expired.load(std::memory_order_acquire)) main_result = main_worker->search(root_board(), limits, false, all);
        } catch (...) {
            shared.stop.store(true, std::memory_order_relaxed);
            if (helper_thread.joinable()) helper_thread.join();
            main_worker->end_search();
            throw;
        }
        shared.stop.store(true, std::memory_order_relaxed);
        if (helper_thread.joinable()) helper_thread.join();
        main_worker->end_search();
        if (helper_error) std::rethrow_exception(helper_error);
        const bool expired = deadline.expired.load(std::memory_order_acquire);
        record(results, counts, condition, trial, k, round, "main", main_result, main_worker->nodes(), target, observed_nodes, delay_us, done_at_main_start, expired);
        if (!empty) record(results, counts, condition, trial, k, round, "helper", helper_result, helper->nodes(), target, observed_nodes, delay_us, done_at_main_start, expired);
        if (expired) { ++counts.timeouts; break; }
        shared.stop.store(false, std::memory_order_relaxed);
    }
    snapshot(snapshots, shared, watched, condition, trial, k);
    ++counts.trials;
}
int main(int argc, char** argv) {
    try {
        const auto c = parse(argc, argv);
        const auto cpus = affinity(c.cpu);
        if (!fs::create_directory(c.output)) throw std::runtime_error("output directory must be NEW: " + c.output.string());
        std::ofstream metadata(c.output / "run_metadata.txt"), results(c.output / "worker_results.tsv"), snapshots(c.output / "final_tt_snapshots.tsv");
        metadata.exceptions(std::ios::badbit | std::ios::failbit);
        results.exceptions(std::ios::badbit | std::ios::failbit);
        snapshots.exceptions(std::ios::badbit | std::ios::failbit);
        metadata << "engine_source=926c55f33227bc4a030d7ce5b1140528aeba75af\nbranch_base=93c51b3\nfixture=" << Fen
                 << "\nmode=" << c.mode << "\nseed=" << c.seed << "\ntrials_per_condition=" << c.trials
                 << "\nmain_depth=" << c.main_depth << "\nmax_seed_depth=" << c.max_seed_depth << "\nmax_seed_nodes=" << c.max_seed_nodes
                 << "\nsmp_v2=" << c.smp_v2 << "\naffinity=" << cpus << "\nmax_seconds=" << c.max_seconds << "\ntrial_seconds=" << c.trial_seconds
                 << "\nsizeof_SearchInfo=" << sizeof(SearchInfo) << "\nsizeof_Worker=" << sizeof(Worker) << "\nNNUE_hidden=" << nnue::HiddenSize
                 << "\nNNUE_available=" << nnue::available() << "\nNNUE_enabled=" << nnue::enabled
                 << "\nHashMB=16\nLocklessTT=false\nSmpHelpersPastDepth=false\nselector=NOT_RUN_raw_worker_results\n"
                 << "node_counters_reset_before_each_round=true\nschedule=seeded_targets_only_OS_interleaving_NOT_deterministic\n"
                 << "snapshots=after_both_searches_only_probe_ages_hits_no_per_store_origin_or_history_proof\ncommand=";
        for (int i = 0; i < argc; ++i) metadata << std::quoted(argv[i]) << ' ';
        metadata << '\n'; metadata.flush();
        if (options::lockless_tt || options::smp_helpers_past_depth || options::hard_deadline_ms != 0)
            throw std::runtime_error("unexpected non-default global option");
        if (!nnue::available() || !nnue::enabled || nnue::HiddenSize != 256) throw std::runtime_error("expected embedded enabled H256 network");
        Board root = root_board(); // Initialize static attack tables before launching any helper.
        std::map<std::uint64_t, Watched> watched;
        watch_tree(root, 0, "", watched);
        metadata << "watched_unique_keys=" << watched.size() << '\n'; metadata.flush();
        results << "condition\ttrial\tseed_depth\tround\tworker\tactual_depth\tnominal_depth\tscore\tmove\tpv\treported_nodes\tworker_nodes\telapsed_ms\ttarget_helper_nodes\tobserved_helper_nodes\tmain_start_delay_us\thelper_done_at_main_start\ttimeout\tclassification\n";
        snapshots << "condition\ttrial\tseed_depth\tminimum_ply\tkey\tfirst_path\tfen\thit\traw_score\tdepth\tbound_1upper_2lower_3exact\tpv\trule50_clock\tmove\tgeneration\n";
        std::mt19937_64 rng(c.seed);
        const auto wall_end = Clock::now() + std::chrono::seconds(c.max_seconds);
        Counts counts;
        bool budget_exhausted = false;
        for (unsigned trial = 1; trial <= c.trials && !budget_exhausted; ++trial) {
            const unsigned max_k = c.mode == "serial" ? c.max_seed_depth : 1;
            for (unsigned k = 1; k <= max_k && !budget_exhausted; ++k) {
                for (const auto& condition : c.mode == "serial" ? std::vector<std::string>{"empty_control", "serial_seeded"}
                                                                : std::vector<std::string>{"concurrent"}) {
                    if (Clock::now() >= wall_end) { budget_exhausted = true; break; }
                    run_trial(c, condition, trial, c.mode == "serial" ? k : 0, rng, wall_end, watched, results, snapshots, counts);
                    if (counts.timeouts != 0) { budget_exhausted = true; break; }
                }
            }
        }
        std::ofstream summary(c.output / "summary.txt");
        summary << "completed_condition_trials=" << counts.trials << "\nmain_results=" << counts.main_results
                << "\nmain_cp=" << counts.main_cp << "\nmain_exact_fixture_mate=" << counts.exact_mate
                << "\nmain_other_mate_UNVERIFIED=" << counts.other_mate << "\nhelper_cp=" << counts.helper_cp
                << "\ntimeouts=" << counts.timeouts << "\nbudget_exhausted=" << budget_exhausted
                << "\nconclusion=DIAGNOSTIC_COUNTS_ONLY_NO_FIX_OR_ELO_CLAIM\n";
        summary.close();
        std::cout << "main_results=" << counts.main_results << " main_cp=" << counts.main_cp << " timeouts=" << counts.timeouts << '\n';
        return budget_exhausted ? 3 : 0; // A reproduced chess symptom is data, not a harness error.
    } catch (const std::exception& error) {
        std::cerr << "HARNESS_ERROR " << error.what() << '\n';
        return 2;
    }
}
