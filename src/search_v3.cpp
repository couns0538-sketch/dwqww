// NNUE v3 evaluation driver (job FB1). Reached only from Worker::static_evaluate
// when UCI NNUEArch is true and a v3 net is loaded; with the option off this
// translation unit is never executed.
//
// M1: every evaluation refreshes both perspectives from scratch (scalar
// reference path). M2 replaces this with the incremental accumulator stack and
// the king-bucket refresh cache.

#include "forge/nnue_v3.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <memory>

namespace forge {

int Worker::static_evaluate_v3(const Board& board, SearchStack* ss) {
    const nnue::v3::Net& net = *nnue::v3::loaded();
    if (!v3_state_) {
        v3_state_ = std::make_unique<nnue::v3::WorkerState>();
        v3_state_->stack.resize(static_cast<std::size_t>(MaxPly + 8));
    }
    nnue::v3::Accumulator& accumulator = v3_state_->stack[static_cast<std::size_t>(ss->ply + 4)];
    nnue::v3::refresh(net, board, accumulator);
    const int network = nnue::v3::evaluate(net, board, accumulator);
    if (!net.residual) return network;
    if (!ss->runtime_psqt.valid) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    // A residual network is a learned correction on top of the hand-crafted evaluation.
    return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}

} // namespace forge
