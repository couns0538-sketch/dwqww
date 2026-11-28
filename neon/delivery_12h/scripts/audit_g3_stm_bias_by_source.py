"""Opus Point 2 Audit (OPUS-2711-G3-READINGS, 22:40 PC):
Measure the exact mean side-to-move (STM) label (score_cp, wdl_score, result_wdl, mixed target WDL,
and r0067 teacher WDL) for EVERY data source in G3_FULL25's training mix using the EXACT same
compact/FQS loaders as train_v3p.py!
"""
from __future__ import annotations

import json
import math
import sys
import zlib
from pathlib import Path

import numpy as np
import torch

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
sys.path.insert(0, str(LAB / "pipeline"))
sys.path.insert(0, str(LAB / "pipeline/ft_triton"))
sys.path.insert(0, str(FIX))
import forge_train as ft  # noqa: E402
import forge_train_v3 as v3  # noqa: E402
_fk = ft.triton_kernels()
import batch_kernel_c as bc  # noqa: E402
import compact_record as cr  # noqa: E402

OUT_JSON = FIX / "G3_STM_TEMPO_BY_SOURCE_AUDIT.json"
K = float(ft.K)  # 2.25
FQS_MAGIC = b"FQS1\x00\x00\x00\x00"
FQS_DTYPE = np.dtype([
    ("packed", np.uint8, (32,)), ("stm", np.uint8), ("score16", np.int16),
    ("res8", np.int8), ("flags", np.uint8), ("weight_u8", np.uint8),
])


def wdl_from_cp(cp: np.ndarray) -> np.ndarray:
    x = np.clip(cp.astype(np.float64) * (K / 400.0), -20.0, 20.0)
    return 1.0 / (1.0 + np.exp(-x))


def cp_from_wdl(w: float) -> float:
    w = max(1e-6, min(1.0 - 1e-6, float(w)))
    return math.log(w / (1.0 - w)) * (400.0 / K)


def load_fqs(items: list[Path], skip_check: bool = True, skip_noisy: bool = False) -> np.ndarray:
    spaths: list[Path] = []
    for p in items:
        if p.is_dir():
            spaths.extend(sorted(list(p.glob("*.fqs")) + list(p.glob("*.fqs.z"))))
        else:
            spaths.append(p)
    mask_bits = (1 if skip_noisy else 0) | (2 if skip_check else 0)
    arrs = []
    for sp in spaths:
        raw = sp.read_bytes()
        if sp.name.endswith(".z"):
            raw = zlib.decompress(raw)
        assert raw[:8] == FQS_MAGIC
        a = np.frombuffer(raw, dtype=FQS_DTYPE, offset=8)
        if mask_bits:
            a = a[(a["flags"] & mask_bits) == 0]
        arrs.append(a.copy())
    return np.concatenate(arrs, axis=0)


def eval_teacher_compact(teacher, d_dict: dict, dev: torch.device, max_n: int = 200000) -> float:
    n = int(d_dict["n"])
    step = max(1, n // max_n)
    idx_all = torch.arange(0, n, step, device=dev, dtype=torch.int64)
    tot = 0.0
    cnt = 0
    bs = 8192
    with torch.no_grad():
        for i in range(0, len(idx_all), bs):
            ix = idx_all[i:i+bs]
            t_hce = torch.zeros(len(ix), device=dev)
            pred = torch.sigmoid(teacher(cr.unpack_feat(d_dict, ix), None, t_hce))
            tot += float(pred.sum().item())
            cnt += len(ix)
    return tot / max(1, cnt)


def summarize(name: str, sc: np.ndarray, res: np.ndarray, stm: np.ndarray,
              repeat: int, mix: float, teacher_mean_wdl: float | None, exact_anchor: bool = False,
              override_eff_rows: int | None = None) -> dict:
    sc_wdl = wdl_from_cp(sc)
    r_wdl = 0.5 * (res.astype(np.float64) + 1.0)
    base_wdl = r_wdl if exact_anchor else (mix * sc_wdl + (1.0 - mix) * r_wdl)
    base_mean = float(base_wdl.mean())
    if teacher_mean_wdl is not None and not exact_anchor:
        final_mean = 0.8 * base_mean + 0.2 * teacher_mean_wdl
    else:
        final_mean = base_mean
    # Note: in Forge compact records, check stm convention: 1 = White to move, 0 = Black to move OR 0 = White, 1 = Black!
    u0 = stm == 0
    u1 = stm == 1
    eff = int(override_eff_rows) if override_eff_rows is not None else int(len(sc) * repeat)
    out = {
        "source": name,
        "sampled_or_unique_rows": int(len(sc)),
        "repeat": int(repeat),
        "effective_rows": eff,
        "mean_score_stm_cp": round(float(sc.mean()), 2),
        "median_score_stm_cp": round(float(np.median(sc)), 2),
        "mean_score_wdl_stm": round(float(sc_wdl.mean()), 6),
        "mean_score_wdl_as_cp": round(cp_from_wdl(sc_wdl.mean()), 2),
        "mean_res_wdl_stm": round(float(r_wdl.mean()), 6),
        "mean_res_wdl_as_cp": round(cp_from_wdl(r_wdl.mean()), 2),
        "mean_base_target_wdl_stm": round(base_mean, 6),
        "mean_base_target_as_cp": round(cp_from_wdl(base_mean), 2),
        "mean_teacher_wdl_stm": round(float(teacher_mean_wdl), 6) if teacher_mean_wdl is not None else None,
        "mean_teacher_as_cp": round(cp_from_wdl(teacher_mean_wdl), 2) if teacher_mean_wdl is not None else None,
        "mean_final_target_wdl_stm": round(final_mean, 6),
        "mean_final_target_as_cp": round(cp_from_wdl(final_mean), 2),
        "stm_eq_0_pct": round(100.0 * float(u0.mean()), 2),
        "stm_eq_0_mean_score_cp": round(float(sc[u0].mean()), 2) if u0.any() else None,
        "stm_eq_1_mean_score_cp": round(float(sc[u1].mean()), 2) if u1.any() else None,
        "stm_eq_0_mean_res_wdl": round(float(r_wdl[u0].mean()), 5) if u0.any() else None,
        "stm_eq_1_mean_res_wdl": round(float(r_wdl[u1].mean()), 5) if u1.any() else None,
    }
    return out


def main() -> int:
    dev = torch.device("cuda")
    teacher = v3.load_model(str(LAB / "runs/forge/r0067/train/cand.pt")).to(dev).eval()
    hce_exe = str(LAB / "forge/build/hce_dump.exe")

    sources = []

    # 1. Live 25 rounds: sample 5 evenly-spaced rounds (r0178, r0184, r0190, r0196, r0202) = ~69.4M exact rows!
    sample_rounds = [178, 184, 190, 196, 202]
    all_25r_count = sum(ft._count_one(str(LAB / f"runs/forge/r{r:04d}/data/filtered.plain"), hce_exe, False, True) for r in range(178, 203))
    sc_l, res_l, stm_l, t_l = [], [], [], []
    for rnum in sample_rounds:
        p = str(LAB / f"runs/forge/r{rnum:04d}/data/filtered.plain")
        d = cr.load_compact([p], hce_exe, False, dev, with_hce=False)
        t_mean = eval_teacher_compact(teacher, d, dev, max_n=60000)
        sc_l.append(d["score16"].cpu().numpy())
        res_l.append(d["res8"].cpu().numpy())
        stm_l.append(d["stm"].cpu().numpy())
        t_l.append(t_mean)
        del d
        torch.cuda.empty_cache()
    sources.append(summarize(
        "live_25r_r0178_r0202 (5 exact rounds: r0178/184/190/196/202)",
        np.concatenate(sc_l), np.concatenate(res_l), np.concatenate(stm_l),
        repeat=1, mix=0.75, teacher_mean_wdl=float(np.mean(t_l)), exact_anchor=False,
        override_eff_rows=int(all_25r_count),
    ))

    def fqs_to_d(arr: np.ndarray) -> dict:
        return {
            "packed": torch.from_numpy(arr["packed"].copy()).to(dev),
            "stm": torch.from_numpy(arr["stm"].copy()).to(dev),
            "score16": torch.from_numpy(arr["score16"].copy()).to(dev),
            "res8": torch.from_numpy(arr["res8"].copy()).to(dev),
            "n": len(arr),
        }

    # 2. CC0 4k v2 shards (repeat=3x)
    a_cc = load_fqs([FIX / "cc0_shards_4k_v2_nodrawconf"], skip_check=True, skip_noisy=False)
    t_cc = eval_teacher_compact(teacher, fqs_to_d(a_cc), dev, max_n=200000)
    sources.append(summarize("cc0_shards_4k_v2_nodrawconf", a_cc["score16"], a_cc["res8"], a_cc["stm"], repeat=3, mix=0.75, teacher_mean_wdl=t_cc, exact_anchor=False))

    # 3. Anchor 1: dead_draws_20k_clean (repeat=25x, exact_anchor=True)
    a_d = load_fqs([FIX / "anchors/dead_draws_20k_clean.fqs.z"], skip_check=False, skip_noisy=False)
    t_d = eval_teacher_compact(teacher, fqs_to_d(a_d), dev, max_n=20000)
    sources.append(summarize("anchor_dead_draws_20k_clean", a_d["score16"], a_d["res8"], a_d["stm"], repeat=25, mix=0.75, teacher_mean_wdl=t_d, exact_anchor=True))

    # 4. Anchor 2: won_endings_syzygy_20k (repeat=25x, exact_anchor=True)
    a_w = load_fqs([FIX / "anchors/won_endings_syzygy_20k.fqs.z"], skip_check=False, skip_noisy=False)
    t_w = eval_teacher_compact(teacher, fqs_to_d(a_w), dev, max_n=20000)
    sources.append(summarize("anchor_won_endings_syzygy_20k", a_w["score16"], a_w["res8"], a_w["stm"], repeat=25, mix=0.75, teacher_mean_wdl=t_w, exact_anchor=True))

    tot_eff = sum(x["effective_rows"] for x in sources)
    mix_base = sum(x["effective_rows"] * x["mean_base_target_wdl_stm"] for x in sources) / tot_eff
    mix_final = sum(x["effective_rows"] * x["mean_final_target_wdl_stm"] for x in sources) / tot_eff
    mix_sc = sum(x["effective_rows"] * x["mean_score_stm_cp"] for x in sources) / tot_eff

    # Also check S2 M & S8 M across G3 Ep 6/24/40, G3a, G3b, G4a, G4b!
    s2_traj = {}
    for lbl, p in [
        ("G3_e6", FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/diag_e6/net_sanity_v2.txt"),
        ("G3_e24", FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/diag_e24/net_sanity_v2.txt"),
        ("G3_e40", FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/net_sanity_v2_cand.txt"),
    ]:
        if p.exists():
            s2_traj[lbl] = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if any(k in ln for k in ("S1 ", "S2 ", "S2w ", "S8 "))]
    for lbl, p in [
        ("G3a_keep_noisy", FIX / "gpu_runs/G3a_cc0_keep_noisy/eval_full.json"),
        ("G3b_skip_noisy", FIX / "gpu_runs/G3b_cc0_skip_noisy/eval_full.json"),
        ("G4a_losspow25", FIX / "gpu_runs/G4a_cc0_losspow25/eval_full.json"),
        ("G4b_obreweight", FIX / "gpu_runs/G4b_cc0_obreweight/eval_full.json"),
    ]:
        if p.exists():
            j = json.loads(p.read_text(encoding="utf-8"))
            s2_traj[lbl] = {
                "S1_startpos": j.get("S1_startpos"),
                "S1_after_1e4": j.get("S1_after_1e4"),
                "S2_white_part": j.get("S2_white_part"),
                "S2_stm_part": j.get("S2_stm_part"),
                "ols_tempo": (j.get("m4_mid20_26_ols_piece_cp") or {}).get("tempo"),
            }

    rep = {
        "total_effective_rows": tot_eff,
        "weighted_mix_mean_score_stm_cp": round(mix_sc, 2),
        "weighted_mix_mean_base_target_wdl": round(mix_base, 6),
        "weighted_mix_mean_base_target_as_cp": round(cp_from_wdl(mix_base), 2),
        "weighted_mix_mean_final_target_wdl": round(mix_final, 6),
        "weighted_mix_mean_final_target_as_cp": round(cp_from_wdl(mix_final), 2),
        "sources": sources,
        "s2_trajectory": s2_traj,
    }
    OUT_JSON.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
