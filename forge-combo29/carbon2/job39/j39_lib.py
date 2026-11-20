#!/usr/bin/env python3
"""
Job 39 Shared Harness Library (`j39_lib.py`):
- Build recipes for `r15d + v3`:
  1. Job 36 Release recipe (`clang++-18 -O3 -DNDEBUG ... -flto=thin`, no profile needed for rows)
  2. Job 37 Part A Checking recipe (`clang++-18 -O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`)
- Exact OFF-number verification (`312866 / 862329 / 4865609`, `PC20 278024 / 587276`,
  `Set A line L` `26,741 / 107,124,743 / d5b52710...`, `n[1..60] line L` `8,449 / 36,688,357 / b6bf7600...`)
- `O` (`first200.fens`, 200 positions, depth 12) and `G` (`set_G.epd`, 353 positions, depth 12)
  runners under `PC20` + built-in evaluation + `Threads 1` + `Hash 16` + `ucinewgame` + `isready`
  before every search, writing `(position, nodes, best move, score)` rows and `.meta` files
  (`exe path, sha256, id name, every option line sent`).
- Selfgame runner keeping the single canonical Job 36 label (`thrown@N` on `noscore`, `maxsims@N` on `maxsims`).
"""
from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Optional

sys.dont_write_bytecode = True

JOB39 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job39")
JOB36 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job36")
JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
WORK39 = pathlib.Path("/tmp/carbon2_job39")
TPL_V3 = pathlib.Path("/tmp/carbon2_job36/tpl_r15d_v3")
REUSED_R15D_V3_EXE = "/tmp/carbon2_job36/bld_sp_sgr15v/forge"
REUSED_R15D_V3_PROF = "/tmp/carbon2_job36/bld_sp_sgr15v/forge.profdata"
REC_R15D_V3_SHA = "bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810"
REC_R15D_V3_PROF_SHA = "e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc"
NET768 = "/tmp/carbon2_work/net768.fnn3"

O_FENS_PATH = WORK39 / "sets/first200.fens"
G_EPD_PATH = WORK39 / "sets/set_G.epd"

sys.path.insert(0, str(JOB36))
sys.path.insert(0, str(JOB35))

from loop_v3_driver import V3SuiteRun, run_loop_detailed, write_v2_v3_rows
from ref_driver import PC20_OPTIONS, RunSettings

TUS = ["bitboard", "board", "book", "eval", "eval_params", "nnue", "nnue_v3", "search", "uci"]

LINE_L_CMD = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"

# Expected tree file sha256s (LF line endings)
EXP_TREE_SHAS = {
    "src/search.cpp": "174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4",
    "src/uci.cpp": "2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013",
    "src/board.cpp": "2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf",
    "include/forge/board.hpp": "5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77",
}

# Expected OFF numbers
EXP_BENCH11_NOOPT = 312866
EXP_BENCH13_NOOPT = 862329
EXP_PERFT5_NOOPT = 4865609
EXP_BENCH11_PC20 = 278024
EXP_BENCH13_PC20 = 587276

EXP_SETA_L_RECORDS = 26741
EXP_SETA_L_NODES = 107124743
EXP_SETA_L_SHA = "d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2"

EXP_N60_L_RECORDS = 8449
EXP_N60_L_SEARCHES = 8482
EXP_N60_L_NODES = 36688357
EXP_N60_L_SHA = "b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15"


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")


def sha256_file(path: str | pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def fmt_cmp(label: str, got: object, exp: object) -> tuple[bool, str]:
    ok = got == exp
    st = "PASS" if ok else "FAIL"
    op = "==" if ok else "!="
    return ok, f"  {label:<44s}: {st} ({got} {op} {exp})"


def load_fens(path: pathlib.Path) -> list[str]:
    fens: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s:
            continue
        if ";" in s:
            s = s.split(";", 1)[0].strip()
        toks = s.split()
        if len(toks) >= 6 and toks[4].isdigit() and toks[5].isdigit():
            fens.append(" ".join(toks[:6]))
        elif len(toks) >= 4:
            fens.append(f"{toks[0]} {toks[1]} {toks[2]} {toks[3]} 0 1")
        else:
            raise ValueError(f"Malformed FEN in {path}: {raw!r}")
    return fens


def get_id_name(exe_path: str) -> str:
    res = subprocess.run(
        [exe_path],
        input="uci\nquit\n",
        text=True,
        capture_output=True,
        check=True,
    )
    for ln in res.stdout.splitlines():
        if ln.startswith("id name "):
            return ln.strip()
    return "id name <unknown>"


def release_compile_flags(src_dir: pathlib.Path) -> list[str]:
    return [
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


def release_link_flags() -> list[str]:
    return [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-O3",
        "-march=sapphirerapids",
        "-flto=thin",
        "-fuse-ld=lld-18",
        "-Wl,--thinlto-jobs=4",
        "-pthread",
    ]


def build_release_v3(src_dir: pathlib.Path, bld_dir: pathlib.Path) -> tuple[str, str, str, str]:
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    (bld_dir / "obj").mkdir(parents=True)
    cflags = release_compile_flags(src_dir)
    procs = [
        subprocess.Popen(cflags + ["-c", str(src_dir / "src" / f"{tu}.cpp"), "-o", str(bld_dir / "obj" / f"{tu}.o")])
        for tu in TUS
    ]
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError(f"Release compile failed in {bld_dir}")
    out_exe = bld_dir / "forge"
    lflags = release_link_flags() + [str(bld_dir / "obj" / f"{tu}.o") for tu in TUS] + ["-o", str(out_exe)]
    subprocess.run(lflags, check=True)
    return str(out_exe), sha256_file(out_exe), " ".join(cflags), " ".join(lflags)


def checking_compile_flags(src_dir: pathlib.Path) -> list[str]:
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


def build_checking_v3(src_dir: pathlib.Path, bld_dir: pathlib.Path) -> tuple[str, str, str, str]:
    if bld_dir.exists():
        shutil.rmtree(bld_dir)
    (bld_dir / "obj").mkdir(parents=True)
    cflags = checking_compile_flags(src_dir)
    procs = [
        subprocess.Popen(cflags + ["-c", str(src_dir / "src" / f"{tu}.cpp"), "-o", str(bld_dir / "obj" / f"{tu}.o")])
        for tu in TUS
    ]
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError(f"Checking compile failed in {bld_dir}")
    out_exe = bld_dir / "forge"
    lflags = checking_link_flags() + [str(bld_dir / "obj" / f"{tu}.o") for tu in TUS] + ["-o", str(out_exe)]
    subprocess.run(lflags, check=True)
    return str(out_exe), sha256_file(out_exe), " ".join(cflags), " ".join(lflags)


def apply_patch_to_fresh_v3(patch_path: pathlib.Path, dst_dir: pathlib.Path) -> tuple[bool, str]:
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    shutil.copytree(TPL_V3, dst_dir)
    chk = subprocess.run(
        ["git", "apply", "--check", "-p1", str(patch_path)],
        cwd=str(dst_dir),
        text=True,
        capture_output=True,
    )
    if chk.returncode != 0:
        return False, f"git apply --check -p1 FAILED (rc={chk.returncode}): {chk.stderr.strip()}"
    ap = subprocess.run(
        ["git", "apply", "-p1", str(patch_path)],
        cwd=str(dst_dir),
        text=True,
        capture_output=True,
        check=True,
    )
    return True, "git apply --check -p1 PASS (0 == 0)"


def generate_diff_u_patch(base_dir: pathlib.Path, mod_dir: pathlib.Path, out_patch: pathlib.Path) -> None:
    rel_files: list[str] = []
    for p in sorted(list((mod_dir / "include").rglob("*.hpp")) + list((mod_dir / "src").rglob("*.cpp"))):
        rel = str(p.relative_to(mod_dir))
        b_file = base_dir / rel
        if not b_file.exists() or b_file.read_bytes() != p.read_bytes():
            assert b"\r\n" not in p.read_bytes(), f"CRLF detected in {p}"
            rel_files.append(rel)
    chunks: list[str] = []
    for rel in rel_files:
        res = subprocess.run(
            [
                "diff",
                "-u",
                "--label",
                f"a/{rel}",
                "--label",
                f"b/{rel}",
                str(base_dir / rel),
                str(mod_dir / rel),
            ],
            text=True,
            capture_output=True,
        )
        assert res.returncode == 1, f"Expected diff rc=1 on {rel}, got {res.returncode}"
        chunks.append(res.stdout)
    patch_txt = "".join(chunks)
    assert "\r" not in patch_txt, "CRLF in generated patch"
    out_patch.write_bytes(patch_txt.encode("utf-8"))


def run_fresh_bench(exe: str, depth: int, opt_lines: list[str]) -> int:
    opt_block = "".join(ln + "\n" for ln in opt_lines)
    stdin = f"uci\n{opt_block}isready\nbench {depth}\nisready\nquit\n"
    res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
    if res.stderr:
        raise RuntimeError(f"Non-empty stderr from {exe}: {res.stderr}")
    prefix = f"info string bench depth {depth} nodes "
    for ln in res.stdout.splitlines():
        if ln.startswith(prefix):
            return int(ln[len(prefix) :].split()[0])
    raise RuntimeError(f"Missing '{prefix}' in {exe} stdout")


def run_fresh_perft5(exe: str) -> int:
    stdin = "uci\nisready\nposition startpos\ngo perft 5\nisready\nquit\n"
    res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
    if res.stderr:
        raise RuntimeError(f"Non-empty stderr from {exe}: {res.stderr}")
    for ln in reversed(res.stdout.splitlines()):
        if ln.startswith("nodes "):
            return int(ln.split()[1])
    raise RuntimeError(f"Missing 'nodes <N>' in {exe} perft stdout")


def pc20_option_lines(extra_opts: Optional[list[tuple[str, str]]] = None) -> list[str]:
    opts = list(PC20_OPTIONS)
    if extra_opts:
        opts.extend(extra_opts)
    return [f"setoption name {k} value {v}" for k, v in opts]


def run_selfgame_set_with_options(
    exe_path: str,
    seed: str,
    attempts: int,
    net_path: Optional[str],
    extra_opts: Optional[list[tuple[str, str]]] = None,
    cpu_pin: Optional[int] = None,
) -> V3SuiteRun:
    """
    Runs the exact Job 36 `loop_v3_driver.py` selfgame loop (`version=3`, `LINE_L_CMD`),
    with optional extra UCI options (`IdeaXX=true` etc.) sent right after `PC20_OPTIONS`.
    Preserves the single canonical Job 36 label (`thrown@N` on `noscore`, `maxsims@N` on `maxsims`).
    """
    if not extra_opts:
        return run_loop_detailed(
            exe_path,
            3,
            seed,
            attempts,
            RunSettings(net_path=net_path),
            cpu_pin=cpu_pin,
            custom_sg_cmd=LINE_L_CMD,
        )

    import chess
    import random
    from loop_driver import parse_sgerror_v2
    from loop_v3_driver import V3AttemptDetail, parse_sgend_v3
    from ref_driver import format_game_records

    def start_eng() -> subprocess.Popen[str]:
        cmd = [exe_path] if cpu_pin is None else ["taskset", "-c", str(cpu_pin), exe_path]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        assert p.stdin is not None and p.stdout is not None
        p.stdin.write("uci\n")
        p.stdin.flush()
        while p.stdout.readline().rstrip("\r\n") != "uciok":
            pass
        opts = list(PC20_OPTIONS) + list(extra_opts)
        if net_path is not None:
            opts.append(("NNUEArchFile", net_path))
            opts.append(("NNUEArch", "true"))
        p.stdin.write("".join(f"setoption name {k} value {v}\n" for k, v in opts) + "isready\n")
        p.stdin.flush()
        while True:
            ln = p.stdout.readline().rstrip("\r\n")
            if ln == "readyok":
                break
        return p

    def close_eng(p: subprocess.Popen[str]) -> None:
        if p.poll() is None and p.stdin is not None:
            try:
                p.stdin.write("quit\n")
                p.stdin.flush()
            except BrokenPipeError:
                pass
        p.wait()
        if p.stdin:
            p.stdin.close()
        if p.stdout:
            p.stdout.close()
        if p.stderr:
            p.stderr.close()

    rng = random.Random(seed)
    proc = start_eng()
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

    try:
        for attempt_idx in range(1, attempts + 1):
            assert proc.stdin is not None and proc.stdout is not None
            board = chess.Board()
            opening_moves: list[str] = []
            rng.sample(range(0, 8), 8)

            proc.stdin.write("ucinewgame\nisready\n")
            proc.stdin.flush()
            while proc.stdout.readline().rstrip("\r\n") != "readyok":
                pass

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
                is_rule_draw = board.is_insufficient_material() or board.halfmove_clock >= 100 or board.is_repetition(3)
                if is_rule_draw or ply >= 300:
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

            pos_cmd = "position startpos moves " + " ".join(opening_moves) if opening_moves else "position startpos"
            proc.stdin.write(f"{pos_cmd}\n{LINE_L_CMD}\n")
            proc.stdin.flush()

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
                line = proc.stdout.readline()
                if line == "":
                    rc = proc.wait()
                    raise RuntimeError(f"Unexpected EOF from {exe_path} (rc={rc})")
                line = line.rstrip("\r\n")
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
                        _run_val,
                        att_searches,
                        att_nodes,
                        final_fen,
                        loop_moves,
                        _stripped,
                    ) = parse_sgend_v3(line)
                    break
                elif line.startswith("sgerror "):
                    sgerror_line = line
                    kind, thrown_ply, att_searches, att_nodes, _err_fen = parse_sgerror_v2(line)
                    thrown = True
                    att_plies = thrown_ply
                    end_reason = f"thrown@{thrown_ply}" if kind == "noscore" else f"{kind}@{thrown_ply}"
                    close_eng(proc)
                    proc = start_eng()
                    break
                else:
                    raise ValueError(f"Unexpected line during selfgame: {line!r}")

            total_sg_lines += len(sg_lines)
            moves_all += att_plies
            total_searches += att_searches
            total_nodes += att_nodes

            if thrown:
                thrown_away += 1
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
        close_eng(proc)

    return V3SuiteRun(
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
    )


def verify_all_off_numbers(label: str, exe_path: str, extra_off_opts: Optional[list[tuple[str, str]]] = None) -> tuple[bool, list[str]]:
    """
    Verifies EVERY OFF number of Step 0 on `exe_path`:
      - no-option bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609 (fresh processes)
      - PC20 (+ explicit switch=false if given) bench 11 = 278024, bench 13 = 587276 (fresh processes)
      - Set A line L through selfgame driver = 26,741 records / 107,124,743 nodes / d5b52710...
      - n[1..60] line L through selfgame driver = 8,449 records / 36,688,357 nodes / b6bf7600...
    Runs Set A line L and n[1..60] line L concurrently on separate cores for speed (single-threaded node/text deterministic!).
    """
    pc20_lines = pc20_option_lines(extra_off_opts)
    b11 = run_fresh_bench(exe_path, 11, [])
    b13 = run_fresh_bench(exe_path, 13, [])
    p5 = run_fresh_perft5(exe_path)
    pc_b11 = run_fresh_bench(exe_path, 11, pc20_lines)
    pc_b13 = run_fresh_bench(exe_path, 13, pc20_lines)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(run_selfgame_set_with_options, exe_path, "carbon2-job33-a", 200, None, extra_off_opts, 1)
        fut_n = pool.submit(run_selfgame_set_with_options, exe_path, "carbon2-job33-n", 60, NET768, extra_off_opts, 2)
        res_a = fut_a.result()
        res_n = fut_n.result()

    checks = [
        (f"{label} no-option bench 11", b11, EXP_BENCH11_NOOPT),
        (f"{label} no-option bench 13", b13, EXP_BENCH13_NOOPT),
        (f"{label} no-option perft 5", p5, EXP_PERFT5_NOOPT),
        (f"{label} PC20 bench 11", pc_b11, EXP_BENCH11_PC20),
        (f"{label} PC20 bench 13", pc_b13, EXP_BENCH13_PC20),
        (f"{label} Set A line L records", res_a.total_records, EXP_SETA_L_RECORDS),
        (f"{label} Set A line L nodes", res_a.total_nodes, EXP_SETA_L_NODES),
        (f"{label} Set A line L sha256", res_a.full_sha256, EXP_SETA_L_SHA),
        (f"{label} n[1..60] line L records", res_n.total_records, EXP_N60_L_RECORDS),
        (f"{label} n[1..60] line L searches", res_n.total_searches, EXP_N60_L_SEARCHES),
        (f"{label} n[1..60] line L nodes", res_n.total_nodes, EXP_N60_L_NODES),
        (f"{label} n[1..60] line L sha256", res_n.full_sha256, EXP_N60_L_SHA),
    ]
    all_ok = True
    lines = [f"[{label}] exe={exe_path} | sha256={sha256_file(exe_path)} | {get_id_name(exe_path)}"]
    for cname, got, exp in checks:
        ok, s = fmt_cmp(cname, got, exp)
        all_ok = all_ok and ok
        lines.append(s)
    return all_ok, lines


def run_epd_depth12(
    exe_path: str,
    set_path: pathlib.Path,
    extra_opts: Optional[list[tuple[str, str]]],
    out_rows: pathlib.Path,
    out_meta: pathlib.Path,
    depth: int = 12,
    cpu_pin: Optional[int] = None,
) -> list[tuple[int, int, str, str]]:
    """
    Runs `set_path` at `depth` under `PC20` + `extra_opts` (built-in evaluation, Threads 1, Hash 16),
    sending `ucinewgame` + `isready` before EVERY search.
    Writes `out_rows` (`position\tnodes\tbestmove\tscore`) and `out_meta` (`exe path, sha256, id name, every option line sent`).
    Returns list of `(idx_1based, nodes, bestmove, score_str)`.
    """
    fens = load_fens(set_path)
    opt_lines = pc20_option_lines(extra_opts)
    cmd = [exe_path] if cpu_pin is None else ["taskset", "-c", str(cpu_pin), exe_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    assert proc.stdin is not None and proc.stdout is not None

    proc.stdin.write("uci\n")
    proc.stdin.flush()
    id_name = "id name <unknown>"
    while True:
        ln = proc.stdout.readline()
        if ln == "":
            raise RuntimeError(f"EOF waiting for uciok from {exe_path}")
        ln = ln.rstrip("\r\n")
        if ln.startswith("id name "):
            id_name = ln
        elif ln == "uciok":
            break

    proc.stdin.write("".join(o + "\n" for o in opt_lines) + "isready\n")
    proc.stdin.flush()
    while proc.stdout.readline().rstrip("\r\n") != "readyok":
        pass

    rows: list[tuple[int, int, str, str]] = []
    for idx, fen in enumerate(fens, start=1):
        proc.stdin.write(f"ucinewgame\nisready\nposition fen {fen}\ngo depth {depth}\n")
        proc.stdin.flush()
        saw_ready = False
        d_nodes: Optional[int] = None
        d_score: Optional[str] = None
        bestmove: Optional[str] = None
        while True:
            ln = proc.stdout.readline()
            if ln == "":
                raise RuntimeError(f"EOF at position {idx} from {exe_path}")
            ln = ln.rstrip("\r\n")
            if not saw_ready:
                if ln == "readyok":
                    saw_ready = True
                continue
            if ln.startswith(f"info depth {depth} ") and " nodes " in ln and " score " in ln:
                toks = ln.split()
                ni = toks.index("nodes")
                si = toks.index("score")
                d_nodes = int(toks[ni + 1])
                d_score = f"{toks[si + 1]} {toks[si + 2]}"
            elif ln.startswith("bestmove "):
                bestmove = ln.split()[1]
                break
        if d_nodes is None or d_score is None or bestmove is None:
            raise RuntimeError(f"Missing depth-{depth} info or bestmove at pos {idx}: nodes={d_nodes} score={d_score} bestmove={bestmove}")
        rows.append((idx, d_nodes, bestmove, d_score))

    proc.stdin.write("quit\n")
    proc.stdin.flush()
    stderr_txt = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()
    if rc != 0 or stderr_txt:
        raise RuntimeError(f"Engine exited rc={rc} stderr={stderr_txt!r}")

    total_nodes = sum(r[1] for r in rows)
    header = [
        f"# set={set_path.name} positions={len(rows)} depth={depth} sum_nodes={total_nodes}",
        "position\tnodes\tbestmove\tscore",
    ]
    body = [f"{pos}\t{nd}\t{bm}\t{sc}" for pos, nd, bm, sc in rows]
    out_rows.write_text("\n".join(header + body) + "\n", encoding="utf-8")

    meta = [
        f"exe_path: {exe_path}",
        f"exe_sha256: {sha256_file(exe_path)}",
        f"id_name: {id_name}",
        f"set_name: {set_path.name}",
        f"set_sha256: {sha256_file(set_path)}",
        f"positions: {len(rows)}",
        f"depth: {depth}",
        f"sum_nodes: {total_nodes}",
        "per_search_reset: ucinewgame + isready",
        "options_sent_begin:",
        *[f"  {o}" for o in opt_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    out_meta.write_text("\n".join(meta) + "\n", encoding="utf-8")
    return rows


def write_seta_meta(
    out_meta: pathlib.Path,
    exe_path: str,
    extra_opts: Optional[list[tuple[str, str]]],
    run: V3SuiteRun,
) -> None:
    opt_lines = pc20_option_lines(extra_opts)
    meta = [
        f"exe_path: {exe_path}",
        f"exe_sha256: {sha256_file(exe_path)}",
        f"id_name: {get_id_name(exe_path)}",
        "suite: Set A (seed='carbon2-job33-a', attempts=200, built-in evaluation)",
        f"selfgame_line: {LINE_L_CMD}",
        f"records: {run.total_records}",
        f"searches: {run.total_searches}",
        f"nodes: {run.total_nodes}",
        f"record_text_sha256: {run.full_sha256}",
        "options_sent_begin:",
        *[f"  {o}" for o in opt_lines],
        "options_sent_end",
        f"utc_completed: {utc_now()}",
    ]
    out_meta.write_text("\n".join(meta) + "\n", encoding="utf-8")


def diff_rows(
    rows_a: list[tuple[int, int, str, str]],
    rows_b: list[tuple[int, int, str, str]],
) -> tuple[int, int]:
    """
    Returns `(any_field_diff_count, nodes_diff_count)` across all positions.
    """
    assert len(rows_a) == len(rows_b)
    any_diff = sum(1 for a, b in zip(rows_a, rows_b) if a[1:] != b[1:])
    nd_diff = sum(1 for a, b in zip(rows_a, rows_b) if a[1] != b[1])
    return any_diff, nd_diff
