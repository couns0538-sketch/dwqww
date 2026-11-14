// Optional bounded Part4 audit; test driver only, no engine changes.
// Build with the same defines/architecture as board.cpp.o and bitboard.cpp.o.
// --lock PATH --merged PATH --out FRESH_DIR [--offset 0 --limit 1 --roots 128
//   --seconds 420 --timeout-ms 30000 --seed 1296127045]
// One atomic unit is one root, all four lock/merged x UseNNUE false/true
// observations, plus ten fresh-process reproductions for each faulty baseline.
// Resume at SUMMARY.next_offset; incomplete units are excluded from totals.
// Positive mate checks use the requested move-DTM <= 2*UCI-mate-1 criterion.
// A failure with an upperbound score is a failed audit criterion, not proof of
// an invalid engine bound. No finite sample establishes universal correctness.
#include "uci_process.hpp"
#include "krk_oracle.hpp"

#include <array>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>

namespace {
using Clock = std::chrono::steady_clock;
std::string quote(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c == '\n') out << "\\n";
        else if (c == '\r') out << "\\r";
        else if (c == '\t') out << "\\t";
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c) << std::dec;
        else out << c;
    }
    out << '"';
    return out.str();
}
const char* boolean(bool v) { return v ? "true" : "false"; }
void save(const std::string& path, const std::string& content) {
    std::ofstream file(path);
    if (!file || !(file << content)) throw std::runtime_error("cannot write " + path);
}
struct Options {
    std::string lock, merged, out;
    std::size_t offset = 0, limit = 1, roots = 128;
    std::uint64_t seed = 1296127045;
    int seconds = 420, timeout_ms = 30000;
};
Options options(int argc, char** argv) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string key = argv[i];
        if (++i == argc) throw std::runtime_error("missing value for " + key);
        const std::string value = argv[i];
        if (key == "--lock") o.lock = value;
        else if (key == "--merged") o.merged = value;
        else if (key == "--out") o.out = value;
        else if (key == "--offset") o.offset = std::stoull(value);
        else if (key == "--limit") o.limit = std::stoull(value);
        else if (key == "--roots") o.roots = std::stoull(value);
        else if (key == "--seed") o.seed = std::stoull(value);
        else if (key == "--seconds") o.seconds = std::stoi(value);
        else if (key == "--timeout-ms") o.timeout_ms = std::stoi(value);
        else throw std::runtime_error("unknown option " + key);
    }
    if (o.lock.empty() || o.merged.empty() || o.out.empty() || o.limit == 0 ||
        o.roots < 1 || o.roots > 10000 || o.offset >= o.roots ||
        o.seconds < 1 || o.seconds > 420 || o.timeout_ms < 1 || o.timeout_ms > 60000)
        throw std::runtime_error("invalid/missing bounded audit options");
    return o;
}
struct Budget {
    Clock::time_point start = Clock::now(), end;
    explicit Budget(int seconds) : end(start + std::chrono::seconds(seconds)) {}
    int left() const { return int(std::chrono::duration_cast<std::chrono::milliseconds>(end - Clock::now()).count()); }
    bool available() const { return left() > 800; }
    int timeout(int requested) const { return std::max(1, std::min(requested, left() - 600)); }
};
std::string fen(int wk, int wr, int bk) {
    std::ostringstream out;
    for (int rank = 7; rank >= 0; --rank) {
        int empty = 0;
        for (int file = 0; file < 8; ++file) {
            const int sq = rank * 8 + file;
            const char piece = sq == wk ? 'K' : sq == wr ? 'R' : sq == bk ? 'k' : 0;
            if (!piece) ++empty;
            else { if (empty) out << empty; empty = 0; out << piece; }
        }
        if (empty) out << empty;
        if (rank) out << '/';
    }
    return out.str() + " w - - 0 1";
}
std::vector<std::string> roots(const Options& o, const soak::KrkOracle& oracle) {
    std::vector<std::string> result{"8/8/8/8/8/1R6/2k5/5K2 w - - 0 1"};
    // Odd multiplier permutes all 64^3 tuples, independent of engine results.
    for (std::uint64_t i = 0; result.size() < o.roots && i < 262144; ++i) {
        const auto state = (i * 176123 + o.seed) & 262143;
        const int wk = state / 4096, wr = (state / 64) % 64, bk = state % 64;
        if (wk == wr || wk == bk || wr == bk || forge::square_distance(wk, bk) <= 1) continue;
        const auto text = fen(wk, wr, bk);
        if (text == result.front()) continue;
        forge::Board board;
        if (!board.set_fen(text) || board.legal_moves().empty()) continue;
        const auto assessment = oracle.assess_root(board);
        if (assessment.supported && assessment.legal) result.push_back(text);
    }
    if (result.size() != o.roots) throw std::runtime_error("root permutation exhausted");
    return result;
}
bool sanitizer(const std::string& text) {
    for (const char* token : {"AddressSanitizer", "UndefinedBehaviorSanitizer", "ThreadSanitizer", "LeakSanitizer", "runtime error:"})
        if (text.find(token) != std::string::npos) return true;
    return false;
}
struct Observation {
    UciResult result;
    UciShutdownResult shutdown;
    bool searched = false, interrupted = false, legal = false, bound_failure = false;
    bool unexpected_exit = false, sanitizer_report = false, operational_fault = false;
    int root_dtm = -1, move_dtm = -1;
    std::int64_t claimed_plies = -1;
    std::string error, trace, stderr_text;
    bool fault() const { return operational_fault || (searched && (!legal || bound_failure)); }
};
Observation observe(const Options& o, Budget& budget, const soak::KrkOracle& oracle,
                    const std::string& root, const std::string& engine, bool nnue) {
    Observation a;
    if (!budget.available()) { a.interrupted = true; a.trace = "! no process started: driver budget\n"; return a; }
    std::unique_ptr<UciProcess> process;
    bool limited = false;
    auto timeout = [&] { const int ms = budget.timeout(o.timeout_ms); limited = ms < o.timeout_ms; return ms; };
    try {
        process = std::make_unique<UciProcess>(engine, 1, timeout());
        process->send(std::string("setoption name UseNNUE value ") + boolean(nnue), timeout());
        process->ready(timeout());
        a.result = process->search(root, 13, timeout(), true);
        a.searched = true;
        forge::Board board;
        if (!board.set_fen(root)) throw std::runtime_error("audit root FEN rejected");
        const auto move = board.parse_uci(a.result.move);
        a.legal = move && board.is_pseudo_legal(*move) && board.is_legal(*move);
        const auto assessment = oracle.assess_move(board, a.legal ? *move : forge::Move{});
        if (!assessment.supported || !assessment.root_legal) throw std::runtime_error("audit root unsupported by oracle");
        a.root_dtm = assessment.root_dtm_plies;
        a.move_dtm = assessment.move_dtm_plies;
        if (a.result.positive_mate()) {
            a.claimed_plies = 2LL * a.result.score - 1;
            a.bound_failure = !a.legal || a.move_dtm < 0 || a.move_dtm > a.claimed_plies;
        }
    } catch (const std::exception& caught) {
        a.error = caught.what();
        const bool response_timeout = a.error.rfind("engine response timeout", 0) == 0 || a.error.rfind("engine stdin timeout", 0) == 0;
        a.interrupted = limited && budget.left() < 1000 && response_timeout;
        if (const auto* startup = dynamic_cast<const UciStartupError*>(&caught)) a.shutdown = startup->shutdown;
    }
    if (process) {
        a.shutdown = process->finish(500);
        a.trace = process->transcript();
        a.stderr_text = process->stderr_output();
    } else {
        a.trace = a.error + "\n" + a.shutdown.transcript;
        a.stderr_text = a.shutdown.stderr_output;
    }
    const bool induced = (a.shutdown.signal == SIGTERM && a.shutdown.driver_sigterm) ||
        (a.shutdown.signal == SIGKILL && a.shutdown.driver_sigkill);
    a.unexpected_exit = a.shutdown.reaped && (a.shutdown.exit_code > 0 || (a.shutdown.signal != 0 && !induced));
    a.sanitizer_report = sanitizer(a.stderr_text + a.error);
    a.operational_fault = a.unexpected_exit || a.sanitizer_report || (!a.interrupted &&
        (!a.error.empty() || !a.searched || !a.shutdown.reaped || a.shutdown.timed_out ||
         !a.shutdown.error.empty() || a.shutdown.exit_code != 0 || a.shutdown.signal != 0 ||
         (a.result.depth < 13 && a.result.score_kind != "mate")));
    return a;
}
std::string json(const Observation& a, const std::string& path) {
    std::ostringstream out;
    out << "{\"searched\":" << boolean(a.searched) << ",\"budget_interrupted\":" << boolean(a.interrupted)
        << ",\"legal_bestmove\":" << boolean(a.legal) << ",\"move\":" << quote(a.result.move)
        << ",\"score_kind\":" << quote(a.result.score_kind) << ",\"score\":" << a.result.score
        << ",\"score_bound\":" << quote(a.result.score_bound) << ",\"depth\":" << a.result.depth
        << ",\"nodes\":" << a.result.nodes << ",\"root_dtm_plies\":" << a.root_dtm
        << ",\"move_dtm_plies\":" << a.move_dtm << ",\"claimed_mate_plies\":" << a.claimed_plies
        << ",\"mate_bound_check_failure\":" << boolean(a.bound_failure)
        << ",\"upperbound_failure_is_not_proof_of_false_bound\":" << boolean(a.bound_failure && a.result.score_bound == "upperbound")
        << ",\"operational_fault\":" << boolean(a.operational_fault) << ",\"fault\":" << boolean(a.fault())
        << ",\"unexpected_exit\":" << boolean(a.unexpected_exit) << ",\"sanitizer_report\":" << boolean(a.sanitizer_report)
        << ",\"shutdown\":{\"reaped\":" << boolean(a.shutdown.reaped) << ",\"exit_code\":" << a.shutdown.exit_code
        << ",\"signal\":" << a.shutdown.signal << ",\"timed_out\":" << boolean(a.shutdown.timed_out)
        << ",\"driver_sigterm\":" << boolean(a.shutdown.driver_sigterm) << ",\"driver_sigkill\":" << boolean(a.shutdown.driver_sigkill)
        << ",\"error\":" << quote(a.shutdown.error) << "},\"error\":" << quote(a.error)
        << ",\"stderr\":" << quote(a.stderr_text) << ",\"transcript\":" << quote(path) << '}';
    return out.str();
}
struct Counts {
    std::size_t trials = 0, positive_mates = 0, bound_failures = 0, illegal_moves = 0;
    std::size_t operational_faults = 0, faults = 0, unexpected_exits = 0, sanitizer_reports = 0;
    std::size_t reproductions = 0, reproduction_faults = 0;
    void record(const Observation& a, bool reproduction) {
        if (reproduction) { ++reproductions; reproduction_faults += a.fault(); }
        else {
            ++trials; positive_mates += a.searched && a.result.positive_mate();
            bound_failures += a.bound_failure; illegal_moves += a.searched && !a.legal;
            operational_faults += a.operational_fault; faults += a.fault();
        }
        unexpected_exits += a.unexpected_exit; sanitizer_reports += a.sanitizer_report;
    }
    void add(const Counts& b) {
        trials += b.trials; positive_mates += b.positive_mates; bound_failures += b.bound_failures;
        illegal_moves += b.illegal_moves; operational_faults += b.operational_faults; faults += b.faults;
        unexpected_exits += b.unexpected_exits; sanitizer_reports += b.sanitizer_reports;
        reproductions += b.reproductions; reproduction_faults += b.reproduction_faults;
    }
    std::string json() const {
        std::ostringstream out;
        out << "{\"trials\":" << trials << ",\"positive_mates_checked\":" << positive_mates
            << ",\"mate_bound_check_failures\":" << bound_failures << ",\"illegal_moves\":" << illegal_moves
            << ",\"operational_faults\":" << operational_faults << ",\"faults\":" << faults
            << ",\"unexpected_exits\":" << unexpected_exits << ",\"sanitizer_reports\":" << sanitizer_reports
            << ",\"reproductions\":" << reproductions << ",\"reproduction_faults\":" << reproduction_faults << '}';
        return out.str();
    }
};
int run(const Options& o, int argc, char** argv) {
    if (std::filesystem::exists(o.out) && !std::filesystem::is_empty(o.out)) throw std::runtime_error("--out must be fresh/empty");
    std::filesystem::create_directories(o.out);
    Budget budget(o.seconds);
    const soak::KrkOracle oracle;
    const auto corpus = roots(o, oracle);
    std::ostringstream config, list;
    config << "{\"mode\":\"mate_bound_audit\",\"argv\":[";
    for (int i = 0; i < argc; ++i) { if (i) config << ','; config << quote(argv[i]); }
    config << "],\"seed\":" << o.seed << ",\"Threads\":1,\"Hash\":16,\"OwnBook\":false,\"depth\":13"
        << ",\"UseNNUE\":[false,true],\"new_options\":\"defaults\",\"fresh_process_each_trial\":true"
        << ",\"reproductions_per_fault\":10,\"oracle\":\"tests_t12 retrograde; shared board/attack primitives; no repetition or fifty-move model\""
        << ",\"selection\":\"Part4 root then fixed permutation of legal White KRK; no engine-score selection\"}\n";
    save(o.out + "/config.json", config.str());
    std::cout << "CONFIG " << config.str();
    for (std::size_t i = 0; i < corpus.size(); ++i) list << i << '\t' << corpus[i] << '\n';
    save(o.out + "/roots.tsv", list.str());
    std::ofstream results(o.out + "/results.jsonl");
    Counts total, partial, observed;
    std::size_t next = o.offset, completed = 0, incomplete = 0, interrupted_observations = 0, interrupted_faults = 0;
    for (; next < corpus.size() && completed < o.limit && budget.available();) {
        Counts unit;
        bool interrupted = false;
        for (int variant = 0; variant < 4 && !interrupted; ++variant) {
            const bool merged = variant / 2, nnue = variant % 2;
            const auto& engine = merged ? o.merged : o.lock;
            bool reproduce = false;
            for (int repetition = 0; repetition == 0 || (reproduce && repetition <= 10); ++repetition) {
                const auto a = observe(o, budget, oracle, corpus[next], engine, nnue);
                const std::string stem = "root-" + std::to_string(next) + (merged ? "-merged" : "-lock") +
                    (nnue ? "-nnue-on" : "-nnue-off") + "-repeat-" + std::to_string(repetition);
                const std::string path = o.out + "/" + stem + ".uci.txt";
                save(path, a.trace); save(o.out + "/" + stem + ".stderr.txt", a.stderr_text);
                const auto observation = json(a, path);
                const std::string row = "{\"root\":" + std::to_string(next) + ",\"fen\":" + quote(corpus[next]) +
                    ",\"build\":" + quote(merged ? "merged" : "lock") + ",\"UseNNUE\":" + boolean(nnue) +
                    ",\"repetition\":" + std::to_string(repetition) + ",\"summary_accounting\":\"completed root units only\",\"observation\":" + observation + '}';
                results << row << '\n'; results.flush(); std::cout << "RESULT " << row << std::endl;
                if (a.fault()) {
                    save(o.out + "/fault-" + stem + ".json", row + "\n");
                    std::cout << "FAULT_RAW_BEGIN " << stem << '\n' << a.trace << "FAULT_RAW_END " << stem << std::endl;
                }
                if (a.interrupted) {
                    ++interrupted_observations; interrupted_faults += a.fault(); interrupted = true; break;
                }
                unit.record(a, repetition != 0); observed.record(a, repetition != 0);
                if (repetition == 0) reproduce = a.fault();
            }
        }
        const std::string completion = "{\"record_type\":\"unit_completion\",\"root\":" + std::to_string(next) +
            ",\"completed\":" + boolean(!interrupted) + ",\"counts\":" + unit.json() + '}';
        results << completion << '\n'; results.flush(); std::cout << "UNIT " << completion << std::endl;
        if (interrupted) { partial.add(unit); ++incomplete; break; }
        total.add(unit); ++completed; ++next;
    }
    std::ostringstream summary;
    summary << "{\"mode\":\"mate_bound_audit\",\"offset\":" << o.offset << ",\"next_offset\":" << next
        << ",\"available_units\":" << corpus.size() << ",\"completed_units\":" << completed << ",\"incomplete_units\":" << incomplete
        << ",\"trials\":" << total.trials << ",\"faults\":" << total.faults << ",\"counts\":" << total.json()
        << ",\"partial_trials_excluded\":" << partial.trials << ",\"partial_counts_excluded\":" << partial.json()
        << ",\"all_noninterrupted_observations\":" << observed.json() << ",\"interrupted_observations\":" << interrupted_observations
        << ",\"interrupted_faults\":" << interrupted_faults << ",\"elapsed_ms\":" << (o.seconds * 1000 - budget.left())
        << ",\"scope\":\"sampled KRK move-DTM checks only; upperbound failures need semantic review; no universal correctness or strength claim\"}\n";
    save(o.out + "/summary.json", summary.str()); std::cout << "SUMMARY " << summary.str();
    return 0;
}
} // namespace
int main(int argc, char** argv) {
    try { return run(options(argc, argv), argc, argv); }
    catch (const std::exception& caught) {
        std::cerr << "SUMMARY {\"driver_error\":" << quote(caught.what()) << "}\n"; return 2;
    }
}
