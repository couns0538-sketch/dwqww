# EVALSCALE 2026-10-27 — static-eval scale of the new nets vs h256_e12 (S41)

**Question (S41).** The search margins (RFP, futility, razoring, ...) were tuned on h256_e12's evaluation scale. Do
the newer nets (e48f006, e48f029, the AL1 lock net s198, plus e48f034) spread their static evaluations wider or
narrower, and what `NetScale` maps them back?

**Answer.** They spread slightly wider: **+0.9% to +2.4%** (robust paired slope; every 95% CI excludes 1.000). The
mapping values are **NetScale 99** for s198 (the lock), e48f006 and e48f034, and **98** for e48f029. Against the
current lock s198, e48f006 and e48f034 sit on the same scale (NetScale 100) and e48f029 is +1.3% (99). The whole
difference comes from the network residual: the hand-crafted evaluation is the same code in all of them. These
are small shifts. No strength claim either way; only a gate can tell.

## Method
- **Positions** (`data/positions_10k_20261027.txt.gz`, sha256 of the text `e144236a…`): all 300 WAC positions (lock
  archive `4_tests/suites/wac300.epd`) plus 9,700 self-play positions. These are the first full line after each of
  9,700 evenly spaced byte offsets (stride 67,039 B) in the closed holdout file
  `D:\grok-pc-data\selfplay_out\forge_selfplay_013.txt` (650,287,208 B, md5 sidecar `f0739b12…`). The file was only
  read, with short seeks. 013 is part of the trainer's holdout (013 + 014), so these positions are essentially
  unseen in training: per `opus-sol-S16`, only 6,069 training rows share a position with the 16.4M-row holdout,
  about 0.04%. 10,000 positions, 0 invalid, 3 in check.
  Positions in check are excluded because the search never uses a static eval there.
- **Evaluation** (`tools/evalscale_dump.cpp`, one build per net with the lock's compiler flags): per position `hce`
  (`Evaluator::evaluate_uncached`), `net` (`nnue::evaluate` after a refresh) and
  `total = clamp(hce + net, ±(MateInMaxPly − 1))`, which is what `Worker::static_evaluate` returns (the lock's
  `forge_runtime_psqt_tests` and this branch's `forge_net_scale_tests` check that identity). Nets come from the lock
  archive `5_nnue/nets`, md5 h256_e12 `6d22f612`, s198 `22b4b9e2`, e48f006 `0fae54a4`, e48f029 `652f7bcf`,
  e48f034 `91d23280`. A second dump of h256_e12 and s198 was byte-identical, and so was a second analysis
  (`logs/step12_repro.log`).
- **Statistics** (`tools/evalscale_20261027.py analyze`): positions with |total| ≤ 2000 cp on both sides (about 9,890
  per pair; beyond that the result is decided and outside margin territory).
  - Primary: `sym` = sqrt(LAD(cand on ref) / LAD(ref on cand)), where LAD is the least-absolute-deviation slope
    through the origin (= weighted median of ratios). `sym` is symmetric, so it has no regression-dilution
    direction.
  - Cross-checks: Theil–Sen (2 M fixed-seed pairs), Huber, OLS, and |eval| quantile ratios.
  - 95% CI: percentile bootstrap, 1,000 resamples, seed 20261027.
  - NetScale = round(100 / sym). "sym after NetScale" re-applies the engine's integer arithmetic (truncation
    toward zero).

## |static eval| quantiles (cp)
| net | n | q10 | q25 | q50 | q75 | q90 | q95 | q99 | mean | beyond 2000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| h256_e12 | 9906 | 23 | 60 | 158 | 385 | 808 | 1171 | 1720 | 300.3 | 91 |
| s198 (AL1) | 9924 | 23 | 62 | 158 | 391 | 840 | 1208 | 1726 | 306.1 | 73 |
| e48f006 | 9907 | 22 | 61 | 157 | 387 | 828 | 1183 | 1757 | 303.7 | 90 |
| e48f029 | 9900 | 22 | 61 | 157 | 386 | 831 | 1211 | 1758 | 305.2 | 97 |
| e48f034 | 9924 | 22 | 61 | 157 | 389 | 833 | 1201 | 1739 | 305.6 | 73 |

The bulk of the distribution (q10-q75) is the same within ±6 cp. The new nets differ in the tail (q90-q95: +2% to
+4%).

## Robust slope against h256_e12 (cand = s · ref)
| net | n | **sym** | 95% CI | LAD c\|r | LAD r\|c | Theil-Sen | Huber | OLS | Pearson | q50 ratio | q90 ratio | **NetScale** | sym after |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| h256_e12 (same net) | 9906 | **1.0000** | 1.0000-1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | **100** | 1.0000 |
| s198 (AL1 lock) | 9895 | **1.0117** | 1.0085-1.0141 | 1.0074 | 0.9843 | 1.0052 | 1.0080 | 1.0067 | 0.9958 | 1.0000 | 1.0204 | **99** | 1.0006 |
| e48f006 | 9884 | **1.0132** | 1.0098-1.0161 | 1.0076 | 0.9815 | 1.0056 | 1.0087 | 1.0111 | 0.9953 | 0.9936 | 1.0222 | **99** | 1.0019 |
| e48f029 | 9883 | **1.0243** | 1.0205-1.0273 | 1.0190 | 0.9713 | 1.0126 | 1.0212 | 1.0253 | 0.9955 | 1.0000 | 1.0311 | **98** | 1.0029 |
| e48f034 | 9893 | **1.0088** | 1.0053-1.0122 | 1.0030 | 0.9856 | 1.0025 | 1.0044 | 1.0048 | 0.9952 | 1.0000 | 1.0152 | **99** | 0.9976 |

- **Same net on both sides gives exactly 1.0000** for every estimator, ratio and CI bound. This holds for
  h256_e12 vs h256_e12 here and for s198 vs s198 in the next table; the unit test asserts `== 1.0`.
- Every estimator agrees on the sign. The one-sided LAD slopes (c|r 1.003-1.019, r|c 0.971-0.986) show the
  expected dilution in both directions, which `sym` cancels.

## Against the current lock s198 (no bootstrap)
| net | sym | Theil-Sen | q50 ratio | q90 ratio | NetScale |
|---|---:|---:|---:|---:|---:|
| h256_e12 | 0.9885 | 0.9853 | 1.0000 | 0.9800 | 101 |
| s198 (same net) | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100 |
| e48f006 | 1.0007 | 0.9967 | 1.0000 | 1.0012 | 100 |
| e48f029 | 1.0131 | 1.0043 | 1.0000 | 1.0097 | 99 |
| e48f034 | 0.9974 | 0.9953 | 1.0000 | 0.9928 | 100 |

## Where the difference sits
| net | sym, \|ref\| ≤ 300 | sym, 300 < \|ref\| ≤ 2000 | mean \|net\| (e12 = 84.6) | net share of \|total\| | residual-only scale for sym 1 (diagnostic) |
|---|---:|---:|---:|---:|---:|
| s198 | 1.0084 | 1.0122 | 86.8 | 0.270 (e12 0.261) | 94.7% |
| e48f006 | 1.0132 | 1.0127 | 88.2 | 0.271 | 94.2% |
| e48f029 | 1.0079 | 1.0266 | 90.8 | 0.276 | 89.8% |
| e48f034 | 1.0116 | 1.0082 | 86.6 | 0.269 | 96.2% |

- The HCE is shared, so the scale change is the residual network's. Its mean magnitude grows from 84.6 cp (e12) to
  86.6-90.8 cp.
- Scaling only the residual would need 90-96% to give the same total spread. `NetScale` scales the total static
  evaluation instead, so a margin sees exactly the mapped value. The tool reports both.

## NetScale benches (patched exes, PC lock recipe; `logs/step7_benches.log`, `logs/step8_sweep.log`)
| exe | NetScale | d11 | d13 | d16 | d20 | d22 | max \|Δ\| vs OFF |
|---|---|---:|---:|---:|---:|---:|---:|
| AL1 patched | 100 (OFF) | 312866 | 862329 | 3024920 | 12389307 | 34048354 | 0 (= AL1 refs, `uci_check --full` ALL OK) |
| AL1 patched | **99 (proposal)** | 308948 | 917342 | 2601047 | 14196959 | 32409747 | 14.6% |
| AL1 patched | 90 (idea board) | 314443 | 981369 | 2815907 | 10725072 | 19172306 | 43.7% (d22) |
| e48f006 base, unpatched | — | 328459 | 945640 | 3024381 | 9162399 | 20421972 | = spec refs |
| e48f006 patched | 100 (OFF) | 328459 | 945640 | 3024381 | 9162399 | 20421972 | 0 (= e48f006 base, perft OK) |
| e48f006 patched | **99 (proposal)** | 359735 | 887594 | 3061541 | 13180572 | 20185144 | 43.9% (d20) |

**Single-position bench nodes are chaotic under any evaluation rescale.** The same sweep on AL1 moves single depths
by up to 38.6% (NetScale 98, d20), 33.7% (95, d22) and 27.2% (105, d20). Only 97 and 103 stay within 11%. On e48f006, +1% (101) moves d20 by 49.9% and
-2% (98) by 35.9%. None of this is a tree-size blowup. On 100 fixed self-play positions at depth 12 (one process,
`ucinewgame` before each), the ON/OFF total-node ratio is:
- AL1 @99: **1.0057**;
- AL1 @90: **1.0061**;
- e48f006 @99: **0.9980**.

Per-position trees move by more than 20% in 61-66% of the positions, in both directions (median 1.03-1.07; IQR
about 0.77-1.37). So by the strict per-depth reading of "no blowup over 20%":
- the proposal for the lock (AL1 @99) **passes**: max 14.6%;
- e48f006 @99 does not (d20 +43.9%);
- the aggregate tree size is unchanged within 0.6% in every case.

## Recommendation
- The scale drift since h256_e12 is small: +1.2% for the lock s198, at most +2.4% (e48f029). A `NetScale` gate
  is not urgent. If the crew wants one, the candidate is `NetScale=99` vs AL1:
  - one option, its own srand from TEST_PLAN, SPRT as usual;
  - expected to be near-neutral (UNVERIFIED).
- For a future lock net, rerun steps 2-3 of the README first and use the `netscale_percent` it prints.
  `NetScale=90` (idea board) would over-correct every net measured here by 8-9%.
