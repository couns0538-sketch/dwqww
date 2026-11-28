"""Fail-before / pass-after behavioral, mate-safety & determinism tests for SF15 and SF27."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3").replace("\\", "/")
BASE_EXE = FIX / "builds/base_r15dsg.exe"
SF15_EXE = FIX / "builds/SF15_rfp_failsoft_blend.exe"
SF27_EXE = FIX / "builds/SF27_goodcap_caphist_see_threshold.exe"


def run_uci(exe: Path, cmds: list[str]) -> str:
    p = subprocess.Popen(
        [str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    out: list[str] = []

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
            out.append(ln)
            if ln.startswith(prefix):
                return

    try:
        send("uci"); read_until("uciok")
        send(f"setoption name NNUEArchFile value {R0067}")
        send("setoption name NNUEArch value true")
        send("setoption name HistRework value 2")
        send("setoption name CorrHistV2 value true")
        send("setoption name TtPruneV2 value true")
        send("isready"); read_until("readyok")
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
    return "".join(out)


def last_nodes(out: str) -> int:
    m = re.findall(r"info .*?nodes (\d+)", out)
    assert m
    return int(m[-1])


def check_one(label: str, exe: Path, fen: str, depth: int) -> int:
    out_m1 = run_uci(exe, ["position fen 6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", "go depth 5"])
    assert "score mate 1" in out_m1 and "bestmove d1d8" in out_m1
    out_m2 = run_uci(exe, ["position fen r2qkb1r/pp2nppp/3p4/2pNN1B1/2BnP3/3P4/PPP2PPP/R2bK2R w KQkq - 1 1", "go mate 2"])
    assert "score mate 2" in out_m2
    nb = last_nodes(run_uci(BASE_EXE, [f"position fen {fen}", f"go depth {depth}"]))
    nc1 = last_nodes(run_uci(exe, [f"position fen {fen}", f"go depth {depth}"]))
    nc2 = last_nodes(run_uci(exe, [f"position fen {fen}", f"go depth {depth}"]))
    assert nc1 == nc2, f"{label} nondeterministic: {nc1} != {nc2}"
    if nc1 == nb:
        print(f"{label}_FAIL_ON_{exe.name}: nodes={nc1} == base={nb}")
        return 1
    print(f"{label}_PASS: exe={exe.name} base={nb} cand={nc1} diff={nc1 - nb:+d}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["all", "sf15", "sf27"], default="all")
    ap.add_argument("--exe", default="")
    args = ap.parse_args()
    rc = 0
    if args.only in ("all", "sf15"):
        e = Path(args.exe) if args.exe else SF15_EXE
        rc |= check_one("SF15", e, "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 9)
    if args.only in ("all", "sf27"):
        e = Path(args.exe) if args.exe else SF27_EXE
        rc |= check_one("SF27", e, "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 10)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
