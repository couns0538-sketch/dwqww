// Node-limited UHO screen: SoundMatePruning on versus off.
// Usage: uho_screen <epd> <start> <openings> <pgn> <summary>
// Each opening is played twice with colors swapped. Option-on is engine A.

#include "forge/board.hpp"
#include "forge/search.hpp"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr std::uint64_t NodeLimit = 50000;
constexpr int MaxPlies = 320;

std::string san(forge::Board& board, const forge::Move& move) {
    const int piece = forge::piece_type(board.moved_piece(move));
    if (piece == forge::King && std::abs(forge::file_of(move.to) - forge::file_of(move.from)) == 2) {
        return forge::file_of(move.to) > forge::file_of(move.from) ? "O-O" : "O-O-O";
    }
    const bool capture = move.is_capture();
    std::string text;
    const forge::MoveList legal = board.legal_moves();
    int same = 0;
    int same_file = 0;
    int same_rank = 0;
    for (const forge::Move other : legal) {
        if (other.to != move.to || other.from == move.from) continue;
        if (forge::piece_type(board.moved_piece(other)) != piece) continue;
        ++same;
        if (forge::file_of(other.from) == forge::file_of(move.from)) ++same_file;
        if (forge::rank_of(other.from) == forge::rank_of(move.from)) ++same_rank;
    }
    const std::string dest = forge::Board::move_to_uci(move).substr(2, 2);
    if (piece == forge::Pawn) {
        if (capture) text += static_cast<char>('a' + forge::file_of(move.from));
    } else {
        text += " PNBRQK"[piece];
        if (same > 0) {
            if (same_file == 0) text += static_cast<char>('a' + forge::file_of(move.from));
            else if (same_rank == 0) text += static_cast<char>('1' + forge::rank_of(move.from));
            else {
                text += static_cast<char>('a' + forge::file_of(move.from));
                text += static_cast<char>('1' + forge::rank_of(move.from));
            }
        }
    }
    if (capture) text += 'x';
    text += dest;
    if (move.is_promotion()) {
        const char promo[] = "?pnbrqk";
        text += '=';
        text += promo[move.promotion];
    }
    forge::Undo undo;
    (void)board.make_move(move, undo);
    const bool mate = board.legal_moves().empty() && board.in_check();
    const bool check = board.in_check();
    board.unmake_move(move, undo);
    if (mate) text += '#';
    else if (check) text += '+';
    return text;
}

std::string fen_of(const std::string& line) {
    std::istringstream input(line);
    std::string field;
    std::string fen;
    for (int i = 0; i < 6 && input >> field; ++i) {
        if (!fen.empty()) fen += ' ';
        fen += field;
    }
    return fen;
}

enum class Outcome { OnWin, Draw, OffWin };

Outcome play_game(const std::string& fen, bool on_is_white, std::vector<std::string>& moves, std::uint64_t& nodes) {
    forge::Board board;
    if (!board.set_fen(fen)) return Outcome::Draw;
    forge::Searcher on_engine(16, 1);
    forge::Searcher off_engine(16, 1);
    moves.clear();
    nodes = 0;
    for (int ply = 0; ply < MaxPlies; ++ply) {
        if (board.legal_moves().empty()) {
            if (!board.in_check()) return Outcome::Draw;
            const bool white_lost = board.side_to_move() == forge::White;
            const bool on_lost = white_lost == on_is_white;
            return on_lost ? Outcome::OffWin : Outcome::OnWin;
        }
        if (board.is_repetition() || board.halfmove_clock() >= 100 || board.is_insufficient_material()) return Outcome::Draw;
        const bool on_turn = (board.side_to_move() == forge::White) == on_is_white;
        forge::tune::SoundMatePruning = on_turn;
        forge::tune::SoundArmPv = forge::tune::SoundPruneArm::FollowOption;
        forge::tune::SoundArmInCheck = forge::tune::SoundPruneArm::FollowOption;
        forge::tune::SoundArmMateAlpha = forge::tune::SoundPruneArm::FollowOption;
        forge::SearchLimits limits;
        limits.nodes = NodeLimit;
        limits.nodes_specified = true;
        forge::Searcher& engine = on_turn ? on_engine : off_engine;
        const forge::SearchInfo info = engine.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
        nodes += info.nodes;
        if (info.best_move.is_none() || !board.is_legal(info.best_move)) {
            return on_turn ? Outcome::OffWin : Outcome::OnWin;
        }
        const int number = board.fullmove_number();
        const bool white = board.side_to_move() == forge::White;
        std::string token;
        if (white || moves.empty()) {
            token = std::to_string(number) + (white ? ". " : "... ");
        }
        token += san(board, info.best_move);
        moves.push_back(token);
        forge::Undo undo;
        (void)board.make_move(info.best_move, undo);
    }
    return Outcome::Draw;
}

const char* result_text(Outcome outcome, bool on_is_white) {
    if (outcome == Outcome::Draw) return "1/2-1/2";
    const bool white_won = (outcome == Outcome::OnWin) == on_is_white;
    return white_won ? "1-0" : "0-1";
}

double game_points(Outcome outcome) {
    if (outcome == Outcome::OnWin) return 1.0;
    if (outcome == Outcome::Draw) return 0.5;
    return 0.0;
}

double elo_of(double score) {
    if (score <= 0.000001) return -800.0;
    if (score >= 0.999999) return 800.0;
    return -400.0 * std::log10(1.0 / score - 1.0);
}

double normal_cdf(double z) {
    return 0.5 * std::erfc(-z / std::sqrt(2.0));
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 6) {
        std::cerr << "usage: uho_screen <epd> <start> <openings> <pgn> <summary>\n";
        return 2;
    }
    const std::string epd_path = argv[1];
    const int start = std::stoi(argv[2]);
    const int openings = std::stoi(argv[3]);
    std::ofstream pgn(argv[4]);
    std::ofstream summary(argv[5]);
    if (!pgn || !summary) return 2;
    std::ifstream epd(epd_path);
    if (!epd) return 2;

    std::string line;
    int index = 0;
    int played = 0;
    int wins = 0;
    int losses = 0;
    int draws = 0;
    int pairs[5] = {};
    std::vector<double> points;
    while (played < openings && std::getline(epd, line)) {
        if (line.empty()) continue;
        if (index++ < start) continue;
        const std::string fen = fen_of(line);
        Outcome pair[2];
        for (int color = 0; color < 2; ++color) {
            const bool on_white = color == 0;
            std::vector<std::string> moves;
            std::uint64_t nodes = 0;
            const Outcome outcome = play_game(fen, on_white, moves, nodes);
            pair[color] = outcome;
            if (outcome == Outcome::OnWin) ++wins;
            else if (outcome == Outcome::OffWin) ++losses;
            else ++draws;
            points.push_back(game_points(outcome));
            pgn << "[Event \"SoundMatePruning UHO nodes 50000\"]\n";
            pgn << "[Site \"local\"]\n";
            pgn << "[Round \"" << index << "." << (color + 1) << "\"]\n";
            pgn << "[White \"" << (on_white ? "option-on" : "option-off") << "\"]\n";
            pgn << "[Black \"" << (on_white ? "option-off" : "option-on") << "\"]\n";
            pgn << "[Result \"" << result_text(outcome, on_white) << "\"]\n";
            pgn << "[FEN \"" << fen << "\"]\n";
            pgn << "[SetUp \"1\"]\n";
            pgn << "[OpeningIndex \"" << (index - 1) << "\"]\n\n";
            for (std::size_t i = 0; i < moves.size(); ++i) {
                if (i > 0) pgn << ' ';
                pgn << moves[i];
            }
            pgn << ' ' << result_text(outcome, on_white) << "\n\n";
            if (played == 0 && color == 0) {
                std::cerr << "first game nodes " << nodes << " plies " << moves.size() << "\n";
            }
        }
        const double pair_points = game_points(pair[0]) + game_points(pair[1]);
        const int bucket = static_cast<int>(pair_points * 2.0 + 0.01);
        if (bucket >= 0 && bucket <= 4) ++pairs[bucket];
        ++played;
        if (played % 10 == 0) {
            std::cerr << "openings " << played << " W " << wins << " L " << losses << " D " << draws << "\n";
            pgn.flush();
        }
    }

    const int games = wins + losses + draws;
    const double score = games == 0 ? 0.0 : (wins + 0.5 * draws) / games;
    double variance = 0.0;
    for (double point : points) {
        const double delta = point - score;
        variance += delta * delta;
    }
    const double se = games > 1 ? std::sqrt(variance / (static_cast<double>(games) * (games - 1))) : 0.0;
    const double z = 1.959963984540054;
    const double low = std::max(0.0, score - z * se);
    const double high = std::min(1.0, score + z * se);
    const double los = se == 0.0 ? (score > 0.5 ? 1.0 : score < 0.5 ? 0.0 : 0.5) : normal_cdf((score - 0.5) / se);

    summary << "command: uho_screen " << epd_path << " " << start << " " << openings << " " << argv[4] << " " << argv[5] << "\n";
    summary << "nodes: " << NodeLimit << "\n";
    summary << "threads: 1\n";
    summary << "hash: 16\n";
    summary << "option_on_first: true\n";
    summary << "openings_requested: " << openings << "\n";
    summary << "openings_played: " << played << "\n";
    summary << "start_index: " << start << "\n";
    summary << "games: " << games << "\n";
    summary << "W-L-D: " << wins << "-" << losses << "-" << draws << "\n";
    summary << "score: " << score << "\n";
    summary << "elo: " << elo_of(score) << "\n";
    summary << "elo95: " << elo_of(low) << " " << elo_of(high) << "\n";
    summary << "los: " << los << "\n";
    summary << "pentanomial: " << pairs[0] << " " << pairs[1] << " " << pairs[2] << " " << pairs[3] << " " << pairs[4] << "\n";
    summary << "pentanomial_order: LL LD WL/DD WD WW\n";
    summary.flush();
    std::cout << "W-L-D " << wins << "-" << losses << "-" << draws
              << " elo " << elo_of(score) << " los " << los
              << " penta " << pairs[0] << " " << pairs[1] << " " << pairs[2] << " " << pairs[3] << " " << pairs[4] << "\n";
    return games == 0 ? 1 : 0;
}
