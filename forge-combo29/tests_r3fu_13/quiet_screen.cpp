#include "forge/board.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <poll.h>
#include <sstream>
#include <string>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

namespace {

constexpr int Nodes = 50000;
constexpr int MoveTimeoutMs = 60000;
constexpr int PairsPerChunk = 40;

struct Engine {
    pid_t pid = -1;
    int to_child = -1;
    int from_child = -1;
    std::string pending;

    ~Engine() { stop(); }

    void stop() {
        if (to_child >= 0) {
            const char* quit = "quit\n";
            (void)::write(to_child, quit, 5);
            ::close(to_child);
            to_child = -1;
        }
        if (from_child >= 0) {
            ::close(from_child);
            from_child = -1;
        }
        if (pid > 0) {
            int status = 0;
            (void)::waitpid(pid, &status, 0);
            pid = -1;
        }
        pending.clear();
    }

    bool start(const std::string& path, bool extinction) {
        stop();
        int in_pipe[2];
        int out_pipe[2];
        if (pipe(in_pipe) != 0 || pipe(out_pipe) != 0) return false;
        pid = fork();
        if (pid < 0) return false;
        if (pid == 0) {
            dup2(in_pipe[0], STDIN_FILENO);
            dup2(out_pipe[1], STDOUT_FILENO);
            ::close(in_pipe[0]);
            ::close(in_pipe[1]);
            ::close(out_pipe[0]);
            ::close(out_pipe[1]);
            execl(path.c_str(), path.c_str(), static_cast<char*>(nullptr));
            _exit(127);
        }
        ::close(in_pipe[0]);
        ::close(out_pipe[1]);
        to_child = in_pipe[1];
        from_child = out_pipe[0];
        if (!write_line("uci")) return false;
        if (!wait_for("uciok", 10000)) return false;
        if (!write_line("setoption name Threads value 1")) return false;
        if (!write_line("setoption name Hash value 16")) return false;
        if (!write_line("setoption name OwnBook value false")) return false;
        if (!write_line(std::string("setoption name QuietExtinction value ") + (extinction ? "true" : "false"))) return false;
        if (!write_line("isready")) return false;
        return wait_for("readyok", 10000);
    }

    bool write_line(const std::string& text) {
        const std::string line = text + "\n";
        const char* data = line.data();
        std::size_t left = line.size();
        while (left > 0) {
            const ssize_t wrote = ::write(to_child, data, left);
            if (wrote < 0) return false;
            data += wrote;
            left -= static_cast<std::size_t>(wrote);
        }
        return true;
    }

    bool read_line(std::string& line, int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        while (true) {
            const auto cut = pending.find('\n');
            if (cut != std::string::npos) {
                line = pending.substr(0, cut);
                if (!line.empty() && line.back() == '\r') line.pop_back();
                pending.erase(0, cut + 1);
                return true;
            }
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - std::chrono::steady_clock::now()).count();
            if (left <= 0) return false;
            pollfd poll_fd{from_child, POLLIN, 0};
            const int ready = poll(&poll_fd, 1, static_cast<int>(left));
            if (ready <= 0) return false;
            char buffer[4096];
            const ssize_t got = ::read(from_child, buffer, sizeof buffer);
            if (got <= 0) return false;
            pending.append(buffer, buffer + got);
        }
    }

    bool wait_for(const std::string& token, int timeout_ms) {
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(timeout_ms);
        std::string line;
        while (std::chrono::steady_clock::now() < deadline) {
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - std::chrono::steady_clock::now()).count();
            if (!read_line(line, static_cast<int>(std::max<std::int64_t>(left, 1)))) return false;
            if (line.rfind(token, 0) == 0) return true;
        }
        return false;
    }

    std::string best_move(const std::string& fen, const std::vector<std::string>& moves) {
        std::string command = "position fen " + fen;
        if (!moves.empty()) {
            command += " moves";
            for (const std::string& move : moves) command += " " + move;
        }
        if (!write_line(command) || !write_line("go nodes " + std::to_string(Nodes))) return {};
        const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(MoveTimeoutMs);
        std::string line;
        while (std::chrono::steady_clock::now() < deadline) {
            const auto left = std::chrono::duration_cast<std::chrono::milliseconds>(deadline - std::chrono::steady_clock::now()).count();
            if (!read_line(line, static_cast<int>(std::max<std::int64_t>(left, 1)))) return {};
            if (line.rfind("bestmove ", 0) != 0) continue;
            std::istringstream input(line);
            std::string tag;
            std::string move;
            input >> tag >> move;
            return move;
        }
        return {};
    }

    bool new_game() {
        if (!write_line("ucinewgame")) return false;
        if (!write_line("isready")) return false;
        return wait_for("readyok", 10000);
    }
};

char file_of(int square) { return static_cast<char>('a' + square % 8); }
char rank_of(int square) { return static_cast<char>('1' + square / 8); }

std::string san(forge::Board& board, forge::Move move) {
    if ((move.flags & forge::KingCastle) != 0) return "O-O";
    if ((move.flags & forge::QueenCastle) != 0) return "O-O-O";
    const int type = forge::piece_type(board.piece_at(move.from));
    std::string text;
    if (type != forge::Pawn) {
        text += std::string(" PNBRQK")[static_cast<std::size_t>(type)];
        bool file_clash = false;
        bool rank_clash = false;
        for (const forge::Move other : board.legal_moves()) {
            if (other.to != move.to || other.from == move.from) continue;
            if (forge::piece_type(board.piece_at(other.from)) != type) continue;
            if (other.from % 8 == move.from % 8) rank_clash = true;
            else file_clash = true;
        }
        if (file_clash) text += file_of(move.from);
        if (rank_clash) text += rank_of(move.from);
    } else if (move.is_capture()) {
        text += file_of(move.from);
    }
    if (move.is_capture()) text += 'x';
    text += file_of(move.to);
    text += rank_of(move.to);
    if (move.is_promotion()) {
        text += '=';
        text += std::string(" PNBRQK")[static_cast<std::size_t>(move.promotion)];
    }
    forge::Undo undo;
    if (!board.make_move(move, undo)) return text;
    if (board.in_check()) text += board.legal_moves().empty() ? '#' : '+';
    board.unmake_move(move, undo);
    return text;
}

std::string result_tag(int on_white_score_twice) {
    if (on_white_score_twice > 0) return "1-0";
    if (on_white_score_twice < 0) return "0-1";
    return "1/2-1/2";
}

double normal_cdf(double z) { return 0.5 * (1.0 + std::erf(z / std::sqrt(2.0))); }

struct Tally {
    int wins = 0;
    int losses = 0;
    int draws = 0;
    int penta[5] = {};
    std::vector<double> scores;

    void add(double score) { scores.push_back(score); }

    int games() const { return wins + losses + draws; }

    void finish_pair(double first, double second) {
        const double sum = first + second;
        if (sum <= 0.0) ++penta[0];
        else if (sum <= 0.5) ++penta[1];
        else if (sum <= 1.0) ++penta[2];
        else if (sum <= 1.5) ++penta[3];
        else ++penta[4];
    }

    std::string report() const {
        const int n = games();
        const double points = wins + 0.5 * draws;
        const double p = n == 0 ? 0.5 : points / n;
        const double clamped = std::min(0.999, std::max(0.001, p));
        const double elo = -400.0 * std::log10(1.0 / clamped - 1.0);
        double sse = 0.0;
        for (const double score : scores) {
            const double diff = score - p;
            sse += diff * diff;
        }
        const double se_p = n > 1 ? std::sqrt(sse / (n * (n - 1.0))) : 0.0;
        const double slope = 400.0 / (std::log(10.0) * clamped * (1.0 - clamped));
        const double se_elo = se_p * slope;
        const double los = se_elo > 1e-9 ? 100.0 * normal_cdf(elo / se_elo) : (elo > 0 ? 100.0 : elo < 0 ? 0.0 : 50.0);
        std::ostringstream out;
        out << "W-L-D " << wins << "-" << losses << "-" << draws << "\n";
        out << "games " << n << " score " << points << "\n";
        out << "Elo " << elo << " 95% " << (elo - 1.96 * se_elo) << " " << (elo + 1.96 * se_elo) << "\n";
        out << "LOS " << los << "\n";
        out << "pentanomial " << penta[0] << " " << penta[1] << " " << penta[2] << " " << penta[3] << " " << penta[4] << "\n";
        return out.str();
    }
};

bool play_game(Engine& white, Engine& black, forge::Board board, const std::string& fen, bool on_white,
               std::vector<std::string>& sans, double& on_score) {
    std::vector<std::string> uci_moves;
    sans.clear();
    for (int ply = 0; ply < 240; ++ply) {
        const forge::MoveList legal = board.legal_moves();
        if (legal.empty()) {
            on_score = board.in_check() ? (board.side_to_move() == forge::White ? (on_white ? 0.0 : 1.0) : (on_white ? 1.0 : 0.0)) : 0.5;
            return true;
        }
        if (board.halfmove_clock() >= 100 || board.is_repetition() || board.is_insufficient_material()) {
            on_score = 0.5;
            return true;
        }
        Engine& side = board.side_to_move() == forge::White ? white : black;
        const std::string text = side.best_move(fen, uci_moves);
        const auto parsed = board.parse_uci(text);
        if (!parsed) return false;
        sans.push_back(san(board, *parsed));
        forge::Undo undo;
        if (!board.make_move(*parsed, undo)) return false;
        uci_moves.push_back(text);
    }
    on_score = 0.5;
    return true;
}

std::string movetext(const std::vector<std::string>& sans, const std::string& result) {
    std::ostringstream out;
    for (std::size_t i = 0; i < sans.size(); ++i) {
        if (i % 2 == 0) out << (i / 2 + 1) << ". ";
        out << sans[i] << " ";
    }
    out << result;
    return out.str();
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 5) {
        std::cerr << "usage: quiet_screen <engine> <epd> <outdir> <hours>\n";
        return 2;
    }
    const std::string engine_path = argv[1];
    const std::string epd_path = argv[2];
    const std::string outdir = argv[3];
    const double hours = std::atof(argv[4]);
    std::ifstream epd(epd_path);
    if (!epd) {
        std::cerr << "cannot read " << epd_path << "\n";
        return 2;
    }
    std::vector<std::string> openings;
    std::string line;
    while (std::getline(epd, line)) {
        if (line.empty()) continue;
        const auto cut = line.find(';');
        if (cut != std::string::npos) line.resize(cut);
        while (!line.empty() && line.back() == ' ') line.pop_back();
        openings.push_back(line);
    }
    if (openings.empty()) return 2;

    Engine on_engine;
    Engine off_engine;
    if (!on_engine.start(engine_path, true) || !off_engine.start(engine_path, false)) {
        std::cerr << "engine start failed\n";
        return 2;
    }

    const auto started = std::chrono::steady_clock::now();
    const auto deadline = started + std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::duration<double>(hours * 3600.0));
    Tally total;
    int chunk = 1;
    std::size_t cursor = 0;
    while (std::chrono::steady_clock::now() < deadline && cursor < openings.size()) {
        const std::string pgn_path = outdir + "/chunk-" + std::to_string(chunk) + ".pgn";
        const std::string sum_path = outdir + "/chunk-" + std::to_string(chunk) + ".txt";
        std::ofstream pgn(pgn_path);
        Tally local;
        int pairs = 0;
        while (pairs < PairsPerChunk && cursor < openings.size() && std::chrono::steady_clock::now() < deadline) {
            const std::string& fen = openings[cursor++];
            double pair_scores[2] = {};
            for (int game = 0; game < 2; ++game) {
                const bool on_white = game == 0;
                if (!on_engine.new_game() || !off_engine.new_game()) return 1;
                forge::Board board;
                if (!board.set_fen(fen)) return 1;
                Engine& white = on_white ? on_engine : off_engine;
                Engine& black = on_white ? off_engine : on_engine;
                std::vector<std::string> sans;
                double on_score = 0.0;
                const bool ok = play_game(white, black, board, fen, on_white, sans, on_score);
                if (!ok) {
                    on_score = 0.0;
                    if (!on_engine.start(engine_path, true) || !off_engine.start(engine_path, false)) return 1;
                }
                if (on_score > 0.75) ++local.wins;
                else if (on_score < 0.25) ++local.losses;
                else ++local.draws;
                local.add(on_score);
                pair_scores[game] = on_score;
                const std::string result = on_white ? (on_score > 0.75 ? "1-0" : on_score < 0.25 ? "0-1" : "1/2-1/2")
                                                    : (on_score > 0.75 ? "0-1" : on_score < 0.25 ? "1-0" : "1/2-1/2");
                pgn << "[Event \"QuietExtinction UHO screen\"]\n";
                pgn << "[Site \"forge-combo29\"]\n";
                pgn << "[White \"" << (on_white ? "QuietExtinction on" : "QuietExtinction off") << "\"]\n";
                pgn << "[Black \"" << (on_white ? "QuietExtinction off" : "QuietExtinction on") << "\"]\n";
                pgn << "[Result \"" << result << "\"]\n";
                pgn << "[FEN \"" << fen << "\"]\n";
                pgn << "[SetUp \"1\"]\n";
                pgn << "[PlyCount \"" << sans.size() << "\"]\n\n";
                pgn << movetext(sans, result) << "\n\n";
                pgn.flush();
                std::cout << "chunk " << chunk << " game " << (pairs * 2 + game + 1) << " on_score " << on_score
                          << " ply " << sans.size() << "\n";
            }
            local.finish_pair(pair_scores[0], pair_scores[1]);
            ++pairs;
        }
        pgn.close();
        total.wins += local.wins;
        total.losses += local.losses;
        total.draws += local.draws;
        for (double score : local.scores) total.add(score);
        for (int i = 0; i < 5; ++i) total.penta[i] += local.penta[i];
        std::ofstream summary(sum_path);
        summary << "chunk " << chunk << "\n" << local.report() << "\ncumulative\n" << total.report();
        summary.close();
        std::ofstream overall(outdir + "/SUMMARY.txt");
        overall << "QuietExtinction on vs off\n";
        overall << "nodes " << Nodes << "\n";
        overall << "openings " << epd_path << "\n";
        overall << "pairs_done " << (cursor) << "\n";
        overall << total.report();
        overall.close();
        std::cout << "CHUNK " << chunk << " done\n" << local.report();
        ++chunk;
    }
    std::cout << "SCREEN DONE\n" << total.report();
    return 0;
}
