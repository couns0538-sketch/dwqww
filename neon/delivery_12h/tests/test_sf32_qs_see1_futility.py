"""Fail-before / pass-after behavioral & mate-safety test for SF32_qs_see1_futility_pruning.

Tests:
  1. Mate-in-1 / mate-in-2 sanity (both base and SF32 must pass).
  2. Mate search (`go mate 2`) exactness (both base and SF32 must pass).
  3. Behavioral signature: on defended equal-exchange tactical middlegames at depth 9,
     SF32_qs_see1_futility_pruning MUST produce a distinct node count from base_r15dsg
     (fails on base_r15dsg.exe, passes on SF32_qs_see1_futility_pruning.exe!).
  4. Determinism: identical node count across 2 consecutive runs.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3").replace("\\", "/")
BASE_EXE = FIX / "builds/base_r15dsg.exe"
SF32_EXE = FIX / "builds/SF32_qs_see1_futility_pruning.exe"


def run_uci(exe: Path, cmds: list[str]) -> str:
    p = subprocess.Popen(
        [str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    out_lines: list[str] = []

    def send(s: str) -> None:
        assert p.stdin is not None
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def read_until(prefix: str) -> None:
        assert p.stdout is not None
        while True:
            ln = p.stdout.readline()
            if not ln:
                break
            out_lines.append(ln)
            if ln.startswith(prefix):
                return

    try:
        send("uci")
        read_until("uciok")
        send(f"setoption name NNUEArchFile value {R0067}")
        send("setoption name NNUEArch value true")
        send("setoption name HistRework value 2")
        send("setoption name CorrHistV2 value true")
        send("setoption name TtPruneV2 value true")
        send("isready")
        read_until("readyok")
        for c in cmds:
            send(c)
            if c.startswith("go "):
                read_until("bestmove")
        send("quit")
        p.wait(timeout=10)
    finally:
        if p.poll() is None:
            p.kill()
    assert p.returncode == 0, f"nonzero rc={p.returncode}"
    return "".join(out_lines)


def extract_nodes(out: str) -> int:
    m = re.findall(r"info .*?nodes (\d+)", out)
    assert m, f"no nodes in output:\n{out[-400:]}"
    return int(m[-1])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", default=str(SF32_EXE))
    args = ap.parse_args()
    exe = Path(args.exe)

    # 1. Mate-in-1 & Mate-in-2 sanity
    out_m1 = run_uci(exe, ["position fen 6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", "go depth 5"])
    assert "score mate 1" in out_m1 and "bestmove d1d8" in out_m1, out_m1[-300:]

    # 2. go mate 2 soundness
    out_m2 = run_uci(exe, ["position fen r2qkb1r/pp2nppp/3p4/2pNN1B1/2BnP3/3P4/PPP2PPP/R2bK2R w KQkq - 1 1", "go mate 2"])
    assert "score mate 2" in out_m2, out_m2[-300:]

    # 3. Behavioral divergence on equal-exchange / rook-and-queen tactical middlegame (FAILS on base_r15dsg!)
    fen = "r1bq1rk1/pp2bppp/2n1pn2/2pp4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9"
    n_base = extract_nodes(run_uci(BASE_EXE, [f"position fen {fen}", "go depth 9"]))
    n_cand1 = extract_nodes(run_uci(exe, [f"position fen {fen}", "go depth 9"]))
    n_cand2 = extract_nodes(run_uci(exe, [f"position fen {fen}", "go depth 9"]))

    # 4. Determinism
    assert n_cand1 == n_cand2, f"nondeterministic: {n_cand1} != {n_cand2}"
    # 5. Behavioral check (must differ from base_r15dsg)
    if n_cand1 == n_base:
        print(f"BEHAVIORAL_FAIL: {exe.name} matched base_r15dsg nodes={n_base} (expected SF32 pruning difference)")
        return 1
    print(f"SF32_TEST_PASS: exe={exe.name} base_nodes={n_base} cand_nodes={n_cand1} diff={n_cand1 - n_base:+d} (deterministic=OK, mates=OK)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
