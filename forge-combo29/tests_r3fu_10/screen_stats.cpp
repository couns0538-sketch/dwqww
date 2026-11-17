#include <cmath>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <utility>
#include <vector>

// Screening arithmetic for one PGN. Option-on is the engine named EvasionOn.
// Pair two color-swapped games that share a FEN. Elo, the 95% interval, and
// LOS follow the pentanomial mean and its variance: each pair contributes its
// average game score, the variance is the mean squared deviation of those
// pair averages, and the interval is the logistic Elo of the score bounds at
// z = 1.959963984540054. This is a screen summary, not a strength claim.

namespace {

constexpr double kZ95 = 1.959963984540054;
constexpr const char* kOn = "EvasionOn";

struct Header {
    std::string white;
    std::string black;
    std::string result;
    std::string fen;
    bool seen = false;
};

[[nodiscard]] std::string tag_value(const std::string& line) {
    const auto q1 = line.find('"');
    const auto q2 = line.rfind('"');
    if (q1 == std::string::npos || q2 <= q1) return {};
    return line.substr(q1 + 1, q2 - q1 - 1);
}

[[nodiscard]] std::string tag_name(const std::string& line) {
    const auto end = line.find(' ');
    if (line.empty() || line[0] != '[' || end == std::string::npos) return {};
    return line.substr(1, end - 1);
}

void consume(Header& game, const std::string& line) {
    const std::string name = tag_name(line);
    if (name.empty()) return;
    game.seen = true;
    const std::string value = tag_value(line);
    if (name == "White") game.white = value;
    else if (name == "Black") game.black = value;
    else if (name == "Result") game.result = value;
    else if (name == "FEN") game.fen = value;
}

[[nodiscard]] bool on_score(const Header& game, double& score) {
    if (game.result == "1/2-1/2") {
        score = 0.5;
        return true;
    }
    const bool on_white = game.white == kOn;
    const bool on_black = game.black == kOn;
    if (on_white == on_black) return false;
    if (game.result == "1-0") score = on_white ? 1.0 : 0.0;
    else if (game.result == "0-1") score = on_white ? 0.0 : 1.0;
    else return false;
    return true;
}

[[nodiscard]] double elo_from_score(double score) {
    return -400.0 * std::log10(1.0 / score - 1.0);
}

struct Totals {
    int wins = 0;
    int losses = 0;
    int draws = 0;
    int skipped = 0;
    int ww = 0;
    int wd = 0;
    int wl = 0;
    int dd = 0;
    int ld = 0;
    int ll = 0;
    int unpaired = 0;
};

void add_game(Totals& t, double score) {
    if (score == 1.0) ++t.wins;
    else if (score == 0.0) ++t.losses;
    else ++t.draws;
}

void add_pair(Totals& t, double a, double b) {
    const double sum = a + b;
    if (sum == 2.0) ++t.ww;
    else if (sum == 1.5) ++t.wd;
    else if (sum == 0.5) ++t.ld;
    else if (sum == 0.0) ++t.ll;
    else if (a == 0.5 && b == 0.5) ++t.dd;
    else ++t.wl;
}

void report(const Totals& t) {
    const int games = t.wins + t.losses + t.draws;
    const double points = t.wins + 0.5 * t.draws;
    const int pairs = t.ww + t.wd + t.wl + t.dd + t.ld + t.ll;
    std::cout << "W-L-D " << t.wins << '-' << t.losses << '-' << t.draws << '\n';
    std::cout << "games " << games << " points " << points;
    if (games > 0) std::cout << " score " << (points / games);
    std::cout << '\n';
    std::cout << "pentanomial LL LD WL DD WD WW " << t.ll << ' ' << t.ld << ' ' << t.wl << ' ' << t.dd << ' '
              << t.wd << ' ' << t.ww << '\n';
    std::cout << "Ptnml(0-2) " << t.ll << ' ' << t.ld << ' ' << (t.wl + t.dd) << ' ' << t.wd << ' ' << t.ww << '\n';
    std::cout << "pairs " << pairs << " unpaired_games " << t.unpaired << " skipped " << t.skipped << '\n';
    if (pairs < 2 || games == 0 || points <= 0.0 || points >= games) {
        std::cout << "elo insufficient\n";
        return;
    }
    const double score = (t.ww + 0.75 * t.wd + 0.5 * (t.wl + t.dd) + 0.25 * t.ld) / pairs;
    const double ww = double(t.ww) / pairs;
    const double wd = double(t.wd) / pairs;
    const double mid = double(t.wl + t.dd) / pairs;
    const double ld = double(t.ld) / pairs;
    const double ll = double(t.ll) / pairs;
    const double variance = ww * std::pow(1.0 - score, 2) + wd * std::pow(0.75 - score, 2) +
                            mid * std::pow(0.5 - score, 2) + ld * std::pow(0.25 - score, 2) +
                            ll * std::pow(0.0 - score, 2);
    const double variance_per_pair = variance / pairs;
    const double se = std::sqrt(variance_per_pair);
    const double upper = score + kZ95 * se;
    const double lower = score - kZ95 * se;
    const double elo = elo_from_score(score);
    const double error = (elo_from_score(upper) - elo_from_score(lower)) / 2.0;
    const double los = (1.0 - std::erf(-(score - 0.5) / std::sqrt(2.0 * variance_per_pair))) / 2.0;
    std::cout.setf(std::ios::fixed);
    std::cout.precision(2);
    std::cout << "Elo " << elo << " +/- " << error << " (95%)\n";
    std::cout << "LOS " << (los * 100.0) << " %\n";
    std::cout << "screen_only not_a_strength_claim\n";
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: screen_stats pgn...\n";
        return 2;
    }
    std::map<std::string, std::vector<double>> by_fen;
    Totals totals;
    for (int i = 1; i < argc; ++i) {
        std::ifstream in(argv[i]);
        if (!in) {
            std::cerr << "cannot read " << argv[i] << '\n';
            return 1;
        }
        Header game;
        std::string line;
        auto flush = [&]() {
            if (!game.seen) return;
            double score = 0.0;
            if (!on_score(game, score) || game.fen.empty()) ++totals.skipped;
            else {
                add_game(totals, score);
                by_fen[game.fen].push_back(score);
            }
            game = Header{};
        };
        while (std::getline(in, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (line.rfind("[Event ", 0) == 0 && game.seen) flush();
            if (!line.empty() && line[0] == '[') consume(game, line);
        }
        flush();
    }
    for (const auto& item : by_fen) {
        const std::vector<double>& scores = item.second;
        if (scores.size() != 2) {
            totals.unpaired += static_cast<int>(scores.size());
            continue;
        }
        add_pair(totals, scores[0], scores[1]);
    }
    report(totals);
    return 0;
}
