# FORGENN3-P (`G3_FULL25` 1024w Pairwise+PSQT) Diagnostic Scaling Trajectory

- **Generated:** `2026-11-27 22:28:33`
- **Integrity Rule (R5):** Strictly offline diagnostic trajectory (M4 WDL MSE, SF19 6k slice, 4,000 unseen Syzygy positions, untouched `r0203` ECE). Playing strength is decided exclusively by declared `fastchess` matches!

| Checkpoint | Updates | Sanity Flags | M4 WDL MSE | M4 Corr | SF19 MSE | SF19 Flip% | Syz Draw Med | Syz Win OK% | r0203 ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `r0067 (768w SCReLU 25r)` | 13.8B | — | 0.01302 | 0.7754 | 0.057367 | 5.10% | 19.0 cp | 99.35% | 0.01743 |
| `G2_1024p (12r Pairwise+PSQT)` | 6.8B | 2 | 0.01234 | 0.7864 | 0.055020 | 4.45% | 8.9 cp | 99.60% | 0.01653 |
| `G3_FULL25 Ep 6 (Cycle 1)` | 2.12B | 1 | 0.01197 | 0.7915 | 0.054138 | 4.45% | 10.7 cp | 99.60% | — |
| `G3_FULL25 Ep 12 (Cycle 2)` | 4.24B | — | 0.01185 | 0.7950 | 0.053505 | 4.27% | 9.2 cp | 99.65% | — |
| `G3_FULL25 Ep 24 (Cycle 3)` | 8.48B | 0 | 0.01175 | 0.7984 | 0.053187 | 3.98% | 10.7 cp | 99.65% | 0.01458 |
| `G3_FULL25 Ep 40 (Final Cycle 4)` | 14.14B | 1 | 0.01140 | 0.8041 | 0.052914 | 3.98% | 9.9 cp | 99.60% | 0.01685 |
