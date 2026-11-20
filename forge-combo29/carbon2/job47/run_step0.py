#!/usr/bin/env python3
"""
Job 47 Step 0 (`run_step0.py`):
1. Tests `git apply --check -p1 job45/P10_B8b_fast.patch.txt` on fresh `bundle9` (`/tmp/carbon2_job47/src_bundle9`);
   since `P10_B8b_fast.patch.txt` was diffed on `bundle8` (without `P9_B8_fast.patch.txt`), rebases ONLY the
   adjacent `IdeaB8_Fast` context lines onto `bundle9` as `job47/P10_on_bundle9.patch.txt`, proves `git apply --check -p1`
   passes (`0 == 0`) on fresh `bundle9`, and builds `bundle10` (`/tmp/carbon2_job47/bld_bundle10/forge`).
2. Enforces strict Job 47 option-list & pre-`readyok` checking on every runner.
3. Verifies:
   - `r15d + v3` source hashes + plain `r15d + v3` pins (`312866 / 862329 / 4865609`, `PC20`, `HindsightDepth` `bench 13 = 840387 / 862329`).
   - Reused `bundle9` (`9441524d...`): `PC20` OFF `O = 8,315,168` (`200 == 200`), `G = 17,611,204` (`353 == 353`),
     `IdeaB8b` alone `O = 8,483,711` (`200 == 200`), `HindsightDepth` `bench 13 = 840387 / 862329`,
     `IdeaS10` alone `O = 8,314,153` (`200 == 200`), `IdeaS13` alone `O = 8,077,984` (`200 == 200`).
   - Fresh `bundle10`:
     * All 11 switches off = every OFF number (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`, `Set A line L`,
       `n[1..60]`, `O = 8,315,168` `200 == 200`, `G = 17,611,204` `353 == 353`, `HindsightDepth` `840387 / 862329`).
     * `IdeaB8b + IdeaB8b_Fast` equals `IdeaB8b` alone on `O` position by position (`8,483,711`, `200 == 200` vs
       `job45/P10c_only_B8b_O_d12.rows.txt` and `job45/P10c_B8b_and_B8b_Fast_O_d12.rows.txt`).
     * `IdeaB8 + IdeaB8_Fast` equals `IdeaB8` alone on `O` position by position (`8,262,696`, `200 == 200` vs
       `job43/P9c_only_B8_O_d12.rows.txt` and `job43/P9c_B8_and_B8_Fast_O_d12.rows.txt`).
"""
from __future__ import annotations

import concurrent.futures
import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j47_lib import (  # noqa: E402
    ALL_ELEVEN_FALSE,
    ALL_NINE_IDEA_FALSE,
    ALL_TEN_FALSE,
    ALL_TEN_IDEA_FALSE,
    BUNDLE7_PATCH,
    EXP_B8B_O_SUM,
    EXP_B8_O_SUM,
    EXP_BASE_V3_SHA,
    EXP_BUNDLE7_SHA,
    EXP_BUNDLE9_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    EXP_P9_B8_FAST_SHA,
    EXP_S10_O_SUM,
    EXP_S10_VS_OFF_BM_DIFF,
    EXP_S10_VS_OFF_ND_DIFF,
    EXP_S13_ALONE_O_SUM,
    EXP_S13_VS_OFF_ND_DIFF,
    EXP_TREE_SHAS,
    EXP_UHO_LINES,
    EXP_UHO_SHA,
    FASTCHESS_BIN,
    G_EPD_PATH,
    JOB39,
    JOB41,
    JOB43,
    JOB45,
    JOB47,
    NINE_SWITCH_NAMES,
    O_FENS_PATH,
    P10_BUNDLE8_PATCH,
    P10_ON_BUNDLE9_PATCH,
    P8_HOIST_PATCH,
    P9_B8_FAST_PATCH,
    PC20_OPTIONS,
    TEN_BUNDLE10_IDEA_NAMES,
    TPL_V3,
    UHO_BOOK,
    WORK40,
    WORK44,
    WORK47,
    apply_bundle9_to_fresh_v3,
    build_release_v3,
    count_row_diffs,
    fmt_cmp,
    generate_diff_u_patch,
    get_id_name_strict,
    read_j39_rows,
    run_epd_depth12_strict,
    run_fresh_bench_strict,
    sha256_file,
    utc_now,
    verify_all_off_numbers_strict,
    verify_uci_option_strict,
)


def replace_exact_once(path: pathlib.Path, old: str, new: str, label: str) -> None:
    txt = path.read_text(encoding="utf-8")
    cnt = txt.count(old)
    if cnt != 1:
        raise RuntimeError(f"Expected 1 occurrence of {label} in {path}, got {cnt}")
    path.write_text(txt.replace(old, new, 1), encoding="utf-8")


def rebase_p10_onto_bundle9(src_b9: pathlib.Path, src_b10: pathlib.Path, out_patch: pathlib.Path) -> list[str]:
    """
    Applies the exact `job45/P10_B8b_fast.patch.txt` hunks onto `src_b9` into `src_b10`
    (changing ONLY context around `IdeaB8_Fast` added by `P9_B8_fast.patch.txt`), writes
    `out_patch` (`job47/P10_on_bundle9.patch.txt`), and verifies `git apply --check -p1` on `src_b9`.
    """
    if src_b10.exists():
        shutil.rmtree(src_b10)
    shutil.copytree(src_b9, src_b10)

    # Extract the exact `namespace { ... threat_role_b8b_bonus_fast ... }` block directly from job45/P10_B8b_fast.patch.txt
    p10_lines = P10_BUNDLE8_PATCH.read_text(encoding="utf-8").splitlines()
    # Grab added block in `include/forge/search.hpp` hunk 2
    hpp_struct_lines = [ln[1:] for ln in p10_lines if ln.startswith("+") and "extern bool IdeaB8b_Fast;" not in ln and "bool IdeaB8b_Fast" not in ln]
    # Better: slice by exact line markers from job45/P10_B8b_fast.patch.txt so zero code is re-typed!
    p10_raw = P10_BUNDLE8_PATCH.read_text(encoding="utf-8")

    def extract_plus_block(start_marker: str, end_marker: str) -> str:
        s_idx = p10_raw.index(start_marker)
        e_idx = p10_raw.index(end_marker, s_idx) + len(end_marker)
        chunk = p10_raw[s_idx:e_idx].splitlines()
        out = []
        for ln in chunk:
            assert ln.startswith("+"), f"Expected '+' line in P10 extract, got: {ln!r}"
            out.append(ln[1:])
        return "\n".join(out)

    hpp_b8b_block = extract_plus_block("+public:\n+    struct B8bFastEntry {", "+    [[nodiscard]] int threat_role_b8b_bonus_fast(const Board& board, Piece piece, Move move) const;")
    cpp_helpers_block = extract_plus_block("+namespace {\n+\n+[[nodiscard]] Worker::B8bFastEntry make_b8b_fast_entry", "+    return raw * tune::IdeaB8b_Weight / 1024;\n+}")

    # 1. include/forge/search.hpp
    replace_exact_once(
        src_b10 / "include/forge/search.hpp",
        "extern bool IdeaB8_Fast;             // faster node-identical IdeaB8 path (false = off; inactive unless IdeaB8 is on)\n"
        "extern bool IdeaB8b;                 // seat 028 threat-role memory (false = off)",
        "extern bool IdeaB8_Fast;             // faster node-identical IdeaB8 path (false = off; inactive unless IdeaB8 is on)\n"
        "extern bool IdeaB8b;                 // seat 028 threat-role memory (false = off)\n"
        "extern bool IdeaB8b_Fast;            // faster node-identical IdeaB8b path (false = off; inactive unless IdeaB8b is on)",
        "search.hpp IdeaB8b_Fast extern",
    )
    replace_exact_once(
        src_b10 / "include/forge/search.hpp",
        "    mutable RoleThreatB role_b8b_threat_{};\n"
        "    mutable std::uint64_t role_b8b_key_ = 0;\n"
        "    mutable bool role_b8b_key_valid_ = false;\n"
        "    [[nodiscard]] int pawn_history_value(const Board& board, Piece piece, Move move) const;",
        "    mutable RoleThreatB role_b8b_threat_{};\n"
        "    mutable std::uint64_t role_b8b_key_ = 0;\n"
        "    mutable bool role_b8b_key_valid_ = false;\n"
        + hpp_b8b_block
        + "\n    [[nodiscard]] int pawn_history_value(const Board& board, Piece piece, Move move) const;",
        "search.hpp B8bFastEntry decls",
    )

    # 2. src/search.cpp
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "bool IdeaB8_Fast = false;\nbool IdeaB8b = false;",
        "bool IdeaB8_Fast = false;\nbool IdeaB8b = false;\nbool IdeaB8b_Fast = false;",
        "search.cpp IdeaB8b_Fast def",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "        const Worker::B8FastEntry* b8_fast_entry = nullptr;\n"
        "        std::array<int, 5> b8_fast_scaled;",
        "        const Worker::B8FastEntry* b8_fast_entry = nullptr;\n"
        "        std::array<int, 5> b8_fast_scaled;\n"
        "        std::array<int, 5> b8b_fast_scaled{};\n"
        "        const Worker::B8bFastEntry* b8b_fast_entry = nullptr;",
        "search.cpp QuietScorer fields",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "            if (tune::IdeaB8 && tune::IdeaB8_Fast) [[unlikely]] {\n"
        "                b8_fast_entry = searcher.prepare_b8_fast_scorer(b, b8_fast_scaled);\n"
        "            }\n"
        "        }",
        "            if (tune::IdeaB8 && tune::IdeaB8_Fast) [[unlikely]] {\n"
        "                b8_fast_entry = searcher.prepare_b8_fast_scorer(b, b8_fast_scaled);\n"
        "            }\n"
        "            if (tune::IdeaB8b && tune::IdeaB8b_Fast) [[unlikely]] {\n"
        "                b8b_fast_entry = searcher.prepare_b8b_fast_scorer(b, b8b_fast_scaled);\n"
        "            }\n"
        "        }",
        "search.cpp QuietScorer ctor",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "            if (tune::IdeaB8) [[unlikely]] {\n"
        "                if (b8_fast_entry != nullptr) {\n"
        "                    value += b8_fast_scaled[static_cast<std::size_t>(role_fast(board, piece, move, *b8_fast_entry))];\n"
        "                } else if (!tune::IdeaB8_Fast) {\n"
        "                    value += worker.threat_role_bonus(board, move);\n"
        "                }\n"
        "            }\n"
        "            if (tune::IdeaB8b) [[unlikely]] value += worker.threat_role_b8b_bonus(board, move);",
        "            if (tune::IdeaB8) [[unlikely]] {\n"
        "                if (b8_fast_entry != nullptr) {\n"
        "                    value += b8_fast_scaled[static_cast<std::size_t>(role_fast(board, piece, move, *b8_fast_entry))];\n"
        "                } else if (!tune::IdeaB8_Fast) {\n"
        "                    value += worker.threat_role_bonus(board, move);\n"
        "                }\n"
        "            }\n"
        "            if (tune::IdeaB8b) [[unlikely]] {\n"
        "                if (b8b_fast_entry != nullptr) {\n"
        "                    value += b8b_fast_scaled[static_cast<std::size_t>(Worker::role_b8b_fast(board, piece, move, *b8b_fast_entry))];\n"
        "                } else if (!tune::IdeaB8b_Fast) {\n"
        "                    value += worker.threat_role_b8b_bonus(board, move);\n"
        "                }\n"
        "            }",
        "search.cpp QuietScorer::score",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "    for (auto& e : b8_fast_cache_) e.occ_w = ~0ULL;\n"
        "    *role_b8b_history_ = ThreatRoleHistoryB{};\n"
        "    role_b8b_key_valid_ = false;",
        "    for (auto& e : b8_fast_cache_) e.occ_w = ~0ULL;\n"
        "    *role_b8b_history_ = ThreatRoleHistoryB{};\n"
        "    role_b8b_key_valid_ = false;\n"
        "    for (auto& e : b8b_fast_cache_) e.occ_w = ~0ULL;",
        "search.cpp Worker::clear",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "    if (tune::IdeaB8) [[unlikely]] score += threat_role_bonus(board, move);\n"
        "    if (tune::IdeaB8b) [[unlikely]] score += threat_role_b8b_bonus(board, move);",
        "    if (tune::IdeaB8) [[unlikely]] score += threat_role_bonus(board, move);\n"
        "    if (tune::IdeaB8b) [[unlikely]] {\n"
        "        score += tune::IdeaB8b_Fast ? threat_role_b8b_bonus_fast(board, piece, move)\n"
        "                                    : threat_role_b8b_bonus(board, move);\n"
        "    }",
        "search.cpp Worker::quiet_history",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "    update_threat_role(board, move, history_bonus(std::max(1, depth)) / 2);\n"
        "}\n\n"
        "const Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {",
        "    update_threat_role(board, move, history_bonus(std::max(1, depth)) / 2);\n"
        "}\n\n"
        + cpp_helpers_block
        + "\n\nconst Worker::RoleThreatB& Worker::role_b8b_threat(const Board& board) const {",
        "search.cpp B8bFast helpers",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8b) return 0;",
        "int Worker::threat_role_b8b_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8b) return 0;\n"
        "    if (tune::IdeaB8b_Fast) return threat_role_b8b_bonus_fast(board, board.piece_at(move.from), move);",
        "search.cpp threat_role_b8b_bonus",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
        "void Worker::update_threat_role_b8b(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8b) return;",
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
        "    }",
        "search.cpp update_threat_role_b8b",
    )
    replace_exact_once(
        src_b10 / "src/search.cpp",
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
        "        if (tune::IdeaB8b) update_threat_role_b8b(board, quiet, -bonus);",
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
        "        }",
        "search.cpp update_quiet_stats",
    )

    # 3. src/uci.cpp
    replace_exact_once(
        src_b10 / "src/uci.cpp",
        '                         "option name IdeaB8_Fast type check default false\\n"\n'
        '                         "option name IdeaB8b type check default false\\n"',
        '                         "option name IdeaB8_Fast type check default false\\n"\n'
        '                         "option name IdeaB8b type check default false\\n"\n'
        '                         "option name IdeaB8b_Fast type check default false\\n"',
        "uci.cpp option decl",
    )
    replace_exact_once(
        src_b10 / "src/uci.cpp",
        '            } else if (name == "IdeaB8b") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
        "                else note_invalid();",
        '            } else if (name == "IdeaB8b") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b = value_text == "true";\n'
        "                else note_invalid();\n"
        '            } else if (name == "IdeaB8b_Fast") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8b_Fast = value_text == "true";\n'
        "                else note_invalid();",
        "uci.cpp option handler",
    )

    tmp_diff = WORK47 / "tmp_p10_b9.diff"
    generate_diff_u_patch(src_b9, src_b10, tmp_diff)
    hdr = [
        "# P10_on_bundle9.patch.txt — Rebase of job45/P10_B8b_fast.patch.txt onto bundle9 (context lines only)",
        "# Context lines changed relative to job45/P10_B8b_fast.patch.txt (all due to job43/P9_B8_fast.patch.txt in bundle9):",
        "#   1. include/forge/search.hpp hunk 1: context above `extern bool IdeaB8b;` has `extern bool IdeaB8_Fast;` (line 316).",
        "#   2. include/forge/search.hpp hunk 2: line offset +15 (`@@ -704,6 +705,26 @@`) below `B8FastEntry`.",
        "#   3. src/search.cpp hunk 1: context above `bool IdeaB8b = false;` has `bool IdeaB8_Fast = false;` (line 176).",
        "#   4. src/search.cpp hunk 2-3 (`QuietScorer`): context around fields and constructor body includes `b8_fast_entry` / `b8_fast_scaled` / `prepare_b8_fast_scorer` (constructor `{ ... }` already opened by P9_B8_fast).",
        "#   5. src/search.cpp hunk 4 (`QuietScorer::score`): context above `if (tune::IdeaB8b)` is the multi-line `if (tune::IdeaB8)` fast block.",
        "#   6. src/search.cpp hunk 5 (`Worker::clear`): context above `*role_b8b_history_` has `for (auto& e : b8_fast_cache_) e.occ_w = ~0ULL;`.",
        "#   7. src/uci.cpp hunks 1-2: context above `IdeaB8b` option listing (line 762) and handler (lines 983-985) includes `IdeaB8_Fast`.",
    ]
    out_patch.write_bytes(("\n".join(hdr) + "\n" + tmp_diff.read_text(encoding="utf-8")).encode("utf-8"))

    chk = subprocess.run(
        ["git", "apply", "--check", "-p1", str(out_patch)],
        cwd=str(src_b9),
        capture_output=True,
        text=True,
        check=False,
    )
    if chk.returncode != 0:
        raise RuntimeError(f"git apply --check failed for {out_patch}: {chk.stderr}")
    return hdr[1:]


def check_nopc20_hindsight_strict(label: str, exe_path: str, extra_false: list[tuple[str, str]]) -> tuple[bool, list[str]]:
    base_opts = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false"), *extra_false]
    b13_false = run_fresh_bench_strict(exe_path, 13, base_opts + [("HindsightDepth", "false")])
    b13_true = run_fresh_bench_strict(exe_path, 13, base_opts + [("HindsightDepth", "true")])
    ok1, s1 = fmt_cmp(f"{label} no-PC20 HindsightDepth=false bench 13", b13_false, EXP_NOPC20_HD_FALSE_BENCH13)
    ok2, s2 = fmt_cmp(f"{label} no-PC20 HindsightDepth=true bench 13", b13_true, EXP_NOPC20_HD_TRUE_BENCH13)
    return (ok1 and ok2), [s1, s2]


def main() -> int:
    WORK47.mkdir(parents=True, exist_ok=True)
    JOB47.mkdir(parents=True, exist_ok=True)
    out_lines: list[str] = [
        "=== JOB 47 STEP 0: r15d + v3, Bundle9, and Bundle10 (bundle9 + P10_on_bundle9.patch.txt) ===",
        f"start_utc: {utc_now()}",
        "harness_policy: Every runner checks that every sent option is in the exe's uci list, keeps every line before readyok, and STOPS on unknown option, invalid value, illegal, invalid FEN, and ERROR.",
        "",
        "--- 1. r15d + v3 Source Tree & Plain Release Executable ---",
    ]
    all_ok = True

    for rel, exp_sha in EXP_TREE_SHAS.items():
        p = TPL_V3 / rel
        crlf = p.read_bytes().count(b"\r\n")
        sha = sha256_file(p)
        ok1, s1 = fmt_cmp(f"{rel} CRLF count", crlf, 0)
        ok2, s2 = fmt_cmp(f"tree file sha256({p})", sha, exp_sha)
        all_ok = all_ok and ok1 and ok2
        out_lines.extend([s1, s2])

    base_exe = str(WORK44 / "bld_base_v3/forge")
    base_sha = sha256_file(base_exe)
    ok_bs, s_bs = fmt_cmp(f"plain r15d+v3 sha256({base_exe})", base_sha, EXP_BASE_V3_SHA)
    ok_hd0, hd0_lines = verify_uci_option_strict(base_exe, "HindsightDepth")
    ok_b0, b0_lines = verify_all_off_numbers_strict("plain_r15d_v3", base_exe, None)
    ok_k0, k0_lines = check_nopc20_hindsight_strict("plain_r15d_v3", base_exe, [])
    all_ok = all_ok and ok_bs and ok_hd0 and ok_b0 and ok_k0
    out_lines.append(s_bs)
    out_lines.extend(hd0_lines + b0_lines + k0_lines)

    out_lines.append("")
    out_lines.append("--- 2. Bundle9 Verification & git apply --check of job45/P10_B8b_fast.patch.txt ---")
    b9_exe = str(WORK44 / "bld_bundle9/forge")
    b9_sha = sha256_file(b9_exe)
    ok_b9s, s_b9s = fmt_cmp(f"bundle9 exe sha256({b9_exe})", b9_sha, EXP_BUNDLE9_SHA)
    all_ok = all_ok and ok_b9s
    out_lines.append(s_b9s)

    src_b9 = WORK47 / "src_bundle9"
    ok_ap9, ap9_msg = apply_bundle9_to_fresh_v3(src_b9)
    all_ok = all_ok and ok_ap9
    out_lines.append(f"  fresh_bundle9_source_apply                  : {ap9_msg}")

    chk_raw_p10 = subprocess.run(
        ["git", "apply", "--check", "-p1", str(P10_BUNDLE8_PATCH)],
        cwd=str(src_b9),
        capture_output=True,
        text=True,
        check=False,
    )
    out_lines.append(
        f"  git apply --check job45/P10_B8b_fast.patch.txt on bundle9: rc={chk_raw_p10.returncode} "
        f"(expected non-zero due to P9_B8_fast context; rebasing onto bundle9 as job47/P10_on_bundle9.patch.txt)"
    )

    src_b10 = WORK47 / "src_bundle10"
    ctx_notes = rebase_p10_onto_bundle9(src_b9, src_b10, P10_ON_BUNDLE9_PATCH)
    p10_b9_crlf = P10_ON_BUNDLE9_PATCH.read_bytes().count(b"\r\n")
    p10_b9_sha = sha256_file(P10_ON_BUNDLE9_PATCH)
    ok_crlf, s_crlf = fmt_cmp("P10_on_bundle9.patch.txt CRLF count", p10_b9_crlf, 0)
    chk_rebased = subprocess.run(
        ["git", "apply", "--check", "-p1", str(P10_ON_BUNDLE9_PATCH)],
        cwd=str(src_b9),
        capture_output=True,
        text=True,
        check=False,
    )
    ok_chk, s_chk = fmt_cmp("git apply --check P10_on_bundle9 on bundle9", chk_rebased.returncode, 0)
    all_ok = all_ok and ok_crlf and ok_chk
    out_lines.extend([s_crlf, s_chk, f"  patch sha256({P10_ON_BUNDLE9_PATCH}): {p10_b9_sha}", *ctx_notes])

    out_lines.append("")
    out_lines.append("--- 3. Build Bundle10 (/tmp/carbon2_job47/bld_bundle10/forge) & Verify Pins + Fast Paths ---")
    b10_exe, b10_sha, b10_cf, b10_lf = build_release_v3(src_b10, WORK47 / "bld_bundle10")
    out_lines.append(f"  bundle10 exe path                           : {b10_exe}")
    out_lines.append(f"  bundle10 exe sha256({b10_exe}): {b10_sha}")
    out_lines.append(f"  bundle10 id name                            : {get_id_name_strict(b10_exe)}")

    for uopt in ["HindsightDepth", "IdeaB8b", "IdeaB8b_Fast", "IdeaB8", "IdeaB8_Fast", "IdeaS13", "IdeaS13_Hoist", "IdeaS10", "IdeaK4"]:
        ok_u, u_lines = verify_uci_option_strict(b10_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    ok_b10_def, b10_def_lines = verify_all_off_numbers_strict("bundle10_default_off", b10_exe, None)
    ok_b10_exp, b10_exp_lines = verify_all_off_numbers_strict("bundle10_explicit_11_false", b10_exe, ALL_ELEVEN_FALSE)
    ok_k9, k9_lines = check_nopc20_hindsight_strict("bundle9", b9_exe, ALL_NINE_IDEA_FALSE)
    ok_k10, k10_lines = check_nopc20_hindsight_strict("bundle10", b10_exe, ALL_TEN_IDEA_FALSE)
    all_ok = all_ok and ok_b10_def and ok_b10_exp and ok_k9 and ok_k10
    out_lines.extend(b10_def_lines + b10_exp_lines + k9_lines + k10_lines)

    out_lines.append("")
    out_lines.append("--- 4. O and G Depth-12 Known-Answer Sweeps on Bundle9 and Bundle10 (PC20) ---")
    b9_b8b_only = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    b9_s10_only = [(o, "true" if o == "IdeaS10" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]
    b9_s13_only = [(o, "true" if o == "IdeaS13" else "false") for o in NINE_SWITCH_NAMES] + [("HindsightDepth", "false")]

    b10_b8b_only = [(o, "true" if o == "IdeaB8b" else "false") for o in TEN_BUNDLE10_IDEA_NAMES] + [("HindsightDepth", "false")]
    b10_b8b_fast = [(o, "true" if o in ("IdeaB8b", "IdeaB8b_Fast") else "false") for o in TEN_BUNDLE10_IDEA_NAMES] + [("HindsightDepth", "false")]
    b10_b8_only = [(o, "true" if o == "IdeaB8" else "false") for o in TEN_BUNDLE10_IDEA_NAMES] + [("HindsightDepth", "false")]
    b10_b8_fast = [(o, "true" if o in ("IdeaB8", "IdeaB8_Fast") else "false") for o in TEN_BUNDLE10_IDEA_NAMES] + [("HindsightDepth", "false")]

    sweeps = {
        "b9_off_O": (b9_exe, O_FENS_PATH, ALL_TEN_FALSE, JOB47 / "step0_bundle9_all_off_O_d12.rows.txt", 1),
        "b9_off_G": (b9_exe, G_EPD_PATH, ALL_TEN_FALSE, JOB47 / "step0_bundle9_all_off_G_d12.rows.txt", 2),
        "b9_b8b_O": (b9_exe, O_FENS_PATH, b9_b8b_only, JOB47 / "step0_bundle9_only_IdeaB8b_O_d12.rows.txt", 3),
        "b9_s10_O": (b9_exe, O_FENS_PATH, b9_s10_only, JOB47 / "step0_bundle9_only_IdeaS10_O_d12.rows.txt", 1),
        "b9_s13_O": (b9_exe, O_FENS_PATH, b9_s13_only, JOB47 / "step0_bundle9_only_IdeaS13_O_d12.rows.txt", 2),
        "b10_off_O": (b10_exe, O_FENS_PATH, ALL_ELEVEN_FALSE, JOB47 / "step0_bundle10_all_off_O_d12.rows.txt", 3),
        "b10_off_G": (b10_exe, G_EPD_PATH, ALL_ELEVEN_FALSE, JOB47 / "step0_bundle10_all_off_G_d12.rows.txt", 1),
        "b10_b8b_O": (b10_exe, O_FENS_PATH, b10_b8b_only, JOB47 / "step0_bundle10_only_IdeaB8b_O_d12.rows.txt", 2),
        "b10_b8bf_O": (b10_exe, O_FENS_PATH, b10_b8b_fast, JOB47 / "step0_bundle10_B8b_and_B8b_Fast_O_d12.rows.txt", 3),
        "b10_b8_O": (b10_exe, O_FENS_PATH, b10_b8_only, JOB47 / "step0_bundle10_only_IdeaB8_O_d12.rows.txt", 1),
        "b10_b8f_O": (b10_exe, O_FENS_PATH, b10_b8_fast, JOB47 / "step0_bundle10_B8_and_B8_Fast_O_d12.rows.txt", 2),
    }

    res_rows: dict[str, list[tuple[int, int, str, str]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futs = {
            k: pool.submit(
                run_epd_depth12_strict,
                ex,
                sp,
                PC20_OPTIONS,
                eo,
                rp,
                pathlib.Path(str(rp) + ".meta"),
                12,
                cp,
            )
            for k, (ex, sp, eo, rp, cp) in sweeps.items()
        }
        for k, fut in futs.items():
            res_rows[k] = fut.result()

    j39_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    j39_off_g = read_j39_rows(JOB39 / "OFF_G_d12.rows.txt")
    j41_b8b_o = read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt")
    j41_s10_o = read_j39_rows(JOB41 / "P7_bundle7_only_S10_O_d12.rows.txt")
    j41_s13_o = read_j39_rows(JOB41 / "P7_bundle7_only_S13_O_d12.rows.txt")
    j45_b8b_o = read_j39_rows(JOB45 / "P10c_only_B8b_O_d12.rows.txt")
    j43_b8_o = read_j39_rows(JOB43 / "P9c_only_B8_O_d12.rows.txt")

    c_b9_off_o = count_row_diffs(res_rows["b9_off_O"], j39_off_o)
    c_b9_off_g = count_row_diffs(res_rows["b9_off_G"], j39_off_g)
    c_b9_b8b = count_row_diffs(res_rows["b9_b8b_O"], j41_b8b_o)
    c_b9_s10 = count_row_diffs(res_rows["b9_s10_O"], j41_s10_o)
    c_b9_s10_off = count_row_diffs(res_rows["b9_s10_O"], res_rows["b9_off_O"])
    c_b9_s13 = count_row_diffs(res_rows["b9_s13_O"], j41_s13_o)
    c_b9_s13_off = count_row_diffs(res_rows["b9_s13_O"], res_rows["b9_off_O"])

    c_b10_off_o = count_row_diffs(res_rows["b10_off_O"], j39_off_o)
    c_b10_off_g = count_row_diffs(res_rows["b10_off_G"], j39_off_g)
    c_b10_b8b_vs_fast = count_row_diffs(res_rows["b10_b8bf_O"], res_rows["b10_b8b_O"])
    c_b10_b8bf_vs_j45 = count_row_diffs(res_rows["b10_b8bf_O"], j45_b8b_o)
    c_b10_b8_vs_fast = count_row_diffs(res_rows["b10_b8f_O"], res_rows["b10_b8_O"])
    c_b10_b8f_vs_j43 = count_row_diffs(res_rows["b10_b8f_O"], j43_b8_o)

    checks = [
        ("bundle9 OFF O d12 sum", c_b9_off_o["sum_a"], EXP_OFF_O_SUM),
        ("bundle9 OFF O d12 equal vs J39 OFF_O", c_b9_off_o["equal"], 200),
        ("bundle9 OFF G d12 sum", c_b9_off_g["sum_a"], EXP_OFF_G_SUM),
        ("bundle9 OFF G d12 equal vs J39 OFF_G", c_b9_off_g["equal"], 353),
        ("bundle9 IdeaB8b O d12 sum", c_b9_b8b["sum_a"], EXP_B8B_O_SUM),
        ("bundle9 IdeaB8b O d12 equal vs J41 P7_B8b", c_b9_b8b["equal"], 200),
        ("bundle9 IdeaS10 O d12 sum", c_b9_s10["sum_a"], EXP_S10_O_SUM),
        ("bundle9 IdeaS10 O d12 equal vs J41 P7_S10", c_b9_s10["equal"], 200),
        ("bundle9 IdeaS10 vs OFF node diffs", c_b9_s10_off["nodes_diff"], EXP_S10_VS_OFF_ND_DIFF),
        ("bundle9 IdeaS10 vs OFF bestmove diffs", c_b9_s10_off["bestmove_diff"], EXP_S10_VS_OFF_BM_DIFF),
        ("bundle9 IdeaS13 (no hoist) O d12 sum", c_b9_s13["sum_a"], EXP_S13_ALONE_O_SUM),
        ("bundle9 IdeaS13 O d12 equal vs J41 P7_S13", c_b9_s13["equal"], 200),
        ("bundle9 IdeaS13 vs OFF node diffs", c_b9_s13_off["nodes_diff"], EXP_S13_VS_OFF_ND_DIFF),
        ("bundle10 OFF O d12 sum", c_b10_off_o["sum_a"], EXP_OFF_O_SUM),
        ("bundle10 OFF O d12 equal vs J39 OFF_O", c_b10_off_o["equal"], 200),
        ("bundle10 OFF G d12 sum", c_b10_off_g["sum_a"], EXP_OFF_G_SUM),
        ("bundle10 OFF G d12 equal vs J39 OFF_G", c_b10_off_g["equal"], 353),
        ("bundle10 B8b+B8b_Fast O sum", c_b10_b8b_vs_fast["sum_a"], EXP_B8B_O_SUM),
        ("bundle10 B8b+B8b_Fast equal to B8b alone", c_b10_b8b_vs_fast["equal"], 200),
        ("bundle10 B8b+B8b_Fast equal to J45 P10c", c_b10_b8bf_vs_j45["equal"], 200),
        ("bundle10 B8+B8_Fast O sum", c_b10_b8_vs_fast["sum_a"], EXP_B8_O_SUM),
        ("bundle10 B8+B8_Fast equal to B8 alone", c_b10_b8_vs_fast["equal"], 200),
        ("bundle10 B8+B8_Fast equal to J43 P9c", c_b10_b8f_vs_j43["equal"], 200),
    ]
    for lbl, got, exp in checks:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)

    out_lines.append("")
    out_lines.append("--- 5. fastchess & UHO Book Prerequisites ---")
    uho_sha = sha256_file(UHO_BOOK)
    with open(UHO_BOOK, "rb") as bf:
        uho_lines = sum(1 for _ in bf)
    ok_ul, s_ul = fmt_cmp(f"book lines({UHO_BOOK})", uho_lines, EXP_UHO_LINES)
    ok_us, s_us = fmt_cmp(f"book sha256({UHO_BOOK})", uho_sha, EXP_UHO_SHA)
    all_ok = all_ok and ok_ul and ok_us
    out_lines.extend([s_ul, s_us])

    out_lines.append("")
    ok_ov, s_ov = fmt_cmp("STEP 0 OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")
    (JOB47 / "step0_raw.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    fc_ver = subprocess.run([str(FASTCHESS_BIN), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    fc_commit = subprocess.run(["git", "-C", str(WORK40 / "fastchess_repo"), "rev-parse", "HEAD"], text=True, capture_output=True, check=True).stdout.strip()
    builds_lines = [
        "=== JOB 47 BUILDS.TXT ===",
        f"1. r15d + v3 source tree: {TPL_V3}",
        *[f"   tree file sha256({TPL_V3 / rel}) = {sha256_file(TPL_V3 / rel)}" for rel in EXP_TREE_SHAS],
        "",
        f"2. Step 0 plain r15d + v3 Release executable (reused): {base_exe}",
        f"   exe sha256({base_exe}) = {base_sha}",
        f"   id_name = {get_id_name_strict(base_exe)}",
        "",
        f"3. Step 0 bundle9 executable (reused from Job 44): {b9_exe}",
        f"   exe sha256({b9_exe}) = {b9_sha}",
        f"   id_name = {get_id_name_strict(b9_exe)}",
        f"   patch 1 sha256({BUNDLE7_PATCH}) = {sha256_file(BUNDLE7_PATCH)}",
        f"   patch 2 sha256({P8_HOIST_PATCH}) = {sha256_file(P8_HOIST_PATCH)}",
        f"   patch 3 sha256({P9_B8_FAST_PATCH}) = {sha256_file(P9_B8_FAST_PATCH)}",
        "",
        f"4. Step 0 + Part T3 bundle10 executable (bundle9 + {P10_ON_BUNDLE9_PATCH}): {b10_exe}",
        f"   exe sha256({b10_exe}) = {b10_sha}",
        f"   id_name = {get_id_name_strict(b10_exe)}",
        f"   rebased patch sha256({P10_ON_BUNDLE9_PATCH}) = {p10_b9_sha}",
        f"   original bundle8 patch sha256({P10_BUNDLE8_PATCH}) = {sha256_file(P10_BUNDLE8_PATCH)}",
        f"   compile_flags = {b10_cf}",
        f"   link_flags    = {b10_lf}",
        "",
        f"5. Official fastchess executable: {FASTCHESS_BIN}",
        f"   version = {fc_ver}",
        f"   git_commit(/tmp/carbon2_job40/fastchess_repo) = {fc_commit}",
        f"   exe sha256({FASTCHESS_BIN}) = {sha256_file(FASTCHESS_BIN)}",
        "",
        f"6. Official opening book: {UHO_BOOK}",
        f"   lines({UHO_BOOK}) = {uho_lines}",
        f"   book sha256({UHO_BOOK}) = {uho_sha}",
    ]
    (JOB47 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
