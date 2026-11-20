#!/usr/bin/env python3
"""
Job 37 Part A Runner (`run_partA_checking.py`):
Builds clean `r15d + v3` and planted controls `CP-A` and `CP-U` with the checking flags
(`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`,
no profile step), verifies `bench 11 = 312866` and `go perft 5 = 4865609`, runs A1, A2,
A3, A4, CP-A, and CP-U, and records every PASS/FAIL comparison side by side.
"""
from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

sys.dont_write_bytecode = True
import chess

JOB37 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job37")
JOB36 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job36")
JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
WORK37 = pathlib.Path("/tmp/carbon2_job37")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")
PLAIN_V3_EXE = "/tmp/carbon2_job36/bld_sp_sgr15v/forge"
NET768 = "/tmp/carbon2_work/net768.fnn3"

sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))
sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/carbon2/job2")

from loop_driver import parse_sgerror_v2
from loop_v3_driver import V3AttemptDetail, V3SuiteRun, parse_sgend_v3, write_v2_v3_rows
from ref_driver import RunSettings, format_game_records
from selfplay_driver_v2 import PC20_OPTIONS
from verify_seven import fmt_cmp, sha256_file

TUS = ["bitboard", "board", "book", "eval", "eval_params", "nnue", "nnue_v3", "search", "uci"]
PC_LINE_L = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"
B4_LINE = "selfgame softnodes 2000 evallimit 2000 maxply 8 writeminply 8 drawply 80 drawscore 5 drawcount 8"


def checking_compile_flags(src_dir: str) -> list[str]:
    return [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-std=c++20",
        "-O1",
        "-g",
        "-fsanitize=address,undefined",
        "-fno-sanitize-recover=all",
        "-D_GLIBCXX_ASSERTIONS",
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
        "-pthread",
        f"-I{src_dir}/include",
    ]


def checking_link_flags() -> list[str]:
    return [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-O1",
        "-g",
        "-fsanitize=address,undefined",
        "-fno-sanitize-recover=all",
        "-march=sapphirerapids",
        "-fuse-ld=lld-18",
        "-pthread",
    ]


def build_checking(src_dir: pathlib.Path, bld_dir: pathlib.Path) -> tuple[str, str, str]:
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    (bld_dir / "obj").mkdir(parents=True)
    cflags = checking_compile_flags(str(src_dir))
    procs = []
    for tu in TUS:
        cmd = cflags + ["-c", str(src_dir / "src" / f"{tu}.cpp"), "-o", str(bld_dir / "obj" / f"{tu}.o")]
        procs.append(subprocess.Popen(cmd))
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError(f"Checking compile failed in {bld_dir}")
    exe = str(bld_dir / "forge")
    lflags = checking_link_flags() + [str(bld_dir / "obj" / f"{tu}.o") for tu in TUS] + ["-o", exe]
    subprocess.run(lflags, check=True)
    return exe, " ".join(cflags), " ".join(lflags)


def make_cpa_tree(dst: pathlib.Path) -> pathlib.Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TPL_V3, dst)
    uci_p = dst / "src" / "uci.cpp"
    txt = uci_p.read_text()

    old = """[[nodiscard]] bool parse_selfgame_config(std::string_view line, SgConfig& out_cfg,
                                         std::string_view& bad_word) noexcept {
    SgConfig cfg;
    unsigned seen_mask = 0U;
    (void)sg_next_token(line);"""

    new = """[[nodiscard]] bool parse_selfgame_config(std::string_view line, SgConfig& out_cfg,
                                         std::string_view& bad_word) noexcept {
    const std::string_view orig_line = line;
    SgConfig cfg;
    unsigned seen_mask = 0U;
    (void)sg_next_token(line);"""
    assert old in txt, "CP-A anchor 1 not found"
    txt = txt.replace(old, new, 1)

    old2 = """        const std::string_view val = sg_next_token(line);
        if (val.empty()) {
            bad_word = key;
            return false;
        }"""

    new2 = """        const std::string_view val = sg_next_token(line);
        if (val.empty()) {
            char* exact_copy = new char[orig_line.size()];
            for (std::size_t i = 0; i < orig_line.size(); ++i) exact_copy[i] = orig_line[i];
            volatile char oob_read = exact_copy[orig_line.size()];
            (void)oob_read;
            delete[] exact_copy;
            bad_word = key;
            return false;
        }"""
    assert old2 in txt, "CP-A anchor 2 not found"
    txt = txt.replace(old2, new2, 1)
    uci_p.write_text(txt)

    diff_res = subprocess.run(
        ["diff", "-u", "a/src/uci.cpp", "b/src/uci.cpp"],
        cwd=str(WORK37),
        capture_output=True,
        text=True,
    )
    # Generate clean unified diff against TPL_V3
    d = subprocess.run(
        ["diff", "-u", "--label", "a/src/uci.cpp", "--label", "b/src/uci.cpp", str(TPL_V3 / "src/uci.cpp"), str(uci_p)],
        capture_output=True,
        text=True,
    )
    assert d.returncode == 1
    patch_p = JOB37 / "control_CPA_s3_heap_oob.patch.txt"
    patch_p.write_text(d.stdout)
    return patch_p


def make_cpu_tree(dst: pathlib.Path) -> pathlib.Path:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(TPL_V3, dst)
    uci_p = dst / "src" / "uci.cpp"
    txt = uci_p.read_text()

    old = """    out += " nodes ";
    out += std::to_string(total_nodes);
    out += " fen ";
    out += board.sg_fen();"""

    new = """    out += " nodes ";
    out += std::to_string(total_nodes);
    {
        volatile int ply_v = ply;
        volatile int ovf_sum = std::numeric_limits<int>::max() + ply_v;
        (void)ovf_sum;
    }
    out += " fen ";
    out += board.sg_fen();"""
    assert old in txt, "CP-U anchor not found"
    txt = txt.replace(old, new, 1)
    uci_p.write_text(txt)

    d = subprocess.run(
        ["diff", "-u", "--label", "a/src/uci.cpp", "--label", "b/src/uci.cpp", str(TPL_V3 / "src/uci.cpp"), str(uci_p)],
        capture_output=True,
        text=True,
    )
    assert d.returncode == 1
    patch_p = JOB37 / "control_CPU_sgend_signed_ovf.patch.txt"
    patch_p.write_text(d.stdout)
    return patch_p


def check_bench11_perft5(exe: str) -> tuple[int, int, int]:
    env = dict(os.environ)
    env["UBSAN_OPTIONS"] = "print_stacktrace=1:report_error_type=1"
    r1 = subprocess.run(
        [exe],
        input="uci\nisready\nbench 11\nisready\nquit\n",
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    b11 = -1
    prefix = "info string bench depth 11 nodes "
    for ln in r1.stdout.splitlines():
        if ln.startswith(prefix):
            b11 = int(ln[len(prefix) :].split()[0])
    r2 = subprocess.run(
        [exe],
        input="uci\nisready\nposition startpos\ngo perft 5\nisready\nquit\n",
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    p5 = -1
    for ln in reversed(r2.stdout.splitlines()):
        if ln.startswith("nodes "):
            p5 = int(ln.split()[1])
            break
    stderr_bytes = len(r1.stderr.encode("utf-8")) + len(r2.stderr.encode("utf-8"))
    return b11, p5, stderr_bytes


class CheckingEngine:
    def __init__(self, exe_path: str, net_path: Optional[str], stderr_fp, cpu_pin: Optional[int] = None) -> None:
        self.exe_path = exe_path
        self.net_path = net_path
        self.stderr_fp = stderr_fp
        self.cpu_pin = cpu_pin
        self.proc: Optional[subprocess.Popen[str]] = None
        self._start()

    def _start(self) -> None:
        cmd = [self.exe_path] if self.cpu_pin is None else ["taskset", "-c", str(self.cpu_pin), self.exe_path]
        env = dict(os.environ)
        env["UBSAN_OPTIONS"] = "print_stacktrace=1:report_error_type=1"
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.stderr_fp,
            text=True,
            bufsize=1,
            env=env,
        )
        self.send("uci\n")
        self.wait_for("uciok")
        opts = list(PC20_OPTIONS)
        if self.net_path is not None:
            opts.append(("NNUEArchFile", self.net_path))
            opts.append(("NNUEArch", "true"))
        self.send("".join(f"setoption name {k} value {v}\n" for k, v in opts) + "isready\n")
        self.wait_for("readyok")

    def send(self, data: str) -> None:
        assert self.proc is not None and self.proc.stdin is not None
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def readline(self) -> str:
        assert self.proc is not None and self.proc.stdout is not None
        ln = self.proc.stdout.readline()
        if ln == "":
            rc = self.proc.wait()
            raise RuntimeError(f"Engine EOF (returncode={rc})")
        return ln.rstrip("\r\n")

    def wait_for(self, tok: str) -> None:
        while True:
            if self.readline() == tok:
                return

    def close(self) -> int:
        if self.proc is None:
            return 0
        if self.proc.poll() is None:
            try:
                self.send("quit\n")
            except BrokenPipeError:
                pass
        rc = self.proc.wait()
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()
        self.proc = None
        return rc

    def restart(self) -> int:
        rc = self.close()
        self._start()
        return rc


def run_v3_with_stderr(
    exe_path: str,
    seed: str,
    attempts: int,
    settings: RunSettings,
    cpu_pin: Optional[int] = None,
    custom_sg_cmd: Optional[str] = None,
) -> tuple[V3SuiteRun, bytes, int]:
    rng = random.Random(seed)
    sg_cmd = (
        custom_sg_cmd.rstrip("\n") + "\n"
        if custom_sg_cmd is not None
        else (
            f"selfgame softnodes {settings.N} evallimit {settings.E} maxply {settings.M} "
            f"writeminply {settings.W} drawply {settings.P} drawscore {settings.S} drawcount {settings.C}\n"
        )
    )

    full_hasher = hashlib.sha256()
    first10_hasher = hashlib.sha256()
    finished = 0
    thrown_away = 0
    total_records = 0
    total_sg_lines = 0
    moves_finished = 0
    moves_all = 0
    total_searches = 0
    total_nodes = 0
    w_wins = 0
    draws = 0
    b_wins = 0
    details: list[V3AttemptDetail] = []
    nonzero_rc = 0

    with tempfile.TemporaryFile() as err_fp:
        eng = CheckingEngine(exe_path, settings.net_path, err_fp, cpu_pin=cpu_pin)
        try:
            for attempt_idx in range(1, attempts + 1):
                board = chess.Board()
                opening_moves: list[str] = []
                rng.sample(range(0, 8), 8)
                eng.send("ucinewgame\nisready\n")
                eng.wait_for("readyok")

                ended_in_opening = False
                result = 0
                end_reason = ""
                while len(opening_moves) < 8:
                    ply = len(opening_moves)
                    if not any(board.legal_moves):
                        result = 0 if not board.is_check() else (-1 if board.turn == chess.WHITE else 1)
                        end_reason = "stalemate" if not board.is_check() else "mate"
                        ended_in_opening = True
                        break
                    is_rule_draw = (
                        board.is_insufficient_material()
                        or board.halfmove_clock >= 100
                        or board.is_repetition(3)
                    )
                    if is_rule_draw or ply >= settings.M:
                        result = 0
                        end_reason = "rule" if is_rule_draw else "plylimit"
                        ended_in_opening = True
                        break
                    mv = rng.choice(list(board.legal_moves))
                    board.push(mv)
                    opening_moves.append(mv.uci())

                if ended_in_opening:
                    finished += 1
                    moves_finished += len(opening_moves)
                    moves_all += len(opening_moves)
                    if result == 1:
                        w_wins += 1
                    elif result == 0:
                        draws += 1
                    else:
                        b_wins += 1
                    details.append(
                        V3AttemptDetail(
                            attempt=attempt_idx,
                            finished=True,
                            opening_moves=opening_moves,
                            loop_moves=[],
                            sg_lines=[],
                            sgend_line=None,
                            sgerror_line=None,
                            final_fen=board.fen(),
                            records=0,
                            result=result,
                            plies=len(opening_moves),
                            searches=0,
                            nodes=0,
                            end_reason=end_reason,
                            text_sha256=hashlib.sha256(b"").hexdigest(),
                        )
                    )
                    continue

                pos_cmd = (
                    "position startpos moves " + " ".join(opening_moves)
                    if opening_moves
                    else "position startpos"
                )
                eng.send(f"{pos_cmd}\n{sg_cmd}")

                records: list[tuple[str, str, int, int, bool]] = []
                sg_lines: list[str] = []
                sgend_line: Optional[str] = None
                sgerror_line: Optional[str] = None
                final_fen: Optional[str] = None
                loop_moves: list[str] = []
                thrown = False
                att_plies = len(opening_moves)
                att_searches = 0
                att_nodes = 0

                while True:
                    line = eng.readline()
                    if line.startswith("sg "):
                        sg_lines.append(line)
                        _, ply_s, x_s, mv_s, fen_s = line.split(" ", 4)
                        was_white = fen_s.split(" ", 2)[1] == "w"
                        records.append((fen_s, mv_s, int(x_s), int(ply_s), was_white))
                    elif line.startswith("sgend "):
                        sgend_line = line
                        (
                            result,
                            end_reason,
                            att_plies,
                            _run,
                            att_searches,
                            att_nodes,
                            final_fen,
                            loop_moves,
                            _stripped,
                        ) = parse_sgend_v3(line)
                        break
                    elif line.startswith("sgerror "):
                        sgerror_line = line
                        reason_tok, err_ply, att_searches, att_nodes, _err_fen = parse_sgerror_v2(line)
                        thrown = True
                        att_plies = err_ply
                        end_reason = f"thrown@{err_ply}" if reason_tok == "maxsims" else f"err_{reason_tok}@{err_ply}"
                        break

                total_sg_lines += len(sg_lines)
                total_searches += att_searches
                total_nodes += att_nodes
                moves_all += att_plies

                if thrown:
                    thrown_away += 1
                    rc_r = eng.restart()
                    if rc_r != 0:
                        nonzero_rc = rc_r
                    details.append(
                        V3AttemptDetail(
                            attempt=attempt_idx,
                            finished=False,
                            opening_moves=opening_moves,
                            loop_moves=[],
                            sg_lines=sg_lines,
                            sgend_line=None,
                            sgerror_line=sgerror_line,
                            final_fen=None,
                            records=0,
                            result=None,
                            plies=att_plies,
                            searches=att_searches,
                            nodes=att_nodes,
                            end_reason=end_reason,
                            text_sha256=hashlib.sha256(b"").hexdigest(),
                        )
                    )
                else:
                    finished += 1
                    moves_finished += att_plies
                    total_records += len(records)
                    if result == 1:
                        w_wins += 1
                    elif result == 0:
                        draws += 1
                    else:
                        b_wins += 1
                    game_txt = format_game_records(records, result)
                    game_bytes = game_txt.encode("ascii")
                    full_hasher.update(game_bytes)
                    if attempt_idx <= 10:
                        first10_hasher.update(game_bytes)
                    details.append(
                        V3AttemptDetail(
                            attempt=attempt_idx,
                            finished=True,
                            opening_moves=opening_moves,
                            loop_moves=loop_moves,
                            sg_lines=sg_lines,
                            sgend_line=sgend_line,
                            sgerror_line=None,
                            final_fen=final_fen,
                            records=len(records),
                            result=result,
                            plies=att_plies,
                            searches=att_searches,
                            nodes=att_nodes,
                            end_reason=end_reason,
                            text_sha256=hashlib.sha256(game_bytes).hexdigest(),
                        )
                    )
        finally:
            rc_end = eng.close()
            if rc_end != 0:
                nonzero_rc = rc_end
            err_fp.seek(0)
            stderr_raw = err_fp.read()

    return (
        V3SuiteRun(
            version=3,
            full_sha256=full_hasher.hexdigest(),
            first10_sha256=first10_hasher.hexdigest(),
            attempts=attempts,
            finished=finished,
            thrown_away=thrown_away,
            total_records=total_records,
            total_sg_lines=total_sg_lines,
            moves_finished=moves_finished,
            moves_all=moves_all,
            total_searches=total_searches,
            total_nodes=total_nodes,
            w_wins=w_wins,
            draws=draws,
            b_wins=b_wins,
            details=details,
        ),
        stderr_raw,
        nonzero_rc,
    )


def main() -> None:
    WORK37.mkdir(parents=True, exist_ok=True)
    src_clean = WORK37 / "src_chk_clean"
    if src_clean.exists():
        shutil.rmtree(src_clean)
    shutil.copytree(TPL_V3, src_clean)

    src_cpa = WORK37 / "src_chk_cpa"
    src_cpu = WORK37 / "src_chk_cpu"
    cpa_patch = make_cpa_tree(src_cpa)
    cpu_patch = make_cpu_tree(src_cpu)

    chk_clean_exe, cflags_clean, lflags_clean = build_checking(src_clean, WORK37 / "bld_chk_clean")
    chk_cpa_exe, cflags_cpa, lflags_cpa = build_checking(src_cpa, WORK37 / "bld_chk_cpa")
    chk_cpu_exe, cflags_cpu, lflags_cpu = build_checking(src_cpu, WORK37 / "bld_chk_cpu")

    # Save Part A build metadata so Part B can include it in builds.txt
    meta_lines = [
        "=== PART A CHECKING BUILDS ===",
        f"Recipe: -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS (no profile step)",
        f"Exact compile flags (template): {cflags_clean}",
        f"Exact link flags:               {lflags_clean}",
        f"1. v3_chk_clean : {chk_clean_exe} | sha256={sha256_file(chk_clean_exe)}",
        f"2. v3_chk_CPA   : {chk_cpa_exe}   | sha256={sha256_file(chk_cpa_exe)} | patch={cpa_patch.name} ({sha256_file(str(cpa_patch))})",
        f"3. v3_chk_CPU   : {chk_cpu_exe}   | sha256={sha256_file(chk_cpu_exe)} | patch={cpu_patch.name} ({sha256_file(str(cpu_patch))})",
    ]
    (WORK37 / "partA_builds_meta.txt").write_text("\n".join(meta_lines) + "\n")

    all_ok = True
    out: list[str] = [
        "=== JOB 37 PART A: v3 Under the Checking Builds (ASan + UBSan + _GLIBCXX_ASSERTIONS) ===",
        *meta_lines[1:],
        "",
        "--- 0. Initial Two Numbers per Checking Build (bench 11 = 312866, go perft 5 = 4865609) ---",
    ]
    for bname, bexe in [
        ("v3_chk_clean", chk_clean_exe),
        ("v3_chk_CPA", chk_cpa_exe),
        ("v3_chk_CPU", chk_cpu_exe),
    ]:
        b11, p5, ebytes = check_bench11_perft5(bexe)
        ok1, s1 = fmt_cmp(f"{bname} bench 11", b11, 312866)
        ok2, s2 = fmt_cmp(f"{bname} go perft 5", p5, 4865609)
        ok3, s3 = fmt_cmp(f"{bname} bench+perft stderr_bytes", ebytes, 0)
        all_ok = all_ok and ok1 and ok2 and ok3
        out.extend([s1, s2, s3])
        if bname == "v3_chk_clean" and not (ok1 and ok2):
            raise SystemExit("STOP: Clean checking build missed bench 11 or perft 5")
    out.append("")

    # --- A1: Through selfgame driver with line L (plus suite-specific B[1..20] & C for completeness) ---
    out.append("--- A1. Selfgame Driver Runs: Plain v3 vs Clean Checking v3 (sha256 Side by Side & stderr_bytes) ---")
    a1_specs = [
        ("Set_A_L", "carbon2-job33-a", 200, RunSettings(), PC_LINE_L),
        ("Set_C_L", "carbon2-job33-c", 100, RunSettings(), PC_LINE_L),
        ("Set_B20_L", "carbon2-job33-b", 20, RunSettings(), PC_LINE_L),
        ("Set_n20_L", "carbon2-job33-n", 20, RunSettings(net_path=NET768), PC_LINE_L),
        ("Set_C_suite", "carbon2-job33-c", 100, RunSettings(N=300, E=400, M=120, P=20, S=30, C=3), None),
        ("Set_B20_suite", "carbon2-job33-b", 20, RunSettings(N=50), None),
    ]

    # Run plain and checking in parallel across 4 cores
    tasks = []
    for idx, (tag, seed, n_att, stg, ccmd) in enumerate(a1_specs):
        tasks.append((tag, "plain", PLAIN_V3_EXE, seed, n_att, stg, ccmd, idx % 4))
        tasks.append((tag, "chk", chk_clean_exe, seed, n_att, stg, ccmd, (idx + 2) % 4))

    a1_res: dict[tuple[str, str], tuple[V3SuiteRun, bytes, int]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {
            pool.submit(run_v3_with_stderr, exe, seed, n_att, stg, cpu, ccmd): (tag, kind)
            for tag, kind, exe, seed, n_att, stg, ccmd, cpu in tasks
        }
        for fut in concurrent.futures.as_completed(futs):
            a1_res[futs[fut]] = fut.result()

    for tag, _seed, _n_att, _stg, _ccmd in a1_specs:
        rp, err_p, rc_p = a1_res[(tag, "plain")]
        rc, err_c, rc_c = a1_res[(tag, "chk")]
        write_v2_v3_rows(JOB37 / f"partA_chk_{tag}_rows.txt", f"partA checking {tag}", rc)
        out.append(
            f"  [{tag}] attempts={rc.attempts} finished={rc.finished} thrown={rc.thrown_away} "
            f"records={rc.total_records} searches={rc.total_searches} nodes={rc.total_nodes}"
        )
        for lbl, got, exp in [
            (f"{tag} record_text sha256 (chk vs plain)", rc.full_sha256, rp.full_sha256),
            (f"{tag} records (chk vs plain)", rc.total_records, rp.total_records),
            (f"{tag} nodes (chk vs plain)", rc.total_nodes, rp.total_nodes),
            (f"{tag} chk stderr_bytes", len(err_c), 0),
            (f"{tag} plain stderr_bytes", len(err_p), 0),
            (f"{tag} chk exit_code", rc_c, 0),
        ]:
            ok, s = fmt_cmp(lbl, got, exp)
            all_ok = all_ok and ok
            out.append("  " + s)
    out.append("")

    # --- A2: Six S lines (S1..S6) ---
    out.append("--- A2. Six Strict-Line Inputs S1..S6 on Clean Checking Build (Fresh Process Each) ---")
    cs_specs = [
        ("S1", "selfgame softnodes 2000 evallimt 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8", "sgerror badline evallimt"),
        ("S2", "selfgame softnodes 2k evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8", "sgerror badline 2k"),
        ("S3", "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount", "sgerror badline drawcount"),
        ("S4", "selfgame softnodes 2000 maxply 300 maxply 60", "sgerror badline maxply"),
        ("S5", "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore -5 drawcount 8", "sgerror badline -5"),
        ("S6", "selfgame softnodes 2000 evallimit 2000 maxply 300x writeminply 8 drawply 80 drawscore 5 drawcount 8", "sgerror badline 300x"),
    ]
    a2_eq = 0
    for sid, bad_cmd, exp_err in cs_specs:
        stdin = f"uci\nisready\nposition startpos\n{bad_cmd}\nisready\nquit\n"
        r_pl = subprocess.run([PLAIN_V3_EXE], input=stdin, text=True, capture_output=True, check=True)
        r_ck = subprocess.run([chk_clean_exe], input=stdin, text=True, capture_output=True, check=True)
        pl_after = r_pl.stdout.splitlines()[r_pl.stdout.splitlines().index("readyok") + 1 :]
        ck_after = r_ck.stdout.splitlines()[r_ck.stdout.splitlines().index("readyok") + 1 :]
        eb = len(r_ck.stderr.encode("utf-8"))
        ok_s = ck_after == pl_after == [exp_err, "readyok"] and eb == 0
        if ok_s:
            a2_eq += 1
        else:
            all_ok = False
        out.append(
            f"  {sid}: {'PASS' if ok_s else 'FAIL'} ({ck_after[0]!r} == {pl_after[0]!r}, readyok={ck_after[1]!r} == 'readyok', stderr_bytes: {eb} == 0)"
        )
    ok_a2, s_a2 = fmt_cmp("A2 S1..S6 exact + readyok + 0 stderr", a2_eq, 6)
    all_ok = all_ok and ok_a2
    out.append(s_a2)
    out.append("")

    # --- A3: Nine KB9 lines (B1..B9) ---
    out.append("--- A3. Nine KB9 Lines B1..B9 on Clean Checking Build vs Plain Build ---")
    kb9_inputs = [
        ("B1", "position startpos moves f2f3 e7e5 g2g4 d8h4", PC_LINE_L),
        ("B2", "position startpos moves e2e3 a7a5 d1h5 a8a6 h5a5 h7h5 h2h4 a6h6 a5c7 f7f6 c7d7 e8f7 d7b7 d8d3 b7b8 d3h7 b8c8 f7g6 c8e6", PC_LINE_L),
        ("B3", "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8", PC_LINE_L),
        ("B4", "position startpos moves e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 d2d3 f8c5", B4_LINE),
        ("B5", "position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1", PC_LINE_L),
        ("B6", "position fen 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80", PC_LINE_L),
        ("B7", "position fen R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80", PC_LINE_L),
        ("B8", "position fen k7/2K5/8/2B5/8/8/8/8 b - - 0 1", PC_LINE_L),
        ("B9", "position fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", PC_LINE_L),
    ]

    def run_kb9_one(exe: str, pos_cmd: str, sg_cmd: str) -> tuple[str, int]:
        opt_str = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
        stdin = f"uci\n{opt_str}ucinewgame\nisready\n{pos_cmd}\n{sg_cmd}\nquit\n"
        r = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
        lns = r.stdout.splitlines()
        idx = lns.index("readyok")
        after = lns[idx + 1 :]
        return (" | ".join(after), len(r.stderr.encode("utf-8")))

    a3_eq = 0
    for bid, pcmd, scmd in kb9_inputs:
        pl_ln, _ = run_kb9_one(PLAIN_V3_EXE, pcmd, scmd)
        ck_ln, ck_eb = run_kb9_one(chk_clean_exe, pcmd, scmd)
        eq = (ck_ln == pl_ln) and (ck_eb == 0)
        if eq:
            a3_eq += 1
        else:
            all_ok = False
        out.append(f"  {bid}: {'EQUAL' if eq else 'DIFF'} (stderr_bytes: {ck_eb} == 0) | {ck_ln}")
        if not eq:
            out.append(f"       plain: {pl_ln}")
    ok_a3, s_a3 = fmt_cmp("A3 B1..B9 equal + 0 stderr count", a3_eq, 9)
    all_ok = all_ok and ok_a3
    out.append(s_a3)
    out.append("")

    # --- A4: Thread inspection ---
    out.append("--- A4. Thread Where `run_selfgame` Runs ---")
    out.append(
        "  Call site: `src/uci.cpp:1228` (`run_selfgame(board, searcher, move_overhead_ms, multipv, sg_cfg);`),"
    )
    out.append(
        "  inside `forge::uci_loop(std::istream& in)` (`src/uci.cpp:618`), directly after `stop_search()` (`src/uci.cpp:1209`)."
    )
    out.append(
        "  Thread: THE SAME main thread that reads UCI commands from `in` (not a separate worker thread; `-fsanitize=thread` conditional branch not triggered)."
    )
    out.append("")

    # --- CONTROLS: CP-A and CP-U ---
    out.append("--- CONTROLS: CP-A (AddressSanitizer on S3) and CP-U (UndefinedBehaviorSanitizer on Set A Attempt 1) ---")

    # CP-A on S3
    s3_cmd = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount"
    cpa_stdin = f"uci\nisready\nposition startpos\n{s3_cmd}\nisready\nquit\n"
    r_cpa = subprocess.run([chk_cpa_exe], input=cpa_stdin, text=True, capture_output=True)
    cpa_err_lines = [ln for ln in r_cpa.stderr.splitlines() if ln.strip()]
    cpa_first_err = next((ln for ln in cpa_err_lines if "AddressSanitizer" in ln or "ERROR:" in ln), cpa_err_lines[0] if cpa_err_lines else "")
    cpa_summary = next((ln for ln in cpa_err_lines if ln.startswith("SUMMARY:")), "")
    cpa_hit = (r_cpa.returncode != 0) and ("heap-buffer-overflow" in r_cpa.stderr)
    ok_cpa_rc, s_cpa_rc = fmt_cmp("CP-A exited non-zero (returncode != 0)", int(r_cpa.returncode != 0), 1)
    ok_cpa_kind, s_cpa_kind = fmt_cmp("CP-A reported heap-buffer-overflow", int("heap-buffer-overflow" in r_cpa.stderr), 1)
    all_ok = all_ok and ok_cpa_rc and ok_cpa_kind
    out.extend([
        f"  [CP-A] patch={cpa_patch.name} | returncode={r_cpa.returncode} | stderr_bytes={len(r_cpa.stderr.encode('utf-8'))}",
        "  Note: parse_selfgame_config views std::getline's std::string (which has spare capacity + trailing NUL), so per spec",
        "  CP-A copies the line into an exact-length `new char[orig_line.size()]` buffer and reads `exact_copy[orig_line.size()]` on S3.",
        "  " + s_cpa_rc,
        "  " + s_cpa_kind,
        f"  CP-A sanitizer first report line: {cpa_first_err}",
        f"  CP-A sanitizer SUMMARY line:      {cpa_summary}",
        "",
    ])
    (JOB37 / "partA_CPA_stderr_raw.txt").write_text(r_cpa.stderr)

    # CP-U on Set A's first attempt
    cpu_failed_as_expected = False
    cpu_err_txt = ""
    cpu_rc = 0
    try:
        _r_u, err_u, rc_u = run_v3_with_stderr(chk_cpu_exe, "carbon2-job33-a", 1, RunSettings(), cpu_pin=3, custom_sg_cmd=PC_LINE_L)
        cpu_err_txt = err_u.decode("utf-8", errors="replace")
        cpu_rc = rc_u
    except Exception:
        # Engine aborts on attempt 1 before writing sgend due to -fno-sanitize-recover=all!
        pass

    # Run attempt 1 directly in a clean subprocess with Set A attempt 1's exact opening moves so we capture exact returncode & stderr cleanly
    rng_a1 = random.Random("carbon2-job33-a")
    b_a1 = chess.Board()
    op_a1: list[str] = []
    rng_a1.sample(range(0, 8), 8)
    while len(op_a1) < 8:
        mv = rng_a1.choice(list(b_a1.legal_moves))
        b_a1.push(mv)
        op_a1.append(mv.uci())
    opt_str = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    cpu_stdin = f"uci\n{opt_str}ucinewgame\nisready\nposition startpos moves {' '.join(op_a1)}\n{PC_LINE_L}\nquit\n"
    env_u = dict(os.environ)
    env_u["UBSAN_OPTIONS"] = "print_stacktrace=1:report_error_type=1"
    r_cpu = subprocess.run(["taskset", "-c", "3", chk_cpu_exe], input=cpu_stdin, text=True, capture_output=True, env=env_u)
    cpu_err_lines = [ln for ln in r_cpu.stderr.splitlines() if ln.strip()]
    cpu_first_err = next((ln for ln in cpu_err_lines if "runtime error:" in ln), cpu_err_lines[0] if cpu_err_lines else "")
    cpu_summary = next((ln for ln in cpu_err_lines if ln.startswith("SUMMARY:")), "")
    has_sig_ovf = ("signed integer overflow" in r_cpu.stderr) or ("signed-integer-overflow" in r_cpu.stderr)
    ok_cpu_rc, s_cpu_rc = fmt_cmp("CP-U exited non-zero (returncode != 0)", int(r_cpu.returncode != 0), 1)
    ok_cpu_kind, s_cpu_kind = fmt_cmp("CP-U reported signed-integer-overflow", int(has_sig_ovf), 1)
    all_ok = all_ok and ok_cpu_rc and ok_cpu_kind
    out.extend([
        f"  [CP-U] patch={cpu_patch.name} | Set A attempt 1 opening={' '.join(op_a1)} | returncode={r_cpu.returncode} | stderr_bytes={len(r_cpu.stderr.encode('utf-8'))}",
        "  " + s_cpu_rc,
        "  " + s_cpu_kind,
        f"  CP-U sanitizer first report line: {cpu_first_err}",
        f"  CP-U sanitizer SUMMARY line:      {cpu_summary}",
        "",
    ])
    (JOB37 / "partA_CPU_stderr_raw.txt").write_text(r_cpu.stderr)

    utc_end = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    out.append(f"PART A OVERALL: {'PASS' if all_ok else 'FAIL'} ({int(all_ok)} == 1)")
    out.append(f"UTC finished: {utc_end}")
    out_txt = "\n".join(out) + "\n"
    (JOB37 / "partA_checking_summary.txt").write_text(out_txt)
    print(out_txt, flush=True)
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
