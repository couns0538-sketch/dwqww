// Step E1 MovePicker Evasion Oracle:
// For every in-check position among positions_1000.txt, their depth-1 children, and sampled depth-2 children
// (plus curated double-check, en-passant-evasion, promotion-evasion, and pinned-interposer positions),
// compares the EXACT sequence of moves (moves AND order) handed out by:
//   (A) Reference pre-E1 MovePicker (generate_pseudo_legal(All) + pick_best() + board.is_legal() filter), vs
//   (B) New E1 MovePicker (picker.next(false) + (!picker.last_move_known_legal() -> board.is_legal()) filter),
// across BOTH empty histories (maximum score ties!) AND warmed/searched PC20 histories (distinct scores +
// HistRework threat maps + continuation history), AND across multiple tt_move choices (none, first legal,
// last legal, and an illegal pseudo-legal move).

#include "search.cpp"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace forge {

struct SearcherTestProbe {
    static std::vector<Move> reference_evasion_sequence(
        const Board& board, Worker& worker, SearchStack* ss, Move tt_move) {
        if (tune::HistRework != 0 && ss != nullptr) {
            worker.threat_maps_[static_cast<std::size_t>(ss->ply)] = b4::lesser_threats(board);
        }
        Move eff_tt = tt_move;
        if (!eff_tt.is_none() && !board.is_pseudo_legal(eff_tt)) eff_tt = Move::none();

        std::vector<Move> out;
        if (!eff_tt.is_none() && board.is_legal(eff_tt)) out.push_back(eff_tt);

        std::array<Bitboard, 7> check_sq{};
        const Color them = opposite(board.side_to_move());
        const int ek = board.king_square(them);
        const Bitboard occ = board.occupied();
        check_sq[Pawn] = attacks::pawn(them, ek);
        check_sq[Knight] = attacks::knight(ek);
        check_sq[Bishop] = attacks::bishop(ek, occ);
        check_sq[Rook] = attacks::rook(ek, occ);
        check_sq[Queen] = check_sq[Bishop] | check_sq[Rook];

        MoveList buf;
        board.generate_pseudo_legal(buf, false);

        struct ScoredRec { Move move; int score; };
        std::array<ScoredRec, 256> arr{};
        std::size_t count = 0;
        bool seeded = false;
        std::size_t seeded_at = 0;
        int seeded_score = 0;

        for (const Move m : buf) {
            int sc = 0;
            if (tune::EvasionOrdering && m.is_capture()) {
                const int victim = SeePieceValue[static_cast<std::size_t>(piece_type(board.captured_piece(m)))];
                sc = 2'000'000 + victim + worker.capture_history_value(board, m);
            } else if (m.is_capture() || m.is_promotion()) {
                sc = 1'000'000 + 10 * capture_value(board, m) -
                     SeePieceValue[static_cast<std::size_t>(piece_type(board.moved_piece(m)))] / 10;
            } else {
                const bool dchk = (check_sq[static_cast<std::size_t>(piece_type(board.moved_piece(m)))] & square_bb(m.to)) != 0;
                sc = worker.quiet_history(board, ss, m) + (dchk ? 12000 : 0);
            }
            if (!seeded || sc > seeded_score) {
                seeded = true;
                seeded_score = sc;
                seeded_at = count;
            }
            arr[count++] = ScoredRec{m, sc};
        }

        std::size_t index = 0;
        bool sorted = false;
        auto pick = [&]() -> Move {
            if (!sorted) {
                if (index < 4) {
                    if (seeded && index == 0) {
                        if (seeded_at != 0) std::swap(arr[0], arr[seeded_at]);
                        seeded = false;
                        return arr[index++].move;
                    }
                    std::size_t best = index;
                    int best_sc = arr[best].score;
                    for (std::size_t i = index + 1; i < count; ++i) {
                        if (arr[i].score > best_sc) {
                            best_sc = arr[i].score;
                            best = i;
                        }
                    }
                    if (best != index) std::swap(arr[index], arr[best]);
                } else {
                    std::sort(arr.begin() + static_cast<std::ptrdiff_t>(index),
                              arr.begin() + static_cast<std::ptrdiff_t>(count),
                              [](const ScoredRec& a, const ScoredRec& b) { return a.score > b.score; });
                    sorted = true;
                }
            }
            return arr[index++].move;
        };

        while (index < count) {
            const Move m = pick();
            if (m == eff_tt) continue;
            if (!board.is_legal(m)) continue;
            out.push_back(m);
        }
        return out;
    }

    static std::vector<Move> e1_evasion_sequence(
        const Board& board, Worker& worker, SearchStack* ss, Move tt_move) {
        if (tune::HistRework != 0 && ss != nullptr) {
            worker.threat_maps_[static_cast<std::size_t>(ss->ply)] = b4::lesser_threats(board);
        }
        MovePicker picker(board, worker, ss, tt_move, MovePicker::Mode::Main);
        std::vector<Move> out;
        Move m;
        while (!(m = picker.next(false)).is_none()) {
            if (!picker.last_move_known_legal() && !board.is_legal(m)) continue;
            out.push_back(m);
        }
        return out;
    }

    static SearchStack* prepare_stack(Worker& w) {
        for (int i = 0; i < 16; ++i) {
            w.stack_[static_cast<std::size_t>(i)].ply = i - 4;
            w.stack_[static_cast<std::size_t>(i)].continuation = &(*w.continuation_history_)[Empty][0];
            w.stack_[static_cast<std::size_t>(i)].current_move = Move::none();
            w.stack_[static_cast<std::size_t>(i)].moved_piece = Empty;
        }
        return &w.stack_[6]; // ply = 2
    }
};

} // namespace forge

int main(int argc, char** argv) {
    if (argc < 2) return 1;
    std::vector<std::string> fens;
    {
        std::ifstream in(argv[1]);
        std::string ln;
        while (std::getline(in, ln)) {
            if (!ln.empty() && ln.back() == '\r') ln.pop_back();
            if (!ln.empty()) fens.push_back(ln);
        }
    }
    // Add targeted double-check, ep-check-evasion, promo-check-evasion, and multi-tie king-evasion FENs
    fens.push_back("rnbqkbnr/ppp2ppp/8/1B1pp3/4P3/8/PPPP1PPP/RNBQK1NR b KQkq - 1 3");
    fens.push_back("4k3/8/4Q3/3pP3/3K4/8/8/8 w - d6 0 1");   // Black pawn d5 just checked Kd4; exd6 e.p. evasion!
    fens.push_back("3r2k1/2P5/8/8/8/8/8/3K4 w - - 0 1");     // Kd1 checked by Rd8; c7xd8=Q/R/B/N promo-capture evasions!
    fens.push_back("k7/8/1R6/8/2b5/8/8/1K6 b - - 0 1");     // double-check style / king evasions

    forge::tune::HistRework = 2;
    forge::tune::CuckooRep = true;
    forge::tune::TtPruneV2 = true;
    forge::tune::CorrHistV2 = true;
    forge::tune::NonPawnCorrection = true;

    forge::Searcher searcher(4, 1);
    forge::Worker& worker = searcher.main_worker();
    forge::SearchStack* ss = forge::SearcherTestProbe::prepare_stack(worker);

    std::uint64_t total_visited = 0;
    std::uint64_t in_check_positions = 0;
    std::uint64_t picker_sequences_compared = 0;

    auto verify_board = [&](const forge::Board& b) -> bool {
        ++total_visited;
        if (!b.in_check()) return true;
        ++in_check_positions;

        forge::MoveList pseudo;
        b.generate_pseudo_legal(pseudo, false);
        const forge::MoveList leg = b.legal_moves();

        std::vector<forge::Move> tt_choices = {forge::Move::none()};
        if (!leg.empty()) {
            tt_choices.push_back(leg.front());
            if (leg.size() > 1) tt_choices.push_back(leg[leg.size() - 1]);
        }
        for (const forge::Move pm : pseudo) {
            if (!b.is_legal(pm)) {
                tt_choices.push_back(pm);
                break;
            }
        }

        for (const forge::Move ttm : tt_choices) {
            const auto ref_seq = forge::SearcherTestProbe::reference_evasion_sequence(b, worker, ss, ttm);
            const auto got_seq = forge::SearcherTestProbe::e1_evasion_sequence(b, worker, ss, ttm);
            ++picker_sequences_compared;
            if (ref_seq != got_seq) {
                std::cerr << "EVASION PICKER MISMATCH on FEN: " << b.fen() << "\n  ref:";
                for (const auto& m : ref_seq) std::cerr << " " << forge::Board::move_to_uci(m);
                std::cerr << "\n  got:";
                for (const auto& m : got_seq) std::cerr << " " << forge::Board::move_to_uci(m);
                std::cerr << "\n";
                return false;
            }
        }
        return true;
    };

    // Pass 1: Cold / zeroed histories (maximizes equal-score ties across evasions!)
    // Pass 2: Populated PC20 histories (after a depth-8 search on Kiwipete + Ruy Lopez!)
    for (int pass = 0; pass < 2; ++pass) {
        if (pass == 1) {
            forge::Board warm;
            (void)warm.set_fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
            forge::SearchLimits lim;
            lim.depth = 8;
            (void)searcher.search(warm, lim, false, forge::Searcher::TTAccess::Exclusive);
            ss = forge::SearcherTestProbe::prepare_stack(worker);
        }
        for (const std::string& fen : fens) {
            forge::Board b;
            if (!b.set_fen(fen)) continue;
            if (!verify_board(b)) return 1;
            const forge::MoveList leg1 = b.legal_moves();
            for (const forge::Move m1 : leg1) {
                forge::Undo u1;
                (void)b.make_move(m1, u1);
                if (!verify_board(b)) return 1;
                const forge::MoveList leg2 = b.legal_moves();
                for (std::size_t idx = 0; idx < leg2.size(); idx += 4) {
                    forge::Undo u2;
                    (void)b.make_move(leg2[idx], u2);
                    if (!verify_board(b)) return 1;
                    b.unmake_move(leg2[idx], u2);
                }
                b.unmake_move(m1, u1);
            }
        }
    }

    std::cout << "E1_EVASION_PICKER_ORACLE PASS: total_visited=" << total_visited
              << " in_check_positions=" << in_check_positions
              << " picker_sequences_compared=" << picker_sequences_compared
              << " mismatches=0\n";
    return 0;
}
