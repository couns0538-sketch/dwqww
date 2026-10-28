// S14 follow-up: pick-order oracle for FORGE_NOZERO_MOVE_BUFFERS.
//
// MovePicker lives inside src/search.cpp, so this file includes that source (path in FORGE_SEARCH_CPP) and is
// built with every other core source except search.cpp (bitboard board book eval eval_params nnue).
// Adapted from Sol's S14 oracle (17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_S14_validation_prepared_20261026/
// forge_sol_S14_picker_oracle_20261026.cpp): the same history seed, stack set-up and six picker configurations,
// plus a seventh (a quiet TT move); without his allocation counter and fixed 20-row workload.
//
// For each position (EPD roots, optionally their legal children, plus built-in stress positions) and each
// configuration, the picker is placement-constructed in a buffer pre-filled with a byte pattern, and the complete
// sequence returned by next() is recorded together with last_move_see_nonnegative() after each move. A picker
// that read storage it had not written would make the sequence depend on the pattern. Built without the switch,
// the constructor zero-fills that storage, so every pattern gives the reference sequences.
// Independent checks (exit 1 on failure): every returned move is pseudo-legal; the sequence ends within 256 moves;
// without skipping, the main and evasion pickers return each pseudo-legal move exactly once, and the quiescence
// picker returns each pseudo-legal capture/promotion exactly once.
//
// usage: picker_order_oracle <roots.epd> <pattern> [--children N] [--dump N]
//   pattern: zero | a5 | 01 | ff | random  (the byte pattern written into the picker storage before construction)
//            heap  (fresh ::operator new storage per picker, not written before construction: under valgrind
//                   memcheck or MSan any read of picker storage that was never written is reported)
//   --children N: also exercise every legal child of the first N roots (default 2000)
//   --dump N: print every sequence of the first N roots (default 0)
// Output: "ROOT <index> <positions> <sequences> <moves> <digest>" per root (built-in positions are roots 0..11),
// then "TOTAL ..." with the digest over all roots. Build with -fno-lifetime-dse so the pattern survives into the
// object (GCC otherwise drops stores made before a constructor runs).
#ifndef FORGE_SEARCH_CPP
#define FORGE_SEARCH_CPP "../../../src/search.cpp"
#endif
#include FORGE_SEARCH_CPP

#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    template <class T> static void fill(T& value, std::uint64_t& state) {
        if constexpr (std::is_integral_v<T>) {
            state = state * 6364136223846793005ULL + 1442695040888963407ULL;
            const int number = static_cast<int>((state >> 32U) % 8191U) - 4095;
            value = static_cast<T>(number == 0 ? 1 : number);
        } else {
            for (auto& item : value) fill(item, state);
        }
    }
    static void seed(Worker& worker) {
        std::uint64_t state = 0x243f6a8885a308d3ULL;
        fill(*worker.main_history_, state);
        fill(*worker.capture_history_, state);
        fill(*worker.continuation_history_, state);
    }
    // Killers, the two previous moves (for continuation history) and a counter move, as in Sol's oracle;
    // `salt` rotates which legal moves are used so that different positions exercise different stages.
    static SearchStack* configure(Worker& worker, std::array<SearchStack, 8>& stack, const Board& board,
                                  const MoveList& legal, std::size_t salt) {
        for (auto& entry : stack) {
            entry.current_move = Move::none();
            entry.moved_piece = Empty;
            entry.killers = {};
            entry.continuation = &(*worker.continuation_history_)[WP][0];
        }
        SearchStack* ss = &stack[4];
        ss->ply = 4;
        std::vector<Move> quiets;
        for (const Move move : legal) {
            if (!move.is_capture() && !move.is_promotion()) quiets.push_back(move);
        }
        const std::size_t q = quiets.size();
        if (q > 0) ss->killers[0] = quiets[salt % q];
        if (q > 1) ss->killers[1] = quiets[(salt + 1) % q];
        for (int back : {1, 2}) {
            if (legal.size() == 0) continue;
            SearchStack* previous = ss - back;
            previous->current_move = legal[(salt + static_cast<std::size_t>(back) - 1) % legal.size()];
            previous->moved_piece = board.moved_piece(previous->current_move);
            previous->continuation = &(*worker.continuation_history_)
                [static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to];
        }
        if (!(ss - 1)->current_move.is_none()) {
            const SearchStack* previous = ss - 1;
            (*worker.counter_moves_)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to] =
                q > 2 ? quiets[(salt + 2) % q] : Move::none();
        }
        return ss;
    }
};
} // namespace forge

namespace {
using forge::Board;
using forge::Move;
using forge::MovePicker;

void require(bool ok, const std::string& message) {
    if (!ok) throw std::runtime_error(message);
}

struct Digest {
    std::uint64_t h = 1469598103934665603ULL;
    void byte(std::uint8_t b) { h = (h ^ b) * 1099511628211ULL; }
    void u64(std::uint64_t v) { for (int i = 0; i < 8; ++i) byte(static_cast<std::uint8_t>(v >> (8 * i))); }
};

enum class Pattern { Zero, A5, One, FF, Random, Heap };
Pattern parse_pattern(const std::string& text) {
    if (text == "zero") return Pattern::Zero;
    if (text == "a5") return Pattern::A5;
    if (text == "01") return Pattern::One;
    if (text == "ff") return Pattern::FF;
    if (text == "random") return Pattern::Random;
    if (text == "heap") return Pattern::Heap;
    throw std::runtime_error("unknown pattern " + text);
}

alignas(MovePicker) std::byte g_storage[sizeof(MovePicker)];
std::uint64_t g_random_state = 0x9E3779B97F4A7C15ULL;

void* prefill(Pattern pattern) {
    if (pattern == Pattern::Heap) return ::operator new(sizeof(MovePicker));
    switch (pattern) {
    case Pattern::Zero: std::memset(g_storage, 0x00, sizeof g_storage); break;
    case Pattern::A5: std::memset(g_storage, 0xA5, sizeof g_storage); break;
    case Pattern::One: std::memset(g_storage, 0x01, sizeof g_storage); break;
    case Pattern::FF: std::memset(g_storage, 0xFF, sizeof g_storage); break;
    case Pattern::Random:
        for (std::byte& b : g_storage) {
            g_random_state ^= g_random_state << 13U;
            g_random_state ^= g_random_state >> 7U;
            g_random_state ^= g_random_state << 17U;
            b = static_cast<std::byte>(g_random_state >> 56U);
        }
        break;
    case Pattern::Heap: break;
    }
    // The pattern must really be in memory when the constructor starts.
    asm volatile("" : : "r"(g_storage) : "memory");
    return g_storage;
}

std::uint32_t key(Move m) {
    return static_cast<std::uint32_t>(m.from) | (static_cast<std::uint32_t>(m.to) << 8U) |
           (static_cast<std::uint32_t>(m.promotion) << 16U) | (static_cast<std::uint32_t>(m.flags) << 24U);
}

struct Totals {
    std::uint64_t positions = 0, sequences = 0, moves = 0;
};

constexpr std::array<const char*, 7> VariantNames{
    "MainNone", "MainTT", "MainSkipQuiets", "SkipAfter3Legal", "QsNone", "QsTT", "MainQuietTT"};

void exercise(Board& board, std::size_t salt, forge::Worker& worker, std::array<forge::SearchStack, 8>& stack,
              Pattern pattern, Digest& digest, Totals& totals, bool dump) {
    const std::string fen_before = board.fen();
    const forge::MoveList legal = board.legal_moves();
    forge::SearchStack* ss = forge::SearcherTestProbe::configure(worker, stack, board, legal, salt);
    const forge::MoveList pseudo_all = board.pseudo_legal_moves(false);
    const forge::MoveList pseudo_noisy = board.pseudo_legal_moves(true);
    Move main_tt = legal.size() == 0 ? Move::none() : legal[salt % legal.size()];
    Move qs_tt = main_tt;
    Move quiet_tt = Move::none();
    for (const Move move : legal) {
        if (move.is_capture() || move.is_promotion()) { qs_tt = move; break; }
    }
    for (const Move move : legal) {
        if (!move.is_capture() && !move.is_promotion()) { quiet_tt = move; break; }
    }
    const bool in_check = board.in_check();
    ++totals.positions;
    for (std::size_t variant = 0; variant < VariantNames.size(); ++variant) {
        const MovePicker::Mode mode = (variant == 4 || variant == 5) ? MovePicker::Mode::Quiescence : MovePicker::Mode::Main;
        const Move tt = variant == 1 ? main_tt : variant == 5 ? qs_tt : variant == 6 ? quiet_tt : Move::none();
        void* storage = prefill(pattern);
        MovePicker* picker = ::new (storage) MovePicker(board, worker, ss, tt, mode);
        std::vector<Move> sequence;
        std::string text;
        unsigned legal_returned = 0;
        bool ended = false;
        digest.u64(0xFEEDULL + variant);
        for (unsigned count = 0; count <= forge::MoveList::Capacity; ++count) {
            const bool skip = variant == 2 || (variant == 3 && legal_returned >= 3);
            const Move move = picker->next(skip);
            if (move.is_none()) { ended = true; break; }
            require(count < forge::MoveList::Capacity, "more than 256 moves without a terminator");
            require(move.from < 64 && move.to < 64 && board.is_pseudo_legal(move),
                    "picker returned a move that is not pseudo-legal: " + fen_before);
            const bool see_flag = picker->last_move_see_nonnegative();
            if (board.is_legal(move)) ++legal_returned;
            sequence.push_back(move);
            digest.u64(key(move) | (see_flag ? (1ULL << 32U) : 0ULL));
            if (dump) {
                if (!text.empty()) text += ',';
                text += Board::move_to_uci(move);
                if (see_flag) text += '+';
            }
        }
        picker->~MovePicker();
        if (pattern == Pattern::Heap) ::operator delete(storage);
        require(ended, "picker did not terminate: " + fen_before);
        digest.u64(0xABCDULL + sequence.size());
        ++totals.sequences;
        totals.moves += sequence.size();
        // Completeness: each generated move exactly once (only for the configurations that skip nothing).
        if (variant == 0 || variant == 1 || variant == 4 || variant == 5 || variant == 6) {
            const forge::MoveList& expected = (mode == MovePicker::Mode::Quiescence && !in_check) ? pseudo_noisy : pseudo_all;
            std::multiset<std::uint32_t> got, want;
            for (const Move m : sequence) got.insert(key(m));
            for (const Move m : expected) want.insert(key(m));
            // A quiet TT move is dropped by the quiescence picker; it is never part of the noisy list either.
            require(got == want, std::string("picker sequence is not the generated move set (") + VariantNames[variant] +
                                     "): " + fen_before);
        }
        if (dump) std::cout << "SEQ " << VariantNames[variant] << ' ' << fen_before << " | " << text << '\n';
    }
    require(board.fen() == fen_before, "board changed while picking");
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc >= 3, "usage: picker_order_oracle <roots.epd> <zero|a5|01|ff|random|heap> [--children N] [--dump N]");
        const std::string roots_path = argv[1];
        const Pattern pattern = parse_pattern(argv[2]);
        std::size_t children_roots = 2000, dump_roots = 0;
        for (int i = 3; i + 1 < argc; i += 2) {
            const std::string option = argv[i];
            if (option == "--children") children_roots = std::stoul(argv[i + 1]);
            else if (option == "--dump") dump_roots = std::stoul(argv[i + 1]);
            else throw std::runtime_error("unknown option " + option);
        }
        std::cout << "PICKER_ORACLE_V1 nozero=" << FORGE_NOZERO_MOVE_BUFFERS << " pattern=" << argv[2]
                  << " children_roots=" << children_roots << " sizeof(MovePicker)=" << sizeof(MovePicker) << '\n';
        forge::Searcher searcher(1, 1);
        forge::Worker& worker = searcher.main_worker();
        forge::SearcherTestProbe::seed(worker);
        std::array<forge::SearchStack, 8> stack{};

        std::vector<std::string> roots = {
            // Forge's bench positions, kiwipete, QA's two nine-queen bad-capture stress positions, and three more.
            std::string(forge::Board::StandardStartFen),
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
            "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
            "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
            "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
            "1Q1bq3/pr1Q1p1R/KQ1n1Q1b/1p1Q1n1Q/BQ1p1Q1r/1p1QpN2/1k1pR2p/5NB1 w - - 0 1",
            "1krQ2b1/8/Q2pQnR1/p1Q3b1/Q1n2QrQ/p1QQpKp1/q1ppR2p/1NB1BN2 w - - 0 1",
            "3qk3/8/8/3p4/8/8/8/3QK3 w - - 0 1",
            "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2",
        };
        std::ifstream input(roots_path);
        require(input.good(), "cannot read " + roots_path);
        std::string line;
        while (std::getline(input, line)) {
            std::istringstream epd(line);
            std::string placement, side, castling, target;
            if (!(epd >> placement >> side >> castling >> target)) continue;
            roots.push_back(placement + " " + side + " " + castling + " " + target + " 0 1");
        }
        Digest total;
        Totals totals;
        Board board;
        for (std::size_t r = 0; r < roots.size(); ++r) {
            require(board.set_fen(roots[r]), "invalid FEN " + roots[r]);
            Digest digest;
            Totals root_totals;
            const bool dump = r < dump_roots;
            exercise(board, r, worker, stack, pattern, digest, root_totals, dump);
            if (r < children_roots) {
                const forge::MoveList legal = board.legal_moves();
                std::size_t c = 0;
                for (const Move move : legal) {
                    forge::Undo undo;
                    require(board.make_move(move, undo), "legal move rejected");
                    exercise(board, r * 131U + c++, worker, stack, pattern, digest, root_totals, dump);
                    board.unmake_move(move, undo);
                }
            }
            std::printf("ROOT %zu %llu %llu %llu %016llx\n", r, static_cast<unsigned long long>(root_totals.positions),
                        static_cast<unsigned long long>(root_totals.sequences),
                        static_cast<unsigned long long>(root_totals.moves), static_cast<unsigned long long>(digest.h));
            total.u64(digest.h);
            totals.positions += root_totals.positions;
            totals.sequences += root_totals.sequences;
            totals.moves += root_totals.moves;
        }
        std::printf("TOTAL roots %zu positions %llu sequences %llu moves %llu digest %016llx\n", roots.size(),
                    static_cast<unsigned long long>(totals.positions), static_cast<unsigned long long>(totals.sequences),
                    static_cast<unsigned long long>(totals.moves), static_cast<unsigned long long>(total.h));
        std::fflush(stdout);
        return 0;
    } catch (const std::exception& error) {
        std::fflush(stdout);
        std::cerr << "picker_order_oracle FAIL: " << error.what() << '\n';
        return 1;
    }
}
