// NNUE v3 evaluation driver (job FB1). Reached only from Worker::static_evaluate
// when UCI NNUEArch is true and a v3 net is loaded; with the option off this
// translation unit is never executed.
//
// The accumulator of a ply is rebuilt lazily from the nearest valid ancestor
// (nnue::v3::make_valid): the piece changes recorded by Worker::record_move in
// SearchStack::dirty are replayed, and a perspective whose king key changed is
// refreshed through the per-worker cache.

#include "forge/nnue_v3.hpp"
#include "forge/search.hpp"

#include <algorithm>
#include <memory>

namespace forge {

int Worker::static_evaluate_v3(const Board& board, SearchStack* ss) {
    const nnue::v3::Net& net = *nnue::v3::loaded();
    if (!v3_state_) v3_state_ = std::make_unique<nnue::v3::WorkerState>();
    nnue::v3::prepare(net, *v3_state_, MaxPly + 8);
    const int index = ss->ply + 4;
    nnue::v3::make_valid(net, *v3_state_, index, board, [this](int k) -> const nnue::DirtyPieces& {
        return stack_[static_cast<std::size_t>(k)].dirty;
    });
    const int network = nnue::v3::evaluate(net, board, v3_state_->stack[static_cast<std::size_t>(index)]);
    if (!net.residual) return network;
    if (!ss->runtime_psqt.valid) {
        // Same lazy scheme for the runtime PSQT of a residual net.
        int back = 0;
        while (back < ss->ply && !(ss - back - 1)->runtime_psqt.valid) ++back;
        if (back >= ss->ply && !(ss - back - 1)->runtime_psqt.valid) {
            ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
        } else {
            for (int i = back; i >= 0; --i) {
                Evaluator::update_runtime_psqt((ss - i - 1)->runtime_psqt, (ss - i)->runtime_psqt, (ss - i)->dirty);
            }
        }
    }
    // A residual network is a learned correction on top of the hand-crafted evaluation.
    return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, -MateInMaxPly + 1, MateInMaxPly - 1);
}

} // namespace forge
