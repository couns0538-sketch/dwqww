// Bounded UCI endgame observations. This is a test driver, not an engine change.
// Build with the normal engine objects except uci.cpp.o, using their exact flags.
// Examples (run from repository root; use a separate --out for each invocation):
//   endgame_driver --mode prepare --merged MERGED --lock LOCK --corpus CORPUS.tsv
//     --out LOGDIR --offset 0 --limit 40 --seconds 420
//   endgame_driver --mode mates --merged MERGED --lock LOCK --corpus CORPUS.tsv
//     --out LOGDIR --offset 0 --limit 8 --seconds 420
//   endgame_driver --mode cost --merged MERGED --lock LOCK --out LOGDIR
//     --offset 0 --limit 40 --seconds 420
// Resume at SUMMARY.next_offset. A partial work unit is rerun in full.
// prepare indices 0..39 retain the supplied KRK roots; subsequent indices are
// deterministic KQK/KBBK candidates selected ONLY by lock-T1 positive exact mate.
// The merged-T1 observation is recorded but never used to exclude a root.
// mates units: root, then build (lock, merged), then threads (2,4), ten trials.
// cost units: 200 deterministic legal roots, build (lock,merged), threads (1,2).
// Each trial sends ucinewgame/isready to reset histories and hash. An incomplete
// PV is never treated as evidence of a false mate. Interrupted groups retain
// their records but do not contribute to completed SUMMARY trial totals.
#include "uci_process.hpp"
#include "forge/board.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Clock = std::chrono::steady_clock;

std::string json_quote(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        switch (c) {
        case '"': out << "\\\""; break;
        case '\\': out << "\\\\"; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default:
            if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c) << std::dec;
            else out << c;
        }
    }
    out << '"';
    return out.str();
}

std::string boolean(bool value) { return value ? "true" : "false"; }
std::string padded(std::uint64_t value) {
    std::ostringstream out;
    out << std::setw(6) << std::setfill('0') << value;
    return out.str();
}

struct Options {
    std::string mode = "mates", merged, lock;
    std::string roots = "forge-combo29/soak_all/krk_roots.txt", corpus, out;
    std::uint64_t seed = 0x434f4d424f323941ULL;
    std::size_t offset = 0, limit = 1;
    int seconds = 420, timeout_ms = 30000, depth = 0, trials = 10;
    std::vector<int> threads;
};

Options options(int argc, char** argv) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string key = argv[i];
        if (key == "--help") {
            std::cout << "--mode prepare|mates|cost --merged PATH --lock PATH --out DIR "
                         "[--roots FILE --corpus TSV --seed UINT --offset N --limit N "
                         "--seconds 1..420 --timeout-ms N --depth N --trials N --threads 1,2]\n";
            std::exit(0);
        }
        if (++i == argc) throw std::runtime_error("missing value for " + key);
        const std::string value = argv[i];
        if (key == "--mode") o.mode = value;
        else if (key == "--merged") o.merged = value;
        else if (key == "--lock") o.lock = value;
        else if (key == "--roots") o.roots = value;
        else if (key == "--corpus") o.corpus = value;
        else if (key == "--out") o.out = value;
        else if (key == "--seed") o.seed = std::stoull(value);
        else if (key == "--offset") o.offset = std::stoull(value);
        else if (key == "--limit") o.limit = std::stoull(value);
        else if (key == "--seconds") o.seconds = std::stoi(value);
        else if (key == "--timeout-ms") o.timeout_ms = std::stoi(value);
        else if (key == "--depth") o.depth = std::stoi(value);
        else if (key == "--trials") o.trials = std::stoi(value);
        else if (key == "--threads") {
            std::istringstream list(value);
            std::string item;
            while (std::getline(list, item, ',')) o.threads.push_back(std::stoi(item));
        } else throw std::runtime_error("unknown option " + key);
    }
    if (o.mode != "prepare" && o.mode != "mates" && o.mode != "cost") throw std::runtime_error("invalid mode");
    if (o.merged.empty() || o.lock.empty() || o.out.empty()) throw std::runtime_error("--merged, --lock, --out required");
    if (o.seconds < 1 || o.seconds > 420 || o.timeout_ms < 1 || o.timeout_ms > 60000 ||
        o.trials < 1 || o.trials > 10 || o.limit == 0) throw std::runtime_error("invalid bounds");
    if (o.depth == 0) o.depth = o.mode == "cost" ? 12 : 14;
    if (o.depth < 1 || o.depth > 64) throw std::runtime_error("invalid depth");
    if (o.threads.empty()) o.threads = o.mode == "prepare" ? std::vector<int>{1} :
        o.mode == "cost" ? std::vector<int>{1, 2} : std::vector<int>{2, 4};
    for (int n : o.threads) if (n < 1 || n > 4) throw std::runtime_error("threads must be 1..4");
    if (o.mode == "prepare" && o.threads != std::vector<int>{1}) throw std::runtime_error("prepare uses Threads 1 only");
    if (o.corpus.empty()) o.corpus = o.out + "/mate-corpus.tsv";
    return o;
}

struct Budget {
    Clock::time_point start = Clock::now(), end;
    explicit Budget(int seconds) : end(start + std::chrono::seconds(seconds)) {}
    int left() const {
        return static_cast<int>(std::chrono::duration_cast<std::chrono::milliseconds>(end - Clock::now()).count());
    }
    int timeout(int requested) const { return std::max(1, std::min(requested, left() - 300)); }
    bool available() const { return left() > 600; }
    std::int64_t elapsed() const {
        return std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - start).count();
    }
};

void write_file(const std::string& path, const std::string& contents) {
    std::ofstream stream(path);
    if (!stream || !(stream << contents)) throw std::runtime_error("cannot write " + path);
}

struct Root {
    std::string id, kind, fen, lock_reference = "null", merged_reference = "null";
};

std::vector<Root> original_roots(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot read KRK roots " + path);
    std::vector<Root> roots;
    std::string fen;
    while (std::getline(input, fen)) {
        if (!fen.empty() && fen.back() == '\r') fen.pop_back();
        if (fen.empty() || fen[0] == '#') continue;
        forge::Board board;
        if (!board.set_fen(fen) || board.legal_moves().empty() || board.in_check(forge::opposite(board.side_to_move())))
            throw std::runtime_error("invalid supplied KRK root " + fen);
        roots.push_back({"KRK-" + padded(roots.size()), "KRK", fen});
    }
    if (roots.size() != 40) throw std::runtime_error("exactly 40 supplied KRK roots required");
    const std::string reproducer = "7k/8/3K4/8/8/8/8/5R2 w - - 0 1";
    if (std::none_of(roots.begin(), roots.end(), [&](const Root& r) { return r.fen == reproducer; }))
        throw std::runtime_error("required KRK reproducer missing");
    return roots;
}

void save_corpus(const std::string& path, const std::vector<Root>& roots) {
    std::ostringstream out;
    out << "# id\tkind\tfen\tlock_t1_reference_json\tmerged_t1_reference_json\n";
    for (const auto& r : roots)
        out << r.id << '\t' << r.kind << '\t' << r.fen << '\t' << r.lock_reference << '\t' << r.merged_reference << '\n';
    write_file(path, out.str());
}

std::vector<Root> load_corpus(const Options& o) {
    auto roots = original_roots(o.roots);
    std::ifstream input(o.corpus);
    std::string line;
    while (std::getline(input, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream row(line);
        Root r;
        if (!std::getline(row, r.id, '\t') || !std::getline(row, r.kind, '\t') || !std::getline(row, r.fen, '\t') ||
            !std::getline(row, r.lock_reference, '\t') || !std::getline(row, r.merged_reference))
            throw std::runtime_error("malformed corpus row");
        auto found = std::find_if(roots.begin(), roots.end(), [&](const Root& old) { return old.id == r.id; });
        if (found != roots.end()) {
            if (found->fen != r.fen) throw std::runtime_error("supplied KRK root changed in corpus");
            *found = r;
        } else roots.push_back(r);
    }
    return roots;
}

std::uint64_t mix(std::uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}

Root generated(std::uint64_t seed, std::size_t index, const std::string& kind, bool attacking_to_move) {
    std::uint64_t random = mix(seed ^ mix(index));
    auto next = [&]() { random = mix(random); return random; };
    for (int attempt = 0; attempt < 100000; ++attempt) {
        const bool black_attacker = (next() & 1U) != 0;
        const bool black_move = attacking_to_move ? black_attacker : ((next() & 1U) != 0);
        const int strong_king = next() % 64, weak_king = next() % 64, first = next() % 64, second = next() % 64;
        if (strong_king == weak_king || strong_king == first || weak_king == first ||
            forge::square_distance(strong_king, weak_king) <= 1) continue;
        if (kind == "KBBK" && (second == strong_king || second == weak_king || second == first ||
            ((forge::file_of(first) + forge::rank_of(first)) & 1) ==
            ((forge::file_of(second) + forge::rank_of(second)) & 1))) continue;
        std::array<char, 64> squares{};
        squares[strong_king] = black_attacker ? 'k' : 'K';
        squares[weak_king] = black_attacker ? 'K' : 'k';
        char piece = kind == "KRK" ? 'R' : kind == "KQK" ? 'Q' : 'B';
        squares[first] = black_attacker ? static_cast<char>(piece + ('a' - 'A')) : piece;
        if (kind == "KBBK") squares[second] = black_attacker ? 'b' : 'B';
        std::ostringstream fen;
        for (int rank = 7; rank >= 0; --rank) {
            int empty = 0;
            for (int file = 0; file < 8; ++file) {
                const char p = squares[rank * 8 + file];
                if (!p) ++empty;
                else { if (empty) fen << empty; empty = 0; fen << p; }
            }
            if (empty) fen << empty;
            if (rank) fen << '/';
        }
        fen << (black_move ? " b" : " w") << " - - 0 1";
        forge::Board board;
        if (!board.set_fen(fen.str()) || board.in_check(forge::opposite(board.side_to_move())) ||
            board.legal_moves().empty() || board.is_insufficient_material()) continue;
        return {kind + "-" + padded(index), kind, fen.str()};
    }
    throw std::runtime_error("deterministic legal-root generator exhausted");
}

std::vector<Root> cost_roots(std::uint64_t seed) {
    const std::array<std::string, 3> kinds{"KRK", "KQK", "KBBK"};
    std::vector<Root> roots;
    std::set<std::string> seen;
    for (std::size_t candidate = 0; roots.size() < 200; ++candidate) {
        auto root = generated(seed ^ 0x434f5354ULL, candidate, kinds[candidate % 3], false);
        if (!seen.insert(root.fen).second) continue;
        root.id = "cost-" + padded(roots.size());
        roots.push_back(std::move(root));
    }
    return roots;
}

struct Trial {
    UciResult result;
    bool completed = false, legal = false, pv_legal = true, pv_terminal_checkmate = false;
    bool budget_interrupted = false;
    bool sanitizer_report = false;
    std::string error, transcript, stderr_text;
};

std::string result_json(const Trial& t, int requested_depth) {
    std::ostringstream out;
    const auto& r = t.result;
    out << "{\"completed\":" << boolean(t.completed) << ",\"legal_bestmove\":" << boolean(t.legal)
        << ",\"move\":" << json_quote(r.move) << ",\"score_kind\":" << json_quote(r.score_kind)
        << ",\"score\":" << r.score << ",\"score_bound\":" << json_quote(r.score_bound)
        << ",\"positive_mate_score\":" << boolean(t.completed && r.positive_mate())
        << ",\"requested_depth\":" << requested_depth << ",\"completed_depth\":" << r.depth
        << ",\"reached_requested_depth\":" << boolean(t.completed && r.depth >= requested_depth)
        << ",\"early_mate_termination\":" << boolean(t.completed && r.depth < requested_depth && r.score_kind == "mate")
        << ",\"unfinished_depth\":" << boolean(t.completed && r.depth < requested_depth && r.score_kind != "mate")
        << ",\"nodes\":" << r.nodes << ",\"reported_ms\":" << r.reported_ms << ",\"wall_ms\":" << r.wall_ms
        << ",\"pv_legal\":" << boolean(t.pv_legal) << ",\"pv_terminal_checkmate\":" << boolean(t.pv_terminal_checkmate)
        << ",\"pv_is_mate_proof\":false,\"pv\":[";
    for (std::size_t i = 0; i < r.pv.size(); ++i) { if (i) out << ','; out << json_quote(r.pv[i]); }
    out << "],\"error\":" << json_quote(t.error) << ",\"stderr\":" << json_quote(t.stderr_text)
        << ",\"sanitizer_report\":" << boolean(t.sanitizer_report) << ",\"budget_interrupted\":" << boolean(t.budget_interrupted)
        << ",\"transcript\":" << json_quote(t.transcript) << '}';
    return out.str();
}

Trial run_trial(const Options& o, Budget& budget, const Root& root, const std::string& engine,
                int threads, const std::string& stem, std::unique_ptr<UciProcess>& process) {
    Trial t;
    t.transcript = o.out + "/" + stem + ".uci.txt";
    if (!budget.available()) { t.budget_interrupted = true; return t; }
    bool limited = false;
    const std::size_t stderr_begin = process ? process->stderr_output().size() : 0;
    try {
        if (!process) {
            const int ms = budget.timeout(o.timeout_ms);
            limited = ms < o.timeout_ms;
            process = std::make_unique<UciProcess>(engine, threads, ms);
        }
        const int legal_ms = budget.timeout(o.timeout_ms);
        limited = legal_ms < o.timeout_ms;
        const auto moves = process->legal_moves(root.fen, legal_ms);
        const int search_ms = budget.timeout(o.timeout_ms);
        limited = search_ms < o.timeout_ms;
        t.result = process->search(root.fen, o.depth, search_ms, true);
        t.completed = true;
        t.legal = std::find(moves.begin(), moves.end(), t.result.move) != moves.end();
        forge::Board pv;
        if (!pv.set_fen(root.fen)) throw std::runtime_error("invalid root in PV check");
        for (const auto& text : t.result.pv) {
            auto move = pv.parse_uci(text);
            if (!move || !pv.is_pseudo_legal(*move) || !pv.is_legal(*move)) { t.pv_legal = false; break; }
            forge::Undo undo;
            if (!pv.make_move(*move, undo)) { t.pv_legal = false; break; }
        }
        t.pv_terminal_checkmate = t.pv_legal && !t.result.pv.empty() && pv.in_check() && pv.legal_moves().empty();
    } catch (const std::exception& e) {
        t.error = e.what();
        t.budget_interrupted = limited && budget.left() < 1000;
    }
    if (process) {
        t.stderr_text = process->stderr_output().substr(stderr_begin);
        write_file(t.transcript, process->transcript());
    }
    else write_file(t.transcript, "Process creation failed: " + t.error + "\n");
    const std::string diagnostics = t.stderr_text + t.error;
    for (const char* marker : {"AddressSanitizer", "UndefinedBehaviorSanitizer", "ThreadSanitizer", "LeakSanitizer", "runtime error:"})
        if (diagnostics.find(marker) != std::string::npos) t.sanitizer_report = true;
    if (!t.completed) process.reset();
    return t;
}

struct Totals {
    std::size_t units = 0, trials = 0, faults = 0, incomplete = 0, selected = 0;
    std::uint64_t nodes = 0, reported_ms = 0;
    double wall_ms = 0.0;
    std::size_t at_depth = 0, early_mate = 0, unfinished_depth = 0;
};

void add_counts(Totals& into, const Totals& from) {
    into.units += from.units;
    into.trials += from.trials;
    into.faults += from.faults;
    into.nodes += from.nodes;
    into.reported_ms += from.reported_ms;
    into.wall_ms += from.wall_ms;
    into.at_depth += from.at_depth;
    into.early_mate += from.early_mate;
    into.unfinished_depth += from.unfinished_depth;
}

void emit_summary(const Options& o, const Budget& budget, const Totals& total,
                  const Totals& partial, std::size_t next, std::size_t available,
                  const std::map<std::string, Totals>& groups) {
    std::ostringstream out;
    out << "{\"mode\":" << json_quote(o.mode) << ",\"seed\":" << o.seed
        << ",\"offset\":" << o.offset << ",\"next_offset\":" << next << ",\"available_units\":" << available
        << ",\"completed_units\":" << total.units << ",\"trials\":" << total.trials << ",\"faults\":" << total.faults
        << ",\"incomplete_units\":" << total.incomplete << ",\"selected_generated\":" << total.selected
        << ",\"partial_trials_excluded\":" << partial.trials << ",\"partial_faults_excluded\":" << partial.faults
        << ",\"partial_nodes_excluded\":" << partial.nodes << ",\"partial_reported_ms_excluded\":" << partial.reported_ms
        << ",\"partial_wall_ms_excluded\":" << partial.wall_ms
        << ",\"elapsed_ms\":" << budget.elapsed() << ",\"budget_seconds\":" << o.seconds
        << ",\"corpus\":" << json_quote(o.corpus) << ",\"out\":" << json_quote(o.out)
        << ",\"selection\":" << json_quote(o.mode == "cost" ?
            "200 fixed-seed legal bare-king roots, no mate-score selection" :
            "40 supplied KRK retained; generated KQK/KBBK selected by lock T1 exact positive mate, not independent proof")
        << ",\"measurements_only_no_speed_conclusion\":true,\"groups\":{";
    bool first = true;
    for (const auto& [key, g] : groups) {
        if (!first) out << ',';
        first = false;
        out << json_quote(key) << ":{\"trials\":" << g.trials << ",\"faults\":" << g.faults
            << ",\"nodes\":" << g.nodes << ",\"reported_ms\":" << g.reported_ms << ",\"wall_ms\":" << g.wall_ms
            << ",\"at_requested_depth\":" << g.at_depth << ",\"early_mate_termination\":" << g.early_mate
            << ",\"unfinished_depth\":" << g.unfinished_depth << '}';
    }
    out << "}}";
    std::cout << "SUMMARY " << out.str() << std::endl;
    write_file(o.out + "/summary.json", out.str() + "\n");
}

int run(const Options& o) {
    std::filesystem::create_directories(o.out);
    if (std::filesystem::exists(o.out + "/summary.json")) throw std::runtime_error("use a fresh --out directory to preserve previous evidence");
    Budget budget(o.seconds);
    auto roots = o.mode == "cost" ? cost_roots(o.seed) : load_corpus(o);
    if (o.mode == "cost") save_corpus(o.out + "/cost-corpus.tsv", roots);
    else if (o.mode == "prepare") save_corpus(o.corpus, roots);
    std::ostringstream config;
    config << "{\"mode\":" << json_quote(o.mode) << ",\"merged\":" << json_quote(o.merged) << ",\"lock\":" << json_quote(o.lock)
        << ",\"seed\":" << o.seed << ",\"depth\":" << o.depth << ",\"trials_per_mate_group\":" << o.trials
        << ",\"Hash\":16,\"OwnBook\":false,\"new_options\":\"defaults\",\"fresh_hash_each_trial\":true"
        << ",\"ucinewgame_each_trial\":true,\"histories\":\"reset each trial via ucinewgame/isready\",\"threads\":[";
    for (std::size_t i = 0; i < o.threads.size(); ++i) { if (i) config << ','; config << o.threads[i]; }
    config << "],\"offset\":" << o.offset << ",\"limit\":" << o.limit << ",\"seconds\":" << o.seconds
        << ",\"timeout_ms\":" << o.timeout_ms << ",\"root_count\":" << roots.size() << '}';
    std::cout << "CONFIG " << config.str() << std::endl;
    write_file(o.out + "/config.json", config.str() + "\n");
    std::ofstream results(o.out + "/results.jsonl");
    if (!results) throw std::runtime_error("cannot open results.jsonl");
    Totals total, partial;
    std::map<std::string, Totals> groups;
    std::size_t next = o.offset;
    const std::size_t available = o.mode == "prepare" ? 100040 : roots.size() * 2 * o.threads.size();
    for (std::size_t done = 0; done < o.limit && next < available && budget.available(); ++done) {
        if (o.mode == "prepare") {
            Root root = next < 40 ? roots[next] : generated(o.seed, next - 40, ((next - 40) % 2 == 0) ? "KQK" : "KBBK", true);
            std::unique_ptr<UciProcess> lock_process, merged_process;
            Trial locked = run_trial(o, budget, root, o.lock, 1, "prepare-" + padded(next) + "-lock", lock_process);
            if (locked.budget_interrupted) { ++total.incomplete; break; }
            const bool selected = next < 40 || (locked.completed && locked.legal && locked.result.positive_mate() && locked.result.score_bound.empty());
            Trial merged;
            if (selected) merged = run_trial(o, budget, root, o.merged, 1, "prepare-" + padded(next) + "-merged", merged_process);
            if (selected && merged.budget_interrupted) { ++total.incomplete; break; }
            root.lock_reference = result_json(locked, o.depth);
            root.merged_reference = selected ? result_json(merged, o.depth) : "null";
            if (selected) {
                auto found = std::find_if(roots.begin(), roots.end(), [&](const Root& old) { return old.id == root.id; });
                if (found == roots.end()) roots.push_back(root); else *found = root;
                if (next >= 40) ++total.selected;
                save_corpus(o.corpus, roots);
            }
            std::string row = "{\"mode\":\"prepare\",\"unit\":" + std::to_string(next) + ",\"id\":" + json_quote(root.id) +
                ",\"kind\":" + json_quote(root.kind) + ",\"fen\":" + json_quote(root.fen) + ",\"selected\":" + boolean(selected) +
                ",\"lock_t1\":" + root.lock_reference + ",\"merged_t1\":" + root.merged_reference + "}";
            results << row << '\n'; results.flush(); std::cout << "RESULT " << row << std::endl;
            total.trials += selected ? 2 : 1;
            if (!locked.completed || !locked.legal || !locked.pv_legal || locked.sanitizer_report ||
                (selected && (!merged.completed || !merged.legal || !merged.pv_legal || merged.sanitizer_report))) ++total.faults;
            ++total.units; ++next;
            continue;
        }
        const std::size_t thread_index = next % o.threads.size();
        const std::size_t build = (next / o.threads.size()) % 2;
        const std::size_t root_index = next / (o.threads.size() * 2);
        const Root& root = roots.at(root_index);
        const std::string build_name = build ? "merged" : "lock";
        const std::string engine = build ? o.merged : o.lock;
        const int threads = o.threads[thread_index];
        const std::string stem = o.mode + "-" + padded(next) + "-" + root.id + "-" + build_name + "-t" + std::to_string(threads);
        std::unique_ptr<UciProcess> process;
        std::vector<std::string> trials;
        std::string interrupted_trial = "null";
        bool interrupted = false, faulty = false;
        const int count = o.mode == "mates" ? o.trials : 1;
        const std::string group_key = build_name + "-t" + std::to_string(threads) + "-" + root.kind;
        Totals unit;
        for (int trial = 0; trial < count; ++trial) {
            Trial t = run_trial(o, budget, root, engine, threads, stem + "-trial" + std::to_string(trial), process);
            if (t.budget_interrupted) {
                interrupted = true;
                interrupted_trial = result_json(t, o.depth);
                break;
            }
            const bool mate_miss = o.mode == "mates" && (!t.completed || !t.result.positive_mate() || !t.result.score_bound.empty());
            const bool unfinished_depth = t.completed && t.result.depth < o.depth && t.result.score_kind != "mate";
            const bool fault = !t.completed || !t.legal || !t.pv_legal || t.sanitizer_report || mate_miss || unfinished_depth;
            const std::string result = result_json(t, o.depth);
            trials.push_back(result);
            std::string row = "{\"mode\":" + json_quote(o.mode) + ",\"unit\":" + std::to_string(next) + ",\"id\":" + json_quote(root.id) +
                ",\"kind\":" + json_quote(root.kind) + ",\"fen\":" + json_quote(root.fen) + ",\"build\":" + json_quote(build_name) +
                ",\"threads\":" + std::to_string(threads) + ",\"trial\":" + std::to_string(trial) +
                ",\"summary_accounting\":\"only if entire unit completes\",\"mate_score_miss\":" + boolean(mate_miss) +
                ",\"fault\":" + boolean(fault) + ",\"result\":" + result + "}";
            results << row << '\n'; results.flush(); std::cout << "RESULT " << row << std::endl;
            ++unit.trials;
            if (fault) { faulty = true; ++unit.faults; }
            if (t.completed) {
                unit.nodes += t.result.nodes; unit.reported_ms += t.result.reported_ms; unit.wall_ms += t.result.wall_ms;
                if (t.result.depth >= o.depth) ++unit.at_depth;
                else if (t.result.score_kind == "mate") ++unit.early_mate;
                else ++unit.unfinished_depth;
            }
        }
        if (faulty || interrupted) {
            std::ostringstream fault;
            fault << "{\"status\":" << json_quote(interrupted ? "partial-rerun-full-group" : "pending-review")
                << ",\"mode\":" << json_quote(o.mode) << ",\"unit\":" << next << ",\"id\":" << json_quote(root.id)
                << ",\"fen\":" << json_quote(root.fen) << ",\"engine\":" << json_quote(engine) << ",\"build\":" << json_quote(build_name)
                << ",\"threads\":" << threads << ",\"Hash\":16,\"OwnBook\":false,\"depth\":" << o.depth
                << ",\"fresh_hash_each_trial\":true,\"ucinewgame_each_trial\":true,\"new_options\":\"defaults\",\"expected_trials\":" << count
                << ",\"completed_trial_records\":" << trials.size() << ",\"lock_t1_reference\":" << root.lock_reference
                << ",\"merged_t1_reference\":" << root.merged_reference << ",\"trials\":[";
            for (std::size_t i = 0; i < trials.size(); ++i) { if (i) fault << ','; fault << trials[i]; }
            fault << "],\"interrupted_trial\":" << interrupted_trial << "}\n";
            write_file(o.out + "/" + (interrupted ? "partial-" : "pending-") + stem + ".json", fault.str());
        }
        if (interrupted) { add_counts(partial, unit); ++total.incomplete; break; }
        unit.units = 1;
        add_counts(total, unit);
        add_counts(groups[group_key], unit);
        ++next;
    }
    emit_summary(o, budget, total, partial, next, available, groups);
    return 0; // Fault observations are in JSON; exit failure is reserved for a broken driver invocation.
}
} // namespace

int main(int argc, char** argv) {
    try { return run(options(argc, argv)); }
    catch (const std::exception& e) {
        std::cerr << "SUMMARY {\"driver_error\":" << json_quote(e.what()) << "}\n";
        return 2;
    }
}
