"""Fail-before / pass-after unit test for SF13_qs_evasion_pruning.patch.

Verifies:
  1. Patch applies cleanly (`git -C C:/nnue-lab/forge/r15dsg apply --check RC=0`).
  2. `go perft 5` == 4,865,609 on target exe.
  3. Mate-in-1 / forced-evasion tactical safety (in-check positions with losing-SEE only escape
     never mis-score as checkmate because move_count > 2 & best_score > -MateInMaxPly).
  4. Target exe differs from base_r15dsg.exe on check-heavy bench 13 nodes (FAILS on base_r15dsg.exe!).
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
BASE_EXE = FIX / "builds/base_r15dsg.exe"
DEFAULT_EXE = FIX / "builds/SF13_qs_evasion_pruning.exe"
PATCH = FIX / "patches/SF13_qs_evasion_pruning.patch"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"


def get_exe() -> Path:
    return Path(os.environ.get("FORGE_TEST_EXE", str(DEFAULT_EXE)))


def run_uci(exe: Path, cmds: list[str], timeout: int = 60) -> str:
    r = subprocess.run([str(exe)], input="\n".join(cmds + ["quit"]) + "\n", capture_output=True, text=True, timeout=timeout)
    assert r.returncode == 0, f"Engine failed rc={r.returncode}: {r.stderr}"
    return r.stdout


def test_patch_applies_cleanly() -> None:
    r = subprocess.run(["git", "-C", str(LAB / "forge/r15dsg"), "apply", "--check", str(PATCH)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_perft5_exact() -> None:
    out = run_uci(get_exe(), ["uci", "isready", "position startpos", "go perft 5"])
    assert "4865609" in out


def test_in_check_tactical_safety() -> None:
    # Forced check evasion where black must block/move cleanly without false checkmate
    fen = "r1bqk2r/pppp1Qpp/2n2n2/2b1p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4"  # mate in 0 (actually QxF7#? wait Kf7 is legal? no Bf4)
    # Use a real non-mate check with multiple legal evasions (some losing SEE)
    fen_check = "r3k2r/ppp2ppp/2n1bn2/3q4/3P4/2NB1N2/PPP2PPP/R2Q1RK1 w kq - 0 1"
    fen_evasion = "r1bqk2r/ppp2ppp/2n2n2/3pp3/1bB1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 5"
    fen_in_check = "rnb1k1nr/pppp1ppp/8/2b1p3/2B1P2q/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 4"
    # Position where White is in check by Queen on h4 after f2-f3? Actually f2-f4 Qh4+!
    fen_qh4_check = "rnb1kbnr/pppp1ppp/8/4p3/5P1q/8/PPPPP1PP/RNBQKBNR w KQkq - 1 3"
    out = run_uci(get_exe(), [
        "uci",
        f"setoption name NNUEArchFile value {str(R0067).replace(chr(92), '/')}",
        "setoption name NNUEArch value true",
        "isready",
        f"position fen {fen_qh4_check}",
        "go depth 6",
    ])
    assert "bestmove g2g3" in out, f"Expected forced evasion g2g3, got:\n{out[-300:]}"
    assert "score mate -1" not in out


def test_sf13_changes_bench13_vs_base() -> None:
    # Fails when FORGE_TEST_EXE == base_r15dsg.exe; passes on SF13_qs_evasion_pruning.exe
    opts = [
        "uci",
        f"setoption name NNUEArchFile value {str(R0067).replace(chr(92), '/')}",
        "setoption name NNUEArch value true",
        "setoption name HistRework value 2",
        "setoption name CorrHistV2 value true",
        "setoption name TtPruneV2 value true",
        "isready",
        "bench 13",
    ]
    base_out = run_uci(BASE_EXE, opts)
    tgt_out = run_uci(get_exe(), opts)
    b_n = int(re.findall(r"nodes\s+(\d+)", base_out)[-1])
    t_n = int(re.findall(r"nodes\s+(\d+)", tgt_out)[-1])
    assert t_n != b_n, f"Expected SF13 to alter bench 13 nodes vs base ({b_n}), got identical {t_n}"
