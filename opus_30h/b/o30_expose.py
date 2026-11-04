#!/usr/bin/env python3
"""o30_expose.py <lock copy dir> - Opus 30-h job Item B: expose 23 more search constants of the lock (git d4f4312) as
tune:: options (advertised by `uci` under -DFORGE_EXPOSE_TUNABLES, i.e. the kit's -Expose), each default = the literal it
replaces, so the defaults give the lock's arithmetic exactly (checked by bench pins). Own code; the literal sites are
the ones R9 (opus-r9-spsa:opus_r9/tools/patch_r9_search.py) proved identical, here without the R9Tune switch.
Every anchor must occur exactly once (assert); LF files only; prints the number of edits.
"""
import sys
from pathlib import Path

NEW = [  # name, default, min, max
    ("NmpEvalDepthMargin", 24, 0, 100), ("NmpEvalBase", 180, -200, 600), ("NullMoveEvalMax", 3, 0, 10),
    ("NullMoveVerifyDepth", 14, 1, 64), ("ProbcutImproving", 50, 0, 300), ("ProbcutReduction", 4, 1, 10),
    ("SingularTtDepth", 3, 1, 8), ("SingularDoubleMargin", 24, 0, 200), ("SingularDoubleLimit", 6, 0, 20),
    ("LmrTtPv", 1024, 0, 4096), ("LmrNotImproving", 1024, 0, 4096), ("LmrCutNode", 2048, 0, 6144),
    ("LmrTtCapture", 1024, 0, 4096), ("LmrGivesCheck", 1024, 0, 4096), ("LmrInCheck", 1024, 0, 4096),
    ("LmrCutoffCount", 1024, 0, 4096), ("HistoryMalusPercent", 100, 0, 300), ("HistoryDepthBonusMargin", 100, 0, 1000),
    ("AspirationMinDepth", 4, 1, 20), ("AspirationGrowPercent", 50, 10, 300), ("AspirationGrowAdd", 4, 0, 100),
    ("QuietCheckBonus", 12000, 0, 40000),
]

EDITS = [
    # declarations after the last lock tunable
    ("int FailLowContinuationBonus = 0;\n",
     "int FailLowContinuationBonus = 0;\n" + "".join(f"int {n} = {d};\n" for n, d, _, _ in NEW)),
    # table entries after the last lock entry
    ("{\"FailLowContinuationBonus\", &FailLowContinuationBonus, 0, 300},\n",
     "{\"FailLowContinuationBonus\", &FailLowContinuationBonus, 0, 300},\n" +
     "".join(f"        {{\"{n}\", &{n}, {lo}, {hi}}},\n" for n, _, lo, hi in NEW)),
    # move ordering: quiet direct-check bonus (two places)
    ("            if (direct_check(move)) score += 12000;", "            if (direct_check(move)) score += tune::QuietCheckBonus;"),
    ("                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);",
     "                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? tune::QuietCheckBonus : 0);"),
    # history malus (quiet and capture)
    ("""    const Piece piece = board.moved_piece(move);
    apply_history((*main_history_)[static_cast<std::size_t>(us)][move.from][move.to], bonus);
    update_continuation(ss, piece, move.to, bonus);
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -bonus);
    }""", """    const Piece piece = board.moved_piece(move);
    apply_history((*main_history_)[static_cast<std::size_t>(us)][move.from][move.to], bonus);
    update_continuation(ss, piece, move.to, bonus);
    const int malus = bonus * tune::HistoryMalusPercent / 100;
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -malus);
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -malus);
    }"""),
    ("""        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    for (int i = 0; i < capture_count; ++i) {""", """        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    const int malus = bonus * tune::HistoryMalusPercent / 100;
    for (int i = 0; i < capture_count; ++i) {"""),
    ("        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -bonus);",
     "        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -malus);"),
    # null move
    ("ss->static_eval >= beta - 24 * depth + 180 &&", "ss->static_eval >= beta - tune::NmpEvalDepthMargin * depth + tune::NmpEvalBase &&"),
    ("std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);", "std::min((eval - beta) / tune::NullMoveEvalDivisor, tune::NullMoveEvalMax);"),
    ("                if (depth < 14) {", "                if (depth < tune::NullMoveVerifyDepth) {"),
    # ProbCut
    ("const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;",
     "const int probcut_beta = beta + tune::ProbcutMargin - tune::ProbcutImproving * improving;"),
    ("value = -search(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);",
     "value = -search(board, ss + 1, depth - tune::ProbcutReduction, -probcut_beta, -probcut_beta + 1, !cut_node);"),
    # singular extension
    ("            tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {",
     "            tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - tune::SingularTtDepth) {"),
    ("if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {",
     "if (!pv_node && singular_score < singular_beta - tune::SingularDoubleMargin &&\n"
     "                    inherited_double_extensions <= tune::SingularDoubleLimit) {"),
    # LMR adjustments in 1/1024 ply (defaults are multiples of 1024: the sum divides exactly, as before)
    ("""            int r = reduction(quiet, depth, move_count);
            if (ss->tt_pv) r -= 1;
            if (!improving) r += 1;
            if (cut_node) r += 2;
            if (tt_capture && quiet) r += 1;
            if (gives_check) r -= 1;
            if (in_check) r -= 1;
            if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;""",
     """            int r1024 = 1024 * reduction(quiet, depth, move_count);
            if (ss->tt_pv) r1024 -= tune::LmrTtPv;
            if (!improving) r1024 += tune::LmrNotImproving;
            if (cut_node) r1024 += tune::LmrCutNode;
            if (tt_capture && quiet) r1024 += tune::LmrTtCapture;
            if (gives_check) r1024 -= tune::LmrGivesCheck;
            if (in_check) r1024 -= tune::LmrInCheck;
            if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r1024 += tune::LmrCutoffCount;
            int r = r1024 / 1024;"""),
    # history depth bonus margin
    ("update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);",
     "update_quiet_stats(board, ss, best_move, depth + (best_score > beta + tune::HistoryDepthBonusMargin), quiets_tried.data(), quiet_count);"),
    # aspiration windows
    ("""        if (depth >= 4) {
            alpha = std::max(score - delta, -Infinite);""", """        if (depth >= tune::AspirationMinDepth) {
            alpha = std::max(score - delta, -Infinite);"""),
    ("            delta += delta / 2 + 4;", "            delta += delta * tune::AspirationGrowPercent / 100 + tune::AspirationGrowAdd;"),
]


def main():
    root = Path(sys.argv[1])
    p = root / "src" / "search.cpp"
    s = p.read_bytes().decode("utf-8")
    if "\r" in s:
        raise SystemExit("CRLF search.cpp: use a fresh LF lock copy")
    for old, new in EDITS:
        n = s.count(old)
        assert n == 1, (n, old[:100])
        s = s.replace(old, new)
    p.write_bytes(s.encode("utf-8"))
    print(f"search.cpp: {len(EDITS)} edits, {len(NEW)} new tunables: " + ", ".join(n for n, *_ in NEW))


if __name__ == "__main__":
    main()
