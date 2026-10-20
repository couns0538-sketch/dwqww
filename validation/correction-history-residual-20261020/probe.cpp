// Invoke actual frozen Forge methods through existing production friendship.
#include "forge/search.hpp"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace forge {
struct SearcherTestProbe {
    static int eval(const Worker& w, const Board& b, int raw) { return w.corrected_eval(b, raw); }
    static void update(Worker& w, const Board& b, int depth, int best, int corrected) {
        w.update_correction(b, depth, best, corrected);
    }
    static CorrectionHistory& pawns(Worker& w) { return *w.correction_history_; }
    static CorrectionHistory& material(Worker& w) { return *w.material_correction_; }
};
}
using namespace forge;
using Probe = SearcherTestProbe;
namespace {
int failures = 0, checks = 0;
bool incremental = false;
void check(bool okay, const std::string& name) {
    ++checks;
    if (!okay) ++failures;
    std::cout << (okay ? "PASS " : "FAIL ") << name << '\n';
}
Board position(const std::string& fen) {
    Board b;
    if (!b.set_fen(fen)) throw std::runtime_error("invalid fixture FEN: " + fen);
    return b;
}
std::size_t pawn_index(const Board& b) { return b.pawn_key() & (CorrectionSize - 1U); }
std::size_t find_material(Worker& w, const Board& b) {
    w.clear();
    tune::MaterialCorrectionWeight = 100;
    Probe::update(w, b, 15, 106, 100);
    const auto side = static_cast<std::size_t>(b.side_to_move());
    std::size_t found = CorrectionSize, count = 0;
    for (std::size_t i = 0; i < CorrectionSize; ++i) {
        if (Probe::material(w)[side][i] != 0) { found = i; ++count; }
    }
    check(count == 1, "actual method writes exactly one material index");
    w.clear();
    return found;
}
int& pawn(Worker& w, const Board& b) { return Probe::pawns(w)[b.side_to_move()][pawn_index(b)]; }
int& material(Worker& w, const Board& b, std::size_t index) { return Probe::material(w)[b.side_to_move()][index]; }
void state(const std::string& label, Worker& w, const Board& b, std::size_t mi, int raw, int n) {
    std::cout << "STATE " << label << " iteration=" << n << " pawn=" << pawn(w,b)
              << " material=" << material(w,b,mi) << " corrected=" << Probe::eval(w,b,raw) << '\n';
}
}
int main(int argc, char** argv) {
    if (argc != 2 || (std::string(argv[1]) != "ema" && std::string(argv[1]) != "increment")) return 2;
    incremental = std::string(argv[1]) == "increment";
    std::cout << "MODEL_EXPECTATION " << argv[1] << " grain=" << CorrectionGrain << " limit=" << CorrectionLimit << '\n';
    const auto a = position("4k3/8/8/8/8/8/P7/4K3 w - - 0 1");
    const auto b = position("4k3/8/8/8/8/8/1P6/4K3 w - - 0 1");
    const auto opposite = position("4k3/8/8/8/8/8/P7/4K3 b - - 0 1");
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    auto& w = *worker;
    const auto mi = find_material(w,a), mbi = find_material(w,b);
    check(mi == mbi && pawn_index(a) != pawn_index(b), "fixtures share actual material index and have distinct pawn indices");
    std::cout << "FIXTURE a=" << a.fen() << " pawn_index=" << pawn_index(a) << " material_index=" << mi << '\n';
    std::cout << "FIXTURE b=" << b.fen() << " pawn_index=" << pawn_index(b) << " material_index=" << mbi << '\n';
    for (const auto [depth, expected] : std::array<std::pair<int,int>,4>{{{0,6},{14,90},{15,96},{100,96}}}) {
        for (int sign : {-1,1}) {
            w.clear(); tune::MaterialCorrectionWeight = 0;
            Probe::update(w,a,depth,100+sign*6,100);
            check(pawn(w,a) == sign*expected && material(w,a,mi) == 0,
                  "signed depth weight depth=" + std::to_string(depth) + " sign=" + std::to_string(sign));
        }
    }
    for (int sign : {-1,1}) {
        w.clear(); tune::MaterialCorrectionWeight = 100;
        Probe::update(w,a,15,100+sign*100,100);
        check(pawn(w,a) == sign*128 && material(w,a,mi) == sign*128, "diff clips at signed eight cp");
        check(Probe::eval(w,a,100) == 100+sign, "two fixed-point tables combine before division");
        w.clear(); tune::MaterialCorrectionWeight = 0;
        pawn(w,a) = sign*512;
        const int corrected = Probe::eval(w,a,100);
        Probe::update(w,a,15,corrected,corrected);
        check(pawn(w,a) == sign*(incremental ? 512 : 480), "zero-residual seeded history decay or retention");
        pawn(w,a) = sign;
        Probe::update(w,a,15,100,100);
        check(pawn(w,a) == (incremental ? sign : 0), "signed truncation on subgrain seeded entry");
        w.clear(); pawn(w,a) = sign*CorrectionLimit;
        Probe::update(w,a,15,100+sign*100,100);
        check(pawn(w,a) == sign*(incremental ? 8192 : 7808), "seeded endpoint with outward residual");
        state("endpoint",w,a,mi,100,1);
        w.clear(); tune::MaterialCorrectionWeight = 33;
        material(w,a,mi) = sign*777;
        check(Probe::eval(w,a,100) == 100+sign, "signed material coefficient33 rounds before grain division");
        material(w,a,mi) = sign*775;
        check(Probe::eval(w,a,100) == 100, "signed subgrain material correction truncates toward zero");
        Probe::update(w,a,15,106,100);
        check(pawn(w,a) == 96 && material(w,a,mi) == (incremental ? sign*775+96 : (sign*775*240+1536*16)/256),
              "material coefficient affects read scale but not update gain");
        for (int mw : {0,100}) {
            w.clear(); tune::MaterialCorrectionWeight = mw;
            const std::string label = "delta" + std::to_string(sign*6) + "_material" + std::to_string(mw);
            for (int n = 1; n <= 4096; ++n) {
                Probe::update(w,a,15,100+sign*6,Probe::eval(w,a,100));
                if (n==1 || n==16 || n==64 || n==256 || n==4096) state(label,w,a,mi,100,n);
            }
            const int expected_entry = incremental ? (mw==0 ? 1536 : 768) : (mw==0 ? 768 : 512);
            const int expected_cp = incremental ? 6 : (mw==0 ? 3 : 4);
            check(pawn(w,a) == sign*expected_entry && Probe::eval(w,a,100) == 100+sign*expected_cp,
                  "fixed delta6 convergence " + label);
            check(material(w,a,mi) == (mw==0 ? 0 : pawn(w,a)), "one-table isolation or equal two-table entries");
            check(Probe::eval(w,opposite,100) == 100, "opposite-side table remains untouched");
            check(Probe::eval(w,b,100) == 100 + (mw==0 ? 0 : material(w,a,mi)/CorrectionGrain),
                  "shared material transfers correction to distinct pawn structure");
            const int before_material = material(w,a,mi), before_pawn_a = pawn(w,a);
            Probe::update(w,b,15,100-sign*6,Probe::eval(w,b,100));
            check(pawn(w,a) == before_pawn_a && (mw==0 ? material(w,a,mi) == before_material : material(w,a,mi) != before_material),
                  mw==0 ? "disabled material control" : "other pawn structure changes shared material entry");
            state(label+"_after_conflict",w,a,mi,100,4097);
            w.clear(); tune::MaterialCorrectionWeight = mw;
            for (int n=1; n<=4096; ++n) Probe::update(w,a,15,100+sign*100,Probe::eval(w,a,100));
            state("large_residual_material"+std::to_string(mw),w,a,mi,100,4096);
            check(std::abs(pawn(w,a)) == (incremental ? CorrectionLimit : 2033), "reachable range under constant clipped residual");
        }
    }
    w.clear(); tune::MaterialCorrectionWeight = 100;
    pawn(w,a)=1024; material(w,a,mi)=-512;
    Probe::update(w,a,15,106,Probe::eval(w,a,100));
    check(pawn(w,a)==(incremental?1088:1024) && material(w,a,mi)==(incremental?-448:-416),
          "unequal tables consume same precomputed joint residual");
    state("unequal_tables",w,a,mi,100,1);
    w.clear(); pawn(w,a)=CorrectionLimit; material(w,a,mi)=CorrectionLimit;
    check(Probe::eval(w,a,MateInMaxPly-2)==MateInMaxPly-1, "upper output mate boundary clamps");
    pawn(w,a)=-CorrectionLimit; material(w,a,mi)=-CorrectionLimit;
    check(Probe::eval(w,a,-MateInMaxPly+2)==-MateInMaxPly+1, "lower output mate boundary clamps");
    tune::MaterialCorrectionWeight=100;
    std::cout << "SUMMARY checks=" << checks << " failures=" << failures << '\n';
    return failures==0 ? 0 : 1;
}
