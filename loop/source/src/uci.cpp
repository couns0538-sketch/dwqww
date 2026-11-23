#include "forge/board.hpp"
#include "forge/book.hpp"
#include "forge/nnue.hpp"
#if FORGE_NNUE_V3
#include "forge/nnue_v3.hpp"
#endif
#include "forge/search.hpp"
#include "forge/uci.hpp"
#include "forge/uci_clock.hpp"
#include "forge/uci_output.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <limits>
#include <mutex>
#include <sstream>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

// forge/r12 repairs (2026-11-15), each with its own switch; 0 gives the code of r9.
// FORGE_FIX_GO_PARSE: in a `go` line a keyword is never taken as the value of the keyword before it, and a token
// that is not a complete integer leaves that ONE parameter out. A complete integer keeps r9's clamping (a negative
// clock is 0 = no time left, depth below 1 is 1, ...). When a limit was named but unusable and no usable limit is
// left on the line, the answer comes at once, as r9 gave it. r9 let `go wtime btime 50` lose the clock.
#ifndef FORGE_FIX_GO_PARSE
#define FORGE_FIX_GO_PARSE 1
#endif
// FORGE_FIX_ISREADY_PENDING: `isready` answers `readyok` while NNUEArch is on and no net file has been named yet
// (a program that sends its options in alphabetical order with `isready` between them sets NNUEArch first). r9
// ended the engine there. A search request in that state still stops, and a file that failed to load is still
// an error.
#ifndef FORGE_FIX_ISREADY_PENDING
#define FORGE_FIX_ISREADY_PENDING 1
#endif

namespace {

struct PositionCache {
    bool valid = false;
    bool startpos = false;
    std::string base_fen;
    std::vector<std::string> moves;
};

void apply_position(forge::Board& board, std::istringstream& input, PositionCache& cache) {
    std::string token;
    if (!(input >> token)) return;
    bool is_startpos = false;
    std::string fen;
    if (token == "startpos") {
        is_startpos = true;
    } else if (token == "fen") {
        for (int i = 0; i < 6 && input >> token; ++i) {
            if (!fen.empty()) fen += ' ';
            fen += token;
        }
    } else {
        return;
    }

    std::vector<std::string> move_tokens;
    if (input >> token) {
        // A token other than "moves" is not part of the FEN.
        while (token != "moves") {
            if (!(input >> token)) break;
        }
        if (token == "moves") {
            move_tokens.reserve(256);
            while (input >> token) move_tokens.push_back(std::move(token));
        }
    }

    std::size_t start_idx = 0;
    const bool same_root = cache.valid && cache.startpos == is_startpos &&
                           (is_startpos || cache.base_fen == fen);
    if (same_root && cache.moves.size() <= move_tokens.size() &&
        std::equal(cache.moves.begin(), cache.moves.end(), move_tokens.begin())) {
        start_idx = cache.moves.size();
    } else {
        if (is_startpos) {
            (void)board.set_fen(forge::Board::StandardStartFen);
        } else {
            forge::Board candidate;
            std::string error;
            if (!candidate.set_fen(fen, &error)) {
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string invalid FEN: " << error << std::endl; }
                return;
            }
            board = std::move(candidate);
        }
        cache.valid = true;
        cache.startpos = is_startpos;
        cache.base_fen = std::move(fen);
        cache.moves.clear();
    }

    for (std::size_t i = start_idx; i < move_tokens.size(); ++i) {
        const auto move = board.parse_uci(move_tokens[i]);
        if (!move.has_value()) {
            // The position and every legal move before this token still stand.
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string illegal move " << move_tokens[i] << std::endl; }
            return;
        }
        forge::Undo undo;
        (void)board.make_move(*move, undo);
        cache.moves.push_back(std::move(move_tokens[i]));
    }
}

bool is_go_keyword(const std::string& token) {
    return token == "depth" || token == "nodes" || token == "softnodes" || token == "movetime" ||
           token == "movestogo" || token == "infinite" || token == "wtime" || token == "btime" ||
           token == "winc" || token == "binc" || token == "mate" || token == "searchmoves" ||
           token == "ponder";
}

forge::SearchLimits parse_limits(std::istringstream& input, forge::Board& board) {
    forge::SearchLimits limits;
    std::string token;
    std::vector<std::string> tokens;
    while (input >> token) tokens.push_back(token);
    const forge::Color side = board.side_to_move();
#if FORGE_FIX_GO_PARSE
    bool limit_given = false;      // a usable limit of any kind is on the line
    bool limit_unusable = false;   // a limit was named, and its value was missing or not a number
    // An optional single sign and then digits only.
    const auto is_integer = [](const std::string& text) {
        std::size_t k = (!text.empty() && (text[0] == '+' || text[0] == '-')) ? 1 : 0;
        if (k >= text.size()) return false;
        for (; k < text.size(); ++k) {
            if (text[k] < '0' || text[k] > '9') return false;
        }
        return true;
    };
    for (std::size_t i = 0; i < tokens.size();) {
        token = tokens[i++];
        // The value of the keyword just read: the next token, unless it is missing or is itself a keyword (then
        // nothing is consumed). A token that is not a complete integer is consumed and gives no value.
        const auto take_integer = [&](std::string& text) {
            if (i >= tokens.size() || is_go_keyword(tokens[i])) return false;
            text = tokens[i++];
            return is_integer(text);
        };
        // An int, saturated at the ends of its range.
        const auto read_int = [&](int& out) {
            std::string text;
            if (!take_integer(text)) return false;
            long long wide = 0;
            const char* const first = text.data() + (text[0] == '+' ? 1 : 0);
            const auto result = std::from_chars(first, text.data() + text.size(), wide);
            if (result.ec == std::errc::result_out_of_range) {
                wide = text[0] == '-' ? std::numeric_limits<int>::min() : std::numeric_limits<int>::max();
            }
            out = static_cast<int>(std::clamp<long long>(wide, std::numeric_limits<int>::min(),
                                                         std::numeric_limits<int>::max()));
            return true;
        };
        // Clocks are 64-bit; parse_clock_ms clamps a complete integer to [0, kMaxClockMs].
        const auto read_clock = [&](std::int64_t& out) {
            std::string text;
            if (!take_integer(text)) return false;
            out = forge::parse_clock_ms(text);
            return true;
        };
        if (token == "depth") {
            int value = 0;
            if (read_int(value)) { limits.depth = std::clamp(value, 1, 64); limit_given = true; }
            else limit_unusable = true;
        }
        else if (token == "nodes" || token == "softnodes") {
            std::string text;
            if (take_integer(text)) {
                // A negative count is 0, and an explicit 0 is an immediate bounded answer in the search.
                std::uint64_t value = 0;
                if (text[0] != '-') {
                    const char* const first = text.data() + (text[0] == '+' ? 1 : 0);
                    const auto result = std::from_chars(first, text.data() + text.size(), value);
                    if (result.ec == std::errc::result_out_of_range) value = std::numeric_limits<std::uint64_t>::max();
                }
                limits.nodes = value;
                limits.nodes_specified = true;
                if (token == "softnodes") limits.soft_nodes = true;
                limit_given = true;
            } else {
                limit_unusable = true;
            }
        }
        else if (token == "movetime") {
            std::int64_t value = 0;
            if (read_clock(value)) { limits.movetime_ms = value; limit_given = true; }
            else limit_unusable = true;
        }
        else if (token == "movestogo") { int value = 0; if (read_int(value)) limits.moves_to_go = std::max(1, value); }
        else if (token == "mate") {
            int value = 0;
            if (read_int(value)) {
                limits.mate_moves = std::clamp(value, 0, 32);
                if (limits.mate_moves > 0) limit_given = true;
            } else {
                limit_unusable = true;
            }
        }
        else if (token == "infinite") { limits.infinite = true; limit_given = true; }
        else if (token == "ponder") limits.ponder = true;
        else if (token == "wtime" || token == "btime") {
            const bool mine = (token == "wtime") == (side == forge::White);
            std::int64_t value = 0;
            if (read_clock(value)) {
                if (mine) { limits.time_ms = value; limit_given = true; }
            } else if (mine) {
                limit_unusable = true;
            }
        }
        else if (token == "winc" || token == "binc") {
            const bool mine = (token == "winc") == (side == forge::White);
            std::int64_t value = 0;
            if (read_clock(value) && mine) limits.increment_ms = value;
        }
        else if (token == "searchmoves") {
            limits.search_moves_specified = true;
            while (i < tokens.size() && !is_go_keyword(tokens[i])) {
                const auto move = board.parse_uci(tokens[i++]);
                if (move.has_value()) limits.search_moves.push_back(*move);
            }
        }
    }
    // A limit was named but could not be read, and nothing else on the line limits the search: answer at once
    // (r9 did, through a value of 0) instead of searching without a limit.
    if (limit_unusable && !limit_given) limits.movetime_ms = 0;
#else
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
        // Clocks are 64-bit. A 32-bit parse turns 3000000000 into 0, and the
        // search then stops at once.
        auto read_clock = [&]() -> std::int64_t {
            if (i >= tokens.size()) return 0;
            return forge::parse_clock_ms(tokens[i++]);
        };
        if (token == "depth") limits.depth = std::clamp(read_int(), 1, 64);
        else if (token == "nodes" || token == "softnodes") {
            if (i < tokens.size()) {
                const std::string& text = tokens[i++];
                std::uint64_t value = 0;
                const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
                if (result.ec == std::errc{} && result.ptr == text.data() + text.size()) {
                    limits.nodes = value;
                    limits.nodes_specified = true;
                    if (token == "softnodes") limits.soft_nodes = true;
                }
            }
        }
        else if (token == "movetime") limits.movetime_ms = read_clock();
        else if (token == "movestogo") limits.moves_to_go = std::max(1, read_int());
        else if (token == "mate") limits.mate_moves = std::clamp(read_int(), 0, 32);
        else if (token == "infinite") limits.infinite = true;
        else if (token == "ponder") limits.ponder = true;
        else if (token == "wtime") { const std::int64_t value = read_clock(); if (side == forge::White) limits.time_ms = value; }
        else if (token == "btime") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.time_ms = value; }
        else if (token == "winc") { const std::int64_t value = read_clock(); if (side == forge::White) limits.increment_ms = value; }
        else if (token == "binc") { const std::int64_t value = read_clock(); if (side == forge::Black) limits.increment_ms = value; }
        else if (token == "searchmoves") {
            limits.search_moves_specified = true;
            while (i < tokens.size() && !is_go_keyword(tokens[i])) {
                const auto move = board.parse_uci(tokens[i++]);
                if (move.has_value()) limits.search_moves.push_back(*move);
            }
        }
    }
#endif
    return limits;
}

} // namespace

namespace {

// Ply number implied by the position's move counters (0 at the start position).
int game_ply(const forge::Board& board) {
    return 2 * (board.fullmove_number() - 1) + (board.side_to_move() == forge::Black ? 1 : 0);
}

struct SgConfig {
    std::uint64_t soft_nodes = 2000;
    int eval_limit = 2000;
    int max_ply = 300;
    int write_min_ply = 8;
    int draw_ply = 80;
    int draw_score = 5;
    int draw_count = 8;
};

struct SgState {
    bool legal = false;
    bool check = false;
    bool material = false;
    int clock = 0;
    bool rep3 = false;
};

[[nodiscard]] bool sg_is_ws(char c) noexcept {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\v' || c == '\f';
}

[[nodiscard]] std::string_view sg_next_token(std::string_view& sv) noexcept {
    std::size_t i = 0;
    while (i < sv.size() && sg_is_ws(sv[i])) ++i;
    sv.remove_prefix(i);
    if (sv.empty()) return {};
    std::size_t j = 0;
    while (j < sv.size() && !sg_is_ws(sv[j])) ++j;
    const std::string_view tok = sv.substr(0, j);
    sv.remove_prefix(j);
    return tok;
}

[[nodiscard]] bool sg_is_digits(std::string_view tok) noexcept {
    if (tok.empty()) return false;
    for (const char c : tok) {
        if (c < '0' || c > '9') return false;
    }
    return true;
}

[[nodiscard]] bool sg_parse_whole_int(std::string_view tok, int& out) noexcept {
    if (!sg_is_digits(tok)) return false;
    int val = 0;
    const auto res = std::from_chars(tok.data(), tok.data() + tok.size(), val);
    if (res.ptr != tok.data() + tok.size() || res.ec != std::errc{} || val < 0) return false;
    out = val;
    return true;
}

[[nodiscard]] bool sg_parse_whole_u64(std::string_view tok, std::uint64_t& out) noexcept {
    if (!sg_is_digits(tok)) return false;
    std::uint64_t val = 0;
    const auto res = std::from_chars(tok.data(), tok.data() + tok.size(), val);
    if (res.ptr != tok.data() + tok.size() || res.ec != std::errc{}) return false;
    out = val;
    return true;
}

[[nodiscard]] bool parse_selfgame_config(std::string_view line, SgConfig& out_cfg,
                                         std::string_view& bad_word) noexcept {
    SgConfig cfg;
    unsigned seen_mask = 0U;
    (void)sg_next_token(line);
    for (;;) {
        const std::string_view key = sg_next_token(line);
        if (key.empty()) break;
        int slot = -1;
        if (key == "softnodes") {
            slot = 0;
        } else if (key == "evallimit") {
            slot = 1;
        } else if (key == "maxply") {
            slot = 2;
        } else if (key == "writeminply") {
            slot = 3;
        } else if (key == "drawply") {
            slot = 4;
        } else if (key == "drawscore") {
            slot = 5;
        } else if (key == "drawcount") {
            slot = 6;
        }
        if (slot < 0 || (seen_mask & (1U << slot)) != 0U) {
            bad_word = key;
            return false;
        }
        seen_mask |= (1U << slot);
        const std::string_view val = sg_next_token(line);
        if (val.empty()) {
            bad_word = key;
            return false;
        }
        bool ok = false;
        if (slot == 0) {
            ok = sg_parse_whole_u64(val, cfg.soft_nodes);
        } else {
            int parsed = 0;
            ok = sg_parse_whole_int(val, parsed);
            if (ok) {
                if (slot == 1) cfg.eval_limit = parsed;
                else if (slot == 2) cfg.max_ply = parsed;
                else if (slot == 3) cfg.write_min_ply = parsed;
                else if (slot == 4) cfg.draw_ply = parsed;
                else if (slot == 5) cfg.draw_score = parsed;
                else if (slot == 6) cfg.draw_count = parsed;
            }
        }
        if (!ok) {
            bad_word = val;
            return false;
        }
    }
    out_cfg = cfg;
    return true;
}

[[nodiscard]] SgState evaluate_sg_state(const forge::Board& board) {
    SgState st;
    st.legal = board.has_legal_move();
    st.check = board.in_check();
    st.material = board.sg_insufficient_material();
    st.clock = board.halfmove_clock();
    st.rep3 = board.is_repetition();
    return st;
}

void emit_sgstate(const forge::Board& board) {
    const SgState st = evaluate_sg_state(board);
    std::string out = "sgstate legal ";
    out += st.legal ? '1' : '0';
    out += " check ";
    out += st.check ? '1' : '0';
    out += " material ";
    out += st.material ? '1' : '0';
    out += " clock ";
    out += std::to_string(st.clock);
    out += " rep3 ";
    out += st.rep3 ? '1' : '0';
    out += " fen ";
    out += board.sg_fen();
    out += '\n';
    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
    std::cout.write(out.data(), static_cast<std::streamsize>(out.size()));
    std::cout.flush();
}

void run_selfgame(forge::Board& board, forge::Searcher& searcher, int move_overhead_ms, int multipv,
                  const SgConfig& cfg) {
    struct SgRecord {
        int ply = 0;
        int score = 0;
        std::string move;
        std::string fen;
    };

    int ply = static_cast<int>(board.history_size() > 0 ? board.history_size() - 1 : 0);
    int run = 0;
    std::uint64_t searches = 0;
    std::uint64_t total_nodes = 0;
    std::vector<SgRecord> records;
    records.reserve(256);
    std::vector<std::string> loop_moves;
    loop_moves.reserve(256);

    int end_result = 0;
    const char* end_reason = "plylimit";

    for (;;) {
        const SgState st = evaluate_sg_state(board);
        if (!st.legal) {
            if (!st.check) {
                end_result = 0;
                end_reason = "stalemate";
            } else {
                end_result = (board.side_to_move() == forge::White) ? -1 : 1;
                end_reason = "mate";
            }
            break;
        }

        const bool rule_draw = st.material || st.clock >= 100 || st.rep3;
        if (rule_draw || ply >= cfg.max_ply) {
            end_result = 0;
            end_reason = rule_draw ? "rule" : "plylimit";
            break;
        }

        forge::SearchLimits limits;
        limits.nodes = cfg.soft_nodes;
        limits.nodes_specified = true;
        limits.soft_nodes = true;
        limits.move_overhead_ms = move_overhead_ms;
        limits.multipv = multipv;
        searcher.reset_stop();
        const forge::SearchInfo info = searcher.search(
            board, limits, false, forge::Searcher::TTAccess::Exclusive);
        ++searches;
        total_nodes += info.nodes;

        if (info.depth <= 0) {
            std::string err = "sgerror noscore ply ";
            err += std::to_string(ply);
            err += " searches ";
            err += std::to_string(searches);
            err += " nodes ";
            err += std::to_string(total_nodes);
            err += " fen ";
            err += board.sg_fen();
            err += '\n';
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout.write(err.data(), static_cast<std::streamsize>(err.size()));
            std::cout.flush();
            return;
        }

        const bool white_turn = (board.side_to_move() == forge::White);
        if (forge::is_mate_score(info.score)) {
            const std::int64_t abs_sc = info.score < 0
                ? -static_cast<std::int64_t>(info.score)
                : static_cast<std::int64_t>(info.score);
            const int distance = static_cast<int>(forge::MateValue - abs_sc);
            const int mate_x = (info.score > 0) ? ((distance + 1) / 2) : -((distance + 1) / 2);
            end_result = (white_turn == (mate_x > 0)) ? 1 : -1;
            end_reason = "matescore";
            break;
        }

        const int x_val = info.score;
        const std::int64_t abs_x = x_val < 0
            ? -static_cast<std::int64_t>(x_val)
            : static_cast<std::int64_t>(x_val);
        if (abs_x >= static_cast<std::int64_t>(cfg.eval_limit)) {
            end_result = (white_turn == (x_val > 0)) ? 1 : -1;
            end_reason = "evallimit";
            break;
        }

        const std::string best_uci = info.best_move.is_none()
            ? "0000"
            : forge::Board::move_to_uci(info.best_move);
        if (ply >= cfg.write_min_ply) {
            records.push_back(SgRecord{ply, x_val, best_uci, board.sg_fen()});
        }

        if (ply >= cfg.draw_ply && abs_x <= static_cast<std::int64_t>(cfg.draw_score)) {
            ++run;
            if (run >= cfg.draw_count) {
                end_result = 0;
                end_reason = "drawadj";
                break;
            }
        } else {
            run = 0;
        }

        const auto parsed_move = board.parse_uci(best_uci);
        if (!parsed_move.has_value()) {
            std::string err = "sgerror nomove ply ";
            err += std::to_string(ply);
            err += " searches ";
            err += std::to_string(searches);
            err += " nodes ";
            err += std::to_string(total_nodes);
            err += " fen ";
            err += board.sg_fen();
            err += '\n';
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout.write(err.data(), static_cast<std::streamsize>(err.size()));
            std::cout.flush();
            return;
        }
        forge::Undo undo;
        (void)board.make_move(*parsed_move, undo);
        loop_moves.push_back(best_uci);
        ++ply;
    }

    std::string out;
    out.reserve(records.size() * 96U + loop_moves.size() * 6U + 256U);
    for (const SgRecord& rec : records) {
        out += "sg ";
        out += std::to_string(rec.ply);
        out += ' ';
        out += std::to_string(rec.score);
        out += ' ';
        out += rec.move;
        out += ' ';
        out += rec.fen;
        out += '\n';
    }
    out += "sgend result ";
    out += std::to_string(end_result);
    out += " reason ";
    out += end_reason;
    out += " plies ";
    out += std::to_string(ply);
    out += " run ";
    out += std::to_string(run);
    out += " searches ";
    out += std::to_string(searches);
    out += " nodes ";
    out += std::to_string(total_nodes);
    out += " fen ";
    out += board.sg_fen();
    out += " moves";
    for (const std::string& mv : loop_moves) {
        out += ' ';
        out += mv;
    }
    out += '\n';
    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
    std::cout.write(out.data(), static_cast<std::streamsize>(out.size()));
    std::cout.flush();
}

} // namespace

namespace forge {

int uci_loop(std::istream& in) {
    forge::Board board;
    forge::Searcher searcher;
    int move_overhead_ms = 10;
    int multipv = 1;
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
    PositionCache pos_cache;
    pos_cache.valid = true;
    pos_cache.startpos = true;

    struct SearchTask {
        forge::Board board;
        forge::SearchLimits limits;
        bool ponder_enabled = false;
    };
    std::mutex stop_mutex;
    std::condition_variable stop_cv;
    std::condition_variable work_cv;
    std::condition_variable done_cv;
    bool stop_requested = false;
    bool ponder_hit_received = false;
    bool has_task = false;
    bool worker_busy = false;
    bool worker_quit = false;
    SearchTask pending_task;

    std::thread worker([&]() {
        for (;;) {
            SearchTask task;
            {
                std::unique_lock<std::mutex> lock(stop_mutex);
                work_cv.wait(lock, [&] { return has_task || worker_quit; });
                if (worker_quit && !has_task) break;
                task = std::move(pending_task);
                has_task = false;
            }
            const forge::SearchInfo result = searcher.search(
                std::move(task.board), task.limits, true, forge::Searcher::TTAccess::Exclusive);
            if (task.limits.infinite || task.limits.ponder) {
                std::unique_lock<std::mutex> lock(stop_mutex);
                stop_cv.wait(lock, [&] {
                    return stop_requested || (task.limits.ponder && ponder_hit_received);
                });
            }
            const std::string best = result.best_move.from == result.best_move.to
                ? "0000" : forge::Board::move_to_uci(result.best_move);
            std::string prediction;
            if (task.ponder_enabled && result.pv.size() > 1 &&
                result.pv.front().from == result.best_move.from &&
                result.pv.front().to == result.best_move.to &&
                result.pv.front().promotion == result.best_move.promotion) {
                prediction = " ponder " + forge::Board::move_to_uci(result.pv[1]);
            }
            {
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                std::cout << "bestmove " << best << prediction << std::endl;
            }
            {
                const std::lock_guard<std::mutex> lock(stop_mutex);
                worker_busy = false;
            }
            done_cv.notify_all();
        }
    });

    auto stop_search = [&]() {
        {
            std::unique_lock<std::mutex> lock(stop_mutex);
            if (!worker_busy) {
                ponder_search_active = false;
                return;
            }
            stop_requested = true;
        }
        searcher.stop();
        stop_cv.notify_all();
        {
            std::unique_lock<std::mutex> lock(stop_mutex);
            done_cv.wait(lock, [&] { return !worker_busy; });
        }
        ponder_search_active = false;
    };

    struct WorkerShutdownGuard {
        decltype(stop_search)& stop_fn;
        std::mutex& mtx;
        std::condition_variable& cv;
        bool& quit_flag;
        std::thread& thr;
        ~WorkerShutdownGuard() {
            stop_fn();
            {
                const std::lock_guard<std::mutex> lock(mtx);
                quit_flag = true;
            }
            cv.notify_all();
            if (thr.joinable()) thr.join();
        }
    } worker_guard{stop_search, stop_mutex, work_cv, worker_quit, worker};

    std::string line;
    while (std::getline(in, line)) {
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
                         "option name MultiPV type spin default 1 min 1 max 8\n"
                         "option name Move Overhead type spin default 10 min 0 max 1000\n"
                         "option name Ponder type check default false\n"
                         "option name OwnBook type check default " << (forge::book::embedded_available() ? "true" : "false") << "\n"
                         "option name Book File type string default <empty>\n"
                         "option name Book Depth type spin default 30 min 0 max 100\n"
                         "option name Book Variety type spin default 30 min 0 max 100\n";
            if (forge::nnue::available()) {
                std::cout << "option name UseNNUE type check default true\n"
                             "option name NnueFile type string default <empty>\n";
#if FORGE_NNUE_V3
                std::cout << "option name NNUEArch type check default false\n"
                             "option name NNUEArchFile type string default <empty>\n";
#endif
            }
            std::cout << "option name ContHist4PlyRead type check default false\n"
                         "option name NonPawnCorrection type check default false\n"
                         "option name LmrDeeperShallower type check default false\n"
                         "option name EvalRule50Damp type check default false\n"
                         "option name ThreatHistory type check default false\n"
                         "option name LmrSignedCorrection type check default false\n"
                         "option name LmrLateParentRelief type check default false\n"
                         "option name HindsightDepth type check default false\n"
                         "option name NullThreatVerify type check default false\n"
                         "option name NullSeeVeto type check default false\n"
                         "option name AspCappedReopen type check default false\n"
                         "option name AspArmLate type check default false\n"
                         "option name EvasionOrdering type check default false\n"
                         "option name DeadMaterial type check default false\n"
                         "option name QuietExtinction type check default false\n"
                         "option name DrawJitter type spin default 0 min 0 max " << forge::DrawJitterMax << "\n"
                         "option name TmFinishIteration type check default false\n"
                         "option name TmNodeShare type check default false\n"
                         "option name SoundMatePruning type check default false\n"
                         // B4 bundle (forge/r9): all four default off = r7's search.
                         "option name CuckooRep type check default false\n"
                         "option name HistRework type spin default 0 min 0 max 3\n"
                         "option name TtPruneV2 type check default false\n"
                         "option name CorrHistV2 type check default false\n";
#if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
            std::cout << "option name MateAlphaGuard type check default false\n";
#endif
#ifdef FORGE_EXPOSE_TUNABLES
            // Development builds advertise the search constants so match
            // runners can set them. Builds without this macro still accept them.
            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                std::cout << "option name " << parameter.name << " type spin default " << *parameter.value
                          << " min " << parameter.minimum << " max " << parameter.maximum << "\n";
            }
#endif
            std::cout << "option name Clear Hash type button\n"
                         "uciok" << std::endl;
        } else if (command == "isready") {
#if FORGE_NNUE_V3
#if FORGE_FIX_ISREADY_PENDING
            if (forge::nnue::v3::pending()) {
                // An unfinished configuration, not an error: say so and answer below.
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                std::cout << "info string NNUE v3: NNUEArch is on and no network is loaded yet (set NNUEArchFile)" << std::endl;
            } else
#endif
            if (const std::string v3_problem = forge::nnue::v3::problem(); !v3_problem.empty()) {
                // Fail-loud rule: a requested v3 net that cannot evaluate never falls back silently.
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string ERROR NNUE v3: " << v3_problem << std::endl; }
                stop_search();
                return 2;
            }
#endif
            { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "readyok" << std::endl; }
        } else if (command == "ucinewgame") {
            stop_search();
            searcher.clear();
            (void)board.set_fen(forge::Board::StandardStartFen);
            pos_cache.valid = true;
            pos_cache.startpos = true;
            pos_cache.base_fen.clear();
            pos_cache.moves.clear();
        } else if (command == "setoption") {
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
            auto note_invalid = [&]() {
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                std::cout << "info string invalid value for option " << name << std::endl;
            };
            // A non-integer leaves the stored value unchanged. An integer outside
            // the advertised range is reported and still clamped, as this lock
            // already did without a message.
            auto apply_spin = [&](int minimum, int maximum, auto&& assign) {
                int value = 0;
                const auto parsed = std::from_chars(value_text.data(), value_text.data() + value_text.size(), value);
                if (parsed.ec != std::errc{} || parsed.ptr != value_text.data() + value_text.size()) {
                    note_invalid();
                    return;
                }
                if (value < minimum || value > maximum) note_invalid();
                assign(std::clamp(value, minimum, maximum));
            };
            bool handled_tunable = false;
            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                if (name != parameter.name) continue;
                handled_tunable = true;
                apply_spin(parameter.minimum, parameter.maximum, [&](int clamped) {
                    *parameter.value = clamped;
                    forge::tune::refresh();
                });
            }
            if (handled_tunable) {
                // Unlisted development options; nothing else to do.
            } else if (name == "Clear Hash") {
                if (value_text.empty()) searcher.clear_hash();
                else note_invalid();
            } else if (name == "Ponder") {
                if (value_text == "true") ponder_enabled = true;
                else if (value_text == "false") ponder_enabled = false;
                else note_invalid();
            } else if (name == "OwnBook") {
                if (value_text == "true") own_book = true;
                else if (value_text == "false") own_book = false;
                else note_invalid();
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
                apply_spin(0, 100, [&](int clamped) {
                    if (name == "Book Depth") book_depth = clamped;
                    else book_variety = clamped;
                });
            } else if (name == "NnueFile") {
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
                std::string error;
                if (!forge::nnue::load_file(path, error)) {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string " << error << std::endl;
                } else {
                    searcher.clear_hash();
                    if (!path.empty() && path != "<empty>") {
                        const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                        std::cout << "info string loaded nnue " << path << std::endl;
                    }
                }
#if FORGE_NNUE_V3
            } else if (name == "NNUEArch") {
                stop_search();
                if (value_text == "true") {
                    forge::nnue::v3::requested = true;
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    if (const std::string v3_problem = forge::nnue::v3::problem(); !v3_problem.empty()) {
                        std::cout << "info string ERROR NNUE v3: " << v3_problem << std::endl;
                    } else {
                        std::cout << "info string NNUE v3 active: " << forge::nnue::v3::describe(*forge::nnue::v3::loaded()) << std::endl;
                    }
                } else if (value_text == "false") {
                    forge::nnue::v3::requested = false;
                } else {
                    note_invalid();
                }
                searcher.clear_hash();
            } else if (name == "NNUEArchFile") {
                stop_search();
                std::string rest;
                std::getline(input, rest);
                std::string path = value_text + rest;
                while (!path.empty() && (path.back() == ' ' || path.back() == '\r')) path.pop_back();
                {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    if (path.empty() || path == "<empty>") {
                        forge::nnue::v3::unload();
                        forge::nnue::v3::set_problem("");
                        std::cout << "info string NNUE v3: no network loaded" << std::endl;
                    } else if (std::string load_error; !forge::nnue::v3::load(path, &load_error)) {
                        forge::nnue::v3::set_problem(load_error);
                        std::cout << "info string ERROR NNUE v3: " << load_error << std::endl;
                    } else if (forge::nnue::v3::loaded()->residual) {
                        // forge/r7 carries the stand-alone path only; a residual v3 net is refused, not half-used.
                        const std::string refused = path + ": a residual v3 net is not supported by this build";
                        forge::nnue::v3::unload();
                        forge::nnue::v3::set_problem(refused);
                        std::cout << "info string ERROR NNUE v3: " << refused << std::endl;
                    } else {
                        forge::nnue::v3::set_problem("");
                        std::cout << "info string NNUE v3 loaded: " << forge::nnue::v3::describe(*forge::nnue::v3::loaded()) << std::endl;
                    }
                }
                searcher.clear_hash();
#endif
            } else if (name == "UseNNUE") {
                if (value_text == "true" || value_text == "false") {
                    forge::nnue::enabled = value_text == "true";
                    searcher.clear_hash();
                } else {
                    note_invalid();
                }
            } else if (name == "HindsightDepth") {
                if (value_text == "true" || value_text == "false") forge::tune::HindsightDepth = value_text == "true";
                else note_invalid();
            } else if (name == "NullThreatVerify") {
                if (value_text == "true") forge::tune::NullThreatVerify = true;
                else if (value_text == "false") forge::tune::NullThreatVerify = false;
                else note_invalid();
            } else if (name == "DeadMaterial") {
                if (value_text != "true" && value_text != "false") note_invalid();
                else if (forge::dead_material_enabled != (value_text == "true")) {
                    forge::dead_material_enabled = value_text == "true";
                    searcher.clear_hash();
                }
            } else if (name == "ContHist4PlyRead" || name == "NonPawnCorrection" || name == "LmrDeeperShallower" ||
                       name == "ThreatHistory" || name == "LmrSignedCorrection" || name == "LmrLateParentRelief" ||
                       name == "NullSeeVeto" || name == "AspArmLate" || name == "EvasionOrdering" ||
                       name == "QuietExtinction" || name == "TmFinishIteration") {
                bool* target = name == "ContHist4PlyRead" ? &forge::tune::ContHist4PlyRead
                             : name == "NonPawnCorrection" ? &forge::tune::NonPawnCorrection
                             : name == "LmrDeeperShallower" ? &forge::tune::LmrDeeperShallower
                             : name == "ThreatHistory" ? &forge::tune::ThreatHistory
                             : name == "LmrSignedCorrection" ? &forge::tune::LmrSignedCorrection
                             : name == "LmrLateParentRelief" ? &forge::tune::LmrLateParentRelief
                             : name == "NullSeeVeto" ? &forge::tune::NullSeeVeto
                             : name == "AspArmLate" ? &forge::tune::AspArmLate
                             : name == "EvasionOrdering" ? &forge::tune::EvasionOrdering
                             : name == "QuietExtinction" ? &forge::tune::QuietExtinction
                                                        : &forge::tune::TmFinishIteration;
                if (value_text == "true" || value_text == "false") {
                    *target = value_text == "true";
                } else {
                    note_invalid();
                }
            } else if (name == "EvalRule50Damp") {
                if (value_text == "true" || value_text == "false") {
                    forge::tune::EvalRule50Damp = value_text == "true";
                    searcher.clear_hash();
                } else {
                    note_invalid();
                }
            } else if (name == "AspCappedReopen") {
                if (value_text == "true" || value_text == "false") {
                    forge::tune::AspCappedReopen = value_text == "true";
                } else {
                    note_invalid();
                }
            } else if (name == "TmNodeShare") {
                if (value_text == "true" || value_text == "false") forge::tune::TmNodeShare = value_text == "true";
                else note_invalid();
            } else if (name == "SoundMatePruning") {
                if (value_text == "true" || value_text == "false") {
                    const bool enabled = value_text == "true";
                    if (forge::tune::SoundMatePruning != enabled) {
                        forge::tune::SoundMatePruning = enabled;
                        // Scores already stored were built with the other guard.
                        searcher.clear();
                    }
                } else {
                    note_invalid();
                }
#if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
            } else if (name == "MateAlphaGuard") {
                if (value_text == "true" || value_text == "false") {
                    const bool enabled = value_text == "true";
                    if (forge::tune::MateAlphaGuard != enabled) {
                        forge::tune::MateAlphaGuard = enabled;
                        searcher.clear();
                    }
                } else {
                    note_invalid();
                }
#endif
            } else if (name == "CuckooRep" || name == "TtPruneV2" || name == "CorrHistV2") {
                // B4 bundle (forge/r9): registration only; the search reads the values between searches.
                bool* target = name == "CuckooRep" ? &forge::tune::CuckooRep
                             : name == "TtPruneV2" ? &forge::tune::TtPruneV2
                                                   : &forge::tune::CorrHistV2;
                if (value_text == "true" || value_text == "false") *target = value_text == "true";
                else note_invalid();
            } else if (name == "HistRework") {
                apply_spin(0, forge::b4::MaxReworkLevel, [&](int clamped) { forge::tune::HistRework = clamped; });
            } else if (name == "MultiPV") {
                apply_spin(1, 8, [&](int clamped) { multipv = clamped; });
            } else if (name == "Hash") {
                apply_spin(1, 2048, [&](int clamped) {
                    searcher.resize_hash(static_cast<std::size_t>(clamped));
                });
            } else if (name == "Threads") {
                apply_spin(1, 256, [&](int clamped) { searcher.set_threads(clamped); });
            } else if (name == "Move Overhead") {
                apply_spin(0, 1000, [&](int clamped) { move_overhead_ms = clamped; });
            } else if (name == "DrawJitter") {
                apply_spin(0, forge::DrawJitterMax, [&](int clamped) { forge::set_draw_jitter(clamped, searcher); });
            } else {
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                std::cout << "info string unknown option " << name << std::endl;
            }
        } else if (command == "position") {
            stop_search();
            apply_position(board, input, pos_cache);
        } else if (command == "go") {
            stop_search();
#if FORGE_NNUE_V3
            if (const std::string v3_problem = forge::nnue::v3::problem(); !v3_problem.empty()) {
                // Fail-loud rule: a requested v3 net that cannot evaluate never falls back silently.
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string ERROR NNUE v3: " << v3_problem << std::endl; }
                return 2;
            }
#endif
            std::string first;
            const auto position = input.tellg();
            input >> first;
            if (first == "perft") {
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
                limits.multipv = multipv;
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
                ponder_search_active = limits.ponder;
                searcher.reset_stop();
                {
                    const std::lock_guard<std::mutex> lock(stop_mutex);
                    stop_requested = false;
                    ponder_hit_received = false;
                    pending_task.board = board;
                    pending_task.limits = std::move(limits);
                    pending_task.ponder_enabled = ponder_enabled;
                    has_task = true;
                    worker_busy = true;
                }
                work_cv.notify_one();
            }
        } else if (command == "eval") {
#if FORGE_NNUE_V3
            if (forge::nnue::enabled && forge::nnue::available() && forge::nnue::v3::active()) {
                // The v3 net is the whole evaluation: the value from fresh accumulators and the scalar output
                // sum (the reference path), from the side to move, in the same line format as below.
                const int value = forge::nnue::v3::evaluate_reference(*forge::nnue::v3::loaded(), board);
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                std::cout << "info string eval hce 0 nnue " << value << " total " << value;
                if (board.in_check()) std::cout << " incheck 1";
                std::cout << std::endl;
                continue;
            }
#endif
            const forge::EvalComponents parts = forge::Evaluator::static_eval_components(board);
            const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
            std::cout << "info string eval hce " << parts.hce << " nnue " << parts.nnue
                      << " total " << parts.total;
            if (parts.in_check) std::cout << " incheck 1";
            std::cout << std::endl;
        } else if (command == "bench") {
            // Fixed-depth search over a small position set; prints a node
            // signature and speed for quick regression and performance checks.
            stop_search();
#if FORGE_NNUE_V3
            if (const std::string v3_problem = forge::nnue::v3::problem(); !v3_problem.empty()) {
                // Fail-loud rule: a requested v3 net that cannot evaluate never falls back silently.
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string ERROR NNUE v3: " << v3_problem << std::endl; }
                return 2;
            }
#endif
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
                ponder_search_active = false;
            }
        } else if (command == "selfgame") {
            stop_search();
            SgConfig sg_cfg;
            std::string_view bad_word;
            if (!parse_selfgame_config(line, sg_cfg, bad_word)) {
                std::string err = "sgerror badline ";
                err += bad_word;
                err += '\n';
                const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                std::cout.write(err.data(), static_cast<std::streamsize>(err.size()));
                std::cout.flush();
                continue;
            }
#if FORGE_NNUE_V3
            if (const std::string v3_problem = forge::nnue::v3::problem(); !v3_problem.empty()) {
                { const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex()); std::cout << "info string ERROR NNUE v3: " << v3_problem << std::endl; }
                return 2;
            }
#endif
            pos_cache.valid = false;
            run_selfgame(board, searcher, move_overhead_ms, multipv, sg_cfg);
        } else if (command == "sgstate") {
            stop_search();
            emit_sgstate(board);
        } else if (command == "stop") {
            stop_search();
        } else if (command == "quit") {
            stop_search();
            break;
        }
    }
    stop_search();
    return 0;
}

}  // namespace forge

#ifndef FORGE_UCI_NO_MAIN
int main() {
    return forge::uci_loop(std::cin);
}
#endif
