// Compile with -DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512. The rename puts this
// copy of the network in forge::nnue512 so it can be linked next to the lock net.

#include "wide_eval.hpp"

#include "forge/nnue.hpp"

static_assert(forge::nnue512::HiddenSize == 512, "build with -DFORGE_NNUE_HIDDEN=512 -Dnnue=nnue512");

namespace forge::t19 {

int network_eval_512(const Board& board) {
    nnue512::Accumulator accumulator;
    nnue512::refresh(board, accumulator);
    return nnue512::evaluate(board, accumulator);
}

bool residual_512() { return nnue512::residual(); }

} // namespace forge::t19
