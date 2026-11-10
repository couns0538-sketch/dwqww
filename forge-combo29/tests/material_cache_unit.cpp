// White-box cache contract test. Preload dependencies before changing access
// control in the search header; production code has no testing hooks.
#include "forge/board.hpp"
#include "forge/eval.hpp"
#include "forge/nnue.hpp"
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>
#define private public
#include "forge/search.hpp"
#undef private
#include "../src/search.cpp"
#include <cstdlib>
#include <iostream>

#if !FORGE_SPD_MATERIAL_CORRECTION_CACHE
#error "Compile this focused test with FORGE_SPD_MATERIAL_CORRECTION_CACHE=1"
#endif

namespace {
void require(bool value, const char* message) {
    if (!value) {
        std::cerr << "FAIL: " << message << '\n';
        std::exit(1);
    }
}
}

int main() {
    using namespace forge;
    SharedSearchState shared(1);
    auto worker = std::make_unique<Worker>(shared, 0);
    Board board;
    SearchStack* ss = worker->stack_.data() + 4;
    ss->ply = 1;
    const int saved_weight = tune::MaterialCorrectionWeight;
    const bool saved_nnue = nnue::enabled;
    for (bool nnue_on : {false, true}) {
        nnue::enabled = nnue_on;
        for (const char* fen : {
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
            "4k3/8/8/8/8/8/8/3QK3 b - - 0 1"}) {
            require(board.set_fen(fen), "Fixture FEN");
            ss->material_correction_index = CorrectionSize;
            tune::MaterialCorrectionWeight = 0;
            (void)worker->corrected_eval(board, ss, 123);
            worker->update_correction(board, ss, 4, 130, 123);
            require(ss->material_correction_index == CorrectionSize,
                    "Disabled correction eagerly computed material index");
            tune::MaterialCorrectionWeight = 100;
            (void)worker->corrected_eval(board, ss, 123);
            const auto expected = material_key(board) & (CorrectionSize - 1U);
            require(ss->material_correction_index == expected, "Incorrect lazy index");
            worker->update_correction(board, ss, 4, 130, 123);
            require(ss->material_correction_index == expected, "Index changed within node");
            // A deliberately seeded cache value proves reuse rather than
            // recomputation. No production call is made with this fake value.
            ss->material_correction_index = CorrectionSize - 1U;
            require(material_correction_index(board, ss) == CorrectionSize - 1U,
                    "Cache getter did not reuse stored index");
            // Force the earliest return after entry. Both positive-depth main
            // search and qsearch must invalidate on *every* reuse, including
            // depth-zero dispatch and same-ply verification-style re-entry.
            worker->aborted_ = true;
            for (int pass = 0; pass < 3; ++pass) {
                ss->material_correction_index = 42;
                (void)worker->qsearch(board, ss, -1, 1);
                require(ss->material_correction_index == CorrectionSize, "Qsearch entry invalidation");
                ss->material_correction_index = 42;
                (void)worker->search(board, ss, 1, -1, 1, false);
                require(ss->material_correction_index == CorrectionSize, "Main entry invalidation");
                ss->material_correction_index = 42;
                (void)worker->search(board, ss, 0, -1, 1, false);
                require(ss->material_correction_index == CorrectionSize, "Depth-zero entry invalidation");
            }
        }
    }
    tune::MaterialCorrectionWeight = saved_weight;
    nnue::enabled = saved_nnue;
    std::cout << "PASS: lazy index, weight-zero skip, NNUE independence, reuse, all search entries\n";
}
