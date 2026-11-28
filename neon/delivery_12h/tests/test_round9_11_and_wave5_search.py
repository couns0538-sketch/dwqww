r"""Fail-before / pass-after pytest suite for Round 9-11 & Wave 5 search packets.

Covers:
  - SF28_qs_evasion_tight_and_standpat_ttpv
  - SF29_lmr_pv_ext_and_eval_diff
  - SF30_probcut_tt_and_corrhist_promo_fix
  - SF31_singular_triple_ext_and_neg_ext
  - SF33_qs_overhaul_SF13_plus_SF32
  - proto_9_corr_complexity_rfp_lmr (CorrComplexityRefine)
  - proto_10_cutnode_history_and_cap_lmr (CutNodeHistRefine)

Run modes:
  - FORGE_TEST_EXE=C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe  -> RC=1 (test_02..test_08 FAIL)
  - FORGE_TEST_EXE=""                                                     -> RC=0 (9/9 PASS)

Invocation (CPU-only):
  - Primary venv (no pytest installed; use unittest discover, not bare .py path):
    C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v
  - Optional CPU-only pytest (with GPU env vars blanked):
    C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
"""
from __future__ import annotations

import functools
import os
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

LAB = Path(r"C:\nnue-lab")
sys.path.insert(0, str(LAB / "pipeline"))
sys.path.insert(0, str(LAB / "neon/forge_fixes"))
import forge_parse  # noqa: E402
import forge_v3p  # noqa: E402

R15DSG_DIR = LAB / "forge/r15dsg"
FIX_DIR = LAB / "neon/forge_fixes"
STREAM_A = Path(__file__).resolve().parent.parent
BASE_EXE = FIX_DIR / "builds/base_r15dsg.exe"
R0067_NET = str(LAB / "runs/forge/r0067/train/cand.fnn3").replace("\\", "/")
VAL_PLAIN = LAB / "runs/forge/val/val.plain"

PATCHES = {
    "sf28": FIX_DIR / "patches/SF28_qs_evasion_tight_and_standpat_ttpv.patch",
    "sf29": FIX_DIR / "patches/SF29_lmr_pv_ext_and_eval_diff.patch",
    "sf30": FIX_DIR / "patches/SF30_probcut_tt_and_corrhist_promo_fix.patch",
    "sf31": FIX_DIR / "patches/SF31_singular_triple_ext_and_neg_ext.patch",
    "sf33": FIX_DIR / "patches/SF33_qs_overhaul_SF13_plus_SF32.patch",
    "proto_9": STREAM_A / "patches/proto_9_corr_complexity_rfp_lmr.patch",
    "proto_10": STREAM_A / "patches/proto_10_cutnode_history_and_cap_lmr.patch",
}

DEFAULT_EXES = {
    "sf28": FIX_DIR / "builds/SF28_qs_evasion_tight_and_standpat_ttpv.exe",
    "sf29": FIX_DIR / "builds/SF29_lmr_pv_ext_and_eval_diff.exe",
    "sf30": FIX_DIR / "builds/SF30_probcut_tt_and_corrhist_promo_fix.exe",
    "sf31": FIX_DIR / "builds/SF31_singular_triple_ext_and_neg_ext.exe",
    "sf33": FIX_DIR / "builds/SF33_qs_overhaul_SF13_plus_SF32.exe",
    "proto_9": STREAM_A / "builds/proto_9_corr_complexity_rfp_lmr.exe",
    "proto_10": STREAM_A / "builds/proto_10_cutnode_history_and_cap_lmr.exe",
}

R0067_OPTIONS = (
    f"setoption name NNUEArchFile value {R0067_NET}",
    "setoption name NNUEArch value true",
)

B4_OPTIONS = (
    *R0067_OPTIONS,
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
)

FULL_OPTIONS = (
    "setoption name MateAlphaGuard value true",
    "setoption name LmrQuietBase value 132",
    "setoption name LmrQuietDivisor value 176",
    "setoption name LmrNoisyBase value 25",
    "setoption name LmrNoisyDivisor value 336",
    "setoption name LmrHistoryDivisor value 6721",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 13",
    "setoption name HistoryPruneMultiplier value 1945",
    "setoption name HistoryBonusQuadratic value 49",
    "setoption name HistoryBonusLinear value 90",
    "setoption name HistoryBonusMax value 2429",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 5",
    "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name DrawJitter value 2",
    "setoption name NullMoveMinDepth value 2",
    "setoption name NullMoveDepthDivisor value 4",
    "setoption name NullMoveEvalDivisor value 184",
    "setoption name RfpDepth value 6",
    "setoption name RfpMargin value 84",
    "setoption name RfpImproving value 37",
    "setoption name RazorDepth value 3",
    "setoption name RazorBase value 182",
    "setoption name RazorMultiplier value 379",
    "setoption name FutilityDepth value 8",
    "setoption name FutilityBase value 12",
    "setoption name FutilityMultiplier value 59",
    "setoption name HistoryPruneDepth value 2",
    "setoption name SeeQuietMultiplier value 15",
    "setoption name SeeNoisyMultiplier value 83",
    "setoption name SingularMargin value 3",
    "setoption name ProbcutDepth value 7",
    "setoption name ProbcutMargin value 168",
    "setoption name QsFutilityMargin value 123",
    "setoption name AspirationDelta value 16",
    "setoption name CheckExtensionDepth value 3",
    "setoption name LmrCutoffThreshold value 9",
    "setoption name MaterialCorrectionWeight value 48",
    "setoption name CaptureFutilityBase value 45",
    "setoption name FailLowContinuationBonus value 41",
    "setoption name EvalSwingMult value 15",
    *R0067_OPTIONS,
)

BENCH_FENS = {
    "startpos_d9": ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 9),
    "kiwipete_d8": ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 8),
    "kiwipete_d10": ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 10),
    "bench3_d9": ("r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10", 9),
    "bench5_d9": ("r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8", 9),
    "bench8_d9": ("r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", 9),
    "tactical_d9": ("r1b1k2r/ppppnppp/2n2q2/2b5/2B1P3/2P2N2/PP3PPP/RNBQ1RK1 w kq - 0 7", 9),
    "sf32_eq_d9": ("r1bq1rk1/pp2bppp/2n1pn2/2pp4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9", 9),
}


def resolve_exe(default_path: Path) -> Path:
    override = os.environ.get("FORGE_TEST_EXE", "").strip()
    return Path(override) if override else default_path


def run_uci_interactive(exe: Path, steps: list[tuple[str, str | None]], timeout: float = 120.0) -> list[str]:
    all_lines: list[str] = []
    with subprocess.Popen(
        [str(exe)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    ) as p:
        assert p.stdin is not None and p.stdout is not None
        for cmd, wait_tok in steps:
            p.stdin.write(cmd + "\n")
            p.stdin.flush()
            if wait_tok is not None:
                while True:
                    line = p.stdout.readline()
                    if not line:
                        err = p.stderr.read() if p.stderr else ""
                        raise RuntimeError(f"{exe.name} closed while waiting for {wait_tok!r}: {err}")
                    s = line.strip()
                    all_lines.append(s)
                    if s.startswith(wait_tok):
                        break
        rc = p.wait(timeout=timeout)
        if rc != 0:
            err = p.stderr.read() if p.stderr else ""
            raise RuntimeError(f"{exe.name} exited {rc}: {err}")
    return all_lines


def get_uci_text(exe: Path) -> str:
    return "\n".join(run_uci_interactive(exe, [("uci", "uciok"), ("quit", None)]))


@functools.lru_cache(maxsize=64)
def query_perft_and_bench(exe: Path, opts: tuple[str, ...]) -> tuple[int, int, int]:
    steps: list[tuple[str, str | None]] = [("uci", "uciok")]
    for o in opts:
        steps.append((o, None))
    steps.extend([
        ("setoption name Threads value 1", None),
        ("setoption name Hash value 16", None),
        ("setoption name OwnBook value false", None),
        ("isready", "readyok"),
        ("position startpos", None),
        ("go perft 5", "nodes "),
        ("bench 11", "info string bench depth 11 "),
        ("bench 13", "info string bench depth 13 "),
        ("quit", None),
    ])
    lines = run_uci_interactive(exe, steps)
    p5 = b11 = b13 = None
    for line in lines:
        if line.startswith("nodes "):
            p5 = int(line.split()[1])
        elif line.startswith("info string bench depth 11 "):
            t = line.split()
            b11 = int(t[t.index("nodes") + 1])
        elif line.startswith("info string bench depth 13 "):
            t = line.split()
            b13 = int(t[t.index("nodes") + 1])
    assert p5 is not None and b11 is not None and b13 is not None, f"Missing perft/bench output in {exe.name}"
    return p5, b11, b13


@functools.lru_cache(maxsize=256)
def query_pos_search(exe: Path, opts: tuple[str, ...], fen: str, depth: int) -> tuple[str, int | None, int]:
    steps: list[tuple[str, str | None]] = [("uci", "uciok")]
    for o in opts:
        steps.append((o, None))
    steps.extend([
        ("setoption name Threads value 1", None),
        ("setoption name Hash value 16", None),
        ("setoption name OwnBook value false", None),
        ("ucinewgame", None),
        ("isready", "readyok"),
        (f"position fen {fen}", None),
        (f"go depth {depth}", "bestmove"),
        ("quit", None),
    ])
    lines = run_uci_interactive(exe, steps)
    best = cp = nodes = None
    for line in lines:
        if line.startswith(f"info depth {depth} "):
            t = line.split()
            if "nodes" in t:
                nodes = int(t[t.index("nodes") + 1])
            if "score" in t and "cp" in t:
                cp = int(t[t.index("cp") + 1])
        elif line.startswith("bestmove "):
            best = line.split()[1]
    assert best is not None and nodes is not None, f"Missing search output in {exe.name}"
    return best, cp, nodes


def load_200_balanced_fens(net: forge_v3p.NetP) -> list[str]:
    all_fens: list[str] = []
    with VAL_PLAIN.open("r", encoding="ascii", errors="replace") as fh:
        for line in fh:
            if line.startswith("fen "):
                all_fens.append(line[4:].strip())
    selected: list[str] = []
    seen: set[str] = set()
    kb_counts = {kb: 0 for kb in range(net.king_buckets)}
    ob_counts = {ob: 0 for ob in range(net.output_buckets)}
    stride = max(1, len(all_fens) // 2000)
    for f in all_fens[::stride]:
        codes = np.frombuffer(forge_parse.fen_codes(f.split()[0]), np.uint8)
        white = f.split()[1] == "w"
        ksq = int(np.nonzero(codes == (6 if white else 12))[0][0])
        kb = int(net.king_map[ksq if white else (ksq ^ 56)])
        ob = int(net.output_map[min(int(np.count_nonzero(codes)), 32)])
        if kb_counts[kb] < 5 and f not in seen:
            selected.append(f)
            seen.add(f)
            kb_counts[kb] += 1
            ob_counts[ob] += 1
    for f in all_fens[::stride]:
        if len(selected) >= 200:
            break
        if f in seen:
            continue
        codes = np.frombuffer(forge_parse.fen_codes(f.split()[0]), np.uint8)
        ob = int(net.output_map[min(int(np.count_nonzero(codes)), 32)])
        if ob_counts[ob] < 25:
            selected.append(f)
            seen.add(f)
            ob_counts[ob] += 1
    assert len(selected) == 200
    return selected


class TestRound911AndWave5Search(unittest.TestCase):
    def test_01_all_patches_apply_cleanly(self) -> None:
        for name, patch_path in PATCHES.items():
            self.assertTrue(patch_path.exists(), f"Missing patch {name}: {patch_path}")
            chk = subprocess.run(
                ["git", "-C", str(R15DSG_DIR), "apply", "--check", str(patch_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(chk.returncode, 0, f"{name} git apply --check failed: {chk.stderr}")

    def test_02_sf28_behavioral_and_bench(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["sf28"])
        b4_keys = ("startpos_d9", "kiwipete_d8", "kiwipete_d10", "bench3_d9", "bench5_d9", "tactical_d9", "sf32_eq_d9")
        for k in b4_keys:
            fen, d = BENCH_FENS[k]
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"SF28 B4 must diverge from base on {k}",
            )
        for k, (fen, d) in BENCH_FENS.items():
            self.assertNotEqual(
                query_pos_search(exe, FULL_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, FULL_OPTIONS, fen, d),
                f"SF28 FULL must diverge from base on {k}",
            )
        _, _, base_b13 = query_perft_and_bench(BASE_EXE, B4_OPTIONS)
        _, _, cand_b13 = query_perft_and_bench(exe, B4_OPTIONS)
        self.assertNotEqual(cand_b13, base_b13, "SF28 B4 bench 13 must diverge from base")
        delta = (cand_b13 - base_b13) / base_b13
        self.assertGreaterEqual(delta, -0.15)
        self.assertLessEqual(delta, -0.05)

    def test_03_sf29_behavioral_and_bench(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["sf29"])
        for k, (fen, d) in BENCH_FENS.items():
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"SF29 B4 must diverge from base on {k}",
            )
        b3_best, _, _ = query_pos_search(exe, B4_OPTIONS, *BENCH_FENS["bench3_d9"])
        self.assertNotEqual(b3_best, "c4d5", "SF29 bench3_d9 B4 bestmove must flip from c4d5")
        sf32_best, _, _ = query_pos_search(exe, B4_OPTIONS, *BENCH_FENS["sf32_eq_d9"])
        self.assertNotEqual(sf32_best, "d4c5", "SF29 sf32_eq_d9 B4 bestmove must flip from d4c5")
        for opts in (B4_OPTIONS, FULL_OPTIONS):
            _, _, base_b13 = query_perft_and_bench(BASE_EXE, opts)
            _, _, cand_b13 = query_perft_and_bench(exe, opts)
            self.assertNotEqual(cand_b13, base_b13)

    def test_04_sf30_behavioral_and_bench(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["sf30"])
        b4_keys = ("startpos_d9", "kiwipete_d8", "kiwipete_d10", "bench3_d9", "bench8_d9", "tactical_d9", "sf32_eq_d9")
        for k in b4_keys:
            fen, d = BENCH_FENS[k]
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"SF30 B4 must diverge from base on {k}",
            )
        kp10_best, _, _ = query_pos_search(exe, B4_OPTIONS, *BENCH_FENS["kiwipete_d10"])
        self.assertNotEqual(kp10_best, "e2a6", "SF30 kiwipete_d10 B4 bestmove must flip from e2a6")
        _, _, base_full_13 = query_perft_and_bench(BASE_EXE, FULL_OPTIONS)
        _, _, cand_full_13 = query_perft_and_bench(exe, FULL_OPTIONS)
        self.assertNotEqual(cand_full_13, base_full_13, "SF30 FULL bench 13 must diverge from base")

    def test_05_sf31_behavioral_and_bench(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["sf31"])
        for k in ("kiwipete_d10", "bench3_d9", "bench5_d9", "tactical_d9"):
            fen, d = BENCH_FENS[k]
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"SF31 B4 must diverge from base on {k}",
            )
        for k in ("kiwipete_d10", "tactical_d9"):
            fen, d = BENCH_FENS[k]
            self.assertNotEqual(
                query_pos_search(exe, FULL_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, FULL_OPTIONS, fen, d),
                f"SF31 FULL must diverge from base on {k}",
            )
        for opts in (B4_OPTIONS, FULL_OPTIONS):
            _, _, base_b13 = query_perft_and_bench(BASE_EXE, opts)
            _, _, cand_b13 = query_perft_and_bench(exe, opts)
            self.assertNotEqual(cand_b13, base_b13)

    def test_06_sf33_behavioral_and_bench(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["sf33"])
        for k, (fen, d) in BENCH_FENS.items():
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"SF33 B4 must diverge from base on {k}",
            )
        b5_best, _, _ = query_pos_search(exe, B4_OPTIONS, *BENCH_FENS["bench5_d9"])
        self.assertNotEqual(b5_best, "c4d5", "SF33 bench5_d9 B4 bestmove must flip from c4d5")
        _, _, base_b13 = query_perft_and_bench(BASE_EXE, B4_OPTIONS)
        _, _, cand_b13 = query_perft_and_bench(exe, B4_OPTIONS)
        self.assertNotEqual(cand_b13, base_b13)

    def test_07_proto_9_uci_ablation_and_behavioral(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["proto_9"])
        uci_out = get_uci_text(exe)
        self.assertIn("option name CorrComplexityRefine type spin default 1 min 0 max 1", uci_out)

        for label, opts in (("B4+r0067", B4_OPTIONS), ("FULL+r0067", FULL_OPTIONS)):
            _, base_11, base_13 = query_perft_and_bench(BASE_EXE, opts)
            _, off_11, off_13 = query_perft_and_bench(exe, (*opts, "setoption name CorrComplexityRefine value 0"))
            self.assertEqual((off_11, off_13), (base_11, base_13), f"proto_9 =0 must be bit-exact on {label}")

            _, _, on_13 = query_perft_and_bench(exe, opts)
            self.assertNotEqual(on_13, base_13, f"proto_9 =1 must diverge on {label} bench 13")

        for k, (fen, d) in BENCH_FENS.items():
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"proto_9 B4 must diverge from base on {k}",
            )
            self.assertNotEqual(
                query_pos_search(exe, FULL_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, FULL_OPTIONS, fen, d),
                f"proto_9 FULL must diverge from base on {k}",
            )

    def test_08_proto_10_uci_ablation_and_behavioral(self) -> None:
        exe = resolve_exe(DEFAULT_EXES["proto_10"])
        uci_out = get_uci_text(exe)
        self.assertIn("option name CutNodeHistRefine type spin default 1 min 0 max 1", uci_out)

        for label, opts in (("B4+r0067", B4_OPTIONS), ("FULL+r0067", FULL_OPTIONS)):
            _, base_11, base_13 = query_perft_and_bench(BASE_EXE, opts)
            _, off_11, off_13 = query_perft_and_bench(exe, (*opts, "setoption name CutNodeHistRefine value 0"))
            self.assertEqual((off_11, off_13), (base_11, base_13), f"proto_10 =0 must be bit-exact on {label}")

            _, _, on_13 = query_perft_and_bench(exe, opts)
            self.assertNotEqual(on_13, base_13, f"proto_10 =1 must diverge on {label} bench 13")

        for k in ("kiwipete_d8", "kiwipete_d10", "bench3_d9", "bench5_d9", "tactical_d9"):
            fen, d = BENCH_FENS[k]
            self.assertNotEqual(
                query_pos_search(exe, B4_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, B4_OPTIONS, fen, d),
                f"proto_10 B4 must diverge from base on {k}",
            )
        for k, (fen, d) in BENCH_FENS.items():
            self.assertNotEqual(
                query_pos_search(exe, FULL_OPTIONS, fen, d),
                query_pos_search(BASE_EXE, FULL_OPTIONS, fen, d),
                f"proto_10 FULL must diverge from base on {k}",
            )

    def test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity(self) -> None:
        unique_exes = list(dict.fromkeys(resolve_exe(p) for p in DEFAULT_EXES.values()))
        net_clean = forge_v3p.read_net(R0067_NET)
        net_bug = forge_v3p.read_net(R0067_NET)
        net_bug.king_map[2] = (net_bug.king_map[2] + 1) % net_bug.king_buckets
        fens = load_200_balanced_fens(net_clean)

        for exe in unique_exes:
            for label, opts in (("Default", ()), ("B4+r0067", B4_OPTIONS), ("FULL+r0067", FULL_OPTIONS)):
                p5, _, _ = query_perft_and_bench(exe, opts)
                self.assertEqual(p5, 4865609, f"{exe.name} {label} perft 5 mismatch")

            # Startpos eval == 87, mate-in-1, go mate 2, Qh4+ check evasion
            lines = run_uci_interactive(
                exe,
                [
                    ("uci", "uciok"),
                    *((o, None) for o in R0067_OPTIONS),
                    ("setoption name Threads value 1", None),
                    ("setoption name Hash value 16", None),
                    ("setoption name OwnBook value false", None),
                    ("isready", "readyok"),
                    ("position startpos", None),
                    ("eval", "info string eval "),
                    ("ucinewgame", None),
                    ("position fen 6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", None),
                    ("go depth 5", "bestmove"),
                    ("ucinewgame", None),
                    ("position fen r2qkb1r/pp2nppp/3p4/2pNN1B1/2BnP3/3P4/PPP2PPP/R2bK2R w KQkq - 1 1", None),
                    ("go mate 2", "bestmove"),
                    ("ucinewgame", None),
                    ("position fen rnb1kbnr/pppp1ppp/8/4p3/5P1q/8/PPPPP1PP/RNBQKBNR w KQkq - 1 3", None),
                    ("go depth 6", "bestmove"),
                    ("quit", None),
                ],
            )
            joined = "\n".join(lines)
            eval_line = [l for l in lines if l.startswith("info string eval ")][-1]
            toks = eval_line.split()
            self.assertEqual(int(toks[toks.index("total") + 1]), 87, f"{exe.name} startpos eval != 87")
            self.assertIn("score mate 1", joined)
            self.assertIn("bestmove d1d8", joined)
            self.assertIn("score mate 2", joined)
            self.assertIn("bestmove g2g3", joined)
            self.assertNotIn("score mate -1", joined)

            # 200-FEN V3 parity across 8/8 KB & 8/8 OB + planted fault detection
            with subprocess.Popen(
                [str(exe)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                bufsize=1,
            ) as p:
                assert p.stdin is not None and p.stdout is not None

                def send(s: str) -> None:
                    p.stdin.write(s + "\n")
                    p.stdin.flush()

                def wait_for(tok: str) -> list[str]:
                    out = []
                    while True:
                        line = p.stdout.readline()
                        if not line:
                            raise RuntimeError(f"{exe.name} closed waiting for {tok!r}")
                        s = line.strip()
                        out.append(s)
                        if s.startswith(tok):
                            return out

                send("uci"); wait_for("uciok")
                send(f"setoption name NNUEArchFile value {R0067_NET}")
                send("setoption name NNUEArch value true")
                send("isready"); wait_for("readyok")
                bad_clean = bad_bug = 0
                kb_seen: set[int] = set()
                ob_seen: set[int] = set()
                for f in fens:
                    codes = np.frombuffer(forge_parse.fen_codes(f.split()[0]), np.uint8)
                    white = f.split()[1] == "w"
                    want_clean = forge_v3p.reference_eval(net_clean, codes, white)
                    want_bug = forge_v3p.reference_eval(net_bug, codes, white)
                    send("position fen " + f)
                    send("eval")
                    got = None
                    for line in wait_for("info string eval"):
                        if line.startswith("info string eval"):
                            t = line.split()
                            got = int(t[t.index("total") + 1])
                    ksq = int(np.nonzero(codes == (6 if white else 12))[0][0])
                    kb_seen.add(int(net_clean.king_map[ksq if white else ksq ^ 56]))
                    ob_seen.add(int(net_clean.output_map[min(int(np.count_nonzero(codes)), 32)]))
                    if got != want_clean:
                        bad_clean += 1
                    if got != want_bug:
                        bad_bug += 1
                send("quit")
                p.wait(timeout=15)

            self.assertEqual(bad_clean, 0, f"{exe.name} v3_parity failed {bad_clean}/200")
            self.assertGreater(bad_bug, 0, f"{exe.name} planted king_map fault was not caught")
            self.assertEqual(len(kb_seen), 8)
            self.assertEqual(len(ob_seen), 8)
