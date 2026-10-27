// Search module: mate-distance scores and their transposition-table encoding.
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {
namespace {

[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score + ply;
    if (score <= -MateInMaxPly) return score - ply;
    return score;
}

[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= MateInMaxPly) return score - ply;
    if (score <= -MateInMaxPly) return score + ply;
    return score;
}

[[nodiscard]] int mated_in(int ply) { return -MateValue + ply; }
[[nodiscard]] int mate_in(int ply) { return MateValue - ply; }

} // namespace
} // namespace forge
