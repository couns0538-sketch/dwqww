"""Chip-free pre-run declarations + Arm A vs G3-alone PGN forensic comparison.
Runs in ~2s on 1 core (zero engine calls, zero GPU, safe beside Arm B clock match).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
FQ = LAB / "neon/filter_quest"
MATCHES = FIX / "matches"

BASE_EXE = FIX / "builds/base_r15dsg.exe"
V3P_EXE = FIX / "builds/v3p_fused_v3_engine.exe"
LIVE_PGO_EXE = LAB / "runs/forge/engines/v3-r15dsg-sp-clang/forge.exe"
R0067 = LAB / "runs/forge/r0067/train/cand.fnn3"
R1_SKIP = FIX / "gpu_runs/OPUS_R1_live768_skipnoisy/cand.fnn3"
BOOK = LAB / "tools/book/UHO_Lichess_4852_v1.epd"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write_declarations() -> None:
    book_sha = sha256_file(BOOK)
    # 1. R1 Twin + 250k Decision Declaration
    r1_decl = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S PC"),
        "request_ref": "OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN Point 3 & OPUS-2811-OWNER-NONSTOP Point 5-6",
        "training_twin": {
            "script": str(FIX / "run_opus_r1_keep_twin.py"),
            "runner": "pipeline/forge_train_v3.py unchanged (exact same standalone runner as OPUS_R1_live768_skipnoisy)",
            "window": "r0178..r0202 (25 rounds, existing read-only .cache-n0c1.npz, zero writes in runs/forge/)",
            "params": {
                "hidden": 768, "epochs": 40, "lr": 0.0005, "batch_size": 8192,
                "lr_cycles": "auto", "w1_decay": 0.3, "mix": 0.75,
                "distill_net": str(LAB / "runs/forge/teachers/b_full.pt"),
                "distill_weight": 0.2, "teacher_once": True, "seed": 1,
                "keep_noisy": True,
            },
            "single_variable_diff_vs_R1_skip": "ONLY --keep-noisy added (R1-skip omitted --keep-noisy).",
            "out_net": str(FIX / "gpu_runs/OPUS_R1_live768_keepnoisy_twin/cand.fnn3"),
        },
        "r1_skip_completed_net": {
            "path": str(R1_SKIP),
            "bytes": R1_SKIP.stat().st_size,
            "sha256": sha256_file(R1_SKIP),
        },
        "matches_declared": [
            {
                "name": "OPUS_R1_skip_vs_R1_keep_1000g_250k",
                "exe_both": str(BASE_EXE),
                "exe_sha256": sha256_file(BASE_EXE),
                "cand_net": str(R1_SKIP),
                "base_net": str(FIX / "gpu_runs/OPUS_R1_live768_keepnoisy_twin/cand.fnn3"),
                "book": str(BOOK), "book_sha256": book_sha,
                "games": 1000, "nodes": 250000, "seed": 202611951, "concurrency": 8,
                "decision_rule": "95% pentanomial Elo CI lower bound > 0 => R1-skip wins (proceed to seed-2 of both + R1-skip vs r0067 at 250k and 6+0.06 conc=7); upper bound < 0 => R1-keep wins; straddling 0 => inconclusive.",
            },
            {
                "name": "OPUS_R1_skip_vs_r0067_1000g_250k",
                "exe_both": str(BASE_EXE),
                "exe_sha256": sha256_file(BASE_EXE),
                "cand_net": str(R1_SKIP),
                "base_net": str(R0067),
                "base_net_sha256": sha256_file(R0067),
                "book": str(BOOK), "book_sha256": book_sha,
                "games": 1000, "nodes": 250000, "seed": 202611952, "concurrency": 8,
                "decision_rule": "Direct fixed-node strength check of R1-skip against live best r0067 (95% pentanomial CI).",
            },
        ],
    }
    (FIX / "R1_TWIN_DECLARATION.json").write_text(json.dumps(r1_decl, indent=2), encoding="utf-8")

    # 2. Stage-2 Clean Quiet 250k Confirmations Declaration
    s2q_items = [
        ("S2Q_G4b_obreweight_vs_G3b_1000g_50k", "S2Q_G4b_obreweight_vs_G3b_600g_250k_CONFIRM",
         FQ / "stage2_runs_quiet/s2q_g4b_obreweight/cand.fnn3",
         FIX / "gpu_runs/G3b_cc0_skip_noisy/cand.fnn3", 202611960, "+14.95 [-1.47, +31.43] (LOS 96.29%)"),
        ("S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_1000g_50k",
         "S2Q_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_600g_250k_CONFIRM",
         FQ / "stage2_runs_quiet/s2q_r1b_rescore16k_2pct_oppcastle/cand.fnn3",
         FQ / "stage2_runs_quiet/s2q_f2_dedup_avg/cand.fnn3", 202611961, "+14.25 [-1.35, +29.92] (LOS 96.33%)"),
        ("S2Q_G4a_losspow25_vs_G3b_1000g_50k", "S2Q_G4a_losspow25_vs_G3b_600g_250k_CONFIRM",
         FQ / "stage2_runs_quiet/s2q_g4a_losspow25/cand.fnn3",
         FIX / "gpu_runs/G3b_cc0_skip_noisy/cand.fnn3", 202611962, "+8.34 [-7.60, +24.32] (LOS 84.74%)"),
    ]
    s2_decl = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S PC"),
        "request_ref": "OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN Point 4 & OPUS-2811-OWNER-NONSTOP Point 5-6",
        "exe_both": str(V3P_EXE),
        "exe_sha256": sha256_file(V3P_EXE),
        "book": str(BOOK),
        "book_sha256": book_sha,
        "concurrency": 8,
        "max_threads_beside_gpu": 12,
        "no_pooling_rule": "Fresh seeds; NEVER pooled with 50k filter matches. Each arm is judged solely by its own 600g @ 250k 95% pentanomial Elo CI.",
        "confirmations": [
            {
                "name": nm250,
                "origin_50k_filter": orig,
                "origin_50k_result": res50,
                "cand_net": str(cn), "cand_net_sha256": sha256_file(cn),
                "base_net": str(bn), "base_net_sha256": sha256_file(bn),
                "games": 600, "nodes": 250000, "seed": sd,
                "decision_rule": "95% pentanomial CI lower bound > 0 => confirmed Server-Day win; positive trend straddling 0 => promising lead; negative => rejected at 250k.",
            }
            for orig, nm250, cn, bn, sd, res50 in s2q_items
        ],
    }
    (FIX / "STAGE2_250K_CONFIRMATIONS_DECLARATION.json").write_text(json.dumps(s2_decl, indent=2), encoding="utf-8")
    print("WROTE R1_TWIN_DECLARATION.json & STAGE2_250K_CONFIRMATIONS_DECLARATION.json")


def parse_pgn_stats(pgn_path: Path) -> dict:
    txt = pgn_path.read_text(encoding="utf-8", errors="replace")
    games = [g.strip() for g in re.split(r"\n\n(?=\[Event )", txt) if g.strip()]
    stats = {
        "pgn": str(pgn_path), "games": len(games),
        "cand_as_white": {"W": 0, "D": 0, "L": 0},
        "cand_as_black": {"W": 0, "D": 0, "L": 0},
        "by_ply_bucket": {
            "short_le80": {"W": 0, "D": 0, "L": 0},
            "mid_81_140": {"W": 0, "D": 0, "L": 0},
            "long_gt140": {"W": 0, "D": 0, "L": 0},
        },
        "avg_plies": 0.0,
    }
    total_plies = 0
    for g in games:
        mw = re.search(r'\[White "([^"]+)"\]', g)
        mr = re.search(r'\[Result "([^"]+)"\]', g)
        if not mw or not mr:
            continue
        white = mw.group(1)
        res = mr.group(1)
        cand_is_w = (white == "cand")
        body = g.split("\n\n", 1)[1] if "\n\n" in g else ""
        # Count plies from move tokens (excluding comments, move numbers, result)
        body_nc = re.sub(r"\{[^}]*\}", " ", body)
        toks = [t for t in body_nc.split() if not re.match(r"^\d+\.+$", t) and t not in ("1-0", "0-1", "1/2-1/2", "*")]
        plies = len(toks)
        total_plies += plies
        if res == "1/2-1/2":
            out = "D"
        elif (res == "1-0" and cand_is_w) or (res == "0-1" and not cand_is_w):
            out = "W"
        else:
            out = "L"
        stats["cand_as_white" if cand_is_w else "cand_as_black"][out] += 1
        bk = "short_le80" if plies <= 80 else ("mid_81_140" if plies <= 140 else "long_gt140")
        stats["by_ply_bucket"][bk][out] += 1
    stats["avg_plies"] = round(total_plies / max(1, len(games)), 1)
    for k in ("cand_as_white", "cand_as_black"):
        d = stats[k]
        d["net"] = d["W"] - d["L"]
    for bk, d in stats["by_ply_bucket"].items():
        d["net"] = d["W"] - d["L"]
    return stats


def main() -> int:
    write_declarations()
    arma_pgn = MATCHES / "OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006/games_20261128_024459.pgn"
    g3_pgns = sorted((MATCHES / "G3_FULL25_PGO_vs_live_r0067_2000g_6p006").glob("games_*.pgn"))
    audit = {
        "written": time.strftime("%Y-%m-%d %H:%M:%S PC"),
        "ARMA_bundleG3_vs_liveR0067": parse_pgn_stats(arma_pgn),
        "G3alone_vs_liveR0067": parse_pgn_stats(g3_pgns[-1]) if g3_pgns else None,
    }
    out = FIX / "OWNER_BUNDLE_ARMA_PGN_FORENSICS.json"
    out.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
