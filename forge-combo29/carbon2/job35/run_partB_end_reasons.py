#!/usr/bin/env python3
"""
Job 35 Part B — The Nine End-Reason Positions (B1..B9), sgstate vs python-chess 1.11.2,
and Control CE (rule (b) tested before rule (a)).
"""
from __future__ import annotations

import datetime
import hashlib
import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
import chess

JOB35 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job35")
JOB33 = pathlib.Path("/agent/repos/dwqww/forge-combo29/carbon2/job33")
sys.path.insert(0, str(JOB35))
sys.path.insert(0, str(JOB33))

from kb1_check import parse_sgstate
from ref_driver import PC20_OPTIONS

R15D_SRC = pathlib.Path("/tmp/carbon2_work/src_r15d")
R15D_EXE = "/tmp/carbon2_job11/bld_sp_r15d_1/forge"
V2_EXE = "/tmp/carbon2_job35/bld_sp_sgr15v/forge"
CE_EXE = "/tmp/carbon2_job35/bld_ce_sgr15d/forge"
WORK = pathlib.Path("/tmp/carbon2_job35")

TUS = ["bitboard", "board", "book", "eval", "eval_params", "nnue", "nnue_v3", "search", "uci"]

DEFAULT_SG = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"
B4_SG = "selfgame softnodes 2000 evallimit 2000 maxply 8 writeminply 8 drawply 80 drawscore 5 drawcount 8"

CASES: list[tuple[str, str, str, str | None, str]] = [
    (
        "B1",
        "position startpos moves f2f3 e7e5 g2g4 d8h4",
        DEFAULT_SG,
        "sgend result -1 reason mate plies 4 run 0 searches 0 nodes 0 moves",
        "White mated",
    ),
    (
        "B2",
        "position startpos moves e2e3 a7a5 d1h5 a8a6 h5a5 h7h5 h2h4 a6h6 a5c7 f7f6 c7d7 e8f7 d7b7 d8d3 b7b8 d3h7 b8c8 f7g6 c8e6",
        DEFAULT_SG,
        "sgend result 0 reason stalemate plies 19 run 0 searches 0 nodes 0 moves",
        "Black stalemated",
    ),
    (
        "B3",
        "position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
        DEFAULT_SG,
        "sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 moves",
        "third occurrence",
    ),
    (
        "B4",
        "position startpos moves e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 d2d3 f8c5",
        B4_SG,
        "sgend result 0 reason plylimit plies 8 run 0 searches 0 nodes 0 moves",
        "no rule, maxply 8",
    ),
    (
        "B5",
        "position fen 8/8/8/4k3/8/8/8/4K3 w - - 0 1",
        DEFAULT_SG,
        "sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves",
        "insufficient material",
    ),
    (
        "B6",
        "position fen 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80",
        DEFAULT_SG,
        "sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves",
        "halfmove clock 100",
    ),
    (
        "B7",
        "position fen R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80",
        DEFAULT_SG,
        "sgend result 1 reason mate plies 0 run 0 searches 0 nodes 0 moves",
        "Black mated AND clock 100: (a) comes first",
    ),
    (
        "B8",
        "position fen k7/2K5/8/2B5/8/8/8/8 b - - 0 1",
        DEFAULT_SG,
        "sgend result 0 reason stalemate plies 0 run 0 searches 0 nodes 0 moves",
        "stalemate AND insufficient material: (a) comes first",
    ),
    (
        "B9",
        "position fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
        DEFAULT_SG,
        None,  # nodes count cross-checked against plain r15d go softnodes 2000
        "mate in 1: a1a8",
    ),
]


def build_control_ce() -> tuple[str, str]:
    v2_patch = (JOB35 / "selfgame_r15d_v2.patch.txt").read_text()
    ce_patch_path = JOB35 / "control_CE_b_before_a.patch.txt"

    a_dir = WORK / "ce_diff_a"
    b_dir = WORK / "ce_diff_b"
    for d in (a_dir, b_dir):
        if d.exists():
            shutil.rmtree(d)
    shutil.copytree(R15D_SRC, a_dir)
    shutil.copytree(R15D_SRC, b_dir)
    subprocess.run(
        ["patch", "-d", str(b_dir), "-p1", "--fuzz=0", "--no-backup-if-mismatch"],
        input=v2_patch,
        text=True,
        check=True,
    )

    uci_p = b_dir / "src/uci.cpp"
    uci_s = uci_p.read_text()
    old_ab = """        const SgState st = evaluate_sg_state(board);
        if (!st.legal) {
            if (!st.check) {
                end_result = 0;
                end_reason = "stalemate";
            } else {
                end_result = (board.side_to_move() == forge::White) ? -1 : 1;
                end_reason = "mate";
            }
            break;
        }

        const bool rule_draw = st.material || st.clock >= 100 || st.rep3;
        if (rule_draw || ply >= cfg.max_ply) {
            end_result = 0;
            end_reason = rule_draw ? "rule" : "plylimit";
            break;
        }"""

    new_ba = """        const SgState st = evaluate_sg_state(board);
        const bool rule_draw = st.material || st.clock >= 100 || st.rep3;
        if (rule_draw || ply >= cfg.max_ply) {
            end_result = 0;
            end_reason = rule_draw ? "rule" : "plylimit";
            break;
        }

        if (!st.legal) {
            if (!st.check) {
                end_result = 0;
                end_reason = "stalemate";
            } else {
                end_result = (board.side_to_move() == forge::White) ? -1 : 1;
                end_reason = "mate";
            }
            break;
        }"""

    assert uci_s.count(old_ab) == 1
    uci_p.write_text(uci_s.replace(old_ab, new_ba, 1))

    diff_chunks = []
    for rel in ["include/forge/board.hpp", "src/board.cpp", "src/uci.cpp"]:
        p = subprocess.run(
            ["diff", "-u", f"--label=a/{rel}", f"--label=b/{rel}", str(a_dir / rel), str(b_dir / rel)],
            text=True,
            capture_output=True,
        )
        assert p.returncode == 1
        diff_chunks.append(p.stdout)
    ce_patch_txt = "".join(diff_chunks)
    ce_patch_path.write_text(ce_patch_txt)
    ce_patch_sha = hashlib.sha256(ce_patch_path.read_bytes()).hexdigest()

    src_ce = WORK / "src_ce_sgr15d"
    bld_ce = WORK / "bld_ce_sgr15d"
    if src_ce.exists():
        shutil.rmtree(src_ce)
    if bld_ce.exists():
        shutil.rmtree(bld_ce)
    shutil.copytree(b_dir, src_ce)
    (bld_ce / "obj").mkdir(parents=True)
    shutil.rmtree(a_dir)
    shutil.rmtree(b_dir)

    flags = [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-std=c++20",
        "-O3",
        "-DNDEBUG",
        "-DFORGE_NNUE_HIDDEN=256",
        f'-DFORGE_NNUE_WEIGHTS="{src_ce}/src/nnue_weights.inc"',
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
        f"-I{src_ce}/include",
    ]
    procs = [
        subprocess.Popen(flags + ["-c", f"{src_ce}/src/{tu}.cpp", "-o", f"{bld_ce}/obj/{tu}.o"])
        for tu in TUS
    ]
    for pr in procs:
        assert pr.wait() == 0
    link = [
        "clang++-18",
        "--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13",
        "-O3",
        "-march=sapphirerapids",
        "-flto=thin",
        "-fuse-ld=lld-18",
        "-Wl,--thinlto-jobs=1",
        "-pthread",
    ] + [f"{bld_ce}/obj/{tu}.o" for tu in TUS] + ["-o", CE_EXE]
    subprocess.run(link, check=True)
    ce_exe_sha = hashlib.sha256(pathlib.Path(CE_EXE).read_bytes()).hexdigest()
    return ce_patch_sha, ce_exe_sha


def get_b9_ref_nodes() -> tuple[int, str, str]:
    pc20 = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    proc = subprocess.Popen(
        [R15D_EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
    )
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(
        f"uci\n{pc20}isready\nucinewgame\nisready\n"
        "position fen 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1\n"
        "go softnodes 2000\n"
    )
    proc.stdin.flush()
    soft_nodes = -1
    score_str = ""
    best_mv = ""
    while True:
        ln = proc.stdout.readline()
        if not ln:
            break
        ln = ln.rstrip("\r\n")
        if ln.startswith("info ") and " score " in ln:
            score_str = " ".join(ln.split(" score ", 1)[1].split()[:2])
        if ln.startswith("info string softnodes nodes "):
            soft_nodes = int(ln.split()[4])
        if ln.startswith("bestmove "):
            best_mv = ln.split()[1]
            break
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    proc.wait()
    assert soft_nodes > 0
    return soft_nodes, score_str, best_mv


def run_one_selfgame(exe: str, pos_cmd: str, sg_cmd: str) -> tuple[list[str], str]:
    pc20 = "".join(f"setoption name {k} value {v}\n" for k, v in PC20_OPTIONS)
    stdin = f"uci\n{pc20}isready\nucinewgame\nisready\n{pos_cmd}\n__MARK__\n{sg_cmd}\nisready\nquit\n"
    # Note: unknown UCI command `__MARK__` is ignored silently; instead synchronize via the second `readyok`!
    stdin = f"uci\n{pc20}isready\nucinewgame\nisready\n{pos_cmd}\n{sg_cmd}\nisready\nquit\n"
    res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
    if res.stderr:
        raise RuntimeError(f"Non-empty stderr: {res.stderr}")
    lines = [ln.rstrip("\r\n") for ln in res.stdout.splitlines()]
    # Collect lines strictly between the 2nd readyok and the 3rd readyok
    ready_idxs = [i for i, ln in enumerate(lines) if ln == "readyok"]
    assert len(ready_idxs) == 3, f"Expected 3 readyok lines, got {ready_idxs}: {lines}"
    sg_block = lines[ready_idxs[1] + 1 : ready_idxs[2]]
    sg_lines = [x for x in sg_block if x.startswith("sg ")]
    end_lines = [x for x in sg_block if x.startswith("sgend ") or x.startswith("sgerror ")]
    assert len(end_lines) == 1 and len(sg_lines) + 1 == len(sg_block), f"Unexpected selfgame output: {sg_block}"
    return sg_lines, end_lines[0]


def python_chess_board_for(pos_cmd: str) -> chess.Board:
    if pos_cmd.startswith("position startpos"):
        b = chess.Board()
        if " moves " in pos_cmd:
            for u in pos_cmd.split(" moves ", 1)[1].split():
                b.push_uci(u)
        return b
    assert pos_cmd.startswith("position fen ")
    rest = pos_cmd[len("position fen ") :]
    if " moves " in rest:
        fen_part, mvs = rest.split(" moves ", 1)
        b = chess.Board(fen_part)
        for u in mvs.split():
            b.push_uci(u)
        return b
    return chess.Board(rest)


def run_sgstate_check_9(exe: str) -> tuple[int, str, list[str]]:
    lines_out: list[str] = []
    diffs = 0
    first_diff = ""
    for name, pos_cmd, _, _, note in CASES:
        b = python_chess_board_for(pos_cmd)
        assert b.is_valid(), f"python-chess says {name} invalid!"
        exp = (
            1 if any(b.legal_moves) else 0,
            1 if b.is_check() else 0,
            1 if b.is_insufficient_material() else 0,
            b.halfmove_clock,
            1 if b.is_repetition(3) else 0,
            b.fen(),
        )
        stdin = f"uci\nisready\nucinewgame\n{pos_cmd}\nsgstate\nquit\n"
        res = subprocess.run([exe], input=stdin, text=True, capture_output=True, check=True)
        sg_ln = next(ln.rstrip("\r\n") for ln in res.stdout.splitlines() if ln.startswith("sgstate "))
        got = parse_sgstate(sg_ln)
        eq = got == exp
        if not eq:
            diffs += 1
            if not first_diff:
                first_diff = f"{name}: got={got} != exp={exp}"
        lines_out.append(f"  {name} [{note}]: {'EQUAL' if eq else 'DIFF'} | {sg_ln}")
    return diffs, first_diff, lines_out


def main() -> None:
    ce_patch_sha, ce_exe_sha = build_control_ce()
    b9_nodes, b9_score, b9_move = get_b9_ref_nodes()
    b9_expected = f"sgend result 1 reason matescore plies 0 run 0 searches 1 nodes {b9_nodes} moves"

    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%a %b %d %I:%M:%S %p UTC %Y")
    out: list[str] = [
        f"UTC: {utc}",
        "=== JOB 35 PART B — Nine End-Reason Positions (B1..B9), sgstate Check, and Control CE ===",
        f"python-chess version: {chess.__version__}",
        f"v2 exe:  {V2_EXE}",
        f"CE exe:  {CE_EXE} (exe_sha256={ce_exe_sha})",
        f"CE patch: forge-combo29/carbon2/job35/control_CE_b_before_a.patch.txt (sha256={ce_patch_sha})",
        f"B9 plain-r15d reference search (go softnodes 2000): bestmove={b9_move}, score='{b9_score}', nodes={b9_nodes}",
        "",
        "--- 1. v2 Build: Nine Positions B1..B9 ---",
    ]

    v2_lines: dict[str, str] = {}
    all_v2_ok = True
    for name, pos_cmd, sg_cmd, exp_line, note in CASES:
        exp = b9_expected if name == "B9" else exp_line
        assert exp is not None
        sg_lns, end_ln = run_one_selfgame(V2_EXE, pos_cmd, sg_cmd)
        v2_lines[name] = end_ln
        no_sg_ok = len(sg_lns) == 0
        eq = (end_ln == exp) and no_sg_ok
        all_v2_ok = all_v2_ok and eq
        verdict = "EQUAL" if eq else f"DIFF (expected: {exp!r}, sg_lines={len(sg_lns)})"
        out.append(f"  {name} [{note}]: {verdict} (sg_lines: {len(sg_lns)} == 0)")
        out.append(f"    printed : {end_ln}")
        out.append(f"    expected: {exp}")

    out.append(f"v2 B1..B9 check: {'PASS' if all_v2_ok else 'FAIL'} (equal_positions: {sum(1 for n,_,_,e,_ in CASES if v2_lines[n] == (b9_expected if n=='B9' else e))} == 9)")
    out.append("")
    out.append("--- 2. sgstate on B1..B9 vs python-chess 1.11.2 ---")
    sg_diffs, sg_first, sg_rows = run_sgstate_check_9(V2_EXE)
    out.extend(sg_rows)
    out.append(f"sgstate B1..B9 differences vs python-chess: {'PASS' if sg_diffs == 0 else 'FAIL'} ({sg_diffs} == 0)")
    if sg_first:
        out.append(f"  FIRST DIFF: {sg_first}")

    out.append("")
    out.append("--- 3. CONTROL CE ((b) tested before (a)): All Nine Lines Side-by-Side ---")
    ce_lines: dict[str, str] = {}
    changed_names: list[str] = []
    for name, pos_cmd, sg_cmd, _, note in CASES:
        sg_lns, end_ln = run_one_selfgame(CE_EXE, pos_cmd, sg_cmd)
        assert len(sg_lns) == 0
        ce_lines[name] = end_ln
        changed = end_ln != v2_lines[name]
        if changed:
            changed_names.append(name)
        tag = "CHANGED" if changed else "UNCHANGED"
        out.append(f"  {name} [{tag}]:")
        out.append(f"    v2: {v2_lines[name]}")
        out.append(f"    CE: {end_ln}")

    exp_b7_ce = "sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves"
    exp_b8_ce = "sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves"
    ce_ok = (
        changed_names == ["B7", "B8"]
        and ce_lines["B7"] == exp_b7_ce
        and ce_lines["B8"] == exp_b8_ce
    )
    out.append("")
    out.append(f"  CONTROL CE changed set : {'PASS' if changed_names == ['B7', 'B8'] else 'FAIL'} ({changed_names} == ['B7', 'B8'])")
    out.append(f"  CONTROL CE B7 line     : {'PASS' if ce_lines['B7'] == exp_b7_ce else 'FAIL'} ({ce_lines['B7']!r} == {exp_b7_ce!r})")
    out.append(f"  CONTROL CE B8 line     : {'PASS' if ce_lines['B8'] == exp_b8_ce else 'FAIL'} ({ce_lines['B8']!r} == {exp_b8_ce!r})")
    out.append(f"PART B OVERALL: {'PASS' if (all_v2_ok and sg_diffs == 0 and ce_ok) else 'FAIL'} ({int(all_v2_ok and sg_diffs == 0 and ce_ok)} == 1)")

    txt = "\n".join(out) + "\n"
    (JOB35 / "partB_end_reasons_CE_raw.txt").write_text(txt)
    print(txt, flush=True)
    if not (all_v2_ok and sg_diffs == 0 and ce_ok):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
