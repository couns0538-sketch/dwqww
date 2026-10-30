// forge_selfplay_fast: native driver for Forge self-play data generation (R8, 2026-10-29; v5 = the R8 review fixes).
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
//                fields
// Extra: --pos writes the kept records also as Forge FPOS v1 files (35 bytes per position, the format of
// nnue_data/pos), so the text -> .pos conversion step is not needed; --own-book sets the engine's OwnBook option
// (the live pipeline leaves the engine default, true, which can return a move without a score: the Oct-18 crash).
//
// Robustness (v5, after the R8 code review):
//   seed         --seed S, else random_device ^ time ^ pid; printed at start, so a restart never replays old games
//   engines      every engine answer has a --engine-timeout [180] s deadline; a silent engine is killed and
//                restarted (its game is dropped); a worker ends after --max-restarts [5] + 1 failures in a row;
//                exit code 3 when every worker's engine is dead
//   shards       data go to <name>.txt.part / .pos.part and are renamed to .txt / .pos when the shard is complete:
//                after --lines-per-file [1,000,000] lines or --rotate-minutes [30]; buffers reach the file at game
//                boundaries at least every --flush-seconds [5]; the STOP file (--stop-file, default <out>\STOP) ends
//                the run cleanly; --resume keeps every complete line of a .txt.part left by a hard kill
//   memory       run-local dedup table --dedup-mb [64]; .pos boards stream to the .pos.part file (3 bytes per record
//                stay in memory until the shard closes); RSS of the driver and its engines is printed with progress
//   global dedup after each shard the driver runs --post-script (dedup_against_db.py --shard, next to this exe by
//                default) against the live hash DB (--dedup-db, opened read only) and its own DB
//                (<out>\<prefix>_seen.sqlite3): <name>.dedup.txt / .dedup.pos hold the new positions only;
//                --no-global-dedup skips it and records that data change in every .pos.info
//   process      the driver runs at BelowNormal, pinned to --cpus [12-15], inside a job object (its engines and
//                post-steps end with it); engines at Idle (--priority belownormal to change); every write is checked
//                (exit 4); an existing --out is refused unless --resume
//
// usage: forge_selfplay_fast --engine E --out DIR [--resume] [--workers N] [--cpus 12-15] [--nodes 5000] [--hash 16]
//        [--max-minutes M] [--games-per-worker G] [--seed S] [--openings FILE] [--prefix NAME] [--pos]
//        [--own-book true|false] [--progress-seconds 60] [--opening-plies 8] [--max-ply 300]
//        [--adjudicate-cp 2000] [--adjudicate-plies 4] [--max-score 3000] [--lines-per-file N] [--rotate-minutes 30]
//        [--flush-seconds 5] [--stop-file PATH] [--engine-timeout 180] [--max-restarts 5] [--no-dedup]
//        [--dedup bounded|exact] [--dedup-mb 64] [--dedup-db PATH] [--post-python EXE] [--post-script PY]
//        [--post-timeout-minutes 60] [--no-global-dedup] [--priority idle|belownormal] [--job-memory-mb 0]
// exit codes: 0 done, 2 usage / refused, 3 every engine dead, 4 output (I/O) error, 5 some workers gave up,
//             6 a global-dedup post-step failed (the raw shard is complete; --resume runs the post-step again)
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0A00
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include "forge/board.hpp"

#include <windows.h>
#include <psapi.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <fstream>
#include <memory>
#include <mutex>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

using namespace forge;

namespace {

constexpr const char* Version = "forge_selfplay_fast v5";

struct Options {
    std::string engine, out, openings, prefix = "forge_selfplay_fast", stop_file;
    std::string dedup_db = R"(D:\grok-pc-data\selfplay_out\forge_seen_hashes.sqlite3)";
    std::string post_python = R"(C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe)";
    std::string post_script;  // default: dedup_against_db.py next to this exe
    int check_nodes = 0;      // > 0: nodes for in-check positions (never recorded); 0 = --nodes (the live rule)
    int workers = 1, nodes = 5000, hash = 16, opening_plies = 8, max_ply = 300, adjudicate_cp = 2000,
        adjudicate_plies = 4, max_score = 3000, max_restarts = 5;
    double max_minutes = 0, progress_seconds = 60, rotate_minutes = 30, flush_seconds = 5, engine_timeout = 180,
           post_timeout_minutes = 60;
    long long games_per_worker = 0, lines_per_file = 1'000'000, dedup_mb = 64, job_memory_mb = 0;
    std::uint64_t seed = 0;
    bool seed_given = false;
    std::vector<int> cpus;
    bool pos = false, dedup = true, own_book = false, idle = true, resume = false, global_dedup = true;
    bool dedup_exact = false;  // false: bounded direct-mapped table of --dedup-mb MB (default); true: exact set
    // test hooks (never needed in production): a simulated hard kill, a failing disk
    double test_exit_after_seconds = 0;
    long long test_fail_write_after = 0;
};

// ---------------------------------------------------------------- logging, errors, files
std::mutex g_print;
std::atomic<bool> g_stop{false};
std::atomic<bool> g_io_failed{false};
std::atomic<long long> g_writes{0};
long long g_fail_write_after = 0;  // test hook

void say(const char* fmt, ...) {  // one timestamped line on stdout
    std::lock_guard<std::mutex> lock(g_print);
    SYSTEMTIME t;
    GetLocalTime(&t);
    std::printf("[%02d:%02d:%02d] ", t.wHour, t.wMinute, t.wSecond);
    va_list ap;
    va_start(ap, fmt);
    std::vprintf(fmt, ap);
    va_end(ap);
    std::putchar('\n');
    std::fflush(stdout);
}

std::string win_error(DWORD code) {
    char buf[300] = {0};
    const DWORD n = FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, nullptr, code, 0, buf,
                                   sizeof(buf) - 1, nullptr);
    std::string s(buf, n);
    while (!s.empty() && (s.back() == '\n' || s.back() == '\r' || s.back() == ' ' || s.back() == '.')) s.pop_back();
    return "Windows error " + std::to_string(code) + (s.empty() ? "" : " (" + s + ")");
}

void fatal_io(const std::string& what) {
    if (!g_io_failed.exchange(true)) say("ERROR: output failed: %s; stopping (the .part files stay for --resume)", what.c_str());
    g_stop = true;
}

class File {  // Win32 file, every call checked; handles are not inheritable
public:
    File() = default;
    File(const File&) = delete;
    File& operator=(const File&) = delete;
    ~File() {
        if (h_ != INVALID_HANDLE_VALUE) CloseHandle(h_);
    }
    // CREATE_NEW never overwrites; CREATE_ALWAYS only for the driver's own .part temp files; OPEN_EXISTING to salvage
    bool open(const std::string& path, DWORD disposition) {
        path_ = path;
        h_ = CreateFileA(path.c_str(), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ, nullptr, disposition,
                         FILE_ATTRIBUTE_NORMAL, nullptr);
        return h_ != INVALID_HANDLE_VALUE || fail("open");
    }
    bool write(const void* data, std::size_t n) {
        if (g_fail_write_after > 0 && ++g_writes > g_fail_write_after) {
            SetLastError(ERROR_DISK_FULL);
            return fail("write (test hook --test-fail-write-after)");
        }
        const char* p = static_cast<const char*>(data);
        while (n > 0) {
            const DWORD chunk = static_cast<DWORD>(std::min<std::size_t>(n, std::size_t{1} << 30));
            DWORD done = 0;
            if (!WriteFile(h_, p, chunk, &done, nullptr) || done == 0) return fail("write");
            p += done;
            n -= done;
        }
        return true;
    }
    bool read(void* data, DWORD n, DWORD& got) {
        got = 0;
        return ReadFile(h_, data, n, &got, nullptr) || fail("read");
    }
    bool seek(std::uint64_t offset) {
        LARGE_INTEGER li;
        li.QuadPart = static_cast<LONGLONG>(offset);
        return SetFilePointerEx(h_, li, nullptr, FILE_BEGIN) || fail("seek");
    }
    bool truncate_at(std::uint64_t offset) { return seek(offset) && (SetEndOfFile(h_) || fail("truncate")); }
    bool sync() { return FlushFileBuffers(h_) || fail("flush to disk"); }
    bool close() {
        if (h_ == INVALID_HANDLE_VALUE) return true;
        const BOOL ok = CloseHandle(h_);
        h_ = INVALID_HANDLE_VALUE;
        return ok || fail("close");
    }
    bool is_open() const { return h_ != INVALID_HANDLE_VALUE; }
    const std::string& error() const { return error_; }

private:
    bool fail(const char* what) {
        const DWORD code = GetLastError();
        error_ = std::string(what) + " " + path_ + ": " + win_error(code);
        return false;
    }
    HANDLE h_ = INVALID_HANDLE_VALUE;
    std::string path_, error_;
};

bool exists(const std::string& p) { return GetFileAttributesA(p.c_str()) != INVALID_FILE_ATTRIBUTES; }

bool rename_new(const std::string& from, const std::string& to, std::string& err) {  // never replaces a file
    if (MoveFileExA(from.c_str(), to.c_str(), MOVEFILE_WRITE_THROUGH)) return true;
    const DWORD code = GetLastError();
    err = "rename " + from + " -> " + to + ": " + win_error(code);
    return false;
}

bool write_small(const std::string& path, const std::string& text, std::string& err) {  // <path>.part, then rename
    File f;
    if (!f.open(path + ".part", CREATE_ALWAYS) || !f.write(text.data(), text.size()) || !f.sync() || !f.close()) {
        err = f.error();
        return false;
    }
    return rename_new(path + ".part", path, err);
}

std::string quote(const std::string& s) { return "\"" + s + "\""; }

// ---------------------------------------------------------------- child processes and the job object
HANDLE g_job = nullptr;
bool g_job_holds_self = false;  // the driver is in the job itself: its children join it automatically

// CreateProcess that lets the child inherit exactly its own std handles (PROC_THREAD_ATTRIBUTE_HANDLE_LIST): the pipes
// of one engine never leak into another engine or a post-step, so a dead engine always closes its pipe.
bool spawn(const std::string& cmdline, HANDLE in, HANDLE out, HANDLE err, DWORD flags, PROCESS_INFORMATION& pi,
           std::string& error) {
    HANDLE list[3];
    std::size_t n = 0;
    for (HANDLE h : {in, out, err})
        if (std::find(list, list + n, h) == list + n) list[n++] = h;
    SIZE_T size = 0;
    InitializeProcThreadAttributeList(nullptr, 1, 0, &size);
    std::vector<unsigned char> buf(size);
    auto* attrs = reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(buf.data());
    if (!InitializeProcThreadAttributeList(attrs, 1, 0, &size)) {
        error = "InitializeProcThreadAttributeList: " + win_error(GetLastError());
        return false;
    }
    bool ok = UpdateProcThreadAttribute(attrs, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST, list, n * sizeof(HANDLE), nullptr,
                                        nullptr) != 0;
    if (ok) {
        STARTUPINFOEXA si{};
        si.StartupInfo.cb = sizeof(si);
        si.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
        si.StartupInfo.hStdInput = in;
        si.StartupInfo.hStdOutput = out;
        si.StartupInfo.hStdError = err;
        si.lpAttributeList = attrs;
        std::vector<char> cmd(cmdline.begin(), cmdline.end());
        cmd.push_back('\0');
        ok = CreateProcessA(nullptr, cmd.data(), nullptr, nullptr, TRUE, flags | EXTENDED_STARTUPINFO_PRESENT, nullptr,
                            nullptr, &si.StartupInfo, &pi) != 0;
    }
    if (!ok) error = "CreateProcess " + cmdline + ": " + win_error(GetLastError());
    DeleteProcThreadAttributeList(attrs);
    return ok;
}

// a suspended child: put it into the job (when the driver is not in it itself), then let it run
bool adopt_child(PROCESS_INFORMATION& pi, DWORD_PTR affinity, std::string& error) {
    if (!g_job_holds_self && !AssignProcessToJobObject(g_job, pi.hProcess)) {
        error = "AssignProcessToJobObject: " + win_error(GetLastError());
    } else if (affinity != 0 && !SetProcessAffinityMask(pi.hProcess, affinity)) {
        error = "SetProcessAffinityMask: " + win_error(GetLastError());
    } else {
        ResumeThread(pi.hThread);
        CloseHandle(pi.hThread);
        return true;
    }
    TerminateProcess(pi.hProcess, 1);  // own suspended child that never ran
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return false;
}

bool make_job(long long memory_mb, std::string& note) {
    g_job = CreateJobObjectA(nullptr, nullptr);
    if (!g_job) {
        note = "CreateJobObject: " + win_error(GetLastError());
        return false;
    }
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION info{};
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if (memory_mb > 0) {
        info.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_JOB_MEMORY;
        info.JobMemoryLimit = static_cast<SIZE_T>(memory_mb) << 20;
    }
    if (!SetInformationJobObject(g_job, JobObjectExtendedLimitInformation, &info, sizeof(info))) {
        note = "SetInformationJobObject: " + win_error(GetLastError());
        return false;
    }
    g_job_holds_self = AssignProcessToJobObject(g_job, GetCurrentProcess()) != 0;
    note = g_job_holds_self ? "driver, engines and post-steps in one job object (kill on close)"
                            : "engines and post-steps in a job object (kill on close); the driver itself could not join it: " +
                                  win_error(GetLastError());
    return true;
}

// ---------------------------------------------------------------- engine process (UCI over pipes)
long long now_ms() { return static_cast<long long>(GetTickCount64()); }

struct EngineSlot {  // shared by a worker and the main thread's watchdog
    std::mutex m;
    HANDLE process = nullptr;
    DWORD pid = 0;
    std::atomic<long long> deadline{0};  // GetTickCount64() ms by which the engine must answer; 0 = not waiting
    std::atomic<bool> killed{false};
};

class Exchange {  // one command/answer exchange: the watchdog kills the engine if it misses the deadline
public:
    Exchange(EngineSlot& s, double seconds) : s_(s) { s_.deadline = now_ms() + static_cast<long long>(seconds * 1000); }
    ~Exchange() { s_.deadline = 0; }
    Exchange(const Exchange&) = delete;
    Exchange& operator=(const Exchange&) = delete;

private:
    EngineSlot& s_;
};

class Engine {
public:
    bool start(const Options& o, DWORD_PTR affinity, EngineSlot& slot, std::string& err) {
        SECURITY_ATTRIBUTES sa{sizeof(sa), nullptr, TRUE};
        HANDLE out_r = nullptr, out_w = nullptr, in_r = nullptr, in_w = nullptr;
        if (!CreatePipe(&out_r, &out_w, &sa, 1 << 16)) {
            err = "CreatePipe: " + win_error(GetLastError());
            return false;
        }
        if (!CreatePipe(&in_r, &in_w, &sa, 1 << 16)) {
            err = "CreatePipe: " + win_error(GetLastError());
            CloseHandle(out_r);
            CloseHandle(out_w);
            return false;
        }
        SetHandleInformation(out_r, HANDLE_FLAG_INHERIT, 0);
        SetHandleInformation(in_w, HANDLE_FLAG_INHERIT, 0);
        PROCESS_INFORMATION pi{};
        const DWORD flags = CREATE_SUSPENDED | CREATE_NO_WINDOW | (o.idle ? IDLE_PRIORITY_CLASS : BELOW_NORMAL_PRIORITY_CLASS);
        bool ok = spawn(quote(o.engine), in_r, out_w, out_w, flags, pi, err);
        CloseHandle(out_w);
        CloseHandle(in_r);
        if (ok) ok = adopt_child(pi, affinity, err);
        if (!ok) {
            CloseHandle(out_r);
            CloseHandle(in_w);
            return false;
        }
        process_ = pi.hProcess;
        pid_ = pi.dwProcessId;
        read_ = out_r;
        write_ = in_w;
        pos_ = len_ = 0;
        std::lock_guard<std::mutex> lock(slot.m);
        slot.process = process_;
        slot.pid = pid_;
        slot.killed = false;
        slot.deadline = 0;
        return true;
    }
    bool send(const std::string& line) {
        const std::string s = line + "\n";
        const char* p = s.data();
        std::size_t n = s.size();
        while (n > 0) {
            DWORD done = 0;
            if (!WriteFile(write_, p, static_cast<DWORD>(n), &done, nullptr) || done == 0) return false;
            p += done;
            n -= done;
        }
        return true;
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
        while (read_line(line))
            if (line.compare(0, n, prefix) == 0) return true;
        return false;
    }
    void stop(EngineSlot& slot) {  // quit (or end) the own child and close its handles
        if (!process_) return;
        if (!slot.killed && WaitForSingleObject(process_, 0) != WAIT_OBJECT_0) send("quit");
        if (WaitForSingleObject(process_, 3000) != WAIT_OBJECT_0) {
            TerminateProcess(process_, 1);  // own child that did not quit
            WaitForSingleObject(process_, 5000);
        }
        {
            std::lock_guard<std::mutex> lock(slot.m);
            slot.process = nullptr;
            slot.pid = 0;
            slot.deadline = 0;
        }
        CloseHandle(process_);
        CloseHandle(read_);
        CloseHandle(write_);
        process_ = read_ = write_ = nullptr;
    }
    DWORD pid() const { return pid_; }
    bool running() const { return process_ != nullptr; }

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

// ---------------------------------------------------------------- global-dedup post-steps (one at a time)
class PostQueue {
public:
    explicit PostQueue(const Options& o) : o_(o), own_db_(o.out + "\\" + o.prefix + "_seen.sqlite3") {}
    void start() {
        if (o_.global_dedup) thread_ = std::thread([this] { run(); });
    }
    void push(const std::string& base) {
        if (!o_.global_dedup) return;
        std::lock_guard<std::mutex> lock(m_);
        q_.push_back(base);
        cv_.notify_one();
    }
    void finish() {  // runs everything still queued, then ends the thread
        if (!thread_.joinable()) return;
        {
            std::lock_guard<std::mutex> lock(m_);
            closing_ = true;
            if (!q_.empty() || busy_) say("waiting for %zu global-dedup post-step(s)", q_.size() + (busy_ ? 1 : 0));
        }
        cv_.notify_one();
        thread_.join();
    }
    int failures() const { return failures_; }
    int done() const { return done_; }

private:
    void run() {
        for (;;) {
            std::string base;
            {
                std::unique_lock<std::mutex> lock(m_);
                cv_.wait(lock, [&] { return closing_ || !q_.empty(); });
                if (q_.empty()) return;
                base = q_.front();
                q_.pop_front();
                busy_ = true;
            }
            run_one(base);
            std::lock_guard<std::mutex> lock(m_);
            busy_ = false;
        }
    }
    static long long json_int(const std::string& text, const char* key) {
        const std::string k = std::string("\"") + key + "\": ";
        const std::size_t p = text.find(k);
        return p == std::string::npos ? -1 : std::atoll(text.c_str() + p + k.size());
    }
    void run_one(const std::string& base) {
        const std::string log_path = base + ".dedup.log";
        SECURITY_ATTRIBUTES sa{sizeof(sa), nullptr, TRUE};
        HANDLE log = CreateFileA(log_path.c_str(), FILE_APPEND_DATA, FILE_SHARE_READ, &sa, OPEN_ALWAYS,
                                 FILE_ATTRIBUTE_NORMAL, nullptr);
        HANDLE nul = CreateFileA("NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, &sa, OPEN_EXISTING, 0, nullptr);
        std::string err;
        bool ok = log != INVALID_HANDLE_VALUE && nul != INVALID_HANDLE_VALUE;
        if (!ok) err = "cannot open " + log_path + " or NUL: " + win_error(GetLastError());
        const std::string cmd = quote(o_.post_python) + " -I -B " + quote(o_.post_script) + " --shard " + quote(base) +
                                " --live-db " + quote(o_.dedup_db) + " --own-db " + quote(own_db_);
        PROCESS_INFORMATION pi{};
        const auto t0 = std::chrono::steady_clock::now();
        if (ok) ok = spawn(cmd, nul, log, log, CREATE_SUSPENDED | CREATE_NO_WINDOW | BELOW_NORMAL_PRIORITY_CLASS, pi, err);
        if (ok) ok = adopt_child(pi, 0, err);  // inherits the driver's CPUs
        if (log != INVALID_HANDLE_VALUE) CloseHandle(log);
        if (nul != INVALID_HANDLE_VALUE) CloseHandle(nul);
        if (!ok) {
            ++failures_;
            say("ERROR: global-dedup post-step for %s did not start: %s", base.c_str(), err.c_str());
            return;
        }
        DWORD code = 1;
        if (WaitForSingleObject(pi.hProcess, static_cast<DWORD>(o_.post_timeout_minutes * 60000)) != WAIT_OBJECT_0) {
            TerminateProcess(pi.hProcess, 1);  // own child past its time limit
            WaitForSingleObject(pi.hProcess, 10000);
            say("ERROR: global-dedup post-step for %s ran over %.0f minutes: ended", base.c_str(), o_.post_timeout_minutes);
        } else {
            GetExitCodeProcess(pi.hProcess, &code);
        }
        CloseHandle(pi.hProcess);
        const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        if (code != 0) {
            ++failures_;
            say("ERROR: global-dedup post-step for %s failed (exit code %lu, log %s); --resume runs it again", base.c_str(),
                static_cast<unsigned long>(code), log_path.c_str());
            return;
        }
        ++done_;
        std::ifstream f(base + ".dedup.json");
        const std::string text((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
        say("global dedup %s: read %lld, kept %lld (duplicates: live DB %lld, own DB %lld, inside %lld) in %.0f s",
            base.c_str(), json_int(text, "read"), json_int(text, "kept"), json_int(text, "dup_live"),
            json_int(text, "dup_own"), json_int(text, "dup_self"), secs);
    }
    const Options& o_;
    const std::string own_db_;
    std::thread thread_;
    std::mutex m_;
    std::condition_variable cv_;
    std::deque<std::string> q_;
    bool closing_ = false, busy_ = false;
    std::atomic<int> failures_{0}, done_{0};
};

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

// FPOS board of a FEN placement (a1 = 0, nibble per square, 1..6 white P N B R Q K, 7..12 black): for --resume
bool fen_to_fpos(const std::string& fen, std::array<std::uint8_t, 32>& out, bool& black) {
    static const char* codes = "PNBRQKpnbrqk";
    out.fill(0);
    int rank = 7, file = 0;
    std::size_t i = 0;
    for (; i < fen.size() && fen[i] != ' '; ++i) {
        const char c = fen[i];
        if (c == '/') {
            if (file != 8 || rank == 0) return false;
            --rank;
            file = 0;
        } else if (c >= '1' && c <= '8') {
            file += c - '0';
        } else {
            const char* p = std::strchr(codes, c);
            if (!p || file > 7) return false;
            const int s = rank * 8 + file++, code = static_cast<int>(p - codes) + 1;
            out[static_cast<std::size_t>(s >> 1)] |= static_cast<std::uint8_t>((s & 1) ? (code << 4) : code);
        }
        if (file > 8) return false;
    }
    if (rank != 0 || file != 8 || i + 1 >= fen.size()) return false;
    black = fen[i + 1] == 'b';
    return fen[i + 1] == 'w' || black;
}

class Output {
public:
    Output(const Options& o, PostQueue& post) : o_(o), post_(post) {
        if (o_.dedup && !o_.dedup_exact) table_.assign(static_cast<std::size_t>(o_.dedup_mb) * 1024 * 1024 / 8, 0);
    }
    // Scans --out: the next shard number follows the highest one of this prefix; with --resume every .txt.part left
    // by a hard kill is salvaged (complete lines kept, .pos rebuilt) and finished shards without a global-dedup result
    // are queued for the post-step again.
    bool init() {
        std::lock_guard<std::mutex> lock(m_);
        std::vector<int> parts, finished;
        WIN32_FIND_DATAA fd;
        const std::string head = o_.prefix + "_";
        HANDLE h = FindFirstFileA((o_.out + "\\" + head + "*").c_str(), &fd);
        if (h != INVALID_HANDLE_VALUE) {
            do {
                const std::string name = fd.cFileName;
                std::size_t k = head.size(), d = k;
                while (d < name.size() && name[d] >= '0' && name[d] <= '9') ++d;
                if (d == k || d >= name.size() || name[d] != '.') continue;
                const int no = std::atoi(name.substr(k, d - k).c_str());
                const std::string ext = name.substr(d + 1);
                file_no_ = std::max(file_no_, no);
                if (ext == "txt.part") parts.push_back(no);
                if (ext == "txt") finished.push_back(no);
            } while (FindNextFileA(h, &fd));
            FindClose(h);
        }
        std::sort(parts.begin(), parts.end());
        std::sort(finished.begin(), finished.end());
        for (int no : finished)
            if (!exists(base_of(no) + ".dedup.json")) post_.push(base_of(no));
        for (int no : parts) {
            if (!o_.resume) return io("unexpected " + base_of(no) + ".txt.part");
            if (!salvage(base_of(no))) return false;
        }
        return true;
    }
    // returns the number of records kept, -1 when the output failed (the run stops)
    long long add_game(const std::vector<Record>& recs, int white_result2) {
        std::lock_guard<std::mutex> lock(m_);
        if (failed_) return -1;
        static const char* res[3] = {"0.0", "0.5", "1.0"};
        long long kept = 0;
        for (const Record& r : recs) {
            if (o_.dedup && is_duplicate(hash_key(four_fields(r.fen)))) continue;
            if (!text_.is_open() && !open_next()) return -1;
            text_buf_ += r.fen;
            text_buf_ += " | ";
            text_buf_ += std::to_string(r.cp);
            text_buf_ += " | ";
            text_buf_ += res[white_result2];
            text_buf_ += '\n';
            if (o_.pos) {
                pos_buf_.append(reinterpret_cast<const char*>(r.board.data()), r.board.size());
                scores_.push_back(static_cast<std::int16_t>(r.cp));
                metas_.push_back(static_cast<std::uint8_t>((r.black ? 1 : 0) | (white_result2 << 1)));
            }
            ++kept;
            ++total_;
            if (++lines_ >= o_.lines_per_file && !finish()) return -1;
        }
        if (text_buf_.size() >= (std::size_t{1} << 20) && !flush()) return -1;
        return kept;
    }
    void tick(double now_s) {  // main thread: time-based flush and rotation
        std::lock_guard<std::mutex> lock(m_);
        now_ = now_s;
        if (failed_ || !text_.is_open()) return;
        if (o_.rotate_minutes > 0 && now_s - opened_s_ >= o_.rotate_minutes * 60) (void)finish();
        else if (now_s - flushed_s_ >= o_.flush_seconds) (void)flush();
    }
    bool close() {
        std::lock_guard<std::mutex> lock(m_);
        return !failed_ && finish();
    }
    long long total() {
        std::lock_guard<std::mutex> lock(m_);
        return total_;
    }
    long long shards() {
        std::lock_guard<std::mutex> lock(m_);
        return shards_;
    }

private:
    std::string base_of(int no) const {
        char name[160];
        std::snprintf(name, sizeof(name), "%s_%03d", o_.prefix.c_str(), no);
        return o_.out + "\\" + name;
    }
    bool io(const std::string& what) {
        failed_ = true;
        fatal_io(what);
        return false;
    }
    // exact: every key of the run; bounded: slot = key mod size holds the newest fingerprint (0 = empty)
    bool is_duplicate(const Hash128& h) {
        if (o_.dedup_exact) return !seen_.insert(h).second;
        const std::uint64_t fp = h.b | 1ULL;
        std::uint64_t& slot = table_[static_cast<std::size_t>(h.a % table_.size())];
        if (slot == fp) return true;
        slot = fp;
        return false;
    }
    std::string info_text(const std::string& base, std::uint64_t n) const {
        std::ostringstream s;
        s << "source=" << base << ".txt\nlines=" << n << "\nrecords=" << n << "\nbad=0\ngenerator=" << Version
          << "\nseed=" << o_.seed << "\nrun_dedup="
          << (!o_.dedup ? "off" : o_.dedup_exact ? "exact" : "bounded " + std::to_string(o_.dedup_mb) + " MB") << "\n";
        if (o_.global_dedup)
            s << "global_dedup=post-step " << base << ".dedup.txt / .dedup.pos (live DB " << o_.dedup_db << " + own DB)\n";
        else
            s << "global_dedup=OFF (data change: positions already in the live hash DB are not removed)\n";
        return s.str();
    }
    bool open_next() {
        static const char* exts[] = {".txt", ".txt.part", ".txt.md5", ".pos", ".pos.part", ".pos.info", ".dedup.txt", ".dedup.json"};
        for (;;) {
            base_ = base_of(++file_no_);
            bool taken = false;
            for (const char* e : exts) taken = taken || exists(base_ + e);
            if (!taken) break;
        }
        if (!text_.open(base_ + ".txt.part", CREATE_NEW)) return io(text_.error());
        if (o_.pos) {
            char header[16] = {'F', 'P', 'O', 'S', 1, 0, 0, 0};  // u32 version 1, u64 count patched at the end
            if (!pos_.open(base_ + ".pos.part", CREATE_NEW) || !pos_.write(header, sizeof(header))) return io(pos_.error());
        }
        lines_ = 0;
        opened_s_ = flushed_s_ = now_;
        return true;
    }
    bool flush() {  // only called at game boundaries
        if (!text_buf_.empty() && !text_.write(text_buf_.data(), text_buf_.size())) return io(text_.error());
        text_buf_.clear();
        if (!pos_buf_.empty() && !pos_.write(pos_buf_.data(), pos_buf_.size())) return io(pos_.error());
        pos_buf_.clear();
        flushed_s_ = now_;
        return true;
    }
    // FPOS tail (scores, metas), the record count at offset 8, .pos.info, then .pos.part -> .pos, .txt.part -> .txt:
    // a final .txt means a complete shard
    bool finish_pos(File& pos, std::vector<std::int16_t>& scores, std::vector<std::uint8_t>& metas, const std::string& base) {
        const std::uint64_t n = scores.size();
        if (!pos.write(scores.data(), n * 2) || !pos.write(metas.data(), n) || !pos.seek(8) || !pos.write(&n, 8) ||
            !pos.sync() || !pos.close())
            return io(pos.error());
        std::string err;
        if (!write_small(base + ".pos.info", info_text(base, n), err) || !rename_new(base + ".pos.part", base + ".pos", err))
            return io(err);
        scores.clear();
        metas.clear();
        return true;
    }
    bool finish() {
        if (!text_.is_open()) return true;
        if (!flush()) return false;
        const long long n = lines_;
        if (o_.pos && !finish_pos(pos_, scores_, metas_, base_)) return false;
        if (!text_.sync() || !text_.close()) return io(text_.error());
        std::string err;
        if (!rename_new(base_ + ".txt.part", base_ + ".txt", err)) return io(err);
        ++shards_;
        say("finished %s.txt: %lld lines%s", base_.c_str(), n, o_.pos ? " (+ .pos, .pos.info)" : "");
        post_.push(base_);
        return true;
    }
    // .txt.part of a killed run: keep every complete line, rebuild the .pos from the text, publish the shard
    bool salvage(const std::string& base) {
        File t;
        if (!t.open(base + ".txt.part", OPEN_EXISTING)) return io(t.error());
        const bool final_pos = exists(base + ".pos");
        const bool build_pos = o_.pos && !final_pos;
        File p;
        if (build_pos) {
            char header[16] = {'F', 'P', 'O', 'S', 1, 0, 0, 0};
            if (!p.open(base + ".pos.part", CREATE_ALWAYS) || !p.write(header, sizeof(header))) return io(p.error());
        }
        std::vector<char> buf(1 << 20);
        std::string carry, boards;
        std::vector<std::int16_t> scores;
        std::vector<std::uint8_t> metas;
        std::uint64_t offset = 0, good_end = 0, n = 0;
        for (;;) {
            DWORD got = 0;
            if (!t.read(buf.data(), static_cast<DWORD>(buf.size()), got)) return io(t.error());
            if (got == 0) break;
            carry.append(buf.data(), got);
            std::size_t start = 0;
            for (std::size_t nl; (nl = carry.find('\n', start)) != std::string::npos; start = nl + 1) {
                const std::string line = carry.substr(start, nl - start);
                const std::size_t a = line.find(" | "), b = a == std::string::npos ? a : line.find(" | ", a + 3);
                std::array<std::uint8_t, 32> board{};
                bool black = false;
                const std::string res = b == std::string::npos ? "" : line.substr(b + 3);
                const int r2 = res == "0.0" ? 0 : res == "0.5" ? 1 : res == "1.0" ? 2 : -1;
                if (r2 < 0 || !fen_to_fpos(line.substr(0, a), board, black))
                    return io("salvage " + base + ".txt.part: bad line " + std::to_string(n + 1) + ": " + line);
                if (build_pos) {
                    boards.append(reinterpret_cast<const char*>(board.data()), board.size());
                    scores.push_back(static_cast<std::int16_t>(std::atoi(line.c_str() + a + 3)));
                    metas.push_back(static_cast<std::uint8_t>((black ? 1 : 0) | (r2 << 1)));
                    if (boards.size() >= (std::size_t{1} << 20)) {
                        if (!p.write(boards.data(), boards.size())) return io(p.error());
                        boards.clear();
                    }
                }
                ++n;
                good_end = offset + nl + 1;
            }
            carry.erase(0, start);
            offset += start;
        }
        const std::uint64_t dropped = offset + carry.size() - good_end;
        if (!t.truncate_at(good_end) || !t.sync() || !t.close()) return io(t.error());
        if (build_pos && ((!boards.empty() && !p.write(boards.data(), boards.size())) || !finish_pos(p, scores, metas, base)))
            return io(p.error());
        if (final_pos) {  // killed between the .pos and the .txt rename: the .pos must hold exactly these lines
            File q;
            char header[16] = {0};
            DWORD got = 0;
            std::uint64_t pn = 0;
            if (!q.open(base + ".pos", OPEN_EXISTING) || !q.read(header, sizeof(header), got) || !q.close())
                return io(q.error());
            std::memcpy(&pn, header + 8, 8);
            if (got != sizeof(header) || pn != n)
                return io("salvage " + base + ": .pos holds " + std::to_string(pn) + " records, the text " + std::to_string(n));
        }
        std::string err;
        if (!rename_new(base + ".txt.part", base + ".txt", err)) return io(err);
        ++shards_;
        say("salvaged %s.txt.part: %llu complete lines kept, %llu bytes of an unfinished line dropped%s", base.c_str(),
            static_cast<unsigned long long>(n), static_cast<unsigned long long>(dropped), build_pos ? ", .pos rebuilt" : "");
        post_.push(base);
        return true;
    }

    const Options& o_;
    PostQueue& post_;
    std::mutex m_;
    std::unordered_set<Hash128, Hash128Hasher> seen_;
    std::vector<std::uint64_t> table_;
    File text_, pos_;
    std::string text_buf_, pos_buf_, base_;
    std::vector<std::int16_t> scores_;
    std::vector<std::uint8_t> metas_;
    long long lines_ = 0, total_ = 0, shards_ = 0;
    int file_no_ = 0;
    bool failed_ = false;
    double now_ = 0, opened_s_ = 0, flushed_s_ = 0;
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
    std::atomic<long long> games{0}, candidates{0}, kept{0}, errors{0}, attempts{0}, restarts{0}, timeouts{0};
    // searched positions and why one was not recorded (first matching reason, in this order)
    std::atomic<long long> searches{0}, not_bound{0}, not_check{0}, not_noisy{0}, not_mate{0}, not_big{0};
    std::atomic<long long> search_us{0};
    std::atomic<int> dead_workers{0};
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

bool handshake(Engine& e, const Options& o, EngineSlot& slot) {
    Exchange x(slot, o.engine_timeout);
    if (!e.send("uci") || !e.wait_for("uciok")) return false;
    if (!e.send("setoption name Threads value 1") || !e.send("setoption name Hash value " + std::to_string(o.hash)) ||
        !e.send(std::string("setoption name OwnBook value ") + (o.own_book ? "true" : "false")) || !e.send("isready"))
        return false;
    return e.wait_for("readyok");
}

bool search(Engine& e, const Game& g, int nodes, Reply& r, Stats& st, EngineSlot& slot, double timeout) {
    std::string cmd = "position startpos";
    if (!g.moves.empty()) {
        cmd += " moves";
        for (const std::string& m : g.moves) {
            cmd += ' ';
            cmd += m;
        }
    }
    Exchange x(slot, timeout);
    if (!e.send(cmd)) return false;
    const auto t0 = std::chrono::steady_clock::now();
    if (!e.send("go nodes " + std::to_string(nodes))) return false;
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

enum class GameEnd { Finished, Skipped, Stopped, EngineFailed, OpeningsDone };

// one game exactly as forge_selfplay.py's play_game(); `result` = White's result * 2 when Finished
GameEnd play_one(Engine& e, const Options& o, Game& g, std::mt19937_64& rng,
                 const std::vector<std::vector<std::string>>& openings, std::atomic<std::size_t>& next_opening,
                 EngineSlot& slot, Stats& st, std::vector<Record>& recs, int& result) {
    ++st.attempts;
    g.reset();
    recs.clear();
    const std::vector<std::string>* book = nullptr;
    if (!openings.empty()) {
        const std::size_t k = next_opening.fetch_add(1);
        if (k >= openings.size()) return GameEnd::OpeningsDone;
        book = &openings[k];
    }
    const int plies = book ? static_cast<int>(book->size()) : o.opening_plies;
    for (int i = 0; i < plies; ++i) {
        if (terminal(g, o.max_ply) >= 0) return GameEnd::Skipped;
        if (book) {
            const auto m = g.board.parse_uci((*book)[static_cast<std::size_t>(i)]);
            if (!m) return GameEnd::Skipped;
            g.push(*m);
        } else {
            const MoveList legal = g.board.legal_moves();
            g.push(legal[static_cast<std::size_t>(rng() % legal.size())]);
        }
    }
    if (terminal(g, o.max_ply) >= 0) return GameEnd::Skipped;  // as play_game: no samples
    {
        Exchange x(slot, o.engine_timeout);
        if (!e.send("ucinewgame") || !e.send("isready") || !e.wait_for("readyok")) return GameEnd::EngineFailed;
    }
    int winner = 0, streak = 0;  // winner: +1 White, -1 Black, 0 none
    for (;;) {
        result = terminal(g, o.max_ply);
        if (result >= 0) return GameEnd::Finished;
        if (g_stop) return GameEnd::Stopped;
        Reply r;
        const int budget = (o.check_nodes > 0 && g.board.in_check()) ? o.check_nodes : o.nodes;
        if (!search(e, g, budget, r, st, slot, o.engine_timeout)) return GameEnd::EngineFailed;
        const auto mv = g.board.parse_uci(r.best);
        if (!mv || !r.has_score) {  // python: RuntimeError (no score / illegal move)
            ++st.errors;
            return GameEnd::Skipped;
        }
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
        if (result >= 0) return GameEnd::Finished;
        if (streak >= o.adjudicate_plies) {
            result = winner > 0 ? 2 : 0;
            return GameEnd::Finished;
        }
    }
}

// CPU mask: with more CPUs than workers each worker gets its own contiguous slice (CPUs 12-15 and 2 workers ->
// 12-13 and 14-15: one physical core each with SMT), with as many workers as CPUs one CPU each, with fewer CPUs
// than workers (or one worker) every worker gets all of them (the live script pins all workers to all CPUs).
DWORD_PTR worker_mask(int id, const Options& o) {
    DWORD_PTR mask = 0;
    const std::size_t n = o.cpus.size(), w = static_cast<std::size_t>(o.workers);
    if (w > 1 && w <= n) {
        const std::size_t slice = n / w, first = static_cast<std::size_t>(id) * slice;
        for (std::size_t k = first; k < first + slice; ++k) mask |= static_cast<DWORD_PTR>(1) << o.cpus[k];
    } else {
        for (int c : o.cpus) mask |= static_cast<DWORD_PTR>(1) << c;
    }
    return mask;
}

void worker(int id, const Options& o, Output& out, Stats& st, const std::vector<std::vector<std::string>>& openings,
            std::atomic<std::size_t>& next_opening, EngineSlot& slot) {
    const DWORD_PTR mask = worker_mask(id, o);
    std::mt19937_64 rng(o.seed * 1000003ULL + static_cast<std::uint64_t>(id));
    Engine e;
    Game g;
    std::vector<Record> recs;
    long long my_games = 0;
    int failures = 0;  // engine failures since the last finished game
    bool gave_up = false;
    while (!g_stop) {
        if (!e.running()) {
            if (failures > o.max_restarts) {
                gave_up = true;
                break;
            }
            std::string err;
            if (e.start(o, mask, slot, err) && handshake(e, o, slot)) {
                say("worker %d: engine PID %lu, affinity 0x%llx, %s%s", id + 1, static_cast<unsigned long>(e.pid()),
                    static_cast<unsigned long long>(mask), o.idle ? "Idle" : "BelowNormal", failures ? " (restarted)" : "");
            } else {
                if (e.running()) {
                    err = slot.killed ? "no uciok/readyok within the timeout" : "the engine closed its pipe during uci/isready";
                    e.stop(slot);
                }
                ++failures;
                say("ERROR: worker %d: engine start failed: %s (failure %d in a row, limit %d)", id + 1, err.c_str(),
                    failures, o.max_restarts + 1);
                for (int i = 0; i < 20 && !g_stop; ++i) Sleep(100);
                continue;
            }
        }
        if (o.games_per_worker && my_games >= o.games_per_worker) break;
        int result = -1;
        const GameEnd end = play_one(e, o, g, rng, openings, next_opening, slot, st, recs, result);
        if (end == GameEnd::OpeningsDone || end == GameEnd::Stopped) break;
        if (end == GameEnd::Skipped) continue;
        if (end == GameEnd::EngineFailed) {
            const bool killed = slot.killed;
            e.stop(slot);
            ++failures;
            ++st.restarts;
            say("worker %d: %s; game dropped, engine restart (failure %d in a row, limit %d)", id + 1,
                killed ? "engine killed after no answer within the timeout" : "engine pipe closed (the engine ended)",
                failures, o.max_restarts + 1);
            continue;
        }
        failures = 0;
        ++my_games;
        ++st.games;
        st.candidates += static_cast<long long>(recs.size());
        const long long kept = out.add_game(recs, result);
        if (kept < 0) break;  // the output failed: g_stop is set
        st.kept += kept;
    }
    if (e.running()) e.stop(slot);
    if (gave_up) {
        ++st.dead_workers;
        say("ERROR: worker %d gives up after %d engine failures in a row", id + 1, failures);
    }
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

struct Mem {
    double ws = 0, peak = 0, priv = 0;
};
Mem mem_of(HANDLE p) {
    PROCESS_MEMORY_COUNTERS_EX c{};
    c.cb = sizeof(c);
    if (!p || !GetProcessMemoryInfo(p, reinterpret_cast<PROCESS_MEMORY_COUNTERS*>(&c), sizeof(c))) return {};
    return {c.WorkingSetSize / 1048576.0, c.PeakWorkingSetSize / 1048576.0, c.PrivateUsage / 1048576.0};
}
std::string mem_report(std::vector<std::unique_ptr<EngineSlot>>& slots) {
    const Mem d = mem_of(GetCurrentProcess());
    double ews = 0, epriv = 0;
    for (auto& s : slots) {
        std::lock_guard<std::mutex> lock(s->m);
        const Mem m = mem_of(s->process);
        ews += m.ws;
        epriv += m.priv;
    }
    double job_peak = 0;
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION ji{};
    if (g_job && QueryInformationJobObject(g_job, JobObjectExtendedLimitInformation, &ji, sizeof(ji), nullptr))
        job_peak = ji.PeakJobMemoryUsed / 1048576.0;
    char buf[256];
    std::snprintf(buf, sizeof(buf), "RSS driver %.1f MB (peak %.1f, private %.1f), engines %.1f MB (private %.1f), job peak commit %.1f MB",
                  d.ws, d.peak, d.priv, ews, epriv, job_peak);
    return buf;
}

BOOL WINAPI on_console(DWORD type) {  // Ctrl+C / Ctrl+Break / console close: stop cleanly
    g_stop = true;
    if (type == CTRL_CLOSE_EVENT || type == CTRL_LOGOFF_EVENT || type == CTRL_SHUTDOWN_EVENT) Sleep(4000);
    return TRUE;
}

std::string exe_dir() {
    char path[MAX_PATH] = {0};
    const DWORD n = GetModuleFileNameA(nullptr, path, MAX_PATH);
    std::string s(path, n);
    const std::size_t k = s.find_last_of("\\/");
    return k == std::string::npos ? "." : s.substr(0, k);
}

int usage(const char* why) {
    std::fprintf(stderr, "%s\nusage: forge_selfplay_fast --engine E --out DIR [options] (see the source header)\n", why);
    return 2;
}

}  // namespace

int main(int argc, char** argv) {
    Options o;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string k = argv[i];
            if (k == "--pos") { o.pos = true; continue; }
            if (k == "--no-dedup") { o.dedup = false; continue; }
            if (k == "--resume") { o.resume = true; continue; }
            if (k == "--no-global-dedup") { o.global_dedup = false; continue; }
            if (i + 1 >= argc) return usage(("option " + k + " needs a value").c_str());
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
            else if (k == "--seed") { o.seed = std::stoull(v); o.seed_given = true; }
            else if (k == "--openings") o.openings = v;
            else if (k == "--prefix") o.prefix = v;
            else if (k == "--own-book") o.own_book = v == "true";
            else if (k == "--progress-seconds") o.progress_seconds = std::stod(v);
            else if (k == "--opening-plies") o.opening_plies = std::stoi(v);
            else if (k == "--max-ply") o.max_ply = std::stoi(v);
            else if (k == "--adjudicate-cp") o.adjudicate_cp = std::stoi(v);
            else if (k == "--adjudicate-plies") o.adjudicate_plies = std::stoi(v);
            else if (k == "--max-score") o.max_score = std::stoi(v);
            else if (k == "--lines-per-file") o.lines_per_file = std::max(1LL, std::stoll(v));
            else if (k == "--rotate-minutes") o.rotate_minutes = std::stod(v);
            else if (k == "--flush-seconds") o.flush_seconds = std::stod(v);
            else if (k == "--stop-file") o.stop_file = v;
            else if (k == "--engine-timeout") o.engine_timeout = std::max(1.0, std::stod(v));
            else if (k == "--max-restarts") o.max_restarts = std::max(0, std::stoi(v));
            else if (k == "--priority") o.idle = v != "belownormal";
            else if (k == "--dedup") o.dedup_exact = v == "exact";
            else if (k == "--dedup-mb") o.dedup_mb = std::max(1LL, std::stoll(v));
            else if (k == "--dedup-db") o.dedup_db = v;
            else if (k == "--post-python") o.post_python = v;
            else if (k == "--post-script") o.post_script = v;
            else if (k == "--post-timeout-minutes") o.post_timeout_minutes = std::max(1.0, std::stod(v));
            else if (k == "--job-memory-mb") o.job_memory_mb = std::max(0LL, std::stoll(v));
            else if (k == "--test-exit-after-seconds") o.test_exit_after_seconds = std::stod(v);
            else if (k == "--test-fail-write-after") o.test_fail_write_after = std::stoll(v);
            else return usage(("unknown option " + k).c_str());
        }
    } catch (const std::exception&) {
        return usage("bad option value");
    }
    if (o.engine.empty() || o.out.empty() || o.workers < 1) return usage("--engine and --out are required");
    if (o.cpus.empty()) o.cpus = {12, 13, 14, 15};
    if (o.stop_file.empty()) o.stop_file = o.out + "\\STOP";
    if (o.post_script.empty()) o.post_script = exe_dir() + "\\dedup_against_db.py";
    g_fail_write_after = o.test_fail_write_after;
    if (!o.seed_given) {
        std::random_device rd;
        const std::uint64_t r = (static_cast<std::uint64_t>(rd()) << 32) ^ rd();
        const auto t = static_cast<std::uint64_t>(std::chrono::system_clock::now().time_since_epoch().count());
        o.seed = r ^ t ^ (static_cast<std::uint64_t>(GetCurrentProcessId()) * 0x9E3779B97F4A7C15ULL);
    }

    // the driver itself: BelowNormal, on the self-play CPUs, in a job object with its children
    DWORD_PTR all = 0;
    for (int c : o.cpus) {
        if (c < 0 || c >= 64) return usage("--cpus out of range");
        all |= static_cast<DWORD_PTR>(1) << c;
    }
    if (!SetPriorityClass(GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS))
        return usage(("SetPriorityClass: " + win_error(GetLastError())).c_str());
    if (!SetProcessAffinityMask(GetCurrentProcess(), all))
        return usage(("SetProcessAffinityMask: " + win_error(GetLastError())).c_str());
    std::string job_note;
    if (!make_job(o.job_memory_mb, job_note)) return usage(job_note.c_str());
    SetConsoleCtrlHandler(on_console, TRUE);

    // the output folder: new unless --resume, one driver at a time, the STOP file, the post-step tools
    const DWORD attr = GetFileAttributesA(o.out.c_str());
    if (attr != INVALID_FILE_ATTRIBUTES && !o.resume) return usage(("--out " + o.out + " exists: pass --resume to continue in it").c_str());
    if (attr != INVALID_FILE_ATTRIBUTES && !(attr & FILE_ATTRIBUTE_DIRECTORY)) return usage(("--out " + o.out + " is a file").c_str());
    if (attr == INVALID_FILE_ATTRIBUTES && !CreateDirectoryA(o.out.c_str(), nullptr))
        return usage(("cannot create --out " + o.out + ": " + win_error(GetLastError())).c_str());
    const std::string lock_path = o.out + "\\" + o.prefix + ".lock";
    HANDLE lock = CreateFileA(lock_path.c_str(), GENERIC_WRITE, 0, nullptr, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (lock == INVALID_HANDLE_VALUE) return usage(("another driver writes into " + o.out + " (" + lock_path + ": " + win_error(GetLastError()) + ")").c_str());
    if (exists(o.stop_file)) {
        say("STOP file %s exists: not starting (remove it to run)", o.stop_file.c_str());
        return 0;
    }
    if (o.global_dedup) {
        for (const std::string* p : {&o.dedup_db, &o.post_python, &o.post_script})
            if (!exists(*p)) return usage(("global dedup needs " + *p + " (or pass --no-global-dedup, a data change)").c_str());
    }
    const auto openings = o.openings.empty() ? std::vector<std::vector<std::string>>{} : load_openings(o.openings);

    say("%s: %d worker(s), CPUs %s, Threads=1, Hash=%d, OwnBook=%s; %d nodes/move; engine %s; out %s%s", Version,
        o.workers, [&] { std::string s; for (int c : o.cpus) s += (s.empty() ? "" : ",") + std::to_string(c); return s; }().c_str(),
        o.hash, o.own_book ? "true" : "false", o.nodes, o.engine.c_str(), o.out.c_str(), o.resume ? " (resume)" : "");
    say("seed=%llu (%s)", static_cast<unsigned long long>(o.seed), o.seed_given ? "--seed" : "random_device ^ time ^ pid");
    say("driver BelowNormal on mask 0x%llx; engines %s; %s", static_cast<unsigned long long>(all), o.idle ? "Idle" : "BelowNormal", job_note.c_str());
    say("shards: %lld lines or %.1f minutes, flush every %.1f s, STOP file %s; engine timeout %.0f s, %d restarts in a row",
        o.lines_per_file, o.rotate_minutes, o.flush_seconds, o.stop_file.c_str(), o.engine_timeout, o.max_restarts);
    if (o.global_dedup) say("global dedup: post-step %s after each shard (live DB %s, read only)", o.post_script.c_str(), o.dedup_db.c_str());
    else say("DATA CHANGE: global dedup OFF (--no-global-dedup): positions already in the live hash DB are kept; recorded in .pos.info");

    PostQueue post(o);
    Output out(o, post);
    post.start();
    if (!out.init()) {
        post.finish();
        return 4;
    }
    Stats st;
    std::atomic<std::size_t> next_opening{0};
    std::vector<std::unique_ptr<EngineSlot>> slots;
    for (int i = 0; i < o.workers; ++i) slots.push_back(std::make_unique<EngineSlot>());
    const auto t0 = std::chrono::steady_clock::now();
    std::vector<std::thread> pool;
    for (int i = 0; i < o.workers; ++i)
        pool.emplace_back(worker, i, std::cref(o), std::ref(out), std::ref(st), std::cref(openings), std::ref(next_opening),
                          std::ref(*slots[static_cast<std::size_t>(i)]));
    std::atomic<int> alive{o.workers};
    std::thread waiter([&] {
        for (auto& t : pool) t.join();
        alive = 0;
    });
    auto last = t0;
    double last_stop_check = 0;
    while (alive > 0) {
        Sleep(200);
        const auto now = std::chrono::steady_clock::now();
        const double el = std::chrono::duration<double>(now - t0).count();
        for (std::size_t i = 0; i < slots.size(); ++i) {  // watchdog: kill an engine that missed its deadline
            EngineSlot& s = *slots[i];
            if (s.deadline == 0 || now_ms() <= s.deadline) continue;
            std::lock_guard<std::mutex> lock(s.m);
            const long long d = s.deadline;
            if (!s.process || d == 0 || now_ms() <= d) continue;
            s.killed = true;
            TerminateProcess(s.process, 0xDEAD);  // own child that gave no answer within --engine-timeout
            s.deadline = 0;
            ++st.timeouts;
            say("worker %zu: engine PID %lu gave no answer for %.0f s: killed", i + 1, static_cast<unsigned long>(s.pid), o.engine_timeout);
        }
        out.tick(el);
        if (el - last_stop_check >= 1.0) {
            last_stop_check = el;
            if (!g_stop && exists(o.stop_file)) {
                say("STOP file %s found: stopping cleanly", o.stop_file.c_str());
                g_stop = true;
            }
        }
        if (o.max_minutes > 0 && el >= o.max_minutes * 60) g_stop = true;
        if (o.test_exit_after_seconds > 0 && el >= o.test_exit_after_seconds) {
            say("TEST HOOK --test-exit-after-seconds: hard exit now (simulates taskkill /F)");
            TerminateProcess(GetCurrentProcess(), 9);
        }
        if (std::chrono::duration<double>(now - last).count() >= o.progress_seconds || alive == 0) {
            last = now;
            const long long kept = out.total();
            say("Elapsed %.3f h: games=%lld positions=%lld positions/h=%.0f eligible=%lld errors=%lld restarts=%lld "
                "search=%.1f%% shards=%lld; %s",
                el / 3600, st.games.load(), kept, kept * 3600.0 / std::max(el, 1e-9), st.candidates.load(),
                st.errors.load(), st.restarts.load(), 100.0 * st.search_us.load() / 1e6 / (std::max(el, 1e-9) * o.workers),
                out.shards(), mem_report(slots).c_str());
        }
    }
    waiter.join();
    const bool closed = out.close();
    post.finish();
    const double el = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    const long long kept = out.total();
    say("searches=%lld not recorded: bound=%lld in_check=%lld capture_or_promotion=%lld mate=%lld abs_cp_over_max=%lld"
        " (games that did not finish are not counted as positions)",
        st.searches.load(), st.not_bound.load(), st.not_check.load(), st.not_noisy.load(), st.not_mate.load(),
        st.not_big.load());
    say("DONE: %.3f h, games=%lld positions=%lld positions/h=%.0f eligible=%lld errors=%lld dedup_removed=%lld "
        "restarts=%lld timeouts=%lld shards=%lld post_steps=%d post_failures=%d; %s",
        el / 3600, st.games.load(), kept, kept * 3600.0 / std::max(el, 1e-9), st.candidates.load(), st.errors.load(),
        st.candidates.load() - kept, st.restarts.load(), st.timeouts.load(), out.shards(), post.done(), post.failures(),
        mem_report(slots).c_str());
    int code = 0;
    if (g_io_failed || !closed) code = 4;
    else if (st.dead_workers == o.workers) code = 3;
    else if (st.dead_workers > 0) code = 5;
    else if (post.failures() > 0) code = 6;
    say("exit code %d%s", code, code == 3 ? " (every engine is dead)" : code == 4 ? " (output error)" : code == 5 ? " (some workers gave up)" : code == 6 ? " (a post-step failed)" : "");
    CloseHandle(lock);
    return code;
}
