// Extracts quiet training positions from UCI-notation PGN files produced by
// fastchess (-pgnout notation=uci). Each output line is:
//   <fen> <result> <score>
// where result is the game result from White's point of view (1, 0.5, 0) and
// score is the searching engine's reported centipawn score from White's point
// of view, or "none" when unavailable.
//
// Usage: forge_extract [--min-ply N] <input.pgn> [more.pgn ...] > positions.txt
// Positions before ply N (default 8) are skipped; book moves never qualify.
#include "forge/board.hpp"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Game {
    std::string result;
    std::string fen; // empty for the standard start position
    std::vector<std::pair<std::string, std::string>> moves; // move, comment
};

bool read_game(std::istream& input, Game& game) {
    game = Game{};
    std::string line;
    bool in_header = false;
    bool have_moves = false;
    std::string movetext;
    while (std::getline(input, line)) {
        if (line.empty()) {
            if (have_moves) break;
            continue;
        }
        if (line[0] == '[') {
            if (have_moves) {
                // Start of the next game without a blank separator.
                break;
            }
            in_header = true;
            if (line.rfind("[Result ", 0) == 0 || line.rfind("[FEN ", 0) == 0) {
                const auto first = line.find('"');
                const auto last = line.rfind('"');
                if (first != std::string::npos && last != std::string::npos && last > first) {
                    const std::string value = line.substr(first + 1, last - first - 1);
                    if (line[1] == 'R') game.result = value;
                    else game.fen = value;
                }
            }
            continue;
        }
        in_header = false;
        have_moves = true;
        movetext += line + ' ';
    }
    (void)in_header;
    if (!have_moves) return false;

    // Tokenise the movetext: move numbers, moves, {comments}, result.
    std::size_t i = 0;
    while (i < movetext.size()) {
        const char c = movetext[i];
        if (c == ' ') { ++i; continue; }
        if (c == '{') {
            const auto end = movetext.find('}', i);
            if (end == std::string::npos) break;
            if (!game.moves.empty()) game.moves.back().second = movetext.substr(i + 1, end - i - 1);
            i = end + 1;
            continue;
        }
        std::size_t end = movetext.find(' ', i);
        if (end == std::string::npos) end = movetext.size();
        std::string token = movetext.substr(i, end - i);
        i = end;
        if (token == "1-0" || token == "0-1" || token == "1/2-1/2" || token == "*") break;
        if (!token.empty() && std::isdigit(static_cast<unsigned char>(token[0]))) {
            const auto dot = token.find('.');
            if (dot == std::string::npos) continue;
            token = token.substr(token.find_last_of('.') + 1);
            if (token.empty()) continue;
        }
        game.moves.emplace_back(token, std::string());
    }
    return true;
}

// Parses a fastchess comment such as "+0.35/12 0.012s" or "-M5/20 0.1s".
std::optional<int> parse_score(const std::string& comment) {
    if (comment.empty() || comment == "book") return std::nullopt;
    std::istringstream input(comment);
    std::string score_text;
    input >> score_text;
    const auto slash = score_text.find('/');
    if (slash != std::string::npos) score_text = score_text.substr(0, slash);
    if (score_text.empty()) return std::nullopt;
    if (score_text.find('M') != std::string::npos) {
        return score_text[0] == '-' ? -3000 : 3000;
    }
    char* end = nullptr;
    const double value = std::strtod(score_text.c_str(), &end);
    if (end == score_text.c_str()) return std::nullopt;
    return static_cast<int>(value * 100.0);
}

} // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_extract <input.pgn> [more.pgn ...]\n";
        return 2;
    }
    std::uint64_t games = 0;
    std::uint64_t positions = 0;
    int min_ply = 8;
    std::ios::sync_with_stdio(false);
    for (int arg = 1; arg < argc; ++arg) {
        if (std::string(argv[arg]) == "--min-ply" && arg + 1 < argc) {
            min_ply = std::atoi(argv[++arg]);
            continue;
        }
        std::ifstream input(argv[arg]);
        if (!input) {
            std::cerr << "cannot open " << argv[arg] << '\n';
            return 1;
        }
        Game game;
        while (read_game(input, game)) {
            double result;
            if (game.result == "1-0") result = 1.0;
            else if (game.result == "0-1") result = 0.0;
            else if (game.result == "1/2-1/2") result = 0.5;
            else continue;
            ++games;
            forge::Board board;
            if (!game.fen.empty() && !board.set_fen(game.fen)) continue;
            int ply = 0;
            for (const auto& [text, comment] : game.moves) {
                const auto move = board.parse_uci(text);
                if (!move.has_value()) break;
                const auto score = parse_score(comment);
                const bool quiet = !move->is_capture() && !move->is_promotion() && !board.in_check();
                // Skip book moves, tactical positions, and extreme scores whose
                // outcome is already decided.
                if (score.has_value() && quiet && ply >= min_ply && std::abs(*score) < 1500) {
                    const int white_score = board.side_to_move() == forge::White ? *score : -*score;
                    std::cout << board.fen() << ' ' << result << ' ' << white_score << '\n';
                    ++positions;
                }
                forge::Undo undo;
                (void)board.make_move(*move, undo);
                ++ply;
            }
        }
    }
    std::cout.flush();
    std::cerr << "games " << games << " positions " << positions << '\n';
    return 0;
}
