"""R9: turn the remaining search literals into tune:: parameters (lock values) and add the R9Tune switch.
Every replacement is anchored on unique text (assert count == 1). Run from the opus-r9-spsa worktree root."""
from pathlib import Path

p = Path("src/search.cpp")
raw = p.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")
edits = []

# 1. new parameter definitions (lock values of the former literals)
edits.append(("""int FailLowContinuationBonus = 0;
""", """int FailLowContinuationBonus = 0;
// R9: former literals (lock values).
int NmpEvalDepthMargin = 24;
int NmpEvalBase = 180;
int NullMoveEvalMax = 3;
int NullMoveVerifyDepth = 14;
int ProbcutImproving = 50;
int ProbcutReduction = 4;
int SingularTtDepth = 3;
int SingularDoubleMargin = 24;
int SingularDoubleLimit = 6;
int LmrTtPv = 1024;
int LmrNotImproving = 1024;
int LmrCutNode = 2048;
int LmrTtCapture = 1024;
int LmrGivesCheck = 1024;
int LmrInCheck = 1024;
int LmrCutoffCount = 1024;
int HistoryBonusOffset = 32;
int HistoryMalusPercent = 100;
int HistoryDepthBonusMargin = 100;
int AspirationMinDepth = 4;
int AspirationGrowPercent = 50;
int AspirationGrowAdd = 4;
int QuietCheckBonus = 12000;
"""))

# 2. table rows (ranges wide enough for SPSA, narrow enough to stay sane)
edits.append(("""        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},
    };""", """        {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},
        // R9: former literals
        {"NmpEvalDepthMargin", &NmpEvalDepthMargin, 0, 100},     {"NmpEvalBase", &NmpEvalBase, -200, 600},
        {"NullMoveEvalMax", &NullMoveEvalMax, 0, 10},            {"NullMoveVerifyDepth", &NullMoveVerifyDepth, 6, 64},
        {"ProbcutImproving", &ProbcutImproving, 0, 200},         {"ProbcutReduction", &ProbcutReduction, 2, 8},
        {"SingularTtDepth", &SingularTtDepth, 1, 8},             {"SingularDoubleMargin", &SingularDoubleMargin, 0, 200},
        {"SingularDoubleLimit", &SingularDoubleLimit, 0, 20},
        {"LmrTtPv", &LmrTtPv, 0, 4096},                          {"LmrNotImproving", &LmrNotImproving, 0, 4096},
        {"LmrCutNode", &LmrCutNode, 0, 6144},                    {"LmrTtCapture", &LmrTtCapture, 0, 4096},
        {"LmrGivesCheck", &LmrGivesCheck, 0, 4096},              {"LmrInCheck", &LmrInCheck, 0, 4096},
        {"LmrCutoffCount", &LmrCutoffCount, 0, 4096},
        {"HistoryBonusOffset", &HistoryBonusOffset, -200, 300},  {"HistoryMalusPercent", &HistoryMalusPercent, 0, 300},
        {"HistoryDepthBonusMargin", &HistoryDepthBonusMargin, 0, 1000},
        {"AspirationMinDepth", &AspirationMinDepth, 1, 16},      {"AspirationGrowPercent", &AspirationGrowPercent, 0, 300},
        {"AspirationGrowAdd", &AspirationGrowAdd, 0, 100},       {"QuietCheckBonus", &QuietCheckBonus, 0, 40000},
    };"""))

# 3. history bonus offset
edits.append(("""tune::HistoryBonusLinear * depth - 32);""", """tune::HistoryBonusLinear * depth - tune::HistoryBonusOffset);"""))

# 4. R9 switch (after tune::refresh)
edits.append(("""void tune::refresh() { Reductions.refresh(); }
""", """void tune::refresh() { Reductions.refresh(); }

// R9Tune: the lock's values are captured before anything can change them (the variables are constant-initialised);
// R9Values holds what the tunable options say and is live only while R9Tune is on.
namespace {
std::vector<int> capture_lock_defaults() {
    std::vector<int> values;
    for (const tune::Parameter& parameter : tune::parameters()) values.push_back(*parameter.value);
    return values;
}
const std::vector<int> LockDefaults = capture_lock_defaults();
std::vector<int> R9Values = LockDefaults;
bool R9Enabled = false;
} // namespace

bool tune::r9_enabled() { return R9Enabled; }

void tune::r9_set_enabled(bool on) {
    R9Enabled = on;
    const std::vector<Parameter>& table = parameters();
    for (std::size_t i = 0; i < table.size(); ++i) *table[i].value = on ? R9Values[i] : LockDefaults[i];
    refresh();
}

bool tune::r9_set(std::string_view name, int value) {
    const std::vector<Parameter>& table = parameters();
    for (std::size_t i = 0; i < table.size(); ++i) {
        if (name != table[i].name) continue;
        R9Values[i] = std::clamp(value, table[i].minimum, table[i].maximum);
        if (R9Enabled) {
            *table[i].value = R9Values[i];
            refresh();
        }
        return true;
    }
    return false;
}

int tune::lock_default(std::size_t index) { return LockDefaults.at(index); }
"""))

# 5. move ordering: quiet direct-check bonus (two places)
edits.append(("""            if (direct_check(move)) score += 12000;""", """            if (direct_check(move)) score += tune::QuietCheckBonus;"""))
edits.append(("""                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);""",
              """                score = searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? tune::QuietCheckBonus : 0);"""))

# 6. history malus (quiet and capture)
edits.append(("""    const Piece piece = board.moved_piece(move);
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
    }"""))
edits.append(("""        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    for (int i = 0; i < capture_count; ++i) {""", """        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][best.to][static_cast<std::size_t>(captured)], bonus);
    }
    const int malus = bonus * tune::HistoryMalusPercent / 100;
    for (int i = 0; i < capture_count; ++i) {"""))
edits.append(("""        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -bonus);""",
              """        apply_history((*capture_history_)[static_cast<std::size_t>(piece)][capture.to][static_cast<std::size_t>(captured)], -malus);"""))

# 7. null move
edits.append(("""ss->static_eval >= beta - 24 * depth + 180 &&""",
              """ss->static_eval >= beta - tune::NmpEvalDepthMargin * depth + tune::NmpEvalBase &&"""))
edits.append(("""std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);""",
              """std::min((eval - beta) / tune::NullMoveEvalDivisor, tune::NullMoveEvalMax);"""))
edits.append(("""                if (depth < 14) {""", """                if (depth < tune::NullMoveVerifyDepth) {"""))

# 8. ProbCut
edits.append(("""const int probcut_beta = beta + tune::ProbcutMargin - 50 * improving;""",
              """const int probcut_beta = beta + tune::ProbcutMargin - tune::ProbcutImproving * improving;"""))
edits.append(("""value = -search(board, ss + 1, depth - 4, -probcut_beta, -probcut_beta + 1, !cut_node);""",
              """value = -search(board, ss + 1, depth - tune::ProbcutReduction, -probcut_beta, -probcut_beta + 1, !cut_node);"""))

# 9. singular extension
edits.append(("""            tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {""",
              """            tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - tune::SingularTtDepth) {"""))
edits.append(("""if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) {""",
              """if (!pv_node && singular_score < singular_beta - tune::SingularDoubleMargin &&
                    inherited_double_extensions <= tune::SingularDoubleLimit) {"""))

# 10. LMR adjustments in 1/1024 ply (multiples of 1024 by default: the sum divides exactly, as before)
edits.append(("""            int r = reduction(quiet, depth, move_count);
            if (ss->tt_pv) r -= 1;
            if (!improving) r += 1;
            if (cut_node) r += 2;
            if (tt_capture && quiet) r += 1;
            if (gives_check) r -= 1;
            if (in_check) r -= 1;
            if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);""",
              """            int r1024 = 1024 * reduction(quiet, depth, move_count);
            if (ss->tt_pv) r1024 -= tune::LmrTtPv;
            if (!improving) r1024 += tune::LmrNotImproving;
            if (cut_node) r1024 += tune::LmrCutNode;
            if (tt_capture && quiet) r1024 += tune::LmrTtCapture;
            if (gives_check) r1024 -= tune::LmrGivesCheck;
            if (in_check) r1024 -= tune::LmrInCheck;
            if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r1024 += tune::LmrCutoffCount;
            int r = r1024 / 1024;
            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);"""))

# 11. history depth bonus margin
edits.append(("""update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);""",
              """update_quiet_stats(board, ss, best_move, depth + (best_score > beta + tune::HistoryDepthBonusMargin), quiets_tried.data(), quiet_count);"""))

# 12. aspiration windows
edits.append(("""        if (depth >= 4) {
            alpha = std::max(score - delta, -Infinite);""", """        if (depth >= tune::AspirationMinDepth) {
            alpha = std::max(score - delta, -Infinite);"""))
edits.append(("""            delta += delta / 2 + 4;""", """            delta += delta * tune::AspirationGrowPercent / 100 + tune::AspirationGrowAdd;"""))

for old, new in edits:
    n = s.count(old)
    assert n == 1, (n, old[:90])
    s = s.replace(old, new)
p.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print(f"search.cpp: {len(edits)} edits applied ({'CRLF' if crlf else 'LF'} kept)")
