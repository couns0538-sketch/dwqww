// Compile the unchanged default evaluator under distinct symbols.
#undef FORGE_SPD_EVAL_BITCOUNT_PREDICATES
#define FORGE_SPD_EVAL_BITCOUNT_PREDICATES 0
#define Evaluator BitcountPredicateOracleEvaluator
#define evaluate_traced bitcount_predicate_oracle_traced
#include "eval.cpp"
namespace forge {
int bitcount_predicate_oracle_uncached(const Board& board) {
    return BitcountPredicateOracleEvaluator::evaluate_uncached(board);
}
int bitcount_predicate_oracle_cached(const Board& board) {
    static BitcountPredicateOracleEvaluator evaluator;
    return evaluator.evaluate(board);
}
} // namespace forge
