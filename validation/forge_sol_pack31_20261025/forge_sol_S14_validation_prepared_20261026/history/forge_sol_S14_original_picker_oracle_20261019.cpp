// Include the actual frozen source definition, never a copied MovePicker.
#ifndef FORGE_PICKER_SOURCE
#error Define FORGE_PICKER_SOURCE to the exact exported src/search.cpp.
#endif
#include FORGE_PICKER_SOURCE
#include <fstream>
#include <sstream>
#include <type_traits>

namespace forge {
struct SearcherTestProbe {
    template<class T> static void fill(T& value, std::uint64_t& state) {
        if constexpr (std::is_integral_v<T>) {
            state = state * 6364136223846793005ULL + 1442695040888963407ULL;
            int number = static_cast<int>((state >> 32U) % 8191U) - 4095;
            value = static_cast<T>(number == 0 ? 1 : number);
        } else for (auto& item : value) fill(item, state);
    }
    static void seed(Worker& worker) {
        std::uint64_t state = 0x243f6a8885a308d3ULL;
        fill(*worker.main_history_, state);
        fill(*worker.capture_history_, state);
        fill(*worker.continuation_history_, state);
    }
    static SearchStack* configure(Worker& worker, std::array<SearchStack, 8>& stack,
                                  const Board& board, const MoveList& legal) {
        for (auto& entry : stack) {
            entry.current_move = Move::none();
            entry.moved_piece = Empty;
            entry.killers = {};
            entry.continuation = &(*worker.continuation_history_)[WP][0];
        }
        SearchStack* ss = &stack[4];
        ss->ply = 4;
        MoveList quiets;
        for (auto move : legal) if (!move.is_capture() && !move.is_promotion()) quiets.push_back(move);
        if (!quiets.empty()) ss->killers[0] = quiets[0];
        if (quiets.size() > 1) ss->killers[1] = quiets[1];
        for (int back : {1, 2}) {
            if (legal.empty()) continue;
            auto* previous = ss - back;
            previous->current_move = legal[static_cast<std::size_t>(back - 1) % legal.size()];
            previous->moved_piece = board.moved_piece(previous->current_move);
            previous->continuation = &(*worker.continuation_history_)
                [static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to];
        }
        if (!(ss - 1)->current_move.is_none()) {
            const auto* previous = ss - 1;
            (*worker.counter_moves_)[static_cast<std::size_t>(previous->moved_piece)][previous->current_move.to] =
                quiets.size() > 2 ? quiets[2] : Move::none();
        }
        return ss;
    }
};
} // namespace forge

namespace {
void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}
struct State {
    std::string fen;
    std::uint64_t key, pawn_key;
    forge::Bitboard checkers;
    std::size_t history;
    explicit State(const forge::Board& board) : fen(board.fen()), key(board.key()), pawn_key(board.pawn_key()),
        checkers(board.checkers()), history(board.history_size()) {}
    void assert_same(const forge::Board& board) const {
        require(fen == board.fen() && key == board.key() && pawn_key == board.pawn_key() &&
                checkers == board.checkers() && history == board.history_size(), "parent state not restored");
    }
};
std::string fen4(const std::string& epd) {
    std::istringstream input(epd);
    std::string pieces, side, castle, ep;
    require(static_cast<bool>(input >> pieces >> side >> castle >> ep), "malformed EPD");
    return pieces + " " + side + " " + castle + " " + ep + " 0 1";
}
void exercise(forge::Board& board, std::size_t case_id, forge::Worker& worker,
              std::array<forge::SearchStack, 8>& stack) {
    using forge::MovePicker;
    const State original(board);
    const auto legal = board.legal_moves();
    auto* ss = forge::SearcherTestProbe::configure(worker, stack, board, legal);
    const forge::Move main_tt = legal.empty() ? forge::Move::none() : legal[case_id % legal.size()];
    forge::Move qs_tt = main_tt;
    for (auto move : legal) if (move.is_capture() || move.is_promotion()) { qs_tt = move; break; }
    constexpr std::array<const char*, 6> names{"Mainnone", "MainTT", "Mainskipquiet", "skipafter3legal", "QSnone", "QSTT"};
    for (unsigned variant = 0; variant < names.size(); ++variant) {
        const auto mode = variant >= 4 ? MovePicker::Mode::Quiescence : MovePicker::Mode::Main;
        const auto tt = variant == 1 ? main_tt : (variant == 5 ? qs_tt : forge::Move::none());
        MovePicker picker(board, worker, ss, tt, mode);
        std::string sequence, legality;
        unsigned legal_returned = 0;
        bool ended = false;
        for (unsigned count = 0; count <= forge::MoveList::Capacity; ++count) {
            original.assert_same(board); // Never query a lazy picker on its child.
            const bool skip = variant == 2 || (variant == 3 && legal_returned >= 3);
            const auto move = picker.next(skip);
            original.assert_same(board);
            if (move.is_none()) { ended = true; break; }
            require(count < forge::MoveList::Capacity, "picker returned >256 moves without terminator");
            require(board.is_pseudo_legal(move), "picker returned non-pseudo-legal move");
            if (!sequence.empty()) sequence += ',';
            sequence += forge::Board::move_to_uci(move);
            const bool valid = board.is_legal(move);
            legality += valid ? 'L' : 'I';
            if (valid) {
                ++legal_returned;
                forge::Undo undo;
                require(board.make_move(move, undo), "legal returned move rejected");
                // Parent stays modified until this unmake; no picker.next here.
                board.unmake_move(move, undo);
                original.assert_same(board);
            }
        }
        require(ended, "picker failed terminator guard");
        std::cout << case_id << '\t' << names[variant] << '\t' << original.fen << '\t'
                  << sequence << '\t' << legality << '\n';
    }
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc == 3, "usage: picker_differential corpus.epd fixtures.tsv");
        forge::Searcher searcher(1, 1);
        auto& worker = searcher.main_worker();
        forge::SearcherTestProbe::seed(worker); // Allocate/fill histories only once.
        std::array<forge::SearchStack, 8> stack{};
        forge::Board board;
        std::ifstream corpus(argv[1]), fixtures(argv[2]);
        require(corpus.good() && fixtures.good(), "missing workload input");
        std::string line;
        std::size_t cases = 0, opening_count = 0, fixture_count = 0;
        while (std::getline(corpus, line)) {
            if (line.empty()) continue;
            require(board.set_fen(fen4(line)), "invalid corpus FEN");
            exercise(board, cases++, worker, stack);
            ++opening_count;
        }
        while (std::getline(fixtures, line)) {
            if (line.empty()) continue;
            const auto first = line.find('\t'), second = line.find('\t', first + 1);
            require(first != std::string::npos && second != std::string::npos, "malformed fixtures");
            require(board.set_fen(line.substr(second + 1)), "invalid fixture FEN");
            exercise(board, cases++, worker, stack);
            ++fixture_count;
        }
        require(opening_count == 10000 && fixture_count == 23, "wrong fixture/corpus count");
        require(std::cout.good(), "stdout write failed");
        std::cerr << "PASS cases=" << cases << " variants=6 rows=" << cases * 6 << '\n';
        return 0;
    } catch (const std::exception& error) { std::cerr << "FAIL " << error.what() << '\n'; return 1; }
}
