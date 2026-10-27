# S44 [Sol leftover] Elo-vs-epochs fit with the new gate points — DONE (advice only)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 26 (inventory: S44, spec line 231). Branch `opus-sol-S44` = `d4f4312` +
`0d99f02` cherry-picked + this job. Tool/analysis job, no engine change (`[skip ci]`). Deliverable:
**`forge_sol_S44_elo_vs_epochs_20261027.md`** + the script `forge_sol_S44_elo_vs_epochs.py`.

**Answer:** more data at e48 is the better next PC run.
- e64 on the same data: +0.3 Elo (95% +0.1 .. +0.9); e96: +0.6 (+0.25 .. +2.1).
- e48 with 1.5× the data: +4.9 (+2.0 .. +8.0); with 2×: +8.5 (+3.4 .. +13.7). Conc-5 Elo scale.
- At ×2 compute, doubling the data is worth about 14× doubling the epochs.

## Acceptance
| line (spec + resume rework) | result | evidence |
|---|---|---|
| every net gate as an unpooled effect-size point | **PASS**. 23 net gates (the spec's G102, G100, G100r, G119, G120, G104 plus G120c, G104c and every net gate since: G90, G95, G98, G103, G105-G112, G122-G125). No pooling; confirm gates are separate points. G101 (a speed patch, SPRT [−3,1]) is not a net gate | `results/s44_points.csv`, deliverable table |
| data size from the settings dumps, not run names | **PASS**. The `train_positions` of each run from its log's settings line (S30 `train_where`, log:6) | `results/s44_points.csv` |
| every point cites its gate row | **PASS**. Gates in the 2026-10-25 13:35 snapshot cite their CSV/MD/HTML row lines in `gate_results_20261025_1335/`. Gates played later (or still running then: G120c had 360 games) cite `LATEST_GATE_FACTS_20261026.md` lines and the sha256 of the PC's final RESULT.md | deliverable table |
| e64/e96 on the same data vs more data at e48, gain as a range | **PASS**: the "Answer" table in the deliverable, three Elo scales (conc 5, conc 7, AL1 conc 8) | deliverable |
| resume rework: add G120/G120c and bias-corrected Elo; keep conc 5 and conc 7/8 apart | **PASS**. Each gate's own stopping rule is simulated (fastchess exact GSPRT, cap, net early stop). The Whitehead bias-adjusted Elo goes into the fits, and the verdict-conditional bias (winner's curse) is reported. Groups `h256_e12 conc5`, `h256_e12 conc7` and `AL1 conc8` are fitted separately | deliverable, `logs/step3_full_run.log` |
| external scope: G120c full results; actual bias inputs | **DONE**. G120c final: 1418 games, +14.46 ± 8.61, H1, Ptnml [5, 103, 444, 142, 15]. The paired (pentanomial) counts that Sol's S48 lacked come from each gate's RESULT.md | `results/s44_points.csv` |
| advice only | yes: no Elo claim, no new games | — |

## Findings
1. **Stale gate folder names.** G98, G103, G105-G112, G122 and G123 were played against **AL1** although their
   folders say `vs_h256e12` (RUN_INFO `base.name`, exe sha256 833C47F3). Any study keyed on folder names mixes
   opponents.
2. **fastchess 1.8.2's LLR is the exact GSPRT** (constrained-MLE log-likelihood ratio, normalized model,
   pentanomial). The tool reproduces all 23 printed LLRs to 0.005, while the usual normal approximation is up to
   0.1 off at H1 stops. Simulations of these gates should use the exact form near the bounds.
3. **Bias.** At the adjusted strength the Whitehead correction of an H1 stop is small (−0.9 to −1.6 Elo). The
   winner's curse at true +10 is +7.6 to +9.4 for H1 stops and −1.3 to −1.9 for caps; this reproduces Sol's S48
   cap figures (G100r −1.73 vs −1.76, G119 −1.45 vs −1.62).
4. **Elo per 1e-4 of holdout b0.6:** 5.0 ± 1.5 (conc 5), 7.5 ± 1.8 (conc 7), 4.3 ± 3.2 (AL1 conc 8). The AL1
   group has a +6.0 ± 2.0 intercept: nets equal to AL1 in holdout score about +6 against it at conc 8 (open
   question).

## Files
- `forge_sol_S44_elo_vs_epochs.py`: check + simulation + fits + projections.
- `test_forge_sol_S44.py`: 7 tests.
- `make_s44_tables.py`: the deliverable tables from the results JSON.
- `forge_sol_S44_elo_vs_epochs_20261027.md`: the deliverable.
- `README.md`, `IDEA_SOURCE.md`, `REPORT.md`.
- `results/`: `s44_points.csv`, `s44_tables.md`, `s44_results.json.gz` (full JSON sha256 a4f89b7e…).
- `logs/`: step 1 check, step 2 tests, step 3 full run.
- `FILES.txt`, `SHA256SUMS`.
- Inputs: read-only copies of the PC's gate RESULT.md / RUN_INFO.json (`F:\opus_scratch\sol_S44\inputs\gates`,
  sha256 per gate in `s44_points.csv`), S30's `final_table.csv` / `fit.json`.

## Reproduce
```
python -I -B forge_sol_S44_elo_vs_epochs.py check --gates <gate copies>
python -I -B test_forge_sol_S44.py <gate copies>
python -I -B forge_sol_S44_elo_vs_epochs.py run --gates <gate copies> --snapshot <LA>/7_history/gate_results/gate_results_20261025_1335 \
  --lgf <LA>/7_history/LATEST_GATE_FACTS_20261026.md --s30-table <S30 out>/final_table.csv --s30-fit <S30 out>/fit.json \
  --out <new dir> --reps 4000 --step 2 --draws 200000      # about 75 min single-threaded at Idle on the loaded PC
python -I -B make_s44_tables.py <new dir>/s44_results.json
```
Machine exclusive: no.

## UNVERIFIED
See the deliverable's "UNVERIFIED / limits" section:
- the tilt model of other strengths;
- a constant holdout→Elo slope across recipes and data sizes;
- the epoch curve measured at 137M positions;
- the unexplained conc-8 offset.
