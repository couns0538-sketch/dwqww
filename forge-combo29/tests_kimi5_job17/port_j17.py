#!/usr/bin/env python3
"""kimi5 job 17: hand-ports of the rejected hunks onto the PC tree (6b98f217 + pc_r15).
Every replacement is an exact string of the PC-original src/search.cpp; each must occur
exactly once (asserted). Trees:
  pt_FailHighBlend, pt_RfpGuards, pt_MalusE : standalone ports (patch(1) applied what it could)
  pcs                                        : the series tree (all five ports)
The patch(1)-applied hunks in pt_LmrFine and pt_AlphaQs were verified by reading; no hand edits.
"""
import re, shutil, subprocess, sys

PC = "/tmp/pc"
JOBS = "/agent/repos/dwqww/forge-combo29"

def read(p):
    with open(p) as f: return f.read()

def write(p, s):
    with open(p, "w") as f: f.write(s)

def rep(text, old, new, tag):
    n = text.count(old)
    assert n == 1, f"{tag}: anchor occurs {n} times (need exactly 1)\n---anchor---\n{old}"
    return text.replace(old, new, 1)

# ---- exact PC-original anchors -------------------------------------------------
DECL_ANCHOR = "int FailLowContinuationBonus = 0;\n"
TABLE_ANCHOR = ('        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},'
                '  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},\n')

FHB_DECL = DECL_ANCHOR + "int FailHighBlend = 0;\n"
FHB_TABLE = TABLE_ANCHOR + '        {"FailHighBlend", &FailHighBlend, 0, 7},\n'

RFP_DECL = ("int RfpNoTtPv = 0;\nint RfpTtGuard = 0;\nint RfpCorrMul = 0;\n")
RFP_TABLE = ('        {"RfpNoTtPv", &RfpNoTtPv, 0, 1},         {"RfpTtGuard", &RfpTtGuard, 0, 1},\n'
             '        {"RfpCorrMul", &RfpCorrMul, 0, 64},\n')

# PC RFP site (r15 added rfp_worsening; the return line differs per tree: eval or the FailHighBlend form)
RFP_COND_OLD = ("""        const int rfp_worsening = tt_prune_v2_ && (ss - 1)->static_eval != ValueNone &&
                                          ss->static_eval + (ss - 1)->static_eval > 2
                                      ? tune::RfpMargin / 3 : 0;
        if (!bare_king_mode && depth <= tune::RfpDepth &&
            eval - (tune::RfpMargin * depth - tune::RfpImproving * improving - rfp_worsening) >= beta &&
""")
RFP_COND_NEW = ("""        const int rfp_worsening = tt_prune_v2_ && (ss - 1)->static_eval != ValueNone &&
                                          ss->static_eval + (ss - 1)->static_eval > 2
                                      ? tune::RfpMargin / 3 : 0;
        const bool rfp_ok = !(tune::RfpNoTtPv && ss->tt_pv) && !(tune::RfpTtGuard && !tt_move.is_none() && !tt_capture);
        const int rfp_corr = tune::RfpCorrMul ? tune::RfpCorrMul * std::abs(ss->static_eval - ss->raw_eval) / 16 : 0;
        if (rfp_ok && !bare_king_mode && depth <= tune::RfpDepth &&
            eval - (tune::RfpMargin * depth - tune::RfpImproving * improving - rfp_worsening + rfp_corr) >= beta &&
""")

# FailHighBlend hunk 7 (correction guard) adapted to the PC call's extra `ss` argument
CORR_OLD = ("""    if (!in_check && excluded.is_none() && !is_mate_score(best_score) &&
        (best_move.is_none() || !best_move.is_capture()) &&
        !(bound == BoundLower && best_score <= ss->static_eval) &&
        !(bound == BoundUpper && best_score >= ss->static_eval)) {
        update_correction(board, depth, best_score, ss->static_eval, ss);
    }
""")
CORR_NEW = ("""    if (!in_check && excluded.is_none() && !is_mate_score(raw_best) &&
        (best_move.is_none() || !best_move.is_capture()) &&
        !(bound == BoundLower && raw_best <= ss->static_eval) &&
        !(bound == BoundUpper && raw_best >= ss->static_eval)) {
        update_correction(board, depth, raw_best, ss->static_eval, ss);
    }
""")

# MalusE hunk 3 inside the PC's update_quiet_stats (pawn history = PC-only table, stays -bonus)
UQS_OLD = ("""    update_continuation(ss, piece, move.to, bonus);
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);
        update_threat_quiet(board, quiet, -bonus);
#if FORGE_PAWN_HISTORY
        update_pawn_history(board, board.moved_piece(quiet), quiet, -bonus);
#endif
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -bonus);
    }
""")
UQS_NEW = ("""    update_continuation(ss, piece, move.to, bonus);
    int not_move_count = 0;
    for (int i = 0; i < quiet_count; ++i) {
        if (quiets[i] != move) ++not_move_count;
    }
    const int malus =
        bonus * std::max(0, tune::QuietMalusBase + tune::QuietMalusPerMove * std::min(not_move_count, 16)) / 64;
    for (int i = 0; i < quiet_count; ++i) {
        const Move quiet = quiets[i];
        if (quiet == move) continue;
        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -malus);
        update_threat_quiet(board, quiet, -malus);
#if FORGE_PAWN_HISTORY
        update_pawn_history(board, board.moved_piece(quiet), quiet, -bonus);
#endif
        update_continuation(ss, board.moved_piece(quiet), quiet.to, -malus);
    }
""")

# MalusE hunk 5 (PC calls search_child, not search)
RES_OLD = ("""                if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {
                    score = -search_child(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
                }
                full_depth_needed = false;
            }
            if (!aborted_ && quiet && score > alpha) {
                // A late quiet move that beat expectations deserves a history boost.
                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
            }
""")
RES_NEW = ("""                if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {
                    score = -search_child(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
                    researched = true;
                }
                full_depth_needed = false;
            }
            if (!aborted_ && quiet && score > alpha) {
                // A late quiet move that beat expectations deserves a history boost.
                update_continuation(ss, moved, move.to, history_bonus(depth) / 2);
            } else if (tune::ResearchMalus && !aborted_ && quiet && researched) {
                update_continuation(ss, moved, move.to, -(history_bonus(depth) / 2));
            }
""")

# ---- 1. standalone hand edits --------------------------------------------------
s = read("/tmp/pt_FailHighBlend/src/search.cpp")
s = rep(s, DECL_ANCHOR, FHB_DECL, "fhb decl")
s = rep(s, TABLE_ANCHOR, FHB_TABLE, "fhb table")
s = rep(s, CORR_OLD, CORR_NEW, "fhb corr")
write("/tmp/pt_FailHighBlend/src/search.cpp", s)

s = read("/tmp/pt_RfpGuards/src/search.cpp")
s = rep(s, DECL_ANCHOR, DECL_ANCHOR + RFP_DECL, "rfp decl")
s = rep(s, TABLE_ANCHOR, TABLE_ANCHOR + RFP_TABLE, "rfp table")
s = rep(s, RFP_COND_OLD, RFP_COND_NEW, "rfp cond")
write("/tmp/pt_RfpGuards/src/search.cpp", s)

s = read("/tmp/pt_MalusE/src/search.cpp")
s = rep(s, UQS_OLD, UQS_NEW, "mal uqs")
s = rep(s, RES_OLD, RES_NEW, "mal res")
write("/tmp/pt_MalusE/src/search.cpp", s)

# ---- 2. series tree: PC + all five ports ---------------------------------------
subprocess.run(["rm", "-rf", "/tmp/pcs"], check=True)
subprocess.run(["mkdir", "/tmp/pcs"], check=True)
subprocess.run(["cp", "-r", f"{PC}/src", f"{PC}/include", "/tmp/pcs/"], check=True)
# the three patches that apply fully (verified by reading): AlphaQs, LmrFine, MalusE(1,2,4)
for name in ["tests_kimi5_job15/AlphaQs.patch.txt", "tests_kimi5_job11/LmrFine.patch.txt",
             "tests_kimi5_job16/MalusE.patch.txt"]:
    r = subprocess.run(["patch", "-p2", "-i", f"{JOBS}/{name}"], cwd="/tmp/pcs",
                       capture_output=True, text=True)
    print(f"series {name}: rc={r.returncode} " + " ".join(
        l for l in (r.stdout + r.stderr).splitlines() if "FAILED" in l or "fuzz" in l))
# hand: FailHighBlend (all 7 edits), RfpGuards, MalusE hunks 3+5
s = read("/tmp/pcs/src/search.cpp")
s = rep(s, DECL_ANCHOR, DECL_ANCHOR + "int FailHighBlend = 0;\n" + RFP_DECL, "pcs decl")
s = rep(s, TABLE_ANCHOR, TABLE_ANCHOR + FHB_TABLE[len(TABLE_ANCHOR):] + RFP_TABLE, "pcs table")
s = rep(s, RFP_COND_OLD, RFP_COND_NEW, "pcs rfp cond")
s = rep(s, """            eval < MateInMaxPly) {
            return eval;
        }
""", """            eval < MateInMaxPly) {
            return (tune::FailHighBlend & 1) ? beta + (eval - beta) / 3 : eval;
        }
""", "pcs rfp return")
s = rep(s, """        best_score = eval;
        if (best_score >= beta) {
""", """        best_score = eval;
        if (best_score >= beta) {
            if ((tune::FailHighBlend & 2) && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score + beta) / 2;
""", "pcs qs1")
s = rep(s, """    if (in_check && move_count == 0) return mated_in(ply);

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
""", """    if (in_check && move_count == 0) return mated_in(ply);

    if ((tune::FailHighBlend & 2) && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score + beta) / 2;

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
""", "pcs qs2")
s = rep(s, """    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (excluded.is_none() && !(root_node && root_restricted_)) {
""", """    const int raw_best = best_score;
    if ((tune::FailHighBlend & 4) && !pv_node && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score * depth + beta) / (depth + 1);

    const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
    if (excluded.is_none() && !(root_node && root_restricted_)) {
""", "pcs main")
s = rep(s, CORR_OLD, CORR_NEW, "pcs corr")
s = rep(s, UQS_OLD, UQS_NEW, "pcs uqs")
s = rep(s, RES_OLD, RES_NEW, "pcs res")
write("/tmp/pcs/src/search.cpp", s)
print("all hand edits applied")
