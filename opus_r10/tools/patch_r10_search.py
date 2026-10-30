"""R10: wire the HalfKA (K32H3^) path into the search and UCI. Anchored replacements, CRLF-aware. Run from the root."""
from pathlib import Path


def patch(path, edits):
    p = Path(path)
    raw = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    s = raw.replace("\r\n", "\n")
    for old, new in edits:
        n = s.count(old)
        assert n == 1, (path, n, old[:90])
        s = s.replace(old, new)
    p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
    print(f"{path}: {len(edits)} edits")


patch("include/forge/search.hpp", [
    ('#include "forge/nnue.hpp"\n', '#include "forge/nnue.hpp"\n#include "forge/nnue_halfka.hpp"\n'),
    ("    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);\n",
     "    [[nodiscard]] int static_evaluate(const Board& board, SearchStack* ss);\n"
     "    [[nodiscard]] int halfka_evaluate(const Board& board, SearchStack* ss);\n"),
    ("    std::array<SearchStack, MaxPly + 8> stack_{};\n",
     "    std::array<SearchStack, MaxPly + 8> stack_{};\n"
     "    // R10: HalfKA (K32H3^) accumulators, one entry per stack_ entry (used only while EvalFileHalfKA is loaded)\n"
     "    halfka::AccumulatorStack halfka_acc_;\n"),
])

patch("src/search.cpp", [
    ("""int Worker::static_evaluate(const Board& board, SearchStack* ss) {
    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);""",
     """int Worker::static_evaluate(const Board& board, SearchStack* ss) {
    if (halfka::active()) return halfka_evaluate(board, ss);
    if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);"""),
    ("""void Worker::record_move(SearchStack* ss, const Board& board, const Move& move) {
    // Called before make_move: the child's accumulator becomes stale and the
    // piece changes are remembered for the lazy update.
    if (!nnue::enabled || !nnue::available()) return;
    (ss + 1)->dirty = nnue::dirty_pieces(board, move);
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
}

void Worker::record_null_move(SearchStack* ss) {
    (ss + 1)->dirty.count = 0;
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
}""",
     """void Worker::record_move(SearchStack* ss, const Board& board, const Move& move) {
    // Called before make_move: the child's accumulator becomes stale and the
    // piece changes are remembered for the lazy update.
    const bool halfka_on = halfka::active();
    if (!halfka_on && (!nnue::enabled || !nnue::available())) return;
    (ss + 1)->dirty = nnue::dirty_pieces(board, move);
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
    if (halfka_on) {
        const std::size_t entry = static_cast<std::size_t>(ss + 1 - stack_.data());
        halfka_acc_.valid[White][entry] = halfka_acc_.valid[Black][entry] = false;
    }
}

void Worker::record_null_move(SearchStack* ss) {
    (ss + 1)->dirty.count = 0;
    (ss + 1)->accumulator.valid = false;
    (ss + 1)->runtime_psqt.valid = false;
    if (halfka::active()) {
        const std::size_t entry = static_cast<std::size_t>(ss + 1 - stack_.data());
        halfka_acc_.valid[White][entry] = halfka_acc_.valid[Black][entry] = false;
    }
}

// R10: HalfKA evaluation with lazy accumulators. A perspective's row is built from the nearest ancestor row on the
// current path when that ancestor had the same own-king square and material state (the same feature bucket and
// orientation): the recorded piece changes of every ply in between are applied in order. Otherwise (king move,
// mirror flip, queen/rook state change, or no valid ancestor) the row is refreshed from the board.
int Worker::halfka_evaluate(const Board& board, SearchStack* ss) {
    halfka::AccumulatorStack& acc = halfka_acc_;
    const int entry = static_cast<int>(ss - stack_.data());
    for (const Color c : {White, Black}) {
        if (acc.valid[c][entry]) continue;
        const int king = board.king_square(c);
        const int bucket = halfka::feature_bucket(board, c);
        int from = entry - 1;
        while (from >= 0 && !acc.valid[c][from]) --from;
        std::int16_t* row = acc.row(entry, c);
        if (from >= 0 && acc.king[c][from] == king && acc.bucket[c][from] == bucket) {
            halfka::apply(acc.row(from, c), row, c, king, bucket, stack_[static_cast<std::size_t>(from + 1)].dirty);
            for (int e = from + 2; e <= entry; ++e) halfka::apply(row, row, c, king, bucket, stack_[static_cast<std::size_t>(e)].dirty);
        } else {
            halfka::refresh(board, c, row);
        }
        acc.valid[c][entry] = true;
        acc.king[c][entry] = king;
        acc.bucket[c][entry] = bucket;
    }
    return std::clamp(halfka::evaluate(board, acc.row(entry, White), acc.row(entry, Black)), -MateInMaxPly + 1,
                      MateInMaxPly - 1);
}"""),
    ("""    if (nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    }
""",
     """    if (nnue::enabled && nnue::available()) {
        nnue::refresh(board, ss->accumulator);
        if (nnue::residual()) ss->runtime_psqt = Evaluator::refresh_runtime_psqt(board);
    }
    if (halfka::active()) halfka_acc_.ensure(static_cast<int>(stack_.size()));
"""),
])
