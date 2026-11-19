#!/usr/bin/env python3
# kimi5 job 35: build the census-options tree from the r15d tree by exact replacements.
import shutil, subprocess, sys, os

SRC = "/tmp/j35/r15d"
DST = "/tmp/j35/patched"
if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("build", "*.log"))

search = open(f"{DST}/src/search.cpp").read()
hpp = open(f"{DST}/include/forge/search.hpp").read()

DECLS = """int LmrCutoffThreshold = 3;
// job 35 census options (kimi5): defaults are today's hand-set numbers.
int LmrDeeperBase = 40;
int LmrDeeperDepthMul = 2;
int LmrShallowerBase = 0;
int LmrShallowerDepthMul = 1;
int DoubleExtMargin = 24;
int DoubleExtLimit = 6;
int LmrTtPv = 1;
int LmrNotImproving = 1;
int LmrCutNode = 2;
int LmrTtCapture = 1;
int LmrGiveCheck = 1;
int LmrInCheck = 1;
int LmrCutoffAdd = 1;
int TtNear50Clock = 90;
int ImprovingLookback = 2;
int ImprovingLookbackFallback = 4;
int RfpWorseningDrop = 2;
int RfpWorseningDiv = 3;
int NullGateSlope = 24;
int NullGateOffset = 180;
int NullEvalReductionCap = 3;
int NullVerifyDepth = 14;
int ProbcutImprovingDiscount = 50;
int ProbcutTtDepthMargin = 3;
int ProbcutSearchReduction = 4;
int TtPruneIirOffset = 2;
int FutilityImprovingDiv = 2;
int HistPruneWeakNum = 3;
int SingularTtDepthMargin = 3;
int SingularDepthDiv = 2;
int DoubleExtPlies = 2;
int LmrMinDepth = 2;
int LmrNoisyMoveCount = 4;
int LmrHistoryClamp = 2;
int LmrQuietBoostDiv = 2;
int HistBonusBetaMargin = 100;
int PvQuietBonusDiv = 4;
int CuckooRepMinClock = 3;
int AspStartDepth = 4;
int AspDeltaGrowDiv = 2;"""

TABLE_ROWS = """        {"LmrCutoffThreshold", &LmrCutoffThreshold, 0, 20},
        {"LmrDeeperBase", &LmrDeeperBase, 0, 100000},    {"LmrDeeperDepthMul", &LmrDeeperDepthMul, 0, 64},
        {"LmrShallowerBase", &LmrShallowerBase, -100000, 400}, {"LmrShallowerDepthMul", &LmrShallowerDepthMul, 0, 64},
        {"DoubleExtMargin", &DoubleExtMargin, 0, 400},   {"DoubleExtLimit", &DoubleExtLimit, -1, 64},
        {"LmrTtPv", &LmrTtPv, 0, 4},                     {"LmrNotImproving", &LmrNotImproving, 0, 4},
        {"LmrCutNode", &LmrCutNode, 0, 4},               {"LmrTtCapture", &LmrTtCapture, 0, 4},
        {"LmrGiveCheck", &LmrGiveCheck, 0, 4},           {"LmrInCheck", &LmrInCheck, 0, 4},
        {"LmrCutoffAdd", &LmrCutoffAdd, 0, 4},
        {"TtNear50Clock", &TtNear50Clock, 0, 100},       {"ImprovingLookback", &ImprovingLookback, 2, 8},
        {"ImprovingLookbackFallback", &ImprovingLookbackFallback, 2, 8},
        {"RfpWorseningDrop", &RfpWorseningDrop, 0, 100}, {"RfpWorseningDiv", &RfpWorseningDiv, 1, 10},
        {"NullGateSlope", &NullGateSlope, 0, 100},       {"NullGateOffset", &NullGateOffset, 0, 400},
        {"NullEvalReductionCap", &NullEvalReductionCap, 0, 10}, {"NullVerifyDepth", &NullVerifyDepth, 2, 30},
        {"ProbcutImprovingDiscount", &ProbcutImprovingDiscount, 0, 200},
        {"ProbcutTtDepthMargin", &ProbcutTtDepthMargin, 0, 10}, {"ProbcutSearchReduction", &ProbcutSearchReduction, 1, 10},
        {"TtPruneIirOffset", &TtPruneIirOffset, 0, 10},  {"FutilityImprovingDiv", &FutilityImprovingDiv, 1, 10},
        {"HistPruneWeakNum", &HistPruneWeakNum, 0, 4},   {"SingularTtDepthMargin", &SingularTtDepthMargin, 0, 10},
        {"SingularDepthDiv", &SingularDepthDiv, 1, 8},   {"DoubleExtPlies", &DoubleExtPlies, 1, 4},
        {"LmrMinDepth", &LmrMinDepth, 1, 8},             {"LmrNoisyMoveCount", &LmrNoisyMoveCount, 1, 16},
        {"LmrHistoryClamp", &LmrHistoryClamp, 0, 8},     {"LmrQuietBoostDiv", &LmrQuietBoostDiv, 1, 8},
        {"HistBonusBetaMargin", &HistBonusBetaMargin, 0, 400}, {"PvQuietBonusDiv", &PvQuietBonusDiv, 1, 16},
        {"CuckooRepMinClock", &CuckooRepMinClock, 0, 100}, {"AspStartDepth", &AspStartDepth, 1, 16},
        {"AspDeltaGrowDiv", &AspDeltaGrowDiv, 1, 8},"""

EXTERN_ANCHOR = "extern int LmrCutoffThreshold;    // child cutoff count above which late moves are reduced more (0 = off)"
EXTERNS = EXTERN_ANCHOR + """
extern int LmrDeeperBase;
extern int LmrDeeperDepthMul;
extern int LmrShallowerBase;
extern int LmrShallowerDepthMul;
extern int DoubleExtMargin;
extern int DoubleExtLimit;
extern int LmrTtPv;
extern int LmrNotImproving;
extern int LmrCutNode;
extern int LmrTtCapture;
extern int LmrGiveCheck;
extern int LmrInCheck;
extern int LmrCutoffAdd;
extern int TtNear50Clock;
extern int ImprovingLookback;
extern int ImprovingLookbackFallback;
extern int RfpWorseningDrop;
extern int RfpWorseningDiv;
extern int NullGateSlope;
extern int NullGateOffset;
extern int NullEvalReductionCap;
extern int NullVerifyDepth;
extern int ProbcutImprovingDiscount;
extern int ProbcutTtDepthMargin;
extern int ProbcutSearchReduction;
extern int TtPruneIirOffset;
extern int FutilityImprovingDiv;
extern int HistPruneWeakNum;
extern int SingularTtDepthMargin;
extern int SingularDepthDiv;
extern int DoubleExtPlies;
extern int LmrMinDepth;
extern int LmrNoisyMoveCount;
extern int LmrHistoryClamp;
extern int LmrQuietBoostDiv;
extern int HistBonusBetaMargin;
extern int PvQuietBonusDiv;
extern int CuckooRepMinClock;
extern int AspStartDepth;
extern int AspDeltaGrowDiv;"""

REPS = [
    ("int LmrCutoffThreshold = 3;", DECLS, 1),
    ('        {"LmrCutoffThreshold", &LmrCutoffThreshold, 0, 20},', TABLE_ROWS, 1),
    ("const bool near50 = board.halfmove_clock() >= 90;",
     "const bool near50 = board.halfmove_clock() >= tune::TtNear50Clock;", 2),
    ("        board.halfmove_clock() < 90 &&",
     "        board.halfmove_clock() < tune::TtNear50Clock &&", 1),
    ("        if ((ss - 2)->static_eval != ValueNone) improving = ss->static_eval > (ss - 2)->static_eval;",
     "        if ((ss - tune::ImprovingLookback)->static_eval != ValueNone) improving = ss->static_eval > (ss - tune::ImprovingLookback)->static_eval;", 1),
    ("        else if ((ss - 4)->static_eval != ValueNone) improving = ss->static_eval > (ss - 4)->static_eval;",
     "        else if ((ss - tune::ImprovingLookbackFallback)->static_eval != ValueNone) improving = ss->static_eval > (ss - tune::ImprovingLookbackFallback)->static_eval;", 1),
    ("ss->static_eval + (ss - 1)->static_eval > 2",
     "ss->static_eval + (ss - 1)->static_eval > tune::RfpWorseningDrop", 1),
    ("? tune::RfpMargin / 3 : 0;", "? tune::RfpMargin / tune::RfpWorseningDiv : 0;", 1),
    ("ss->static_eval >= beta - 24 * depth + 180 &&",
     "ss->static_eval >= beta - tune::NullGateSlope * depth + tune::NullGateOffset &&", 1),
    ("std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);",
     "std::min((eval - beta) / tune::NullMoveEvalDivisor, tune::NullEvalReductionCap);", 1),
    ("depth < 14 && tune::NullThreatVerify && cheaper_enemy_attacks_dearer(board);",
     "depth < tune::NullVerifyDepth && tune::NullThreatVerify && cheaper_enemy_attacks_dearer(board);", 1),
    ("if (depth < 14 && !threat_gate) {", "if (depth < tune::NullVerifyDepth && !threat_gate) {", 1),
    ("const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;",
     "const int probcut_beta = beta + tune::ProbcutMargin - tune::ProbcutImprovingDiscount * improving;", 1),
    ("!(tt_hit && tt_depth >= depth - 3 && tt_score != ValueNone && tt_score < probcut_beta)) {",
     "!(tt_hit && tt_depth >= depth - tune::ProbcutTtDepthMargin && tt_score != ValueNone && tt_score < probcut_beta)) {", 1),
    ("value = -search_child(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);",
     "value = -search_child(board, ss + 1, depth - tune::ProbcutSearchReduction, -probcut_beta, -probcut_beta + 1, !cut_node);", 1),
    (", move, depth - 3, BoundLower, ss->tt_pv, board.halfmove_clock());",
     ", move, depth - tune::ProbcutTtDepthMargin, BoundLower, ss->tt_pv, board.halfmove_clock());", 2),
    ("depth >= tune::IirDepth + 2 && cut_node &&",
     "depth >= tune::IirDepth + tune::TtPruneIirOffset && cut_node &&", 1),
    ("? tune::FutilityBase / 2 : 0;", "? tune::FutilityBase / tune::FutilityImprovingDiv : 0;", 1),
    ("? -tune::HistoryPruneMultiplier * depth * 3 / 4",
     "? -tune::HistoryPruneMultiplier * depth * tune::HistPruneWeakNum / 4", 1),
    ("!is_mate_score(tt_score) && tt_depth >= depth - 3) {",
     "!is_mate_score(tt_score) && tt_depth >= depth - tune::SingularTtDepthMargin) {", 1),
    ("const int singular_depth = std::max(1, (depth - 1) / 2);",
     "const int singular_depth = std::max(1, (depth - 1) / tune::SingularDepthDiv);", 1),
    ("if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {",
     "if (!pv_node && singular_score < singular_beta - tune::DoubleExtMargin && inherited_double_extensions <= tune::DoubleExtLimit) {", 1),
    ("                    extension = 2;", "                    extension = tune::DoubleExtPlies;", 1),
    ("ss->double_extensions = inherited_double_extensions + (extension == 2);",
     "ss->double_extensions = inherited_double_extensions + (extension == tune::DoubleExtPlies);", 1),
    ("board.halfmove_clock() + new_depth < 100 && depth >= 2 &&",
     "board.halfmove_clock() + new_depth < 100 && depth >= tune::LmrMinDepth &&", 1),
    ("(quiet || !ss->tt_pv || move_count > 4)) {",
     "(quiet || !ss->tt_pv || move_count > tune::LmrNoisyMoveCount)) {", 1),
    ("            if (ss->tt_pv) r -= 1;", "            if (ss->tt_pv) r -= tune::LmrTtPv;", 1),
    ("            if (!improving) r += 1;", "            if (!improving) r += tune::LmrNotImproving;", 1),
    ("            if (cut_node) r += 2;", "            if (cut_node) r += tune::LmrCutNode;", 1),
    ("            if (tt_capture && quiet) r += 1;", "            if (tt_capture && quiet) r += tune::LmrTtCapture;", 1),
    ("            if (gives_check) r -= 1;", "            if (gives_check) r -= tune::LmrGiveCheck;", 1),
    ("            if (in_check) r -= 1;", "            if (in_check) r -= tune::LmrInCheck;", 1),
    ("(ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;",
     "(ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += tune::LmrCutoffAdd;", 1),
    ("r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);",
     "r -= std::clamp(history / tune::LmrHistoryDivisor, -tune::LmrHistoryClamp, tune::LmrHistoryClamp);", 1),
    ("const bool do_deeper = score > best_score + 40 + 2 * new_depth;",
     "const bool do_deeper = score > best_score + tune::LmrDeeperBase + tune::LmrDeeperDepthMul * new_depth;", 1),
    ("const bool do_shallower = score < best_score + new_depth;",
     "const bool do_shallower = score < best_score + tune::LmrShallowerBase + tune::LmrShallowerDepthMul * new_depth;", 1),
    ("update_continuation(ss, moved, move.to, history_bonus(depth) / 2);",
     "update_continuation(ss, moved, move.to, history_bonus(depth) / tune::LmrQuietBoostDiv);", 1),
    ("depth + (best_score > beta + 100)", "depth + (best_score > beta + tune::HistBonusBetaMargin)", 1),
    ("history_bonus(depth) / 4", "history_bonus(depth) / tune::PvQuietBonusDiv", 4),
    ("{ return board.halfmove_clock() >= 3; }", "{ return board.halfmove_clock() >= tune::CuckooRepMinClock; }", 1),
    ("const bool narrow = depth >= 4 && !(tune::AspArmLate && reopen_full_window);",
     "const bool narrow = depth >= tune::AspStartDepth && !(tune::AspArmLate && reopen_full_window);", 1),
    ("            delta += delta / 2 + 4;", "            delta += delta / tune::AspDeltaGrowDiv + 4;", 1),
]

for old, new, want in REPS:
    n = search.count(old)
    if n != want:
        print(f"FAIL count {n} != {want} for: {old[:70]}")
        sys.exit(1)
    search = search.replace(old, new)

if hpp.count(EXTERN_ANCHOR) != 1:
    print("FAIL hpp anchor")
    sys.exit(1)
hpp = hpp.replace(EXTERN_ANCHOR, EXTERNS)

open(f"{DST}/src/search.cpp", "w").write(search)
open(f"{DST}/include/forge/search.hpp", "w").write(hpp)
print("all replacements OK")
