#!/usr/bin/env python3
"""
Job 41 Part P7 (`build_and_verify_p7.py`):
- Hand-ports seat `028`'s `IdeaB8` as `IdeaB8b` (`IdeaB8b`, `IdeaB8b_Weight` = 1024, `IdeaB8b_Swing` = 40)
  with completely separate table (`ThreatRoleHistoryB`), cache (`role_b8b_*`), and `SearchStack` field
  (`role_b8b_eval_valid`).
- Emits three LF `diff -u` patches against `r15d + v3`:
  1. `P7_B8b_028.patch.txt` (`P7` alone)
  2. `B8_both.patch.txt` (`P6` + `P7` together: `IdeaB8` and `IdeaB8b` only)
  3. `bundle_grok7.patch.txt` (Job 39's 6-switch bundle + `P7` = 7 switches)
- Applies each patch to a brand-new copy of `r15d + v3`, builds Release binaries, and executes every
  verification required by `FABLE_TO_carbon2_41.md` `P7c`.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j41_lib import (  # noqa: E402
    ALL_SEVEN_FALSE,
    BUNDLE6_PATCH,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_SETA_L_NODES,
    EXP_SETA_L_RECORDS,
    EXP_SETA_L_SHA,
    G_EPD_PATH,
    JOB39,
    JOB41,
    O_FENS_PATH,
    P6_B8_PATCH,
    SEVEN_SWITCH_NAMES,
    SIX_OLD_SWITCHES,
    TPL_V3,
    WORK41,
    apply_patch_to_fresh_v3,
    build_release_v3,
    diff_rows,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name,
    pc20_option_lines,
    read_j39_rows,
    run_epd_depth12,
    run_fresh_bench,
    run_selfgame_set_with_options,
    sha256_file,
    utc_now,
    verify_all_off_numbers,
    verify_uci_option_check,
    write_seta_meta,
    write_v2_v3_rows,
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    cnt = text.count(old)
    if cnt != 1:
        raise RuntimeError(f"[{label}] expected 1 occurrence of anchor, found {cnt}:\n{old!r}")
    return text.replace(old, new, 1)


def inject_p7_into_tree(tree_dir: pathlib.Path) -> None:
    """
    Applies seat `028`'s `IdeaB8b` port cleanly onto a tree that is either:
    - plain `r15d + v3`,
    - `r15d + v3` + `P6_B8_078.patch.txt`, or
    - `r15d + v3` + `bundle_grok.patch.txt`.
    """
    # 1. include/forge/search.hpp
    shpp_path = tree_dir / "include/forge/search.hpp"
    shpp = shpp_path.read_text(encoding="utf-8")

    if "extern int IdeaB8_Swing;" in shpp:
        shpp = replace_once(
            shpp,
            "extern int IdeaB8_Swing;             // centipawns of eval gain that count as the threat being answered\n",
            "extern int IdeaB8_Swing;             // centipawns of eval gain that count as the threat being answered\n"
            "extern int IdeaB8b_Weight;           // seat 028 threat-role history added to a quiet, in 1/1024\n"
            "extern int IdeaB8b_Swing;            // seat 028 centipawn static-eval gain that counts threat as answered\n",
            "search.hpp spin externs after P6",
        )
    else:
        shpp = replace_once(
            shpp,
            "extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)\n",
            "extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)\n"
            "extern int IdeaB8b_Weight;           // seat 028 threat-role history added to a quiet, in 1/1024\n"
            "extern int IdeaB8b_Swing;            // seat 028 centipawn static-eval gain that counts threat as answered\n",
            "search.hpp spin externs plain",
        )

    if "extern bool IdeaB8;" in shpp:
        shpp = replace_once(
            shpp,
            "extern bool IdeaB8;                  // threat-role memory (false = off; off keeps today's search path)\n",
            "extern bool IdeaB8;                  // threat-role memory (false = off; off keeps today's search path)\n"
            "extern bool IdeaB8b;                 // seat 028 threat-role memory (false = off)\n",
            "search.hpp bool extern after P6",
        )
    else:
        shpp = replace_once(
            shpp,
            "extern bool ThreatHistory;           // second quiet history keyed by cheaper-attacker threats (false = off)\n",
            "extern bool ThreatHistory;           // second quiet history keyed by cheaper-attacker threats (false = off)\n"
            "extern bool IdeaB8b;                 // seat 028 threat-role memory (false = off)\n",
            "search.hpp bool extern plain",
        )

    b8b_hist_typedef = (
        "// [side][attacked piece type 0..6 (incl. King=6)][attacker piece type 0..6][role 0..4].\n"
        "// Seat 028 roles: 0 none, 1 attacked piece steps away, 2 another piece blocks,\n"
        "// 3 quiet attacks the attacker, 4 quiet creates a greater threat (incl. counter-check).\n"
        "using ThreatRoleHistoryB = std::array<std::array<std::array<std::array<std::int16_t, 5>, 7>, 7>, 2>;\n"
    )
    if "using ThreatRoleHistory =" in shpp:
        shpp = replace_once(
            shpp,
            "using ThreatRoleHistory = std::array<std::array<std::array<std::array<std::int16_t, 5>, 7>, 7>, 2>;\n",
            "using ThreatRoleHistory = std::array<std::array<std::array<std::array<std::int16_t, 5>, 7>, 7>, 2>;\n"
            + b8b_hist_typedef,
            "search.hpp typedef after P6",
        )
    else:
        shpp = replace_once(
            shpp,
            "using ThreatQuietHistory = std::array<std::array<std::array<std::array<std::int16_t, 64>, 64>, 4>, 2>;\n",
            "using ThreatQuietHistory = std::array<std::array<std::array<std::array<std::int16_t, 64>, 64>, 4>, 2>;\n"
            + b8b_hist_typedef,
            "search.hpp typedef plain",
        )

    b8b_ss_field = (
        "    // True only after this visit wrote a non-ValueNone static_eval. Read only when IdeaB8b is on.\n"
        "    bool role_b8b_eval_valid = false;\n"
    )
    if "    bool role_eval_ready = false;\n" in shpp:
        shpp = replace_once(
            shpp,
            "    bool role_eval_ready = false;\n",
            "    bool role_eval_ready = false;\n" + b8b_ss_field,
            "search.hpp SearchStack after P6",
        )
    else:
        shpp = replace_once(
            shpp,
            "    mutable std::uint8_t corr_valid = 0;\n",
            "    mutable std::uint8_t corr_valid = 0;\n" + b8b_ss_field,
            "search.hpp SearchStack plain",
        )

    b8b_worker_fields = (
        "    std::unique_ptr<ThreatRoleHistoryB> role_b8b_history_;\n"
    )
    if "    mutable int threat_role_victim_value_ = 0;\n" in shpp:
        shpp = replace_once(
            shpp,
            "    mutable int threat_role_victim_value_ = 0;\n",
            "    mutable int threat_role_victim_value_ = 0;\n" + b8b_worker_fields,
            "search.hpp Worker table field after P6",
        )
    else:
        shpp = replace_once(
            shpp,
            "    std::unique_ptr<ThreatQuietHistory> threat_history_;\n",
            "    std::unique_ptr<ThreatQuietHistory> threat_history_;\n" + b8b_worker_fields,
            "search.hpp Worker table field plain",
        )

    b8b_worker_methods = (
        "    struct RoleThreatB {\n"
        "        bool present = false;\n"
        "        int victim_sq = 0;\n"
        "        int attacker_sq = 0;\n"
        "        int victim_type = 0;\n"
        "        int attacker_type = 0;\n"
        "        int victim_worth = 0;\n"
        "    };\n"
        "    [[nodiscard]] const RoleThreatB& role_b8b_threat(const Board& board) const;\n"
        "    [[nodiscard]] static int threat_role_b8b_of(const Board& board, Move move, const RoleThreatB& threat);\n"
        "    [[nodiscard]] int threat_role_b8b_bonus(const Board& board, Move move) const;\n"
        "    void update_threat_role_b8b(const Board& board, Move move, int bonus);\n"
        "    void note_role_b8b_swing(const Board& board, SearchStack* ss, Move move, int depth);\n"
        "    mutable RoleThreatB role_b8b_threat_{};\n"
        "    mutable std::uint64_t role_b8b_key_ = 0;\n"
        "    mutable bool role_b8b_key_valid_ = false;\n"
    )
    if "    void ensure_role_threat(const Board& board) const;\n" in shpp:
        shpp = replace_once(
            shpp,
            "    void ensure_role_threat(const Board& board) const;\n",
            "    void ensure_role_threat(const Board& board) const;\n" + b8b_worker_methods,
            "search.hpp Worker methods after P6",
        )
    else:
        shpp = replace_once(
            shpp,
            "    void update_threat_quiet(const Board& board, Move move, int bonus);\n",
            "    void update_threat_quiet(const Board& board, Move move, int bonus);\n" + b8b_worker_methods,
            "search.hpp Worker methods plain",
        )

    shpp_path.write_text(shpp, encoding="utf-8")

    # 2. src/search.cpp
    scpp_path = tree_dir / "src/search.cpp"
    scpp = scpp_path.read_text(encoding="utf-8")

    if "int IdeaB8_Swing = 48;\n" in scpp:
        scpp = replace_once(
            scpp,
            "int IdeaB8_Swing = 48;\n",
            "int IdeaB8_Swing = 48;\nint IdeaB8b_Weight = 1024;\nint IdeaB8b_Swing = 40;\n",
            "search.cpp spin defs after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "int FailLowContinuationBonus = 0;\n",
            "int FailLowContinuationBonus = 0;\nint IdeaB8b_Weight = 1024;\nint IdeaB8b_Swing = 40;\n",
            "search.cpp spin defs plain",
        )

    if "bool IdeaB8 = false;\n" in scpp:
        scpp = replace_once(
            scpp,
            "bool IdeaB8 = false;\n",
            "bool IdeaB8 = false;\nbool IdeaB8b = false;\n",
            "search.cpp bool def after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "bool ThreatHistory = false;\n",
            "bool ThreatHistory = false;\nbool IdeaB8b = false;\n",
            "search.cpp bool def plain",
        )

    if '        {"IdeaB8_Swing", &IdeaB8_Swing, 0, 500},\n' in scpp:
        scpp = replace_once(
            scpp,
            '        {"IdeaB8_Swing", &IdeaB8_Swing, 0, 500},\n',
            '        {"IdeaB8_Swing", &IdeaB8_Swing, 0, 500},\n'
            '        {"IdeaB8b_Weight", &IdeaB8b_Weight, 0, 4096},\n'
            '        {"IdeaB8b_Swing", &IdeaB8b_Swing, 0, 500},\n',
            "search.cpp parameters after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            '        {"TtCutoffHistory", &TtCutoffHistory, 0, 1},\n',
            '        {"TtCutoffHistory", &TtCutoffHistory, 0, 1},\n'
            '        {"IdeaB8b_Weight", &IdeaB8b_Weight, 0, 4096},\n'
            '        {"IdeaB8b_Swing", &IdeaB8b_Swing, 0, 500},\n',
            "search.cpp parameters plain",
        )

    # QuietScorer::score
    if "            if (tune::IdeaB8) [[unlikely]] value += worker.threat_role_bonus(board, move);\n" in scpp:
        scpp = replace_once(
            scpp,
            "            if (tune::IdeaB8) [[unlikely]] value += worker.threat_role_bonus(board, move);\n",
            "            if (tune::IdeaB8) [[unlikely]] value += worker.threat_role_bonus(board, move);\n"
            "            if (tune::IdeaB8b) [[unlikely]] value += worker.threat_role_b8b_bonus(board, move);\n",
            "search.cpp QuietScorer after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "            if (use_threat_hist) [[unlikely]] value += worker.threat_quiet_bonus(board, move);\n",
            "            if (use_threat_hist) [[unlikely]] value += worker.threat_quiet_bonus(board, move);\n"
            "            if (tune::IdeaB8b) [[unlikely]] value += worker.threat_role_b8b_bonus(board, move);\n",
            "search.cpp QuietScorer plain",
        )

    # Worker ctor
    if "      threat_role_history_(std::make_unique<ThreatRoleHistory>()),\n" in scpp:
        scpp = replace_once(
            scpp,
            "      threat_role_history_(std::make_unique<ThreatRoleHistory>()),\n",
            "      threat_role_history_(std::make_unique<ThreatRoleHistory>()),\n"
            "      role_b8b_history_(std::make_unique<ThreatRoleHistoryB>()),\n",
            "search.cpp Worker ctor after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "      threat_history_(std::make_unique<ThreatQuietHistory>()),\n",
            "      threat_history_(std::make_unique<ThreatQuietHistory>()),\n"
            "      role_b8b_history_(std::make_unique<ThreatRoleHistoryB>()),\n",
            "search.cpp Worker ctor plain",
        )

    # Worker::clear
    if "    threat_role_cached_ = false;\n" in scpp:
        scpp = replace_once(
            scpp,
            "    threat_role_cached_ = false;\n",
            "    threat_role_cached_ = false;\n"
            "    *role_b8b_history_ = ThreatRoleHistoryB{};\n"
            "    role_b8b_key_valid_ = false;\n",
            "search.cpp Worker clear after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "    *threat_history_ = ThreatQuietHistory{};\n",
            "    *threat_history_ = ThreatQuietHistory{};\n"
            "    *role_b8b_history_ = ThreatRoleHistoryB{};\n"
            "    role_b8b_key_valid_ = false;\n",
            "search.cpp Worker clear plain",
        )

    # Worker::quiet_history
    if "    if (tune::IdeaB8) [[unlikely]] score += threat_role_bonus(board, move);\n" in scpp:
        scpp = replace_once(
            scpp,
            "    if (tune::IdeaB8) [[unlikely]] score += threat_role_bonus(board, move);\n",
            "    if (tune::IdeaB8) [[unlikely]] score += threat_role_bonus(board, move);\n"
            "    if (tune::IdeaB8b) [[unlikely]] score += threat_role_b8b_bonus(board, move);\n",
            "search.cpp quiet_history after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "    if (tune::ThreatHistory) [[unlikely]] score += threat_quiet_bonus(board, move);\n",
            "    if (tune::ThreatHistory) [[unlikely]] score += threat_quiet_bonus(board, move);\n"
            "    if (tune::IdeaB8b) [[unlikely]] score += threat_role_b8b_bonus(board, move);\n",
            "search.cpp quiet_history plain",
        )

    # Seat 028 method definitions
    b8b_defs = """
const Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {
    const std::uint64_t key = board.key();
    if (role_b8b_key_valid_ && role_b8b_key_ == key) return role_b8b_threat_;
    role_b8b_key_ = key;
    role_b8b_key_valid_ = true;
    RoleThreatB best;
    int best_victim_worth = 0;
    int best_attacker_worth = 0;
    constexpr int KingWorth = 100000;
    const Color us = board.side_to_move();
    const Bitboard enemy = board.occupied(opposite(us));
    Bitboard ours = board.pieces(us, Knight) | board.pieces(us, Bishop) | board.pieces(us, Rook) |
                    board.pieces(us, Queen) | board.pieces(us, King);
    while (ours != 0) {
        const int square = pop_lsb(ours);
        const int victim_type = piece_type(board.piece_at(square));
        const int victim_worth = victim_type == King ? KingWorth : SeePieceValue[static_cast<std::size_t>(victim_type)];
        Bitboard hits = board.attackers_to(square) & enemy;
        while (hits != 0) {
            const int from = pop_lsb(hits);
            const int attacker_type = piece_type(board.piece_at(from));
            const int attacker_worth = SeePieceValue[static_cast<std::size_t>(attacker_type)];
            if (attacker_worth <= 0 || attacker_worth >= victim_worth) continue;
            const bool better = !best.present || victim_worth > best_victim_worth ||
                                (victim_worth == best_victim_worth &&
                                 (attacker_worth < best_attacker_worth ||
                                  (attacker_worth == best_attacker_worth &&
                                   (square < best.victim_sq || (square == best.victim_sq && from < best.attacker_sq)))));
            if (!better) continue;
            best.present = true;
            best.victim_sq = square;
            best.attacker_sq = from;
            best.victim_type = victim_type;
            best.attacker_type = attacker_type;
            best.victim_worth = victim_worth;
            best_victim_worth = victim_worth;
            best_attacker_worth = attacker_worth;
        }
    }
    role_b8b_threat_ = best;
    return role_b8b_threat_;
}

int Worker::threat_role_b8b_of(const Board& board, Move move, const RoleThreatB& threat) {
    if (!threat.present) return 0;
    if (move.from == threat.victim_sq) return 1;
    if (threat.attacker_type == Bishop || threat.attacker_type == Rook || threat.attacker_type == Queen) {
        if ((attacks::between(threat.attacker_sq, threat.victim_sq) & square_bb(move.to)) != 0) return 2;
    }
    const int mover_type = piece_type(board.piece_at(move.from));
    const Color us = board.side_to_move();
    const Bitboard occupancy = (board.occupied() ^ square_bb(move.from)) | square_bb(move.to);
    Bitboard attacks_bb = 0;
    switch (mover_type) {
    case NoPieceType:
        break;
    case Pawn:
        attacks_bb = attacks::pawn(us, move.to);
        break;
    case Knight:
        attacks_bb = attacks::knight(move.to);
        break;
    case Bishop:
        attacks_bb = attacks::bishop(move.to, occupancy);
        break;
    case Rook:
        attacks_bb = attacks::rook(move.to, occupancy);
        break;
    case Queen:
        attacks_bb = attacks::queen(move.to, occupancy);
        break;
    case King:
        attacks_bb = attacks::king(move.to);
        break;
    default: {
        const int unexpected = mover_type;
        (void)unexpected;
        break;
    }
    }
    if ((attacks_bb & square_bb(threat.attacker_sq)) != 0) return 3;
    const int mover_worth = SeePieceValue[static_cast<std::size_t>(mover_type)];
    if (mover_worth <= 0) return 0;
    const Bitboard them = board.occupied(opposite(us));
    Bitboard targets = attacks_bb & them;
    while (targets != 0) {
        const int square = pop_lsb(targets);
        const int enemy_type = piece_type(board.piece_at(square));
        const int enemy_worth = enemy_type == King ? 100000 : SeePieceValue[static_cast<std::size_t>(enemy_type)];
        if (enemy_worth > threat.victim_worth && mover_worth < enemy_worth) return 4;
    }
    return 0;
}

int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {
    if (!tune::IdeaB8b) return 0;
    const RoleThreatB& threat = role_b8b_threat(board);
    if (!threat.present) return 0;
    const int role = threat_role_b8b_of(board, move, threat);
    const int raw = (*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())][static_cast<std::size_t>(threat.victim_type)]
                                        [static_cast<std::size_t>(threat.attacker_type)][static_cast<std::size_t>(role)];
    return raw * tune::IdeaB8b_Weight / 1024;
}

void Worker::update_threat_role_b8b(const Board& board, Move move, int bonus) {
    if (!tune::IdeaB8b) return;
    const RoleThreatB& threat = role_b8b_threat(board);
    if (!threat.present) return;
    const int role = threat_role_b8b_of(board, move, threat);
    apply_history((*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())][static_cast<std::size_t>(threat.victim_type)]
                                      [static_cast<std::size_t>(threat.attacker_type)][static_cast<std::size_t>(role)],
                  bonus);
}

void Worker::note_role_b8b_swing(const Board& board, SearchStack* ss, Move move, int depth) {
    if (!tune::IdeaB8b || ss->static_eval == ValueNone) return;
    const SearchStack* child = ss + 1;
    if (!child->role_b8b_eval_valid || child->static_eval == ValueNone) return;
    const int gained = -child->static_eval - ss->static_eval;
    if (gained < tune::IdeaB8b_Swing) return;
    update_threat_role_b8b(board, move, history_bonus(depth));
}
"""
    scpp = replace_once(
        scpp,
        "int Worker::capture_history_value(const Board& board, Move move) const {\n",
        b8b_defs.lstrip("\n") + "\nint Worker::capture_history_value(const Board& board, Move move) const {\n",
        "search.cpp method definitions before capture_history_value",
    )

    # Worker::update_quiet_stats
    if "    if (tune::IdeaB8) update_threat_role(board, move, bonus);\n" in scpp:
        scpp = replace_once(
            scpp,
            "    if (tune::IdeaB8) update_threat_role(board, move, bonus);\n",
            "    if (tune::IdeaB8) update_threat_role(board, move, bonus);\n"
            "    if (tune::IdeaB8b) update_threat_role_b8b(board, move, bonus);\n",
            "search.cpp update_quiet_stats best after P6",
        )
        scpp = replace_once(
            scpp,
            "        if (tune::IdeaB8) update_threat_role(board, quiet, -bonus);\n",
            "        if (tune::IdeaB8) update_threat_role(board, quiet, -bonus);\n"
            "        if (tune::IdeaB8b) update_threat_role_b8b(board, quiet, -bonus);\n",
            "search.cpp update_quiet_stats malus after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "    update_threat_quiet(board, move, bonus);\n",
            "    update_threat_quiet(board, move, bonus);\n"
            "    if (tune::IdeaB8b) update_threat_role_b8b(board, move, bonus);\n",
            "search.cpp update_quiet_stats best plain",
        )
        scpp = replace_once(
            scpp,
            "        update_threat_quiet(board, quiet, -bonus);\n",
            "        update_threat_quiet(board, quiet, -bonus);\n"
            "        if (tune::IdeaB8b) update_threat_role_b8b(board, quiet, -bonus);\n",
            "search.cpp update_quiet_stats malus plain",
        )

    # Worker::qsearch entry and eval_valid
    scpp = replace_once(
        scpp,
        "int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {\n",
        "int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {\n"
        "    if (tune::IdeaB8b) ss->role_b8b_eval_valid = false;\n",
        "search.cpp qsearch entry",
    )
    scpp = replace_once(
        scpp,
        "    int futility_base;\n    if (in_check) {\n        ss->static_eval = ValueNone;\n",
        "    int futility_base;\n    if (in_check) {\n        ss->static_eval = ValueNone;\n"
        "        if (tune::IdeaB8b) ss->role_b8b_eval_valid = false;\n",
        "search.cpp qsearch in_check",
    )
    qsearch_eval_anchor_p6 = (
        "        if (tt_hit && tte.eval != ValueNone) ss->raw_eval = tte.eval;\n"
        "        else ss->raw_eval = static_evaluate(board, ss);\n"
        "        eval = ss->static_eval = rule50_damped_static(corrected_eval(board, ss->raw_eval, ss), board.halfmove_clock());\n"
        "        if (tune::IdeaB8) ss->role_eval_ready = true;\n"
    )
    qsearch_eval_anchor_plain = (
        "        if (tt_hit && tte.eval != ValueNone) ss->raw_eval = tte.eval;\n"
        "        else ss->raw_eval = static_evaluate(board, ss);\n"
        "        eval = ss->static_eval = rule50_damped_static(corrected_eval(board, ss->raw_eval, ss), board.halfmove_clock());\n"
    )
    if qsearch_eval_anchor_p6 in scpp:
        scpp = replace_once(
            scpp,
            qsearch_eval_anchor_p6,
            qsearch_eval_anchor_p6 + "        if (tune::IdeaB8b) ss->role_b8b_eval_valid = ss->static_eval != ValueNone;\n",
            "search.cpp qsearch static_eval after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            qsearch_eval_anchor_plain,
            qsearch_eval_anchor_plain + "        if (tune::IdeaB8b) ss->role_b8b_eval_valid = ss->static_eval != ValueNone;\n",
            "search.cpp qsearch static_eval plain",
        )

    # Worker::search entry, static_eval, beta cutoff swing, PV quiet bonus
    scpp = replace_once(
        scpp,
        "int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n",
        "int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n"
        "    if (tune::IdeaB8b) ss->role_b8b_eval_valid = false;\n",
        "search.cpp search entry",
    )
    scpp = replace_once(
        scpp,
        "    bool improving = false;\n    if (!in_check) {\n",
        "    if (tune::IdeaB8b) ss->role_b8b_eval_valid = ss->static_eval != ValueNone;\n\n"
        "    bool improving = false;\n    if (!in_check) {\n",
        "search.cpp search static_eval",
    )
    scpp = replace_once(
        scpp,
        "            update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);\n",
        "            update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);\n"
        "            if (tune::IdeaB8b) note_role_b8b_swing(board, ss, best_move, depth);\n",
        "search.cpp search beta cutoff swing",
    )
    if "        if (tune::IdeaB8) update_threat_role(board, best_move, history_bonus(depth) / 4);\n" in scpp:
        scpp = replace_once(
            scpp,
            "        if (tune::IdeaB8) update_threat_role(board, best_move, history_bonus(depth) / 4);\n",
            "        if (tune::IdeaB8) update_threat_role(board, best_move, history_bonus(depth) / 4);\n"
            "        if (tune::IdeaB8b) update_threat_role_b8b(board, best_move, history_bonus(depth) / 4);\n",
            "search.cpp search PV bonus after P6",
        )
    else:
        scpp = replace_once(
            scpp,
            "        update_threat_quiet(board, best_move, history_bonus(depth) / 4);\n",
            "        update_threat_quiet(board, best_move, history_bonus(depth) / 4);\n"
            "        if (tune::IdeaB8b) update_threat_role_b8b(board, best_move, history_bonus(depth) / 4);\n",
            "search.cpp search PV bonus plain",
        )

    # CuckooRep child wrappers
    for fn_hdr in [
        "int Worker::search_child(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n",
        "int Worker::qsearch_child(Board& board, SearchStack* ss, int alpha, int beta) {\n",
        "int Worker::search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {\n",
        "int Worker::qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta) {\n",
    ]:
        scpp = replace_once(
            scpp,
            fn_hdr,
            fn_hdr + "    if (tune::IdeaB8b) ss->role_b8b_eval_valid = false;\n",
            f"search.cpp {fn_hdr.strip()}",
        )

    scpp_path.write_text(scpp, encoding="utf-8")

    # 3. src/uci.cpp
    ucpp_path = tree_dir / "src/uci.cpp"
    ucpp = ucpp_path.read_text(encoding="utf-8")

    if '                         "option name IdeaB8 type check default false\\n"\n' in ucpp:
        ucpp = replace_once(
            ucpp,
            '                         "option name IdeaB8 type check default false\\n"\n',
            '                         "option name IdeaB8 type check default false\\n"\n'
            '                         "option name IdeaB8b type check default false\\n"\n',
            "uci.cpp option decl after P6",
        )
    else:
        ucpp = replace_once(
            ucpp,
            '                         "option name ThreatHistory type check default false\\n"\n',
            '                         "option name ThreatHistory type check default false\\n"\n'
            '                         "option name IdeaB8b type check default false\\n"\n',
            "uci.cpp option decl plain",
        )

    if '            } else if (name == "IdeaB8") {\n' in ucpp:
        ucpp = replace_once(
            ucpp,
            '            } else if (name == "IdeaB8") {\n'
            '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8 = value_text == "true";\n'
            '                else note_invalid();\n',
            '            } else if (name == "IdeaB8") {\n'
            '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8 = value_text == "true";\n'
            '                else note_invalid();\n'
            '            } else if (name == "IdeaB8b") {\n'
            '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
            '                else note_invalid();\n',
            "uci.cpp setoption after P6",
        )
    else:
        ucpp = replace_once(
            ucpp,
            '            } else if (name == "DeadMaterial") {\n',
            '            } else if (name == "IdeaB8b") {\n'
            '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
            '                else note_invalid();\n'
            '            } else if (name == "DeadMaterial") {\n',
            "uci.cpp setoption plain",
        )

    ucpp_path.write_text(ucpp, encoding="utf-8")


def main() -> int:
    out_lines: list[str] = [
        "=== JOB 41 PART P7: Seat 028 IdeaB8b Port, Three Patches, Builds & Full P7c Verification ===",
        f"start_utc: {utc_now()}",
        "",
    ]
    all_ok = True

    # 1. Construct modified source trees and emit LF diff -u patches
    patch_p7 = JOB41 / "P7_B8b_028.patch.txt"
    patch_both = JOB41 / "B8_both.patch.txt"
    patch_b7 = JOB41 / "bundle_grok7.patch.txt"

    gen_p7 = WORK41 / "gen_src_p7"
    if gen_p7.exists():
        shutil.rmtree(gen_p7)
    shutil.copytree(TPL_V3, gen_p7)
    inject_p7_into_tree(gen_p7)
    generate_diff_u_patch(TPL_V3, gen_p7, patch_p7)

    gen_both = WORK41 / "gen_src_both"
    ok_g1, _ = apply_patch_to_fresh_v3(P6_B8_PATCH, gen_both)
    if not ok_g1:
        raise RuntimeError("Failed applying P6_B8_078.patch.txt")
    inject_p7_into_tree(gen_both)
    generate_diff_u_patch(TPL_V3, gen_both, patch_both)

    gen_b7 = WORK41 / "gen_src_b7"
    ok_g2, _ = apply_patch_to_fresh_v3(BUNDLE6_PATCH, gen_b7)
    if not ok_g2:
        raise RuntimeError("Failed applying bundle_grok.patch.txt")
    inject_p7_into_tree(gen_b7)
    generate_diff_u_patch(TPL_V3, gen_b7, patch_b7)

    out_lines.append("--- 1. Patch Files Emitted & Verified Clean Against Fresh r15d + v3 ---")
    builds_append: list[str] = ["", "=== PART P7 BUILDS ==="]

    built: dict[str, tuple[str, str, str, str, str, int]] = {}
    for label, ppath, sdir, bdir in [
        ("P7_alone", patch_p7, WORK41 / "src_p7_alone", WORK41 / "bld_p7_alone"),
        ("B8_both", patch_both, WORK41 / "src_b8_both", WORK41 / "bld_b8_both"),
        ("bundle_grok7", patch_b7, WORK41 / "src_bundle7", WORK41 / "bld_bundle7"),
    ]:
        raw = ppath.read_bytes()
        crlf = raw.count(b"\r\n")
        ok_crlf, s_crlf = fmt_cmp(f"{ppath.name} CRLF count", crlf, 0)
        all_ok = all_ok and ok_crlf
        psha = sha256_file(ppath)
        plines = len(raw.decode("utf-8").splitlines())
        ok_ap, ap_msg = apply_patch_to_fresh_v3(ppath, sdir)
        all_ok = all_ok and ok_ap
        exe, esha, cf, lf = build_release_v3(sdir, bdir)
        built[label] = (exe, esha, psha, cf, lf, plines)
        out_lines.extend(
            [
                s_crlf,
                f"  patch path                                  : {ppath}",
                f"  patch lines({ppath}) : {plines}",
                f"  patch sha256({ppath}) : {psha}",
                f"  apply_against_fresh_r15d_v3                 : {ap_msg}",
                f"  exe path                                    : {exe}",
                f"  exe sha256({exe}) : {esha}",
                f"  id name                                     : {get_id_name(exe)}",
            ]
        )
        ok_hd, hd_lines = verify_uci_option_check(exe, "HindsightDepth")
        ok_b8b_uci, b8b_uci_lines = verify_uci_option_check(exe, "IdeaB8b")
        all_ok = all_ok and ok_hd and ok_b8b_uci
        out_lines.extend(hd_lines + b8b_uci_lines)

        builds_append.extend(
            [
                f"Part P7 [{label}]:",
                f"   patch path = {ppath}",
                f"   patch lines({ppath}) = {plines}",
                f"   patch sha256({ppath}) = {psha}",
                f"   exe path = {exe}",
                f"   exe sha256({exe}) = {esha}",
                f"   id_name = {get_id_name(exe)}",
                f"   compile_flags = {cf}",
                f"   link_flags    = {lf}",
                "",
            ]
        )

    p7_exe = built["P7_alone"][0]
    both_exe = built["B8_both"][0]
    b7_exe = built["bundle_grok7"][0]

    # Also verify IdeaB8 UCI option on B8_both and bundle_grok7
    for lbl, ex in [("B8_both", both_exe), ("bundle_grok7", b7_exe)]:
        ok_u, u_lines = verify_uci_option_check(ex, "IdeaB8")
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    out_lines.append("")
    out_lines.append("--- 2. All-Switches-OFF Verification on P7_alone, B8_both, and bundle_grok7 ---")
    for lbl, ex, extra in [
        ("P7_alone_off", p7_exe, [("IdeaB8b", "false")]),
        ("B8_both_off", both_exe, [("IdeaB8", "false"), ("IdeaB8b", "false")]),
        ("bundle_grok7_default_off", b7_exe, None),
        ("bundle_grok7_explicit_7_false", b7_exe, ALL_SEVEN_FALSE),
    ]:
        ok_off, off_lines = verify_all_off_numbers(lbl, ex, extra)
        all_ok = all_ok and ok_off
        out_lines.extend(off_lines)

    # Verify bundle_grok7 OFF O and OFF G rows == Job 39 OFF O and OFF G
    out_lines.append("")
    out_lines.append("--- 3. bundle_grok7 All-7-OFF O and G Depth-12 Rows vs Job 39 OFF Rows ---")
    j39_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    j39_off_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")

    b7_off_o = run_epd_depth12(
        b7_exe,
        O_FENS_PATH,
        ALL_SEVEN_FALSE,
        JOB41 / "P7_bundle7_all_off_O_d12.rows.txt",
        JOB41 / "P7_bundle7_all_off_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    b7_off_g = run_epd_depth12(
        b7_exe,
        G_EPD_PATH,
        ALL_SEVEN_FALSE,
        JOB41 / "P7_bundle7_all_off_G_d12.rows.txt",
        JOB41 / "P7_bundle7_all_off_G_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    diff_off_o, _ = diff_rows(b7_off_o, j39_off_o)
    diff_off_g, _ = diff_rows(b7_off_g, j39_off_g)
    ok_oo1, s_oo1 = fmt_cmp("bundle_grok7 OFF O sum vs J39 OFF O", sum(r[1] for r in b7_off_o), EXP_OFF_O_SUM)
    ok_oo2, s_oo2 = fmt_cmp("bundle_grok7 OFF O equal positions", 200 - diff_off_o, 200)
    ok_og1, s_og1 = fmt_cmp("bundle_grok7 OFF G sum vs J39 OFF G", sum(r[1] for r in b7_off_g), EXP_OFF_G_SUM)
    ok_og2, s_og2 = fmt_cmp("bundle_grok7 OFF G equal positions", 353 - diff_off_g, 353)
    all_ok = all_ok and ok_oo1 and ok_oo2 and ok_og1 and ok_og2
    out_lines.extend([s_oo1, s_oo2, s_og1, s_og2])

    # 4. bundle_grok7 with each of the 6 old switches alone on == Job 39 P-c O rows position by position
    out_lines.append("")
    out_lines.append("--- 4. bundle_grok7 Six Old Switches Alone ON vs Job 39 P1..P6 O Depth-12 Rows ---")
    b7_old_rows: dict[str, list[tuple[int, int, str]]] = {}
    for short, opt_name, j39_fname, exp_sum in SIX_OLD_SWITCHES:
        opts = [(o, "true" if o == opt_name else "false") for o in SEVEN_SWITCH_NAMES]
        rows = run_epd_depth12(
            b7_exe,
            O_FENS_PATH,
            opts,
            JOB41 / f"P7_bundle7_only_{short}_O_d12.rows.txt",
            JOB41 / f"P7_bundle7_only_{short}_O_d12.rows.txt.meta",
            depth=12,
            cpu_pin=1,
        )
        b7_old_rows[opt_name] = rows
        j39_ref = read_j39_rows(JOB39 / j39_fname)
        any_d, _ = diff_rows(rows, j39_ref)
        got_s = sum(r[1] for r in rows)
        ok_s, ss1 = fmt_cmp(f"bundle_grok7 only {opt_name} O sum", got_s, exp_sum)
        ok_p, ss2 = fmt_cmp(f"bundle_grok7 only {opt_name} equal pos vs J39", 200 - any_d, 200)
        all_ok = all_ok and ok_s and ok_p
        out_lines.extend([ss1, ss2])

    # 5. bundle_grok7 with IdeaB8b alone on: O rows, G rows, Set A line L
    out_lines.append("")
    out_lines.append("--- 5. bundle_grok7 IdeaB8b (028) Alone ON: O d12, G d12, and Set A Line L ---")
    b8b_only_7 = [(o, "true" if o == "IdeaB8b" else "false") for o in SEVEN_SWITCH_NAMES]
    b7_b8b_o = run_epd_depth12(
        b7_exe,
        O_FENS_PATH,
        b8b_only_7,
        JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt",
        JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    b7_b8b_g = run_epd_depth12(
        b7_exe,
        G_EPD_PATH,
        b8b_only_7,
        JOB41 / "P7_bundle7_only_B8b_G_d12.rows.txt",
        JOB41 / "P7_bundle7_only_B8b_G_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )

    b8b_o_sum = sum(r[1] for r in b7_b8b_o)
    b8b_g_sum = sum(r[1] for r in b7_b8b_g)
    b8b_o_ratio = b8b_o_sum / EXP_OFF_O_SUM
    b8b_g_ratio = b8b_g_sum / EXP_OFF_G_SUM
    diff_b8b_vs_off_o, nd_b8b_vs_off_o = diff_rows(b7_b8b_o, j39_off_o)
    diff_b8b_vs_off_g, nd_b8b_vs_off_g = diff_rows(b7_b8b_g, j39_off_g)
    diff_b8b_vs_b8_o, nd_b8b_vs_b8_o = diff_rows(b7_b8b_o, b7_old_rows["IdeaB8"])
    mv_b8b_vs_off_o = sum(1 for a, b in zip(b7_b8b_o, j39_off_o) if a[3] != b[3])
    mv_b8b_vs_off_g = sum(1 for a, b in zip(b7_b8b_g, j39_off_g) if a[3] != b[3])
    mv_b8b_vs_b8_o = sum(1 for a, b in zip(b7_b8b_o, b7_old_rows["IdeaB8"]) if a[3] != b[3])

    # Set A line L with IdeaB8b alone on
    res_sa = run_selfgame_set_with_options(b7_exe, "carbon2-job33-a", 200, None, b8b_only_7, cpu_pin=1)
    sa_rows_path = JOB41 / "P7_bundle7_only_B8b_SetA_L.rows.txt"
    sa_meta_path = JOB41 / "P7_bundle7_only_B8b_SetA_L.rows.txt.meta"
    write_v2_v3_rows(sa_rows_path, "Job 41 Part P7 bundle_grok7 IdeaB8b alone ON Set A line L (built-in eval, PC20)", res_sa)
    write_seta_meta(sa_meta_path, b7_exe, b8b_only_7, res_sa)
    sa_records = res_sa.total_records
    sa_searches = res_sa.total_searches
    sa_nodes = res_sa.total_nodes
    sa_sha = res_sa.full_sha256

    out_lines.extend(
        [
            f"  IdeaB8b O d12 sum_nodes                     : {b8b_o_sum} (OFF = {EXP_OFF_O_SUM}, ratio = {b8b_o_ratio:.6f})",
            f"  IdeaB8b O d12 first 3 nodes                 : {b7_b8b_o[0][1]} / {b7_b8b_o[1][1]} / {b7_b8b_o[2][1]}",
            f"  IdeaB8b O d12 differing positions vs OFF    : {diff_b8b_vs_off_o} / 200 (node diffs = {nd_b8b_vs_off_o}, bestmove diffs = {mv_b8b_vs_off_o})",
            f"  IdeaB8b O d12 differing positions vs B8(078): {diff_b8b_vs_b8_o} / 200 (node diffs = {nd_b8b_vs_b8_o}, bestmove diffs = {mv_b8b_vs_b8_o})",
            f"  IdeaB8b G d12 sum_nodes                     : {b8b_g_sum} (OFF = {EXP_OFF_G_SUM}, ratio = {b8b_g_ratio:.6f})",
            f"  IdeaB8b G d12 differing positions vs OFF    : {diff_b8b_vs_off_g} / 353 (node diffs = {nd_b8b_vs_off_g}, bestmove diffs = {mv_b8b_vs_off_g})",
            f"  IdeaB8b Set A line L records / searches     : {sa_records} / {sa_searches} (OFF = {EXP_SETA_L_RECORDS})",
            f"  IdeaB8b Set A line L sum_nodes              : {sa_nodes} (OFF = {EXP_SETA_L_NODES}, ratio = {sa_nodes / EXP_SETA_L_NODES:.6f})",
            f"  IdeaB8b Set A line L sha256                 : {sa_sha} (OFF = {EXP_SETA_L_SHA})",
        ]
    )

    # 6. Cross-build identities: P7_alone and B8_both vs bundle_grok7
    out_lines.append("")
    out_lines.append("--- 6. Cross-Build Identities: P7_alone & B8_both vs bundle_grok7 ---")
    p7_alone_o = run_epd_depth12(
        p7_exe,
        O_FENS_PATH,
        [("IdeaB8b", "true")],
        JOB41 / "P7_alone_B8b_on_O_d12.rows.txt",
        JOB41 / "P7_alone_B8b_on_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    both_b8b_o = run_epd_depth12(
        both_exe,
        O_FENS_PATH,
        [("IdeaB8", "false"), ("IdeaB8b", "true")],
        JOB41 / "P7_B8_both_only_B8b_O_d12.rows.txt",
        JOB41 / "P7_B8_both_only_B8b_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    both_b8_o = run_epd_depth12(
        both_exe,
        O_FENS_PATH,
        [("IdeaB8", "true"), ("IdeaB8b", "false")],
        JOB41 / "P7_B8_both_only_B8_O_d12.rows.txt",
        JOB41 / "P7_B8_both_only_B8_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )

    d_p7_vs_b7, _ = diff_rows(p7_alone_o, b7_b8b_o)
    d_both_b8b_vs_b7, _ = diff_rows(both_b8b_o, b7_b8b_o)
    d_both_b8_vs_b7, _ = diff_rows(both_b8_o, b7_old_rows["IdeaB8"])

    ok_c1, sc1 = fmt_cmp("P7_alone IdeaB8b O sum vs bundle_grok7", sum(r[1] for r in p7_alone_o), b8b_o_sum)
    ok_c2, sc2 = fmt_cmp("P7_alone IdeaB8b equal pos vs bundle_grok7", 200 - d_p7_vs_b7, 200)
    ok_c3, sc3 = fmt_cmp("B8_both IdeaB8b O sum vs bundle_grok7", sum(r[1] for r in both_b8b_o), b8b_o_sum)
    ok_c4, sc4 = fmt_cmp("B8_both IdeaB8b equal pos vs bundle_grok7", 200 - d_both_b8b_vs_b7, 200)
    ok_c5, sc5 = fmt_cmp("B8_both IdeaB8 O sum vs bundle_grok7", sum(r[1] for r in both_b8_o), 8262696)
    ok_c6, sc6 = fmt_cmp("B8_both IdeaB8 equal pos vs bundle_grok7", 200 - d_both_b8_vs_b7, 200)

    # Also verify BOTH IdeaB8=true AND IdeaB8b=true together on B8_both vs bundle_grok7 (PC20 bench 11)
    both_on_b8both = run_fresh_bench(both_exe, 11, pc20_option_lines([("IdeaB8", "true"), ("IdeaB8b", "true")]))
    both_on_b7 = run_fresh_bench(
        b7_exe,
        11,
        pc20_option_lines([(o, "true" if o in ("IdeaB8", "IdeaB8b") else "false") for o in SEVEN_SWITCH_NAMES]),
    )
    ok_c7, sc7 = fmt_cmp("B8_both (IdeaB8+IdeaB8b ON) PC20 bench 11 == bundle_grok7", both_on_b8both, both_on_b7)

    all_ok = all_ok and ok_c1 and ok_c2 and ok_c3 and ok_c4 and ok_c5 and ok_c6 and ok_c7
    out_lines.extend([sc1, sc2, sc3, sc4, sc5, sc6, sc7])

    out_lines.append("")
    ok_ov, s_ov = fmt_cmp("PART P7 OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")

    (JOB41 / "partP7_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    with open(JOB41 / "builds.txt", "a", encoding="utf-8") as bf:
        bf.write("\n".join(builds_append) + "\n")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
