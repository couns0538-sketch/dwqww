#include <cmath>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>

namespace {

struct Game {
    int round = 0;
    std::string white;
    std::string black;
    std::string result;
    std::string fen;
};

std::string tag_value(const std::string& line) {
    const auto quote = line.find('"');
    if (quote == std::string::npos) return {};
    const auto end = line.find('"', quote + 1);
    if (end == std::string::npos) return {};
    return line.substr(quote + 1, end - quote - 1);
}

double score_for_on(const Game& game) {
    const bool on_white = game.white == "on";
    if (game.result == "1/2-1/2") return 0.5;
    if (game.result == "1-0") return on_white ? 1.0 : 0.0;
    if (game.result == "0-1") return on_white ? 0.0 : 1.0;
    return -1.0;
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: pgn_screen file.pgn [more.pgn ...]\n";
        return 1;
    }
    std::ifstream in;
    int file_index = 1;
    auto open_next = [&]() {
        while (file_index < argc) {
            in.close();
            in.clear();
            in.open(argv[file_index]);
            if (!in) {
                std::cerr << "cannot read " << argv[file_index] << "\n";
                return false;
            }
            ++file_index;
            return true;
        }
        return false;
    };
    if (!open_next()) return 1;
    int round_base = 0;

    std::vector<Game> games;
    Game current;
    bool in_game = false;
    std::string line;
    while (true) {
        if (!std::getline(in, line)) {
            if (in_game && !current.result.empty()) games.push_back(current);
            current = Game{};
            in_game = false;
            if (!open_next()) break;
            round_base += 1000000;
            continue;
        }
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.rfind("[Round ", 0) == 0) {
            current = Game{};
            current.round = round_base + std::stoi(tag_value(line));
            in_game = true;
        } else if (in_game && line.rfind("[White ", 0) == 0) {
            current.white = tag_value(line);
        } else if (in_game && line.rfind("[Black ", 0) == 0) {
            current.black = tag_value(line);
        } else if (in_game && line.rfind("[Result ", 0) == 0) {
            current.result = tag_value(line);
        } else if (in_game && line.rfind("[FEN ", 0) == 0) {
            current.fen = tag_value(line);
        } else if (in_game && line.empty() && !current.result.empty() && !current.white.empty()) {
            games.push_back(current);
            current = Game{};
            in_game = false;
        }
    }
    if (in_game && !current.result.empty()) games.push_back(current);

    int wins = 0;
    int losses = 0;
    int draws = 0;
    int skipped = 0;
    double points = 0.0;
    std::map<int, std::vector<double>> by_round;
    for (const Game& game : games) {
        const double score = score_for_on(game);
        if (score < 0.0) {
            ++skipped;
            continue;
        }
        points += score;
        if (score == 1.0) ++wins;
        else if (score == 0.0) ++losses;
        else ++draws;
        by_round[game.round].push_back(score);
    }

    int bins[5] = {};
    int paired = 0;
    int unpaired_rounds = 0;
    double pair_sum = 0.0;
    std::vector<double> pair_scores;
    for (const auto& entry : by_round) {
        if (entry.second.size() != 2) {
            ++unpaired_rounds;
            continue;
        }
        const double pair = entry.second[0] + entry.second[1];
        const int bin = static_cast<int>(std::lround(pair * 2.0));
        if (bin < 0 || bin > 4) {
            ++unpaired_rounds;
            continue;
        }
        ++bins[bin];
        ++paired;
        pair_sum += pair;
        pair_scores.push_back(pair);
    }

    const int played = wins + losses + draws;
    std::cout << "games " << played << " skipped " << skipped << "\n";
    std::cout << "W-L-D " << wins << "-" << losses << "-" << draws << "\n";
    if (played == 0) return 0;
    const double game_score = points / static_cast<double>(played);
    std::cout.setf(std::ios::fixed);
    std::cout.precision(4);
    std::cout << "score " << game_score << " points " << points << "\n";

    // Pair result on a 0..1 scale (average of the two games). The 95% band is
    // the normal interval of that mean, then converted at the two score ends.
    double elo = 0.0;
    double margin = 0.0;
    double los = 0.5;
    auto elo_from_score = [](double score) {
        if (score <= 0.0) return -10000.0;
        if (score >= 1.0) return 10000.0;
        return -400.0 * std::log10(1.0 / score - 1.0);
    };
    if (paired > 0 && game_score > 0.0 && game_score < 1.0) {
        const double mean_pair = (pair_sum / static_cast<double>(paired)) / 2.0;
        double square = 0.0;
        for (double pair : pair_scores) {
            const double centered = pair / 2.0 - mean_pair;
            square += centered * centered;
        }
        const double variance = square / static_cast<double>(paired);
        const double variance_of_mean = variance / static_cast<double>(paired);
        constexpr double kZ95 = 1.959963984540054;
        const double half = kZ95 * std::sqrt(variance_of_mean);
        const double lower = std::max(0.0, mean_pair - half);
        const double upper = std::min(1.0, mean_pair + half);
        elo = elo_from_score(mean_pair);
        margin = (elo_from_score(upper) - elo_from_score(lower)) / 2.0;
        if (variance_of_mean > 0.0) {
            const double z = (mean_pair - 0.5) / std::sqrt(2.0 * variance_of_mean);
            los = (1.0 - std::erf(-z)) / 2.0;
        }
    } else if (game_score >= 1.0) {
        elo = 10000.0;
        los = 1.0;
    } else if (game_score <= 0.0) {
        elo = -10000.0;
        los = 0.0;
    }

    std::cout << "Elo95 " << elo << " +/- " << margin << "\n";
    std::cout.precision(2);
    std::cout << "LOS " << (100.0 * los) << "\n";
    std::cout << "pentanomial " << bins[0] << " " << bins[1] << " " << bins[2] << " " << bins[3] << " "
              << bins[4] << "\n";
    std::cout << "pairs " << paired << " unpaired_rounds " << unpaired_rounds << "\n";
    return 0;
}
