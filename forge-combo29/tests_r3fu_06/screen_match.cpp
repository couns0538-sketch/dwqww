#include "forge/board.hpp"

#include <openssl/sha.h>

#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <optional>
#include <poll.h>
#include <signal.h>
#include <sstream>
#include <string>
#include <string_view>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

namespace {

constexpr int kNodes = 50000;
constexpr int kMoveTimeoutMs = 30000;
constexpr int kReadyTimeoutMs = 10000;
constexpr int kMaxHalfmoves = 800;

std::string sha256_file(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    SHA256_CTX ctx;
    SHA256_Init(&ctx);
    char buf[1 << 16];
    while (in) {
        in.read(buf, sizeof buf);
        if (in.gcount() > 0) SHA256_Update(&ctx, buf, static_cast<std::size_t>(in.gcount()));
    }
    unsigned char out[SHA256_DIGEST_LENGTH];
    SHA256_Final(out, &ctx);
    static constexpr char hex[] = "0123456789abcdef";
    std::string text(SHA256_DIGEST_LENGTH * 2, '0');
    for (int i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
        text[static_cast<std::size_t>(i * 2)] = hex[out[i] >> 4];
        text[static_cast<std::size_t>(i * 2 + 1)] = hex[out[i] & 15];
    }
    return text;
}

class Engine {
public:
    Engine() = default;
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;
    ~Engine() { stop(); }

    bool start(const std::string& path) {
        stop();
        int to_child[2] = {-1, -1};
        int from_child[2] = {-1, -1};
        if (pipe(to_child) != 0 || pipe(from_child) != 0) return false;
        const pid_t child = fork();
        if (child < 0) return false;
        if (child == 0) {
            dup2(to_child[0], STDIN_FILENO);
            dup2(from_child[1], STDOUT_FILENO);
            const int sink = open("/dev/null", O_WRONLY);
            if (sink >= 0) dup2(sink, STDERR_FILENO);
            close(to_child[0]);
            close(to_child[1]);
            close(from_child[0]);
            close(from_child[1]);
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        close(to_child[0]);
        close(from_child[1]);
        pid_ = child;
        write_fd_ = to_child[1];
        read_fd_ = from_child[0];
        buffer_.clear();
        return true;
    }

    void stop() {
        if (write_fd_ >= 0) {
            send("quit");
            close(write_fd_);
            write_fd_ = -1;
        }
        if (read_fd_ >= 0) {
            close(read_fd_);
            read_fd_ = -1;
        }
        if (pid_ > 0) {
            int status = 0;
            const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
            while (waitpid(pid_, &status, WNOHANG) == 0 && std::chrono::steady_clock::now() < deadline) {
                usleep(10000);
            }
            if (waitpid(pid_, &status, WNOHANG) == 0) {
                kill(pid_, SIGKILL);
                waitpid(pid_, &status, 0);
            }
            pid_ = -1;
        }
    }

    bool send(const std::string& line) {
        const std::string text = line + '\n';
        std::size_t sent = 0;
        while (sent < text.size()) {
            const ssize_t n = ::write(write_fd_, text.data() + sent, text.size() - sent);
            if (n < 0) return false;
            sent += static_cast<std::size_t>(n);
        }
        return true;
    }

    std::optional<std::string> read_line(std::chrono::steady_clock::time_point deadline) {
        while (true) {
            const auto pos = buffer_.find('\n');
            if (pos != std::string::npos) {
                std::string line = buffer_.substr(0, pos);
                buffer_.erase(0, pos + 1);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                return line;
            }
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(
                                  deadline - std::chrono::steady_clock::now())
                                  .count();
            if (left <= 0) return std::nullopt;
            pollfd pfd{};
            pfd.fd = read_fd_;
            pfd.events = POLLIN;
            const int rc = poll(&pfd, 1, static_cast<int>(std::min<std::int64_t>(left, 1000)));
            if (rc < 0) return std::nullopt;
            if (rc == 0) continue;
            char tmp[4096];
            const ssize_t n = ::read(read_fd_, tmp, sizeof tmp);
            if (n <= 0) return std::nullopt;
            buffer_.append(tmp, static_cast<std::size_t>(n));
        }
    }

    bool wait_prefix(std::string_view prefix, int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        while (true) {
            const auto line = read_line(deadline);
            if (!line) return false;
            if (line->rfind(prefix, 0) == 0) return true;
        }
    }

    std::optional<std::string> wait_bestmove(int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        while (true) {
            const auto line = read_line(deadline);
            if (!line) return std::nullopt;
            if (line->rfind("bestmove ", 0) == 0) return *line;
        }
    }

private:
    pid_t pid_ = -1;
    int write_fd_ = -1;
    int read_fd_ = -1;
    std::string buffer_;
};

bool boot(Engine& engine, const std::string& path, bool option_on) {
    if (!engine.start(path)) return false;
    if (!engine.send("uci") || !engine.wait_prefix("uciok", kReadyTimeoutMs)) return false;
    if (!engine.send("setoption name Threads value 1")) return false;
    if (!engine.send("setoption name Hash value 16")) return false;
    if (!engine.send("setoption name OwnBook value false")) return false;
    if (!engine.send(std::string("setoption name NullThreatVerify value ") + (option_on ? "true" : "false"))) return false;
    return engine.send("isready") && engine.wait_prefix("readyok", kReadyTimeoutMs);
}

std::string square_name(int square) {
    std::string text;
    text += static_cast<char>('a' + forge::file_of(square));
    text += static_cast<char>('1' + forge::rank_of(square));
    return text;
}

std::string san(const forge::Board& board, forge::Move move) {
    std::string text;
    if (move.is_castle()) {
        text = (move.flags & forge::KingCastle) != 0 ? "O-O" : "O-O-O";
    } else {
        const int type = forge::piece_type(board.piece_at(move.from));
        const bool capture = move.is_capture();
        if (type == forge::Pawn) {
            if (capture) {
                text += static_cast<char>('a' + forge::file_of(move.from));
                text += 'x';
            }
        } else {
            text += " NBRQK"[type];
            bool clash = false;
            bool same_file = false;
            bool same_rank = false;
            for (const forge::Move other : board.legal_moves()) {
                if (other.from == move.from || other.to != move.to) continue;
                if (forge::piece_type(board.piece_at(other.from)) != type) continue;
                clash = true;
                if (forge::file_of(other.from) == forge::file_of(move.from)) same_file = true;
                if (forge::rank_of(other.from) == forge::rank_of(move.from)) same_rank = true;
            }
            if (clash) {
                if (!same_file) text += static_cast<char>('a' + forge::file_of(move.from));
                else if (!same_rank) text += static_cast<char>('1' + forge::rank_of(move.from));
                else text += square_name(move.from);
            }
            if (capture) text += 'x';
        }
        text += square_name(move.to);
        if (move.is_promotion()) {
            text += '=';
            text += " NBRQK"[move.promotion];
        }
    }
    forge::Board next = board;
    forge::Undo undo;
    (void)next.make_move(move, undo);
    if (next.legal_moves().empty() && next.in_check()) text += '#';
    else if (next.in_check()) text += '+';
    return text;
}

enum class Ending { Ongoing, WhiteWin, BlackWin, Draw, Illegal, Timeout, Length };

struct Game {
    Ending ending = Ending::Ongoing;
    std::vector<std::string> sans;
    int halfmoves = 0;
    bool mover_white = true;
    std::string note;
};

Game play_game(Engine& white, Engine& black, const std::string& fen) {
    Game game;
    forge::Board board;
    if (!board.set_fen(fen)) {
        game.ending = Ending::Illegal;
        game.note = "fen rejected";
        return game;
    }
    std::string moves;
        if (!white.send("ucinewgame") || !white.send("isready") || !white.wait_prefix("readyok", kReadyTimeoutMs) ||
            !black.send("ucinewgame") || !black.send("isready") || !black.wait_prefix("readyok", kReadyTimeoutMs)) {
            game.ending = Ending::Timeout;
            game.mover_white = true;
            game.note = "ucinewgame failed";
            return game;
        }
    while (game.halfmoves < kMaxHalfmoves) {
        if (board.halfmove_clock() >= 100 || board.is_insufficient_material() || board.is_repetition()) {
            game.ending = Ending::Draw;
            if (board.halfmove_clock() >= 100) game.note = "fifty-move";
            else if (board.is_insufficient_material()) game.note = "insufficient material";
            else game.note = "threefold";
            return game;
        }
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) {
            game.ending = board.in_check() ? (board.side_to_move() == forge::White ? Ending::BlackWin : Ending::WhiteWin)
                                           : Ending::Draw;
            if (legal.empty() && !board.in_check()) game.note = "stalemate";
            return game;
        }
        Engine& side = board.side_to_move() == forge::White ? white : black;
        game.mover_white = board.side_to_move() == forge::White;
        const std::string command = "position fen " + fen + (moves.empty() ? "" : " moves " + moves);
        if (!side.send(command) || !side.send("go nodes " + std::to_string(kNodes))) {
            game.ending = Ending::Timeout;
            game.note = "send failed";
            return game;
        }
        const auto line = side.wait_bestmove(kMoveTimeoutMs);
        if (!line) {
            game.ending = Ending::Timeout;
            game.note = "bestmove timeout";
            return game;
        }
        std::istringstream parser(*line);
        std::string tag;
        std::string uci;
        parser >> tag >> uci;
        const auto parsed = board.parse_uci(uci);
        if (!parsed || !board.is_legal(*parsed)) {
            game.ending = Ending::Illegal;
            game.note = "illegal " + uci;
            return game;
        }
        game.sans.push_back(san(board, *parsed));
        if (!moves.empty()) moves += ' ';
        moves += uci;
        forge::Undo undo;
        (void)board.make_move(*parsed, undo);
        ++game.halfmoves;
    }
    game.ending = Ending::Length;
    game.note = "halfmove cap";
    return game;
}

const char* result_text(Ending ending) {
    switch (ending) {
    case Ending::WhiteWin: return "1-0";
    case Ending::BlackWin: return "0-1";
    case Ending::Draw:
    case Ending::Length: return "1/2-1/2";
    case Ending::Illegal:
    case Ending::Timeout: return "*";
    case Ending::Ongoing: return "*";
    }
    return "*";
}

double on_points(const Game& game, bool on_white) {
    if (game.ending == Ending::Draw || game.ending == Ending::Length) return 0.5;
    if (game.ending == Ending::Illegal || game.ending == Ending::Timeout) {
        const bool on_moved = game.mover_white == on_white;
        return on_moved ? 0.0 : 1.0;
    }
    const bool white_won = game.ending == Ending::WhiteWin;
    return white_won == on_white ? 1.0 : 0.0;
}

struct Tally {
    std::int64_t games = 0;
    std::int64_t wins = 0;
    std::int64_t losses = 0;
    std::int64_t draws = 0;
    std::int64_t pairs = 0;
    std::int64_t penta[5] = {};
    std::int64_t pair_dd = 0;
    std::int64_t pair_wl = 0;
    std::int64_t illegal = 0;
    std::int64_t timeouts = 0;
    std::int64_t length_draws = 0;
    double sum_pair = 0;
    double sum_pair_sq = 0;
};

void add_game(Tally& tally, double points, Ending ending) {
    ++tally.games;
    if (points == 1.0) ++tally.wins;
    else if (points == 0.0) ++tally.losses;
    else ++tally.draws;
    if (ending == Ending::Illegal) ++tally.illegal;
    if (ending == Ending::Timeout) ++tally.timeouts;
    if (ending == Ending::Length) ++tally.length_draws;
}

void add_pair(Tally& tally, double first, double second) {
    const double score = first + second;
    ++tally.pairs;
    tally.sum_pair += score;
    tally.sum_pair_sq += score * score;
    const int bucket = static_cast<int>(std::lround(score * 2.0));
    if (bucket >= 0 && bucket < 5) ++tally.penta[bucket];
    if (bucket == 2) {
        if (first == 0.5 && second == 0.5) ++tally.pair_dd;
        else ++tally.pair_wl;
    }
}

std::string format_tally(const Tally& tally) {
    std::ostringstream out;
    out << "W-L-D " << tally.wins << '-' << tally.losses << '-' << tally.draws << '\n';
    out << "games " << tally.games << " pairs " << tally.pairs << '\n';
    out << "pentanomial LL LD DD/WL WD WW " << tally.penta[0] << ' ' << tally.penta[1] << ' ' << tally.penta[2]
        << ' ' << tally.penta[3] << ' ' << tally.penta[4] << '\n';
    out << "middle DD " << tally.pair_dd << " WL " << tally.pair_wl << '\n';
    out << "illegal " << tally.illegal << " timeouts " << tally.timeouts << " length_draws " << tally.length_draws
        << '\n';
    if (tally.pairs < 2 || tally.games == 0) {
        out << "elo n/a\nlos n/a\n";
        return out.str();
    }
    const double mean_pair = tally.sum_pair / static_cast<double>(tally.pairs);
    const double mean_game = mean_pair / 2.0;
    const double var_num = tally.sum_pair_sq - static_cast<double>(tally.pairs) * mean_pair * mean_pair;
    const double var = std::max(0.0, var_num / static_cast<double>(tally.pairs - 1));
    const double se_game = std::sqrt(var / static_cast<double>(tally.pairs)) / 2.0;
    out << "mean_game_score " << mean_game << '\n';
    if (mean_game <= 0.0 || mean_game >= 1.0 || se_game == 0.0) {
        out << "elo n/a\n";
        out << "los " << (mean_game > 0.5 ? 1.0 : mean_game < 0.5 ? 0.0 : 0.5) << '\n';
        return out.str();
    }
    const double elo = -400.0 * std::log10(1.0 / mean_game - 1.0);
    const double se_elo = se_game * 400.0 / (std::log(10.0) * mean_game * (1.0 - mean_game));
    const double ci = 1.959963984540054 * se_elo;
    const double los = 0.5 * (1.0 + std::erf((mean_game - 0.5) / (se_game * std::sqrt(2.0))));
    out << "elo " << elo << '\n';
    out << "elo95 " << (elo - ci) << ' ' << (elo + ci) << '\n';
    out << "los " << los << '\n';
    return out.str();
}

void write_pgn_game(std::ostream& out, int chunk, int opening, int game_in_pair, bool on_white, const std::string& fen,
                    const Game& game) {
    out << "[Event \"NullThreatVerify screen\"]\n";
    out << "[Site \"local\"]\n";
    out << "[Date \"2026.11.14\"]\n";
    out << "[Round \"" << chunk << '.' << opening << '.' << game_in_pair << "\"]\n";
    out << "[White \"" << (on_white ? "NullThreatVerify on" : "NullThreatVerify off") << "\"]\n";
    out << "[Black \"" << (on_white ? "NullThreatVerify off" : "NullThreatVerify on") << "\"]\n";
    out << "[Result \"" << result_text(game.ending) << "\"]\n";
    out << "[FEN \"" << fen << "\"]\n";
    out << "[SetUp \"1\"]\n";
    out << "[OpeningIndex \"" << opening << "\"]\n";
    if (!game.note.empty()) out << "[Termination \"" << game.note << "\"]\n";
    out << '\n';
    std::string line;
    int fullmove = 1;
    std::istringstream fen_in(fen);
    std::string skip;
    fen_in >> skip >> skip >> skip >> skip >> skip >> fullmove;
    bool white_to_move = fen.size() > 0 && fen.find(" w ") != std::string::npos;
    for (std::size_t i = 0; i < game.sans.size(); ++i) {
        std::string token;
        if (white_to_move) token = std::to_string(fullmove) + ". " + game.sans[i];
        else {
            if (i == 0) token = std::to_string(fullmove) + "... " + game.sans[i];
            else token = game.sans[i];
        }
        if (!line.empty() && line.size() + 1 + token.size() > 78) {
            out << line << '\n';
            line.clear();
        }
        if (!line.empty()) line += ' ';
        line += token;
        if (!white_to_move) ++fullmove;
        white_to_move = !white_to_move;
    }
    if (!line.empty()) line += ' ';
    line += result_text(game.ending);
    out << line << "\n\n";
}

std::vector<std::string> load_chunk(const std::string& path, int chunk, int openings, std::string& error) {
    std::ifstream in(path);
    if (!in) {
        error = "cannot open book";
        return {};
    }
    const std::int64_t skip = static_cast<std::int64_t>(chunk) * openings;
    std::string line;
    for (std::int64_t i = 0; i < skip; ++i) {
        if (!std::getline(in, line)) {
            error = "book ended before chunk";
            return {};
        }
    }
    std::vector<std::string> fens;
    fens.reserve(static_cast<std::size_t>(openings));
    while (static_cast<int>(fens.size()) < openings && std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        const auto cut = line.find(';');
        if (cut != std::string::npos) line.resize(cut);
        while (!line.empty() && line.back() == ' ') line.pop_back();
        if (!line.empty()) fens.push_back(line);
    }
    return fens;
}

std::string read_nps(const std::string& engine, bool option_on) {
    Engine side;
    if (!boot(side, engine, option_on)) return "boot-failed";
    if (!side.send("bench 13")) return "send-failed";
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(120);
    while (true) {
        const auto line = side.read_line(deadline);
        if (!line) return "timeout";
        if (line->rfind("info string bench depth 13 nodes ", 0) == 0) return *line;
    }
}

int run_bench(const std::string& engine, const std::string& out_path) {
    std::ofstream out(out_path);
    if (!out) return 1;
    out << "bench 13 nps, five off and five on, alternating, option off first\n";
    out << "same binary " << engine << '\n';
    out << "sha256 " << sha256_file(engine) << '\n';
    out << "Threads 1 Hash 16 OwnBook false are the match settings; bench uses its own 16 MB table\n";
    for (int i = 0; i < 10; ++i) {
        const bool on = (i % 2) == 1;
        const std::string line = read_nps(engine, on);
        out << (on ? "on " : "off ") << (i / 2 + 1) << ' ' << line << '\n';
        out.flush();
        std::cout << (on ? "on " : "off ") << line << '\n';
    }
    return 0;
}

int run_match(const std::string& engine, const std::string& book, const std::string& outdir, int chunk, int openings,
              int hour_budget) {
    const auto started = std::chrono::steady_clock::now();
    char name[64];
    std::snprintf(name, sizeof name, "/chunk_%03d.pgn", chunk);
    const std::string pgn_file = outdir + name;
    std::snprintf(name, sizeof name, "/chunk_%03d_summary.txt", chunk);
    const std::string summary_file = outdir + name;
    std::string error;
    const std::vector<std::string> fens = load_chunk(book, chunk, openings, error);
    if (!error.empty() || fens.empty()) {
        std::cerr << "book error " << error << " loaded " << fens.size() << '\n';
        return 1;
    }
    Engine on_engine;
    Engine off_engine;
    if (!boot(on_engine, engine, true) || !boot(off_engine, engine, false)) {
        std::cerr << "boot failed\n";
        return 1;
    }
    std::ofstream pgn(pgn_file);
    Tally tally;
    const std::int64_t opening0 = static_cast<std::int64_t>(chunk) * openings;
    for (std::size_t i = 0; i < fens.size(); ++i) {
        if (hour_budget > 0) {
            const double hours = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count() / 3600.0;
            if (i > 0 && hours >= static_cast<double>(hour_budget)) {
                std::cerr << "hour budget reached at opening " << i << '\n';
                break;
            }
        }
        const Game first = play_game(on_engine, off_engine, fens[i]);
        if (first.ending == Ending::Timeout) {
            boot(on_engine, engine, true);
            boot(off_engine, engine, false);
        }
        const double p1 = on_points(first, true);
        add_game(tally, p1, first.ending);
        write_pgn_game(pgn, chunk, static_cast<int>(opening0 + static_cast<std::int64_t>(i)), 1, true, fens[i], first);

        const Game second = play_game(off_engine, on_engine, fens[i]);
        if (second.ending == Ending::Timeout) {
            boot(on_engine, engine, true);
            boot(off_engine, engine, false);
        }
        const double p2 = on_points(second, false);
        add_game(tally, p2, second.ending);
        add_pair(tally, p1, p2);
        write_pgn_game(pgn, chunk, static_cast<int>(opening0 + static_cast<std::int64_t>(i)), 2, false, fens[i], second);
        pgn.flush();
        if ((i + 1) % 10 == 0) {
            std::cout << "chunk " << chunk << " openings " << (i + 1) << " W-L-D " << tally.wins << '-' << tally.losses
                      << '-' << tally.draws << '\n';
        }
    }
    const double seconds = std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
    std::ofstream summary(summary_file);
    summary << "screening only, not a strength claim\n";
    summary << "NullThreatVerify on versus off, same binary\n";
    summary << "W-L-D is option on first\n";
    summary << "chunk " << chunk << " openings_requested " << openings << " openings_played " << tally.pairs << '\n';
    summary << "opening_index_first " << opening0 << '\n';
    summary << "order sequential\n";
    summary << "nodes " << kNodes << " Threads 1 Hash 16 OwnBook false\n";
    summary << "pairing game1 option on white, game2 option on black\n";
    summary << "engine " << engine << '\n';
    summary << "engine_sha256 " << sha256_file(engine) << '\n';
    summary << "book " << book << '\n';
    summary << "book_sha256 " << sha256_file(book) << '\n';
    summary << "seconds " << seconds << '\n';
    summary << format_tally(tally);
    summary << "pgn " << pgn_file << '\n';
    std::cout << "CHUNK_DONE " << chunk << "\n" << format_tally(tally);
    return tally.illegal > 0 || tally.timeouts > 0 ? 2 : 0;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 3) {
        std::cerr << "usage: screen_match bench <engine> <out>\n"
                     "       screen_match match <engine> <epd> <outdir> <chunk> <openings> <hour-budget>\n";
        return 1;
    }
    const std::string mode = argv[1];
    if (mode == "bench") return run_bench(argv[2], argv[3]);
    if (mode == "match") {
        if (argc < 8) return 1;
        return run_match(argv[2], argv[3], argv[4], std::atoi(argv[5]), std::atoi(argv[6]), std::atoi(argv[7]));
    }
    return 1;
}
