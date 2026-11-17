#include "forge/board.hpp"
#include "forge/search.hpp"

#include <iostream>
#include <sstream>
#include <string>

namespace {

int failures = 0;

bool move_is_legal(const forge::Board& board, forge::Move move);

void expect(bool ok, const std::string& message) {
    if (ok) return;
    std::cout << "FAIL " << message << std::endl;
    ++failures;
}

void check_formula() {
    forge::tune::EvalRule50Damp = false;
    expect(forge::rule50_damped_static(250, 90) == 250, "off leaves a high-clock score alone");
    expect(forge::rule50_damped_static(forge::MateValue, 90) == forge::MateValue, "off leaves a mate score alone");
    expect(forge::rule50_damped_static(forge::ValueNone, 10) == forge::ValueNone, "off leaves the sentinel alone");

    forge::tune::EvalRule50Damp = true;
    expect(forge::rule50_damped_static(250, 0) == 250, "clock 0 keeps the whole score");
    expect(forge::rule50_damped_static(-80, 0) == -80, "clock 0 keeps a negative score");
    expect(forge::rule50_damped_static(200, 50) == 100, "clock 50 keeps half");
    expect(forge::rule50_damped_static(-200, 50) == -100, "clock 50 halves a negative score toward zero");
    expect(forge::rule50_damped_static(250, 90) == 25, "clock 90 keeps ten percent");
    expect(forge::rule50_damped_static(300, 99) == 3, "clock 99 keeps one percent");
    expect(forge::rule50_damped_static(180, 100) == 0, "clock 100 keeps nothing");
    expect(forge::rule50_damped_static(180, 140) == 0, "a clock past 100 stays fully shrunk");
    expect(forge::rule50_damped_static(40, -3) == 40, "a negative clock is treated as zero");
    expect(forge::rule50_damped_static(forge::ValueNone, 90) == forge::ValueNone, "the sentinel is not a static score");
    expect(forge::rule50_damped_static(forge::MateValue - 10, 80) == forge::MateValue - 10, "a positive mate score is not scaled");
    expect(forge::rule50_damped_static(-(forge::MateValue - 10), 80) == -(forge::MateValue - 10),
           "a negative mate score is not scaled");
    forge::tune::EvalRule50Damp = false;
}

forge::SearchInfo search_at(forge::Searcher& searcher, const std::string& fen, int depth) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) {
        expect(false, "set_fen " + fen + " " + error);
        return {};
    }
    forge::SearchLimits limits;
    limits.depth = depth;
    searcher.clear();
    return searcher.search(board, limits, false);
}

int stored_eval(forge::Searcher& searcher, const std::string& fen) {
    forge::Board board;
    std::string error;
    if (!board.set_fen(fen, &error)) return forge::ValueNone;
    const forge::TTProbe probe = searcher.transposition_table().probe(board.key());
    expect(probe.hit, "root evaluation was stored for " + fen);
    return probe.entry.eval;
}

void check_search_behaviour() {
    const std::string quiet = "4k3/8/8/8/8/3Q4/8/4K3 w - - 80 20";
    forge::Searcher searcher(16);
    expect(searcher.threads() == 1, "searcher starts at one thread");

    forge::tune::EvalRule50Damp = false;
    const forge::SearchInfo off = search_at(searcher, quiet, 1);
    const int off_stored = stored_eval(searcher, quiet);

    forge::tune::EvalRule50Damp = true;
    const forge::SearchInfo on = search_at(searcher, quiet, 1);
    const int on_stored = stored_eval(searcher, quiet);

    const std::string quiet_zero = "4k3/8/8/8/8/3Q4/8/4K3 w - - 0 20";
    (void)search_at(searcher, quiet_zero, 1);
    const int zero_stored = stored_eval(searcher, quiet_zero);

    std::cout << "quiet depth1 off " << off.score << " on " << on.score
              << " stored_off " << off_stored << " stored_on " << on_stored
              << " stored_clock0 " << zero_stored << std::endl;

    expect(!forge::is_mate_score(off.score) && !forge::is_mate_score(on.score),
           "queen ending depth 1 is a static score, not a mate");
    expect(off.score > 200 && on.score > 0, "both sides still see a white advantage");
    expect(on.score * 2 < off.score, "clock 80 static search score is clearly smaller with the option on");
    expect(on_stored == off_stored, "the hash table keeps the unscaled evaluation");
    expect(zero_stored == on_stored, "clock 0 and clock 80 store the same raw evaluation");

    const std::string mate = "6k1/4Q3/6K1/8/8/8/8/8 w - - 90 40";
    forge::tune::EvalRule50Damp = false;
    const forge::SearchInfo mate_off = search_at(searcher, mate, 2);
    forge::tune::EvalRule50Damp = true;
    const forge::SearchInfo mate_on = search_at(searcher, mate, 2);
    std::cout << "mate off " << mate_off.score << " " << forge::Board::move_to_uci(mate_off.best_move)
              << " on " << mate_on.score << " " << forge::Board::move_to_uci(mate_on.best_move) << std::endl;
    expect(forge::is_mate_score(mate_off.score) && mate_off.score > 0, "mate score stays a mate with the option off");
    expect(forge::is_mate_score(mate_on.score) && mate_on.score > 0, "mate score is not shrunk toward zero");
    expect(mate_on.score == mate_off.score, "the option does not change the mate distance");

    forge::Board mate_board;
    expect(mate_board.set_fen(mate), "mate fen parses");
    bool mate_legal = false;
    for (const forge::Move& move : mate_board.legal_moves()) {
        if (move == mate_on.best_move) mate_legal = true;
    }
    expect(mate_legal, "mate search returns a legal move");

    const std::string mate99 = "6k1/4Q3/6K1/8/8/8/8/8 w - - 99 50";
    const forge::SearchInfo mate_late = search_at(searcher, mate99, 2);
    std::cout << "mate99 " << mate_late.score << " " << forge::Board::move_to_uci(mate_late.best_move) << std::endl;
    expect(forge::is_mate_score(mate_late.score) && mate_late.score == mate_on.score,
           "a mate one half-move from the draw is still that mate");

    const std::string in_check = "4k3/8/8/4q3/8/8/8/4K3 w - - 40 20";
    forge::Board checked;
    expect(checked.set_fen(in_check) && checked.in_check(), "white is in check");
    const forge::SearchInfo evasion = search_at(searcher, in_check, 4);
    expect(move_is_legal(checked, evasion.best_move), "a check evasion stays legal with the option on");

    forge::Searcher fresh(16);
    const forge::SearchInfo low_fresh = search_at(fresh, quiet_zero, 4);
    forge::Searcher warm(16);
    const forge::SearchInfo high = search_at(warm, quiet, 4);
    forge::Board low_board;
    expect(low_board.set_fen(quiet_zero), "clock 0 queen fen");
    forge::SearchLimits limits;
    limits.depth = 4;
    const forge::SearchInfo low_warm = warm.search(low_board, limits, false);
    std::cout << "clock isolation fresh0 " << low_fresh.score << " warm0 " << low_warm.score
              << " high80 " << high.score << std::endl;
    expect(high.score * 2 < low_fresh.score, "depth 4 at clock 80 is clearly smaller than clock 0");
    expect(low_warm.score > low_fresh.score * 3 / 5,
           "a clock-80 score is not reused for the same placement at clock 0");
    const int warm_eval = stored_eval(warm, quiet_zero);
    expect(warm_eval == on_stored, "the shared hash entry still holds the unscaled evaluation");

    const std::string losing = "4k3/3q4/8/8/8/8/8/4K3 w - - 80 20";
    forge::tune::EvalRule50Damp = false;
    const forge::SearchInfo losing_off = search_at(searcher, losing, 1);
    forge::tune::EvalRule50Damp = true;
    const forge::SearchInfo losing_on = search_at(searcher, losing, 1);
    std::cout << "losing off " << losing_off.score << " on " << losing_on.score << std::endl;
    expect(losing_off.score < -200 && losing_on.score < 0, "a losing static score stays negative");
    expect(losing_on.score > losing_off.score && losing_off.score < losing_on.score * 2,
           "a negative score shrinks toward zero");

    const std::string stale = "7k/5Q2/6K1/8/8/8/8/8 b - - 70 40";
    forge::Board stale_board;
    expect(stale_board.set_fen(stale) && stale_board.legal_moves().empty() && !stale_board.in_check(),
           "constructed stalemate has no legal move");
    const forge::SearchInfo stale_info = search_at(searcher, stale, 3);
    expect(stale_info.best_move.is_none(), "stalemate search does not invent a move");

    const std::string promote = "8/P7/8/8/8/8/8/k6K w - - 55 40";
    forge::Board promote_board;
    expect(promote_board.set_fen(promote), "promotion fen");
    const forge::SearchInfo promote_info = search_at(searcher, promote, 4);
    expect(move_is_legal(promote_board, promote_info.best_move) && promote_info.best_move.is_promotion(),
           "a high-clock promotion search returns a legal promotion");
    forge::tune::EvalRule50Damp = false;
}

std::uint64_t mix(std::uint64_t& state) {
    state += 0xA5A5A5A5A5A5A5A5ULL;
    state = (state << 7) | (state >> 57);
    state ^= state >> 13;
    state *= 0x6C62272E07BB0141ULL;
    return state;
}

bool move_is_legal(const forge::Board& board, forge::Move move) {
    if (move.is_none()) return board.legal_moves().empty();
    for (const forge::Move& legal : board.legal_moves()) {
        if (legal == move) return true;
    }
    return false;
}

std::string with_clock(const forge::Board& board, int clock) {
    std::istringstream input(board.fen());
    std::string placement;
    std::string side;
    std::string castle;
    std::string ep;
    std::string half;
    std::string full;
    input >> placement >> side >> castle >> ep >> half >> full;
    return placement + " " + side + " " + castle + " " + ep + " " + std::to_string(clock) + " " + full;
}

int search_walk(forge::Searcher& searcher, std::uint64_t seed, int games, int max_plies) {
    forge::SearchLimits limits;
    limits.depth = 10;
    std::uint64_t state = seed;
    int illegal = 0;
    int in_check = 0;
    int raised = 0;
    for (int n = 0; n < games; ++n) {
        forge::Board board;
        if (!board.set_fen(forge::Board::StandardStartFen)) {
            expect(false, "start position");
            return games;
        }
        const int plies = static_cast<int>(mix(state) % static_cast<std::uint64_t>(max_plies));
        for (int ply = 0; ply < plies; ++ply) {
            const forge::MoveList moves = board.legal_moves();
            if (moves.empty()) break;
            forge::Undo undo;
            const forge::Move chosen = moves[mix(state) % moves.size()];
            if (!board.make_move(chosen, undo)) {
                expect(false, "make_move rejected a legal move");
                return games;
            }
        }
        if ((n % 5) == 4) {
            const int clock = 20 + static_cast<int>(mix(state) % 80ULL);
            std::string error;
            if (!board.set_fen(with_clock(board, clock), &error)) {
                expect(false, "reclock " + error);
                return games;
            }
            ++raised;
        }
        if (board.in_check()) ++in_check;
        searcher.clear();
        const forge::SearchInfo info = searcher.search(board, limits, false);
        if (!move_is_legal(board, info.best_move)) {
            ++illegal;
            std::cout << "ILLEGAL " << n << " " << board.fen() << " "
                      << forge::Board::move_to_uci(info.best_move) << std::endl;
        }
    }
    std::cout << "depth10 games " << games << " seed " << seed << " illegal " << illegal
              << " incheck " << in_check << " raised " << raised << std::endl;
    return illegal;
}

void check_two_hundred_searches() {
    forge::tune::EvalRule50Damp = true;
    forge::Searcher searcher(16);
    const int first = search_walk(searcher, 0x51A7E0D5ULL, 200, 18);
    const int second = search_walk(searcher, 0xC0FFEE11ULL, 200, 40);
    expect(first == 0 && second == 0, "every depth-10 move is legal");
    forge::tune::EvalRule50Damp = false;
}

}  // namespace

int main() {
    check_formula();
    check_search_behaviour();
    if (failures == 0) check_two_hundred_searches();
    if (failures != 0) {
        std::cout << "failures " << failures << std::endl;
        return 1;
    }
    std::cout << "ok" << std::endl;
    return 0;
}
