#!/usr/bin/env python3
"""
Job 45 Part P10 (`run_partP10.py`): AN `IdeaB8b` THAT COSTS LESS, WITH EVERY NODE EQUAL.
  (a) Counters on a scratch copy of `bundle8` (`/tmp/carbon2_job45/bld_p10_counter/forge`, never used
      for rows/games), verified `200 == 200` on `O` depth 12 against Step 0 clean `bundle8` `IdeaB8b` rows:
      counts `role_b8b_threat` calls, computations, one-key cache hits, `threat.present == true`, and
      roles `0..4` returned across all 200 `O` depth-12 searches (`sum_p10_counters.py`).
  (b) Emits `forge-combo29/carbon2/job45/P10_B8b_fast.patch.txt` on top of `bundle8` (`r15d + v3 +
      job41/bundle_grok7.patch.txt + job42/P8_S13_hoist.patch.txt`): adds UCI check option
      `IdeaB8b_Fast` (default `false`) that does nothing unless `IdeaB8b` is on.
  (c) Identity checks on `/tmp/carbon2_job45/bld_bundle8_p10/forge`:
      - All 9 `Idea*` switches off = every OFF number + non-PC20 `HindsightDepth` `bench 13`.
      - `IdeaB8b_Fast=true` alone (`IdeaB8b=false`) = OFF `O` (`8,315,168 == 8,315,168`, `200 == 200`).
      - `IdeaB8b + IdeaB8b_Fast` = `IdeaB8b` alone position by position on `O` (`8,483,711`, `200 == 200`),
        `G` (`17,366,116`, `353 == 353`), and `Set A line L` (`26,709 == 26,709` records, `26,829 == 26,829`
        searches, `106,651,211 == 106,651,211` nodes, `de20b5698c77baab... == de20b5698c77baab...`, `200 == 200`
        per-attempt rows vs Job 41 `P7_bundle7_only_B8b_SetA_L.rows.txt`).
        If any position/game differs, reports the first position that differs and stops Part P10 without timing.
  (d) Times as in `P9d` (`O`, depth 12, pinned core 1, forward `01..04` then reverse `05..08`):
      `all_off_1`, `all_off_2`, `only_B8b`, `B8b_and_B8b_Fast`.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j45_lib import (  # noqa: E402
    EIGHT_SWITCH_NAMES,
    EXP_B8B_G_SUM,
    EXP_B8B_O_SUM,
    EXP_B8B_SETA_L_NODES,
    EXP_B8B_SETA_L_RECORDS,
    EXP_B8B_SETA_L_SEARCHES,
    EXP_B8B_SETA_L_SHA,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    G_EPD_PATH,
    JOB39,
    JOB41,
    JOB45,
    O_FENS_PATH,
    TPL_V3,
    WORK45,
    apply_bundle8_to_fresh_v3,
    build_release_v3,
    diff_breakdown_with_samples,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name,
    load_fens,
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

P10_SWITCH_NAMES = [
    "IdeaK4",
    "IdeaS32",
    "IdeaB1",
    "IdeaS13",
    "IdeaS13_Hoist",
    "IdeaS10",
    "IdeaB8",
    "IdeaB8b",
    "IdeaB8b_Fast",
]
ALL_NINE_P10_FALSE = [(o, "false") for o in P10_SWITCH_NAMES]


def replace_once(src: str, old: str, new: str, label: str) -> str:
    cnt = src.count(old)
    if cnt != 1:
        raise RuntimeError(f"[{label}] expected 1 occurrence, found {cnt}:\n{old!r}")
    return src.replace(old, new, 1)


def inject_p10a_counters(tree_dir: pathlib.Path) -> None:
    shpp_p = tree_dir / "include/forge/search.hpp"
    shpp = shpp_p.read_text(encoding="utf-8")
    shpp = replace_once(
        shpp,
        "    void reset_node_count() {\n"
        "        local_nodes_ = 0;\n"
        "        nodes_.store(0, std::memory_order_relaxed);\n"
        "    }\n",
        "    void reset_node_count() {\n"
        "        local_nodes_ = 0;\n"
        "        nodes_.store(0, std::memory_order_relaxed);\n"
        "        p10_threat_calls_ = 0;\n"
        "        p10_threat_computes_ = 0;\n"
        "        p10_cache_hits_ = 0;\n"
        "        p10_compute_present_ = 0;\n"
        "        p10_call_present_ = 0;\n"
        "        p10_trob_calls_ = 0;\n"
        "        p10_trob_from_bonus_ = 0;\n"
        "        p10_trob_from_update_ = 0;\n"
        "        for (auto& c : p10_role_cnt_) c = 0;\n"
        "        p10_swing_runs_ = 0;\n"
        "        p10_swing_gained_ = 0;\n"
        "        p10_total_updates_ = 0;\n"
        "    }\n"
        "    mutable std::uint64_t p10_threat_calls_ = 0;\n"
        "    mutable std::uint64_t p10_threat_computes_ = 0;\n"
        "    mutable std::uint64_t p10_cache_hits_ = 0;\n"
        "    mutable std::uint64_t p10_compute_present_ = 0;\n"
        "    mutable std::uint64_t p10_call_present_ = 0;\n"
        "    mutable std::uint64_t p10_trob_calls_ = 0;\n"
        "    mutable std::uint64_t p10_trob_from_bonus_ = 0;\n"
        "    mutable std::uint64_t p10_trob_from_update_ = 0;\n"
        "    mutable std::array<std::uint64_t, 5> p10_role_cnt_{};\n"
        "    mutable std::uint64_t p10_swing_runs_ = 0;\n"
        "    mutable std::uint64_t p10_swing_gained_ = 0;\n"
        "    mutable std::uint64_t p10_total_updates_ = 0;\n",
        "P10a search.hpp counter fields",
    )
    shpp_p.write_text(shpp, encoding="utf-8")

    scpp_p = tree_dir / "src/search.cpp"
    scpp = scpp_p.read_text(encoding="utf-8")

    scpp = replace_once(
        scpp,
        "const Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {\n"
        "    const std::uint64_t key = board.key();\n"
        "    if (role_b8b_key_valid_ && role_b8b_key_ == key) return role_b8b_threat_;\n"
        "    role_b8b_key_ = key;\n"
        "    role_b8b_key_valid_ = true;\n",
        "const Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {\n"
        "    ++p10_threat_calls_;\n"
        "    const std::uint64_t key = board.key();\n"
        "    if (role_b8b_key_valid_ && role_b8b_key_ == key) {\n"
        "        ++p10_cache_hits_;\n"
        "        if (role_b8b_threat_.present) ++p10_call_present_;\n"
        "        return role_b8b_threat_;\n"
        "    }\n"
        "    ++p10_threat_computes_;\n"
        "    role_b8b_key_ = key;\n"
        "    role_b8b_key_valid_ = true;\n",
        "P10a role_b8b_threat entry counters",
    )

    scpp = replace_once(
        scpp,
        "    role_b8b_threat_ = best;\n"
        "    return role_b8b_threat_;\n"
        "}\n",
        "    if (best.present) {\n"
        "        ++p10_compute_present_;\n"
        "        ++p10_call_present_;\n"
        "    }\n"
        "    role_b8b_threat_ = best;\n"
        "    return role_b8b_threat_;\n"
        "}\n",
        "P10a role_b8b_threat exit counters",
    )

    scpp = replace_once(
        scpp,
        "int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8b) return 0;\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n"
        "    if (!threat.present) return 0;\n"
        "    const int role = threat_role_b8b_of(board, move, threat);\n",
        "int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8b) return 0;\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n"
        "    if (!threat.present) return 0;\n"
        "    const int role = threat_role_b8b_of(board, move, threat);\n"
        "    ++p10_trob_calls_;\n"
        "    ++p10_trob_from_bonus_;\n"
        "    if (role >= 0 && role <= 4) ++p10_role_cnt_[static_cast<std::size_t>(role)];\n",
        "P10a threat_role_b8b_bonus counters",
    )

    scpp = replace_once(
        scpp,
        "void Worker::update_threat_role_b8b(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8b) return;\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n"
        "    if (!threat.present) return;\n"
        "    const int role = threat_role_b8b_of(board, move, threat);\n"
        "    apply_history((*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())][static_cast<std::size_t>(threat.victim_type)]\n"
        "                                      [static_cast<std::size_t>(threat.attacker_type)][static_cast<std::size_t>(role)],\n"
        "                  bonus);\n"
        "}\n",
        "void Worker::update_threat_role_b8b(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8b) return;\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n"
        "    if (!threat.present) return;\n"
        "    const int role = threat_role_b8b_of(board, move, threat);\n"
        "    ++p10_trob_calls_;\n"
        "    ++p10_trob_from_update_;\n"
        "    if (role >= 0 && role <= 4) ++p10_role_cnt_[static_cast<std::size_t>(role)];\n"
        "    ++p10_total_updates_;\n"
        "    apply_history((*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())][static_cast<std::size_t>(threat.victim_type)]\n"
        "                                      [static_cast<std::size_t>(threat.attacker_type)][static_cast<std::size_t>(role)],\n"
        "                  bonus);\n"
        "}\n",
        "P10a update_threat_role_b8b counters",
    )

    scpp = replace_once(
        scpp,
        "void Worker::note_role_b8b_swing(const Board& board, SearchStack* ss, Move move, int depth) {\n"
        "    if (!tune::IdeaB8b || ss->static_eval == ValueNone) return;\n"
        "    const SearchStack* child = ss + 1;\n"
        "    if (!child->role_b8b_eval_valid || child->static_eval == ValueNone) return;\n"
        "    const int gained = -child->static_eval - ss->static_eval;\n"
        "    if (gained < tune::IdeaB8b_Swing) return;\n"
        "    update_threat_role_b8b(board, move, history_bonus(depth));\n"
        "}\n",
        "void Worker::note_role_b8b_swing(const Board& board, SearchStack* ss, Move move, int depth) {\n"
        "    if (!tune::IdeaB8b) return;\n"
        "    ++p10_swing_runs_;\n"
        "    if (ss->static_eval == ValueNone) return;\n"
        "    const SearchStack* child = ss + 1;\n"
        "    if (!child->role_b8b_eval_valid || child->static_eval == ValueNone) return;\n"
        "    const int gained = -child->static_eval - ss->static_eval;\n"
        "    if (gained < tune::IdeaB8b_Swing) return;\n"
        "    ++p10_swing_gained_;\n"
        "    update_threat_role_b8b(board, move, history_bonus(depth));\n"
        "}\n",
        "P10a note_role_b8b_swing counters",
    )

    scpp = replace_once(
        scpp,
        "    for (auto& helper : helpers) helper.join();\n"
        "    shared_.stop.store(external_stop, std::memory_order_relaxed);\n"
        "    return result;\n",
        "    for (auto& helper : helpers) helper.join();\n"
        "    shared_.stop.store(external_stop, std::memory_order_relaxed);\n"
        "    if (emit_info) {\n"
        "        const Worker* w = all[0];\n"
        "        const std::lock_guard<std::mutex> output_lock(uci_output_mutex());\n"
        '        std::cout << "info string p10_b8b_cnt "\n'
        '                  << w->p10_threat_calls_ << " " << w->p10_threat_computes_ << " " << w->p10_cache_hits_ << " "\n'
        '                  << w->p10_compute_present_ << " " << w->p10_call_present_ << " " << w->p10_trob_calls_ << " "\n'
        '                  << w->p10_trob_from_bonus_ << " " << w->p10_trob_from_update_ << " " << w->p10_role_cnt_[0] << " "\n'
        '                  << w->p10_role_cnt_[1] << " " << w->p10_role_cnt_[2] << " " << w->p10_role_cnt_[3] << " "\n'
        '                  << w->p10_role_cnt_[4] << " " << w->p10_swing_runs_ << " " << w->p10_swing_gained_ << " "\n'
        '                  << w->p10_total_updates_ << std::endl;\n'
        "    }\n"
        "    return result;\n",
        "P10a Searcher::search emit_info",
    )
    scpp_p.write_text(scpp, encoding="utf-8")


def run_p10a_counter_o_d12(exe_path: str, switch_opts: list[tuple[str, str]], out_raw: pathlib.Path, out_meta: pathlib.Path) -> None:
    fens = load_fens(O_FENS_PATH)
    opt_lines = pc20_option_lines(switch_opts)
    proc = subprocess.Popen(
        ["taskset", "-c", "1", exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline().rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    cnt_re = re.compile(r"^info string p10_b8b_cnt ((?:\d+\s*){16})$")
    rows_lines = [
        "# position\tnodes\tbestmove\tscore\tthreat_calls\tthreat_computes\tcache_hits\tcompute_present\tcall_present\ttrob_calls\ttrob_from_bonus\ttrob_from_update\trole_0\trole_1\trole_2\trole_3\trole_4\tswing_runs\tswing_gained_ge_40\ttotal_table_updates"
    ]
    sum_nodes = 0
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write(f"ucinewgame\nisready\nposition fen {fen}\nisready\ngo depth 12\n")
        proc.stdin.flush()
        ready_seen = 0
        last_nodes: int | None = None
        last_score: str | None = None
        last_cnts: list[int] | None = None
        bm: str | None = None
        while True:
            s = proc.stdout.readline().rstrip("\r\n").strip()
            if ready_seen < 2:
                if s == "readyok":
                    ready_seen += 1
                continue
            if s.startswith("info depth 12 ") and " nodes " in s and " score " in s:
                toks = s.split()
                ni = toks.index("nodes")
                si = toks.index("score")
                last_nodes = int(toks[ni + 1])
                last_score = f"{toks[si + 1]} {toks[si + 2]}"
                continue
            mc = cnt_re.match(s)
            if mc:
                last_cnts = [int(x) for x in mc.group(1).split()]
                continue
            if s.startswith("bestmove "):
                bm = s.split()[1]
                break
        assert last_nodes is not None and last_score is not None and last_cnts is not None and bm is not None, (
            f"pos {idx}: nodes={last_nodes} score={last_score} cnts={last_cnts} bm={bm}"
        )
        sum_nodes += last_nodes
        cnt_s = "\t".join(str(x) for x in last_cnts)
        rows_lines.append(f"{idx}\t{last_nodes}\t{bm}\t{last_score}\t{cnt_s}")

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    rc = proc.wait()
    assert rc == 0, f"counter engine exited with {rc}"

    out_raw.write_text("\n".join(rows_lines) + "\n", encoding="utf-8")
    out_meta.write_text(
        "\n".join(
            [
                f"exe_path: {exe_path}",
                f"exe_sha256({exe_path}): {sha256_file(pathlib.Path(exe_path))}",
                f"id_name: {id_name}",
                f"set_path: {O_FENS_PATH}",
                f"set_sha256({O_FENS_PATH}): {sha256_file(O_FENS_PATH)}",
                "positions: 200",
                "depth: 12",
                f"sum_nodes: {sum_nodes}",
                f"utc_completed: {utc_now()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def inject_p10_b8b_fast(tree_dir: pathlib.Path) -> None:
    # 1. include/forge/search.hpp
    shpp_p = tree_dir / "include/forge/search.hpp"
    shpp = shpp_p.read_text(encoding="utf-8")
    shpp = replace_once(
        shpp,
        "extern bool IdeaB8b;                 // seat 028 threat-role memory (false = off)\n",
        "extern bool IdeaB8b;                 // seat 028 threat-role memory (false = off)\n"
        "extern bool IdeaB8b_Fast;            // faster node-identical IdeaB8b path (false = off; inactive unless IdeaB8b is on)\n",
        "search.hpp IdeaB8b_Fast extern",
    )
    shpp = replace_once(
        shpp,
        "    mutable RoleThreatB role_b8b_threat_{};\n"
        "    mutable std::uint64_t role_b8b_key_ = 0;\n"
        "    mutable bool role_b8b_key_valid_ = false;\n",
        "    mutable RoleThreatB role_b8b_threat_{};\n"
        "    mutable std::uint64_t role_b8b_key_ = 0;\n"
        "    mutable bool role_b8b_key_valid_ = false;\n"
        "public:\n"
        "    struct B8bFastEntry {\n"
        "        std::uint64_t key = 0;\n"
        "        Bitboard occ_w = ~0ULL;\n"
        "        Bitboard occ_b = ~0ULL;\n"
        "        Bitboard between_bb = 0;\n"
        "        Bitboard attacker_bb = 0;\n"
        "        std::array<Bitboard, 7> role4_mask{};\n"
        "        std::uint8_t victim_sq = 0;\n"
        "        std::uint8_t attacker_sq = 0;\n"
        "        std::uint8_t victim_type = 0;\n"
        "        std::uint8_t attacker_type = 0;\n"
        "        bool present = false;\n"
        "    };\n"
        "    [[nodiscard]] static int role_b8b_fast(const Board& b, Piece moved_piece, Move m, const B8bFastEntry& e);\n"
        "private:\n"
        "    mutable std::array<B8bFastEntry, 256> b8b_fast_cache_{};\n"
        "    [[nodiscard]] const B8bFastEntry& ensure_b8b_fast(const Board& board) const;\n"
        "    [[nodiscard]] const B8bFastEntry* prepare_b8b_fast_scorer(const Board& board, std::array<int, 5>& scaled) const;\n"
        "    [[nodiscard]] int threat_role_b8b_bonus_fast(const Board& board, Piece piece, Move move) const;\n",
        "search.hpp B8bFastEntry decls",
    )
    shpp_p.write_text(shpp, encoding="utf-8")

    # 2. src/search.cpp
    scpp_p = tree_dir / "src/search.cpp"
    scpp = scpp_p.read_text(encoding="utf-8")

    scpp = replace_once(
        scpp,
        "bool IdeaB8b = false;\n",
        "bool IdeaB8b = false;\n"
        "bool IdeaB8b_Fast = false;\n",
        "search.cpp IdeaB8b_Fast def",
    )

    # Note: place `b8b_fast_scaled` BEFORE `b8b_fast_entry` so constructor body populates safely without order issues
    scpp = replace_once(
        scpp,
        "        int quarters;\n"
        "        bool rework;\n"
        "        bool use_threat_hist;\n"
        "\n"
        "        QuietScorer(const Board& b, const Worker& searcher, const SearchStack* ss)\n",
        "        int quarters;\n"
        "        bool rework;\n"
        "        bool use_threat_hist;\n"
        "        std::array<int, 5> b8b_fast_scaled{};\n"
        "        const Worker::B8bFastEntry* b8b_fast_entry = nullptr;\n"
        "\n"
        "        QuietScorer(const Board& b, const Worker& searcher, const SearchStack* ss)\n",
        "search.cpp QuietScorer B8bFast fields",
    )

    scpp = replace_once(
        scpp,
        "              rework(tune::HistRework != 0 && ss != nullptr),\n"
        "              use_threat_hist(tune::ThreatHistory) {}\n",
        "              rework(tune::HistRework != 0 && ss != nullptr),\n"
        "              use_threat_hist(tune::ThreatHistory) {\n"
        "            if (tune::IdeaB8b && tune::IdeaB8b_Fast) [[unlikely]] {\n"
        "                b8b_fast_entry = searcher.prepare_b8b_fast_scorer(b, b8b_fast_scaled);\n"
        "            }\n"
        "        }\n",
        "search.cpp QuietScorer ctor B8bFast",
    )

    scpp = replace_once(
        scpp,
        "            if (tune::IdeaB8b) [[unlikely]] value += worker.threat_role_b8b_bonus(board, move);\n",
        "            if (tune::IdeaB8b) [[unlikely]] {\n"
        "                if (b8b_fast_entry != nullptr) {\n"
        "                    value += b8b_fast_scaled[static_cast<std::size_t>(Worker::role_b8b_fast(board, piece, move, *b8b_fast_entry))];\n"
        "                } else if (!tune::IdeaB8b_Fast) {\n"
        "                    value += worker.threat_role_b8b_bonus(board, move);\n"
        "                }\n"
        "            }\n",
        "search.cpp QuietScorer::score B8bFast",
    )

    scpp = replace_once(
        scpp,
        "    *role_b8b_history_ = ThreatRoleHistoryB{};\n"
        "    role_b8b_key_valid_ = false;\n",
        "    *role_b8b_history_ = ThreatRoleHistoryB{};\n"
        "    role_b8b_key_valid_ = false;\n"
        "    for (auto& e : b8b_fast_cache_) e.occ_w = ~0ULL;\n",
        "search.cpp Worker::clear b8b_fast_cache_",
    )

    scpp = replace_once(
        scpp,
        "    if (tune::IdeaB8b) [[unlikely]] score += threat_role_b8b_bonus(board, move);\n",
        "    if (tune::IdeaB8b) [[unlikely]] {\n"
        "        score += tune::IdeaB8b_Fast ? threat_role_b8b_bonus_fast(board, piece, move)\n"
        "                                    : threat_role_b8b_bonus(board, move);\n"
        "    }\n",
        "search.cpp Worker::quiet_history B8bFast",
    )

    scpp = replace_once(
        scpp,
        "    if (tune::IdeaB8) update_threat_role(board, move, bonus);\n"
        "    if (tune::IdeaB8b) update_threat_role_b8b(board, move, bonus);\n"
        "#if FORGE_PAWN_HISTORY\n"
        "    update_pawn_history(board, piece, move, bonus);\n"
        "#endif\n"
        "    update_continuation(ss, piece, move.to, bonus);\n"
        "    for (int i = 0; i < quiet_count; ++i) {\n"
        "        const Move quiet = quiets[i];\n"
        "        if (quiet == move) continue;\n"
        "        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);\n"
        "        update_threat_quiet(board, quiet, -bonus);\n"
        "        if (tune::IdeaB8) update_threat_role(board, quiet, -bonus);\n"
        "        if (tune::IdeaB8b) update_threat_role_b8b(board, quiet, -bonus);\n",
        "    if (tune::IdeaB8) update_threat_role(board, move, bonus);\n"
        "    const B8bFastEntry* b8b_fast_upd = nullptr;\n"
        "    if (tune::IdeaB8b) [[unlikely]] {\n"
        "        if (tune::IdeaB8b_Fast) {\n"
        "            const B8bFastEntry& e = ensure_b8b_fast(board);\n"
        "            if (e.present) {\n"
        "                b8b_fast_upd = &e;\n"
        "                const int role = role_b8b_fast(board, piece, move, e);\n"
        "                apply_history((*role_b8b_history_)[static_cast<std::size_t>(us)][static_cast<std::size_t>(e.victim_type)]\n"
        "                                                  [static_cast<std::size_t>(e.attacker_type)][static_cast<std::size_t>(role)],\n"
        "                              bonus);\n"
        "            }\n"
        "        } else {\n"
        "            update_threat_role_b8b(board, move, bonus);\n"
        "        }\n"
        "    }\n"
        "#if FORGE_PAWN_HISTORY\n"
        "    update_pawn_history(board, piece, move, bonus);\n"
        "#endif\n"
        "    update_continuation(ss, piece, move.to, bonus);\n"
        "    for (int i = 0; i < quiet_count; ++i) {\n"
        "        const Move quiet = quiets[i];\n"
        "        if (quiet == move) continue;\n"
        "        apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);\n"
        "        update_threat_quiet(board, quiet, -bonus);\n"
        "        if (tune::IdeaB8) update_threat_role(board, quiet, -bonus);\n"
        "        if (tune::IdeaB8b) [[unlikely]] {\n"
        "            if (tune::IdeaB8b_Fast) {\n"
        "                if (b8b_fast_upd != nullptr) {\n"
        "                    const int role = role_b8b_fast(board, board.moved_piece(quiet), quiet, *b8b_fast_upd);\n"
        "                    apply_history((*role_b8b_history_)[static_cast<std::size_t>(us)][static_cast<std::size_t>(b8b_fast_upd->victim_type)]\n"
        "                                                      [static_cast<std::size_t>(b8b_fast_upd->attacker_type)][static_cast<std::size_t>(role)],\n"
        "                                  -bonus);\n"
        "                }\n"
        "            } else {\n"
        "                update_threat_role_b8b(board, quiet, -bonus);\n"
        "            }\n"
        "        }\n",
        "search.cpp Worker::update_quiet_stats B8bFast",
    )

    fast_impl = (
        "namespace {\n\n"
        "[[nodiscard]] Worker::B8bFastEntry make_b8b_fast_entry(const Board& board) {\n"
        "    Worker::B8bFastEntry e;\n"
        "    e.key = board.key();\n"
        "    e.occ_w = board.occupied(White);\n"
        "    e.occ_b = board.occupied(Black);\n"
        "    const Color us = board.side_to_move();\n"
        "    const Color them = opposite(us);\n"
        "    const Bitboard occ = e.occ_w | e.occ_b;\n"
        "    const Bitboard enemy_pawns = board.pieces(them, Pawn);\n"
        "    const Bitboard enemy_pawn_att = pawn_attacks_bb(them, enemy_pawns);\n"
        "\n"
        "    auto finish = [&](int v_sq, int v_type, int a_sq, int a_type) -> Worker::B8bFastEntry {\n"
        "        e.present = true;\n"
        "        e.victim_sq = static_cast<std::uint8_t>(v_sq);\n"
        "        e.attacker_sq = static_cast<std::uint8_t>(a_sq);\n"
        "        e.victim_type = static_cast<std::uint8_t>(v_type);\n"
        "        e.attacker_type = static_cast<std::uint8_t>(a_type);\n"
        "        e.between_bb = (a_type == Bishop || a_type == Rook || a_type == Queen)\n"
        "                           ? attacks::between(a_sq, v_sq)\n"
        "                           : 0ULL;\n"
        "        e.attacker_bb = square_bb(a_sq);\n"
        "        if (v_type != King) {\n"
        "            const Bitboard ek = board.pieces(them, King);\n"
        "            const Bitboard eqk = board.pieces(them, Queen) | ek;\n"
        "            if (v_type == Queen) {\n"
        "                e.role4_mask[Pawn] = ek;\n"
        "                e.role4_mask[Knight] = ek;\n"
        "                e.role4_mask[Bishop] = ek;\n"
        "                e.role4_mask[Rook] = ek;\n"
        "                e.role4_mask[Queen] = ek;\n"
        "            } else if (v_type == Rook) {\n"
        "                e.role4_mask[Pawn] = eqk;\n"
        "                e.role4_mask[Knight] = eqk;\n"
        "                e.role4_mask[Bishop] = eqk;\n"
        "                e.role4_mask[Rook] = eqk;\n"
        "                e.role4_mask[Queen] = ek;\n"
        "            } else {\n"
        "                const Bitboard erqk = board.pieces(them, Rook) | eqk;\n"
        "                e.role4_mask[Pawn] = erqk;\n"
        "                e.role4_mask[Knight] = erqk;\n"
        "                e.role4_mask[Bishop] = erqk;\n"
        "                e.role4_mask[Rook] = eqk;\n"
        "                e.role4_mask[Queen] = ek;\n"
        "            }\n"
        "        }\n"
        "        return e;\n"
        "    };\n"
        "\n"
        "    // 1. King victim (worth = 100000): board.checkers() is already maintained on Board.\n"
        "    if (const Bitboard chk = board.checkers(); chk != 0) {\n"
        "        const int k_sq = board.king_square(us);\n"
        "        if (k_sq >= 0) {\n"
        "            if (const Bitboard p = chk & enemy_pawns; p != 0) return finish(k_sq, King, lsb(p), Pawn);\n"
        "            if (const Bitboard nb = chk & (board.pieces(them, Knight) | board.pieces(them, Bishop)); nb != 0) {\n"
        "                const int a_sq = lsb(nb);\n"
        "                return finish(k_sq, King, a_sq, piece_type(board.piece_at(a_sq)));\n"
        "            }\n"
        "            if (const Bitboard r = chk & board.pieces(them, Rook); r != 0) return finish(k_sq, King, lsb(r), Rook);\n"
        "            if (const Bitboard q = chk & board.pieces(them, Queen); q != 0) return finish(k_sq, King, lsb(q), Queen);\n"
        "        }\n"
        "    }\n"
        "\n"
        "    // 2. Queen victim (worth = 900): strict attacker_worth order Pawn(100) -> Knight|Bishop(300) -> Rook(500).\n"
        "    if (const Bitboard queens = board.pieces(us, Queen); queens != 0) {\n"
        "        if (const Bitboard qp = queens & enemy_pawn_att; qp != 0) {\n"
        "            const int v_sq = lsb(qp);\n"
        "            return finish(v_sq, Queen, lsb(attacks::pawn(us, v_sq) & enemy_pawns), Pawn);\n"
        "        }\n"
        "        const Bitboard enemy_knights = board.pieces(them, Knight);\n"
        "        const Bitboard enemy_bishops = board.pieces(them, Bishop);\n"
        "        for (Bitboard q = queens; q != 0;) {\n"
        "            const int sq = pop_lsb(q);\n"
        "            if (const Bitboard nb = (attacks::knight(sq) & enemy_knights) | (attacks::bishop(sq, occ) & enemy_bishops); nb != 0) {\n"
        "                const int a_sq = lsb(nb);\n"
        "                return finish(sq, Queen, a_sq, piece_type(board.piece_at(a_sq)));\n"
        "            }\n"
        "        }\n"
        "        const Bitboard enemy_rooks = board.pieces(them, Rook);\n"
        "        for (Bitboard q = queens; q != 0;) {\n"
        "            const int sq = pop_lsb(q);\n"
        "            if (const Bitboard r = attacks::rook(sq, occ) & enemy_rooks; r != 0) {\n"
        "                return finish(sq, Queen, lsb(r), Rook);\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "\n"
        "    // 3. Rook victim (worth = 500): strict attacker_worth order Pawn(100) -> Knight|Bishop(300).\n"
        "    if (const Bitboard rooks = board.pieces(us, Rook); rooks != 0) {\n"
        "        if (const Bitboard rp = rooks & enemy_pawn_att; rp != 0) {\n"
        "            const int v_sq = lsb(rp);\n"
        "            return finish(v_sq, Rook, lsb(attacks::pawn(us, v_sq) & enemy_pawns), Pawn);\n"
        "        }\n"
        "        const Bitboard enemy_knights = board.pieces(them, Knight);\n"
        "        const Bitboard enemy_bishops = board.pieces(them, Bishop);\n"
        "        for (Bitboard r = rooks; r != 0;) {\n"
        "            const int sq = pop_lsb(r);\n"
        "            if (const Bitboard nb = (attacks::knight(sq) & enemy_knights) | (attacks::bishop(sq, occ) & enemy_bishops); nb != 0) {\n"
        "                const int a_sq = lsb(nb);\n"
        "                return finish(sq, Rook, a_sq, piece_type(board.piece_at(a_sq)));\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "\n"
        "    // 4. Minor victim (Knight|Bishop, worth = 300): attacker Pawn(100).\n"
        "    if (const Bitboard mp = (board.pieces(us, Knight) | board.pieces(us, Bishop)) & enemy_pawn_att; mp != 0) {\n"
        "        const int v_sq = lsb(mp);\n"
        "        return finish(v_sq, piece_type(board.piece_at(v_sq)), lsb(attacks::pawn(us, v_sq) & enemy_pawns), Pawn);\n"
        "    }\n"
        "\n"
        "    return e;\n"
        "}\n\n"
        "} // namespace\n\n"
        "int Worker::role_b8b_fast(const Board& b, Piece moved_piece, Move m, const B8bFastEntry& e) {\n"
        "    if (m.from == e.victim_sq) return 1;\n"
        "    if ((e.between_bb & square_bb(m.to)) != 0) return 2;\n"
        "    const int mover = piece_type(moved_piece);\n"
        "    const Bitboard occ = b.occupied() ^ square_bb(m.from);\n"
        "    Bitboard hits = 0;\n"
        "    switch (mover) {\n"
        "    case Pawn: hits = attacks::pawn(b.side_to_move(), m.to); break;\n"
        "    case Knight: hits = attacks::knight(m.to); break;\n"
        "    case Bishop: hits = attacks::bishop(m.to, occ); break;\n"
        "    case Rook: hits = attacks::rook(m.to, occ); break;\n"
        "    case Queen: hits = attacks::queen(m.to, occ); break;\n"
        "    case King: hits = attacks::king(m.to); break;\n"
        "    default: return 0;\n"
        "    }\n"
        "    if ((hits & e.attacker_bb) != 0) return 3;\n"
        "    if ((hits & e.role4_mask[static_cast<std::size_t>(mover)]) != 0) return 4;\n"
        "    return 0;\n"
        "}\n\n"
        "const Worker::B8bFastEntry& Worker::ensure_b8b_fast(const Board& board) const {\n"
        "    const std::uint64_t key = board.key();\n"
        "    B8bFastEntry& slot = b8b_fast_cache_[static_cast<std::size_t>(key & 255ULL)];\n"
        "    if (slot.key == key && slot.occ_w == board.occupied(White) && slot.occ_b == board.occupied(Black)) {\n"
        "        return slot;\n"
        "    }\n"
        "    slot = make_b8b_fast_entry(board);\n"
        "    return slot;\n"
        "}\n\n"
        "const Worker::B8bFastEntry* Worker::prepare_b8b_fast_scorer(const Board& board, std::array<int, 5>& scaled) const {\n"
        "    const B8bFastEntry& e = ensure_b8b_fast(board);\n"
        "    if (!e.present) return nullptr;\n"
        "    const auto& row = (*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())]\n"
        "                                          [static_cast<std::size_t>(e.victim_type)]\n"
        "                                          [static_cast<std::size_t>(e.attacker_type)];\n"
        "    const int w = tune::IdeaB8b_Weight;\n"
        "    for (std::size_t r = 0; r < 5; ++r) {\n"
        "        scaled[r] = row[r] * w / 1024;\n"
        "    }\n"
        "    return &e;\n"
        "}\n\n"
        "int Worker::threat_role_b8b_bonus_fast(const Board& board, Piece piece, Move move) const {\n"
        "    const B8bFastEntry& e = ensure_b8b_fast(board);\n"
        "    if (!e.present) return 0;\n"
        "    const int role = role_b8b_fast(board, piece, move, e);\n"
        "    const int raw = (*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())]\n"
        "                                        [static_cast<std::size_t>(e.victim_type)]\n"
        "                                        [static_cast<std::size_t>(e.attacker_type)]\n"
        "                                        [static_cast<std::size_t>(role)];\n"
        "    return raw * tune::IdeaB8b_Weight / 1024;\n"
        "}\n\n"
    )

    scpp = replace_once(
        scpp,
        "const Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {\n",
        fast_impl + "const Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {\n",
        "search.cpp B8bFast helpers",
    )

    scpp = replace_once(
        scpp,
        "int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8b) return 0;\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n",
        "int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8b) return 0;\n"
        "    if (tune::IdeaB8b_Fast) return threat_role_b8b_bonus_fast(board, board.piece_at(move.from), move);\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n",
        "search.cpp threat_role_b8b_bonus fast branch",
    )

    scpp = replace_once(
        scpp,
        "void Worker::update_threat_role_b8b(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8b) return;\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n",
        "void Worker::update_threat_role_b8b(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8b) return;\n"
        "    if (tune::IdeaB8b_Fast) {\n"
        "        const B8bFastEntry& e = ensure_b8b_fast(board);\n"
        "        if (!e.present) return;\n"
        "        const int role = role_b8b_fast(board, board.piece_at(move.from), move, e);\n"
        "        apply_history((*role_b8b_history_)[static_cast<std::size_t>(board.side_to_move())][static_cast<std::size_t>(e.victim_type)]\n"
        "                                          [static_cast<std::size_t>(e.attacker_type)][static_cast<std::size_t>(role)],\n"
        "                      bonus);\n"
        "        return;\n"
        "    }\n"
        "    const RoleThreatB& threat = role_b8b_threat(board);\n",
        "search.cpp update_threat_role_b8b fast branch",
    )
    scpp_p.write_text(scpp, encoding="utf-8")

    # 3. src/uci.cpp
    ucpp_p = tree_dir / "src/uci.cpp"
    ucpp = ucpp_p.read_text(encoding="utf-8")
    ucpp = replace_once(
        ucpp,
        '                         "option name IdeaB8b type check default false\\n"\n',
        '                         "option name IdeaB8b type check default false\\n"\n'
        '                         "option name IdeaB8b_Fast type check default false\\n"\n',
        "uci.cpp IdeaB8b_Fast decl",
    )
    ucpp = replace_once(
        ucpp,
        '            } else if (name == "IdeaB8b") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
        '                else note_invalid();\n',
        '            } else if (name == "IdeaB8b") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
        '                else note_invalid();\n'
        '            } else if (name == "IdeaB8b_Fast") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b_Fast = value_text == "true";\n'
        '                else note_invalid();\n',
        "uci.cpp IdeaB8b_Fast setoption",
    )
    ucpp_p.write_text(ucpp, encoding="utf-8")


def parse_seta_rows(path: pathlib.Path) -> list[str]:
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#") and not ln.startswith("attempt\t")]


def run_timed_o_d12(
    exe_path: str,
    run_idx: int,
    pass_tag: str,
    setting_name: str,
    extra_opts: list[tuple[str, str]],
    fens: list[str],
    ref_rows: list[tuple[int, int, str, str]],
    cpu_pin: int = 1,
) -> dict:
    opt_lines = pc20_option_lines(extra_opts)
    proc = subprocess.Popen(
        ["taskset", "-c", str(cpu_pin), exe_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline().rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    rows: list[tuple[int, int, int, str, str]] = []
    cmp_rows: list[tuple[int, int, str, str]] = []
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write("ucinewgame\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass
        proc.stdin.write(f"position fen {fen}\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass

        last_nodes = None
        last_score = ""
        bestmove = None
        t0_ns = time.perf_counter_ns()
        proc.stdin.write("go depth 12\n")
        proc.stdin.flush()
        while True:
            ln = proc.stdout.readline()
            if not ln:
                raise RuntimeError(f"EOF at pos {idx}")
            if ln.startswith("bestmove "):
                t1_ns = time.perf_counter_ns()
                bestmove = ln.split()[1]
                break
            if ln.startswith("info ") and " nodes " in ln:
                toks = ln.split()
                last_nodes = int(toks[toks.index("nodes") + 1])
                if "score" in toks:
                    si = toks.index("score")
                    last_score = f"{toks[si + 1]} {toks[si + 2]}"
        assert last_nodes is not None and bestmove is not None
        rows.append((idx, last_nodes, t1_ns - t0_ns, bestmove, last_score))
        cmp_rows.append((idx, last_nodes, bestmove, last_score))

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    assert rc == 0 and not stderr_txt

    d_cmp, _ = diff_breakdown_with_samples(cmp_rows, ref_rows, setting_name, "ref")
    node_sum = sum(r[1] for r in rows)
    wall_ns = sum(r[2] for r in rows)
    wall_s = wall_ns / 1e9
    wall_ms = wall_ns / 1e6
    ms_per_1k = wall_ms / (node_sum / 1000.0)
    us_per_1k = (wall_ns / 1e3) / (node_sum / 1000.0)

    stem = f"P10d_partT_{run_idx:02d}_{pass_tag}_{setting_name}"
    rows_path = JOB45 / f"{stem}.rows.txt"
    meta_path = JOB45 / f"{stem}.rows.txt.meta"
    hdr = [
        f"# run={run_idx:02d} pass={pass_tag} setting={setting_name} positions={len(rows)} depth=12 "
        f"node_sum={node_sum} wall_ns_sum={wall_ns} wall_ms={wall_ms:.3f} ms_per_1000_nodes={ms_per_1k:.6f}",
        "position\tnodes\twall_ns\tbestmove\tscore",
    ]
    rows_path.write_text(
        "\n".join(hdr + [f"{p}\t{nd}\t{w}\t{bm}\t{sc}" for p, nd, w, bm, sc in rows]) + "\n",
        encoding="utf-8",
    )
    meta_path.write_text(
        "\n".join(
            [
                f"run_id: {stem}",
                f"exe_path: {exe_path}",
                f"exe_sha256({exe_path}): {sha256_file(pathlib.Path(exe_path))}",
                f"id_name: {id_name}",
                f"cpu_pin: {cpu_pin}",
                f"set_path: {O_FENS_PATH}",
                f"set_sha256({O_FENS_PATH}): {sha256_file(O_FENS_PATH)}",
                "positions: 200",
                f"equal_positions_vs_ref: {d_cmp['equal']}",
                "depth: 12",
                f"node_sum: {node_sum}",
                f"wall_ns_sum: {wall_ns}",
                f"wall_s: {wall_s:.6f}",
                f"ms_per_1000_nodes: {ms_per_1k:.6f}",
                f"us_per_1000_nodes: {us_per_1k:.3f}",
                "options_sent_begin:",
                *[f"  {o}" for o in opt_lines],
                "options_sent_end",
                f"utc_completed: {utc_now()}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "stem": stem,
        "pass": pass_tag,
        "setting": setting_name,
        "node_sum": node_sum,
        "equal_pos": d_cmp["equal"],
        "wall_s": wall_s,
        "ms_per_1k": ms_per_1k,
        "us_per_1k": us_per_1k,
    }


def main() -> int:
    start_u = utc_now()
    out_lines = [
        "=== JOB 45 PART P10: AN IdeaB8b THAT COSTS LESS, WITH EVERY NODE EQUAL (P10a..P10d) ===",
        f"start_utc: {start_u}",
        "",
        "--- 1. P10a: Scratch Counter Build on Copy of Bundle8 (/tmp/carbon2_job45/bld_p10_counter/forge) ---",
    ]
    all_ok = True

    # P10a: Scratch counter build
    cnt_exe_path = WORK45 / "bld_p10_counter/forge"
    raw_cnt_path = JOB45 / "P10a_B8b_counters_O_d12.raw.txt"
    if cnt_exe_path.exists() and raw_cnt_path.exists():
        cnt_exe = str(cnt_exe_path)
        cnt_sha = sha256_file(cnt_exe_path)
        cnt_cf = "(built from fresh bundle8 + inject_p10a_counters in /tmp/carbon2_job45/src_p10_counter)"
        cnt_lf = "(lld-18 ThinLTO Release link into /tmp/carbon2_job45/bld_p10_counter/forge)"
    else:
        src_cnt = WORK45 / "src_p10_counter"
        ok_c, _ = apply_bundle8_to_fresh_v3(src_cnt)
        assert ok_c
        inject_p10a_counters(src_cnt)
        cnt_exe, cnt_sha, cnt_cf, cnt_lf = build_release_v3(src_cnt, WORK45 / "bld_p10_counter")
        only_b8b_8 = [(o, "true" if o == "IdeaB8b" else "false") for o in EIGHT_SWITCH_NAMES] + [("HindsightDepth", "false")]
        run_p10a_counter_o_d12(
            cnt_exe,
            only_b8b_8,
            raw_cnt_path,
            JOB45 / "P10a_B8b_counters_O_d12.raw.txt.meta",
        )
    out_lines.append(f"  counter exe path                            : {cnt_exe}")
    out_lines.append(f"  counter exe sha256({cnt_exe}) : {cnt_sha}")
    out_lines.append(f"  counter exe id name                         : {get_id_name(cnt_exe)}")
    sum_res = subprocess.run([sys.executable, str(JOB45 / "sum_p10_counters.py")], text=True, capture_output=True, check=False)
    out_lines.append(sum_res.stdout.rstrip())
    if sum_res.returncode != 0:
        out_lines.append("  WARNING: P10a counter build differed from clean build -> stopping P10a only; P10b..P10d continue.")
        all_ok = False

    # P10b: Generate job45/P10_B8b_fast.patch.txt on top of bundle8 and build bld_bundle8_p10
    out_lines.append("")
    out_lines.append("--- 2. P10b: Emit job45/P10_B8b_fast.patch.txt on Top of Bundle8 & Build (/tmp/carbon2_job45/bld_bundle8_p10/forge) ---")
    base_b8 = WORK45 / "src_p10_base_bundle8"
    gen_p10 = WORK45 / "src_p10_gen_b8bfast"
    ok_b, _ = apply_bundle8_to_fresh_v3(base_b8)
    assert ok_b
    if gen_p10.exists():
        shutil.rmtree(gen_p10)
    shutil.copytree(base_b8, gen_p10)
    inject_p10_b8b_fast(gen_p10)

    raw_diff_path = WORK45 / "tmp_raw_p10.patch"
    generate_diff_u_patch(base_b8, gen_p10, raw_diff_path)
    header = (
        "# P10_B8b_fast.patch.txt — IdeaB8b_Fast (option name IdeaB8b_Fast type check default false; inactive unless IdeaB8b is on)\n"
        f"# Applies to tree: bundle8 = r15d + v3 ({TPL_V3})\n"
        f"#   + forge-combo29/carbon2/job41/bundle_grok7.patch.txt (sha256 = {EXP_BUNDLE7_SHA})\n"
        f"#   + forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt (sha256 = {EXP_P8_HOIST_SHA})\n"
    )
    p10_patch_path = JOB45 / "P10_B8b_fast.patch.txt"
    p10_patch_path.write_text(header + raw_diff_path.read_text(encoding="utf-8"), encoding="utf-8")

    p10_bytes = p10_patch_path.read_bytes()
    p10_crlf = p10_bytes.count(b"\r\n")
    p10_sha = sha256_file(p10_patch_path)
    p10_nlines = len(p10_bytes.splitlines())

    src_p10 = WORK45 / "src_bundle8_p10"
    ok_p10_base, _ = apply_bundle8_to_fresh_v3(src_p10)
    assert ok_p10_base
    chk = subprocess.run(["git", "apply", "--check", "-p1", str(p10_patch_path)], cwd=str(src_p10), capture_output=True, text=True)
    ok_chk, s_chk = fmt_cmp("P10_B8b_fast.patch.txt git apply --check -p1 on bundle8", chk.returncode, 0)
    ok_lf, s_lf = fmt_cmp("P10_B8b_fast.patch.txt CRLF count", p10_crlf, 0)
    all_ok = all_ok and ok_chk and ok_lf
    out_lines.extend(
        [
            s_lf,
            s_chk,
            f"  patch path                                  : {p10_patch_path}",
            f"  patch lines({p10_patch_path}) : {p10_nlines}",
            f"  patch sha256({p10_patch_path}) : {p10_sha}",
        ]
    )
    subprocess.run(["git", "apply", "-p1", str(p10_patch_path)], cwd=str(src_p10), check=True)

    p10_exe, p10_sha_exe, p10_cf, p10_lf = build_release_v3(src_p10, WORK45 / "bld_bundle8_p10")
    out_lines.append(f"  bundle8_p10 exe path                        : {p10_exe}")
    out_lines.append(f"  bundle8_p10 exe sha256({p10_exe}) : {p10_sha_exe}")
    out_lines.append(f"  bundle8_p10 id name                         : {get_id_name(p10_exe)}")

    for uopt in ["IdeaB8b_Fast", "IdeaB8b", "IdeaB8", "HindsightDepth", "IdeaS13_Hoist"]:
        ok_u, u_lines = verify_uci_option_check(p10_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    # P10c: Identity & Known Answers
    out_lines.append("")
    out_lines.append("--- 3. P10c: All-OFF, IdeaB8b_Fast-Alone=OFF, and Exact Identity (IdeaB8b + IdeaB8b_Fast == IdeaB8b Alone on O, G, Set A Line L) ---")
    ok_def, def_lines = verify_all_off_numbers("bundle8_p10_default_off", p10_exe, None)
    ok_exp, exp_lines = verify_all_off_numbers("bundle8_p10_explicit_9_false", p10_exe, ALL_NINE_P10_FALSE)
    b13_f = run_fresh_bench(
        p10_exe, 13,
        ["setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false"]
        + [f"setoption name {k} value {v}" for k, v in ALL_NINE_P10_FALSE]
        + ["setoption name HindsightDepth value false"],
    )
    b13_t = run_fresh_bench(
        p10_exe, 13,
        ["setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false"]
        + [f"setoption name {k} value {v}" for k, v in ALL_NINE_P10_FALSE]
        + ["setoption name HindsightDepth value true"],
    )
    ok_k1, s_k1 = fmt_cmp("bundle8_p10 no-PC20 HindsightDepth=false bench 13", b13_f, EXP_NOPC20_HD_FALSE_BENCH13)
    ok_k2, s_k2 = fmt_cmp("bundle8_p10 no-PC20 HindsightDepth=true bench 13", b13_t, EXP_NOPC20_HD_TRUE_BENCH13)
    all_ok = all_ok and ok_def and ok_exp and ok_k1 and ok_k2
    out_lines.extend(def_lines + exp_lines + [s_k1, s_k2])

    ref_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    fast_only_opts = [(o, "true" if o == "IdeaB8b_Fast" else "false") for o in P10_SWITCH_NAMES] + [("HindsightDepth", "false")]
    fast_only_o = run_epd_depth12(
        p10_exe, O_FENS_PATH, fast_only_opts,
        JOB45 / "P10c_only_IdeaB8b_Fast_B8b_off_O_d12.rows.txt",
        JOB45 / "P10c_only_IdeaB8b_Fast_B8b_off_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    d_fo, _ = diff_breakdown_with_samples(fast_only_o, ref_off_o, "only_B8b_Fast", "OFF_O")

    only_b8b_opts = [(o, "true" if o == "IdeaB8b" else "false") for o in P10_SWITCH_NAMES] + [("HindsightDepth", "false")]
    b8b_plus_fast_opts = [(o, "true" if o in ("IdeaB8b", "IdeaB8b_Fast") else "false") for o in P10_SWITCH_NAMES] + [("HindsightDepth", "false")]

    b8b_o = run_epd_depth12(
        p10_exe, O_FENS_PATH, only_b8b_opts,
        JOB45 / "P10c_only_B8b_O_d12.rows.txt",
        JOB45 / "P10c_only_B8b_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    b8bf_o = run_epd_depth12(
        p10_exe, O_FENS_PATH, b8b_plus_fast_opts,
        JOB45 / "P10c_B8b_and_B8b_Fast_O_d12.rows.txt",
        JOB45 / "P10c_B8b_and_B8b_Fast_O_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )

    b8b_g = run_epd_depth12(
        p10_exe, G_EPD_PATH, only_b8b_opts,
        JOB45 / "P10c_only_B8b_G_d12.rows.txt",
        JOB45 / "P10c_only_B8b_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )
    b8bf_g = run_epd_depth12(
        p10_exe, G_EPD_PATH, b8b_plus_fast_opts,
        JOB45 / "P10c_B8b_and_B8b_Fast_G_d12.rows.txt",
        JOB45 / "P10c_B8b_and_B8b_Fast_G_d12.rows.txt.meta",
        depth=12, cpu_pin=1,
    )

    j41_b8b_o = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt")
    j41_b8b_g = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_G_d12.rows.txt")

    d_b8b_j41_o, _ = diff_breakdown_with_samples(b8b_o, j41_b8b_o, "p10_B8b_O", "J41_P7_O")
    d_b8b_j41_g, _ = diff_breakdown_with_samples(b8b_g, j41_b8b_g, "p10_B8b_G", "J41_P7_G")
    d_fast_o, _ = diff_breakdown_with_samples(b8bf_o, b8b_o, "B8b+Fast_O", "B8b_alone_O")
    d_fast_g, _ = diff_breakdown_with_samples(b8bf_g, b8b_g, "B8b+Fast_G", "B8b_alone_G")

    seta_b8b = run_selfgame_set_with_options(p10_exe, "carbon2-job33-a", 200, None, extra_opts=only_b8b_opts, cpu_pin=1)
    seta_b8b_path = JOB45 / "P10c_only_B8b_SetA_L.rows.txt"
    write_v2_v3_rows(seta_b8b_path, "Job 45 Part P10c bundle8_p10 IdeaB8b alone Set A line L (built-in eval, PC20)", seta_b8b)
    write_seta_meta(JOB45 / "P10c_only_B8b_SetA_L.rows.txt.meta", p10_exe, only_b8b_opts, seta_b8b)

    seta_b8bf = run_selfgame_set_with_options(p10_exe, "carbon2-job33-a", 200, None, extra_opts=b8b_plus_fast_opts, cpu_pin=1)
    seta_b8bf_path = JOB45 / "P10c_B8b_and_B8b_Fast_SetA_L.rows.txt"
    write_v2_v3_rows(seta_b8bf_path, "Job 45 Part P10c bundle8_p10 IdeaB8b + IdeaB8b_Fast Set A line L (built-in eval, PC20)", seta_b8bf)
    write_seta_meta(JOB45 / "P10c_B8b_and_B8b_Fast_SetA_L.rows.txt.meta", p10_exe, b8b_plus_fast_opts, seta_b8bf)

    j41_seta_rows = parse_seta_rows(JOB41 / "P7_bundle7_only_B8b_SetA_L.rows.txt")
    p10_seta_b8b_rows = parse_seta_rows(seta_b8b_path)
    p10_seta_b8bf_rows = parse_seta_rows(seta_b8bf_path)
    eq_seta_j41 = sum(1 for a, b in zip(p10_seta_b8bf_rows, j41_seta_rows) if a == b)
    eq_seta_pair = sum(1 for a, b in zip(p10_seta_b8bf_rows, p10_seta_b8b_rows) if a == b)

    identity_ok = True
    for lbl, got, exp in [
        ("IdeaB8b_Fast=true (IdeaB8b=false) O sum vs OFF O", sum(r[1] for r in fast_only_o), EXP_OFF_O_SUM),
        ("IdeaB8b_Fast=true (IdeaB8b=false) O equal pos vs OFF O", d_fo["equal"], 200),
        ("bundle8_p10 only_B8b O equal pos vs J41 P7 O", d_b8b_j41_o["equal"], 200),
        ("bundle8_p10 only_B8b G equal pos vs J41 P7 G", d_b8b_j41_g["equal"], 353),
        ("B8b+B8b_Fast vs only_B8b O sum_nodes", sum(r[1] for r in b8bf_o), EXP_B8B_O_SUM),
        ("B8b+B8b_Fast vs only_B8b O equal positions", d_fast_o["equal"], 200),
        ("B8b+B8b_Fast vs only_B8b G sum_nodes", sum(r[1] for r in b8bf_g), EXP_B8B_G_SUM),
        ("B8b+B8b_Fast vs only_B8b G equal positions", d_fast_g["equal"], 353),
        ("B8b+B8b_Fast Set A line L records vs J41 P7 known answer", seta_b8bf.total_records, EXP_B8B_SETA_L_RECORDS),
        ("B8b+B8b_Fast Set A line L searches vs J41 P7 known answer", seta_b8bf.total_searches, EXP_B8B_SETA_L_SEARCHES),
        ("B8b+B8b_Fast Set A line L nodes vs J41 P7 known answer", seta_b8bf.total_nodes, EXP_B8B_SETA_L_NODES),
        ("B8b+B8b_Fast Set A line L full_sha256 vs J41 P7 known answer", seta_b8bf.full_sha256, EXP_B8B_SETA_L_SHA),
        ("B8b+B8b_Fast Set A line L equal attempts vs only_B8b", eq_seta_pair, 200),
        ("B8b+B8b_Fast Set A line L equal attempts vs J41 P7", eq_seta_j41, 200),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        identity_ok = identity_ok and ok
        all_ok = all_ok and ok
        out_lines.append(s)

    if not identity_ok:
        for a, b in zip(fast_only_o, ref_off_o):
            if a != b:
                out_lines.append(f"  FIRST DIFF (Fast_alone vs OFF_O): pos {a[0]} got={a} vs exp={b}")
                break
        for a, b in zip(b8bf_o, b8b_o):
            if a != b:
                out_lines.append(f"  FIRST DIFF (B8b+Fast vs B8b on O): pos {a[0]} got={a} vs exp={b}")
                break
        for a, b in zip(b8bf_g, b8b_g):
            if a != b:
                out_lines.append(f"  FIRST DIFF (B8b+Fast vs B8b on G): pos {a[0]} got={a} vs exp={b}")
                break
        for idx, (a, b) in enumerate(zip(p10_seta_b8bf_rows, p10_seta_b8b_rows), start=1):
            if a != b:
                out_lines.append(f"  FIRST DIFF (B8b+Fast vs B8b on Set A): attempt {idx} got={a} vs exp={b}")
                break
        out_lines.append("  STOPPING PART P10 BEFORE P10d TIMING PER FILE 45 LINE 90.")
        (JOB45 / "P10_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        print("\n".join(out_lines))
        return 1

    # P10d: Times on O depth 12, pinned core 1, forward (01..04) then reverse (05..08)
    out_lines.append("")
    out_lines.append("--- 4. P10d: Part T Cost per 1,000 Nodes (Forward + Reverse, Pinned Core 1, O Set Depth 12, PC20) ---")
    fens = load_fens(O_FENS_PATH)
    all_off_10 = ALL_NINE_P10_FALSE + [("HindsightDepth", "false")]
    fwd_settings = [
        ("all_off_1", all_off_10),
        ("all_off_2", all_off_10),
        ("only_B8b", only_b8b_opts),
        ("B8b_and_B8b_Fast", b8b_plus_fast_opts),
    ]
    rev_settings = list(reversed(fwd_settings))
    refs = {
        "all_off_1": ref_off_o,
        "all_off_2": ref_off_o,
        "only_B8b": b8b_o,
        "B8b_and_B8b_Fast": b8b_o,
    }
    exp_sums = {
        "all_off_1": EXP_OFF_O_SUM,
        "all_off_2": EXP_OFF_O_SUM,
        "only_B8b": EXP_B8B_O_SUM,
        "B8b_and_B8b_Fast": EXP_B8B_O_SUM,
    }

    # 1s warm-up on pinned CPU 1 before Run 01
    subprocess.run(["taskset", "-c", "1", p10_exe], input="uci\nisready\nbench 12\nquit\n", text=True, capture_output=True, check=True)

    schedule = [("fwd", k, v) for k, v in fwd_settings] + [("rev", k, v) for k, v in rev_settings]
    t_results: list[dict] = []
    for idx, (ptag, sname, sopts) in enumerate(schedule, start=1):
        r = run_timed_o_d12(p10_exe, idx, ptag, sname, sopts, fens, refs[sname], cpu_pin=1)
        t_results.append(r)
        ok_n, s_n = fmt_cmp(f"{r['stem']} node_sum", r["node_sum"], exp_sums[sname])
        ok_p, s_p = fmt_cmp(f"{r['stem']} equal_pos", r["equal_pos"], 200)
        all_ok = all_ok and ok_n and ok_p
        out_lines.extend([s_n, s_p])

    off_runs = [r for r in t_results if r["setting"].startswith("all_off")]
    fwd_off = [r for r in off_runs if r["pass"] == "fwd"]
    rev_off = [r for r in off_runs if r["pass"] == "rev"]
    mean_off_4 = statistics.mean(r["ms_per_1k"] for r in off_runs)
    mean_off_fwd = statistics.mean(r["ms_per_1k"] for r in fwd_off)
    mean_off_rev = statistics.mean(r["ms_per_1k"] for r in rev_off)

    t_lines = [
        "=== JOB 45 PART P10d: COST PER 1,000 NODES (O Set, 200 FENs, Depth 12, PC20, Built-in Eval, Pinned Core 1) ===",
        f"exe_path: {p10_exe}",
        f"exe_sha256({p10_exe}): {p10_sha_exe}",
        "variant_scope: IdeaB8b_Fast covers IdeaB8b (028) only; it does nothing unless IdeaB8b is on.",
        f"mean_all_off_4_runs  : {mean_off_4:.6f} ms / 1,000 nodes ({mean_off_4 * 1000.0:.3f} us / 1,000 nodes)",
        f"mean_all_off_forward : {mean_off_fwd:.6f} ms / 1,000 nodes",
        f"mean_all_off_reverse : {mean_off_rev:.6f} ms / 1,000 nodes",
        f"drift (rev / fwd)    : {mean_off_rev / mean_off_fwd:.6f}",
        "",
        "--- All 8 Runs in Execution Order (Forward 01..04, Reverse 05..08) ---",
        "  run_id                                   | pass | setting          | node_sum | wall_s  | ms/1k_nodes | us/1k_nodes | ratio_vs_mean4",
        "  -----------------------------------------+------+------------------+----------+---------+-------------+-------------+---------------",
    ]
    for r in t_results:
        t_lines.append(
            f"  {r['stem']:<40s} | {r['pass']:<4s} | {r['setting']:<16s} | {r['node_sum']:>8d} | "
            f"{r['wall_s']:>7.4f} | {r['ms_per_1k']:>11.6f} | {r['us_per_1k']:>11.3f} | {r['ms_per_1k'] / mean_off_4:>13.6f}"
        )

    t_lines.extend(
        [
            "",
            "--- Forward + Reverse Paired Means per Setting ---",
            "  setting          | node_sum | fwd_ms/1k  | rev_ms/1k  | mean_ms/1k | mean_us/1k | ratio_vs_all_off",
            "  -----------------+----------+------------+------------+------------+------------+-----------------",
        ]
    )
    paired_ms1k: dict[str, float] = {}
    for sname, _ in fwd_settings:
        rf = next(r for r in t_results if r["pass"] == "fwd" and r["setting"] == sname)
        rr = next(r for r in t_results if r["pass"] == "rev" and r["setting"] == sname)
        m_ms = 0.5 * (rf["ms_per_1k"] + rr["ms_per_1k"])
        m_us = 0.5 * (rf["us_per_1k"] + rr["us_per_1k"])
        paired_ms1k[sname] = m_ms
        t_lines.append(
            f"  {sname:<16s} | {rf['node_sum']:>8d} | {rf['ms_per_1k']:>10.6f} | {rr['ms_per_1k']:>10.6f} | "
            f"{m_ms:>10.6f} | {m_us:>10.3f} | {m_ms / mean_off_4:>15.6f}"
        )

    b8b_fast_over_b8b = paired_ms1k["B8b_and_B8b_Fast"] / paired_ms1k["only_B8b"]
    two_off_spread_pct = 100.0 * abs(paired_ms1k["all_off_1"] - paired_ms1k["all_off_2"]) / mean_off_4
    b8b_overhead_saved_pct = 100.0 * (paired_ms1k["only_B8b"] - paired_ms1k["B8b_and_B8b_Fast"]) / max(1e-9, paired_ms1k["only_B8b"] - mean_off_4)
    pred2_ok = 0.945 <= b8b_fast_over_b8b <= 0.988
    t_lines.extend(
        [
            "",
            f"  TWO ALL-OFF PAIRS SPREAD: all_off_1={paired_ms1k['all_off_1']:.6f} vs all_off_2={paired_ms1k['all_off_2']:.6f} ms/1k (diff={two_off_spread_pct:.2f}%)",
            f"  KEY RATIO: (IdeaB8b + IdeaB8b_Fast) / (IdeaB8b alone) = {paired_ms1k['B8b_and_B8b_Fast']:.6f} / {paired_ms1k['only_B8b']:.6f} = {b8b_fast_over_b8b:.6f}",
            f"  Incremental IdeaB8b overhead vs all_off cut by        : {b8b_overhead_saved_pct:.2f}% (from +{(paired_ms1k['only_B8b'] / mean_off_4 - 1.0) * 100.0:.2f}% to +{(paired_ms1k['B8b_and_B8b_Fast'] / mean_off_4 - 1.0) * 100.0:.2f}%)",
            f"  PREDICTION (2) CHECK: observed {b8b_fast_over_b8b:.6f} vs predicted 0.962 [0.945, 0.988] -> {'TRUE' if pred2_ok else 'FALSE'}",
        ]
    )

    (JOB45 / "P10d_timing_summary.txt").write_text("\n".join(t_lines) + "\n", encoding="utf-8")
    out_lines.append("\n".join(t_lines))

    with open(JOB45 / "builds.txt", "a", encoding="utf-8") as bf:
        bf.write(
            "\n=== PART P10a SCRATCH COUNTER BUILD (NOT used for bundle rows or games) ===\n"
            f"   exe path = {cnt_exe}\n"
            f"   exe sha256({cnt_exe}) = {cnt_sha}\n"
            f"   id_name = {get_id_name(cnt_exe)}\n"
            f"   compile_flags = {cnt_cf}\n"
            f"   link_flags    = {cnt_lf}\n\n"
            "=== PART P10b..d BUNDLE8_P10 BUILD (bundle8 + job45/P10_B8b_fast.patch.txt) ===\n"
            f"   patch path = {p10_patch_path}\n"
            f"   patch lines({p10_patch_path}) = {p10_nlines}\n"
            f"   patch sha256({p10_patch_path}) = {p10_sha}\n"
            f"   exe path = {p10_exe}\n"
            f"   exe sha256({p10_exe}) = {p10_sha_exe}\n"
            f"   id_name = {get_id_name(p10_exe)}\n"
            f"   compile_flags = {p10_cf}\n"
            f"   link_flags    = {p10_lf}\n"
        )

    ok_ov, s_ov = fmt_cmp("PART P10 OVERALL", 1 if all_ok else 0, 1)
    out_lines.append("")
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")
    (JOB45 / "P10_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
