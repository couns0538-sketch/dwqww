# S21 [Sol leftover] int16 range study on all 13 nets + research-only clipped export — DONE (RESEARCH ONLY)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 13. Branch `opus-sol-S21` = `d4f4312` + `0d99f02` cherry-picked + this
commit. **No engine patch** (crew rework 10:30: research only; rule 8: no int16 H256 engine path). `[skip ci]`.
Sol never started S21.

## Acceptance (Sol's pass line)
| line | result | evidence |
|---|---|---|
| per-net int16 range report over 200k positions | **PASS** | `forge_sol_S21_int16range.py study`: 13 nets × 200,000 positions (data32 `t00000`-`t03000`), both perspectives, all 256 lanes; table below (`logs/step1_study.log`, `s21_study_200k.json` in `logs/s21_results.tar.gz`) |
| flags the overflow on all 13 nets, consistent with CR's table | **PASS** | every net has int16 overflow on 28.1%-85.5% of the positions; CR's weight-only bounds are reproduced exactly for all 13 nets (max\|w1\|, top-32 bound, 768 bound, max\|w2\|; test `test_weight_bounds_equal_cr_table`), and every top-32 bound exceeds 32767 as CR states |
| clipped-export tool stating the float-parity loss | **PASS** | `forge_sol_S21_int16range.py export`: 13 nets × 2 modes, every export fits int16 on the 200k positions, parity loss table below (`logs/step3_exports.log`, `logs/step3b_exports_fix.log`) |
| deterministic | **PASS** | integer accumulation in a fixed order, float64 outputs; no randomness |
| tests | **PASS** | 5/5 (`logs/step4_tests.log`): feature mapping vs the trainer formula, accumulator and cp vs a direct loop, wrap semantics, export fits int16 and carries `#error`, CR table equality |
| forward = engine | **PASS** | `forge_sol_S21_engine_parity.py`: the study's Python forward vs `forge::nnue` (the archive's `nnue_check.cpp` built per net against the lock sources) on the 916-line real sample: 916/916 exact, 0 cp, for e12, f006 and the AL1 lock net f003rec_s198 (`logs/step2_engine_parity.log`) |

## 1. Range study (int units of 1/4096; 200,000 positions; both perspectives)
| net | md5 | max\|w1\| | top-32 bound | 768 bound | max\|acc\| | q0.999 \|acc\| | positions with an int16 overflow | lanes that ever overflow | output changed by int16 wrapping |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| e12_e_ep12 | 6d22f612 | 10323 | 262551 | 1635680 | 86271 | 40640 | 112,106 (56.1%) | 117/256 | 112,100 |
| e32_f003_b06_ep32 | 80a35e2f | 14055 | 383755 | 1940536 | 104686 | 49408 | 167,911 (84.0%) | 172/256 | 167,895 |
| e16_f004_b06_sol_ep16 | 4c8ba6dd | 9688 | 259245 | 1498988 | 76397 | 36800 | 77,432 (38.7%) | 87/256 | 77,419 |
| e24_f005_b06_ep24 | 0ae059d1 | 10128 | 258309 | 1415036 | 72647 | 34304 | 56,118 (28.1%) | 59/256 | 56,110 |
| e48_f006_b06_ep48 | 0fae54a4 | 12011 | 327268 | 2177169 | 106879 | 51072 | 171,083 (85.5%) | 131/256 | 171,065 |
| e16_f007_b06_ep16 | eaf55cb9 | 9964 | 267511 | 1501156 | 83707 | 37568 | 92,363 (46.2%) | 84/256 | 92,347 |
| e20_f008_b06_sol_ep20 | 1a2ea398 | 10673 | 251600 | 1569811 | 78332 | 37184 | 84,323 (42.2%) | 78/256 | 84,310 |
| e16_f009_b06_ep16 | eee839ba | 10979 | 254787 | 1529476 | 90427 | 36864 | 86,833 (43.4%) | 95/256 | 86,826 |
| e16_f010_b06_ep16 | d8e332e9 | 9115 | 249454 | 1448510 | 84366 | 34368 | 63,254 (31.6%) | 53/256 | 63,246 |
| e20_f011_b06_ep20 | 2623b434 | 13735 | 331731 | 1531680 | 88928 | 41984 | 125,226 (62.6%) | 112/256 | 125,217 |
| e16_f012_b06_sol_ep16 | 1f0bca9a | 10109 | 245561 | 1512252 | 80044 | 36800 | 83,965 (42.0%) | 88/256 | 83,954 |
| e20_f013_b06_ep20 | 6d0ede66 | 8738 | 229760 | 1494818 | 71592 | 35968 | 74,747 (37.4%) | 43/256 | 74,734 |
| e20_f014_b06_ep20 | 4eb57893 | 9292 | 237793 | 1506055 | 89231 | 36608 | 77,783 (38.9%) | 51/256 | 77,773 |

**Reading:**
- An int16 accumulator at the trainer's scale (4096 = activation 1.0) overflows on every net, on 28-86% of real
  positions. Even the 99.9th percentile of |acc| (34k-51k) is beyond 32767.
- With int16 wrapping arithmetic, the network output changes on almost every overflowing position.
- The overflow is not a corner case; an int16 path would need a different scale or quantisation-aware training.
- The AL1 float path and an int32 port are unaffected: CR's headroom table, reproduced here.

## 2. Research export: W1/B1 rescaled into int16 (float-parity loss on the same 200,000 positions)
- **Mode `bound`:** `a = (32767 − 17) / top-32 bound`, guaranteed for every legal position.
- **Mode `observed`:** `a = (32767 − 17) / max|acc|` on these positions, NOT guaranteed beyond them.
- 17 int units are reserved for the rounding of up to 33 terms.
- W2/B2 are unchanged; the activation divides by 4096·a.
- Every export `.inc` starts with `#error`, so the engine cannot be built with it.
- "Sign flips" counts positions whose network cp changes sign where |original| ≥ 1 cp.

| net | bound: a | mean \|Δ\| cp | max \|Δ\| cp | flips | observed: a | mean \|Δ\| cp | max \|Δ\| cp | flips |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| e12_e_ep12 | 0.12474 | 0.887 | 11.57 | 58 | 0.37962 | 0.291 | 3.90 | 2 |
| e32_f003 | 0.08534 | 1.378 | 14.29 | 129 | 0.31284 | 0.392 | 4.46 | 2 |
| e16_f004 | 0.12633 | 1.029 | 11.02 | 49 | 0.42868 | 0.304 | 3.51 | 1 |
| e24_f005 | 0.12679 | 1.238 | 12.33 | 121 | 0.45081 | 0.347 | 3.43 | 2 |
| e48_f006 | 0.10007 | 1.402 | 14.41 | 147 | 0.30642 | 0.450 | 4.60 | 11 |
| e16_f007 | 0.12242 | 1.018 | 10.82 | 70 | 0.39125 | 0.323 | 3.54 | 1 |
| e20_f008 | 0.13017 | 1.097 | 11.85 | 85 | 0.41809 | 0.348 | 4.37 | 0 |
| e16_f009 | 0.12854 | 0.972 | 9.93 | 59 | 0.36217 | 0.346 | 3.65 | 5 |
| e16_f010 | 0.13129 | 1.135 | 11.84 | 75 | 0.38819 | 0.372 | 4.61 | 5 |
| e20_f011 | 0.09872 | 1.219 | 12.27 | 85 | 0.36828 | 0.326 | 3.43 | 1 |
| e16_f012 | 0.13337 | 0.933 | 9.32 | 67 | 0.40915 | 0.304 | 3.46 | 0 |
| e20_f013 | 0.14254 | 1.157 | 11.41 | 81 | 0.45745 | 0.348 | 3.65 | 1 |
| e20_f014 | 0.13772 | 1.112 | 12.56 | 80 | 0.36702 | 0.430 | 4.42 | 7 |

All 26 exports fit int16 on the positions (max |acc'| ≤ 32752).

**Notes:**
- The first four exports (e12 and f003, both modes) were re-run after the rounding-headroom fix. The first f003
  `observed` run had reached 32769; the table uses the re-runs (`exports_fix`).
- **Parity cost:**
  - A guaranteed int16 accumulator costs about 0.9-1.4 cp mean and 9-14 cp worst-case network error, plus 49-147
    sign flips per 200k positions.
  - The data-fitted scale costs about 0.3-0.45 cp mean, but offers no guarantee.
- **What this means for int16:** if int16 is ever revisited, the route is quantisation-aware training at the target
  scale (a later design job), not post-hoc clipping of float-trained nets. No engine path is proposed here.

## Files
- **Tools:**
  - `forge_sol_S21_int16range.py` (study and export);
  - `forge_sol_S21_engine_parity.py` (Python forward vs engine).
- **Tests and docs:** `test_forge_sol_S21_int16range.py`, `README.md`, `IDEA_SOURCE.md`, `REPORT.md`.
- **Logs:**
  - `logs/step1_study.log`, `logs/step2_engine_parity.log`, `logs/step3_exports.log`,
    `logs/step3b_exports_fix.log`, `logs/step4_tests.log`;
  - `logs/s21_results.tar.gz` (9,187 B: the study JSON, the engine-parity JSON, the 30 export JSONs with parity
    numbers).
- `FILES`, `SHA256SUMS`.
- **Not committed:** the export `.inc` files (about 1.1 MB each; research only, `#error` guarded) stay in
  `F:\opus_scratch\sol_s21\exports*`.
- **Housekeeping:**
  - The study JSON was first written as `s21_study_200k.json.json` (a naming bug in study mode, fixed in the
    committed tool); the copy in the archive has the right name.
  - Machine exclusive: no.

## UNVERIFIED
- The data32 sample's positions stand in for real positions. Their accumulator ranges come from real piece
  placements; the sample's labels are irrelevant to this study. The full production data was not swept.
- Any int16 engine path: none exists or is proposed.
