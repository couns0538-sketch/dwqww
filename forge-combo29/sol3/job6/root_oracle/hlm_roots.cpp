#include "forge/hlm_probe.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

constexpr std::uint64_t ExpectedRoots = 8612;
constexpr std::uint64_t ExpectedFixtures = 389;
constexpr std::size_t FixtureDepth = 2;

struct Audit {
    forge::HlmProbeStats stats{};
    std::string first_site;
};

std::uint64_t observations(const Audit& audit) {
    return audit.stats.checked.calls + audit.stats.unchecked.calls;
}

void print_group(std::string_view set, std::string_view group, std::uint64_t positions,
                 std::uint64_t in_check, std::uint64_t nomove, std::uint64_t mismatch) {
    std::cout << "set=" << set << " group=" << group << " positions=" << positions
              << " in_check=" << in_check << " nomove=" << nomove << " mismatch=" << mismatch << '\n';
}

void print_set(std::string_view set, const Audit& audit) {
    const auto& checked = audit.stats.checked;
    const auto& unchecked = audit.stats.unchecked;
    print_group(set, "all", observations(audit), checked.calls,
                checked.nomove + unchecked.nomove, checked.mismatch + unchecked.mismatch);
    print_group(set, "in_check", checked.calls, checked.calls, checked.nomove, checked.mismatch);
    print_group(set, "not_in_check", unchecked.calls, 0, unchecked.nomove, unchecked.mismatch);
    if (audit.stats.first_mismatch) {
        const auto& first = *audit.stats.first_mismatch;
        std::cout << "set=" << set << " first_mismatch " << audit.first_site
                  << " fast=" << first.result.fast << " full=" << first.result.full
                  << " in_check=" << first.result.in_check << " fen=" << std::quoted(first.fen) << '\n';
    } else {
        std::cout << "set=" << set << " first_mismatch=none\n";
    }
}

void load_fen(forge::Board& board, std::string_view fen, const std::string& site) {
    std::string error;
    if (!board.set_fen(fen, &error)) {
        throw std::runtime_error(site + ": invalid FEN: " + error);
    }
}

Audit audit_roots(const char* path) {
    std::ifstream roots(path);
    if (!roots) throw std::runtime_error(std::string("Cannot open ") + path);
    Audit audit;
    forge::Board board;
    std::string command;
    std::uint64_t line = 0;
    while (std::getline(roots, command)) {
        ++line;
        const std::string site = "root_line=" + std::to_string(line);
        std::istringstream input(command);
        std::string position, start, moves;
        if (!(input >> position >> start >> moves) || position != "position" ||
            start != "startpos" || moves != "moves") {
            throw std::runtime_error(site + ": expected one complete position startpos moves command");
        }
        load_fen(board, forge::Board::StandardStartFen, site);
        std::string token;
        std::uint64_t played_plies = 0;
        while (input >> token) {
            ++played_plies;
            const auto move = board.parse_uci(token);
            forge::Undo undo;
            if (!move || !board.make_move(*move, undo)) {
                throw std::runtime_error(site + ": illegal move at ply " + std::to_string(played_plies) + ": " + token);
            }
        }
        if (played_plies == 0) throw std::runtime_error(site + ": empty move history");
        const auto result = forge::probe_has_legal_move(board, audit.stats);
        if (result.fast != result.full && audit.first_site.empty()) {
            audit.first_site = site + " played_plies=" + std::to_string(played_plies);
        }
    }
    if (!roots.eof() || line != ExpectedRoots || observations(audit) != line) {
        throw std::runtime_error("Expected 8612 complete root commands, read " + std::to_string(line));
    }
    return audit;
}

void visit_fixture(forge::Board& board, std::uint64_t line, std::size_t depth,
                   std::array<forge::Move, FixtureDepth>& path,
                   std::array<std::uint64_t, FixtureDepth + 1>& by_depth, Audit& audit) {
    ++by_depth[depth];
    forge::MoveList moves;
    const auto result = forge::probe_has_legal_move(board, audit.stats, depth < FixtureDepth ? &moves : nullptr);
    if (result.fast != result.full && audit.first_site.empty()) {
        std::string site = "fixture_line=" + std::to_string(line) + " depth=" + std::to_string(depth) + " path=";
        if (depth == 0) site += "root";
        for (std::size_t i = 0; i < depth; ++i) {
            if (i != 0) site += ',';
            site += forge::Board::move_to_uci(path[i]);
        }
        audit.first_site = site;
    }
    if (depth == FixtureDepth) return;
    for (const forge::Move move : moves) {
        forge::Undo undo;
        if (!board.make_move(move, undo)) {
            throw std::runtime_error("Full generator yielded an unplayable move at fixture line " + std::to_string(line));
        }
        path[depth] = move;
        visit_fixture(board, line, depth + 1, path, by_depth, audit);
        board.unmake_move(move, undo);
    }
}

Audit audit_fixtures(const char* path, std::array<std::uint64_t, FixtureDepth + 1>& by_depth) {
    std::ifstream fixtures(path);
    if (!fixtures) throw std::runtime_error(std::string("Cannot open ") + path);
    Audit audit;
    forge::Board board;
    std::array<forge::Move, FixtureDepth> moves{};
    std::uint64_t line = 0;
    std::string fen;
    while (std::getline(fixtures, fen)) {
        ++line;
        load_fen(board, fen, "fixture_line=" + std::to_string(line));
        visit_fixture(board, line, 0, moves, by_depth, audit);
    }
    if (!fixtures.eof() || line != ExpectedFixtures || observations(audit) != by_depth[0] + by_depth[1] + by_depth[2]) {
        throw std::runtime_error("Expected 389 complete fixture FENs, read " + std::to_string(line));
    }
    return audit;
}

Audit combined(const Audit& roots, const Audit& fixtures) {
    Audit result = roots;
    result.stats.checked.calls += fixtures.stats.checked.calls;
    result.stats.checked.nomove += fixtures.stats.checked.nomove;
    result.stats.checked.mismatch += fixtures.stats.checked.mismatch;
    result.stats.unchecked.calls += fixtures.stats.unchecked.calls;
    result.stats.unchecked.nomove += fixtures.stats.unchecked.nomove;
    result.stats.unchecked.mismatch += fixtures.stats.unchecked.mismatch;
    if (!result.stats.first_mismatch && fixtures.stats.first_mismatch) {
        result.stats.first_mismatch = fixtures.stats.first_mismatch;
        result.first_site = fixtures.first_site;
    }
    return result;
}

} // namespace

int main(int argc, char** argv) {
    if (argc != 3) {
        std::cerr << "usage: hlm_roots <timed-position-commands.txt> <positions.txt>\n";
        return 2;
    }
    try {
        const Audit roots = audit_roots(argv[1]);
        std::array<std::uint64_t, FixtureDepth + 1> by_depth{};
        const Audit fixtures = audit_fixtures(argv[2], by_depth);
        std::cout << "counting=position_paths_including_duplicates fixture_max_depth=" << FixtureDepth << '\n';
        std::cout << "fixture_positions_by_depth depth0=" << by_depth[0]
                  << " depth1=" << by_depth[1] << " depth2=" << by_depth[2] << '\n';
        print_set("whole_game_roots", roots);
        print_set("fixture_paths", fixtures);
        print_set("combined", combined(roots, fixtures));
    } catch (const std::exception& ex) {
        std::cerr << "ERROR " << ex.what() << '\n';
        return 1;
    }
    return 0;
}
