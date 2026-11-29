# Net Diagnostics Comparison: `F_FIX_25R_v2` vs `OPUS_R1_live768_skipnoisy`

> **STRICTLY DIAGNOSTIC — NOT AN ELO CLAIM**
> Offline diagnostics (`S1..S7`, M4 WDL MSE, M4 correlation, OLS material ratios, `ob0<->ob1` cliff) do NOT measure playing strength or Elo. Only `fastchess` matches measure Elo.
> Unit-normalized `cp` uses `net_sanity` v2 classical pawn unit `u = (S6_Q + S6_R + S6_B + S6_N) / 20.0`.

| Metric | `F_FIX_25R_v2` | `OPUS_R1_live768_skipnoisy` | Delta (`cand - base`) |
|---|---:|---:|---:|
| `net_bytes` | 9,463,528 | 9,463,528 | +0 |
| `unit_u` (raw / pawn) | 167.55 | 162.15 | +5.40 |
| `S1_startpos` (unit cp / raw) | +36.4 cp (+61) | +25.9 cp (+42) | +10.5 cp (+19) |
| `S1_after_1e4` (unit cp / raw) | +6.0 cp (+10) | -6.2 cp (-10) | +12.1 cp (+20) |
| `S2_start_plus_e4` (unit cp / raw) | +42.4 cp (+71) | +19.7 cp (+32) | +22.6 cp (+39) |
| `S5_dead_draws` `K-K` (unit cp / raw) | -0.6 cp (-1) | +9.9 cp (+16) | -10.5 cp (-17) |
| `S5_dead_draws` `KN-K` (unit cp / raw) | -37.6 cp (-63) | -32.1 cp (-52) | -5.5 cp (-11) |
| `S5_dead_draws` `KB-K` (unit cp / raw) | -35.8 cp (-60) | -27.8 cp (-45) | -8.1 cp (-15) |
| `S5_dead_draws` `KNN-K` (unit cp / raw) | +44.2 cp (+74) | +59.8 cp (+97) | -15.7 cp (-23) |
| `S7_won_endings` `KQ-K` (unit cp / raw) | +1128.6 cp (+1891) | +751.2 cp (+1218) | +377.5 cp (+673) |
| `S7_won_endings` `KR-K` (unit cp / raw) | +411.8 cp (+690) | +288.0 cp (+467) | +123.8 cp (+223) |
| `ob0_ob1_cliff_median_jump_cp` (raw / unit cp) | 118.0 (70.4 cp) | 108.5 (66.9 cp) | +9.5 (+3.5 cp) |
| `m4_wdl_mse` | 0.01315 | 0.01314 | +0.00001 |
| `m4_opp_wing_wdl_mse` | 0.01652 | 0.01606 | +0.00046 |
| `m4_corr` | 0.7581 | 0.7601 | -0.0020 |
| `OLS Q/P` | 8.836 | 9.010 | -0.175 |
| `OLS R/P` | 5.097 | 5.005 | +0.092 |
| `OLS B/P` | 4.032 | 3.965 | +0.067 |
| `OLS N/P` | 3.503 | 3.489 | +0.015 |
| `OLS raw (P/N/B/R/Q/tempo)` | `73.1/256.1/294.7/372.6/645.9/3.5` | `76.7/267.6/304.1/383.9/691.1/1.6` | — |
| `master_gates` `overall_status` | `PASS_WITH_ADVISORY_FLAGS` | `PASS_WITH_ADVISORY_FLAGS` | — |
| `master_gates` `hard_pass` | `True` | `True` | — |
| `net_sanity` status (flags) | `ADVISORY_FLAGS` (S2 start vs 1.e4, side-to-move part) | `ADVISORY_FLAGS` (S5 dead draws, S7 won endings) | — |
| `v3_parity` `max_diff_cp` (`ob_covered`) | `0` (`8/8`) | `0` (`8/8`) | — |

## Provenance
- **F_FIX_25R_v2**: net=`C:\nnue-lab\neon\forge_fixes\gpu_runs\F_FIX_25R_v2\cand.fnn3`, eval=`None`, gates=`C:\nnue-lab\neon\forge_fixes\gpu_runs\F_FIX_25R_v2\master_gates_quick.json`
- **OPUS_R1_live768_skipnoisy**: net=`C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\cand.fnn3`, eval=`C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\eval_full.json`, gates=`C:\nnue-lab\neon\forge_fixes\gpu_runs\OPUS_R1_live768_skipnoisy\master_gate_quick.json`
