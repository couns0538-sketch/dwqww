#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

enum class Kind { Exact, Timed, Short };

struct Expect {
    Kind kind = Kind::Exact;
    std::string best;
    std::string stable;
    int min_wall_ms = 0;
    int max_wall_ms = 0;
    int max_depth = 0;
    int line = 0;
};

struct Search {
    std::string last_info;
    std::string best;
    double wall_ms = 0;
    bool saw_info = false;
};

std::string trim(std::string text) {
    while (!text.empty() && (text.back() == '\r' || text.back() == ' ' || text.back() == '\t')) text.pop_back();
    std::size_t i = 0;
    while (i < text.size() && (text[i] == ' ' || text[i] == '\t')) ++i;
    return text.substr(i);
}

std::vector<Expect> load_expected(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        std::cerr << "fail: cannot read " << path << "\n";
        std::exit(2);
    }
    std::vector<Expect> out;
    std::string line;
    int number = 0;
    while (std::getline(in, line)) {
        ++number;
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;
        std::istringstream row(line);
        std::string kind;
        if (!(row >> kind)) continue;
        Expect expect;
        expect.line = number;
        if (kind == "exact") {
            expect.kind = Kind::Exact;
            if (!(row >> expect.best)) {
                std::cerr << "fail: expected file line " << number << " has no move\n";
                std::exit(2);
            }
            std::string rest;
            std::getline(row, rest);
            expect.stable = trim(rest);
            if (expect.stable.empty()) {
                std::cerr << "fail: expected file line " << number << " has no info line\n";
                std::exit(2);
            }
        } else if (kind == "timed") {
            expect.kind = Kind::Timed;
            if (!(row >> expect.min_wall_ms >> expect.max_wall_ms)) {
                std::cerr << "fail: expected file line " << number << " needs min and max wall ms\n";
                std::exit(2);
            }
        } else if (kind == "short") {
            expect.kind = Kind::Short;
            if (!(row >> expect.max_wall_ms >> expect.max_depth)) {
                std::cerr << "fail: expected file line " << number << " needs max wall ms and max depth\n";
                std::exit(2);
            }
        } else {
            std::cerr << "fail: expected file line " << number << " has unknown kind " << kind << "\n";
            std::exit(2);
        }
        out.push_back(std::move(expect));
    }
    return out;
}

std::string stable_info(const std::string& line) {
    std::istringstream in(line);
    std::string token;
    std::string out;
    while (in >> token) {
        if (token == "nps" || token == "hashfull" || token == "time") {
            std::string skip;
            in >> skip;
            continue;
        }
        if (!out.empty()) out += ' ';
        out += token;
    }
    return out;
}

std::string best_move(const std::string& line) {
    std::istringstream in(line);
    std::string command;
    std::string move;
    in >> command >> move;
    return move;
}

int info_depth(const std::string& line) {
    std::istringstream in(line);
    std::string info;
    std::string depth;
    int value = -1;
    in >> info >> depth >> value;
    return value;
}

std::vector<Search> read_searches() {
    std::vector<Search> searches;
    Search current;
    bool in_search = false;
    auto started = std::chrono::steady_clock::time_point{};
    std::string line;
    while (std::getline(std::cin, line)) {
        line = trim(line);
        const auto now = std::chrono::steady_clock::now();
        if (line.rfind("info depth ", 0) == 0) {
            if (!in_search) {
                started = now;
                in_search = true;
                current = Search{};
            }
            current.last_info = line;
            current.saw_info = true;
            continue;
        }
        if (line.rfind("bestmove ", 0) == 0) {
            current.best = line;
            if (in_search) {
                current.wall_ms = std::chrono::duration<double, std::milli>(now - started).count();
            }
            searches.push_back(current);
            current = Search{};
            in_search = false;
        }
    }
    return searches;
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: check_clock expected.txt < engine-stdout\n";
        return 2;
    }
    const std::vector<Expect> expected = load_expected(argv[1]);
    const std::vector<Search> searches = read_searches();
    int failures = 0;
    const std::size_t n = std::max(expected.size(), searches.size());
    for (std::size_t i = 0; i < n; ++i) {
        if (i >= expected.size()) {
            std::cout << "fail " << (i + 1) << ": unexpected extra search\n";
            ++failures;
            continue;
        }
        if (i >= searches.size()) {
            std::cout << "fail " << (i + 1) << ": missing search (expected file line " << expected[i].line << ")\n";
            ++failures;
            continue;
        }
        const Expect& want = expected[i];
        const Search& got = searches[i];
        const std::string move = best_move(got.best);
        const int depth = got.saw_info ? info_depth(got.last_info) : -1;
        auto fail = [&](const std::string& why) {
            std::cout << "fail " << (i + 1) << ": " << why << "\n";
            std::cout << "  wall_ms " << got.wall_ms << " depth " << depth << "\n";
            std::cout << "  best " << got.best << "\n";
            if (got.saw_info) std::cout << "  info " << stable_info(got.last_info) << "\n";
            ++failures;
        };
        if (!got.saw_info || move.empty()) {
            fail("search produced no info depth line or no bestmove");
            continue;
        }
        if (want.kind == Kind::Exact) {
            const std::string stable = stable_info(got.last_info);
            if (move != want.best || stable != want.stable) {
                fail("exact mismatch");
                std::cout << "  expected best " << want.best << "\n";
                std::cout << "  expected info " << want.stable << "\n";
                continue;
            }
        } else if (want.kind == Kind::Timed) {
            if (got.wall_ms < want.min_wall_ms || got.wall_ms > want.max_wall_ms) {
                fail("wall time outside " + std::to_string(want.min_wall_ms) + ".." +
                     std::to_string(want.max_wall_ms) + " ms");
                continue;
            }
        } else if (want.kind == Kind::Short) {
            if (got.wall_ms > want.max_wall_ms || depth > want.max_depth) {
                fail("expected a short search, wall <= " + std::to_string(want.max_wall_ms) +
                     " ms and depth <= " + std::to_string(want.max_depth));
                continue;
            }
        }
        std::cout << "ok " << (i + 1) << " wall_ms " << got.wall_ms << " depth " << depth
                  << " best " << move << "\n";
    }
    if (failures != 0) {
        std::cout << "fail " << failures << "\n";
        return 1;
    }
    std::cout << "pass\n";
    return 0;
}
