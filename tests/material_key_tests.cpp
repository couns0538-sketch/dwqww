// Job S11 (node-exact speed), UCI MaterialKeyTable: the contribution-table
// material key (forge/material_key_table.hpp) equals the search's Horner key.
//
//  1. Count domain. Both keys are a constant plus one independent term per
//     slot, so equality on the 650 single-slot vectors (each slot, counts
//     0..64; count 0 is the zero vector) proves equality for all 65^10 count
//     vectors. 100000 seeded random vectors are compared directly as well.
//  2. Boards. Seeded random legal walks from the opening file (default
//     1,000,000 positions) plus extreme-inventory fixtures: table key ==
//     polynomial key (all 64 bits), and the material index that the search
//     really uses, read through Worker::corrected_eval, is the same with the
//     option OFF and ON and equals the polynomial's index.
//  3. Search. The 8 positions of the UCI `bench` command at a fixed depth:
//     the same nodes, score and best move with the option OFF and ON.
//  4. Negative controls: a one-word table change and a one-count key error
//     are reported by the same checks.
// usage: forge_material_key_tests <openings.epd> [positions] [bench depth]
#include "forge/material_key_table.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static int eval(const Worker& w, const Board& b, int raw) { return w.corrected_eval(b, raw); }
    static CorrectionHistory& pawns(Worker& w) { return *w.correction_history_; }
    static CorrectionHistory& material(Worker& w) { return *w.material_correction_; }
};
} // namespace forge

using namespace forge;
using Probe = SearcherTestProbe;
using Counts = std::array<std::uint64_t, matkey::Slots>;

namespace {

int failures = 0;
int checks = 0;

void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << name << '\n';
}

// The AL1 s198 material key (src/search.cpp material_key with the option OFF),
// written on a count vector: the oracle.
std::uint64_t polynomial(const Counts& counts) {
    std::uint64_t key = 0;
    for (const std::uint64_t count : counts) key = key * 1099511628211ULL + count + 1U;
    return key * 0x9E3779B97F4A7C15ULL;
}

std::uint64_t table_sum(const matkey::ContributionTable& table, const Counts& counts) {
    std::uint64_t key = 0;
    for (std::size_t slot = 0; slot < matkey::Slots; ++slot) key += table[slot][counts[slot]];
    return key;
}

Counts counts_of(const Board& board) {
    Counts counts{};
    std::size_t slot = 0;
    for (const Color color : {White, Black}) {
        for (int type = Pawn; type <= Queen; ++type) {
            counts[slot++] = static_cast<std::uint64_t>(popcount(board.pieces(color, static_cast<PieceType>(type))));
        }
    }
    return counts;
}

// Mismatches of a table against the polynomial on the 650 single-slot vectors.
int basis_mismatches(const matkey::ContributionTable& table) {
    int mismatches = 0;
    for (std::size_t slot = 0; slot < matkey::Slots; ++slot) {
        for (std::size_t count = 0; count < matkey::CountValues; ++count) {
            Counts basis{};
            basis[slot] = count;
            if (table_sum(table, basis) != polynomial(basis)) ++mismatches;
        }
    }
    return mismatches;
}

struct Rng {
    std::uint64_t state;
    std::uint64_t next() {
        state ^= state << 13U;
        state ^= state >> 7U;
        state ^= state << 17U;
        return state;
    }
};

// The search's material index for `board`, read through the actual
// Worker::corrected_eval: with a zero pawn table and material[side][i] =
// i * CorrectionGrain, corrected_eval(board, 0) returns i.
int search_material_index(const Worker& worker, const Board& board) { return Probe::eval(worker, board, 0); }

void prepare_index_probe(Worker& worker) {
    worker.clear();
    for (auto& side : Probe::material(worker)) {
        for (std::size_t i = 0; i < CorrectionSize; ++i) side[i] = static_cast<std::int32_t>(i) * CorrectionGrain;
    }
}

std::vector<std::string> read_fens(const std::string& path) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("cannot open " + path);
    std::vector<std::string> fens;
    std::string line;
    while (std::getline(input, line)) {
        // EPD: four placement fields, then operations; complete the FEN.
        std::string fields[4];
        std::size_t position = 0;
        bool complete = true;
        for (std::string& field : fields) {
            while (position < line.size() && line[position] == ' ') ++position;
            const std::size_t end = line.find(' ', position);
            if (position >= line.size()) { complete = false; break; }
            field = line.substr(position, end == std::string::npos ? std::string::npos : end - position);
            position = end == std::string::npos ? line.size() : end;
        }
        if (complete) fens.push_back(fields[0] + ' ' + fields[1] + ' ' + fields[2] + ' ' + fields[3] + " 0 1");
    }
    return fens;
}

std::uint64_t parse_number(const char* text) {
    std::uint64_t value = 0;
    const std::string_view view(text);
    const auto parsed = std::from_chars(view.data(), view.data() + view.size(), value);
    if (parsed.ec != std::errc{} || parsed.ptr != view.data() + view.size()) throw std::runtime_error("bad number");
    return value;
}

struct BoardStats {
    std::uint64_t positions = 0;
    std::uint64_t key_mismatches = 0;
    std::uint64_t index_mismatches = 0;
    std::uint64_t oracle_index_mismatches = 0;
    std::uint64_t promoted_positions = 0;
    std::uint64_t capture_positions = 0;
    std::array<std::uint64_t, matkey::Slots> max_count{};
};

void check_board(const Board& board, Worker& worker, BoardStats& stats) {
    const Counts counts = counts_of(board);
    const std::uint64_t oracle = polynomial(counts);
    if (matkey::table_key(board) != oracle) ++stats.key_mismatches;
    options::material_key_table = false;
    const int off = search_material_index(worker, board);
    options::material_key_table = true;
    const int on = search_material_index(worker, board);
    options::material_key_table = false;
    if (off != on) ++stats.index_mismatches;
    if (static_cast<std::uint64_t>(off) != (oracle & (CorrectionSize - 1U))) ++stats.oracle_index_mismatches;
    ++stats.positions;
    bool promoted = false;
    bool captured = false;
    for (std::size_t slot = 0; slot < matkey::Slots; ++slot) {
        stats.max_count[slot] = std::max(stats.max_count[slot], counts[slot]);
        const std::size_t type = slot % 5;  // 0 pawn, 1 knight, 2 bishop, 3 rook, 4 queen
        const std::uint64_t initial = type == 0 ? 8 : type == 4 ? 1 : 2;
        if (counts[slot] > initial) promoted = true;
        if (counts[slot] < initial) captured = true;
    }
    stats.promoted_positions += promoted ? 1 : 0;
    stats.capture_positions += captured ? 1 : 0;
}

} // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) throw std::runtime_error("usage: forge_material_key_tests <openings.epd> [positions] [bench depth]");
        const std::uint64_t target = argc > 2 ? parse_number(argv[2]) : 1000000U;
        const int bench_depth = argc > 3 ? static_cast<int>(parse_number(argv[3])) : 11;
        std::cout << "S11 MaterialKeyTable: contribution-table key vs the search's Horner key\n";
        check(!options::material_key_table, "option MaterialKeyTable is off by default");

        // 1. Count domain.
        const int basis = basis_mismatches(matkey::Contributions);
        std::cout << "count domain: 650 single-slot vectors, mismatches " << basis << '\n';
        check(basis == 0, "table equals the polynomial on every single-slot vector (proof for all 65^10 vectors)");
        Rng rng{0x5110C0DE2026ULL};
        int random_mismatches = 0;
        for (int i = 0; i < 100000; ++i) {
            Counts counts{};
            for (std::uint64_t& count : counts) count = rng.next() % matkey::CountValues;
            if (table_sum(matkey::Contributions, counts) != polynomial(counts)) ++random_mismatches;
        }
        std::cout << "count domain: 100000 random vectors, mismatches " << random_mismatches << '\n';
        check(random_mismatches == 0, "table equals the polynomial on 100000 random count vectors");

        // 2. Boards: the opening file walked at random, plus extreme inventories.
        SharedSearchState shared(1);
        auto worker = std::make_unique<Worker>(shared, 0);
        prepare_index_probe(*worker);
        check(tune::MaterialCorrectionWeight > 0, "material correction is active (MaterialCorrectionWeight > 0)");
        BoardStats stats;
        const std::array<std::string, 6> fixtures{
            std::string(Board::StandardStartFen),
            "8/8/8/8/8/8/8/K6k w - - 0 1",                       // all counts zero
            "NNNNNNNN/NN6/8/8/8/8/8/K6k w - - 0 1",              // ten white knights
            "qqqqqqqq/q7/8/8/8/8/8/K6k w - - 0 1",               // nine black queens
            "k7/8/8/8/8/8/1BBBBBBB/BBBK4 b - - 0 1",             // ten white bishops
            "rrrrrrrr/rr6/8/8/8/k7/8/7K w - - 0 1",              // ten black rooks
        };
        int fixtures_set = 0;
        for (const std::string& fen : fixtures) {
            Board board;
            std::string error;
            if (!board.set_fen(fen, &error)) {
                std::cout << "fixture rejected: " << fen << " (" << error << ")\n";
                continue;
            }
            ++fixtures_set;
            check_board(board, *worker, stats);
        }
        check(fixtures_set == static_cast<int>(fixtures.size()), "every extreme-inventory fixture is a legal board");
        const std::vector<std::string> fens = read_fens(argv[1]);
        std::cout << "opening positions: " << fens.size() << '\n';
        check(!fens.empty(), "opening file has positions");
        Rng walk{20261027ULL};
        std::size_t opening = 0;
        std::uint64_t walks = 0;
        while (stats.positions < target && !fens.empty()) {
            Board board;
            if (!board.set_fen(fens[opening++ % fens.size()])) continue;
            ++walks;
            const int plies = 40 + static_cast<int>(walk.next() % 200U);
            for (int ply = 0; ply <= plies && stats.positions < target; ++ply) {
                check_board(board, *worker, stats);
                const MoveList moves = board.legal_moves();
                if (moves.empty()) break;
                const Move move = moves[static_cast<std::size_t>(walk.next() % moves.size())];
                Undo undo;
                (void)board.make_move(move, undo);
            }
        }
        std::cout << "boards: " << stats.positions << " positions (" << walks << " random walks), " << stats.promoted_positions
                  << " with promoted material, " << stats.capture_positions << " with captured material; max count per slot";
        for (const std::uint64_t count : stats.max_count) std::cout << ' ' << count;
        std::cout << "\nboards: key mismatches " << stats.key_mismatches << ", search index OFF/ON mismatches "
                  << stats.index_mismatches << ", search index vs polynomial mismatches " << stats.oracle_index_mismatches << '\n';
        check(stats.positions >= target, "board check covered the requested number of positions");
        check(stats.key_mismatches == 0, "table key equals the polynomial key on every board (64 bits)");
        check(stats.index_mismatches == 0, "the search's material index is the same with MaterialKeyTable off and on");
        check(stats.oracle_index_mismatches == 0, "the search's material index equals the polynomial's index");
        check(stats.promoted_positions > 0 && stats.capture_positions > 0, "walks reached captures and promotions");

        // 3. Search: the UCI bench positions, option OFF then ON.
        constexpr std::array<std::string_view, 8> bench_fens{
            Board::StandardStartFen,
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
            "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
            "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
            "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
        };
        std::array<std::array<SearchInfo, 8>, 2> results{};
        std::array<std::uint64_t, 2> totals{};
        for (const bool on : {false, true}) {
            options::material_key_table = on;
            Searcher searcher(16);
            for (std::size_t i = 0; i < bench_fens.size(); ++i) {
                Board board;
                if (!board.set_fen(bench_fens[i])) throw std::runtime_error("bad bench FEN");
                SearchLimits limits;
                limits.depth = bench_depth;
                searcher.clear();
                results[on ? 1U : 0U][i] = searcher.search(board, limits, false, Searcher::TTAccess::Exclusive);
                totals[on ? 1U : 0U] += results[on ? 1U : 0U][i].nodes;
            }
        }
        options::material_key_table = false;
        bool same = true;
        for (std::size_t i = 0; i < bench_fens.size(); ++i) {
            const SearchInfo& off = results[0][i];
            const SearchInfo& on = results[1][i];
            const bool equal = off.nodes == on.nodes && off.score == on.score && off.best_move == on.best_move &&
                               off.depth == on.depth && off.pv == on.pv;
            same = same && equal;
            std::cout << "bench d" << bench_depth << " position " << i << " nodes off " << off.nodes << " on " << on.nodes
                      << " score " << off.score << '/' << on.score << " move " << Board::move_to_uci(off.best_move) << '/'
                      << Board::move_to_uci(on.best_move) << (equal ? "" : " DIFFERENT") << '\n';
        }
        std::cout << "bench d" << bench_depth << " total nodes off " << totals[0] << " on " << totals[1] << '\n';
        check(same && totals[0] == totals[1], "bench positions: same nodes, score, best move and PV with MaterialKeyTable off and on");

        // 4. Negative controls: the checks above must notice small errors.
        matkey::ContributionTable broken = matkey::Contributions;
        broken[0][8] += 1U;  // eight white pawns
        check(basis_mismatches(broken) == 1, "control: a one-word table change is caught by the count-domain check");
        Board start;
        (void)start.set_fen(Board::StandardStartFen);
        Counts off_by_one = counts_of(start);
        off_by_one[9] += 1U;  // one black queen too many
        check(polynomial(off_by_one) != matkey::table_key(start), "control: a one-count key error is caught by the board check");
    } catch (const std::exception& error) {
        std::cout << "FAIL exception: " << error.what() << '\n';
        ++failures;
    }
    std::cout << (failures == 0 ? "ALL PASS " : "FAILURES ") << failures << " of " << checks << " checks failed\n";
    return failures == 0 ? 0 : 1;
}
