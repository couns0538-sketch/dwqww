// Adapted only as a diagnostic from our exact historical actual-MovePicker oracle.
// This is not an engine patch. Include the exact bound source, never a copied picker.
#include "forge_sol_S14_cpp_alloc_counter_20261026.hpp"
#ifndef FORGE_PICKER_SOURCE
#error Define FORGE_PICKER_SOURCE to the exact bound src/search.cpp.
#endif
#ifndef FORGE_S14_SOURCE_SHA256
#error Define source/core/workload hashes and role from the validated build plan.
#endif
#ifndef FORGE_S14_CORE_SHA256
#error Missing exact core archive hash.
#endif
#ifndef FORGE_S14_WORKLOAD_SHA256
#error Missing exact workload hash.
#endif
#ifndef FORGE_S14_ROLE
#error Missing explicit L/Lprime/B source role.
#endif
#include FORGE_PICKER_SOURCE
#include "forge_sol_S14_expected_workload_20261026.hpp"
#include <fstream>
#include <sstream>
#include <type_traits>
#include <string_view>

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

std::uint64_t mailbox_checks = 0;

void check_mailbox(const forge::Board& board) {
    constexpr std::array<int,13> expected_types{
        forge::NoPieceType, forge::Pawn, forge::Knight, forge::Bishop,
        forge::Rook, forge::Queen, forge::King, forge::Pawn, forge::Knight,
        forge::Bishop, forge::Rook, forge::Queen, forge::King};
    for (int square = 0; square < 64; ++square) {
        const auto bit = forge::square_bb(square);
        forge::Piece found = forge::Empty;
        for (int value = forge::WP; value <= forge::BK; ++value) {
            const auto piece = static_cast<forge::Piece>(value);
            if ((board.pieces(piece) & bit) == 0) continue;
            require(found == forge::Empty, "overlapping piece bitboards");
            found = piece;
        }
        const auto actual = board.piece_at(square);
        require(actual >= forge::Empty && actual <= forge::BK && actual == found,
                "mailbox/bitboard mismatch");
        require(forge::piece_type(actual) == expected_types[static_cast<std::size_t>(actual)],
                "piece enum/type mismatch");
        require(((board.occupied(forge::White) & bit) != 0) == forge::is_white(actual) &&
                ((board.occupied(forge::Black) & bit) != 0) == forge::is_black(actual),
                "mailbox/color occupancy mismatch");
    }
    ++mailbox_checks;
}

struct PickerSlot {
    alignas(forge::MovePicker) std::byte storage[sizeof(forge::MovePicker)];
    forge::MovePicker* picker = nullptr;
    forge_s14_alloc::Stats constructor_stats;
    PickerSlot(const forge::Board& board, const forge::Worker& worker,
               const forge::SearchStack* stack, forge::Move tt,
               forge::MovePicker::Mode mode, bool inject) {
        {
            forge_s14_alloc::Window window(constructor_stats);
            picker = ::new (static_cast<void*>(storage)) forge::MovePicker(board, worker, stack, tt, mode);
            if (inject) {
                void* p = forge_s14_alloc::control_allocate(0);
                forge_s14_alloc::escape(p);
                forge_s14_alloc::control_free(p, 0);
            }
        }
    }
    ~PickerSlot() { if (picker != nullptr) picker->~MovePicker(); }
    PickerSlot(const PickerSlot&) = delete;
    PickerSlot& operator=(const PickerSlot&) = delete;
};

void exercise(forge::Board& board, std::size_t case_id, const std::string& case_name,
              forge::Worker& worker, std::array<forge::SearchStack,8>& stack, bool inject) {
    using forge::MovePicker;
    const State original(board);
    check_mailbox(board);
    const auto legal = board.legal_moves();
    auto* ss = forge::SearcherTestProbe::configure(worker, stack, board, legal);
    const forge::Move main_tt = legal.empty() ? forge::Move::none() : legal[case_id % legal.size()];
    forge::Move qs_tt = main_tt;
    for (auto move : legal) if (move.is_capture() || move.is_promotion()) { qs_tt = move; break; }
    constexpr std::array<const char*,6> names{
        "Mainnone", "MainTT", "Mainskipquiet", "skipafter3legal", "QSnone", "QSTT"};
    for (unsigned variant = 0; variant < names.size(); ++variant) {
        const auto mode = variant >= 4 ? MovePicker::Mode::Quiescence : MovePicker::Mode::Main;
        const auto tt = variant == 1 ? main_tt : (variant == 5 ? qs_tt : forge::Move::none());
        PickerSlot slot(board, worker, ss, tt, mode, inject && case_id == 0 && variant == 0);
        require(!slot.constructor_stats.overflow && slot.constructor_stats.calls == 0 &&
                slot.constructor_stats.bytes == 0, "allocation violation in picker constructor window");
        forge_s14_alloc::Stats next_stats;
        std::string sequence, legality;
        unsigned legal_returned = 0, total_returned = 0;
        bool ended = false;
        for (unsigned count = 0; count <= forge::MoveList::Capacity; ++count) {
            original.assert_same(board); // Formatting/checking stays OUTSIDE allocation windows.
            const bool skip = variant == 2 || (variant == 3 && legal_returned >= 3);
            forge::Move move;
            forge_s14_alloc::Stats one;
            {
                forge_s14_alloc::Window window(one);
                move = slot.picker->next(skip);
            }
            require(!one.overflow, "allocation counter overflow");
            next_stats.calls += one.calls;
            next_stats.bytes += one.bytes;
            require(one.calls == 0 && one.bytes == 0, "allocation violation in picker next window");
            original.assert_same(board);
            if (move.is_none()) { ended = true; break; }
            require(count < forge::MoveList::Capacity, "picker returned >256 moves without terminator");
            require(board.is_pseudo_legal(move), "picker returned non-pseudo-legal move");
            const bool valid = board.is_legal(move);
            if (count < 64) {
                if (!sequence.empty()) sequence += ',';
                sequence += forge::Board::move_to_uci(move);
                legality += valid ? 'L' : 'I';
            }
            ++total_returned;
            if (valid) {
                ++legal_returned;
                forge::Undo undo;
                require(board.make_move(move, undo), "legal returned move rejected");
                check_mailbox(board);
                board.unmake_move(move, undo);
                check_mailbox(board);
                original.assert_same(board);
            }
        }
        require(ended, "picker failed terminator guard");
        std::cout << "PICK\t" << case_id << '\t' << case_name << '\t' << names[variant]
                  << '\t' << original.fen << '\t' << sequence << '\t' << legality
                  << '\t' << total_returned << '\t' << legal_returned << "\t1\t"
                  << slot.constructor_stats.calls << '\t' << next_stats.calls << '\t'
                  << slot.constructor_stats.bytes << '\t' << next_stats.bytes << '\n';
    }
}
}

int main(int argc, char** argv) {
    try {
        require(argc == 2 || argc == 3, "usage: picker workload20.tsv [--negative-counter-disabled|--negative-inject-allocation]");
        std::string mode = "NORMAL";
        bool inject = false;
        if (argc == 3) {
            const std::string_view option(argv[2]);
            if (option == "--negative-counter-disabled") {
                forge_s14_alloc::disabled_control = true;
                mode = "counter_disabled";
            } else if (option == "--negative-inject-allocation") {
                inject = true;
                mode = "inject_allocation";
            } else throw std::runtime_error("unknown diagnostic argument");
        }
        require(std::string_view(FORGE_S14_ROLE) == "L" || std::string_view(FORGE_S14_ROLE) == "Lprime" ||
                std::string_view(FORGE_S14_ROLE) == "B", "unknown source role");
        std::cout << "FORGE_S14_PICKER_V1\t" << FORGE_S14_ROLE << '\t' << FORGE_S14_SOURCE_SHA256
                  << '\t' << FORGE_S14_CORE_SHA256 << '\t' << FORGE_S14_WORKLOAD_SHA256
                  << "\tcpp_new_family_v1;direct_C_alloc_uncovered;thread_local_only\t20\t6\t64\t" << mode << '\n';
        forge_s14_alloc::positive_controls(); // Failure is not a successful zero-allocation observation.
        forge::Searcher searcher(1,1);
        auto& worker = searcher.main_worker();
        forge::SearcherTestProbe::seed(worker); // Preserved historical seed/setup, OUTSIDE windows.
        std::array<forge::SearchStack,8> stack{};
        forge::Board board;
        std::ifstream input(argv[1]);
        require(input.good(), "missing workload");
        std::string line;
        std::size_t cases = 0;
        while (std::getline(input, line)) {
            require(cases < forge_s14_fixture::Workload.size(), "too many workload rows");
            const auto tab = line.find('\t');
            require(tab != std::string::npos && line.find('\t', tab + 1) == std::string::npos,
                    "workload must be id<TAB>FEN");
            const auto name = line.substr(0,tab), fen = line.substr(tab + 1);
            require(name == forge_s14_fixture::Workload[cases].first &&
                    fen == forge_s14_fixture::Workload[cases].second, "compiled workload row mismatch");
            require(board.set_fen(fen), "invalid workload FEN");
            exercise(board,cases,name,worker,stack,inject);
            ++cases;
        }
        require(input.eof() && !input.bad() && cases == 20, "incomplete20-row workload");
        require(std::cout.good(), "stdout write failed");
        std::cout << "DONE\t20\t120\t" << mailbox_checks << '\t' << forge_s14_alloc::windows << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "S14 diagnostic FAIL: " << error.what() << '\n';
        return 1;
    }
}
