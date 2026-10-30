// forge_selfplay_fast: native driver for Forge self-play data generation (R8, 2026-10-29).
//
// Plays the same games as forge-nnue-tools/forge_selfplay.py with the same, unchanged engine binary (UCI, one
// process per worker, Threads 1, Hash 16, `ucinewgame` once per game, the growing `position startpos moves ...`
// history, `go nodes N` per move), the same rules and the same output lines, without Python: no python-chess,
// no asyncio pipes, no SQLite + fsync per game. Chess rules come from Forge's own Board (src/board.cpp).
//
// Rules reproduced from forge_selfplay.py (defaults in brackets):
//   opening      --opening-plies [8] uniformly random legal moves (or the moves of --openings FILE, one game per line)
//   per move     the score of the LAST `info ... score` line (bound if it says lowerbound/upperbound)
//   record       (FEN before the move, cp) when: not in check, move not a capture / en passant / promotion, score
//                not a mate and not a bound, |cp| <= --max-score [3000]
//   adjudicate   --adjudicate-plies [4] consecutive plies whose (exact) score, seen from White, is >= +/-
//                --adjudicate-cp [2000] for the same side -> that side wins; mate scores count as decisive
//   terminal     checkmate, stalemate, insufficient material (python-chess's rule), threefold repetition,
//                halfmove clock >= 100, ply >= --max-ply [300] (draws); only completed games are exported
//   output       "FEN | cp | result" (result = White's, one decimal) after de-duplication on the first four FEN
//                fields; files of --lines-per-file [10,000,000] lines
// Extra: --pos writes the kept records also as Forge FPOS v1 files (35 bytes per position, the format of
// nnue_data/pos), so the text -> .pos conversion step is not needed; --own-book sets the engine's OwnBook option
// (the live pipeline leaves the engine default, true, which can return a move without a score: the Oct-18 crash).
//
// usage: forge_selfplay_fast --engine E --out DIR [--workers N] [--cpus 8,9|8-9] [--nodes 5000] [--hash 16]
//        [--max-minutes M] [--games-per-worker G] [--seed S] [--openings FILE] [--prefix NAME] [--pos]
//        [--own-book true|false] [--progress-seconds 60] [--opening-plies 8] [--max-ply 300]
//        [--adjudicate-cp 2000] [--adjudicate-plies 4] [--max-score 3000] [--lines-per-file N] [--no-dedup]
//        [--priority idle|belownormal]
#include "forge/board.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <mutex>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

using namespace forge;

namespace {

struct Options {
    std::string engine, out, openings, prefix = "forge_selfplay_fast";
    int check_nodes = 0;  // > 0: nodes for in-check positions (never recorded); 0 = --nodes (the live rule)
    int workers = 1, nodes = 5000, hash = 16, opening_plies = 8, max_ply = 300, adjudicate_cp = 2000,
        adjudicate_plies = 4, max_score = 3000;
    double max_minutes = 0, progress_seconds = 60;
    long long games_per_worker = 0, lines_per_file = 10'000'000;
    std::uint64_t seed = 1;
    std::vector<int> cpus;
    bool pos = false, dedup = true, own_book = false, idle = true;
    bool dedup_exact = false;  // false: bounded direct-mapped table of --dedup-mb MB (default); true: exact set
    long long dedup_mb = 512;
};

// ---------------------------------------------------------------- engine process (UCI over pipes)
class Engine {
public:
    bool start(const std::string& exe, DWORD_PTR affinity, bool idle) {
        SECURITY_ATTRIBUTES sa{sizeof(sa), nullptr, TRUE};
        HANDLE out_r, out_w, in_r, in_w;
        if (!CreatePipe(&out_r, &out_w, &sa, 1 << 16) || !CreatePipe(&in_r, &in_w, &sa, 1 << 16)) return false;
        SetHandleInformation(out_r, HANDLE_FLAG_INHERIT, 0);
        SetHandleInformation(in_w, HANDLE_FLAG_INHERIT, 0);
        STARTUPINFOA si{};
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = in_r;
        si.hStdOutput = out_w;
        si.hStdError = out_w;
        PROCESS_INFORMATION pi{};
        std::string cmd = "\"" + exe + "\"";
        std::vector<char> cmdline(cmd.begin(), cmd.end());
        cmdline.push_back('\0');
        const DWORD flags = CREATE_SUSPENDED | CREATE_NO_WINDOW | (idle ? IDLE_PRIORITY_CLASS : BELOW_NORMAL_PRIORITY_CLASS);
        if (!CreateProcessA(nullptr, cmdline.data(), nullptr, nullptr, TRUE, flags, nullptr, nullptr, &si, &pi)) return false;
        if (affinity != 0) SetProcessAffinityMask(pi.hProcess, affinity);
        ResumeThread(pi.hThread);
        CloseHandle(pi.hThread);
        CloseHandle(out_w);
        CloseHandle(in_r);
        process_ = pi.hProcess;
        pid_ = pi.dwProcessId;
        read_ = out_r;
        write_ = in_w;
        return true;
    }
    void send(const std::string& line) {
        std::string s = line + "\n";
        DWORD done = 0;
        WriteFile(write_, s.data(), static_cast<DWORD>(s.size()), &done, nullptr);
    }
    bool read_line(std::string& line) {
        line.clear();
        for (;;) {
            if (pos_ < len_) {
                const char* nl = static_cast<const char*>(std::memchr(buf_ + pos_, '\n', len_ - pos_));
                if (nl) {
                    line.append(buf_ + pos_, nl - (buf_ + pos_));
                    pos_ = (nl - buf_) + 1;
                    if (!line.empty() && line.back() == '\r') line.pop_back();
                    return true;
                }
                line.append(buf_ + pos_, len_ - pos_);
                pos_ = len_ = 0;
            }
            DWORD got = 0;
            if (!ReadFile(read_, buf_, sizeof(buf_), &got, nullptr) || got == 0) return false;
            pos_ = 0;
            len_ = got;
        }
    }
    bool wait_for(const char* prefix) {
        std::string line;
        const std::size_t n = std::strlen(prefix);
        while (read_line(line)) if (line.compare(0, n, prefix) == 0) return true;
        return false;
    }
    void quit() {
        send("quit");
        if (WaitForSingleObject(process_, 10000) != WAIT_OBJECT_0) TerminateProcess(process_, 1);  // own child only
        CloseHandle(process_);
        CloseHandle(read_);
        CloseHandle(write_);
    }
    DWORD pid() const { return pid_; }

private:
    HANDLE process_ = nullptr, read_ = nullptr, write_ = nullptr;
    DWORD pid_ = 0;
    char buf_[1 << 15];
    std::size_t pos_ = 0, len_ = 0;
};

// ---------------------------------------------------------------- chess rules as forge_selfplay.py (python-chess)
constexpr Bitboard DarkSquares = 0xAA55AA55AA55AA55ULL;

bool side_insufficient(const Board& b, Color c) {
    const Bitboard own = b.occupied(c), opp = b.occupied(c == White ? Black : White);
    const Bitboard pawns = b.pieces(Pawn), knights = b.pieces(Knight), bishops = b.pieces(Bishop),
                   rooks = b.pieces(Rook), queens = b.pieces(Queen), kings = b.pieces(King);
    if (own & (pawns | rooks | queens)) return false;
    if (own & knights) return popcount(own) <= 2 && (opp & ~kings & ~queens) == 0;
    if (own & bishops) {
        const bool same_colour = (bishops & DarkSquares) == 0 || (bishops & ~DarkSquares) == 0;
        return same_colour && pawns == 0 && knights == 0;
    }
    return true;
}

bool insufficient_material(const Board& b) { return side_insufficient(b, White) && side_insufficient(b, Black); }

// Game state: the board plus the key history for threefold repetition (every position since the start).
struct Game {
    Board board;
    std::vector<std::uint64_t> keys;
    std::vector<std::string> moves;
    int ply = 0;
    void reset() {
        (void)board.set_fen(Board::StandardStartFen);
        keys.assign(1, board.key());
        moves.clear();
        ply = 0;
    }
    void push(const Move& m) {
        moves.push_back(Board::move_to_uci(m));
        Undo u;
        (void)board.make_move(m, u);
        keys.push_back(board.key());
        ++ply;
    }
    bool threefold() const { return std::count(keys.begin(), keys.end(), keys.back()) >= 3; }
};

// terminal_result(): -1 = not over, else White's result * 2 (0 loss, 1 draw, 2 win)
int terminal(Game& g, int max_ply) {
    const MoveList legal = g.board.legal_moves();
    if (legal.size() == 0) {
        if (g.board.in_check()) return g.board.side_to_move() == White ? 0 : 2;
        return 1;
    }
    if (insufficient_material(g.board) || g.threefold() || g.board.halfmove_clock() >= 100 || g.ply >= max_ply) return 1;
    return -1;
}

// ---------------------------------------------------------------- output: dedup, text and FPOS files
struct Hash128 {
    std::uint64_t a, b;
    bool operator==(const Hash128& o) const { return a == o.a && b == o.b; }
};
struct Hash128Hasher {
    std::size_t operator()(const Hash128& h) const { return static_cast<std::size_t>(h.a ^ (h.b * 0x9E3779B97F4A7C15ULL)); }
};
Hash128 hash_key(const std::string& s) {  // two independent 64-bit hashes of the first four FEN fields
    std::uint64_t a = 1469598103934665603ULL, b = 0x6a09e667f3bcc909ULL;
    for (unsigned char c : s) {
        a = (a ^ c) * 1099511628211ULL;
        b = (b + c) * 0x9E3779B97F4A7C15ULL;
        b ^= b >> 29;
    }
    a ^= a >> 31;
    b ^= b >> 32;
    return {a * 0xbf58476d1ce4e5b9ULL, b * 0x94d049bb133111ebULL};
}
std::string four_fields(const std::string& fen) {
    std::size_t p = 0;
    for (int i = 0; i < 4 && p != std::string::npos; ++i) p = fen.find(' ', p + 1);
    return p == std::string::npos ? fen : fen.substr(0, p);
}

struct Record {
    std::string fen;
    int cp;
    std::array<std::uint8_t, 32> board;
    bool black;
};

class Output {
public:
    explicit Output(const Options& o) : o_(o) {
        if (o_.dedup && !o_.dedup_exact) table_.assign(static_cast<std::size_t>(o_.dedup_mb) * 1024 * 1024 / 8, 0);
    }
    // returns the number of records kept
    long long add_game(const std::vector<Record>& recs, int white_result2) {
        std::lock_guard<std::mutex> lock(m_);
        long long kept = 0;
        for (const Record& r : recs) {
            if (o_.dedup && is_duplicate(hash_key(four_fields(r.fen)))) continue;
            if (!text_.is_open()) open_next();
            static const char* res[3] = {"0.0", "0.5", "1.0"};
            text_buf_ += r.fen;
            text_buf_ += " | ";
            text_buf_ += std::to_string(r.cp);
            text_buf_ += " | ";
            text_buf_ += res[white_result2];
            text_buf_ += '\n';
            if (o_.pos) {
                boards_.insert(boards_.end(), r.board.begin(), r.board.end());
                scores_.push_back(static_cast<std::int16_t>(r.cp));
                metas_.push_back(static_cast<std::uint8_t>((r.black ? 1 : 0) | (white_result2 << 1)));
            }
            ++kept;
            if (++lines_ == o_.lines_per_file) close_file();
        }
        if (text_buf_.size() >= (1 << 20)) flush_text();
        total_ += kept;
        return kept;
    }
    void close() {
        std::lock_guard<std::mutex> lock(m_);
        close_file();
    }
    long long total() {
        std::lock_guard<std::mutex> lock(m_);
        return total_;
    }

private:
    // exact: every key of the run; bounded: slot = key mod size holds the newest fingerprint (0 = empty)
    bool is_duplicate(const Hash128& h) {
        if (o_.dedup_exact) return !seen_.insert(h).second;
        const std::uint64_t fp = h.b | 1ULL;
        std::uint64_t& slot = table_[static_cast<std::size_t>(h.a % table_.size())];
        if (slot == fp) return true;
        slot = fp;
        return false;
    }
    static bool exists(const std::string& path) { return GetFileAttributesA(path.c_str()) != INVALID_FILE_ATTRIBUTES; }
    void open_next() {
        // Never overwrite: skip every number whose .txt, .txt.part, .txt.md5 or .pos already exists.
        for (;;) {
            char name[64];
            std::snprintf(name, sizeof(name), "%s_%03d", o_.prefix.c_str(), ++file_no_);
            base_ = o_.out + "\\" + name;
            if (!exists(base_ + ".txt") && !exists(base_ + ".txt.part") && !exists(base_ + ".txt.md5") && !exists(base_ + ".pos")) break;
        }
        text_.open(base_ + ".txt", std::ios::binary | std::ios::trunc);
        lines_ = 0;
    }
    void flush_text() {
        if (text_.is_open() && !text_buf_.empty()) {
            text_.write(text_buf_.data(), static_cast<std::streamsize>(text_buf_.size()));
            text_.flush();
        }
        text_buf_.clear();
    }
    void close_file() {
        if (!text_.is_open()) return;
        flush_text();
        text_.close();
        if (o_.pos) {
            std::ofstream f(base_ + ".pos", std::ios::binary | std::ios::trunc);
            const std::uint32_t ver = 1;
            const std::uint64_t n = scores_.size();
            f.write("FPOS", 4);
            f.write(reinterpret_cast<const char*>(&ver), 4);
            f.write(reinterpret_cast<const char*>(&n), 8);
            f.write(reinterpret_cast<const char*>(boards_.data()), static_cast<std::streamsize>(boards_.size()));
            f.write(reinterpret_cast<const char*>(scores_.data()), static_cast<std::streamsize>(n * 2));
            f.write(reinterpret_cast<const char*>(metas_.data()), static_cast<std::streamsize>(n));
            f.close();
            std::ofstream info(base_ + ".pos.info", std::ios::binary | std::ios::trunc);
            info << "source=" << base_ << ".txt\nlines=" << n << "\nrecords=" << n << "\nbad=0\n";
            boards_.clear();
            scores_.clear();
            metas_.clear();
        }
    }
    const Options& o_;
    std::mutex m_;
    std::unordered_set<Hash128, Hash128Hasher> seen_;
    std::vector<std::uint64_t> table_;
    std::ofstream text_;
    std::string text_buf_, base_;
    std::vector<std::uint8_t> boards_;
    std::vector<std::int16_t> scores_;
    std::vector<std::uint8_t> metas_;
    long long lines_ = 0, total_ = 0;
    int file_no_ = 0;
};

std::array<std::uint8_t, 32> fpos_board(const Board& b) {
    std::array<std::uint8_t, 32> out{};
    for (int s = 0; s < 64; ++s) {
        const int p = b.piece_at(s);  // Forge: 0 empty, 1..6 white P N B R Q K, 7..12 black (FPOS codes)
        out[static_cast<std::size_t>(s >> 1)] |= static_cast<std::uint8_t>((s & 1) ? (p << 4) : p);
    }
    return out;
}

// ---------------------------------------------------------------- worker
struct Stats {
    std::atomic<long long> games{0}, candidates{0}, kept{0}, errors{0}, attempts{0};
    // searched positions and why one was not recorded (first matching reason, in this order)
    std::atomic<long long> searches{0}, not_bound{0}, not_check{0}, not_noisy{0}, not_mate{0}, not_big{0};
    std::atomic<long long> search_us{0};
};

std::vector<std::vector<std::string>> load_openings(const std::string& path) {
    std::vector<std::vector<std::string>> out;
    std::ifstream f(path);
    std::string line;
    while (std::getline(f, line)) {
        std::istringstream in(line);
        std::vector<std::string> mv;
        std::string m;
        while (in >> m) mv.push_back(m);
        out.push_back(mv);
    }
    return out;
}

struct Reply {
    std::string best;
    bool has_score = false, mate = false, bound = false;
    int value = 0;
};

bool search(Engine& e, const Game& g, int nodes, Reply& r, Stats& st) {
    std::string cmd = "position startpos";
    if (!g.moves.empty()) {
        cmd += " moves";
        for (const std::string& m : g.moves) {
            cmd += ' ';
            cmd += m;
        }
    }
    e.send(cmd);
    const auto t0 = std::chrono::steady_clock::now();
    e.send("go nodes " + std::to_string(nodes));
    r = Reply{};
    std::string line;
    while (e.read_line(line)) {
        if (line.compare(0, 9, "bestmove ") == 0) {
            const std::size_t sp = line.find(' ', 9);
            r.best = line.substr(9, sp == std::string::npos ? std::string::npos : sp - 9);
            st.search_us += std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - t0).count();
            return true;
        }
        if (line.compare(0, 5, "info ") != 0 || line.compare(0, 12, "info string ") == 0) continue;
        const std::size_t s = line.find(" score ");
        if (s == std::string::npos) continue;
        std::istringstream in(line.substr(s + 7));
        std::string kind;
        int v = 0;
        in >> kind >> v;
        r.has_score = true;
        r.mate = kind == "mate";
        r.value = v;
        r.bound = line.find(" lowerbound") != std::string::npos || line.find(" upperbound") != std::string::npos;
    }
    return false;
}

void worker(int id, const Options& o, Output& out, Stats& st, const std::vector<std::vector<std::string>>& openings,
            std::atomic<std::size_t>& next_opening, std::atomic<bool>& stop) {
    Engine e;
    // CPU mask: with more CPUs than workers each worker gets its own contiguous slice (CPUs 12-15 and 2 workers ->
    // 12-13 and 14-15: one physical core each with SMT), with as many workers as CPUs one CPU each, with fewer CPUs
    // than workers (or one worker) every worker gets all of them (the live script pins all workers to all CPUs).
    DWORD_PTR mask = 0;
    if (!o.cpus.empty()) {
        const std::size_t n = o.cpus.size(), w = static_cast<std::size_t>(o.workers);
        if (w > 1 && w <= n) {
            const std::size_t slice = n / w, first = static_cast<std::size_t>(id) * slice;
            for (std::size_t k = first; k < first + slice; ++k) mask |= static_cast<DWORD_PTR>(1) << o.cpus[k];
        } else {
            for (int c : o.cpus) mask |= static_cast<DWORD_PTR>(1) << c;
        }
    }
    if (!e.start(o.engine, mask, o.idle)) {
        std::fprintf(stderr, "worker %d: cannot start %s\n", id + 1, o.engine.c_str());
        stop = true;
        return;
    }
    e.send("uci");
    e.wait_for("uciok");
    e.send("setoption name Threads value 1");
    e.send("setoption name Hash value " + std::to_string(o.hash));
    e.send(std::string("setoption name OwnBook value ") + (o.own_book ? "true" : "false"));
    e.send("isready");
    e.wait_for("readyok");
    std::printf("Worker %d: engine PID %lu, affinity 0x%llx, %s\n", id + 1, static_cast<unsigned long>(e.pid()),
                static_cast<unsigned long long>(mask), o.idle ? "Idle" : "BelowNormal");
    std::fflush(stdout);
    std::mt19937_64 rng(o.seed * 1000003ULL + static_cast<std::uint64_t>(id));
    Game g;
    long long my_games = 0;
    bool engine_dead = false;
    while (!stop && !engine_dead) {
        if (o.games_per_worker && my_games >= o.games_per_worker) break;
        ++st.attempts;
        g.reset();
        bool aborted = false;
        // opening
        const std::vector<std::string>* book = nullptr;
        if (!openings.empty()) {
            const std::size_t k = next_opening.fetch_add(1);
            if (k >= openings.size()) break;
            book = &openings[k];
        }
        const int plies = book ? static_cast<int>(book->size()) : o.opening_plies;
        for (int i = 0; i < plies && !aborted; ++i) {
            if (terminal(g, o.max_ply) >= 0) { aborted = true; break; }
            if (book) {
                const auto m = g.board.parse_uci((*book)[static_cast<std::size_t>(i)]);
                if (!m) { aborted = true; break; }
                g.push(*m);
            } else {
                const MoveList legal = g.board.legal_moves();
                g.push(legal[static_cast<std::size_t>(rng() % legal.size())]);
            }
        }
        if (aborted || terminal(g, o.max_ply) >= 0) continue;  // as play_game: no samples
        e.send("ucinewgame");
        e.send("isready");
        if (!e.wait_for("readyok")) { engine_dead = true; break; }
        std::vector<Record> recs;
        int winner = 0, streak = 0, result = -1;  // winner: +1 White, -1 Black, 0 none
        for (;;) {
            result = terminal(g, o.max_ply);
            if (result >= 0) break;
            if (stop) { result = -2; break; }
            Reply r;
            const int budget = (o.check_nodes > 0 && g.board.in_check()) ? o.check_nodes : o.nodes;
            if (!search(e, g, budget, r, st)) { engine_dead = true; result = -3; break; }
            const auto mv = g.board.parse_uci(r.best);
            if (!mv || !r.has_score) { ++st.errors; result = -3; break; }  // python: RuntimeError (no score / illegal)
            const Move m = *mv;
            const bool stm_white = g.board.side_to_move() == White;
            ++st.searches;
            if (r.bound) ++st.not_bound;
            else if (g.board.in_check()) ++st.not_check;
            else if (m.is_capture() || m.is_promotion()) ++st.not_noisy;
            else if (r.mate) ++st.not_mate;
            else if (std::abs(r.value) > o.max_score) ++st.not_big;
            else recs.push_back({g.board.fen(), r.value, fpos_board(g.board), !stm_white});
            int side = 0;
            if (!r.bound) {
                // python-chess Score order: mate(+n) is above every cp, mate(-n) below; Mate(0) is a loss for the mover
                const bool stm_wins = r.mate ? r.value > 0 : r.value >= o.adjudicate_cp;
                const bool stm_loses = r.mate ? r.value <= 0 : r.value <= -o.adjudicate_cp;
                if (stm_wins) side = stm_white ? 1 : -1;
                else if (stm_loses) side = stm_white ? -1 : 1;
            }
            streak = (side != 0 && side == winner) ? streak + 1 : (side != 0 ? 1 : 0);
            winner = side;
            g.push(m);
            result = terminal(g, o.max_ply);
            if (result >= 0) break;
            if (streak >= o.adjudicate_plies) { result = winner > 0 ? 2 : 0; break; }
        }
        if (result < 0) {
            if (result == -3 && !engine_dead) continue;
            break;
        }
        ++my_games;
        ++st.games;
        st.candidates += static_cast<long long>(recs.size());
        st.kept += out.add_game(recs, result);
    }
    if (engine_dead) {
        ++st.errors;
        std::fprintf(stderr, "worker %d: the engine stopped answering (pipe closed); this worker ends\n", id + 1);
    }
    e.quit();
}

std::vector<int> parse_cpus(const std::string& s) {
    std::vector<int> v;
    std::stringstream in(s);
    std::string part;
    while (std::getline(in, part, ',')) {
        const std::size_t d = part.find('-');
        if (d == std::string::npos) v.push_back(std::stoi(part));
        else for (int c = std::stoi(part.substr(0, d)); c <= std::stoi(part.substr(d + 1)); ++c) v.push_back(c);
    }
    return v;
}

}  // namespace

int main(int argc, char** argv) {
    Options o;
    for (int i = 1; i < argc; ++i) {
        const std::string k = argv[i];
        if (k == "--pos") { o.pos = true; continue; }
        if (k == "--no-dedup") { o.dedup = false; continue; }
        if (i + 1 >= argc) { std::fprintf(stderr, "option %s needs a value\n", k.c_str()); return 2; }
        const std::string v = argv[++i];
        if (k == "--engine") o.engine = v;
        else if (k == "--out") o.out = v;
        else if (k == "--workers") o.workers = std::stoi(v);
        else if (k == "--cpus") o.cpus = parse_cpus(v);
        else if (k == "--nodes") o.nodes = std::stoi(v);
        else if (k == "--check-nodes") o.check_nodes = std::stoi(v);
        else if (k == "--hash") o.hash = std::stoi(v);
        else if (k == "--max-minutes") o.max_minutes = std::stod(v);
        else if (k == "--games-per-worker") o.games_per_worker = std::stoll(v);
        else if (k == "--seed") o.seed = std::stoull(v);
        else if (k == "--openings") o.openings = v;
        else if (k == "--prefix") o.prefix = v;
        else if (k == "--own-book") o.own_book = v == "true";
        else if (k == "--progress-seconds") o.progress_seconds = std::stod(v);
        else if (k == "--opening-plies") o.opening_plies = std::stoi(v);
        else if (k == "--max-ply") o.max_ply = std::stoi(v);
        else if (k == "--adjudicate-cp") o.adjudicate_cp = std::stoi(v);
        else if (k == "--adjudicate-plies") o.adjudicate_plies = std::stoi(v);
        else if (k == "--max-score") o.max_score = std::stoi(v);
        else if (k == "--lines-per-file") o.lines_per_file = std::stoll(v);
        else if (k == "--priority") o.idle = v != "belownormal";
        else if (k == "--dedup") o.dedup_exact = v == "exact";
        else if (k == "--dedup-mb") o.dedup_mb = std::max(1LL, std::stoll(v));
        else { std::fprintf(stderr, "unknown option %s\n", k.c_str()); return 2; }
    }
    if (o.engine.empty() || o.out.empty() || o.workers < 1) {
        std::fprintf(stderr, "usage: forge_selfplay_fast --engine E --out DIR [options] (see the source header)\n");
        return 2;
    }
    CreateDirectoryA(o.out.c_str(), nullptr);
    const auto openings = o.openings.empty() ? std::vector<std::vector<std::string>>{} : load_openings(o.openings);
    std::atomic<std::size_t> next_opening{0};
    Output out(o);
    Stats st;
    std::atomic<bool> stop{false};
    std::printf("forge_selfplay_fast: %d worker(s), CPUs", o.workers);
    for (int c : o.cpus) std::printf(" %d", c);
    std::printf(", Threads=1, Hash=%d, OwnBook=%s; %d nodes/move; engine %s\n", o.hash, o.own_book ? "true" : "false",
                o.nodes, o.engine.c_str());
    std::fflush(stdout);
    const auto t0 = std::chrono::steady_clock::now();
    std::vector<std::thread> pool;
    for (int i = 0; i < o.workers; ++i)
        pool.emplace_back(worker, i, std::cref(o), std::ref(out), std::ref(st), std::cref(openings), std::ref(next_opening), std::ref(stop));
    auto last = t0;
    std::atomic<int> alive{o.workers};
    std::thread waiter([&] { for (auto& t : pool) t.join(); alive = 0; });
    while (alive > 0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
        const auto now = std::chrono::steady_clock::now();
        const double el = std::chrono::duration<double>(now - t0).count();
        if (o.max_minutes > 0 && el >= o.max_minutes * 60) stop = true;
        if (std::chrono::duration<double>(now - last).count() >= o.progress_seconds || alive == 0) {
            last = now;
            const long long kept = out.total();
            std::printf("Elapsed %.3f h: games=%lld positions=%lld positions/h=%.0f eligible=%lld errors=%lld search=%.1f%%\n",
                        el / 3600, st.games.load(), kept, kept * 3600.0 / std::max(el, 1e-9), st.candidates.load(),
                        st.errors.load(), 100.0 * st.search_us.load() / 1e6 / (std::max(el, 1e-9) * o.workers));
            std::fflush(stdout);
        }
    }
    waiter.join();
    out.close();
    const double el = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    const long long kept = out.total();
    std::printf("searches=%lld not recorded: bound=%lld in_check=%lld capture_or_promotion=%lld mate=%lld abs_cp_over_max=%lld"
                " (games that did not finish are not counted as positions)\n",
                st.searches.load(), st.not_bound.load(), st.not_check.load(), st.not_noisy.load(), st.not_mate.load(),
                st.not_big.load());
    std::printf("DONE: %.3f h, games=%lld positions=%lld positions/h=%.0f eligible=%lld errors=%lld dedup_removed=%lld\n",
                el / 3600, st.games.load(), kept, kept * 3600.0 / std::max(el, 1e-9), st.candidates.load(), st.errors.load(),
                st.candidates.load() - kept);
    return 0;
}
