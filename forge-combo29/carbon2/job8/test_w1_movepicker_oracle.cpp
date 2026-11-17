// Step W1 All-Stages MovePicker (Fused Captures, Fused AVX-512 Quiets, Pin-Legality, Cached gives_check,
// and Lazy/Selective HistRework Threat Maps) Two-Binary Differential Oracle + Planted-Fault Verifier.

#define FORGE_UCI_NO_MAIN 1
#include "search.cpp"

#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static void populate_histories(Worker& w) {
        std::mt19937_64 rng(20261117ULL);
        auto rand16 = [&]() -> std::int16_t {
            return static_cast<std::int16_t>(static_cast<int>(rng() % 16001ULL) - 8000);
        };
        for (auto& s : *w.main_history_)
            for (auto& f : s)
                for (auto& t : f) t = rand16();
        for (auto& s : *w.rework_history_)
            for (auto& fb : s)
                for (auto& tb : fb)
                    for (auto& f : tb)
                        for (auto& t : f) t = rand16();
        for (auto& p : *w.capture_history_)
            for (auto& t : p)
                for (auto& v : t) v = rand16();
        for (auto& p1 : *w.continuation_history_)
            for (auto& s1 : p1)
                for (auto& p2 : s1)
                    for (auto& s2 : p2) s2 = rand16();
    }

    static std::vector<std::string> run(const std::vector<std::string>& fens) {
        attacks::init();
        tune::HistRework = 2;
        tune::ContHist4PlyRead = true;

        SharedSearchState shared(16);
        Worker w(shared, 0);
        populate_histories(w);

        for (std::size_t k = 0; k < w.stack_.size(); ++k) {
            w.stack_[k].ply = static_cast<int>(k) - 4;
            w.stack_[k].continuation = &(*w.continuation_history_)[WN][(k * 7) & 63];
            w.stack_[k].current_move = Move{12, 28, 0, Quiet};
            w.stack_[k].moved_piece = WP;
        }
        SearchStack* ss = &w.stack_[8];

        std::vector<std::string> out;
        out.reserve(fens.size() * 2);
        for (const std::string& fen : fens) {
            Board b;
            if (!b.set_fen(fen)) continue;
            const auto legals = b.legal_moves();
            const Move tt = legals.empty() ? Move::none() : legals[legals.size() / 2];
            ss->killers[0] = legals.size() > 1 ? legals[0] : Move::none();
            ss->killers[1] = legals.size() > 2 ? legals[legals.size() - 1] : Move::none();
            (*w.counter_moves_)[WP][28] = legals.size() > 3 ? legals[1] : Move::none();

            for (const auto mode : {MovePicker::Mode::Main, MovePicker::Mode::Quiescence}) {
#ifdef HAS_LAZY_THREAT_READY
                w.threat_map_ready_[static_cast<std::size_t>(ss->ply)] = 0U;
#else
                w.threat_maps_[static_cast<std::size_t>(ss->ply)] = b4::lesser_threats(b);
#endif
                MovePicker picker(b, w, ss, tt, mode);
                std::string rec = (mode == MovePicker::Mode::Main ? "M:" : "Q:");
                Move m;
                while (!(m = picker.next(false)).is_none()) {
                    if (!picker.last_move_known_legal() && !b.is_legal(m)) continue;
                    const bool capture = m.is_capture();
                    const bool quiet = !capture && !m.is_promotion();
#ifdef HAS_LAZY_THREAT_READY
                    const bool gc = picker.has_cached_gives_check() ? picker.cached_gives_check() : b.gives_check(m);
#else
                    const bool gc = b.gives_check(m);
#endif
                    const int hist = quiet
                        ? (picker.has_cached_quiet_history(w.quiet_hist_epoch_) ? picker.cached_quiet_history()
                                                                                : w.quiet_history(b, ss, m))
                        : w.capture_history_value(b, m);
                    rec += Board::move_to_uci(m) + "," + std::to_string(hist) + "," + (gc ? "1" : "0") + "," +
                           (picker.last_move_see_nonnegative() ? "1;" : "0;");
                }
                out.push_back(std::move(rec));
            }
        }
        return out;
    }
};
} // namespace forge

static std::vector<std::string> load_test_fens(const char* path) {
    std::vector<std::string> fens;
    std::ifstream in(path);
    std::string ln;
    while (std::getline(in, ln)) {
        if (!ln.empty() && ln.back() == '\r') ln.pop_back();
        if (!ln.empty()) fens.push_back(ln);
    }
    fens.push_back("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1");
    fens.push_back("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1");
    fens.push_back("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1");
    fens.push_back("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8");
    fens.push_back("4k3/4r3/8/8/8/8/4R3/4K3 w - - 0 1");
    return fens;
}

static std::vector<std::string> generate_records(const std::vector<std::string>& fens) {
    return forge::SearcherTestProbe::run(fens);
}

int main(int argc, char** argv) {
    if (argc < 4) return 1;
    const std::string mode = argv[1];
    const auto fens = load_test_fens(argv[2]);
    const auto recs = generate_records(fens);

    if (mode == "--dump") {
        std::ofstream out(argv[3]);
        for (const auto& r : recs) out << r << "\n";
        std::cout << "W1_PICKER_REF_DUMP sequences=" << recs.size() << "\n";
        return 0;
    }
    if (mode == "--verify") {
        std::ifstream in(argv[3]);
        std::string exp;
        for (std::size_t i = 0; i < recs.size(); ++i) {
            if (!std::getline(in, exp)) return 1;
            if (recs[i] != exp) {
                std::cerr << "W1_PICKER_ORACLE MISMATCH at seq=" << i << " (fen_idx=" << (i / 2) << "):\n"
                          << "  exp: " << exp << "\n  got: " << recs[i] << "\n";
                return 1;
            }
        }
        std::cout << "W1_PICKER_ORACLE PASS: sequences_compared=" << recs.size() << " mismatches=0\n";
        return 0;
    }
    return 1;
}
