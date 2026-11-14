#include "forge/eval.hpp"
#include "forge/search.hpp"
#include "forge/uci.hpp"

#include <chrono>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void fail(const std::string& message) {
    std::cerr << "fail: " << message << '\n';
    ++g_failures;
}

std::string run_uci(const std::string& commands) {
    std::stringstream input(commands);
    std::stringstream output;
    std::streambuf* previous = std::cout.rdbuf(output.rdbuf());
    const int code = forge::uci_loop(input);
    std::cout.rdbuf(previous);
    if (code != 0) fail("uci_loop returned " + std::to_string(code));
    return output.str();
}

struct Scored {
    bool recognized = false;
    int score = 0;
    bool fen_ok = false;
};

Scored score_fen(const std::string& fen) {
    Scored result;
    forge::Board board;
    result.fen_ok = board.set_fen(fen);
    if (!result.fen_ok) return result;
    int score = 0;
    result.recognized = forge::dead_material_score(board, score);
    result.score = score;
    return result;
}

std::string other_side(std::string fen) {
    const auto white = fen.find(" w ");
    if (white != std::string::npos) {
        fen.replace(white, 3, " b ");
        return fen;
    }
    const auto black = fen.find(" b ");
    if (black != std::string::npos) fen.replace(black, 3, " w ");
    return fen;
}

void expect_draw(const char* name, const char* fen) {
    for (const std::string& side : {std::string(fen), other_side(fen)}) {
        const Scored scored = score_fen(side);
        if (!scored.fen_ok) fail(std::string(name) + " rejected fen " + side);
        else if (!scored.recognized || scored.score != 0) {
            fail(std::string(name) + " score " + std::to_string(scored.score) +
                 " recognized " + (scored.recognized ? "yes" : "no") + " " + side);
        }
    }
}

void expect_unrecognized(const char* name, const char* fen) {
    const Scored scored = score_fen(fen);
    if (!scored.fen_ok) fail(std::string(name) + " rejected fen " + fen);
    else if (scored.recognized) fail(std::string(name) + " was recognized " + fen);
}

bool move_is_legal(const forge::Board& board, forge::Move move) {
    const forge::MoveList legal = board.legal_moves();
    if (move.is_none()) return legal.empty();
    for (const forge::Move candidate : legal) {
        if (candidate == move) return true;
    }
    return false;
}

bool pv_is_legal(const forge::Board& board, const std::vector<forge::Move>& pv) {
    forge::Board cursor = board;
    for (const forge::Move move : pv) {
        if (!move_is_legal(cursor, move)) return false;
        forge::Undo undo;
        if (!cursor.make_move(move, undo)) return false;
    }
    return true;
}

}  // namespace

int main() {
    if (forge::dead_material_enabled) fail("DeadMaterial starts enabled");

    const std::string banner = run_uci("uci\nquit\n");
    const std::string option_line = "option name DeadMaterial type check default false";
    if (banner.find(option_line) == std::string::npos) fail("uci answer missing DeadMaterial");
    if (banner.find(option_line) != banner.rfind(option_line)) fail("DeadMaterial listed twice");
    if (forge::dead_material_enabled) fail("uci command enabled DeadMaterial");

    const std::string enabled = run_uci("setoption name DeadMaterial value true\nquit\n");
    if (!forge::dead_material_enabled) fail("setoption true did not enable DeadMaterial");
    const std::string rejected = run_uci("setoption name DeadMaterial value maybe\nquit\n");
    if (!forge::dead_material_enabled) fail("invalid value changed DeadMaterial");
    if (rejected.find("invalid value for option DeadMaterial") == std::string::npos) {
        fail("invalid DeadMaterial value was not reported");
    }
    run_uci("setoption name DeadMaterial value false\nquit\n");
    if (forge::dead_material_enabled) fail("setoption false left DeadMaterial on");

    expect_draw("bare kings", "8/8/8/4k3/8/8/4K3/8 w - - 0 1");
    expect_draw("white knight", "8/8/8/4k3/8/8/4K3/4N3 w - - 0 1");
    expect_draw("black knight", "8/8/8/4k3/8/8/4K3/4n3 w - - 0 1");
    expect_draw("white bishop", "8/8/8/4k3/8/8/4K3/4B3 w - - 0 1");
    expect_draw("black bishop", "8/8/8/4k3/8/8/4K3/4b3 w - - 0 1");
    expect_draw("white two knights", "8/8/8/4k3/8/8/4K3/2N1N3 w - - 0 1");
    expect_draw("black two knights", "2n1n3/4k3/8/8/8/8/4K3/8 w - - 0 1");

    expect_unrecognized("start", forge::Board::StandardStartFen.data());
    expect_unrecognized("queen", "8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1");
    expect_unrecognized("rook", "8/8/8/4k3/8/8/4K3/4R3 w - - 0 1");
    expect_unrecognized("pawn", "8/8/8/4k3/8/4P3/4K3/8 w - - 0 1");
    expect_unrecognized("knight each", "8/8/8/2k1n3/8/2N5/3K4/8 w - - 0 1");
    expect_unrecognized("two bishops", "8/8/8/4k3/8/8/4K3/2B1B3 w - - 0 1");
    expect_unrecognized("bishop and pawn", "8/8/8/4k3/8/4P3/4K3/2B5 w - - 0 1");
    expect_unrecognized("pair plus pawn", "8/8/8/4k3/8/4P3/4K3/2B1N3 w - - 0 1");

    const char* light_far = "8/8/8/4k3/8/N7/8/KB6 w - - 0 1";
    const char* light_near = "8/8/8/4k3/8/N2K4/8/1B6 w - - 0 1";
    const char* light_corner = "k7/8/8/8/8/N7/1K6/1B6 w - - 0 1";
    const char* light_wrong = "7k/8/8/8/8/N7/1K6/1B6 w - - 0 1";
    const char* dark_corner = "7k/8/8/8/8/3N4/1K6/2B5 w - - 0 1";
    const char* dark_wrong = "k7/8/8/8/8/3N4/1K6/2B5 w - - 0 1";
    const char* black_pair = "2b1n3/3k4/8/8/8/8/8/4K3 w - - 0 1";

    const Scored far = score_fen(light_far);
    const Scored near = score_fen(light_near);
    const Scored corner = score_fen(light_corner);
    const Scored wrong = score_fen(light_wrong);
    const Scored dark = score_fen(dark_corner);
    const Scored dark_bad = score_fen(dark_wrong);
    const Scored black = score_fen(black_pair);
    const Scored black_stm = score_fen(other_side(black_pair));
    const Scored corner_stm = score_fen(other_side(light_corner));
    for (const Scored& item : {far, near, corner, wrong, dark, dark_bad, black, black_stm, corner_stm}) {
        if (!item.fen_ok || !item.recognized) fail("KBN fixture was not recognized");
    }
    if (far.score <= 0 || near.score <= far.score) fail("closer attacking king did not raise the score");
    if (corner.score <= wrong.score) fail("light-bishop corner did not outscore the other corner");
    if (dark.score <= dark_bad.score) fail("dark-bishop corner did not outscore the other corner");
    if (black.score >= 0) fail("lone white king was not behind against black bishop and knight");
    if (black_stm.score <= 0) fail("black bishop and knight were not ahead on their turn");
    if (black.score + black_stm.score != 0) fail("black pair score did not negate with the side to move");
    if (corner.score + corner_stm.score != 0) fail("corner score did not negate with the side to move");

    // Light bishop on f1, so a8 is a mating corner. The lone king steps toward it.
    const char* walk[] = {
        "8/8/8/8/4k3/N7/1K6/5B2 w - - 0 1",
        "8/8/8/3k4/8/N7/1K6/5B2 w - - 0 1",
        "8/8/2k5/8/8/N7/1K6/5B2 w - - 0 1",
        "8/1k6/8/8/8/N7/1K6/5B2 w - - 0 1",
        "k7/8/8/8/8/N7/1K6/5B2 w - - 0 1",
    };
    int previous = 0;
    for (int i = 0; i < 5; ++i) {
        const Scored step = score_fen(walk[i]);
        if (!step.fen_ok || !step.recognized) fail(std::string("walk fen ") + walk[i]);
        if (i > 0 && step.score < previous) fail("walk toward a8 lowered the score");
        previous = step.score;
    }
    const Scored walk_start = score_fen(walk[0]);
    const Scored walk_end = score_fen(walk[4]);
    if (walk_end.score <= walk_start.score) fail("a8 was not better than the start of the walk");

    forge::Board start;
    if (!start.set_fen(forge::Board::StandardStartFen)) fail("start fen");
    forge::dead_material_enabled = false;
    const forge::EvalComponents start_off = forge::Evaluator::static_eval_components(start);
    forge::dead_material_enabled = true;
    const forge::EvalComponents start_on = forge::Evaluator::static_eval_components(start);
    if (start_off.hce != start_on.hce || start_off.nnue != start_on.nnue || start_off.total != start_on.total) {
        fail("DeadMaterial changed the starting position");
    }

    forge::Board kbn;
    if (!kbn.set_fen(light_corner)) fail("light corner fen");
    forge::dead_material_enabled = false;
    const forge::EvalComponents kbn_off = forge::Evaluator::static_eval_components(kbn);
    forge::dead_material_enabled = true;
    const forge::EvalComponents kbn_on = forge::Evaluator::static_eval_components(kbn);
    if (kbn_on.hce != 0 || kbn_on.nnue != 0 || kbn_on.total != corner.score) {
        fail("enabled KBN eval did not replace the network");
    }
    if (kbn_off.nnue == 0) fail("disabled KBN eval did not call the network");
    if (kbn_off.total == kbn_on.total) fail("KBN network total matched the corner score");

    forge::Board bare;
    if (!bare.set_fen("8/8/8/4k3/8/8/4K3/8 w - - 0 1")) fail("bare fen");
    const forge::EvalComponents bare_on = forge::Evaluator::static_eval_components(bare);
    if (bare_on.total != 0 || bare_on.nnue != 0 || bare_on.hce != 0) fail("enabled bare kings were not zero");

    auto nodes_at = [](bool enabled, const char* fen, int depth) {
        forge::dead_material_enabled = enabled;
        forge::Board position;
        if (!position.set_fen(fen)) return static_cast<std::uint64_t>(0);
        forge::Searcher local(16);
        forge::SearchLimits limits;
        limits.depth = depth;
        return local.search(position, limits, false).nodes;
    };
    const std::uint64_t pair_off = nodes_at(false, light_corner, 5);
    const std::uint64_t pair_on = nodes_at(true, light_corner, 5);
    if (pair_off == 0 || pair_off == pair_on) fail("option did not change the bishop-and-knight search");

    forge::dead_material_enabled = true;
    std::vector<std::string> positions;
    positions.reserve(220);
    forge::Board walk_board;
    std::uint64_t rng = 0xD3AD5EEDULL;
    auto next_rand = [&]() {
        rng = rng * 6364136223846793005ULL + 1442695040888963407ULL;
        return rng;
    };
    while (positions.size() < 200) {
        if (!walk_board.set_fen(forge::Board::StandardStartFen)) fail("reset start");
        const int plies = static_cast<int>(4 + (next_rand() % 10U));
        for (int ply = 0; ply < plies; ++ply) {
            const forge::MoveList moves = walk_board.legal_moves();
            if (moves.empty()) break;
            forge::Undo undo;
            const forge::Move chosen = moves[static_cast<std::size_t>(next_rand() % moves.size())];
            if (!walk_board.make_move(chosen, undo)) fail("generator made an illegal move");
        }
        positions.push_back(walk_board.fen());
    }
    positions.push_back(light_corner);
    positions.push_back(dark_corner);
    positions.push_back("8/8/8/4k3/8/8/4K3/8 w - - 0 1");
    positions.push_back("8/8/8/4k3/8/8/4K3/2N1N3 w - - 0 1");
    positions.push_back("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1");

    forge::Searcher searcher(16);
    forge::SearchLimits limits;
    limits.depth = 10;
    const auto started = std::chrono::steady_clock::now();
    for (std::size_t index = 0; index < positions.size(); ++index) {
        forge::Board board;
        if (!board.set_fen(positions[index])) {
            fail("search fen " + positions[index]);
            break;
        }
        searcher.clear();
        const forge::SearchInfo info = searcher.search(board, limits, false);
        if (!move_is_legal(board, info.best_move) || !pv_is_legal(board, info.pv)) {
            fail("illegal move " + forge::Board::move_to_uci(info.best_move) + " in " + positions[index]);
            break;
        }
        if ((index + 1) % 50 == 0) std::cerr << "searches " << (index + 1) << '\n';
    }
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - started).count();
    std::cout << "dead-material tests failures " << g_failures
              << " searches " << positions.size()
              << " ms " << elapsed
              << " corner " << corner.score
              << " wrong " << wrong.score
              << " near " << near.score
              << " far " << far.score
              << " pair " << pair_off << " " << pair_on
              << '\n';
    return g_failures == 0 ? 0 : 1;
}
