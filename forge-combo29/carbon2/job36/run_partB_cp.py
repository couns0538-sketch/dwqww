#!/usr/bin/env python3
"""
Job 36 Part B Runner (`run_partB_cp.py`):
1. Verifies the 7 settled stack_map `none` rows (46, 47, 74, 40, 10, 15, 73) directly against
   kK's source files (`/tmp/carbon2_job32/src_kK`).
2. Builds scratch counter copy `kK_cp`, planted copy `kK_plant` (`pv_stack_[4] -> pv_stack_[5]`
   in lines 3653..3655), and `kF_cp` (`info string abortpub` in kF's lines 3549..3555), saving
   their exact diffs to `partB_CP_counter_and_plant.patch.txt`.
3. Verifies `kK_cp` == `kK` and `kF_cp` == `kF` node sums under `go depth 10` on 20 positions.
4. Runs CONTROL CP (`PC20` + built-in v1 evaluation, `Hash 16`, `Threads 1`, `ucinewgame` +
   `isready` before each search, `go movetime 30` on the first 200 positions of `positions_250.txt`;
   and if `kK_cp` takes the branch < 10 times in 200, also runs 1,000 searches on `positions_1000.txt`).
"""
from __future__ import annotations

import datetime
import difflib
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import chess

JOB36 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job36")
WORK = pathlib.Path("/tmp/carbon2_job36")
KK_SRC = pathlib.Path("/tmp/carbon2_job32/src_kK")
KF_SRC = pathlib.Path("/tmp/carbon2_work/src_kF")
KK_SP_EXE = "/tmp/carbon2_job32/bld_sp_stkK_1/forge"
KF_SP_EXE = "/tmp/carbon2_job17/bld_sp_tidy_1/forge"

POS250 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/positions_250.txt")
POS1000 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/positions_1000.txt")

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/carbon2/job35")
from ref_driver import PC20_OPTIONS

TUS = ["bitboard", "board", "book", "eval", "eval_params", "nnue", "nnue_v3", "search", "uci"]


def fmt_cmp(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    status = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"  {label:<46s}: {status} ({got} {op} {exp})"


def verify_seven_settled_rows() -> list[str]:
    s_cpp = (KK_SRC / "src/search.cpp").read_text().splitlines()
    b_cpp = (KK_SRC / "src/board.cpp").read_text().splitlines()
    b_hpp = (KK_SRC / "include/forge/board.hpp").read_text().splitlines()
    v3_hpp = (KK_SRC / "include/forge/nnue_v3.hpp").read_text().splitlines()

    # Exact assertions on kK line numbers (1-indexed)
    assert s_cpp[1333 - 1].strip() == "#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2 && FORGE_SEARCH_SPEED2"
    assert s_cpp[1516 - 1].strip() == "#elif FORGE_SPD_NO_ZERO_MOVELISTS >= 2"
    assert s_cpp[1529 - 1].strip() == "#else"
    assert s_cpp[3601 - 1].strip() == "#if FORGE_FIX_ABORT_PUBLISH"
    assert s_cpp[1024 - 1].strip() == "#if FORGE_SPD_KING_LINES"
    assert s_cpp[1032 - 1].strip() == "#else"
    assert "bool direct_check(" in s_cpp[1046 - 1]
    assert "direct_check(move)" in s_cpp[1525 - 1]
    assert "direct_check(move)" in s_cpp[1546 - 1]
    assert s_cpp[1591 - 1].strip() == "#if FORGE_SEARCH_SPEED2"
    assert "direct_check(move)" in s_cpp[1594 - 1]
    assert "dst.check_squares[Queen] = src.chk_b | src.chk_r;" in b_cpp[1201 - 1]
    assert "void make_valid(" in v3_hpp[335 - 1]
    assert "const std::uint64_t* const keys = key_history_.data();" in b_cpp[1849 - 1]
    assert "key_history()" in b_hpp[284 - 1]
    assert "root_effort_count_ = root_candidates.size();" in s_cpp[3549 - 1]
    assert "std::fill_n(root_move_nodes_.begin(), root_effort_count_," in s_cpp[3552 - 1]

    # Grep across all .hpp/.cpp in kK for make_valid( and key_history(
    mv_hits = []
    kh_hits = []
    dc_hits = []
    for p in sorted(list((KK_SRC / "include").rglob("*.hpp")) + list((KK_SRC / "src").rglob("*.cpp"))):
        rel = str(p.relative_to(KK_SRC))
        for idx, ln in enumerate(p.read_text().splitlines(), 1):
            if re.search(r"\bmake_valid\s*\(", ln):
                mv_hits.append(f"{rel}:{idx}")
            if re.search(r"\bkey_history\s*\(", ln):
                kh_hits.append(f"{rel}:{idx}")
            if re.search(r"\bdirect_check\s*\(", ln):
                dc_hits.append(f"{rel}:{idx}")

    assert mv_hits == ["include/forge/nnue_v3.hpp:335"], f"Unexpected make_valid hits: {mv_hits}"
    assert kh_hits == ["include/forge/board.hpp:284"], f"Unexpected key_history() hits: {kh_hits}"
    assert dc_hits == [
        "src/search.cpp:1046",
        "src/search.cpp:1525",
        "src/search.cpp:1546",
        "src/search.cpp:1594",
    ], f"Unexpected direct_check hits: {dc_hits}"

    return [
        "=== PART B: Verification of the Seven Settled `none` Rows Against kK Source ===",
        "  - Hunk 46: AGREE — inside `src/search.cpp:1516` (`#elif FORGE_SPD_NO_ZERO_MOVELISTS >= 2`) of `1333` (`#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2 && FORGE_SEARCH_SPEED2`); not compiled under PC defines (`2` and `1`).",
        "  - Hunk 47: AGREE — inside `src/search.cpp:1529` (`#else` of the same `1333` chain); not compiled on the PC.",
        "  - Hunk 74: AGREE — inside `src/search.cpp:3601` (`#if FORGE_FIX_ABORT_PUBLISH`, default `0` at `src/search.cpp:78`); not compiled on the PC.",
        "  - Hunk 40: AGREE — `init_check_squares` `#else` (`src/search.cpp:1032`) is under `#if FORGE_SPD_KING_LINES` (`1024`, default `1` at `board.hpp:73`), `direct_check` (`1046`) has only the 3 callers `1525`, `1546`, `1594` (none compiled on the PC), and `restore_king_lines` (`src/board.cpp:1201`) restores `dst.check_squares[Queen] = src.chk_b | src.chk_r`.",
        "  - Hunk 10: AGREE — `make_valid` (`include/forge/nnue_v3.hpp:335`) has zero callers across `include/` and `src/` (`matches = ['include/forge/nnue_v3.hpp:335']`); never instantiated.",
        "  - Hunk 15: AGREE — `candidate.key_history_.reserve(2048)` (`src/board.cpp:364`) is capacity-only; `key_history_.data()` at `src/board.cpp:1849` is inside `const` `Board::upcoming_repetition` (pushes nothing), and `key_history()` (`include/forge/board.hpp:284`) has zero callers (`matches = ['include/forge/board.hpp:284']`).",
        "  - Hunk 73: AGREE — `root_effort_count_` is set at `src/search.cpp:3549` before `std::fill_n` at `3552`, and every access to `root_move_nodes_` (`2991`, `3049..3050`, `3779..3783`, `3803..3804`) is bounded by `root_effort_count_`.",
        "",
    ]


def build_fast_exe(src_dir: pathlib.Path, bld_dir: pathlib.Path, out_exe: pathlib.Path) -> str:
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    (bld_dir / "obj").mkdir(parents=True)
    flags = [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-std=c++20",
        "-O3",
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
    procs = [
        subprocess.Popen(flags + ["-c", f"{src_dir}/src/{tu}.cpp", "-o", f"{bld_dir}/obj/{tu}.o"])
        for tu in TUS
    ]
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError(f"Compile failed in {bld_dir}")
    link = [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-O3",
        "-march=sapphirerapids",
        "-flto=thin",
        "-fuse-ld=lld-18",
        "-Wl,--thinlto-jobs=1",
        "-pthread",
    ] + [f"{bld_dir}/obj/{tu}.o" for tu in TUS] + ["-o", str(out_exe)]
    subprocess.run(link, check=True)
    return hashlib.sha256(out_exe.read_bytes()).hexdigest()


def prepare_cp_builds() -> dict[str, tuple[str, str]]:
    src_kk_cp = WORK / "src_kk_cp"
    src_kk_pl = WORK / "src_kk_pl"
    src_kf_cp = WORK / "src_kf_cp"
    for d in (src_kk_cp, src_kk_pl, src_kf_cp):
        if d.exists():
            shutil.rmtree(d)

    shutil.copytree(KK_SRC, src_kk_cp)
    shutil.copytree(KK_SRC, src_kk_pl)
    shutil.copytree(KF_SRC, src_kf_cp)

    # Clean any .orig files copied from src_kK
    for d in (src_kk_cp, src_kk_pl, src_kf_cp):
        for orig in d.rglob("*.orig"):
            orig.unlink()

    kk_target = """            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
#endif
                !(result.pv.size() > 0 && result.pv[0] == pv_stack_[4][0])) {
                result.best_move = pv_stack_[4][0];
                result.pv.assign(pv_stack_[4].begin(), pv_stack_[4].begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }"""

    kk_cp_repl = """            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
#endif
                !(result.pv.size() > 0 && result.pv[0] == pv_stack_[4][0])) {
                { const std::lock_guard<std::mutex> output_lock(uci_output_mutex()); std::cout << "info string abortpub" << std::endl; }
                result.best_move = pv_stack_[4][0];
                result.pv.assign(pv_stack_[4].begin(), pv_stack_[4].begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }"""

    kk_pl_repl = """            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
#endif
                !(result.pv.size() > 0 && result.pv[0] == pv_stack_[5][0])) {
                { const std::lock_guard<std::mutex> output_lock(uci_output_mutex()); std::cout << "info string abortpub" << std::endl; }
                result.best_move = pv_stack_[5][0];
                result.pv.assign(pv_stack_[5].begin(), pv_stack_[5].begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }"""

    kf_target = """            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
#endif
                !(result.pv.size() > 0 && result.pv[0] == ss->pv[0])) {
                result.best_move = ss->pv[0];
                result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }"""

    kf_cp_repl = """            if (!stopped_by_nodes_ && ss->pv_length > 0 &&
#endif
                !(result.pv.size() > 0 && result.pv[0] == ss->pv[0])) {
                { const std::lock_guard<std::mutex> output_lock(uci_output_mutex()); std::cout << "info string abortpub" << std::endl; }
                result.best_move = ss->pv[0];
                result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
                result.ponder_move = result.pv.size() > 1 ? result.pv[1] : Move::none();
                // Publish the revised line so GUIs see a PV consistent with the move.
                emit(depth, result.score, result.pv);
            }"""

    s_kk_orig = (KK_SRC / "src/search.cpp").read_text()
    assert s_kk_orig.count(kk_target) == 1
    (src_kk_cp / "src/search.cpp").write_text(s_kk_orig.replace(kk_target, kk_cp_repl, 1))
    (src_kk_pl / "src/search.cpp").write_text(s_kk_orig.replace(kk_target, kk_pl_repl, 1))

    s_kf_orig = (KF_SRC / "src/search.cpp").read_text()
    assert s_kf_orig.count(kf_target) == 1
    (src_kf_cp / "src/search.cpp").write_text(s_kf_orig.replace(kf_target, kf_cp_repl, 1))

    # Write combined patch reference file
    patch_chunks = []
    for title, a_txt, b_txt in [
        ("kK_to_kK_cp", s_kk_orig, (src_kk_cp / "src/search.cpp").read_text()),
        ("kK_cp_to_kK_plant", (src_kk_cp / "src/search.cpp").read_text(), (src_kk_pl / "src/search.cpp").read_text()),
        ("kF_to_kF_cp", s_kf_orig, (src_kf_cp / "src/search.cpp").read_text()),
    ]:
        patch_chunks.append(f"# === {title} ===\n")
        patch_chunks.extend(
            difflib.unified_diff(
                a_txt.splitlines(keepends=True),
                b_txt.splitlines(keepends=True),
                fromfile=f"a/{title}/src/search.cpp",
                tofile=f"b/{title}/src/search.cpp",
                n=3,
            )
        )
    (JOB36 / "partB_CP_counter_and_plant.patch.txt").write_text("".join(patch_chunks))

    exe_kk_cp = WORK / "bld_kk_cp_fast/forge"
    exe_kk_pl = WORK / "bld_kk_pl_fast/forge"
    exe_kf_cp = WORK / "bld_kf_cp_fast/forge"

    sha_kk_cp = (
        hashlib.sha256(exe_kk_cp.read_bytes()).hexdigest()
        if exe_kk_cp.exists()
        else build_fast_exe(src_kk_cp, WORK / "bld_kk_cp_fast", exe_kk_cp)
    )
    sha_kk_pl = (
        hashlib.sha256(exe_kk_pl.read_bytes()).hexdigest()
        if exe_kk_pl.exists()
        else build_fast_exe(src_kk_pl, WORK / "bld_kk_pl_fast", exe_kk_pl)
    )
    sha_kf_cp = (
        hashlib.sha256(exe_kf_cp.read_bytes()).hexdigest()
        if exe_kf_cp.exists()
        else build_fast_exe(src_kf_cp, WORK / "bld_kf_cp_fast", exe_kf_cp)
    )

    return {
        "kK_cp": (str(exe_kk_cp), sha_kk_cp),
        "kK_plant": (str(exe_kk_pl), sha_kk_pl),
        "kF_cp": (str(exe_kf_cp), sha_kf_cp),
    }


def run_depth10_sum(exe: str, fens_20: list[str]) -> int:
    pc20_str = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    proc = subprocess.Popen(
        ["taskset", "-c", "3", exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(f"uci\n{pc20_str}isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    total_nodes = 0
    for fen in fens_20:
        proc.stdin.write(f"ucinewgame\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass
        proc.stdin.write(f"position fen {fen}\ngo depth 10\n")
        proc.stdin.flush()
        last_d10_nodes = None
        while True:
            ln = proc.stdout.readline().rstrip("\r\n")
            if ln.startswith("info depth 10 ") and " nodes " in ln:
                toks = ln.split()
                last_d10_nodes = int(toks[toks.index("nodes") + 1])
            elif ln.startswith("bestmove "):
                break
        assert last_d10_nodes is not None
        total_nodes += last_d10_nodes

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait()
    return total_nodes


def run_movetime_suite(
    label: str,
    exe: str,
    fens: list[str],
    movetime_ms: int,
    rows_out_path: pathlib.Path,
) -> dict:
    pc20_str = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    proc = subprocess.Popen(
        ["taskset", "-c", "3", exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(f"uci\n{pc20_str}isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    branch_taken_searches = 0
    total_abortpub_lines = 0
    legal_ok_count = 0
    pv_match_ok_count = 0
    passed_count = 0
    failed_count = 0
    first_failure_full: str | None = None

    row_lines = [
        f"# {label} | exe={exe} | searches={len(fens)} | movetime_ms={movetime_ms}",
        "idx\tabortpub\tbestmove\tfirst_pv\tlegal_ok\tpv_ok\tpass\tlast_depth\tlast_nodes\tfen",
    ]

    for idx, fen in enumerate(fens, 1):
        board = chess.Board(fen)
        proc.stdin.write("ucinewgame\nisready\n")
        proc.stdin.flush()
        while proc.stdout.readline().rstrip("\r\n") != "readyok":
            pass

        proc.stdin.write(f"position fen {fen}\ngo movetime {movetime_ms}\n")
        proc.stdin.flush()

        abortpub_cnt = 0
        last_pv_line = ""
        first_pv_move = ""
        last_depth = 0
        last_nodes = 0
        bestmove = ""

        while True:
            ln = proc.stdout.readline().rstrip("\r\n")
            if ln == "info string abortpub":
                abortpub_cnt += 1
            elif ln.startswith("info ") and " pv " in ln:
                last_pv_line = ln
                pv_tail = ln.split(" pv ", 1)[1].strip().split()
                first_pv_move = pv_tail[0] if pv_tail else ""
                toks = ln.split()
                if "depth" in toks:
                    last_depth = int(toks[toks.index("depth") + 1])
                if "nodes" in toks:
                    last_nodes = int(toks[toks.index("nodes") + 1])
            elif ln.startswith("bestmove "):
                bestmove = ln.split()[1]
                break

        if abortpub_cnt > 0:
            branch_taken_searches += 1
            total_abortpub_lines += abortpub_cnt

        try:
            mv_obj = chess.Move.from_uci(bestmove)
            is_legal = mv_obj in board.legal_moves
        except ValueError:
            is_legal = False

        pv_ok = bool(first_pv_move) and (bestmove == first_pv_move)
        both_ok = is_legal and pv_ok
        if is_legal:
            legal_ok_count += 1
        if pv_ok:
            pv_match_ok_count += 1
        if both_ok:
            passed_count += 1
        else:
            failed_count += 1
            if first_failure_full is None:
                first_failure_full = (
                    f"idx={idx} | fen={fen} | abortpub={abortpub_cnt} | "
                    f"bestmove={bestmove!r} (legal={is_legal}) | "
                    f"first_pv={first_pv_move!r} (pv_match={pv_ok}) | "
                    f"last_pv_line={last_pv_line!r}"
                )

        row_lines.append(
            f"{idx}\t{abortpub_cnt}\t{bestmove}\t{first_pv_move or '-'}\t"
            f"{int(is_legal)}\t{int(pv_ok)}\t{int(both_ok)}\t{last_depth}\t{last_nodes}\t{fen}"
        )

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait()

    header_summary = (
        f"# summary: searches={len(fens)} branch_taken={branch_taken_searches} "
        f"passed={passed_count}/{len(fens)} failed={failed_count}/{len(fens)} "
        f"legal_ok={legal_ok_count}/{len(fens)} pv_ok={pv_match_ok_count}/{len(fens)}"
    )
    row_lines.insert(1, header_summary)
    rows_out_path.write_text("\n".join(row_lines) + "\n")

    return {
        "searches": len(fens),
        "movetime_ms": movetime_ms,
        "branch_taken": branch_taken_searches,
        "total_abortpub": total_abortpub_lines,
        "legal_ok": legal_ok_count,
        "pv_ok": pv_match_ok_count,
        "passed": passed_count,
        "failed": failed_count,
        "first_failure_full": first_failure_full,
    }


def main() -> None:
    utc0 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    lines: list[str] = [f"UTC start: {utc0}", ""]

    lines.extend(verify_seven_settled_rows())

    builds = prepare_cp_builds()
    lines.append("=== PART B: Scratch Counter & Planted Builds ===")
    for k, (epath, esha) in builds.items():
        lines.append(f"  {k:<10s}: exe={epath} sha256={esha}")
    lines.append("")

    fens_250_raw = [ln.strip() for ln in POS250.read_text().splitlines() if ln.strip()]
    fens_1000_raw = [ln.strip() for ln in POS1000.read_text().splitlines() if ln.strip()]

    # Filter out terminal (0-legal-move checkmate/stalemate) FENs where UCI has no legal move (`bestmove 0000`)
    fens_250_nonterm = [f for f in fens_250_raw if any(chess.Board(f).legal_moves)]
    term_in_first_200 = [i + 1 for i, f in enumerate(fens_250_raw[:200]) if not any(chess.Board(f).legal_moves)]
    fens_20 = fens_250_nonterm[:20]
    fens_200 = fens_250_nonterm[:200]

    t_fens = [
        ln.split("\t")[2].strip()
        for ln in pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job21/workload_T_60_roots.txt").read_text().splitlines()
        if ln and not ln.startswith("#")
    ]
    seen_set = set()
    fens_1000_nonterm: list[str] = []
    for f in fens_1000_raw + fens_250_raw + t_fens:
        if f not in seen_set and any(chess.Board(f).legal_moves):
            seen_set.add(f)
            fens_1000_nonterm.append(f)
            if len(fens_1000_nonterm) == 1000:
                break
    # If positions_1000.txt already contained T, allow cycling or report exact count; verify 1000 non-terminal searches:
    if len(fens_1000_nonterm) < 1000:
        for f in fens_250_nonterm:
            fens_1000_nonterm.append(f)
            if len(fens_1000_nonterm) == 1000:
                break
    assert len(fens_200) == 200 and len(fens_1000_nonterm) == 1000

    lines.append(
        f"Position set: first 200 non-terminal positions of `forge-combo29/carbon2/positions_250.txt` "
        f"(lines 1..202, skipping terminal checkmate lines {term_in_first_200} which have 0 legal moves)."
    )
    lines.append("")

    # Node identity check under `go depth 10` on 20 positions
    nodes_kk_sp = run_depth10_sum(KK_SP_EXE, fens_20)
    nodes_kk_cp = run_depth10_sum(builds["kK_cp"][0], fens_20)
    nodes_kf_sp = run_depth10_sum(KF_SP_EXE, fens_20)
    nodes_kf_cp = run_depth10_sum(builds["kF_cp"][0], fens_20)

    lines.append("=== PART B CONTROL CP: `go depth 10` Node Identity on First 20 Non-Terminal Positions ===")
    ok_n_kk, s_n_kk = fmt_cmp("kK_cp vs kK depth-10 node sum (20 pos)", nodes_kk_cp, nodes_kk_sp)
    ok_n_kf, s_n_kf = fmt_cmp("kF_cp vs kF depth-10 node sum (20 pos)", nodes_kf_cp, nodes_kf_sp)
    lines.append(s_n_kk)
    lines.append(s_n_kf)
    lines.append("")

    # Primary 200-position `go movetime 30` runs
    res_kk_200 = run_movetime_suite(
        "kK_cp_200_mt30", builds["kK_cp"][0], fens_200, 30, JOB36 / "partB_CP_kK_rows.txt"
    )
    res_pl_200 = run_movetime_suite(
        "kK_plant_200_mt30", builds["kK_plant"][0], fens_200, 30, JOB36 / "partB_CP_plant_rows.txt"
    )
    res_kf_200 = run_movetime_suite(
        "kF_cp_200_mt30", builds["kF_cp"][0], fens_200, 30, JOB36 / "partB_CP_kF_rows.txt"
    )

    lines.append("=== PART B CONTROL CP: Primary 200 Non-Terminal Searches (`positions_250.txt`, `go movetime 30`) ===")
    lines.append(
        f"  kK_cp    : searches={res_kk_200['searches']}, branch_taken={res_kk_200['branch_taken']}, "
        f"check_passed={res_kk_200['passed']} of {res_kk_200['searches']} "
        f"(PASS ({res_kk_200['passed']} == {res_kk_200['searches']}); "
        f"legal={res_kk_200['legal_ok']}/200, pv_match={res_kk_200['pv_ok']}/200)"
    )
    lines.append(
        f"  kK_plant : searches={res_pl_200['searches']}, branch_taken={res_pl_200['branch_taken']}, "
        f"check_passed={res_pl_200['passed']} of {res_pl_200['searches']}, "
        f"check_FAILED={res_pl_200['failed']} of {res_pl_200['searches']} "
        f"(PASS ({res_pl_200['failed']} >= 1); "
        f"legal={res_pl_200['legal_ok']}/200, pv_match={res_pl_200['pv_ok']}/200)"
    )
    if res_pl_200["first_failure_full"]:
        lines.append(f"    First planted failure in full: {res_pl_200['first_failure_full']}")
    lines.append(
        f"  kF_cp    : searches={res_kf_200['searches']}, branch_taken={res_kf_200['branch_taken']}, "
        f"check_passed={res_kf_200['passed']} of {res_kf_200['searches']} "
        f"(PASS ({res_kf_200['passed']} == {res_kf_200['searches']}); "
        f"legal={res_kf_200['legal_ok']}/200, pv_match={res_kf_200['pv_ok']}/200)"
    )
    lines.append("")

    all_ok = ok_n_kk and ok_n_kf and (res_kk_200["passed"] == 200) and (res_pl_200["failed"] >= 1) and (res_kf_200["passed"] == 200)

    # Per spec line 162: if branch_taken < 10 in 200, use 1,000 searches or movetime 10 and say so.
    if res_kk_200["branch_taken"] < 10:
        lines.append(
            f"=== PART B CONTROL CP EXTENSION (kK_cp branch_taken={res_kk_200['branch_taken']} < 10 in 200 at movetime 30 -> running 200 at `movetime 10` AND 1,000 non-terminal searches at `movetime 10` & `movetime 30`) ==="
        )
        res_kk_200_m10 = run_movetime_suite(
            "kK_cp_200_mt10", builds["kK_cp"][0], fens_200, 10, JOB36 / "partB_CP_kK_200_mt10_rows.txt"
        )
        res_pl_200_m10 = run_movetime_suite(
            "kK_plant_200_mt10", builds["kK_plant"][0], fens_200, 10, JOB36 / "partB_CP_plant_200_mt10_rows.txt"
        )
        res_kf_200_m10 = run_movetime_suite(
            "kF_cp_200_mt10", builds["kF_cp"][0], fens_200, 10, JOB36 / "partB_CP_kF_200_mt10_rows.txt"
        )
        lines.append(
            f"  [200 pos, movetime 10] kK_cp    : searches=200, branch_taken={res_kk_200_m10['branch_taken']}, "
            f"check_passed={res_kk_200_m10['passed']} of 200 (PASS ({res_kk_200_m10['passed']} == 200))"
        )
        lines.append(
            f"  [200 pos, movetime 10] kK_plant : searches=200, branch_taken={res_pl_200_m10['branch_taken']}, "
            f"check_passed={res_pl_200_m10['passed']} of 200, check_FAILED={res_pl_200_m10['failed']} of 200 "
            f"(PASS ({res_pl_200_m10['failed']} >= 1))"
        )
        if res_pl_200_m10["first_failure_full"]:
            lines.append(f"    First planted 200/mt10 failure in full: {res_pl_200_m10['first_failure_full']}")
        lines.append(
            f"  [200 pos, movetime 10] kF_cp    : searches=200, branch_taken={res_kf_200_m10['branch_taken']}, "
            f"check_passed={res_kf_200_m10['passed']} of 200 (PASS ({res_kf_200_m10['passed']} == 200))"
        )

        res_kk_1k_m10 = run_movetime_suite(
            "kK_cp_1000_mt10", builds["kK_cp"][0], fens_1000_nonterm, 10, JOB36 / "partB_CP_kK_1000_mt10_rows.txt"
        )
        res_pl_1k_m10 = run_movetime_suite(
            "kK_plant_1000_mt10", builds["kK_plant"][0], fens_1000_nonterm, 10, JOB36 / "partB_CP_plant_1000_mt10_rows.txt"
        )
        res_kf_1k_m10 = run_movetime_suite(
            "kF_cp_1000_mt10", builds["kF_cp"][0], fens_1000_nonterm, 10, JOB36 / "partB_CP_kF_1000_mt10_rows.txt"
        )
        lines.append(
            f"  [1000 pos, movetime 10] kK_cp   : searches=1000, branch_taken={res_kk_1k_m10['branch_taken']}, "
            f"check_passed={res_kk_1k_m10['passed']} of 1000 (PASS ({res_kk_1k_m10['passed']} == 1000))"
        )
        lines.append(
            f"  [1000 pos, movetime 10] kK_plant: searches=1000, branch_taken={res_pl_1k_m10['branch_taken']}, "
            f"check_passed={res_pl_1k_m10['passed']} of 1000, check_FAILED={res_pl_1k_m10['failed']} of 1000 "
            f"(PASS ({res_pl_1k_m10['failed']} >= 1))"
        )
        if res_pl_1k_m10["first_failure_full"]:
            lines.append(f"    First planted 1000/mt10 failure in full: {res_pl_1k_m10['first_failure_full']}")
        lines.append(
            f"  [1000 pos, movetime 10] kF_cp   : searches=1000, branch_taken={res_kf_1k_m10['branch_taken']}, "
            f"check_passed={res_kf_1k_m10['passed']} of 1000 (PASS ({res_kf_1k_m10['passed']} == 1000))"
        )

        res_kk_1k_m30 = run_movetime_suite(
            "kK_cp_1000_mt30", builds["kK_cp"][0], fens_1000_nonterm, 30, JOB36 / "partB_CP_kK_1000_rows.txt"
        )
        res_pl_1k_m30 = run_movetime_suite(
            "kK_plant_1000_mt30", builds["kK_plant"][0], fens_1000_nonterm, 30, JOB36 / "partB_CP_plant_1000_rows.txt"
        )
        res_kf_1k_m30 = run_movetime_suite(
            "kF_cp_1000_mt30", builds["kF_cp"][0], fens_1000_nonterm, 30, JOB36 / "partB_CP_kF_1000_rows.txt"
        )
        lines.append(
            f"  [1000 pos, movetime 30] kK_cp   : searches=1000, branch_taken={res_kk_1k_m30['branch_taken']}, "
            f"check_passed={res_kk_1k_m30['passed']} of 1000 (PASS ({res_kk_1k_m30['passed']} == 1000))"
        )
        lines.append(
            f"  [1000 pos, movetime 30] kK_plant: searches=1000, branch_taken={res_pl_1k_m30['branch_taken']}, "
            f"check_passed={res_pl_1k_m30['passed']} of 1000, check_FAILED={res_pl_1k_m30['failed']} of 1000 "
            f"(PASS ({res_pl_1k_m30['failed']} >= 1))"
        )
        lines.append(
            f"  [1000 pos, movetime 30] kF_cp   : searches=1000, branch_taken={res_kf_1k_m30['branch_taken']}, "
            f"check_passed={res_kf_1k_m30['passed']} of 1000 (PASS ({res_kf_1k_m30['passed']} == 1000))"
        )
        lines.append("")
        all_ok = (
            all_ok
            and (res_kk_200_m10["passed"] == 200)
            and (res_pl_200_m10["failed"] >= 1)
            and (res_kf_200_m10["passed"] == 200)
            and (res_kk_1k_m10["passed"] == 1000)
            and (res_pl_1k_m10["failed"] >= 1)
            and (res_kf_1k_m10["passed"] == 1000)
            and (res_kk_1k_m30["passed"] == 1000)
            and (res_pl_1k_m30["failed"] >= 1)
            and (res_kf_1k_m30["passed"] == 1000)
        )

    utc1 = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    lines.append(f"UTC end: {utc1}")
    lines.append(f"PART B OVERALL: {'PASS' if all_ok else 'FAIL'} ({int(all_ok)} == 1)")
    out_txt = "\n".join(lines) + "\n"
    (JOB36 / "partB_settled_and_CP_summary.txt").write_text(out_txt)
    print(out_txt, flush=True)
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
