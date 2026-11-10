// Compile the unchanged default path under distinct evaluation symbols.
// Board, attacks, parameters, and EvalTrace remain the real shared types.
#undef FORGE_SPD_WEAK_QUEEN_MASK
#define FORGE_SPD_WEAK_QUEEN_MASK 0
#define Evaluator WeakQueenOracleEvaluator
#define evaluate_traced weak_queen_oracle_traced
#include "eval.cpp"

namespace forge {
int weak_queen_oracle_uncached(const Board& board) {
    return WeakQueenOracleEvaluator::evaluate_uncached(board);
}
int weak_queen_oracle_cached(const Board& board) {
    static WeakQueenOracleEvaluator evaluator;
    return evaluator.evaluate(board);
}
} // namespace forge
