// Part 2 C: cold depth-9 comparisons over a fixed, ordered FEN corpus.
// Every engine run starts a fresh process, sends ucinewgame, and observes quit,
// both output EOFs, and process status before the position can be committed.
// --offset and --limit count nonblank, noncomment input records, including
// explicitly recorded exclusions. --seed identifies the corpus/run; this
// driver never shuffles it. --out names an append-only JSONL file. Evidence
// goes to <out>.evidence.txt and faults to <out>.pending-<record-index>.txt.
// A position interrupted during its initial pair or ten reproduction pairs
// is journaled as partial, contributes no committed counters, and is retried
// at SUMMARY.next_offset. Completed exclusions do advance that input cursor.
#include "uci_process.hpp"
#include "forge/board.hpp"

#include <charconv>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <optional>

namespace {
using Clock = std::chrono::steady_clock;
constexpr int SearchDepth = 9;
constexpr int Reproductions = 10;
const std::string Options =
    "{\"Threads\":1,\"Hash\":16,\"OwnBook\":false,\"UseNNUE\":true,"
    "\"MultiPV\":1,\"NnueFile\":\"\",\"ContHist4PlyRead\":false,"
    "\"NonPawnCorrection\":false,\"LmrDeeperShallower\":false}";

std::string quote(const std::string& text) {
    static constexpr char hex[] = "0123456789abcdef";
    std::string result = "\"";
    for (const unsigned char c : text) {
        if (c == '"' || c == '\\') { result += '\\'; result += static_cast<char>(c); }
        else if (c < 32) {
            result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15];
        } else result += static_cast<char>(c);
    }
    return result + '"';
}
std::string boolean(bool value) { return value ? "true" : "false"; }
std::string first_line(const std::string& text) { return text.substr(0, text.find('\n')); }
bool sanitizer(const std::string& text) {
    for (const char* marker : {"AddressSanitizer", "UndefinedBehaviorSanitizer", "ThreadSanitizer",
                               "LeakSanitizer", "MemorySanitizer", "runtime error:"})
        if (text.find(marker) != std::string::npos) return true;
    return false;
}
std::uint64_t number(const std::string& text) {
    std::uint64_t value = 0;
    const auto parsed = std::from_chars(text.data(), text.data() + text.size(), value);
    if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size())
        throw std::runtime_error("invalid unsigned integer: " + text);
    return value;
}
struct Config {
    std::string merged, lock, input, out;
    std::uint64_t offset = 0, limit = 100000, seed = 1;
    int seconds = 420;
};
Config arguments(int argc, char** argv) {
    Config c;
    for (int i = 1; i < argc; ++i) {
        const std::string key = argv[i];
        if (i + 1 == argc) throw std::runtime_error("missing value for " + key);
        const std::string value = argv[++i];
        if (key == "--merged") c.merged = value;
        else if (key == "--lock") c.lock = value;
        else if (key == "--input") c.input = value;
        else if (key == "--out") c.out = value;
        else if (key == "--offset") c.offset = number(value);
        else if (key == "--limit") c.limit = number(value);
        else if (key == "--seed") c.seed = number(value);
        else if (key == "--seconds") {
            const auto seconds = number(value);
            if (seconds < 1 || seconds > 420) throw std::runtime_error("--seconds must be 1..420");
            c.seconds = static_cast<int>(seconds);
        } else throw std::runtime_error("unknown argument: " + key);
    }
    if (c.merged.empty() || c.lock.empty() || c.input.empty() || c.out.empty())
        throw std::runtime_error("required: --merged ENGINE --lock ENGINE --input FENS --out FILE");
    return c;
}
std::string result_json(const UciResult& r) {
    std::string pv = "[";
    for (std::size_t i = 0; i < r.pv.size(); ++i) {
        if (i) pv += ',';
        pv += quote(r.pv[i]);
    }
    return "{\"bestmove\":" + quote(r.move) + ",\"score_kind\":" + quote(r.score_kind) +
        ",\"score\":" + std::to_string(r.score) + ",\"bound\":" + quote(r.score_bound) +
        ",\"nodes\":" + std::to_string(r.nodes) + ",\"depth\":" + std::to_string(r.depth) +
        ",\"pv\":" + pv + "],\"reported_ms\":" + std::to_string(r.reported_ms) +
        ",\"wall_ms\":" + std::to_string(r.wall_ms) + "}";
}
struct Run {
    bool attempted = false, budget = false;
    std::optional<UciResult> result;
    std::string error, trace;
    unsigned illegal = 0, missing = 0, missing_info = 0, wrong_depth = 0, diagnostics = 0, transport = 0;
    bool shutdown_observed = false;
    UciShutdownResult shutdown;
    unsigned crashes = 0, nonzero_exits = 0, shutdown_timeouts = 0;
    bool issue() const { return illegal || missing || missing_info || wrong_depth || diagnostics || transport ||
                               crashes || nonzero_exits || shutdown_timeouts; }
    std::string json() const {
        return "{\"attempted\":" + boolean(attempted) + ",\"budget_interrupted\":" + boolean(budget) +
            ",\"result\":" + (result ? result_json(*result) : "null") + ",\"error\":" + quote(error) +
            ",\"illegal\":" + std::to_string(illegal) + ",\"missing\":" + std::to_string(missing) +
            ",\"missing_info\":" + std::to_string(missing_info) + ",\"wrong_depth\":" + std::to_string(wrong_depth) +
            ",\"sanitizer_issues\":" + std::to_string(diagnostics) + ",\"transport_issues\":" + std::to_string(transport) +
            ",\"crashes\":" + std::to_string(crashes) + ",\"nonzero_exits\":" + std::to_string(nonzero_exits) +
            ",\"shutdown_timeouts\":" + std::to_string(shutdown_timeouts) +
            ",\"shutdown\":{\"observed\":" + boolean(shutdown_observed) + ",\"reaped\":" + boolean(shutdown.reaped) +
            ",\"exit_code\":" + std::to_string(shutdown.exit_code) + ",\"signal\":" + std::to_string(shutdown.signal) +
            ",\"timed_out\":" + boolean(shutdown.timed_out) + ",\"driver_sigterm\":" + boolean(shutdown.driver_sigterm) +
            ",\"driver_sigkill\":" + boolean(shutdown.driver_sigkill) + ",\"error\":" + quote(shutdown.error) + "}}";
    }
};
struct Engine {
    std::string path, startup;
    std::unique_ptr<UciProcess> process;
};
int timeout_ms(Clock::time_point deadline) {
    const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - Clock::now()).count();
    return static_cast<int>(std::max<std::int64_t>(0, std::min<std::int64_t>(30000, left)));
}
Run search(Engine& engine, const std::string& fen, const std::vector<std::string>& legal,
           Clock::time_point deadline) {
    Run run;
    if (!timeout_ms(deadline)) { run.budget = true; return run; }
    run.attempted = true;
    // Bound startup plus search together. Eleven failed pairs therefore fit
    // into a fresh 420-second batch instead of forever restarting at one FEN.
    const auto run_deadline = std::min(deadline, Clock::now() + std::chrono::seconds(15));
    std::size_t trace_start = 0;
    bool began_search = false, new_process = false;
    try {
        if (!engine.process) {
            engine.process = std::make_unique<UciProcess>(engine.path, 1, timeout_ms(run_deadline));
            engine.startup = engine.process->transcript();
            new_process = true;
        }
        trace_start = engine.process->transcript().size();
        if (!timeout_ms(run_deadline)) {
            throw std::runtime_error("engine response timeout before search");
        }
        began_search = true;
        run.result = engine.process->search(fen, SearchDepth, timeout_ms(run_deadline), true);
        run.trace = engine.startup + run.result->transcript;
        run.diagnostics = sanitizer((new_process ? engine.startup : "") + run.result->stderr_output) ? 1 : 0;
        if (run.result->move.empty() || run.result->move == "0000" || run.result->move == "(none)") run.missing = 1;
        else if (std::find(legal.begin(), legal.end(), run.result->move) == legal.end()) run.illegal = 1;
        if (run.result->depth != SearchDepth) run.wrong_depth = 1;
    } catch (const std::exception& error) {
        run.error = first_line(error.what());
        run.trace = engine.process && began_search
            ? engine.startup + engine.process->transcript().substr(trace_start)
            : std::string(error.what());
        run.diagnostics = sanitizer(run.trace) ? 1 : 0;
        if (const auto* startup = dynamic_cast<const UciStartupError*>(&error)) {
            run.shutdown = startup->shutdown;
            run.shutdown_observed = true;
        }
        run.budget = !timeout_ms(deadline) && run.error.find("timeout") != std::string::npos;
        if (!run.budget) {
            run.transport = 1;
            run.missing_info = run.error.find("completed score info") != std::string::npos ? 1 : 0;
            run.missing = run.missing_info ? 0 : 1;
        }
    }
    if (engine.process) {
        const int remaining = timeout_ms(deadline);
        run.shutdown = engine.process->finish(std::max(1, std::min(250, remaining)));
        run.shutdown_observed = true;
        run.trace += run.shutdown.transcript;
        if (sanitizer(run.shutdown.stderr_output)) run.diagnostics = 1;
        if (run.shutdown.timed_out && remaining < 250 && !timeout_ms(deadline)) run.budget = true;
        engine.process.reset();
    }
    if (run.shutdown_observed && !run.budget) {
        const bool forced_signal = (run.shutdown.signal == SIGTERM && run.shutdown.driver_sigterm) ||
                                   (run.shutdown.signal == SIGKILL && run.shutdown.driver_sigkill);
        run.crashes = run.shutdown.signal != 0 && !forced_signal;
        run.nonzero_exits = run.shutdown.exit_code > 0;
        run.shutdown_timeouts = run.shutdown.timed_out;
        if (!run.shutdown.reaped || !run.shutdown.error.empty()) run.transport = 1;
    }
    return run;
}
struct Pair {
    Run merged, lock;
    bool complete() const { return merged.attempted && lock.attempted && !merged.budget && !lock.budget; }
    bool different() const { return merged.result && lock.result && !merged.result->same(*lock.result); }
    bool issue() const { return merged.issue() || lock.issue(); }
    std::string json() const {
        return "{\"complete\":" + boolean(complete()) + ",\"different\":" + boolean(different()) +
            ",\"merged\":" + merged.json() + ",\"lock\":" + lock.json() + "}";
    }
};
Pair compare(Engine& merged, Engine& lock, const std::string& fen, const std::vector<std::string>& legal,
             Clock::time_point deadline) {
    Pair pair;
    pair.merged = search(merged, fen, legal, deadline);
    if (!pair.merged.budget) pair.lock = search(lock, fen, legal, deadline);
    return pair;
}
void evidence(std::ostream& out, const std::string& context, int repetition, const Pair& pair) {
    out << "CASE " << context << "\nATTEMPT " << repetition << ' ' << pair.json()
        << "\n=== MERGED FULL TRANSCRIPT ===\n" << pair.merged.trace
        << "\n=== LOCK FULL TRANSCRIPT ===\n" << pair.lock.trace << "\n=== END ATTEMPT ===\n";
    out.flush();
}
struct Counters {
    std::uint64_t records = 0, positions = 0, low = 0, high = 0, diff_low = 0, diff_high = 0, faults = 0;
    std::uint64_t excluded = 0, no_legal = 0, insufficient = 0, rule50 = 0, invalid = 0;
    std::uint64_t searches = 0, illegal = 0, missing = 0, missing_info = 0, wrong_depth = 0, diagnostics = 0, transport = 0;
    std::uint64_t crashes = 0, nonzero_exits = 0, shutdown_timeouts = 0;
    std::uint64_t repro_pairs = 0, repro_differences = 0, repro_faults = 0;
    void account(const Run& run) {
        searches += run.attempted; illegal += run.illegal; missing += run.missing; missing_info += run.missing_info;
        wrong_depth += run.wrong_depth; diagnostics += run.diagnostics; transport += run.transport;
        crashes += run.crashes; nonzero_exits += run.nonzero_exits; shutdown_timeouts += run.shutdown_timeouts;
    }
    void account(const Pair& pair) { account(pair.merged); account(pair.lock); }
    std::string json_fields() const {
        return "\"records_completed\":" + std::to_string(records) + ",\"positions\":" + std::to_string(positions) +
            ",\"positions_low_clock\":" + std::to_string(low) + ",\"positions_high_clock\":" + std::to_string(high) +
            ",\"differences_low_clock\":" + std::to_string(diff_low) + ",\"differences_high_clock\":" + std::to_string(diff_high) +
            ",\"fault_positions\":" + std::to_string(faults) + ",\"excluded\":" + std::to_string(excluded) +
            ",\"excluded_no_legal\":" + std::to_string(no_legal) + ",\"excluded_insufficient\":" + std::to_string(insufficient) +
            ",\"excluded_halfmove100\":" + std::to_string(rule50) + ",\"invalid_fens\":" + std::to_string(invalid) +
            ",\"engine_runs\":" + std::to_string(searches) + ",\"illegal\":" + std::to_string(illegal) +
            ",\"missing\":" + std::to_string(missing) + ",\"missing_info\":" + std::to_string(missing_info) +
            ",\"wrong_depth\":" + std::to_string(wrong_depth) + ",\"sanitizer_issues\":" + std::to_string(diagnostics) +
            ",\"transport_issues\":" + std::to_string(transport) + ",\"crashes\":" + std::to_string(crashes) +
            ",\"nonzero_exits\":" + std::to_string(nonzero_exits) + ",\"shutdown_timeouts\":" + std::to_string(shutdown_timeouts) +
            ",\"reproduction_pairs\":" + std::to_string(repro_pairs) +
            ",\"reproduction_differences\":" + std::to_string(repro_differences) + ",\"reproduction_fault_pairs\":" + std::to_string(repro_faults);
    }
};
bool record_line(std::string& line) {
    if (!line.empty() && line.back() == '\r') line.pop_back();
    const auto start = line.find_first_not_of(" \t");
    if (start == std::string::npos || line[start] == '#') return false;
    line = line.substr(start, line.find_last_not_of(" \t") - start + 1);
    return true;
}
int execute(const Config& config) {
    const auto started = Clock::now();
    // Reserve one second for the two child-process destructors and final flush.
    const auto deadline = started + std::chrono::milliseconds(config.seconds * 1000 - 1000);
    std::ifstream input(config.input);
    if (!input) throw std::runtime_error("cannot open input corpus: " + config.input);
    std::ofstream output(config.out, std::ios::app), details(config.out + ".evidence.txt", std::ios::app);
    output.exceptions(std::ios::badbit | std::ios::failbit);
    details.exceptions(std::ios::badbit | std::ios::failbit);
    const std::string setup = "{\"type\":\"config\",\"merged\":" + quote(config.merged) + ",\"lock\":" + quote(config.lock) +
        ",\"input\":" + quote(config.input) + ",\"offset\":" + std::to_string(config.offset) +
        ",\"limit\":" + std::to_string(config.limit) + ",\"seconds\":" + std::to_string(config.seconds) +
        ",\"seed\":" + std::to_string(config.seed) + ",\"seed_role\":\"metadata_no_shuffle\",\"depth\":9,"
        "\"offset_unit\":\"nonblank_noncomment_input_records_including_exclusions\","
        "\"cold_state\":\"fresh_process_and_ucinewgame_before_every_search\",\"observed_shutdown\":true,"
        "\"startup_and_search_timeout_ms\":15000,\"reproductions_use_new_processes\":true,"
        "\"equality_fields\":[\"bestmove\",\"score_kind\",\"score\",\"nodes\",\"bound\"],\"options\":" + Options + "}";
    output << setup << '\n'; output.flush(); details << "CONFIG " << setup << '\n'; details.flush();
    std::cout << "CONFIG " << setup << std::endl;
    Engine merged{config.merged, {}, {}}, lock{config.lock, {}, {}};
    Counters counters;
    std::uint64_t index = 0, physical_line = 0, next_offset = config.offset;
    bool partial = false, eof = false;
    std::string partial_json = "null", line;
    while (counters.records < config.limit && timeout_ms(deadline)) {
        if (!std::getline(input, line)) { eof = true; break; }
        ++physical_line;
        if (!record_line(line)) continue;
        const std::uint64_t current = index++;
        if (current < config.offset) continue;
        const std::string fen = line;
        forge::Board board;
        std::string error;
        if (!board.set_fen(fen, &error)) {
            const std::string failure = "{\"type\":\"invalid_fen\",\"index\":" + std::to_string(current) +
                ",\"physical_line\":" + std::to_string(physical_line) + ",\"fen\":" + quote(fen) + ",\"error\":" + quote(error) + "}";
            output << failure << '\n'; output.flush(); details << failure << '\n'; details.flush();
            ++counters.invalid; ++counters.faults; ++counters.records; next_offset = current + 1;
            continue;
        }
        const int halfmove = board.halfmove_clock();
        const bool low_clock = halfmove < 80;
        const std::string context = "{\"index\":" + std::to_string(current) + ",\"physical_line\":" + std::to_string(physical_line) +
            ",\"seed\":" + std::to_string(config.seed) + ",\"fen\":" + quote(fen) +
            ",\"halfmove\":" + std::to_string(halfmove) + ",\"required_equality\":" + boolean(low_clock) +
            ",\"depth\":9,\"options\":" + Options + "}";
        const auto legal_moves = board.legal_moves();
        std::string excluded;
        if (legal_moves.empty()) { excluded = "no_legal_moves"; ++counters.no_legal; }
        else if (board.is_insufficient_material()) { excluded = "insufficient_material"; ++counters.insufficient; }
        else if (halfmove >= 100) { excluded = "halfmove_at_least_100"; ++counters.rule50; }
        if (!excluded.empty()) {
            output << "{\"type\":\"excluded\",\"context\":" << context << ",\"reason\":" << quote(excluded) << "}\n";
            output.flush(); ++counters.excluded; ++counters.records; next_offset = current + 1; continue;
        }
        std::vector<std::string> legal;
        for (const auto move : legal_moves) legal.push_back(forge::Board::move_to_uci(move));
        std::vector<Pair> attempts;
        attempts.push_back(compare(merged, lock, fen, legal, deadline));
        const bool initial_difference = attempts.front().different();
        const bool investigate = initial_difference || attempts.front().issue();
        const bool initial_fault = (low_clock && initial_difference) || attempts.front().issue();
        std::ofstream pending;
        std::string pending_path;
        if (initial_fault) {
            pending_path = config.out + ".pending-" + std::to_string(current) + ".txt";
            pending.open(pending_path, std::ios::app);
            pending.exceptions(std::ios::badbit | std::ios::failbit);
            pending << "PENDING FAULT " << context << '\n';
            evidence(pending, context, 0, attempts.front());
        }
        if (investigate || !attempts.front().complete()) evidence(details, context, 0, attempts.front());
        if (attempts.front().complete() && investigate) {
            for (int repetition = 1; repetition <= Reproductions; ++repetition) {
                Engine fresh_merged{config.merged, {}, {}}, fresh_lock{config.lock, {}, {}};
                attempts.push_back(compare(fresh_merged, fresh_lock, fen, legal, deadline));
                evidence(details, context, repetition, attempts.back());
                if (!pending.is_open() && attempts.back().issue()) {
                    pending_path = config.out + ".pending-" + std::to_string(current) + ".txt";
                    pending.open(pending_path, std::ios::app);
                    pending.exceptions(std::ios::badbit | std::ios::failbit);
                    pending << "PENDING FAULT " << context << '\n';
                    for (std::size_t prior = 0; prior + 1 < attempts.size(); ++prior)
                        evidence(pending, context, static_cast<int>(prior), attempts[prior]);
                }
                if (pending.is_open()) evidence(pending, context, repetition, attempts.back());
                if (!attempts.back().complete()) break;
            }
        }
        const bool complete = attempts.back().complete() && (!investigate || attempts.size() == Reproductions + 1);
        if (!complete) {
            partial = true;
            partial_json = "{\"context\":" + context + ",\"initial\":" + attempts.front().json() +
                ",\"attempts_recorded\":" + std::to_string(attempts.size()) +
                ",\"pending_file\":" + quote(pending_path) + ",\"counted\":false}";
            output << "{\"type\":\"partial\",\"data\":" << partial_json << "}\n"; output.flush();
            details << "PARTIAL NOT COUNTED; RETRY SAME INDEX " << partial_json << '\n'; details.flush();
            if (pending.is_open()) { pending << "STATUS PARTIAL NOT COUNTED; RETRY SAME INDEX\n"; pending.flush(); }
            break;
        }
        unsigned repro_differences = 0, repro_faults = 0, original_signatures = 0;
        bool fault = initial_fault;
        for (std::size_t attempt = 0; attempt < attempts.size(); ++attempt) {
            const auto& pair = attempts[attempt];
            counters.account(pair);
            fault = fault || pair.issue() || (low_clock && pair.different());
            if (attempt == 0) continue;
            ++counters.repro_pairs;
            repro_differences += pair.different();
            repro_faults += pair.issue() || (low_clock && pair.different());
            if (pair.merged.result && pair.lock.result && attempts[0].merged.result && attempts[0].lock.result &&
                pair.merged.result->same(*attempts[0].merged.result) && pair.lock.result->same(*attempts[0].lock.result))
                ++original_signatures;
        }
        counters.repro_differences += repro_differences; counters.repro_faults += repro_faults;
        ++counters.positions; ++counters.records;
        if (low_clock) { ++counters.low; counters.diff_low += initial_difference; }
        else { ++counters.high; counters.diff_high += initial_difference; }
        counters.faults += fault;
        next_offset = current + 1;
        const std::string record = "{\"type\":\"position\",\"context\":" + context +
            ",\"initial\":" + attempts.front().json() + ",\"fault\":" + boolean(fault) +
            ",\"reproductions_completed\":" + std::to_string(attempts.size() - 1) +
            ",\"reproduction_difference_frequency\":" + std::to_string(repro_differences) +
            ",\"reproduction_fault_frequency\":" + std::to_string(repro_faults) +
            ",\"reproduction_original_signature_frequency\":" + std::to_string(original_signatures) +
            ",\"pending_file\":" + quote(pending_path) + "}";
        output << record << '\n'; output.flush();
        if (investigate) { details << "COMPLETED " << record << '\n'; details.flush(); }
        if (pending.is_open()) { pending << "STATUS COMPLETE " << record << '\n'; pending.flush(); }
        if (counters.positions % 100 == 0)
            std::cout << "PROGRESS positions=" << counters.positions << " next_offset=" << next_offset
                      << " faults=" << counters.faults << std::endl;
    }
    merged.process.reset(); lock.process.reset();
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - started).count();
    const std::string summary = "{\"type\":\"summary\",\"seed\":" + std::to_string(config.seed) +
        ",\"offset\":" + std::to_string(config.offset) + ",\"next_offset\":" + std::to_string(next_offset) +
        ",\"eof\":" + boolean(eof) + ",\"elapsed_ms\":" + std::to_string(elapsed) +
        ",\"partial\":" + boolean(partial) + ",\"partial_evidence\":" + partial_json + ',' + counters.json_fields() + "}";
    output << summary << '\n'; output.flush(); details << "SUMMARY " << summary << '\n'; details.flush();
    std::cout << "SUMMARY " << summary << std::endl;
    return counters.faults ? 1 : 0;
}
} // namespace

int main(int argc, char** argv) {
    try { return execute(arguments(argc, argv)); }
    catch (const std::exception& error) { std::cerr << "DRIVER_ERROR " << error.what() << '\n'; return 2; }
}
