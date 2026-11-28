# Stage-2 Filter Quest & Opus Declared Ablations Summary (2026-11-27 22:42:28)

- **GPU Arms Complete:** `13 / 13`
- **Declared 1,000g @ 50k Head-to-Head Matches Complete:** `0 / 12`

## 1. Stage-2 GPU Arms (Diagnostic Only — Per R5 Never Elo Claims)

| Arm | Done | Train Loss | r0203 Quiet Mix60 | M4 WDL MSE | M4 Corr | Flags | Syz Draw Med | Syz Win OK% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `G3a_cc0_keep_noisy` | OK | 0.000847 | 0.034220 | 0.02941 | 0.5074 | 2 | 36.0 cp | 99.40% |
| `G3b_cc0_skip_noisy` | OK | 0.000407 | 0.022602 | 0.02339 | 0.6334 | 2 | 29.6 cp | 99.30% |
| `G3a_cc0_keep_noisy_eqret` | OK | 0.000761 | 0.034481 | 0.02918 | 0.5081 | 2 | 33.8 cp | 99.35% |
| `G4a_cc0_losspow25` | OK | 0.000244 | 0.034500 | 0.02937 | 0.4977 | 2 | 38.2 cp | 99.35% |
| `G4b_cc0_obreweight` | OK | 0.000830 | 0.034405 | 0.02951 | 0.5045 | 2 | 34.7 cp | 99.35% |
| `s2_ctrl_cc0_nodrawconf` | OK | 0.000843 | 0.034227 | 0.02938 | 0.5067 | 2 | 35.8 cp | 99.35% |
| `s2_f1_hard` | OK | 0.000826 | 0.034179 | 0.02899 | 0.5051 | 2 | 37.2 cp | 99.35% |
| `s2_f1_ctrl_eqret` | OK | 0.000790 | 0.034349 | 0.02938 | 0.5085 | 2 | 36.5 cp | 99.40% |
| `s2_f2_dedup_first` | OK | 0.000903 | 0.034411 | 0.02930 | 0.5102 | 1 | 35.3 cp | 99.30% |
| `s2_f2_dedup_avg` | OK | 0.000901 | 0.034308 | 0.02921 | 0.5123 | 1 | 36.3 cp | 99.35% |
| `s2_r1_rescore16k_0p5pct` | OK | 0.000908 | 0.034181 | 0.02923 | 0.5118 | 1 | 36.1 cp | 99.40% |
| `s2_r1b_rescore16k_2pct_oppcastle` | OK | 0.000904 | 0.034286 | 0.02912 | 0.5119 | 1 | 35.9 cp | 99.35% |
| `s2_w3_soft_weight` | OK | 0.000904 | 0.034335 | 0.02887 | 0.5087 | 1 | 36.2 cp | 99.30% |

## 2. Declared 1,000g @ 50k Head-to-Head Matches

| Match | Games | W–D–L | Elo [95% CI] | z | LOS% | Ptnml | Clean |
|---|---:|---|---:|---:|---:|---|---|
| `G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k` | — | pending | — | — | — | — | — |
| `G3b_skipnoisy_vs_G3a_eqret_1000g_50k` | — | pending | — | — | — | — | — |
| `G4a_losspow25_vs_G3a_losspow20_1000g_50k` | — | pending | — | — | — | — | — |
| `G4b_obreweight_cc0_vs_G3a_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_F1_hard_vs_ctrl_eqraw_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_F1_hard_vs_ctrl_eqret_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_F2_first_vs_ctrl_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_F2_avg_vs_first_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_R1_rescore16k_vs_dedup_avg_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_R1b_rescore16k_2pct_oppcastle_vs_dedup_avg_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_W3_softweight_vs_dedup_avg_1000g_50k` | — | pending | — | — | — | — | — |
| `FQ_EXP_W3_softweight_vs_f1_hard_1000g_50k` | — | pending | — | — | — | — | — |
