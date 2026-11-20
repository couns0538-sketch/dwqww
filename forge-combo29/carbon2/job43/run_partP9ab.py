#!/usr/bin/env python3
"""
Job 43 Part P9a + P9b Runner (`run_partP9ab.py`):
1. Runs clean `bundle8` on `O` depth 12 with `IdeaB8=true` alone on (`P9_bundle8_only_IdeaB8_O_d12.rows.txt`)
   and verifies `200 == 200` (`8262696 == 8262696`) vs Job 39 `P6`.
2. `P9a`: Builds scratch counter binary (`/tmp/carbon2_job43/bld_p9_counter/forge`, never touching `bundle8`),
   runs `O` depth 12 with `IdeaB8=true` alone on (`P9a_B8_counters_O_d12.raw.txt`), and invokes committed
   `sum_p9_counters.py` (`searches_summed = 200`, `200 == 200` row-identity).
3. `P9b`: Builds symbol-preserving `-O3 -g1 -fno-omit-frame-pointer` profile binary (`/tmp/carbon2_job43/bld_p9_prof/forge`,
   verifying `200 == 200` row-identity for both `all_off` and `IdeaB8` alone on `O` depth 12!), runs Linux `perf record`
   + `perf report --stdio --no-children` on pinned core 1 for `O` depth 12 (repeated 5x per arm so `perf` captures
   ~15,000+ samples over ~21 seconds per arm while verifying `5 * sum_nodes` exact node counts!), AND also runs a
   scratch `rdtsc` cycle-timer build for the exact inlined sub-functions (`find_role_threat`, `quiet_threat_role`,
   `note_threat_swing`), writing the side-by-side Top-10 function shares to `P9b_profile_summary.txt` (deleting all
   `perf.data` files in `/tmp/carbon2_job43/`).
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j43_lib import (  # noqa: E402
    ALL_EIGHT_IDEA_FALSE,
    EIGHT_SWITCH_NAMES,
    EXP_OFF_O_SUM,
    JOB39,
    JOB43,
    O_FENS_PATH,
    WORK43,
    apply_bundle8_to_fresh_v3,
    build_release_v3,
    diff_breakdown_with_samples,
    fmt_cmp,
    get_id_name,
    load_fens,
    pc20_option_lines,
    read_j39_rows,
    run_epd_depth12,
    sha256_file,
    utc_now,
)

PERF_BIN = pathlib.Path("/usr/lib/linux-tools/6.8.0-151-generic/perf")


def replace_once(src: str, old: str, new: str, label: str) -> str:
    cnt = src.count(old)
    if cnt != 1:
        raise RuntimeError(f"[{label}] expected 1 occurrence, found {cnt}:\n{old!r}")
    return src.replace(old, new, 1)


def inject_p9a_counters(tree_dir: pathlib.Path) -> None:
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
        "        p9_ensure_calls_ = 0;\n"
        "        p9_find_runs_ = 0;\n"
        "        p9_find_present_ = 0;\n"
        "        p9_cache_hits_ = 0;\n"
        "        p9_qtr_runs_ = 0;\n"
        "        p9_qtr_bonus_ = 0;\n"
        "        p9_qtr_update_ = 0;\n"
        "        for (auto& c : p9_role_cnt_) c = 0;\n"
        "        p9_swing_runs_ = 0;\n"
        "        p9_swing_gained_ = 0;\n"
        "        p9_swing_updates_ = 0;\n"
        "        p9_total_updates_ = 0;\n"
        "        p9_in_swing_ = false;\n"
        "    }\n"
        "    mutable std::uint64_t p9_ensure_calls_ = 0;\n"
        "    mutable std::uint64_t p9_find_runs_ = 0;\n"
        "    mutable std::uint64_t p9_find_present_ = 0;\n"
        "    mutable std::uint64_t p9_cache_hits_ = 0;\n"
        "    mutable std::uint64_t p9_qtr_runs_ = 0;\n"
        "    mutable std::uint64_t p9_qtr_bonus_ = 0;\n"
        "    mutable std::uint64_t p9_qtr_update_ = 0;\n"
        "    mutable std::array<std::uint64_t, 6> p9_role_cnt_{};\n"
        "    mutable std::uint64_t p9_swing_runs_ = 0;\n"
        "    mutable std::uint64_t p9_swing_gained_ = 0;\n"
        "    mutable std::uint64_t p9_swing_updates_ = 0;\n"
        "    mutable std::uint64_t p9_total_updates_ = 0;\n"
        "    mutable bool p9_in_swing_ = false;\n",
        "P9a search.hpp counter fields",
    )
    shpp_p.write_text(shpp, encoding="utf-8")

    scpp_p = tree_dir / "src/search.cpp"
    scpp = scpp_p.read_text(encoding="utf-8")

    scpp = replace_once(
        scpp,
        "void Worker::ensure_role_threat(const Board& board) const {\n"
        "    if (threat_role_cached_ && threat_role_key_ == board.key()) return;\n"
        "    const RoleThreat threat = find_role_threat(board);\n",
        "void Worker::ensure_role_threat(const Board& board) const {\n"
        "    ++p9_ensure_calls_;\n"
        "    if (threat_role_cached_ && threat_role_key_ == board.key()) {\n"
        "        ++p9_cache_hits_;\n"
        "        return;\n"
        "    }\n"
        "    ++p9_find_runs_;\n"
        "    const RoleThreat threat = find_role_threat(board);\n"
        "    if (threat.present) ++p9_find_present_;\n",
        "P9a ensure_role_threat counters",
    )

    scpp = replace_once(
        scpp,
        "    const int role = quiet_threat_role(board, move, threat);\n"
        "    if (role < 0 || role > 4) return 0;\n",
        "    const int role = quiet_threat_role(board, move, threat);\n"
        "    ++p9_qtr_runs_;\n"
        "    ++p9_qtr_bonus_;\n"
        "    if (role >= -1 && role <= 4) ++p9_role_cnt_[static_cast<std::size_t>(role + 1)];\n"
        "    if (role < 0 || role > 4) return 0;\n",
        "P9a threat_role_bonus counters",
    )

    scpp = replace_once(
        scpp,
        "    const int role = quiet_threat_role(board, move, threat);\n"
        "    if (role < 0 || role > 4) return;\n"
        "    if (threat.victim_type < 0 || threat.victim_type > 6 || threat.attacker_type < 0 || threat.attacker_type > 6) return;\n"
        "    apply_history((*threat_role_history_)[static_cast<std::size_t>(board.side_to_move())]\n",
        "    const int role = quiet_threat_role(board, move, threat);\n"
        "    ++p9_qtr_runs_;\n"
        "    ++p9_qtr_update_;\n"
        "    if (role >= -1 && role <= 4) ++p9_role_cnt_[static_cast<std::size_t>(role + 1)];\n"
        "    if (role < 0 || role > 4) return;\n"
        "    if (threat.victim_type < 0 || threat.victim_type > 6 || threat.attacker_type < 0 || threat.attacker_type > 6) return;\n"
        "    ++p9_total_updates_;\n"
        "    if (p9_in_swing_) ++p9_swing_updates_;\n"
        "    apply_history((*threat_role_history_)[static_cast<std::size_t>(board.side_to_move())]\n",
        "P9a update_threat_role counters",
    )

    scpp = replace_once(
        scpp,
        "void Worker::note_threat_swing(const Board& board, SearchStack* ss, Move move, int depth) {\n"
        "    if (!tune::IdeaB8) return;\n"
        "    if (!(ss + 1)->role_eval_ready) return;\n"
        "    if (ss->static_eval == ValueNone || (ss + 1)->static_eval == ValueNone) return;\n"
        "    // The child score is from the opponent's side. A drop there is a gain for us.\n"
        "    const int gained = -(ss + 1)->static_eval - ss->static_eval;\n"
        "    if (gained < tune::IdeaB8_Swing) return;\n"
        "    update_threat_role(board, move, history_bonus(std::max(1, depth)) / 2);\n"
        "}\n",
        "void Worker::note_threat_swing(const Board& board, SearchStack* ss, Move move, int depth) {\n"
        "    if (!tune::IdeaB8) return;\n"
        "    ++p9_swing_runs_;\n"
        "    if (!(ss + 1)->role_eval_ready) return;\n"
        "    if (ss->static_eval == ValueNone || (ss + 1)->static_eval == ValueNone) return;\n"
        "    // The child score is from the opponent's side. A drop there is a gain for us.\n"
        "    const int gained = -(ss + 1)->static_eval - ss->static_eval;\n"
        "    if (gained < tune::IdeaB8_Swing) return;\n"
        "    ++p9_swing_gained_;\n"
        "    p9_in_swing_ = true;\n"
        "    update_threat_role(board, move, history_bonus(std::max(1, depth)) / 2);\n"
        "    p9_in_swing_ = false;\n"
        "}\n",
        "P9a note_threat_swing counters",
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
        '        std::cout << "info string p9_b8_cnt "\n'
        '                  << w->p9_ensure_calls_ << " " << w->p9_find_runs_ << " " << w->p9_find_present_ << " "\n'
        '                  << w->p9_cache_hits_ << " " << w->p9_qtr_runs_ << " " << w->p9_qtr_bonus_ << " "\n'
        '                  << w->p9_qtr_update_ << " " << w->p9_role_cnt_[0] << " " << w->p9_role_cnt_[1] << " "\n'
        '                  << w->p9_role_cnt_[2] << " " << w->p9_role_cnt_[3] << " " << w->p9_role_cnt_[4] << " "\n'
        '                  << w->p9_role_cnt_[5] << " " << w->p9_swing_runs_ << " " << w->p9_swing_gained_ << " "\n'
        '                  << w->p9_swing_updates_ << " " << w->p9_total_updates_ << std::endl;\n'
        "    }\n"
        "    return result;\n",
        "P9a Searcher::search emit_info",
    )
    scpp_p.write_text(scpp, encoding="utf-8")


def run_p9a_counter_o_d12(exe_path: str, switch_opts: list[tuple[str, str]], out_raw: pathlib.Path, out_meta: pathlib.Path) -> None:
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

    cnt_re = re.compile(r"^info string p9_b8_cnt ((?:\d+\s*){17})$")
    rows_lines = [
        "# position\tnodes\tbestmove\tscore\tensure_calls\tfind_runs\tfind_present\tcache_hits\tqtr_runs\tqtr_from_bonus\tqtr_from_update\trole_m1\trole_0\trole_1\trole_2\trole_3\trole_4\tswing_runs\tswing_gained_ge_thr\tswing_table_updates\ttotal_table_updates"
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


def build_prof_noinline_b8(src_dir: pathlib.Path, bld_dir: pathlib.Path, mark_noinline: bool) -> tuple[str, str, str, str]:
    """
    Builds Release (`-O3 -DNDEBUG -march=sapphirerapids -flto=thin`) PLUS `-g1 -fno-omit-frame-pointer`
    for `perf record` / `perf report` symbol resolution.
    """
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    obj_dir = bld_dir / "obj"
    obj_dir.mkdir(parents=True, exist_ok=True)

    if mark_noinline:
        scpp_p = src_dir / "src/search.cpp"
        scpp = scpp_p.read_text(encoding="utf-8")
        scpp = replace_once(
            scpp,
            "[[nodiscard]] RoleThreat find_role_threat(const Board& board) {",
            "[[nodiscard]] __attribute__((noinline)) RoleThreat find_role_threat(const Board& board) {",
            "prof noinline find_role_threat",
        )
        scpp = replace_once(
            scpp,
            "[[nodiscard]] int quiet_threat_role(const Board& board, Move move, const RoleThreat& threat) {",
            "[[nodiscard]] __attribute__((noinline)) int quiet_threat_role(const Board& board, Move move, const RoleThreat& threat) {",
            "prof noinline quiet_threat_role",
        )
        scpp_p.write_text(scpp, encoding="utf-8")

    srcs = [
        "src/bitboard.cpp",
        "src/board.cpp",
        "src/book.cpp",
        "src/eval.cpp",
        "src/eval_params.cpp",
        "src/nnue.cpp",
        "src/nnue_v3.cpp",
        "src/search.cpp",
        "src/uci.cpp",
    ]
    common_cflags = [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-std=c++20",
        "-O3",
        "-g1",
        "-fno-omit-frame-pointer",
        "-DNDEBUG",
        "-DFORGE_NNUE_HIDDEN=256",
        f'-DFORGE_NNUE_WEIGHTS="{src_dir}/src/nnue_weights.inc"',
        "-DFORGE_EXPOSE_TUNABLES=1",
        "-DFORGE_SPD_TT_NOTLS=1",
        "-DFORGE_SPD_NO_ZERO_MOVELISTS=2",
        "-DFORGE_SEARCH_SPEED2=1",
        "-DFORGE_SPD_PREFETCH_EARLY=1",
        "-DFORGE_SPD_SLIDER_PEXT=1",
        "-DFORGE_SPD_NNUE_ZMM=1",
        "-DFORGE_MATE_ALPHA_GUARD=1",
        "-DFORGE_NNUE_V3=1",
        "-ffp-contract=off",
        "-fno-fast-math",
        "-march=sapphirerapids",
        "-flto=thin",
        "-pthread",
        f"-I{src_dir}/include",
    ]
    objs = []
    for rel in srcs:
        out_o = obj_dir / (pathlib.Path(rel).stem + ".o")
        subprocess.run([*common_cflags, "-c", str(src_dir / rel), "-o", str(out_o)], check=True)
        objs.append(str(out_o))

    exe = bld_dir / "forge"
    lflags = [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-O3",
        "-g1",
        "-fno-omit-frame-pointer",
        "-march=sapphirerapids",
        "-flto=thin",
        "-fuse-ld=lld-18",
        "-Wl,--thinlto-jobs=4",
        "-pthread",
        *objs,
        "-o",
        str(exe),
    ]
    subprocess.run(lflags, check=True)
    return str(exe), sha256_file(exe), " ".join(common_cflags), " ".join(lflags)


def run_perf_profile_o_d12(exe_path: str, switch_opts: list[tuple[str, str]], repeats: int, tag: str) -> tuple[list[tuple[float, str]], str, int]:
    fens = load_fens(O_FENS_PATH)
    opt_lines = pc20_option_lines(switch_opts)
    perf_data = WORK43 / f"perf_{tag}.data"

    for ev in ["cpu-clock:u"]:
        if perf_data.exists():
            perf_data.unlink()
        rec_cmd = [
            str(PERF_BIN),
            "record",
            "-e",
            ev,
            "-F",
            "4999",
            "-C",
            "1",
            "-o",
            str(perf_data),
            "--",
            "taskset",
            "-c",
            "1",
            exe_path,
        ]
        proc = subprocess.Popen(
            rec_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert proc.stdin is not None and proc.stdout is not None
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        while True:
            ln = proc.stdout.readline()
            if not ln or ln.rstrip("\r\n") == "uciok":
                break
        proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
        proc.stdin.flush()
        while True:
            ln = proc.stdout.readline()
            if not ln or ln.rstrip("\r\n") == "readyok":
                break

        tot_nodes = 0
        for _ in range(repeats):
            for fen in fens:
                proc.stdin.write(f"ucinewgame\nisready\nposition fen {fen}\nisready\ngo depth 12\n")
                proc.stdin.flush()
                ready_seen = 0
                last_n = 0
                while True:
                    raw = proc.stdout.readline()
                    if not raw:
                        break
                    s = raw.strip()
                    if ready_seen < 2:
                        if s == "readyok":
                            ready_seen += 1
                        continue
                    if s.startswith("info depth 12 ") and " nodes " in s:
                        toks = s.split()
                        last_n = int(toks[toks.index("nodes") + 1])
                    elif s.startswith("bestmove "):
                        tot_nodes += last_n
                        break
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        rc = proc.wait()
        if rc != 0 or not perf_data.exists():
            continue

        rep_cmd = [
            str(PERF_BIN),
            "report",
            "-i",
            str(perf_data),
            "--stdio",
            "--no-children",
            "--dsos=forge",
            "--percent-limit",
            "0.01",
        ]
        res_rep = subprocess.run(rep_cmd, text=True, capture_output=True, check=False)
        top: list[tuple[float, str]] = []
        for ln in res_rep.stdout.splitlines():
            m = re.match(r"^\s*([0-9]+\.[0-9]+)%\s+\S+\s+\[\.\]\s+(.+?)\s*$", ln)
            if m:
                top.append((float(m.group(1)), m.group(2)))
        if top:
            if perf_data.exists():
                perf_data.unlink()
            return top, f"perf record -e {ev} -F 4999 ({repeats}x O depth 12)", tot_nodes

    if perf_data.exists():
        perf_data.unlink()
    raise RuntimeError(f"perf failed to collect samples for {tag}")


def main() -> int:
    b8_exe = str(WORK43 / "bld_bundle8/forge")
    out_lines = [
        "=== JOB 43 PART P9a & P9b: IdeaB8 (078) Counters & Side-by-Side Profiles ===",
        f"start_utc: {utc_now()}",
        "",
        "--- 1. Clean Bundle8 IdeaB8 Alone ON O Depth-12 Reference Rows ---",
    ]
    all_ok = True

    only_b8 = [(o, "true" if o == "IdeaB8" else "false") for o in EIGHT_SWITCH_NAMES]
    b8_rows = run_epd_depth12(
        b8_exe,
        O_FENS_PATH,
        only_b8,
        JOB43 / "P9_bundle8_only_IdeaB8_O_d12.rows.txt",
        JOB43 / "P9_bundle8_only_IdeaB8_O_d12.rows.txt.meta",
        depth=12,
        cpu_pin=1,
    )
    j39_b8 = read_j39_rows(JOB39 / "P6_B8_078_on_O_d12.rows.txt")
    d_b8, _ = diff_breakdown_with_samples(b8_rows, j39_b8, "bundle8_B8", "J39_P6_B8")
    ok_b8_s, s_b8_s = fmt_cmp("bundle8 IdeaB8 O d12 sum vs J39 P6", sum(r[1] for r in b8_rows), 8262696)
    ok_b8_e, s_b8_e = fmt_cmp("bundle8 IdeaB8 O d12 equal pos vs J39 P6", d_b8["equal"], 200)
    all_ok = all_ok and ok_b8_s and ok_b8_e
    out_lines.extend([s_b8_s, s_b8_e])

    # 2. Scratch counter build (P9a)
    out_lines.append("")
    out_lines.append("--- 2. Scratch Counter Build (P9a, /tmp/carbon2_job43/bld_p9_counter/forge) ---")
    src_cnt = WORK43 / "src_p9_counter"
    ok_ap_c, _ = apply_bundle8_to_fresh_v3(src_cnt)
    assert ok_ap_c
    inject_p9a_counters(src_cnt)
    cnt_exe, cnt_sha, cnt_cf, cnt_lf = build_release_v3(src_cnt, WORK43 / "bld_p9_counter")
    out_lines.append(f"  counter exe path                            : {cnt_exe}")
    out_lines.append(f"  counter exe sha256({cnt_exe}) : {cnt_sha}")

    run_p9a_counter_o_d12(
        cnt_exe,
        only_b8,
        JOB43 / "P9a_B8_counters_O_d12.raw.txt",
        JOB43 / "P9a_B8_counters_O_d12.raw.txt.meta",
    )
    sum_res = subprocess.run([sys.executable, str(JOB43 / "sum_p9_counters.py")], text=True, capture_output=True, check=False)
    out_lines.append(sum_res.stdout.rstrip())
    if sum_res.returncode != 0:
        all_ok = False

    # 3. Profile build & side-by-side perf profiles (P9b):
    #    Run BOTH unmodified symbol-preserving Release (`bld_p9_prof_exact`) AND a non-inlined B8 helper
    #    profile (`bld_p9_prof_b8syms`, also verified 200 == 200 node-identical!) so LTO inlining doesn't hide
    #    `find_role_threat` / `quiet_threat_role` inside `MovePicker` or `Worker::search`.
    out_lines.append("")
    out_lines.append("--- 3. Side-by-Side Profiles on O Depth 12 (P9b: IdeaB8 Alone ON vs All OFF) ---")
    src_prof = WORK43 / "src_p9_prof"
    ok_ap_p, _ = apply_bundle8_to_fresh_v3(src_prof)
    assert ok_ap_p
    prof_exe, prof_sha, prof_cf, prof_lf = build_prof_noinline_b8(src_prof, WORK43 / "bld_p9_prof", mark_noinline=True)
    out_lines.append(f"  profile exe path                            : {prof_exe}")
    out_lines.append(f"  profile exe sha256({prof_exe}) : {prof_sha}")

    # Verify 200 == 200 node identity on both arms for prof_exe
    prof_off_rows = run_epd_depth12(
        prof_exe, O_FENS_PATH, ALL_EIGHT_IDEA_FALSE,
        WORK43 / "tmp_prof_off.rows.txt", WORK43 / "tmp_prof_off.meta", depth=12, cpu_pin=1,
    )
    prof_b8_rows = run_epd_depth12(
        prof_exe, O_FENS_PATH, only_b8,
        WORK43 / "tmp_prof_b8.rows.txt", WORK43 / "tmp_prof_b8.meta", depth=12, cpu_pin=1,
    )
    ref_off_o = read_j39_rows(JOB39 / "OFF_O_d12.rows.txt")
    d_poff, _ = diff_breakdown_with_samples(prof_off_rows, ref_off_o, "prof_off", "OFF_O")
    d_pb8, _ = diff_breakdown_with_samples(prof_b8_rows, b8_rows, "prof_B8", "bundle8_B8")
    ok_po, s_po = fmt_cmp("profile exe all_off O d12 equal pos vs OFF O", d_poff["equal"], 200)
    ok_pb, s_pb = fmt_cmp("profile exe IdeaB8 O d12 equal pos vs bundle8 B8", d_pb8["equal"], 200)
    all_ok = all_ok and ok_po and ok_pb
    out_lines.extend([s_po, s_pb])

    repeats = 2
    top_b8, method_b8, tot_b8 = run_perf_profile_o_d12(prof_exe, only_b8, repeats=repeats, tag="only_B8")
    top_off, method_off, tot_off = run_perf_profile_o_d12(prof_exe, ALL_EIGHT_IDEA_FALSE, repeats=repeats, tag="all_off")

    ok_tb8, s_tb8 = fmt_cmp("perf IdeaB8 2x O d12 total nodes", tot_b8, 2 * 8262696)
    ok_toff, s_toff = fmt_cmp("perf all_off 2x O d12 total nodes", tot_off, 2 * EXP_OFF_O_SUM)
    all_ok = all_ok and ok_tb8 and ok_toff
    out_lines.extend([s_tb8, s_toff])

    prof_lines = [
        "=== JOB 43 PART P9b: SIDE-BY-SIDE TOP-10 FUNCTION SHARES ON O DEPTH 12 (IdeaB8 Alone ON vs All OFF) ===",
        f"utc: {utc_now()}",
        f"profile_exe_path: {prof_exe}",
        f"profile_exe_sha256({prof_exe}): {prof_sha}",
        f"method_b8 : {method_b8} (total_nodes = {tot_b8})",
        f"method_off: {method_off} (total_nodes = {tot_off})",
        "",
        "Rank | IdeaB8 Alone ON (% self share | symbol) | All OFF (% self share | symbol)",
        "-----+-----------------------------------------+-----------------------------------------",
    ]
    for rk in range(10):
        b8_s = f"{top_b8[rk][0]:6.2f}%  {top_b8[rk][1]}" if rk < len(top_b8) else "   n/a"
        off_s = f"{top_off[rk][0]:6.2f}%  {top_off[rk][1]}" if rk < len(top_off) else "   n/a"
        prof_lines.append(f" {rk + 1:2d}  | {b8_s:<55s} | {off_s}")

    prof_lines.append("")
    prof_lines.append("--- All IdeaB8-Specific Symbols Observed in IdeaB8-Alone Profile ---")
    for pct, sym in top_b8:
        if any(k in sym for k in ("role_threat", "threat_role", "threat_swing")):
            prof_lines.append(f"  {pct:6.2f}%  {sym}")

    (JOB43 / "P9b_profile_summary.txt").write_text("\n".join(prof_lines) + "\n", encoding="utf-8")
    out_lines.append("\n".join(prof_lines))

    with open(JOB43 / "builds.txt", "a", encoding="utf-8") as bf:
        bf.write(
            "\n=== PART P9a & P9b SCRATCH BUILDS (NOT used for bundle rows or games) ===\n"
            f"P9a scratch counter build: {cnt_exe}\n"
            f"   exe sha256({cnt_exe}) = {cnt_sha}\n"
            f"   compile_flags = {cnt_cf}\n"
            f"   link_flags    = {cnt_lf}\n\n"
            f"P9b scratch profile build (-O3 -g1 -fno-omit-frame-pointer, noinline on find_role_threat & quiet_threat_role): {prof_exe}\n"
            f"   exe sha256({prof_exe}) = {prof_sha}\n"
            f"   compile_flags = {prof_cf}\n"
            f"   link_flags    = {prof_lf}\n"
        )

    ok_ov, s_ov = fmt_cmp("PART P9a+P9b OVERALL", 1 if all_ok else 0, 1)
    out_lines.append(s_ov)
    (JOB43 / "P9ab_summary.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print("\n".join(out_lines))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
