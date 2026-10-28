// R3-5 perft regression suite: 20 positions (the start position, Kiwipete, Chessprogramming-wiki positions 3-6
// and position 4 mirrored, and edge cases for en passant, castling, promotion, pins, checks, stalemate and mate)
// against published node counts at depth 5 or more (tests/data/perft_suite.tsv; every count was recomputed with
// python-chess, opus_r3/R3-5/logs/perft_crosscheck.log).
//
//   forge_perft_suite <perft_suite.tsv> [--group cpw|edge|all] [--max-depth D] [--max-nodes N]
//
// Each position runs at its deepest published depth <= D (default 6) whose count is <= N (default: no limit);
// a position whose published counts are all deeper than D (the small edge positions, published at depth 6 or 7
// only) runs at its shallowest published depth. CMakeLists.txt passes D = 6 in plain builds, D = 5 in
// sanitizer builds, and D = 5 with N = 20000000 in ThreadSanitizer builds (perft is single-threaded, so TSan
// finds nothing there; there kiwipete and positions 5 and 6 run at depth 4). Every position must also be left
// unchanged by perft (FEN, key, history length).
#include "forge/board.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

struct Reference {
    int depth = 0;
    std::uint64_t nodes = 0;
};

struct Case {
    std::string id;
    std::string group;
    std::string fen;
    std::vector<Reference> refs;
    std::string sources;
    std::string theme;
};

int failures = 0;

void fail(const std::string& message) {
    std::cout << "FAIL " << message << '\n';
    ++failures;
}

std::vector<std::string> split(const std::string& text, char separator) {
    std::vector<std::string> out;
    std::string field;
    std::istringstream stream(text);
    while (std::getline(stream, field, separator)) out.push_back(field);
    return out;
}

std::vector<Case> read_suite(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        fail("cannot open " + path);
        return {};
    }
    std::vector<Case> cases;
    std::string line;
    int line_number = 0;
    while (std::getline(in, line)) {
        ++line_number;
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty() || line.front() == '#') continue;
        const std::vector<std::string> fields = split(line, '\t');
        if (fields.size() != 6) {
            fail(path + ":" + std::to_string(line_number) + ": expected 6 tab-separated fields");
            continue;
        }
        Case item{fields[0], fields[1], fields[2], {}, fields[4], fields[5]};
        std::istringstream refs(fields[3]);
        std::string token;
        while (refs >> token) {
            const std::size_t colon = token.find(':');
            if (colon == std::string::npos) {
                fail(path + ":" + std::to_string(line_number) + ": bad reference " + token);
                continue;
            }
            item.refs.push_back({std::stoi(token.substr(0, colon)), std::stoull(token.substr(colon + 1))});
        }
        std::sort(item.refs.begin(), item.refs.end(), [](const Reference& a, const Reference& b) { return a.depth < b.depth; });
        cases.push_back(item);
    }
    return cases;
}

// The reference to run under the depth / node caps (see the head of the file); depth 0 = none.
Reference choose(const Case& item, int max_depth, std::uint64_t max_nodes) {
    std::vector<Reference> affordable;
    for (const Reference& ref : item.refs) {
        if (max_nodes == 0 || ref.nodes <= max_nodes) affordable.push_back(ref);
    }
    if (affordable.empty()) return {};
    Reference best{};
    for (const Reference& ref : affordable) {
        if (ref.depth <= max_depth) best = ref;  // ascending: the deepest one wins
    }
    return best.depth != 0 ? best : affordable.front();
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: forge_perft_suite <perft_suite.tsv> [--group cpw|edge|all] [--max-depth D] [--max-nodes N]\n";
        return 2;
    }
    const std::string path = argv[1];
    std::string group = "all";
    int max_depth = 6;
    std::uint64_t max_nodes = 0;
    for (int i = 2; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--group" && i + 1 < argc) group = argv[++i];
        else if (arg == "--max-depth" && i + 1 < argc) max_depth = std::atoi(argv[++i]);
        else if (arg == "--max-nodes" && i + 1 < argc) max_nodes = std::strtoull(argv[++i], nullptr, 10);
        else {
            std::cerr << "unknown argument " << arg << '\n';
            return 2;
        }
    }
    const std::vector<Case> cases = read_suite(path);

    // Data checks: at least 20 positions, unique ids, each with a published count at depth >= 5.
    int all_positions = 0;
    std::vector<std::string> ids;
    for (const Case& item : cases) {
        ++all_positions;
        if (std::find(ids.begin(), ids.end(), item.id) != ids.end()) fail("duplicate id " + item.id);
        ids.push_back(item.id);
        if (item.refs.empty() || item.refs.back().depth < 5) fail(item.id + ": no published count at depth >= 5");
        if (item.group != "cpw" && item.group != "edge") fail(item.id + ": unknown group " + item.group);
    }
    if (all_positions < 20) fail("the suite has " + std::to_string(all_positions) + " positions, expected at least 20");

    std::cout << "perft suite " << path << ": group " << group << ", max depth " << max_depth << ", max nodes "
              << (max_nodes == 0 ? std::string("none") : std::to_string(max_nodes)) << '\n';
    int run = 0;
    int below_five = 0;
    std::uint64_t total_nodes = 0;
    const auto suite_start = std::chrono::steady_clock::now();
    for (const Case& item : cases) {
        if (group != "all" && item.group != group) continue;
        const Reference ref = choose(item, max_depth, max_nodes);
        if (ref.depth == 0) {
            std::cout << "SKIP " << item.id << ": every published count is above --max-nodes\n";
            continue;
        }
        forge::Board board;
        std::string error;
        if (!board.set_fen(item.fen, &error)) {
            fail(item.id + ": FEN rejected (" + error + "): " + item.fen);
            continue;
        }
        const std::string fen_before = board.fen();
        const std::uint64_t key_before = board.key();
        const std::size_t history_before = board.history_size();
        const auto start = std::chrono::steady_clock::now();
        const std::uint64_t nodes = board.perft(ref.depth);
        const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
        ++run;
        total_nodes += nodes;
        if (ref.depth < 5) ++below_five;
        const bool ok = nodes == ref.nodes;
        std::cout << (ok ? "PASS " : "FAIL ") << item.id << " depth " << ref.depth << " expected " << ref.nodes << " got "
                  << nodes << " (" << ms << " ms; " << item.theme << "; " << item.sources << ")"
                  << (ref.depth < 5 ? "  [depth below 5: --max-nodes cap]" : "") << '\n';
        if (!ok) ++failures;
        if (board.fen() != fen_before || board.key() != key_before || board.history_size() != history_before) {
            fail(item.id + ": perft changed the position");
        }
    }
    const auto total_ms =
        std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - suite_start).count();
    if (run == 0) fail("no position ran (group " + group + ")");
    std::cout << "perft suite: " << run << " positions, " << total_nodes << " nodes, " << total_ms << " ms, "
              << below_five << " below depth 5, failures " << failures << '\n';
    std::cout << (failures == 0 ? "PASS" : "FAIL") << " forge_perft_suite\n";
    return failures == 0 ? 0 : 1;
}
