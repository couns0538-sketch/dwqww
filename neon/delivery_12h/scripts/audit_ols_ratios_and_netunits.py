"""Compile scale-free OLS material ratios (Q/P, R/P, B/P, N/P) and net-unit-normalized cp
across all key trained Forge nets (per OPUS-2811-OLS-CAUTION, 01:04 PC).

Reads strictly existing eval_full*.json / STAGE2_QUIET_GPU_SUMMARY.json / SERVERDAY_ARCH_SUITE_SUMMARY.json
files — zero engine invocations, zero GPU/CPU contention!
"""
from __future__ import annotations

import json
from pathlib import Path

LAB = Path(r"C:\nnue-lab")
FIX = LAB / "neon/forge_fixes"
FQ = LAB / "neon/filter_quest"


def extract_row(label: str, ef: dict | None, extra: dict | None = None) -> dict | None:
    if not ef:
        return None
    ols = ef.get("m4_mid20_26_ols_piece_cp") or ef.get("ols_piece_values") or ef.get("ols") or {}
    s6 = ef.get("S6_startpos_minus") or {}

    def g(d: dict, *ks):
        for k in ks:
            if k in d and d[k] is not None:
                return float(d[k])
        return None

    p = g(ols, "P", "pawn")
    n = g(ols, "N", "knight")
    b = g(ols, "B", "bishop")
    r = g(ols, "R", "rook")
    q = g(ols, "Q", "queen")
    if not p or abs(p) < 1e-6 or q is None or r is None or b is None or n is None:
        return None
    # Exact net_sanity.py unit u = (S6_Q + S6_R + S6_B + S6_N) / 20 (fallback to OLS if S6 missing)
    s6_vals = [g(s6, k) for k in ("Q", "R", "B", "N")]
    if all(v is not None for v in s6_vals):
        u = sum(s6_vals) / 20.0
    else:
        u = (q + r + b + n) / 20.0
    s6_q = g(s6, "Q")
    s6_p = g(s6, "P")
    row = {
        "net": label,
        "m4_wdl_mse": ef.get("m4_wdl_mse"),
        "raw_ols": {"P": round(p, 2), "N": round(n, 2), "B": round(b, 2), "R": round(r, 2), "Q": round(q, 2)},
        "ratios_vs_P": {
            "N_P": round(n / p, 3),
            "B_P": round(b / p, 3),
            "R_P": round(r / p, 3),
            "Q_P": round(q / p, 3),
        },
        "unit_u": round(u, 2),
        "s6_Q_unit_cp": round(100.0 * s6_q / u, 1) if (s6_q is not None and u > 0) else None,
        "s6_Q_over_P": round(s6_q / s6_p, 2) if (s6_q is not None and s6_p and abs(s6_p) > 1e-6) else None,
        "net_unit_cp": {
            "P_cp": round(100.0 * p / u, 1) if u > 0 else None,
            "N_cp": round(100.0 * n / u, 1) if u > 0 else None,
            "B_cp": round(100.0 * b / u, 1) if u > 0 else None,
            "R_cp": round(100.0 * r / u, 1) if u > 0 else None,
            "Q_cp": round(100.0 * q / u, 1) if u > 0 else None,
        },
    }
    if extra:
        row.update(extra)
    return row


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    rows = []
    # Core baselines & G2/G3
    candidates = [
        ("r0067 (live 768w, keep_noisy)", FIX / "baseline_r0067_scorecard.json"),
        ("r0202 (loop 768w, keep_noisy)", FIX / "r0202_scorecard.json"),
        ("G2_1024p (12r V3P, keep_noisy)", FIX / "gpu_runs/G2_v3p_1024_pairwise_psqt/eval_full.json"),
        ("G3_FULL25 (25r V3P, keep_noisy)", FIX / "gpu_runs/G3_FULL25_v3p_1024_cc0_anchored/eval_full_cand.json"),
        ("G3a_cc0_keep_noisy (scratch V3P)", FIX / "gpu_runs/G3a_cc0_keep_noisy/eval_full.json"),
        ("G3b_cc0_skip_noisy (scratch V3P)", FIX / "gpu_runs/G3b_cc0_skip_noisy/eval_full.json"),
        ("G3a_distill_keep_noisy (r0067 w=0.2)", FIX / "gpu_runs/G3a_distill_keep_noisy/eval_full.json"),
        ("G3b_distill_skip_noisy (r0067 w=0.2)", FIX / "gpu_runs/G3b_distill_skip_noisy/eval_full.json"),
        ("OPUS_R1_live768_keepnoisy_twin (25r)", FIX / "gpu_runs/OPUS_R1_live768_keepnoisy_twin/eval_full.json"),
        ("OPUS_R1_live768_skipnoisy (25r)", FIX / "gpu_runs/OPUS_R1_live768_skipnoisy/eval_full.json"),
    ]
    for lbl, p in candidates:
        d = load_json(p)
        if d:
            r = extract_row(lbl, d)
            if r:
                rows.append(r)

    # All 9 Clean Quiet Stage-2 arms
    for ef_p in sorted((FQ / "stage2_runs_quiet").glob("*/eval_full.json")):
        d = load_json(ef_p)
        r = extract_row(f"S2Q/{ef_p.parent.name}", d)
        if r:
            rows.append(r)

    # Server-Day Arch Suite (768p/kb8, 1536p/kb8, 1024p/kb16)
    for ef_p in sorted((FIX / "gpu_runs").glob("G5*/eval_full.json")):
        d = load_json(ef_p)
        r = extract_row(ef_p.parent.name, d)
        if r:
            rows.append(r)

    out_json = FIX / "OLS_SCALEFREE_COMPARISON.json"
    out_json.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")

    lines = [
        "# Scale-Free OLS Material Ratios & Net-Unit CP Comparison (OPUS-2811-OLS-CAUTION)",
        "",
        "> Strictly diagnostic (never a replacement for fastchess games). Ratios `Q/P, R/P, B/P, N/P` are invariant to each net's output scale; `unit u = (Q+R+B+N)/20` matches `net_sanity.py`.",
        "",
        "| Net | M4 WDL MSE | `N/P` | `B/P` | `R/P` | `Q/P` | `u` | `P/N/B/R/Q` (net-unit cp) |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        rt = r["ratios_vs_P"]
        nc = r["net_unit_cp"]
        mse = f"{r['m4_wdl_mse']:.5f}" if isinstance(r["m4_wdl_mse"], (int, float)) else "-"
        lines.append(
            f"| `{r['net']}` | {mse} | {rt['N_P']:.2f} | {rt['B_P']:.2f} | {rt['R_P']:.2f} | **{rt['Q_P']:.2f}** | "
            f"{r['unit_u']:.1f} | `{nc['P_cp']}/{nc['N_cp']}/{nc['B_cp']}/{nc['R_cp']}/{nc['Q_cp']}` |"
        )
    out_md = FIX / "OLS_SCALEFREE_COMPARISON.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {out_md} ({len(rows)} nets)")
    for ln in lines[4:]:
        print(ln)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
