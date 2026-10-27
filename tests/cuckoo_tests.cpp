// C6 CuckooRep tests: the cuckoo table of reversible-move keys, the
// upcoming-repetition detector (Board::upcoming_repetition) against a
// brute-force reference, its rule-50 / null-move / root windows, and the
// search-level draw bound (UCI CuckooRep, default off).
//
// Reference definition used throughout: the side to move has an upcoming
// repetition iff some legal move leads to a position for which
// Board::is_repetition(root_index) holds, i.e. a position the search itself
// scores as a repetition draw. The reference generates every legal move.
#include "forge/bitboard.hpp"
#include "forge/board.hpp"
#include "forge/nnue.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace forge {

// Node-level access to a worker, in the style of tests/rule50_tests.cpp: one
// non-root node (ply 1) with a given window, depth and root history index.
struct SearcherTestProbe {
    struct Result {
        int score = 0;
        std::uint64_t nodes = 0;
    };
    static Result run(Searcher& searcher, Board board, std::size_t root_index, int depth, int alpha, int beta,
                      bool cuckoo) {
        auto& worker = searcher.main_worker();
        worker.clear();
        worker.shared_.tt.clear();
        worker.shared_.stop.store(false, std::memory_order_relaxed);
        worker.shared_.ponder_hit_ns.store(0, std::memory_order_relaxed);
        worker.all_workers_ = nullptr;
        worker.aborted_ = false;
        worker.local_nodes_ = 0;
        worker.nodes_.store(0, std::memory_order_relaxed);
        worker.node_limit_ = 0;
        worker.node_limit_specified_ = false;
        worker.hard_limit_ms_ = worker.soft_limit_ms_ = 0;
        worker.time_managed_ = worker.pondering_ = false;
        worker.start_ = std::chrono::steady_clock::now();
        worker.seldepth_ = 0;
        worker.root_history_index_ = root_index;
        auto* ss = &worker.stack_[5];
        ss->ply = 1;
        if (nnue::enabled && nnue::available()) nnue::refresh(board, ss->accumulator);
        Result result;
        if (cuckoo) {
            result.score = depth == 0 ? worker.qsearch_cuckoo(board, ss, alpha, beta)
                                      : worker.search_cuckoo(board, ss, depth, alpha, beta, false);
        } else {
            result.score = depth == 0 ? worker.qsearch(board, ss, alpha, beta)
                                      : worker.search(board, ss, depth, alpha, beta, false);
        }
        result.nodes = worker.local_nodes_;
        return result;
    }
};

} // namespace forge

namespace {

using forge::Board;

int failures = 0;
std::uint64_t checks_run = 0;

void check(bool condition, const std::string& message) {
    ++checks_run;
    if (!condition) {
        ++failures;
        if (failures <= 40) std::cout << "FAIL " << message << '\n';
    }
}

struct Rng {
    std::uint64_t state;
    std::uint64_t next() {
        state ^= state << 13U;
        state ^= state >> 7U;
        state ^= state << 17U;
        return state;
    }
    std::size_t below(std::size_t n) { return static_cast<std::size_t>(next() % n); }
};

// A UCI move, or "0000" for a null move (only when not in check).
bool play_token(Board& board, std::string_view token) {
    if (token == "0000") {
        if (board.in_check()) return false;
        forge::NullUndo undo;
        board.make_null_move(undo);
        return true;
    }
    const auto move = board.parse_uci(token);
    if (!move.has_value()) return false;
    forge::Undo undo;
    (void)board.make_move(*move, undo);
    return true;
}

bool setup(Board& board, const std::string& fen, const std::string& moves) {
    if (!board.set_fen(fen)) return false;
    std::istringstream input(moves);
    std::string token;
    while (input >> token) {
        if (!play_token(board, token)) return false;
    }
    return true;
}

bool is_reversible(const Board& board, forge::Move move) {
    return move.is_quiet() && !move.is_castle() && forge::piece_type(board.moved_piece(move)) != forge::Pawn;
}

// Brute-force reference for two root indices at once.
std::pair<bool, bool> reference_upcoming(Board& board, std::size_t root_a, std::size_t root_b) {
    bool a = false;
    bool b = false;
    for (const forge::Move move : board.legal_moves()) {
        forge::Undo undo;
        (void)board.make_move(move, undo);
        a = a || board.is_repetition(root_a);
        b = b || board.is_repetition(root_b);
        board.unmake_move(move, undo);
        if (a && b) break;
    }
    return {a, b};
}

bool reference_upcoming(Board& board, std::size_t root) { return reference_upcoming(board, root, root).first; }

// ---------------------------------------------------------------------------
// 1. The table: 3668 entries, exact round trip, no stray hits.
// ---------------------------------------------------------------------------
void test_table() {
    using namespace forge;
    const Board initialised;  // runs attacks::init()
    (void)initialised;
    std::array<std::size_t, 7> per_type{};
    std::vector<std::uint64_t> keys;
    std::size_t round_trips = 0;
    for (int p = WN; p <= BK; ++p) {
        const Piece piece = static_cast<Piece>(p);
        const int type = piece_type(piece);
        if (type == Pawn) continue;
        for (int a = 0; a < 64; ++a) {
            // Independent geometry: the engine's empty-board attack tables.
            Bitboard targets = 0;
            switch (type) {
            case Knight: targets = attacks::knight(a); break;
            case Bishop: targets = attacks::bishop(a, 0); break;
            case Rook: targets = attacks::rook(a, 0); break;
            case Queen: targets = attacks::queen(a, 0); break;
            default: targets = attacks::king(a); break;
            }
            while (targets != 0) {
                const int b = pop_lsb(targets);
                if (b <= a) continue;
                ++per_type[static_cast<std::size_t>(type)];
                const std::uint64_t key = cuckoo::move_key(piece, a, b);
                keys.push_back(key);
                check(key == cuckoo::move_key(piece, b, a), "move key is symmetric in the two squares");
                const auto entry = cuckoo::lookup(key);
                const bool exact = entry.has_value() && entry->piece == piece && entry->a == a && entry->b == b;
                check(exact, "round trip piece " + std::to_string(p) + " " + std::to_string(a) + "-" + std::to_string(b));
                round_trips += exact ? 1 : 0;
            }
        }
    }
    const std::size_t total = keys.size();
    std::cout << "table: reversible non-pawn moves enumerated " << total << " (N " << per_type[Knight] << ", B "
              << per_type[Bishop] << ", R " << per_type[Rook] << ", Q " << per_type[Queen] << ", K "
              << per_type[King] << "), entry_count " << cuckoo::entry_count() << ", exact round trips "
              << round_trips << '\n';
    check(total == 3668, "3668 reversible non-pawn moves");
    check(per_type[Knight] == 336 && per_type[Bishop] == 560 && per_type[Rook] == 896 && per_type[Queen] == 1456 &&
              per_type[King] == 420,
          "per piece type: 2 x (168, 280, 448, 728, 210)");
    check(cuckoo::entry_count() == 3668, "table holds exactly 3668 entries");
    check(round_trips == 3668, "every entry round-trips exactly");
    std::vector<std::uint64_t> sorted = keys;
    std::sort(sorted.begin(), sorted.end());
    check(std::adjacent_find(sorted.begin(), sorted.end()) == sorted.end(), "all move keys distinct");
    check(sorted.front() != 0, "no move key is zero");

    std::size_t occupied = 0;
    bool only_move_keys = true;
    for (std::size_t slot = 0; slot < cuckoo::Slots; ++slot) {
        const std::uint64_t key = cuckoo::slot_key(slot);
        if (key == 0) continue;
        ++occupied;
        only_move_keys = only_move_keys && std::binary_search(sorted.begin(), sorted.end(), key);
    }
    std::cout << "table: occupied slots " << occupied << " of " << cuckoo::Slots << '\n';
    check(occupied == 3668, "3668 occupied slots");
    check(only_move_keys, "occupied slots hold only move keys");

    // Misses: key 0, pawn steps, piece-only differences (no side key), random keys.
    check(!cuckoo::lookup(0).has_value(), "key 0 is not found");
    std::size_t stray = 0;
    for (int a = 8; a < 56; ++a) {
        stray += cuckoo::lookup(cuckoo::move_key(WP, a, a + 8)).has_value() ? 1 : 0;
        stray += cuckoo::lookup(cuckoo::move_key(BP, a, a - 8)).has_value() ? 1 : 0;
        if (a < 48) stray += cuckoo::lookup(cuckoo::move_key(WP, a, a + 16)).has_value() ? 1 : 0;
    }
    // side key = move_key(p,a,b) ^ move_key(p,a,c) ^ move_key(p,b,c)
    const std::uint64_t side = cuckoo::move_key(WN, 0, 1) ^ cuckoo::move_key(WN, 0, 2) ^ cuckoo::move_key(WN, 1, 2);
    for (const std::uint64_t key : keys) stray += cuckoo::lookup(key ^ side).has_value() ? 1 : 0;
    Rng rng{0x9E3779B97F4A7C15ULL};
    for (int i = 0; i < 1000000; ++i) stray += cuckoo::lookup(rng.next()).has_value() ? 1 : 0;
    std::cout << "table: stray hits on 1,000,000 random keys + pawn steps + side-less keys: " << stray << '\n';
    check(stray == 0, "no stray hits");

    // The key formula is the engine's own Zobrist difference (make_move).
    Board board;
    const std::uint64_t before = board.key();
    check(play_token(board, "g1f3"), "g1f3 legal");
    check((before ^ board.key()) == cuckoo::move_key(WN, 6, 21), "g1f3 key delta equals the table key");
    check(play_token(board, "b8c6"), "b8c6 legal");
    const auto knight = cuckoo::lookup(board.key_history()[1] ^ board.key());
    check(knight.has_value() && knight->piece == BN && knight->a == 42 && knight->b == 57,
          "b8c6 key delta finds the black knight entry {c6, b8}");
}

// ---------------------------------------------------------------------------
// 2. Hand-written positions: expected value, detector and reference agree.
// ---------------------------------------------------------------------------
struct HandCase {
    const char* name;
    const char* fen;
    const char* moves;
    int root;  // history index of the root; -1 = the current position
    bool expected;
};

constexpr const char* Start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
constexpr const char* KN = "4k3/8/8/8/8/8/8/4K1N1 w - - 0 1";

std::string repeat(const std::string& text, int times) {
    std::string out;
    for (int i = 0; i < times; ++i) out += text;
    return out;
}

void test_hand_cases() {
    static const std::string long_history = repeat("g1f3 e8d8 f3g1 d8e8 ", 260) + "g1f3 e8d8 f3g1";
    const std::vector<HandCase> cases = {
        {"H01 W knight back, start is in-tree", Start, "g1f3 g8f6 f3g1", 0, true},
        {"H02 same, start before the root once", Start, "g1f3 g8f6 f3g1", -1, false},
        {"H03 two occurrences before the root", Start, "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1", -1, true},
        {"H04 B knight back, target in-tree", Start, "g1f3 g8f6 f3g1 f6g8 g1f3", 2, true},
        {"H05 same, target just before the root", Start, "g1f3 g8f6 f3g1 f6g8 g1f3", 3, false},
        {"H06 same, root = current", Start, "g1f3 g8f6 f3g1 f6g8 g1f3", -1, false},
        {"H07 rule50 edge: target right after a pawn move", Start, "e2e4 g8f6 g1f3 f6g8", 0, true},
        {"H08 rule50 edge, root at the target", Start, "e2e4 g8f6 g1f3 f6g8", 1, true},
        {"H09 rule50 edge, target before the root", Start, "e2e4 g8f6 g1f3 f6g8", 2, false},
        {"H10 history starts at the FEN (size bound)", KN, "g1f3 e8d8 f3g1", 0, true},
        {"H11 same, root = current", KN, "g1f3 e8d8 f3g1", -1, false},
        {"H12 null-move window: target before the null", KN, "g1f3 0000 f3g1 0000", 0, false},
        {"H13 same plies with real moves", KN, "g1f3 e8d8 f3g1 d8e8", 0, true},
        {"H14 null-move edge: target is the null position", KN, "e1d1 0000 g1f3 e8d8 f3g1", 0, true},
        {"H15 same, root = current", KN, "e1d1 0000 g1f3 e8d8 f3g1", -1, false},
        {"H16 rook way back blocked by own bishop", "4k3/8/8/8/8/B7/8/R3K3 w - - 0 1",
         "e1f1 e8d8 a1b1 d8c8 b1b5 c8d8 b5a5 d8e8", 0, false},
        {"H17 rook way back free (distance 7)", "4k3/8/8/8/8/8/8/R3K3 w - - 0 1",
         "e1f1 e8d8 a1b1 d8c8 b1b5 c8d8 b5a5 d8e8", 0, true},
        {"H18 rook way back blocked by enemy bishop", "4k3/8/8/8/8/b7/8/R3K3 w - - 0 1",
         "e1f1 e8d8 a1b1 d8c8 b1b5 c8d8 b5a5 d8e8", 0, false},
        {"H19 opponent piece not back", Start, "g1f3 g8f6 f3g1 b8c6", 0, false},
        {"H20 net move of an enemy piece (wrong colour)", "1n2k3/8/8/8/8/8/8/4K1N1 b - - 0 1",
         "e8d8 g1f3 b8c6 f3g1 d8e8", 0, false},
        {"H21 W bishop", "4k3/8/8/8/8/8/3B4/4K3 b - - 0 1", "e8d8 d2c1 d8e8", 0, true},
        {"H22 W bishop long diagonal", "4k3/8/8/8/8/8/8/B3K3 b - - 0 1", "e8d8 a1h8 d8e8", 0, true},
        {"H23 W rook", "4k3/8/8/8/8/8/8/R3K3 b - - 0 1", "e8d8 a1a7 d8e8", 0, true},
        {"H24 W queen", "4k3/8/8/8/8/8/8/Q3K3 b - - 0 1", "e8d8 a1b1 d8e8", 0, true},
        {"H25 W king", "4k3/8/8/8/8/8/8/4K3 b - - 0 1", "e8d8 e1f2 d8e8", 0, true},
        {"H26 B bishop (after a check)", "2b1k3/8/8/8/8/8/8/4K3 w - - 0 1", "e1d1 c8g4 d1e1", 0, true},
        {"H27 B rook", "r3k3/8/8/8/8/8/8/4K3 w - - 0 1", "e1d1 a8a2 d1e1", 0, true},
        {"H28 B queen", "q3k3/8/8/8/8/8/8/4K3 w - - 0 1", "e1f1 a8b8 f1e1", 0, true},
        {"H29 B king", "4k3/8/8/8/8/8/8/4K3 w - - 0 1", "e1d1 e8f7 d1e1", 0, true},
        {"H30 B knight", Start, "g1f3 g8f6 f3g1 f6g8 g1f3", 0, true},
        {"H31 threefold, most recent in-tree", Start, "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1", 4, true},
        {"H32 threefold, both before the root", Start, "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1", 5, true},
        {"H33 king triangle, distance 5", "4k3/8/8/8/8/8/8/3K4 b - - 0 1", "e8d8 d1e1 d8d7 e1e2 d7e8", 0, true},
        {"H34 same, target before the root once", "4k3/8/8/8/8/8/8/3K4 b - - 0 1", "e8d8 d1e1 d8d7 e1e2 d7e8", 1,
         false},
        {"H35 castling rights already gone in the target", "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1", "e1f1 e8d8 f1e1 d8e8",
         0, true},
        {"H36 castling rights differ from the target", "4k3/8/8/8/8/8/8/R3K2R b KQ - 0 1", "e8d8 e1f1 d8e8 f1e1", 0,
         false},
        {"H37 target has an en-passant key", "4k3/8/8/8/1p6/8/P7/4K3 w - - 0 1", "a2a4 e8d8 e1d1 d8e8", 0, false},
        {"H38 same without a capturer (no ep key)", "4k3/8/8/8/8/8/P7/4K3 w - - 0 1", "a2a4 e8d8 e1d1 d8e8", 0, true},
        {"H39 escaping check into the repetition", "7k/8/8/8/8/8/8/1Q2K3 w - - 0 1", "b1b8 h8h7 b8b1 h7h8 b1b8", 0, true},
        {"H40 same, root = current", "7k/8/8/8/8/8/8/1Q2K3 w - - 0 1", "b1b8 h8h7 b8b1 h7h8 b1b8", -1, false},
        {"H41 current already repeated, next repeats again", Start, "g1f3 g8f6 f3g1 f6g8", 0, true},
        {"H42 too short (1 ply)", Start, "g1f3", 0, false},
        {"H43 too short (2 plies)", Start, "g1f3 g8f6", 0, false},
        {"H44 pawn move resets the window", Start, "g1f3 g8f6 f3g1 e7e6", 0, false},
        {"H45 1043 plies, null counter saturated", KN, long_history.c_str(), -1, true},
        {"H46 rook way back blocked by own king (distance 7)", "4k3/8/8/8/8/8/8/4K2R b - - 0 1",
         "e8d8 h1h3 d8c8 h3a3 c8d8 a3a1 d8e8", 0, false},
        {"H47 same with the king off the rank", "4k3/8/8/8/8/8/4K3/7R b - - 0 1",
         "e8d8 h1h3 d8c8 h3a3 c8d8 a3a1 d8e8", 0, true},
        {"H48 null long before the target", KN, "0000 e8d8 g1f3 d8e8 f3g1", 0, true},
        {"H49 B queen orthogonal", "3qk3/8/8/8/8/8/8/4K3 w - - 0 1", "e1f1 d8d4 f1e1", 0, true},
        {"H50 repetition with the other knight", Start, "g1f3 g8f6 b1c3 f6g8", 0, true},
        {"H51 two moves needed", Start, "g1f3 g8f6 b1c3 b8c6", 0, false},
    };
    int agree = 0;
    int positive = 0;
    for (const HandCase& c : cases) {
        Board board;
        if (!setup(board, c.fen, c.moves)) {
            check(false, std::string(c.name) + ": setup failed");
            continue;
        }
        const std::size_t root = c.root < 0 ? board.history_size() - 1 : static_cast<std::size_t>(c.root);
        const bool fast = board.upcoming_repetition(root);
        const bool slow = reference_upcoming(board, root);
        check(fast == c.expected, std::string(c.name) + ": detector " + (fast ? "true" : "false"));
        check(slow == c.expected, std::string(c.name) + ": reference " + (slow ? "true" : "false"));
        agree += fast == slow ? 1 : 0;
        positive += c.expected ? 1 : 0;
    }
    std::cout << "hand-written: " << cases.size() << " positions (" << positive << " with an upcoming repetition), "
              << "detector == reference on " << agree << ", mismatches " << (static_cast<int>(cases.size()) - agree)
              << '\n';
}

// ---------------------------------------------------------------------------
// 3. Random reversible-move sequences: detector == reference at every ply.
// ---------------------------------------------------------------------------
void test_random_sequences(int sequences) {
    const std::vector<std::string> starts = {
        std::string(Start),
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
        "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
        "4k3/8/3n4/8/8/2N5/8/4K3 w - - 0 1",
        "2b1k3/8/8/8/8/8/8/2B1K3 w - - 0 1",
        "3qk3/8/8/8/8/8/8/3QK3 w - - 0 1",
        "4k3/pp6/8/8/8/8/PP6/4K2R w K - 0 1",
        "8/8/4k3/8/2r5/8/3K4/5B2 w - - 0 1",
        "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "4k3/8/8/2pP4/8/8/8/4K3 w - c6 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
        "7k/8/8/8/8/8/2Q5/K7 w - - 0 1",
        "6k1/ppp3p1/8/8/1r6/1q6/4Q1PP/7K w - - 0 1",
        "r1b1k2r/ppppqppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1",
        "8/k7/3p4/p2P1p2/P2P1P2/8/8/K7 w - - 0 1",
        "1k6/8/1K6/8/8/8/6N1/6B1 w - - 0 1",
    };
    for (const std::string& fen : starts) {
        Board board;
        check(board.set_fen(fen), "random start FEN parses: " + fen);
    }
    const std::array<int, 5> clocks{0, 2, 9, 40, 97};
    Rng rng{0xC6C6C6C6DEADBEEFULL};
    std::uint64_t compared = 0;
    std::uint64_t positives = 0;
    std::uint64_t positives_current_root = 0;
    std::uint64_t key_deltas = 0;
    std::uint64_t nulls = 0;
    std::uint64_t plies = 0;
    int mismatches = 0;
    for (int sequence = 0; sequence < sequences; ++sequence) {
        // FEN with a random halfmove clock.
        std::string fen = starts[rng.below(starts.size())];
        {
            std::istringstream fields(fen);
            std::string placement, side, castling, ep, clock, full;
            fields >> placement >> side >> castling >> ep >> clock >> full;
            fen = placement + ' ' + side + ' ' + castling + ' ' + ep + ' ' +
                  std::to_string(clocks[rng.below(clocks.size())]) + ' ' + full;
        }
        Board board;
        if (!board.set_fen(fen)) {
            check(false, "random FEN parses: " + fen);
            continue;
        }
        std::vector<forge::Move> played;  // Move::none() = null move
        std::string trail;
        const std::size_t length = 8 + rng.below(53);
        for (std::size_t ply = 0; ply < length; ++ply) {
            const forge::MoveList legal = board.legal_moves();
            if (legal.empty()) break;
            std::vector<forge::Move> reversible;
            for (const forge::Move move : legal) {
                if (is_reversible(board, move)) reversible.push_back(move);
            }
            forge::Move chosen = forge::Move::none();
            bool null_move = false;
            const std::size_t roll = rng.below(100);
            auto reverse_of = [&](std::size_t back) {
                if (played.size() < back) return forge::Move::none();
                const forge::Move earlier = played[played.size() - back];
                if (earlier.is_none()) return forge::Move::none();
                for (const forge::Move move : reversible) {
                    if (move.from == earlier.to && move.to == earlier.from) return move;
                }
                return forge::Move::none();
            };
            if (roll < 5 && !board.in_check() && !played.empty() && !played.back().is_none()) {
                null_move = true;
            } else if (roll < 45) {
                chosen = reverse_of(2);
            } else if (roll < 55) {
                chosen = reverse_of(4);
            }
            if (!null_move && chosen.is_none()) {
                chosen = !reversible.empty() && rng.below(100) < 85 ? reversible[rng.below(reversible.size())]
                                                                    : legal[rng.below(legal.size())];
            }
            if (null_move) {
                forge::NullUndo undo;
                board.make_null_move(undo);
                played.push_back(forge::Move::none());
                trail += " 0000";
                ++nulls;
            } else {
                const std::uint64_t before = board.key();
                const bool no_ep_before = board.ep_square() < 0;
                const std::uint8_t rights = board.castling_rights();
                const forge::Piece piece = board.moved_piece(chosen);
                const bool reversible_move = is_reversible(board, chosen);
                forge::Undo undo;
                (void)board.make_move(chosen, undo);
                played.push_back(chosen);
                trail += ' ' + Board::move_to_uci(chosen);
                if (reversible_move && no_ep_before && rights == board.castling_rights()) {
                    const std::uint64_t delta = before ^ board.key();
                    const auto entry = forge::cuckoo::lookup(delta);
                    check(delta == forge::cuckoo::move_key(piece, chosen.from, chosen.to) && entry.has_value() &&
                              entry->piece == piece &&
                              entry->a == std::min<int>(chosen.from, chosen.to) &&
                              entry->b == std::max<int>(chosen.from, chosen.to),
                          "reversible move key delta is a table entry");
                    ++key_deltas;
                }
            }
            ++plies;
            const std::size_t size = board.history_size();
            const std::size_t current = size - 1;
            const std::size_t random_root = rng.below(size);
            const auto [slow_current, slow_random] = reference_upcoming(board, current, random_root);
            const bool fast_current = board.upcoming_repetition(current);
            const bool fast_random = board.upcoming_repetition(random_root);
            compared += 2;
            positives += (slow_current ? 1 : 0) + (slow_random ? 1 : 0);
            positives_current_root += slow_current ? 1 : 0;
            if (fast_current != slow_current || fast_random != slow_random) {
                ++mismatches;
                if (mismatches <= 10) {
                    std::cout << "MISMATCH fen " << fen << " moves" << trail << " roots " << current << '/'
                              << random_root << " detector " << fast_current << '/' << fast_random << " reference "
                              << slow_current << '/' << slow_random << '\n';
                }
            }
        }
    }
    std::cout << "random: " << sequences << " sequences, " << plies << " plies (" << nulls << " null moves), "
              << compared << " comparisons, " << positives << " with an upcoming repetition ("
              << positives_current_root << " with root = current), " << key_deltas
              << " move key deltas checked, mismatches " << mismatches << '\n';
    check(mismatches == 0, "random sequences: detector == reference");
    check(positives >= 10000 && compared - positives >= 10000, "random sequences exercise both outcomes");
}

// ---------------------------------------------------------------------------
// 4. Node level (as in tests/rule50_tests.cpp): the bound fires exactly when the
//    detector says so, including at the rule-50 and null-move window edges.
// ---------------------------------------------------------------------------
void test_node_bound() {
    using forge::SearcherTestProbe;
    struct NodeCase {
        const char* name;
        const char* fen;
        const char* moves;
        int root;  // -1 = current
        bool bound;  // the detector fires for the side to move
    };
    // The side to move is a queen down in all of them and its position is new
    // (not itself a repetition), so without the bound its score is far below
    // zero unless the search finds and plays the quiet drawing move itself.
    const std::vector<NodeCase> cases = {
        {"N1 in-tree target (distance 3)", "4kq2/8/8/8/8/8/8/4K1N1 w - - 0 1", "g1f3 e8d8 e1d1 d8e8", 0, true},
        {"N2 same, target before the root once", "4kq2/8/8/8/8/8/8/4K1N1 w - - 0 1", "g1f3 e8d8 e1d1 d8e8", -1,
         false},
        {"N3 null-move window excludes the target", "4kq2/8/8/8/8/8/8/4K1N1 w - - 0 1", "g1f3 0000 e1d1 0000", 0,
         false},
        {"N4 rule-50 edge: target right after a pawn move", "4kq2/8/8/8/8/8/P7/4K1N1 w - - 0 1",
         "a2a3 e8d8 g1f3 d8e8", 0, true},
        {"N5 null-move edge: target is the null position", "4kq2/8/8/8/8/8/8/4K1N1 w - - 0 1",
         "0000 e8d8 g1f3 d8e8", 0, true},
    };
    for (const NodeCase& c : cases) {
        Board board;
        if (!setup(board, c.fen, c.moves)) {
            check(false, std::string(c.name) + ": setup failed");
            continue;
        }
        const std::size_t root = c.root < 0 ? board.history_size() - 1 : static_cast<std::size_t>(c.root);
        check(board.upcoming_repetition(root) == c.bound, std::string(c.name) + ": detector");
        check(reference_upcoming(board, root) == c.bound, std::string(c.name) + ": reference");
        for (const int depth : {0, 1, 3}) {
            forge::Searcher off_searcher(4, 1);
            forge::Searcher on_searcher(4, 1);
            // Null window at the draw score: the bound fails the node high at once.
            const auto off = SearcherTestProbe::run(off_searcher, board, root, depth, -1, 0, false);
            const auto on = SearcherTestProbe::run(on_searcher, board, root, depth, -1, 0, true);
            // Full window: the bound lifts the result to the draw score.
            const auto off_full = SearcherTestProbe::run(off_searcher, board, root, depth, -forge::Infinite,
                                                         forge::Infinite, false);
            const auto on_full = SearcherTestProbe::run(on_searcher, board, root, depth, -forge::Infinite,
                                                        forge::Infinite, true);
            std::cout << "node: " << c.name << " depth " << depth << ": null window OFF " << off.score << " ("
                      << off.nodes << " nodes) ON " << on.score << " (" << on.nodes << " nodes); full window OFF "
                      << off_full.score << " ON " << on_full.score << '\n';
            check(off.nodes > 0, std::string(c.name) + ": OFF has to search the node");
            if (depth == 0) {
                // Quiescence does not try the quiet drawing move.
                check(off.score < 0 && off_full.score < -300, std::string(c.name) + ": OFF quiescence sees a loss");
            }
            if (c.bound) {
                check(on.score == 0 && on.nodes == 0, std::string(c.name) + ": ON fails high at once with 0");
                check(on_full.score == 0, std::string(c.name) + ": ON full-window score is the draw score");
            } else {
                check(off.score < 0 && off_full.score < -300, std::string(c.name) + ": OFF score is a loss");
                // No bound: ON searches as well and keeps the loss. At depth <= 1
                // no node below can have a repetition target, so ON == OFF exactly.
                check(on.score < 0 && on.nodes > 0, std::string(c.name) + ": ON searches and fails low");
                check(on_full.score < -300, std::string(c.name) + ": ON full-window score stays a loss");
                if (depth <= 1) {
                    check(on.score == off.score && on.nodes == off.nodes && on_full.score == off_full.score,
                          std::string(c.name) + ": ON == OFF when the bound does not apply");
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// 5. Search level: forced perpetual-check draws. With CuckooRep on the search
//    returns the draw score at a depth where it does not with the option off;
//    a deeper search with the option off confirms the draw.
// ---------------------------------------------------------------------------
int root_score(const std::string& fen, int depth, bool cuckoo) {
    Board board;
    if (!board.set_fen(fen)) return 99999;
    forge::options::cuckoo_rep = cuckoo;
    forge::Searcher searcher(16, 1);
    searcher.clear();
    forge::SearchLimits limits;
    limits.depth = depth;
    const forge::SearchInfo info = searcher.search(board, limits, false, forge::Searcher::TTAccess::Exclusive);
    forge::options::cuckoo_rep = false;
    return info.score;
}

void test_search_draws() {
    struct DrawCase {
        const char* name;
        const char* fen;
    };
    // White (or Black in the colour mirrors) is a rook and pawns down; its queen
    // checks from two squares and every reply is a forced king move.
    const std::vector<DrawCase> cases = {
        {"Q1 1.Qe8+ Kh7 2.Qh5+ Kg8 3.Qe8+", "6k1/ppp3p1/8/8/1r6/1q6/4Q1PP/7K w - - 0 1"},
        {"Q2 1.Qh5+ Kg8 2.Qe8+ Kh7 3.Qh5+", "8/ppp3pk/8/8/1r6/8/1q4PP/3Q3K w - - 0 1"},
        {"Q3 colour mirror of Q1", "7k/4q1pp/1Q6/1R6/8/8/PPP3P1/6K1 b - - 0 1"},
        {"Q4 colour mirror of Q2", "3q3k/1Q4pp/8/1R6/8/8/PPP3PK/8 b - - 0 1"},
        {"Q5 file mirror of Q1", "1k6/1p3ppp/8/8/6r1/6q1/PP1Q4/K7 w - - 0 1"},
        {"Q6 file mirror of Q2", "8/kp3ppp/8/8/6r1/8/PP4q1/K3Q3 w - - 0 1"},
    };
    constexpr int ShallowDepth = 3;
    constexpr int DeepDepth = 8;
    int on_only = 0;
    for (const DrawCase& c : cases) {
        const int off = root_score(c.fen, ShallowDepth, false);
        const int on = root_score(c.fen, ShallowDepth, true);
        const int deep_off = root_score(c.fen, DeepDepth, false);
        const int deep_on = root_score(c.fen, DeepDepth, true);
        std::cout << "search: " << c.name << ": depth " << ShallowDepth << " OFF " << off << " ON " << on << "; depth "
                  << DeepDepth << " OFF " << deep_off << " ON " << deep_on << '\n';
        check(deep_off == 0 && deep_on == 0, std::string(c.name) + ": known draw (deep search scores 0)");
        if (on == 0 && off != 0) ++on_only;
    }
    std::cout << "search: draw score with CuckooRep on but not off at depth " << ShallowDepth << ": " << on_only
              << " of " << cases.size() << " positions\n";
    check(on_only >= 5, "at least 5 known repetition draws found only with CuckooRep on");
}

} // namespace

int main(int argc, char** argv) {
    int sequences = 10000;
    if (argc > 1) sequences = std::max(1, std::atoi(argv[1]));
    forge::options::cuckoo_rep = false;
    test_table();
    test_hand_cases();
    test_random_sequences(sequences);
    test_node_bound();
    test_search_draws();
    check(!forge::options::cuckoo_rep, "option restored to its default");
    if (failures == 0) {
        std::cout << "PASS cuckoo_tests checks=" << checks_run << '\n';
        return 0;
    }
    std::cout << "FAIL cuckoo_tests failures=" << failures << " checks=" << checks_run << '\n';
    return 1;
}
