#pragma once

namespace forge {
class Board;
namespace t19 {
// Network output of the 512-wide net, in centipawns, from nnue::evaluate.
[[nodiscard]] int network_eval_512(const Board& board);
[[nodiscard]] bool residual_512();
} // namespace t19
} // namespace forge
