// Search module: mate-distance scores and their transposition-table encoding.
// Compiled as part of src/search.cpp (included exactly once).

namespace forge {
namespace {

// Mate scores, and tablebase scores while tables are loaded (the band just
// below the mate scores, forge/syzygy.hpp), are stored as the distance from
// the storing node; everything else unchanged. Without tables the TB band
// holds ordinary scores and is stored unchanged, as in AL1 s198.
[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= syzygy::TbWinInMaxPly) return score >= MateInMaxPly || syzygy::tb_scores ? score + ply : score;
    if (score <= -syzygy::TbWinInMaxPly) return score <= -MateInMaxPly || syzygy::tb_scores ? score - ply : score;
    return score;
}

[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= syzygy::TbWinInMaxPly) return score >= MateInMaxPly || syzygy::tb_scores ? score - ply : score;
    if (score <= -syzygy::TbWinInMaxPly) return score <= -MateInMaxPly || syzygy::tb_scores ? score + ply : score;
    return score;
}

[[nodiscard]] int mated_in(int ply) { return -MateValue + ply; }
[[nodiscard]] int mate_in(int ply) { return MateValue - ply; }

} // namespace
} // namespace forge
