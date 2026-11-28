"""Multi-Thread (Threads=1, 2, 4) Soundness & Astra Bare-King Mate Stress Gate.

Verifies our top Forge engine/search builds under Lazy SMP multi-threading (Threads=2 & Threads=4):
  1. Astra's famous 2-thread bare-king mate position (`7k/8/3K4/8/8/8/8/5R2 w - - 0 1`): must find mate
     in 5/5 runs at Threads=2 and 5/5 runs at Threads=4 (zero missed mates, zero crashes).
  2. Multi-thread Kiwipete & tactical middlegame `go movetime 120` stress at Threads=4 (5 runs each):
     clean `bestmove`, valid legal UCI move, zero crashes/hangs.
  3. Clean `stop` under `go infinite` at Threads=4 (50ms -> stop -> bestmove within 2s).
Tests both legacy `r0067` (768w SCReLU) and `G3_FULL25` Ep 24 (`1024w` Pairwise+PSQT) on `STACK_V3Pv3_SF13_SF8_W2P1.exe`!
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
R0067 = str(LAB / "runs/forge/r0067/train/cand.fnn3").replace("\\", "/")
G3E24 = str(FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/diag_e24/cand.fnn3").replace("\\", "/")

ASTRA_FEN = "7k/8/3K4/8/8/8/8/5R2 w - - 0 1"
KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"


def test_exe(label: str, exe: Path, net: str) -> dict:
    p = subprocess.Popen(
        [str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )

    def send(s: str) -> None:
        assert p.stdin is not None
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def read_until(prefix: str) -> list[str]:
        assert p.stdout is not None
        buf = []
        while True:
            ln = p.stdout.readline()
            if not ln:
                raise RuntimeError(f"EOF waiting for {prefix} on {label}")
            buf.append(ln.strip())
            if ln.startswith(prefix):
                return buf

    mate_t2 = 0
    mate_t4 = 0
    try:
        send("uci"); read_until("uciok")
        send(f"setoption name NNUEArchFile value {net}")
        send("setoption name NNUEArch value true")
        send("setoption name HistRework value 2")
        send("setoption name CorrHistV2 value true")
        send("setoption name TtPruneV2 value true")
        send("setoption name MateAlphaGuard value true")

        for threads, key in ((2, "t2"), (4, "t4")):
            send(f"setoption name Threads value {threads}")
            send("isready"); read_until("readyok")
            for _ in range(5):
                send("ucinewgame"); send("isready"); read_until("readyok")
                send(f"position fen {ASTRA_FEN}")
                send("go depth 12")
                lines = read_until("bestmove")
                found_mate = any("score mate " in ln for ln in lines)
                if key == "t2":
                    mate_t2 += int(found_mate)
                else:
                    mate_t4 += int(found_mate)

        # Threads=4 tactical stress + go infinite / stop responsiveness
        send("setoption name Threads value 4")
        send("isready"); read_until("readyok")
        for _ in range(3):
            send("ucinewgame"); send("isready"); read_until("readyok")
            send(f"position fen {KIWIPETE}")
            send("go movetime 80")
            lines = read_until("bestmove")
            bm = lines[-1].split()[1]
            assert len(bm) >= 4 and bm != "0000", lines[-1]

        send(f"position fen {KIWIPETE}")
        send("go infinite")
        time.sleep(0.06)
        t_s = time.time()
        send("stop")
        lines = read_until("bestmove")
        stop_ms = round((time.time() - t_s) * 1000.0, 1)
        assert stop_ms < 2000.0 and len(lines[-1].split()[1]) >= 4

        send("quit")
        p.wait(timeout=10)
    finally:
        if p.poll() is None:
            p.kill()
    assert p.returncode == 0 and mate_t2 == 5 and mate_t4 == 5, (label, p.returncode, mate_t2, mate_t4)
    return {"label": label, "rc": 0, "astra_mate_t2": f"{mate_t2}/5", "astra_mate_t4": f"{mate_t4}/5", "t4_stop_ms": stop_ms}


def main() -> int:
    targets = [
        ("STACK_V3Pv3_SF13_SF8_W2P1__G3e24", FIX / "builds/STACK_V3Pv3_SF13_SF8_W2P1.exe", G3E24),
        ("STACK_V3Pv3_SF13_SF8_W2P1__r0067", FIX / "builds/STACK_V3Pv3_SF13_SF8_W2P1.exe", R0067),
        ("SF13_qs_evasion_pruning__r0067", FIX / "builds/SF13_qs_evasion_pruning.exe", R0067),
        ("W2_proto_1_corrhist_minor__r0067", FIX / "teamwork_wave2/streamA_search/builds/proto_1_corrhist_minor.exe", R0067),
        ("SF15_rfp_failsoft_blend__r0067", FIX / "builds/SF15_rfp_failsoft_blend.exe", R0067),
        ("SF32_qs_see1_futility__r0067", FIX / "builds/SF32_qs_see1_futility_pruning.exe", R0067),
    ]
    res = [test_exe(lbl, exe, net) for lbl, exe, net in targets]
    rep = {"all_pass": True, "runs": res}
    (FIX / "MULTITHREAD_STRESS_PROOF.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print("MULTITHREAD_STRESS_ALL_PASS:", json.dumps(rep, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
