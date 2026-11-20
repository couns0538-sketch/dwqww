#!/usr/bin/env python3
"""
Job 43 Part P9c, P9d, and P9e (`run_partP9cde.py`):
- `P9c`: Implements `IdeaB8_Fast` (`option name IdeaB8_Fast type check default false`; does nothing unless `IdeaB8` is on)
  on top of `r15d + v3 + bundle_grok7.patch.txt + P8_S13_hoist.patch.txt`:
  1) 256-slot per-Worker `B8FastEntry` cache (preventing child subtrees from evicting parent ply's threat lookup).
  2) Value-tiered `make_b8_fast_entry` (`Queen -> Rook -> (Knight|Bishop)` with `pawn_attacks_bb` bitmask for minors
     and precomputed `between_bb`, `attacker_bb`, `dearer_enemy_bb`).
  3) Per-MovePicker `QuietScorer` precomputation (`prepare_b8_fast_scorer`): zero per-move calls on the 90.82% of
     positions without a threat, and inline bitmask role classification + pre-scaled bonus lookup on the 9.18% with a threat.
- Verifies:
  * All 9 `Idea*` switches off (default and explicit) = every OFF number + non-PC20 `HindsightDepth` `bench 13`.
  * `IdeaB8_Fast=true` with `IdeaB8=false` = OFF `O` rows (`200 == 200`, `8315168 == 8315168`).
  * `IdeaB8=true, IdeaB8_Fast=false` = `bundle8` `IdeaB8` alone on `O` (`200 == 200`), `G` (`353 == 353`), and `Set A line L`.
  * `IdeaB8=true, IdeaB8_Fast=true` = `IdeaB8` alone position by position on `O` (`200 == 200`), `G` (`353 == 353`),
    and `Set A line L` (exact `records`, `searches`, `nodes`, and `record_text_sha256`!).
- `P9d`: Runs 10-run (`forward 01..05` + `reverse 06..10`) pinned-core Part T timing on `O` depth 12 (`PC20`, built-in eval):
  `all_off_1`, `all_off_2`, `only_B8`, `B8_and_B8_Fast`, `only_B8b` (`IdeaB8_Fast` covers `IdeaB8` (078) only so it
  strictly does nothing unless `IdeaB8` is on).
- `P9e`: Emits `forge-combo29/carbon2/job43/P9_B8_fast.patch.txt` (`diff -u`, LF `0 == 0` CRLF, first lines naming the
  exact tree it applies to, verified via `git apply --check -p1` `0 == 0`).
"""
from __future__ import annotations

import pathlib
import shutil
import statistics
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j43_lib import (  # noqa: E402
    BUNDLE7_PATCH,
    EIGHT_SWITCH_NAMES,
    EXP_BUNDLE7_SHA,
    EXP_NOPC20_HD_FALSE_BENCH13,
    EXP_NOPC20_HD_TRUE_BENCH13,
    EXP_OFF_G_SUM,
    EXP_OFF_O_SUM,
    EXP_P8_HOIST_SHA,
    G_EPD_PATH,
    JOB39,
    JOB41,
    JOB43,
    O_FENS_PATH,
    P8_HOIST_PATCH,
    TPL_V3,
    WORK43,
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

NINE_SWITCH_NAMES = [
    "IdeaK4",
    "IdeaS32",
    "IdeaB1",
    "IdeaS13",
    "IdeaS13_Hoist",
    "IdeaS10",
    "IdeaB8",
    "IdeaB8_Fast",
    "IdeaB8b",
]
ALL_NINE_IDEA_FALSE = [(o, "false") for o in NINE_SWITCH_NAMES]


def replace_once(src: str, old: str, new: str, label: str) -> str:
    cnt = src.count(old)
    if cnt != 1:
        raise RuntimeError(f"[{label}] expected 1 occurrence, found {cnt}:\n{old!r}")
    return src.replace(old, new, 1)


def inject_p9_b8_fast(tree_dir: pathlib.Path) -> None:
    # 1. include/forge/search.hpp
    shpp_p = tree_dir / "include/forge/search.hpp"
    shpp = shpp_p.read_text(encoding="utf-8")
    shpp = replace_once(
        shpp,
        "extern bool IdeaB8;                  // threat-role memory (false = off; off keeps today's search path)\n",
        "extern bool IdeaB8;                  // threat-role memory (false = off; off keeps today's search path)\n"
        "extern bool IdeaB8_Fast;             // faster node-identical IdeaB8 path (false = off; inactive unless IdeaB8 is on)\n",
        "search.hpp IdeaB8_Fast extern",
    )
    shpp = replace_once(
        shpp,
        "    mutable int threat_role_victim_value_ = 0;\n",
        "    mutable int threat_role_victim_value_ = 0;\n"
        "public:\n"
        "    struct B8FastEntry {\n"
        "        std::uint64_t key = 0;\n"
        "        Bitboard occ_w = ~0ULL;\n"
        "        Bitboard occ_b = ~0ULL;\n"
        "        Bitboard between_bb = 0;\n"
        "        Bitboard attacker_bb = 0;\n"
        "        Bitboard dearer_enemy_bb = 0;\n"
        "        std::uint8_t victim_sq = 0;\n"
        "        std::uint8_t attacker_sq = 0;\n"
        "        std::uint8_t victim_type = 0;\n"
        "        std::uint8_t attacker_type = 0;\n"
        "        bool present = false;\n"
        "    };\n"
        "private:\n"
        "    mutable std::array<B8FastEntry, 256> b8_fast_cache_{};\n",
        "search.hpp B8FastEntry cache",
    )
    shpp = replace_once(
        shpp,
        "    void ensure_role_threat(const Board& board) const;\n",
        "    void ensure_role_threat(const Board& board) const;\n"
        "    [[nodiscard]] const B8FastEntry& ensure_b8_fast(const Board& board) const;\n"
        "    [[nodiscard]] const B8FastEntry* prepare_b8_fast_scorer(const Board& board, std::array<int, 5>& scaled) const;\n",
        "search.hpp ensure_b8_fast decls",
    )
    shpp_p.write_text(shpp, encoding="utf-8")

    # 2. src/search.cpp
    scpp_p = tree_dir / "src/search.cpp"
    scpp = scpp_p.read_text(encoding="utf-8")

    scpp = replace_once(
        scpp,
        "bool IdeaB8 = false;\n",
        "bool IdeaB8 = false;\n"
        "bool IdeaB8_Fast = false;\n",
        "search.cpp IdeaB8_Fast def",
    )

    # Place `quiet_threat_role_fast` helper right before `MovePicker` or inside `QuietScorer`
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
        "        const Worker::B8FastEntry* b8_fast_entry = nullptr;\n"
        "        std::array<int, 5> b8_fast_scaled;\n"
        "\n"
        "        [[nodiscard]] static int role_fast(const Board& b, Piece moved_piece, Move m,\n"
        "                                           const Worker::B8FastEntry& e) {\n"
        "            if (m.from == e.victim_sq) return 0;\n"
        "            if ((e.between_bb & square_bb(m.to)) != 0) return 1;\n"
        "            const int mover = piece_type(moved_piece);\n"
        "            const Bitboard occ = b.occupied() ^ square_bb(m.from);\n"
        "            Bitboard hits = 0;\n"
        "            switch (mover) {\n"
        "            case Pawn: hits = attacks::pawn(b.side_to_move(), m.to); break;\n"
        "            case Knight: hits = attacks::knight(m.to); break;\n"
        "            case Bishop: hits = attacks::bishop(m.to, occ); break;\n"
        "            case Rook: hits = attacks::rook(m.to, occ); break;\n"
        "            case Queen: hits = attacks::queen(m.to, occ); break;\n"
        "            case King: hits = attacks::king(m.to); break;\n"
        "            default: break;\n"
        "            }\n"
        "            if ((hits & e.attacker_bb) != 0) return 2;\n"
        "            if ((hits & e.dearer_enemy_bb) != 0) return 3;\n"
        "            return 4;\n"
        "        }\n"
        "\n"
        "        QuietScorer(const Board& b, const Worker& searcher, const SearchStack* ss)\n",
        "search.cpp QuietScorer fields",
    )

    scpp = replace_once(
        scpp,
        "              rework(tune::HistRework != 0 && ss != nullptr),\n"
        "              use_threat_hist(tune::ThreatHistory) {}\n",
        "              rework(tune::HistRework != 0 && ss != nullptr),\n"
        "              use_threat_hist(tune::ThreatHistory) {\n"
        "            if (tune::IdeaB8 && tune::IdeaB8_Fast) [[unlikely]] {\n"
        "                b8_fast_entry = searcher.prepare_b8_fast_scorer(b, b8_fast_scaled);\n"
        "            }\n"
        "        }\n",
        "search.cpp QuietScorer ctor",
    )

    scpp = replace_once(
        scpp,
        "            if (tune::IdeaB8) [[unlikely]] value += worker.threat_role_bonus(board, move);\n",
        "            if (tune::IdeaB8) [[unlikely]] {\n"
        "                if (b8_fast_entry != nullptr) {\n"
        "                    value += b8_fast_scaled[static_cast<std::size_t>(role_fast(board, piece, move, *b8_fast_entry))];\n"
        "                } else if (!tune::IdeaB8_Fast) {\n"
        "                    value += worker.threat_role_bonus(board, move);\n"
        "                }\n"
        "            }\n",
        "search.cpp QuietScorer score",
    )

    scpp = replace_once(
        scpp,
        "    *threat_role_history_ = ThreatRoleHistory{};\n"
        "    threat_role_cached_ = false;\n",
        "    *threat_role_history_ = ThreatRoleHistory{};\n"
        "    threat_role_cached_ = false;\n"
        "    for (auto& e : b8_fast_cache_) e.occ_w = ~0ULL;\n",
        "search.cpp Worker::clear b8_fast_cache_",
    )

    fast_impl = (
        "[[nodiscard]] Worker::B8FastEntry make_b8_fast_entry(const Board& board) {\n"
        "    Worker::B8FastEntry e;\n"
        "    e.key = board.key();\n"
        "    e.occ_w = board.occupied(White);\n"
        "    e.occ_b = board.occupied(Black);\n"
        "    const Color us = board.side_to_move();\n"
        "    const Color them = opposite(us);\n"
        "    const Bitboard occ = e.occ_w | e.occ_b;\n"
        "    const Bitboard enemy_pawns = board.pieces(them, Pawn);\n"
        "\n"
        "    auto finish = [&](int v_sq, int v_type, int a_sq, int a_type, Bitboard dearer) -> Worker::B8FastEntry {\n"
        "        e.present = true;\n"
        "        e.victim_sq = static_cast<std::uint8_t>(v_sq);\n"
        "        e.attacker_sq = static_cast<std::uint8_t>(a_sq);\n"
        "        e.victim_type = static_cast<std::uint8_t>(v_type);\n"
        "        e.attacker_type = static_cast<std::uint8_t>(a_type);\n"
        "        e.between_bb = (a_type == Bishop || a_type == Rook || a_type == Queen)\n"
        "                           ? attacks::between(a_sq, v_sq)\n"
        "                           : 0ULL;\n"
        "        e.attacker_bb = square_bb(a_sq);\n"
        "        e.dearer_enemy_bb = dearer;\n"
        "        return e;\n"
        "    };\n"
        "\n"
        "    if (Bitboard queens = board.pieces(us, Queen); queens != 0) {\n"
        "        const Bitboard enemy_knights = board.pieces(them, Knight);\n"
        "        const Bitboard enemy_bishops = board.pieces(them, Bishop);\n"
        "        const Bitboard enemy_rooks = board.pieces(them, Rook);\n"
        "        while (queens != 0) {\n"
        "            const int sq = pop_lsb(queens);\n"
        "            if (const Bitboard p = attacks::pawn(us, sq) & enemy_pawns; p != 0) {\n"
        "                return finish(sq, Queen, lsb(p), Pawn, 0ULL);\n"
        "            }\n"
        "            if (const Bitboard nb = (attacks::knight(sq) & enemy_knights) | (attacks::bishop(sq, occ) & enemy_bishops); nb != 0) {\n"
        "                const int a_sq = lsb(nb);\n"
        "                return finish(sq, Queen, a_sq, piece_type(board.piece_at(a_sq)), 0ULL);\n"
        "            }\n"
        "            if (const Bitboard r = attacks::rook(sq, occ) & enemy_rooks; r != 0) {\n"
        "                return finish(sq, Queen, lsb(r), Rook, 0ULL);\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "\n"
        "    if (Bitboard rooks = board.pieces(us, Rook); rooks != 0) {\n"
        "        const Bitboard enemy_knights = board.pieces(them, Knight);\n"
        "        const Bitboard enemy_bishops = board.pieces(them, Bishop);\n"
        "        while (rooks != 0) {\n"
        "            const int sq = pop_lsb(rooks);\n"
        "            if (const Bitboard p = attacks::pawn(us, sq) & enemy_pawns; p != 0) {\n"
        "                return finish(sq, Rook, lsb(p), Pawn, board.pieces(them, Queen));\n"
        "            }\n"
        "            if (const Bitboard nb = (attacks::knight(sq) & enemy_knights) | (attacks::bishop(sq, occ) & enemy_bishops); nb != 0) {\n"
        "                const int a_sq = lsb(nb);\n"
        "                return finish(sq, Rook, a_sq, piece_type(board.piece_at(a_sq)), board.pieces(them, Queen));\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "\n"
        "    const Bitboard minors_hit = (board.pieces(us, Knight) | board.pieces(us, Bishop)) & pawn_attacks_bb(them, enemy_pawns);\n"
        "    if (minors_hit != 0) {\n"
        "        const int sq = lsb(minors_hit);\n"
        "        const int a_sq = lsb(attacks::pawn(us, sq) & enemy_pawns);\n"
        "        return finish(sq, piece_type(board.piece_at(sq)), a_sq, Pawn, board.pieces(them, Rook) | board.pieces(them, Queen));\n"
        "    }\n"
        "\n"
        "    return e;\n"
        "}\n"
        "\n"
        "[[nodiscard]] int quiet_threat_role_fast(const Board& board, Move move, const Worker::B8FastEntry& e) {\n"
        "    if (move.from == e.victim_sq) return 0;\n"
        "    if ((e.between_bb & square_bb(move.to)) != 0) return 1;\n"
        "    const Bitboard hits = attacks_after_quiet(board, move);\n"
        "    if ((hits & e.attacker_bb) != 0) return 2;\n"
        "    if ((hits & e.dearer_enemy_bb) != 0) return 3;\n"
        "    return 4;\n"
        "}\n"
    )

    scpp = replace_once(
        scpp,
        "} // namespace\n\nvoid Worker::ensure_role_threat(const Board& board) const {\n",
        fast_impl + "\n} // namespace\n\n"
        "const Worker::B8FastEntry& Worker::ensure_b8_fast(const Board& board) const {\n"
        "    const std::uint64_t key = board.key();\n"
        "    B8FastEntry& slot = b8_fast_cache_[static_cast<std::size_t>(key & 255ULL)];\n"
        "    if (slot.key == key && slot.occ_w == board.occupied(White) && slot.occ_b == board.occupied(Black)) {\n"
        "        return slot;\n"
        "    }\n"
        "    slot = make_b8_fast_entry(board);\n"
        "    return slot;\n"
        "}\n\n"
        "const Worker::B8FastEntry* Worker::prepare_b8_fast_scorer(const Board& board, std::array<int, 5>& scaled) const {\n"
        "    const B8FastEntry& e = ensure_b8_fast(board);\n"
        "    if (!e.present) return nullptr;\n"
        "    const auto& row = (*threat_role_history_)[static_cast<std::size_t>(board.side_to_move())]\n"
        "                                             [static_cast<std::size_t>(e.victim_type)]\n"
        "                                             [static_cast<std::size_t>(e.attacker_type)];\n"
        "    const int w = tune::IdeaB8_Weight;\n"
        "    for (std::size_t r = 0; r < 5; ++r) {\n"
        "        scaled[r] = row[r] * w / 1024;\n"
        "    }\n"
        "    return &e;\n"
        "}\n\n"
        "void Worker::ensure_role_threat(const Board& board) const {\n",
        "search.cpp ensure_b8_fast impl",
    )

    scpp = replace_once(
        scpp,
        "int Worker::threat_role_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8) return 0;\n"
        "    ensure_role_threat(board);\n",
        "int Worker::threat_role_bonus(const Board& board, Move move) const {\n"
        "    if (!tune::IdeaB8) return 0;\n"
        "    if (tune::IdeaB8_Fast) {\n"
        "        const B8FastEntry& e = ensure_b8_fast(board);\n"
        "        if (!e.present) return 0;\n"
        "        const int role = quiet_threat_role_fast(board, move, e);\n"
        "        const int raw = (*threat_role_history_)[static_cast<std::size_t>(board.side_to_move())]\n"
        "                                               [static_cast<std::size_t>(e.victim_type)]\n"
        "                                               [static_cast<std::size_t>(e.attacker_type)]\n"
        "                                               [static_cast<std::size_t>(role)];\n"
        "        return raw * tune::IdeaB8_Weight / 1024;\n"
        "    }\n"
        "    ensure_role_threat(board);\n",
        "search.cpp threat_role_bonus fast branch",
    )

    scpp = replace_once(
        scpp,
        "void Worker::update_threat_role(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8 || move.is_capture() || move.is_promotion()) return;\n"
        "    ensure_role_threat(board);\n",
        "void Worker::update_threat_role(const Board& board, Move move, int bonus) {\n"
        "    if (!tune::IdeaB8 || move.is_capture() || move.is_promotion()) return;\n"
        "    if (tune::IdeaB8_Fast) {\n"
        "        const B8FastEntry& e = ensure_b8_fast(board);\n"
        "        if (!e.present) return;\n"
        "        const int role = quiet_threat_role_fast(board, move, e);\n"
        "        apply_history((*threat_role_history_)[static_cast<std::size_t>(board.side_to_move())]\n"
        "                                             [static_cast<std::size_t>(e.victim_type)]\n"
        "                                             [static_cast<std::size_t>(e.attacker_type)]\n"
        "                                             [static_cast<std::size_t>(role)],\n"
        "                      bonus);\n"
        "        return;\n"
        "    }\n"
        "    ensure_role_threat(board);\n",
        "search.cpp update_threat_role fast branch",
    )
    scpp_p.write_text(scpp, encoding="utf-8")

    # 3. src/uci.cpp
    ucpp_p = tree_dir / "src/uci.cpp"
    ucpp = ucpp_p.read_text(encoding="utf-8")
    ucpp = replace_once(
        ucpp,
        '                         "option name IdeaB8 type check default false\\n"\n',
        '                         "option name IdeaB8 type check default false\\n"\n'
        '                         "option name IdeaB8_Fast type check default false\\n"\n',
        "uci.cpp IdeaB8_Fast decl",
    )
    ucpp = replace_once(
        ucpp,
        '            } else if (name == "IdeaB8") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8 = value_text == "true";\n'
        '                else note_invalid();\n',
        '            } else if (name == "IdeaB8") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8 = value_text == "true";\n'
        '                else note_invalid();\n'
        '            } else if (name == "IdeaB8_Fast") {\n'
        '                if (value_text == "true" || value_text == "false") forge::tune::IdeaB8_Fast = value_text == "true";\n'
        '                else note_invalid();\n',
        "uci.cpp IdeaB8_Fast setoption",
    )
    ucpp_p.write_text(ucpp, encoding="utf-8")


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

    stem = f"P9d_partT_{run_idx:02d}_{pass_tag}_{setting_name}"
    rows_path = JOB43 / f"{stem}.rows.txt"
    meta_path = JOB43 / f"{stem}.rows.txt.meta"
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
        "=== JOB 43 PART P9c, P9d, P9e: IdeaB8_Fast Patch, Zero-Node-Change Proofs, and Part T Timing ===",
        f"start_utc: {start_u}",
        "",
        "--- 1. P9e: Emit job43/P9_B8_fast.patch.txt (Against r15d + v3 + bundle_grok7 + P8_S13_hoist) & Build ---",
    ]
    all_ok = True

    base_b8 = WORK43 / "src_p9_base_bundle8"
    gen_b9 = WORK43 / "src_p9_gen_b8fast"
    ok_b, _ = apply_bundle8_to_fresh_v3(base_b8)
    assert ok_b
    if gen_b9.exists():
        shutil.rmtree(gen_b9)
    shutil.copytree(base_b8, gen_b9)
    inject_p9_b8_fast(gen_b9)

    raw_diff_path = WORK43 / "tmp_raw_p9.patch"
    generate_diff_u_patch(base_b8, gen_b9, raw_diff_path)
    header = (
        "# P9_B8_fast.patch.txt — IdeaB8_Fast (option name IdeaB8_Fast type check default false; inactive unless IdeaB8 is on)\n"
        f"# Applies to tree: r15d + v3 ({TPL_V3})\n"
        f"#   + forge-combo29/carbon2/job41/bundle_grok7.patch.txt (sha256 = {EXP_BUNDLE7_SHA})\n"
        f"#   + forge-combo29/carbon2/job42/P8_S13_hoist.patch.txt (sha256 = {EXP_P8_HOIST_SHA})\n"
    )
    p9_patch_path = JOB43 / "P9_B8_fast.patch.txt"
    p9_patch_path.write_text(header + raw_diff_path.read_text(encoding="utf-8"), encoding="utf-8")

    p9_raw_bytes = p9_patch_path.read_bytes()
    p9_crlf = p9_raw_bytes.count(b"\r\n")
    p9_sha = sha256_file(p9_patch_path)
    p9_nlines = len(p9_raw_bytes.splitlines())

    src_b9 = WORK43 / "src_bundle9"
    ok_b9_base, _ = apply_bundle8_to_fresh_v3(src_b9)
    assert ok_b9_base
    chk = subprocess.run(["git", "apply", "--check", "-p1", str(p9_patch_path)], cwd=str(src_b9), capture_output=True, text=True)
    ok_chk, s_chk = fmt_cmp("P9_B8_fast.patch.txt git apply --check -p1 on bundle8", chk.returncode, 0)
    ok_lf, s_lf = fmt_cmp("P9_B8_fast.patch.txt CRLF count", p9_crlf, 0)
    all_ok = all_ok and ok_chk and ok_lf
    out_lines.extend(
        [
            s_lf,
            s_chk,
            f"  patch path                                  : {p9_patch_path}",
            f"  patch lines({p9_patch_path}) : {p9_nlines}",
            f"  patch sha256({p9_patch_path}) : {p9_sha}",
        ]
    )
    subprocess.run(["git", "apply", "-p1", str(p9_patch_path)], cwd=str(src_b9), check=True)

    b9_exe_path = WORK43 / "bld_bundle9/forge"
    if b9_exe_path.exists():
        b9_exe = str(b9_exe_path)
        b9_sha = sha256_file(b9_exe_path)
        b9_cf, b9_lf = "(reused fresh bld_bundle9)", "(reused fresh bld_bundle9)"
    else:
        b9_exe, b9_sha, b9_cf, b9_lf = build_release_v3(src_b9, WORK43 / "bld_bundle9")
    out_lines.append(f"  bundle9 exe path                            : {b9_exe}")
    out_lines.append(f"  bundle9 exe sha256({b9_exe}) : {b9_sha}")
    out_lines.append(f"  bundle9 id name                             : {get_id_name(b9_exe)}")

    for uopt in ["IdeaB8_Fast", "IdeaB8", "IdeaB8b", "HindsightDepth", "IdeaS13_Hoist"]:
        ok_u, u_lines = verify_uci_option_check(b9_exe, uopt)
        all_ok = all_ok and ok_u
        out_lines.extend(u_lines)

    # 2. All-off & IdeaB8_Fast-alone-is-noop verification
    out_lines.append("")
    out_lines.append("--- 2. P9c All-OFF & IdeaB8_Fast-Alone-When-IdeaB8-Off Verification ---")
    ok_def, def_lines = verify_all_off_numbers("bundle9_default_off", b9_exe, None)
    ok_exp, exp_lines = verify_all_off_numbers("bundle9_explicit_9_false", b9_exe, ALL_NINE_IDEA_FALSE)
    b13_f = run_fresh_bench(
        b9_exe, 13,
        ["setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false"]
        + [f"setoption name {k} value {v}" for k, v in ALL_NINE_IDEA_FALSE]
        + ["setoption name HindsightDepth value false"],
    )
    b13_t = run_fresh_bench(
        b9_exe, 13,
        ["setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false"]
        + [f"setoption name {k} value {v}" for k, v in ALL_NINE_IDEA_FALSE]
        + ["setoption name HindsightDepth value true"],
    )
    ok_k1, s_k1 = fmt_cmp("bundle9 no-PC20 HindsightDepth=false bench 13", b13_f, EXP_NOPC20_HD_FALSE_BENCH13)
    ok_k2, s_k2 = fmt_cmp("bundle9 no-PC20 HindsightDepth=true bench 13", b13_t, EXP_NOPC20_HD_TRUE_BENCH13)
    all_ok = all_ok and ok_def and ok_exp and ok_k1 and ok_k2
    out_lines.extend(def_lines + exp_lines + [s_k1, s_k2])

    ref_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    fast_only_opts = [(o, "true" if o == "IdeaB8_Fast" else "false") for o in NINE_SWITCH_NAMES]
    def get_or_run_d12(epd_p: pathlib.Path, opts: list[tuple[str, str]], rows_p: pathlib.Path, meta_p: pathlib.Path):
        if rows_p.exists() and meta_p.exists():
            return read_j39_rows(rows_p)
        return run_epd_depth12(b9_exe, epd_p, opts, rows_p, meta_p, depth=12, cpu_pin=1)

    fast_only_o = get_or_run_d12(
        O_FENS_PATH, fast_only_opts,
        JOB43 / "P9c_only_IdeaB8_Fast_B8_off_O_d12.rows.txt",
        JOB43 / "P9c_only_IdeaB8_Fast_B8_off_O_d12.rows.txt.meta",
    )
    d_fo, _ = diff_breakdown_with_samples(fast_only_o, ref_off_o, "only_B8_Fast", "OFF_O")
    ok_fo1, s_fo1 = fmt_cmp("IdeaB8_Fast=true (IdeaB8=false) O sum vs OFF O", sum(r[1] for r in fast_only_o), EXP_OFF_O_SUM)
    ok_fo2, s_fo2 = fmt_cmp("IdeaB8_Fast=true (IdeaB8=false) O equal pos vs OFF O", d_fo["equal"], 200)
    all_ok = all_ok and ok_fo1 and ok_fo2
    out_lines.extend([s_fo1, s_fo2])

    # 3. Exact identity: IdeaB8 + IdeaB8_Fast == IdeaB8 alone on O, G, and Set A line L
    out_lines.append("")
    out_lines.append("--- 3. P9c Exact Node/Move/Score Identity: IdeaB8 + IdeaB8_Fast == IdeaB8 Alone on O, G, and Set A Line L ---")
    only_b8_opts = [(o, "true" if o == "IdeaB8" else "false") for o in NINE_SWITCH_NAMES]
    b8_plus_fast_opts = [(o, "true" if o in ("IdeaB8", "IdeaB8_Fast") else "false") for o in NINE_SWITCH_NAMES]

    b8_o = get_or_run_d12(
        O_FENS_PATH, only_b8_opts,
        JOB43 / "P9c_only_B8_O_d12.rows.txt",
        JOB43 / "P9c_only_B8_O_d12.rows.txt.meta",
    )
    b8f_o = get_or_run_d12(
        O_FENS_PATH, b8_plus_fast_opts,
        JOB43 / "P9c_B8_and_B8_Fast_O_d12.rows.txt",
        JOB43 / "P9c_B8_and_B8_Fast_O_d12.rows.txt.meta",
    )

    b8_g = get_or_run_d12(
        G_EPD_PATH, only_b8_opts,
        JOB43 / "P9c_only_B8_G_d12.rows.txt",
        JOB43 / "P9c_only_B8_G_d12.rows.txt.meta",
    )
    b8f_g = get_or_run_d12(
        G_EPD_PATH, b8_plus_fast_opts,
        JOB43 / "P9c_B8_and_B8_Fast_G_d12.rows.txt",
        JOB43 / "P9c_B8_and_B8_Fast_G_d12.rows.txt.meta",
    )

    j39_b8_o = read_j39_rows(JOB39 / "P6_B8_078_on_O_d12.rows.txt")
    j39_b8_g = read_j39_rows(JOB39 / "P6_B8_078_on_G_d12.rows.txt")

    d_b8_j39_o, _ = diff_breakdown_with_samples(b8_o, j39_b8_o, "b9_B8_O", "J39_P6_O")
    d_b8_j39_g, _ = diff_breakdown_with_samples(b8_g, j39_b8_g, "b9_B8_G", "J39_P6_G")
    d_fast_o, _ = diff_breakdown_with_samples(b8f_o, b8_o, "B8+Fast_O", "B8_alone_O")
    d_fast_g, _ = diff_breakdown_with_samples(b8f_g, b8_g, "B8+Fast_G", "B8_alone_G")

    seta_b8 = run_selfgame_set_with_options(b9_exe, "carbon2-job33-a", 200, None, extra_opts=only_b8_opts, cpu_pin=1)
    seta_b8_rows = JOB43 / "P9c_only_B8_SetA_L.rows.txt"
    write_v2_v3_rows(seta_b8_rows, "Job 43 Part P9c bundle9 IdeaB8 alone Set A line L (built-in eval, PC20)", seta_b8)
    write_seta_meta(JOB43 / "P9c_only_B8_SetA_L.rows.txt.meta", b9_exe, only_b8_opts, seta_b8)

    seta_b8f = run_selfgame_set_with_options(b9_exe, "carbon2-job33-a", 200, None, extra_opts=b8_plus_fast_opts, cpu_pin=1)
    seta_b8f_rows = JOB43 / "P9c_B8_and_B8_Fast_SetA_L.rows.txt"
    write_v2_v3_rows(seta_b8f_rows, "Job 43 Part P9c bundle9 IdeaB8 + IdeaB8_Fast Set A line L (built-in eval, PC20)", seta_b8f)
    write_seta_meta(JOB43 / "P9c_B8_and_B8_Fast_SetA_L.rows.txt.meta", b9_exe, b8_plus_fast_opts, seta_b8f)

    for lbl, got, exp in [
        ("bundle9 only_B8 O equal pos vs J39 P6 O", d_b8_j39_o["equal"], 200),
        ("bundle9 only_B8 G equal pos vs J39 P6 G", d_b8_j39_g["equal"], 353),
        ("B8+B8_Fast vs only_B8 O sum_nodes", sum(r[1] for r in b8f_o), sum(r[1] for r in b8_o)),
        ("B8+B8_Fast vs only_B8 O equal positions", d_fast_o["equal"], 200),
        ("B8+B8_Fast vs only_B8 G sum_nodes", sum(r[1] for r in b8f_g), sum(r[1] for r in b8_g)),
        ("B8+B8_Fast vs only_B8 G equal positions", d_fast_g["equal"], 353),
        ("B8+B8_Fast vs only_B8 Set A line L records", seta_b8f.total_records, seta_b8.total_records),
        ("B8+B8_Fast vs only_B8 Set A line L searches", seta_b8f.total_searches, seta_b8.total_searches),
        ("B8+B8_Fast vs only_B8 Set A line L nodes", seta_b8f.total_nodes, seta_b8.total_nodes),
        ("B8+B8_Fast vs only_B8 Set A line L record_text sha256", seta_b8f.full_sha256, seta_b8.full_sha256),
    ]:
        ok, s = fmt_cmp(lbl, got, exp)
        all_ok = all_ok and ok
        out_lines.append(s)
        if not ok:
            raise RuntimeError(f"IDENTITY CHECK FAILED: {s}")

    # 4. P9d: Part T Timing (Forward 01..05, then Reverse 06..10) on pinned CPU 1
    out_lines.append("")
    out_lines.append("--- 4. P9d: Part T Cost per 1,000 Nodes (Forward + Reverse, Pinned Core 1, O Set Depth 12, PC20) ---")
    fens = load_fens(O_FENS_PATH)
    only_b8b_opts = [(o, "true" if o == "IdeaB8b" else "false") for o in NINE_SWITCH_NAMES]
    fwd_settings = [
        ("all_off_1", ALL_NINE_IDEA_FALSE + [("HindsightDepth", "false")]),
        ("all_off_2", ALL_NINE_IDEA_FALSE + [("HindsightDepth", "false")]),
        ("only_B8", only_b8_opts + [("HindsightDepth", "false")]),
        ("B8_and_B8_Fast", b8_plus_fast_opts + [("HindsightDepth", "false")]),
        ("only_B8b", only_b8b_opts + [("HindsightDepth", "false")]),
    ]
    rev_settings = list(reversed(fwd_settings))
    refs = {
        "all_off_1": ref_off_o,
        "all_off_2": ref_off_o,
        "only_B8": b8_o,
        "B8_and_B8_Fast": b8_o,
        "only_B8b": read_j39_rows(JOB41 / "P7_bundle7_only_B8b_O_d12.rows.txt"),
    }
    exp_sums = {
        "all_off_1": EXP_OFF_O_SUM,
        "all_off_2": EXP_OFF_O_SUM,
        "only_B8": 8262696,
        "B8_and_B8_Fast": 8262696,
        "only_B8b": 8483711,
    }

    # 1s warm-up on pinned CPU 1 before Run 01
    subprocess.run(["taskset", "-c", "1", b9_exe], input="uci\nisready\nbench 12\nquit\n", text=True, capture_output=True, check=True)

    schedule = [("fwd", k, v) for k, v in fwd_settings] + [("rev", k, v) for k, v in rev_settings]
    t_results: list[dict] = []
    for idx, (ptag, sname, sopts) in enumerate(schedule, start=1):
        r = run_timed_o_d12(b9_exe, idx, ptag, sname, sopts, fens, refs[sname], cpu_pin=1)
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
        "=== JOB 43 PART P9d: COST PER 1,000 NODES (O Set, 200 FENs, Depth 12, PC20, Built-in Eval, Pinned Core 1) ===",
        f"exe_path: {b9_exe}",
        f"exe_sha256({b9_exe}): {b9_sha}",
        "variant_scope: IdeaB8_Fast covers IdeaB8 (078) only; it does nothing unless IdeaB8 is on (IdeaB8b is reported alone).",
        f"mean_all_off_4_runs  : {mean_off_4:.6f} ms / 1,000 nodes ({mean_off_4 * 1000.0:.3f} us / 1,000 nodes)",
        f"mean_all_off_forward : {mean_off_fwd:.6f} ms / 1,000 nodes",
        f"mean_all_off_reverse : {mean_off_rev:.6f} ms / 1,000 nodes",
        f"drift (rev / fwd)    : {mean_off_rev / mean_off_fwd:.6f}",
        "",
        "--- All 10 Runs in Execution Order (Forward 01..05, Reverse 06..10) ---",
        "  run_id                                 | pass | setting         | node_sum | wall_s  | ms/1k_nodes | us/1k_nodes | ratio_vs_mean4",
        "  ---------------------------------------+------+-----------------+----------+---------+-------------+-------------+---------------",
    ]
    for r in t_results:
        t_lines.append(
            f"  {r['stem']:<38s} | {r['pass']:<4s} | {r['setting']:<15s} | {r['node_sum']:>8d} | "
            f"{r['wall_s']:>7.4f} | {r['ms_per_1k']:>11.6f} | {r['us_per_1k']:>11.3f} | {r['ms_per_1k'] / mean_off_4:>13.6f}"
        )

    t_lines.extend(
        [
            "",
            "--- Forward + Reverse Paired Means per Setting ---",
            "  setting         | node_sum | fwd_ms/1k  | rev_ms/1k  | mean_ms/1k | mean_us/1k | ratio_vs_all_off",
            "  ----------------+----------+------------+------------+------------+------------+-----------------",
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
            f"  {sname:<15s} | {rf['node_sum']:>8d} | {rf['ms_per_1k']:>10.6f} | {rr['ms_per_1k']:>10.6f} | "
            f"{m_ms:>10.6f} | {m_us:>10.3f} | {m_ms / mean_off_4:>15.6f}"
        )

    b8_fast_over_b8 = paired_ms1k["B8_and_B8_Fast"] / paired_ms1k["only_B8"]
    b8_overhead_saved_pct = 100.0 * (paired_ms1k["only_B8"] - paired_ms1k["B8_and_B8_Fast"]) / max(1e-9, paired_ms1k["only_B8"] - mean_off_4)
    t_lines.extend(
        [
            "",
            f"  KEY RATIO: (IdeaB8 + IdeaB8_Fast) / (IdeaB8 alone) = {paired_ms1k['B8_and_B8_Fast']:.6f} / {paired_ms1k['only_B8']:.6f} = {b8_fast_over_b8:.6f}",
            f"  Incremental IdeaB8 overhead vs all_off cut by      : {b8_overhead_saved_pct:.2f}% (from +{(paired_ms1k['only_B8'] / mean_off_4 - 1.0) * 100.0:.2f}% to +{(paired_ms1k['B8_and_B8_Fast'] / mean_off_4 - 1.0) * 100.0:.2f}%)",
        ]
    )

    (JOB43 / "P9d_timing_summary.txt").write_text("\n".join(t_lines) + "\n", encoding="utf-8")
    out_lines.append("\n".join(t_lines))

    with open(JOB43 / "builds.txt", "a", encoding="utf-8") as bf:
        bf.write(
            "\n=== PART P9c..e BUNDLE9 BUILD (bundle8 + P9_B8_fast.patch.txt) ===\n"
            f"   patch path = {p9_patch_path}\n"
            f"   patch lines({p9_patch_path}) = {p9_nlines}\n"
            f"   patch sha256({p9_patch_path}) = {p9_sha}\n"
            f"   exe path = {b9_exe}\n"
            f"   exe sha256({b9_exe}) = {b9_sha}\n"
            f"   id_name = {get_id_name(b9_exe)}\n"
            f"   compile_flags = {b9_cf}\n"
            f"   link_flags    = {b9_lf}\n"
        )

    ok_ov, s_ov = fmt_cmp("PART P9c+P9d+P9e OVERALL", 1 if all_ok else 0, 1)
    out_lines.append("")
    out_lines.append(s_ov)
    out_lines.append(f"done_utc: {utc_now()}")
    (JOB43 / "P9cde_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
