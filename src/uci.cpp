#include "forge/board.hpp"
#include "forge/book.hpp"
#include "forge/nnue.hpp"
#include "forge/nnue_v2.hpp"
#include "forge/search.hpp"
#include "forge/syzygy.hpp"
#include "forge/search_options.hpp"
#include "forge/uci_output.hpp"
#include "search/timeman.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <string_view>
#include <memory>
#include <optional>
#include <thread>
#include <utility>
#include <vector>

// Test hooks (the hidden DebugSearchDelayMs option) exist only in debug builds
// (no NDEBUG) and in test-only builds that pass FORGE_DEBUG_HOOKS=1; release
// builds (CMake Release, the box recipe) contain no trace of them.
#ifndef FORGE_DEBUG_HOOKS
#ifdef NDEBUG
#define FORGE_DEBUG_HOOKS 0
#else
#define FORGE_DEBUG_HOOKS 1
#endif
#endif

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#endif

namespace {

void apply_position(forge::Board& board, std::istringstream& input) {
    forge::Board candidate = board;
    std::string token;
    if (!(input >> token)) return;
    if (token == "startpos") {
        (void)candidate.set_fen(forge::Board::StandardStartFen);
    } else if (token == "fen") {
        std::string fen;
        for (int i = 0; i < 6 && input >> token; ++i) {
            if (!fen.empty()) fen += ' ';
            fen += token;
        }
        std::string error;
        if (!candidate.set_fen(fen, &error)) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
            return;
        }
    } else {
        return;
    }
    if (!(input >> token)) {
        board = candidate;
        return;
    }
    if (token != "moves") return;
    while (input >> token) {
        const auto move = candidate.parse_uci(token);
        if (!move.has_value()) {
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string illegal move " << token << std::endl; }
            return;
        }
        forge::Undo undo;
        (void)candidate.make_move(*move, undo);
    }
    board = candidate;
}

bool is_go_keyword(const std::string& token) {
    return token == "depth" || token == "nodes" || token == "movetime" || token == "movestogo" ||
           token == "infinite" || token == "wtime" || token == "btime" || token == "winc" ||
           token == "binc" || token == "mate" || token == "searchmoves" || token == "ponder";
}

forge::SearchLimits parse_limits(std::istringstream& input, forge::Board& board) {
    forge::SearchLimits limits;
    std::string token;
    std::vector<std::string> tokens;
    while (input >> token) tokens.push_back(token);
    const forge::Color side = board.side_to_move();
    for (std::size_t i = 0; i < tokens.size();) {
        token = tokens[i++];
        auto read_int = [&]() {
            int value = 0;
            if (i < tokens.size()) {
                const std::string& text = tokens[i++];
                const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
                if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) return 0;
            }
            return value;
        };
        if (token == "depth") limits.depth = std::clamp(read_int(), 1, 64);
        else if (token == "nodes") {
            if (i < tokens.size()) {
                const std::string& text = tokens[i++];
                std::uint64_t value = 0;
                const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
                if (result.ec == std::errc{} && result.ptr == text.data() + text.size()) {
                    limits.nodes = value;
                    limits.nodes_specified = true;
                }
            }
        }
        else if (token == "movetime") limits.movetime_ms = std::max(0, read_int());
        else if (token == "movestogo") limits.moves_to_go = std::max(1, read_int());
        else if (token == "mate") limits.mate_moves = std::clamp(read_int(), 0, 32);
        else if (token == "infinite") limits.infinite = true;
        else if (token == "ponder") limits.ponder = true;
        else if (token == "wtime") { const int value = std::max(0, read_int()); if (side == forge::White) limits.time_ms = value; }
        else if (token == "btime") { const int value = std::max(0, read_int()); if (side == forge::Black) limits.time_ms = value; }
        else if (token == "winc") { const int value = std::max(0, read_int()); if (side == forge::White) limits.increment_ms = value; }
        else if (token == "binc") { const int value = std::max(0, read_int()); if (side == forge::Black) limits.increment_ms = value; }
        else if (token == "searchmoves") {
            limits.search_moves_specified = true;
            while (i < tokens.size() && !is_go_keyword(tokens[i])) {
                const auto move = board.parse_uci(tokens[i++]);
                if (move.has_value()) limits.search_moves.push_back(*move);
            }
        }
    }
    return limits;
}

} // namespace

namespace {

// Ply number implied by the position's move counters (0 at the start position).
int game_ply(const forge::Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == forge::Black ? 1 : 0);
}

// HardDeadline (forge/search_options.hpp): state of one `go` shared by the
// search thread, its watchdog and the UCI loop.
struct SearchRun {
    std::mutex mutex;
    std::condition_variable cv;
    bool done = false;  // this go is over: its bestmove is out (or the UCI loop ended it)
    bool ponder_hit = false;
    std::chrono::steady_clock::time_point ponder_hit_time{};
    // Claimed by whoever sends this go's single bestmove (search thread or watchdog).
    std::atomic<bool> answered{false};
};

// HardDeadline control threads (the UCI input loop and the watchdog) wait almost
// all the time; at time-critical priority they wake on time even when the
// engine's search threads are starved of CPU (e.g. a niced engine sharing a core
// with other work). Heavy commands run at normal priority. Windows only: other
// systems need privileges to raise a thread's priority.
void set_control_priority(bool time_critical) {
#ifdef _WIN32
    (void)SetThreadPriority(GetCurrentThread(), time_critical ? THREAD_PRIORITY_TIME_CRITICAL : THREAD_PRIORITY_NORMAL);
#else
    (void)time_critical;
#endif
}

bool contains(const forge::MoveList& moves, forge::Move move) {
    return std::find(moves.begin(), moves.end(), move) != moves.end();
}

// The watchdog's answer, with the search's own fallbacks: the published
// best/ponder pair if it is a root candidate here (a legal move, inside
// `searchmoves` when given), else the first candidate, else "0000" (no legal
// move, or a searchmoves list without a legal move).
std::string forced_bestmove(const forge::Board& board, bool ponder_enabled, bool restricted,
                            const std::vector<forge::Move>& search_moves) {
    const auto [best, ponder] = forge::Searcher::published_moves();
    forge::MoveList candidates;
    for (const forge::Move move : board.legal_moves()) {
        if (!restricted || std::find(search_moves.begin(), search_moves.end(), move) != search_moves.end()) {
            candidates.push_back(move);
        }
    }
    if (candidates.empty()) return "bestmove 0000";
    if (best.is_none() || !contains(candidates, best)) return "bestmove " + forge::Board::move_to_uci(candidates.front());
    std::string line = "bestmove " + forge::Board::move_to_uci(best);
    if (ponder_enabled && !ponder.is_none()) {
        forge::Board after = board;
        forge::Undo undo;
        (void)after.make_move(best, undo);
        if (contains(after.legal_moves(), ponder)) line += " ponder " + forge::Board::move_to_uci(ponder);
    }
    return line;
}

// HardDeadline watchdog: one persistent thread, started when the option is set,
// that raises its own priority once (a thread created at search time would first
// have to be scheduled at normal priority, which a starved engine cannot count
// on) and then serves every clocked go: it sleeps until the go's deadline (hard
// limit + HardDeadline ms; ponder searches from ponderhit) and, if the search has
// not answered by then, stops it and sends the bestmove itself.
class DeadlineWatchdog {
public:
    struct Job {
        std::shared_ptr<SearchRun> run;
        forge::Board board;
        bool ponder = false;
        std::chrono::steady_clock::time_point origin{};
        std::chrono::milliseconds allowance{0};
        bool ponder_enabled = false;
        bool restricted = false;  // go searchmoves ...
        std::vector<forge::Move> search_moves;
    };

    explicit DeadlineWatchdog(forge::Searcher& searcher) : searcher_(searcher) {}
    ~DeadlineWatchdog() {
        {
            const std::lock_guard<std::mutex> lock(mutex_);
            quit_ = true;
        }
        cv_.notify_all();
        if (thread_.joinable()) thread_.join();
    }
    DeadlineWatchdog(const DeadlineWatchdog&) = delete;
    DeadlineWatchdog& operator=(const DeadlineWatchdog&) = delete;

    void start() {
        if (!thread_.joinable()) thread_ = std::thread([this] { loop(); });
    }

    void arm(Job job) {
        start();
        {
            const std::lock_guard<std::mutex> lock(mutex_);
            job_ = std::move(job);
        }
        cv_.notify_all();
    }

    // Call after the run is marked done: returns once the watchdog no longer
    // serves it, so a forced bestmove can never come after later output.
    void finish(const SearchRun* run) {
        std::unique_lock<std::mutex> lock(mutex_);
        if (job_ && job_->run.get() == run) job_.reset();
        cv_.wait(lock, [this, run] { return serving_ != run; });
    }

private:
    void loop() {
        set_control_priority(true);
        std::unique_lock<std::mutex> lock(mutex_);
        while (true) {
            cv_.wait(lock, [this] { return quit_ || job_.has_value(); });
            if (quit_) return;
            Job job = std::move(*job_);
            job_.reset();
            serving_ = job.run.get();
            lock.unlock();
            serve(job);
            lock.lock();
            serving_ = nullptr;
            cv_.notify_all();
        }
    }

    void serve(const Job& job) {
        SearchRun& run = *job.run;
        std::unique_lock<std::mutex> lock(run.mutex);
        auto origin = job.origin;
        if (job.ponder) {
            run.cv.wait(lock, [&run] { return run.done || run.ponder_hit; });
            if (!run.ponder_hit) return;
            origin = run.ponder_hit_time;
        }
        if (run.cv.wait_until(lock, origin + job.allowance, [&run] { return run.done; })) return;
        lock.unlock();
        if (run.answered.exchange(true)) return;  // the search thread is sending its bestmove
        searcher_.stop();
        const std::string line = forced_bestmove(job.board, job.ponder_enabled, job.restricted, job.search_moves);
        const auto late = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - origin).count();
        {
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "info string HardDeadline: no answer within " << job.allowance.count()
                      << " ms, bestmove sent at " << late << " ms" << std::endl;
            std::cout << line << std::endl;
        }
        lock.lock();
        run.done = true;
        lock.unlock();
        run.cv.notify_all();
    }

    forge::Searcher& searcher_;
    std::mutex mutex_;
    std::condition_variable cv_;
    std::optional<Job> job_;
    const SearchRun* serving_ = nullptr;
    bool quit_ = false;
    std::thread thread_;
};

} // namespace

int main() {
    forge::Board board;
    forge::Searcher searcher;
    int move_overhead_ms = 10;
    bool ponder_enabled = false;
    forge::book::Book book;
    book.load_embedded();
    bool own_book = forge::book::embedded_available();
    std::string book_file;
    int book_depth = 30;
    int book_variety = 30;
    std::uint64_t book_rng = static_cast<std::uint64_t>(
        std::chrono::steady_clock::now().time_since_epoch().count()) | 1ULL;
    bool ponder_search_active = false;
    std::thread worker;
    // HardDeadline state of the current go (see SearchRun / DeadlineWatchdog).
    std::shared_ptr<SearchRun> run;
    DeadlineWatchdog deadline_watchdog(searcher);
    std::mutex stop_mutex;
    std::condition_variable stop_cv;
    bool stop_requested = false;
    bool ponder_hit_received = false;
#if FORGE_DEBUG_HOOKS
    // Hidden test hook (not advertised): the search thread waits this long before
    // searching, which simulates a starved search thread for the HardDeadline tests.
    int debug_search_delay_ms = 0;
#endif
    auto stop_search = [&]() {
        {
            const std::lock_guard<std::mutex> lock(stop_mutex);
            stop_requested = true;
        }
        searcher.stop();
        stop_cv.notify_all();
        if (worker.joinable()) worker.join();
        if (run) {
            { const std::lock_guard<std::mutex> lock(run->mutex); run->done = true; }
            run->cv.notify_all();
            deadline_watchdog.finish(run.get());
        }
        ponder_search_active = false;
    };

    // HardDeadline: the input loop waits for commands at time-critical priority.
    bool control_high = false;
    auto control_priority = [&control_high](bool high) {
        if (high == control_high) return;
        set_control_priority(high);
        control_high = high;
    };

    // v2 networks (UCI NNUEFile / NNUEKingBuckets / NNUEOutputBuckets / NNUEThreats / NNUEPawnPairs / PureNnue;
    // fail-loud rule in forge/search_options.hpp): a requested v2 net that cannot be used is reported at once and,
    // if still unusable at the next isready, go or bench, reported again before the engine exits with status 2.
    // Never a silent fall-back to the compiled-in network. With no NNUE option set nothing here prints anything.
    constexpr int NnueV2ExitStatus = 2;
    int exit_status = 0;
    std::string nnue_file;         // NNUEFile ("" = none)
    std::string nnue_file_error;   // why nnue_file did not load ("" = it loaded)
    std::string nnue_v2_active;    // "active: ..." while a v2 net is in use, else ""
    bool nnue_v2_shown = false;    // the last state printed was a v2 one (request, error or active net)
    auto nnue_v2_changed = [&]() {
        std::string state;
        const bool active = forge::options::apply_nnue_v2(&state);
        const std::string problem = forge::options::nnue_v2_problem(nnue_file, nnue_file_error);
        const bool requested = !nnue_file.empty() || forge::options::nnue_king_buckets > 0 ||
                               forge::options::nnue_output_buckets > 0 || forge::options::nnue_threats != 0 ||
                               forge::options::nnue_pawn_pairs != 0 || forge::options::pure_nnue;
        if (!nnue_file_error.empty()) state += " (NNUEFile " + nnue_file + ": " + nnue_file_error + ")";
        {
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            if (!problem.empty()) std::cout << "info string ERROR NNUE v2: " << problem << std::endl;
            else if (active && state != nnue_v2_active) std::cout << "info string NNUE v2: " << state << std::endl;
            else if (!active && (requested || nnue_v2_shown)) std::cout << "info string NNUE v2: " << state << std::endl;
        }
        nnue_v2_active = active ? state : std::string();
        nnue_v2_shown = requested || active || !problem.empty();
        searcher.clear_hash();
    };
    // True (after printing the error) when a v2 request cannot be honoured.
    auto nnue_v2_unusable = [&]() {
        const std::string problem = forge::options::nnue_v2_problem(nnue_file, nnue_file_error);
        if (problem.empty()) return false;
        const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
        std::cout << "info string ERROR NNUE v2: " << problem << std::endl;
        return true;
    };

    std::string line;
    while (true) {
        control_priority(forge::options::hard_deadline_ms > 0);
        if (!std::getline(std::cin, line)) break;
        const auto command_start = std::chrono::steady_clock::now();
        std::istringstream input(line);
        std::string command;
        input >> command;
        if (command == "uci") {
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "id name Chess Engine Forge 6.4.24 candidate\n"
                         "id author OpenAI\n"
                         "option name Hash type spin default 32 min 1 max 2048\n"
                         "option name Threads type spin default 1 min 1 max 256\n"
                         "option name Move Overhead type spin default 10 min 0 max 1000\n"
                         "option name Ponder type check default false\n"
                         "option name OwnBook type check default " << (forge::book::embedded_available() ? "true" : "false") << "\n"
                         "option name Book File type string default <empty>\n"
                         "option name Book Depth type spin default 30 min 0 max 100\n"
                         "option name Book Variety type spin default 30 min 0 max 100\n";
            if (forge::nnue::available()) std::cout << "option name UseNNUE type check default true\n";
            // Search options added after AL1 s198; all default OFF (see forge/search_options.hpp).
            std::cout << "option name SmpExactNodes type check default false\n"
                         "option name SmpBestThread type check default false\n"
                         "option name LocklessTT type check default false\n";
            std::cout << "option name SyzygyPath type string default <empty>\n"
                         "option name SyzygyProbeDepth type spin default 1 min 1 max 10\n"
                         "option name Syzygy50MoveRule type check default true\n";
            std::cout << "option name CorrHistPlus type spin default 0 min 0 max 7\n";
            std::cout << "option name HardDeadline type spin default 0 min 0 max 1000\n";
            // v2 networks (forge/search_options.hpp): off unless NNUEKingBuckets or NNUEOutputBuckets > 0.
            std::cout << "option name NNUEFile type string default <empty>\n"
                         "option name NNUEKingBuckets type spin default 0 min 0 max 32\n"
                         "option name NNUEOutputBuckets type spin default 0 min 0 max 16\n";
            // O6: a v2 net with threat inputs (needs such a net in NNUEFile).
            std::cout << "option name NNUEThreats type spin default 0 min 0 max 1\n";
            // O7: a v2 net with pawn-pair inputs (needs such a net in NNUEFile).
            std::cout << "option name NNUEPawnPairs type spin default 0 min 0 max 1\n";
            // O4: the network alone, without the hand-crafted evaluation (needs a stand-alone v2 net).
            std::cout << "option name PureNnue type spin default 0 min 0 max 1\n";
            std::cout << "option name CorrMargins type spin default 0 min 0 max 1\n";
            std::cout << "option name CorrExt type spin default 0 min 0 max 1\n";
            std::cout << "option name CuckooRep type check default false\n";
#ifdef FORGE_EXPOSE_TUNABLES
            // Development builds advertise the search constants so match
            // runners can set them; release builds accept them silently.
            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                std::cout << "option name " << parameter.name << " type spin default " << *parameter.value
                          << " min " << parameter.minimum << " max " << parameter.maximum << "\n";
            }
#endif
#ifdef FORGE_S13_TT_CHILD_PREFETCH
            std::cout << "option name TtChildPrefetch type check default false\n";
#endif
            std::cout << "option name Clear Hash type button\n"
                         "uciok" << std::endl;
        } else if (command == "isready") {
            if (nnue_v2_unusable()) { exit_status = NnueV2ExitStatus; break; }
            {
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                if (!nnue_v2_active.empty()) std::cout << "info string NNUE v2: " << nnue_v2_active << '\n';
                std::cout << "readyok" << std::endl;
            }
        } else if (command == "ucinewgame") {
            control_priority(false);
            stop_search();
            searcher.clear();
            (void)board.set_fen(forge::Board::StandardStartFen);
        } else if (command == "setoption") {
            control_priority(false);  // Hash resize / clears / book loading can be heavy
            stop_search();
            std::string token;
            std::string name;
            std::string value_text;
            input >> token;
            if (token == "name") {
                while (input >> token && token != "value") {
                    if (!name.empty()) name += ' ';
                    name += token;
                }
                if (token == "value") input >> value_text;
            }
            bool handled_tunable = false;
            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                if (name != parameter.name) continue;
                handled_tunable = true;
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    *parameter.value = std::clamp(value, parameter.minimum, parameter.maximum);
                    forge::tune::refresh();
                }
            }
            if (handled_tunable) {
                // Unlisted development options; nothing else to do.
#ifdef FORGE_S13_TT_CHILD_PREFETCH
            } else if (name == "TtChildPrefetch") {
                if (value_text == "true" || value_text == "false") {
                    searcher.set_s13_tt_child_prefetch(value_text == "true");
                } else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option TtChildPrefetch" << std::endl;
                }
#endif
            } else if (name == "Clear Hash") {
                searcher.clear_hash();
            } else if (name == "Ponder") {
                if (value_text == "true") ponder_enabled = true;
                else if (value_text == "false") ponder_enabled = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option Ponder" << std::endl;
                }
            } else if (name == "OwnBook") {
                if (value_text == "true") own_book = true;
                else if (value_text == "false") own_book = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option OwnBook" << std::endl;
                }
            } else if (name == "Book File") {
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
                if (path.empty() || path == "<empty>") {
                    book_file.clear();
                    book.load_embedded();
                } else if (book.load_file(path)) {
                    book_file = path;
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string loaded book " << path << " with " << book.size() << " entries" << std::endl;
                } else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string cannot load book " << path << std::endl;
                }
            } else if (name == "Book Depth" || name == "Book Variety") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else if (name == "Book Depth") {
                    book_depth = std::clamp(value, 0, 100);
                } else {
                    book_variety = std::clamp(value, 0, 100);
                }
            } else if (name == "SmpExactNodes" || name == "SmpBestThread" || name == "LocklessTT") {
                bool& option = name == "SmpExactNodes"   ? forge::options::smp_exact_nodes
                               : name == "SmpBestThread" ? forge::options::smp_best_thread
                                                         : forge::options::lockless_tt;
                if (value_text == "true") option = true;
                else if (value_text == "false") option = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                }
                if (name == "LocklessTT" && value_text == "true") {
                    // Confirms the switch in engine logs (applied at the next search).
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string LocklessTT active" << std::endl;
                }
            } else if (name == "SyzygyPath") {
                // Folders separated by ';' (Windows) or ':' (elsewhere); may contain spaces.
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
                const forge::syzygy::LoadSummary summary = forge::syzygy::load(path);
                // Stored tablebase scores are encoded by whether tables are loaded (forge/syzygy.hpp).
                searcher.clear_hash();
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                if (path.empty() || path == "<empty>") {
                    std::cout << "info string Syzygy tablebases off" << std::endl;
                } else {
                    std::cout << "info string Syzygy: " << summary.wdl_tables << " WDL and " << summary.dtz_tables
                              << " DTZ tables, up to " << summary.max_pieces << " pieces";
                    if (summary.rejected > 0) std::cout << ", " << summary.rejected << " invalid files skipped";
                    std::cout << std::endl;
                }
            } else if (name == "SyzygyProbeDepth") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    forge::options::syzygy_probe_depth = std::clamp(value, 1, 10);
                }
            } else if (name == "Syzygy50MoveRule") {
                if (value_text == "true") forge::options::syzygy_50_move_rule = true;
                else if (value_text == "false") forge::options::syzygy_50_move_rule = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                }
            } else if (name == "CorrHistPlus") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    forge::options::corr_hist_plus = static_cast<std::uint8_t>(std::clamp(value, 0, 7));
                }
#if FORGE_DEBUG_HOOKS
            } else if (name == "DebugSearchDelayMs") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec == std::errc{} && parsed.ptr == value_text.data() + value_text.size()) {
                    debug_search_delay_ms = std::clamp(value, 0, 10000);
                }
#endif
            } else if (name == "HardDeadline") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option HardDeadline" << std::endl;
                } else {
                    forge::options::hard_deadline_ms = std::clamp(value, 0, 1000);
                    // Start (and prioritise) the watchdog now, not inside a starved search.
                    if (forge::options::hard_deadline_ms > 0) deadline_watchdog.start();
                }
            } else if (name == "CorrMargins") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    forge::options::corr_margins = static_cast<std::uint8_t>(std::clamp(value, 0, 1));
                }
            } else if (name == "CorrExt") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    forge::options::corr_ext = static_cast<std::uint8_t>(std::clamp(value, 0, 1));
                }
            } else if (name == "CuckooRep") {
                if (value_text == "true") forge::options::cuckoo_rep = true;
                else if (value_text == "false") forge::options::cuckoo_rep = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option CuckooRep" << std::endl;
                }
            } else if (name == "UseNNUE") {
                if (value_text == "true") forge::nnue::enabled = true;
                else if (value_text == "false") forge::nnue::enabled = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option UseNNUE" << std::endl;
                }
                // Silent unless a v2 network was requested (the default prints nothing new).
                nnue_v2_changed();
            } else if (name == "NNUEFile") {
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
                // "<empty>" (the advertised default) clears the file part of the request.
                nnue_file = path == "<empty>" ? std::string() : path;
                nnue_file_error.clear();
                if (nnue_file.empty()) {
                    forge::nnue::v2::unload();
                } else if (!forge::nnue::v2::load(nnue_file, &nnue_file_error)) {
                    if (nnue_file_error.empty()) nnue_file_error = "load failed";
                } else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string NNUE v2: loaded " << forge::nnue::v2::summary(*forge::nnue::v2::loaded())
                              << std::endl;
                }
                nnue_v2_changed();
            } else if (name == "NNUEKingBuckets" || name == "NNUEOutputBuckets") {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option " << name << std::endl;
                } else {
                    if (name == "NNUEKingBuckets") forge::options::nnue_king_buckets = std::clamp(value, 0, 32);
                    else forge::options::nnue_output_buckets = std::clamp(value, 0, 16);
                }
                nnue_v2_changed();
            } else if (name == "NNUEThreats") {   // O6: spin 0-1 (true / false accepted as well)
                if (value_text == "1" || value_text == "true") forge::options::nnue_threats = 1;
                else if (value_text == "0" || value_text == "false") forge::options::nnue_threats = 0;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option NNUEThreats" << std::endl;
                }
                nnue_v2_changed();
            } else if (name == "NNUEPawnPairs") {   // O7: spin 0-1 (true / false accepted as well)
                if (value_text == "1" || value_text == "true") forge::options::nnue_pawn_pairs = 1;
                else if (value_text == "0" || value_text == "false") forge::options::nnue_pawn_pairs = 0;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option NNUEPawnPairs" << std::endl;
                }
                nnue_v2_changed();
            } else if (name == "PureNnue") {   // O4: spin 0-1 (true / false accepted as well)
                if (value_text == "1" || value_text == "true") forge::options::pure_nnue = true;
                else if (value_text == "0" || value_text == "false") forge::options::pure_nnue = false;
                else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option PureNnue" << std::endl;
                }
                nnue_v2_changed();
            } else if (name == "Hash" || name == "Move Overhead" || name == "Threads") {
                int value = 0;
                const auto parsed = std::from_chars(
                    value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid value for option " << name << std::endl; }
                } else if (name == "Hash") {
                    searcher.resize_hash(static_cast<std::size_t>(std::clamp(value, 1, 2048)));
                } else if (name == "Threads") {
                    searcher.set_threads(std::clamp(value, 1, 256));
                } else {
                    move_overhead_ms = std::clamp(value, 0, 1000);
                }
            }
        } else if (command == "position") {
            stop_search();
            apply_position(board, input);
        } else if (command == "go") {
            stop_search();
            if (nnue_v2_unusable()) { exit_status = NnueV2ExitStatus; break; }
            std::string first;
            const auto position = input.tellg();
            input >> first;
            if (first == "perft") {
                control_priority(false);
                std::string depth_text;
                int depth = -1;
                if (!(input >> depth_text)) depth_text.clear();
                const auto parsed = std::from_chars(
                    depth_text.data(), depth_text.data() + depth_text.size(), depth);
                if (parsed.ec != std::errc{} || parsed.ptr != depth_text.data() + depth_text.size() ||
                    depth < 0 || depth > 10) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string perft depth must be an integer from 0 to 10" << std::endl; }
                    continue;
                }
                if (depth == 0) {
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "nodes 1" << std::endl; }
                    continue;
                }
                std::uint64_t total = 0;
                for (const forge::Move move : board.legal_moves()) {
                    forge::Undo undo;
                    (void)board.make_move(move, undo);
                    const std::uint64_t nodes = board.perft(depth - 1);
                    board.unmake_move(move, undo);
                    total += nodes;
                    { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << forge::Board::move_to_uci(move) << ": " << nodes << std::endl; }
                }
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "nodes " << total << std::endl; }
            } else {
                input.clear();
                input.seekg(position);
                forge::SearchLimits limits = parse_limits(input, board);
                limits.move_overhead_ms = move_overhead_ms;
                // Charge dispatch admission only to finite externally clocked searches.
                if (!limits.infinite && !limits.ponder &&
                    (limits.time_ms >= 0 || limits.movetime_ms >= 0)) limits.start_time = command_start;
                // Book moves apply to game play (clock or movetime searches), not
                // to analysis, pondering or restricted searches.
                const bool game_search = (limits.time_ms >= 0 || limits.movetime_ms >= 0) && !limits.infinite &&
                                         !limits.ponder && !limits.search_moves_specified && limits.mate_moves == 0;
                if (game_search && own_book && !book.empty() && game_ply(board) < book_depth) {
                    const forge::Move book_move = book.probe(board, book_variety, book_rng);
                    if (!book_move.is_none()) {
                        std::string prediction;
                        if (ponder_enabled) {
                            forge::Board reply_board = board;
                            forge::Undo undo;
                            (void)reply_board.make_move(book_move, undo);
                            const forge::Move reply = book.probe(reply_board, 0, book_rng);
                            if (!reply.is_none()) prediction = " ponder " + forge::Board::move_to_uci(reply);
                        }
                        const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                        std::cout << "info string book move " << forge::Board::move_to_uci(book_move) << std::endl;
                        std::cout << "bestmove " << forge::Board::move_to_uci(book_move) << prediction << std::endl;
                        continue;
                    }
                }
                const forge::Board search_board = board;
                {
                    const std::lock_guard<std::mutex> lock(stop_mutex);
                    stop_requested = false;
                    ponder_hit_received = false;
                }
                ponder_search_active = limits.ponder;
                searcher.reset_stop();
                run = std::make_shared<SearchRun>();
                const bool deadline_watch = forge::options::hard_deadline_ms > 0 && !limits.infinite &&
                                            (limits.time_ms >= 0 || limits.movetime_ms >= 0);
                if (deadline_watch) forge::Searcher::reset_published_moves();
                worker = std::thread([&searcher, &stop_mutex, &stop_cv, &stop_requested, &ponder_hit_received,
                                      search_board, limits, ponder_enabled, run
#if FORGE_DEBUG_HOOKS
                                      , delay = debug_search_delay_ms
#endif
                                      ]() mutable {
#if FORGE_DEBUG_HOOKS
                    if (delay > 0) std::this_thread::sleep_for(std::chrono::milliseconds(delay));
#endif
                    const forge::SearchInfo result = searcher.search(
                        search_board, limits, true, forge::Searcher::TTAccess::Exclusive);
                    if (limits.infinite || limits.ponder) {
                        std::unique_lock<std::mutex> lock(stop_mutex);
                        stop_cv.wait(lock, [&stop_requested, &ponder_hit_received, &limits] {
                            return stop_requested || (limits.ponder && ponder_hit_received);
                        });
                    }
                    const std::string best = result.best_move.from == result.best_move.to
                        ? "0000" : forge::Board::move_to_uci(result.best_move);
                    std::string prediction;
                    if (ponder_enabled && result.pv.size() > 1 &&
                        result.pv.front().from == result.best_move.from &&
                        result.pv.front().to == result.best_move.to &&
                        result.pv.front().promotion == result.best_move.promotion) {
                        prediction = " ponder " + forge::Board::move_to_uci(result.pv[1]);
                    }
                    // The HardDeadline watchdog may already have answered this go.
                    if (run->answered.exchange(true)) return;
                    {
                        const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                        std::cout << "bestmove " << best << prediction << std::endl;
                    }
                    {
                        const std::lock_guard<std::mutex> lock(run->mutex);
                        run->done = true;
                    }
                    run->cv.notify_all();
                });
                if (deadline_watch) {
                    std::int64_t soft_ms = 0;
                    std::int64_t hard_ms = 0;
                    bool managed = false;
                    forge::timeman::allocate(limits, soft_ms, hard_ms, managed);
                    deadline_watchdog.arm({run, search_board, limits.ponder, limits.start_time,
                                           std::chrono::milliseconds(hard_ms + forge::options::hard_deadline_ms),
                                           ponder_enabled, limits.search_moves_specified, limits.search_moves});
                }
            }
        } else if (command == "bench") {
            // Fixed-depth search over a small position set; prints a node
            // signature and speed for quick regression and performance checks.
            control_priority(false);
            stop_search();
            if (nnue_v2_unusable()) { exit_status = NnueV2ExitStatus; break; }
            int depth = 13;
            if (int parsed = 0; input >> parsed) depth = std::clamp(parsed, 1, 64);
            constexpr std::array<std::string_view, 8> fens{
                forge::Board::StandardStartFen,
                "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
                "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
                "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
                "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
                "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
                "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
            };
            std::uint64_t total_nodes = 0;
            const auto start = std::chrono::steady_clock::now();
            forge::Searcher bench_searcher(16);
#ifdef FORGE_S13_TT_CHILD_PREFETCH
            bench_searcher.set_s13_tt_child_prefetch(searcher.s13_tt_child_prefetch_enabled());
#endif
            for (const std::string_view fen : fens) {
                forge::Board bench_board;
                if (!bench_board.set_fen(fen)) continue;
                forge::SearchLimits limits;
                limits.depth = depth;
                bench_searcher.clear();
                total_nodes += bench_searcher.search(
                    bench_board, limits, false, forge::Searcher::TTAccess::Exclusive).nodes;
            }
            const auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - start).count();
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "info string bench depth " << depth << " nodes " << total_nodes << " time " << elapsed_ms
                      << " nps " << (elapsed_ms > 0 ? total_nodes * 1000U / static_cast<std::uint64_t>(elapsed_ms) : 0)
                      << std::endl;
        } else if (command == "ponderhit") {
            if (ponder_search_active) {
                searcher.ponderhit();
                {
                    const std::lock_guard<std::mutex> lock(stop_mutex);
                    ponder_hit_received = true;
                }
                stop_cv.notify_all();
                if (run) {
                    {
                        const std::lock_guard<std::mutex> lock(run->mutex);
                        run->ponder_hit = true;
                        run->ponder_hit_time = std::chrono::steady_clock::now();
                    }
                    run->cv.notify_all();
                }
                ponder_search_active = false;
            }
        } else if (command == "stop") {
            stop_search();
        } else if (command == "quit") {
            stop_search();
            break;
        }
    }
    stop_search();
    return exit_status;
}
