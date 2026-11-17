#include "forge/board.hpp"

#include <atomic>
#include <cstdlib>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

namespace {

constexpr int kChunks = 4;
constexpr int kGamesPerChunk = 1000;
constexpr int kGames = kChunks * kGamesPerChunk;
constexpr std::int64_t kBaseMs = 10000;
constexpr std::int64_t kIncMs = 100;
constexpr int kOpenPlies = 8;

std::atomic<pid_t> g_pids[8]{};

void kill_children(int) {
    for (auto& slot : g_pids) {
        const pid_t pid = slot.load();
        if (pid > 0) kill(pid, SIGKILL);
    }
    _exit(130);
}

std::uint64_t mix(std::uint64_t& state) {
    state ^= state << 7;
    state ^= state >> 9;
    state ^= state << 8;
    return state;
}

std::string opening_fen(int chunk, int index) {
    for (int attempt = 0; attempt < 32; ++attempt) {
        forge::Board board;
        if (!board.set_fen(forge::Board::StandardStartFen)) continue;
        std::uint64_t state = 1600200ULL + static_cast<std::uint64_t>(chunk) * 1000003ULL +
                              static_cast<std::uint64_t>(index) * 97ULL + static_cast<std::uint64_t>(attempt) * 17ULL;
        bool terminal = false;
        for (int ply = 0; ply < kOpenPlies; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty() || board.is_repetition() || board.halfmove_clock() >= 100 ||
                board.is_insufficient_material()) {
                terminal = true;
                break;
            }
            const std::size_t pick = static_cast<std::size_t>(mix(state) % legal.size());
            forge::Undo undo;
            if (!board.make_move(legal[pick], undo)) {
                terminal = true;
                break;
            }
        }
        if (terminal) continue;
        if (board.legal_moves().empty() || board.is_repetition() || board.halfmove_clock() >= 100 ||
            board.is_insufficient_material()) {
            continue;
        }
        return board.fen();
    }
    return std::string(forge::Board::StandardStartFen);
}

char promo_letter(int promotion) {
    switch (promotion) {
    case forge::Knight:
        return 'N';
    case forge::Bishop:
        return 'B';
    case forge::Rook:
        return 'R';
    case forge::Queen:
        return 'Q';
    default:
        return 'Q';
    }
}

std::string san(const forge::Board& board, forge::Move move) {
    if (move.is_castle()) return (move.flags & forge::QueenCastle) != 0 ? "O-O-O" : "O-O";
    const int type = forge::piece_type(board.piece_at(move.from));
    const bool capture = move.is_capture();
    const std::string dest = forge::Board::move_to_uci(forge::Move{static_cast<std::uint8_t>(move.to),
                                                                    static_cast<std::uint8_t>(move.to), 0, 0})
                                 .substr(0, 2);
    std::string text;
    if (type == forge::Pawn) {
        if (capture) {
            text += static_cast<char>('a' + forge::file_of(move.from));
            text += 'x';
        }
        text += dest;
    } else {
        text += " PNBRQK"[type];
        bool any = false;
        bool same_file = false;
        bool same_rank = false;
        for (const forge::Move other : board.legal_moves()) {
            if (other.from == move.from || other.to != move.to) continue;
            if (forge::piece_type(board.piece_at(other.from)) != type) continue;
            any = true;
            if (forge::file_of(other.from) == forge::file_of(move.from)) same_file = true;
            if (forge::rank_of(other.from) == forge::rank_of(move.from)) same_rank = true;
        }
        if (any) {
            if (!same_file) text += static_cast<char>('a' + forge::file_of(move.from));
            else if (!same_rank) text += static_cast<char>('1' + forge::rank_of(move.from));
            else {
                text += static_cast<char>('a' + forge::file_of(move.from));
                text += static_cast<char>('1' + forge::rank_of(move.from));
            }
        }
        if (capture) text += 'x';
        text += dest;
    }
    if (move.is_promotion()) {
        text += '=';
        text += promo_letter(move.promotion);
    }
    forge::Board next = board;
    forge::Undo undo;
    if (next.make_move(move, undo)) {
        if (next.in_check()) text += next.legal_moves().empty() ? '#' : '+';
    }
    return text;
}

struct Engine {
    pid_t pid = -1;
    int to = -1;
    int from = -1;
    int slot = 0;
    std::string pending;
    std::string id_name;

    ~Engine() { stop(); }

    void stop() {
        if (pid > 0) {
            g_pids[slot].store(0);
            kill(pid, SIGKILL);
            int status = 0;
            waitpid(pid, &status, 0);
            pid = -1;
        }
        if (to >= 0) close(to);
        if (from >= 0) close(from);
        to = -1;
        from = -1;
        pending.clear();
    }

    bool start(const std::string& path, int pid_slot, bool node_share) {
        stop();
        int parent_to_child[2]{-1, -1};
        int child_to_parent[2]{-1, -1};
        if (pipe(parent_to_child) != 0 || pipe(child_to_parent) != 0) return false;
        const pid_t child = fork();
        if (child < 0) return false;
        if (child == 0) {
            dup2(parent_to_child[0], STDIN_FILENO);
            dup2(child_to_parent[1], STDOUT_FILENO);
            const int sink = open("/dev/null", O_WRONLY);
            if (sink >= 0) dup2(sink, STDERR_FILENO);
            for (int fd = 3; fd < 64; ++fd) close(fd);
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        close(parent_to_child[0]);
        close(child_to_parent[1]);
        pid = child;
        slot = pid_slot;
        g_pids[slot].store(pid);
        to = parent_to_child[1];
        from = child_to_parent[0];
        if (!send("uci\n")) return false;
        bool saw_uciok = false;
        for (;;) {
            std::string line;
            if (!read_line(line, 10000)) return false;
            if (line.rfind("id name ", 0) == 0) id_name = line.substr(8);
            if (line == "uciok") {
                saw_uciok = true;
                break;
            }
        }
        if (!saw_uciok) return false;
        const std::string share = node_share ? "true" : "false";
        if (!send("setoption name Threads value 1\n") || !send("setoption name Hash value 16\n") ||
            !send("setoption name OwnBook value false\n") ||
            !send("setoption name TmNodeShare value " + share + "\n") || !send("isready\n")) {
            return false;
        }
        return wait_ready(10000);
    }

    bool send(const std::string& text) const {
        const char* data = text.data();
        std::size_t left = text.size();
        while (left > 0) {
            const ssize_t wrote = write(to, data, left);
            if (wrote < 0) {
                if (errno == EINTR) continue;
                return false;
            }
            data += wrote;
            left -= static_cast<std::size_t>(wrote);
        }
        return true;
    }

    bool read_line(std::string& line, int timeout_ms) {
        for (;;) {
            const auto cut = pending.find('\n');
            if (cut != std::string::npos) {
                line = pending.substr(0, cut);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                pending.erase(0, cut + 1);
                return true;
            }
            pollfd pfd{};
            pfd.fd = from;
            pfd.events = POLLIN;
            const int got = poll(&pfd, 1, timeout_ms);
            if (got <= 0) return false;
            char block[4096];
            const ssize_t n = read(from, block, sizeof block);
            if (n <= 0) return false;
            pending.append(block, static_cast<std::size_t>(n));
        }
    }

    bool wait_ready(int timeout_ms) {
        for (;;) {
            std::string line;
            if (!read_line(line, timeout_ms)) return false;
            if (line == "readyok") return true;
        }
    }

    // Returns false when the engine produced no bestmove before timeout_ms.
    bool best_move(std::string& uci, int timeout_ms) {
        for (;;) {
            std::string line;
            if (!read_line(line, timeout_ms)) return false;
            if (line.rfind("bestmove ", 0) != 0) continue;
            std::istringstream input(line.substr(9));
            input >> uci;
            return !uci.empty();
        }
    }
};

enum class Ending { Checkmate, Stalemate, Fifty, Repetition, Material, Time, Illegal, Failure, PlyCap };

struct Played {
    double on_score = 0;
    bool on_flag = false;
    bool off_flag = false;
    bool ok = false;
    std::string pgn;
    std::string result;
    Ending ending = Ending::Failure;
};

const char* ending_name(Ending ending) {
    switch (ending) {
    case Ending::Checkmate:
        return "checkmate";
    case Ending::Stalemate:
        return "stalemate";
    case Ending::Fifty:
        return "50-move";
    case Ending::Repetition:
        return "repetition";
    case Ending::Material:
        return "insufficient material";
    case Ending::Time:
        return "time forfeit";
    case Ending::Illegal:
        return "illegal move";
    case Ending::Failure:
        return "engine failure";
    case Ending::PlyCap:
        return "ply cap";
    }
    return "engine failure";
}

Played play_game(Engine& on, Engine& off, const std::string& fen, bool on_white, int chunk, int round_no) {
    Played out;
    auto fail = [&](bool on_failed) {
        out.ok = true;
        out.ending = Ending::Failure;
        out.on_score = on_failed ? 0 : 1;
        out.result = on_white ? (on_failed ? "0-1" : "1-0") : (on_failed ? "1-0" : "0-1");
        return out;
    };
    if (!on.send("ucinewgame\nisready\n") || !on.wait_ready(10000)) return fail(true);
    if (!off.send("ucinewgame\nisready\n") || !off.wait_ready(10000)) return fail(false);

    forge::Board board;
    if (!board.set_fen(fen)) return fail(true);
    const std::string white_name = on_white ? "Forge TmNodeShare on" : "Forge TmNodeShare off";
    const std::string black_name = on_white ? "Forge TmNodeShare off" : "Forge TmNodeShare on";
    std::int64_t white_ms = kBaseMs;
    std::int64_t black_ms = kBaseMs;
    std::vector<std::string> sans;
    std::vector<std::string> uci_moves;
    Ending ending = Ending::PlyCap;
    std::string result = "1/2-1/2";
    bool on_flag = false;
    bool off_flag = false;

    auto finish_score = [&](double white_score) {
        out.on_score = on_white ? white_score : 1.0 - white_score;
    };

    for (int ply = 0; ply < 1000; ++ply) {
        const forge::MoveList legal = board.legal_moves();
        const bool white_turn = board.side_to_move() == forge::White;
        if (legal.empty()) {
            if (board.in_check()) {
                ending = Ending::Checkmate;
                result = white_turn ? "0-1" : "1-0";
                finish_score(white_turn ? 0 : 1);
            } else {
                ending = Ending::Stalemate;
                result = "1/2-1/2";
                finish_score(0.5);
            }
            break;
        }
        if (board.halfmove_clock() >= 100) {
            ending = Ending::Fifty;
            result = "1/2-1/2";
            finish_score(0.5);
            break;
        }
        if (board.is_repetition()) {
            ending = Ending::Repetition;
            result = "1/2-1/2";
            finish_score(0.5);
            break;
        }
        if (board.is_insufficient_material()) {
            ending = Ending::Material;
            result = "1/2-1/2";
            finish_score(0.5);
            break;
        }
        std::int64_t& clock = white_turn ? white_ms : black_ms;
        const bool on_turn = white_turn == on_white;
        if (clock <= 0) {
            ending = Ending::Time;
            result = white_turn ? "0-1" : "1-0";
            finish_score(white_turn ? 0 : 1);
            if (on_turn) on_flag = true;
            else off_flag = true;
            break;
        }
        Engine& mover = on_turn ? on : off;
        std::ostringstream position;
        position << "position fen " << fen;
        if (!uci_moves.empty()) {
            position << " moves";
            for (const std::string& move : uci_moves) position << ' ' << move;
        }
        position << '\n';
        std::ostringstream go;
        go << "go wtime " << white_ms << " btime " << black_ms << " winc " << kIncMs << " binc " << kIncMs << '\n';
        const auto started = std::chrono::steady_clock::now();
        if (!mover.send(position.str()) || !mover.send(go.str())) {
            return fail(on_turn);
        }
        std::string uci;
        const int budget = static_cast<int>(std::min<std::int64_t>(clock + 5000, 120000));
        if (!mover.best_move(uci, budget)) {
            ending = Ending::Time;
            result = white_turn ? "0-1" : "1-0";
            finish_score(white_turn ? 0 : 1);
            if (on_turn) on_flag = true;
            else off_flag = true;
            out.ending = ending;
            out.result = result;
            out.on_flag = on_flag;
            out.off_flag = off_flag;
            out.ok = true;
            break;
        }
        const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                                 std::chrono::steady_clock::now() - started)
                                 .count();
        if (elapsed > clock) {
            ending = Ending::Time;
            result = white_turn ? "0-1" : "1-0";
            finish_score(white_turn ? 0 : 1);
            if (on_turn) on_flag = true;
            else off_flag = true;
            break;
        }
        clock = clock - elapsed + kIncMs;
        const auto parsed = board.parse_uci(uci);
        if (!parsed || parsed->is_none()) {
            ending = Ending::Illegal;
            result = white_turn ? "0-1" : "1-0";
            finish_score(white_turn ? 0 : 1);
            break;
        }
        sans.push_back(san(board, *parsed));
        uci_moves.push_back(forge::Board::move_to_uci(*parsed));
        forge::Undo undo;
        if (!board.make_move(*parsed, undo)) {
            sans.pop_back();
            uci_moves.pop_back();
            ending = Ending::Illegal;
            result = white_turn ? "0-1" : "1-0";
            finish_score(white_turn ? 0 : 1);
            break;
        }
        ending = Ending::PlyCap;
        result = "1/2-1/2";
        finish_score(0.5);
    }

    std::ostringstream body;
    forge::Board cursor;
    if (!cursor.set_fen(fen)) return out;
    int number = cursor.fullmove_number();
    bool white_to_move = cursor.side_to_move() == forge::White;
    std::string moves;
    for (std::size_t i = 0; i < sans.size(); ++i) {
        if (white_to_move) {
            moves += std::to_string(number);
            moves += ". ";
            moves += sans[i];
            moves += ' ';
            white_to_move = false;
        } else {
            if (i == 0) {
                moves += std::to_string(number);
                moves += "... ";
            }
            moves += sans[i];
            moves += ' ';
            white_to_move = true;
            ++number;
        }
    }
    moves += result;

    std::ostringstream pgn;
    pgn << "[Event \"TmNodeShare clock screen\"]\n"
        << "[Site \"local\"]\n"
        << "[Date \"2026.11.14\"]\n"
        << "[Round \"" << round_no << "\"]\n"
        << "[White \"" << white_name << "\"]\n"
        << "[Black \"" << black_name << "\"]\n"
        << "[Result \"" << result << "\"]\n"
        << "[FEN \"" << fen << "\"]\n"
        << "[SetUp \"1\"]\n"
        << "[TimeControl \"10+0.1\"]\n"
        << "[Termination \"" << ending_name(ending) << "\"]\n"
        << "[Chunk \"" << (chunk + 1) << "\"]\n\n"
        << moves << "\n\n";
    out.pgn = pgn.str();
    out.result = result;
    out.ending = ending;
    out.on_flag = on_flag;
    out.off_flag = off_flag;
    out.ok = true;
    return out;
}

struct Tally {
    int wins = 0;
    int losses = 0;
    int draws = 0;
    int on_time = 0;
    int off_time = 0;
    int pent[5]{};
    int middle_wl = 0;
    int middle_dd = 0;
};

Tally g_tally;
Tally g_chunk[kChunks];
std::mutex g_mu;
std::mutex g_pgn_mu[kChunks];
std::ofstream g_pgn[kChunks];
std::atomic<int> g_chunk_done[kChunks]{};
std::atomic<int> g_done{0};
std::string g_id_name;
std::string g_engine_path;
std::string g_sha;
std::string g_out_dir;
int g_concurrency = 1;
int g_limit = kGames;

std::string sha256_of(const std::string& path) {
    const std::string command = "sha256sum " + path;
    FILE* pipe = popen(command.c_str(), "r");
    if (pipe == nullptr) return {};
    char buf[128]{};
    std::string out;
    if (fgets(buf, sizeof buf, pipe) != nullptr) out = buf;
    pclose(pipe);
    const auto space = out.find(' ');
    if (space != std::string::npos) out.resize(space);
    return out;
}

void write_block(std::ostream& out, const std::string& title, const Tally& tally) {
    const int games = tally.wins + tally.losses + tally.draws;
    const int pairs = tally.pent[0] + tally.pent[1] + tally.pent[2] + tally.pent[3] + tally.pent[4];
    out << title << "\n";
    out << "W-L-D " << tally.wins << "-" << tally.losses << "-" << tally.draws << "\n";
    out << "games " << games << "\n";
    out << "time losses on " << tally.on_time << " off " << tally.off_time << "\n";
    out << "pentanomial LL LD DD/WL WD WW " << tally.pent[0] << " " << tally.pent[1] << " " << tally.pent[2] << " "
        << tally.pent[3] << " " << tally.pent[4] << "\n";
    out << "middle split WL " << tally.middle_wl << " DD " << tally.middle_dd << "\n";
    if (games <= 0 || pairs <= 1) {
        out << "elo n/a\nLOS n/a\n";
        return;
    }
    const double points = tally.wins + 0.5 * tally.draws;
    const double score = points / games;
    if (!(score > 0.0 && score < 1.0)) {
        out << "elo inf score " << score << "\nLOS n/a\n";
        return;
    }
    double pair_mean = 0;
    for (int i = 0; i < 5; ++i) pair_mean += tally.pent[i] * (0.5 * i);
    pair_mean /= pairs;
    double pair_var = 0;
    for (int i = 0; i < 5; ++i) {
        const double diff = 0.5 * i - pair_mean;
        pair_var += tally.pent[i] * diff * diff;
    }
    pair_var /= static_cast<double>(pairs - 1);
    const double se_score = std::sqrt(pair_var / pairs) / 2.0;
    const double elo = -400.0 * std::log10(1.0 / score - 1.0);
    const double slope = (400.0 / std::log(10.0)) / (score * (1.0 - score));
    const double se_elo = slope * se_score;
    constexpr double kZ = 1.959963984540054;
    const double z = se_score > 0 ? (score - 0.5) / se_score : 0;
    const double los = 0.5 * (1.0 + std::erf(z / std::sqrt(2.0)));
    out << "score " << score << "\n";
    out << "elo " << elo << "\n";
    out << "elo95 " << (elo - kZ * se_elo) << " " << (elo + kZ * se_elo) << "\n";
    out << "LOS " << los << "\n";
}

void write_summary(const std::string& path) {
    Tally total;
    Tally chunks[kChunks];
    {
        const std::lock_guard<std::mutex> lock(g_mu);
        total = g_tally;
        for (int i = 0; i < kChunks; ++i) chunks[i] = g_chunk[i];
    }
    std::ofstream out(path, std::ios::trunc);
    out << "command ./clock_screen " << g_engine_path << " " << g_out_dir << "\n";
    out << "uci options both sides: setoption name Threads value 1; setoption name Hash value 16; "
           "setoption name OwnBook value false\n";
    out << "on side also: setoption name TmNodeShare value true\n";
    out << "off side also: setoption name TmNodeShare value false\n";
    out << "tc 10+0.1 (" << kBaseMs << " ms + " << kIncMs << " ms)\n";
    out << "concurrency " << g_concurrency << "\n";
    out << "chunks " << kChunks << " games " << kGames << "\n";
    out << "version " << g_id_name << "\n";
    out << "engine " << g_engine_path << "\n";
    out << "sha256 " << g_sha << "\n";
    out << "W-L-D is option on first\n";
    out << "pentanomial is pair scores of option on: 0, 0.5, 1, 1.5, 2\n";
    out << "elo95 is the paired pentanomial normal interval\n";
    write_block(out, "total", total);
    for (int i = 0; i < kChunks; ++i) {
        out << "chunk " << (i + 1) << " games done " << g_chunk_done[i].load() << "\n";
        write_block(out, "chunk " + std::to_string(i + 1), chunks[i]);
    }
}

void note_result(int chunk, int game_index, const Played& played, const std::array<Played, 2>& pending, bool pair_ready,
                 const Played& first, const Played& second) {
    {
        const std::lock_guard<std::mutex> lock(g_pgn_mu[chunk]);
        g_pgn[chunk] << played.pgn;
        g_pgn[chunk].flush();
    }
    {
        const std::lock_guard<std::mutex> lock(g_mu);
        auto add = [&](Tally& tally) {
            if (played.on_score > 0.75) ++tally.wins;
            else if (played.on_score < 0.25) ++tally.losses;
            else ++tally.draws;
            if (played.on_flag) ++tally.on_time;
            if (played.off_flag) ++tally.off_time;
        };
        add(g_tally);
        add(g_chunk[chunk]);
        if (pair_ready) {
            const double pair = first.on_score + second.on_score;
            int bin = static_cast<int>(std::lround(pair * 2.0));
            if (bin < 0) bin = 0;
            if (bin > 4) bin = 4;
            ++g_tally.pent[bin];
            ++g_chunk[chunk].pent[bin];
            if (bin == 2) {
                const bool wl = (first.on_score > 0.75 && second.on_score < 0.25) ||
                                (first.on_score < 0.25 && second.on_score > 0.75);
                if (wl) {
                    ++g_tally.middle_wl;
                    ++g_chunk[chunk].middle_wl;
                } else {
                    ++g_tally.middle_dd;
                    ++g_chunk[chunk].middle_dd;
                }
            }
        }
    }
    int wins = 0;
    int losses = 0;
    int draws = 0;
    {
        const std::lock_guard<std::mutex> lock(g_mu);
        wins = g_tally.wins;
        losses = g_tally.losses;
        draws = g_tally.draws;
    }
    const int finished = g_chunk_done[chunk].fetch_add(1) + 1;
    const int all = g_done.fetch_add(1) + 1;
    if (finished == kGamesPerChunk) {
        std::cout << "CHUNK_DONE " << (chunk + 1) << std::endl;
    }
    if (all % 25 == 0 || finished == kGamesPerChunk) {
        write_summary(g_out_dir + "/screen_summary.txt");
        std::cout << "progress " << all << " W " << wins << " L " << losses << " D " << draws << std::endl;
    }
    (void)game_index;
    (void)pending;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: clock_screen engine outdir\n";
        return 2;
    }
    g_engine_path = argv[1];
    g_out_dir = argv[2];
    if (argc >= 4) g_limit = std::max(2, std::atoi(argv[3]));
    if (g_limit > kGames) g_limit = kGames;
    if (g_limit % 2 != 0) --g_limit;
    const long cpus = sysconf(_SC_NPROCESSORS_ONLN);
    g_concurrency = static_cast<int>(std::max(1L, cpus / 2));
    g_sha = sha256_of(g_engine_path);
    struct sigaction action{};
    action.sa_handler = kill_children;
    sigaction(SIGINT, &action, nullptr);
    sigaction(SIGTERM, &action, nullptr);

    std::vector<std::string> fens[kChunks];
    for (int chunk = 0; chunk < kChunks; ++chunk) {
        fens[chunk].resize(kGamesPerChunk / 2);
        for (int i = 0; i < kGamesPerChunk / 2; ++i) fens[chunk][i] = opening_fen(chunk, i);
        g_pgn[chunk].open(g_out_dir + "/chunk" + std::to_string(chunk + 1) + ".pgn", std::ios::trunc);
        if (!g_pgn[chunk]) {
            std::cerr << "cannot write pgn\n";
            return 1;
        }
    }

    std::atomic<int> next{0};
    std::vector<std::array<Played, 2>> pair_slot(kGames / 2);
    std::mutex pair_mu;
    std::vector<std::thread> workers;
    workers.reserve(static_cast<std::size_t>(g_concurrency));
    for (int worker = 0; worker < g_concurrency; ++worker) {
        workers.emplace_back([&, worker]() {
            Engine on;
            Engine off;
            const int base = worker * 2;
            if (!on.start(g_engine_path, base, true) || !off.start(g_engine_path, base + 1, false)) {
                std::cerr << "engine start failed\n";
                kill_children(0);
            }
            if (g_id_name.empty()) g_id_name = on.id_name;
            for (;;) {
                const int game = next.fetch_add(1);
                if (game >= g_limit) break;
                const int chunk = game / kGamesPerChunk;
                const int within = game % kGamesPerChunk;
                const int opening = within / 2;
                const bool on_white = (within % 2) == 0;
                Played played = play_game(on, off, fens[chunk][opening], on_white, chunk, game + 1);
                if (played.ending == Ending::Failure) {
                    on.start(g_engine_path, base, true);
                    off.start(g_engine_path, base + 1, false);
                }
                bool ready = false;
                Played first;
                Played second;
                {
                    const std::lock_guard<std::mutex> lock(pair_mu);
                    const int pair = game / 2;
                    const int side = game % 2;
                    pair_slot[static_cast<std::size_t>(pair)][static_cast<std::size_t>(side)] = played;
                    const Played& a = pair_slot[static_cast<std::size_t>(pair)][0];
                    const Played& b = pair_slot[static_cast<std::size_t>(pair)][1];
                    ready = a.ok && b.ok;
                    if (ready) {
                        first = a;
                        second = b;
                    }
                }
                std::array<Played, 2> unused{};
                note_result(chunk, game, played, unused, ready, first, second);
            }
            on.stop();
            off.stop();
        });
    }
    for (auto& worker : workers) worker.join();
    write_summary(g_out_dir + "/screen_summary.txt");
    std::cout << "SCREEN_DONE" << std::endl;
    return 0;
}
