# P5 relabel QC — R13

QC integrity: **PASS**. Authentic game separation: **UNVERIFIED**.
No strength, training-readiness or improved-label-quality claim.

| Measure | R14-B jobA | Old R13 baseline |
|---|---:|---:|
| Rows | 999921 | 440000 |
| Mate-range rows | 2717 | 1001 |
| Mate-range percentage | 0.27172146599581365 | 0.2275 |
| Mean STM score | 35.62344025177989 | 24.821402272727273 |
| Mean White score | 169.25168288294776 | 179.01585227272727 |
| Exact-FEN duplicate rows | 0 | 0 |
| Exact-FEN duplicate rate | 0.0 | 0.0 |
| Non-mate rows | 997204 | 438999 |
| Non-mate mean STM score | 7.7154814862355146 | 1.6319877721817133 |
| Non-mate paired mean absolute label delta | 116.66204708364587 | 117.80011571780345 |

## Score distribution

Buckets are STM centipawns, lower-inclusive and upper-exclusive. Mate flagging is separately inclusive at abs(score) >= 30000.

| Bucket | R14-B rows | R14-B % | Old rows | Old % |
|---|---:|---:|---:|---:|
| [-inf,-30000) | 922 | 0.0922 | 341 | 0.0775 |
| [-10000,-3000) | 487 | 0.0487 | 223 | 0.0507 |
| [-3000,-1000) | 64295 | 6.4300 | 28718 | 6.5268 |
| [-1000,-300) | 130337 | 13.0347 | 59227 | 13.4607 |
| [-300,-100) | 127092 | 12.7102 | 56572 | 12.8573 |
| [-100,0) | 152271 | 15.2283 | 67017 | 15.2311 |
| [0,100) | 187943 | 18.7958 | 79441 | 18.0548 |
| [100,300) | 134208 | 13.4219 | 59545 | 13.5330 |
| [300,1000) | 133945 | 13.3956 | 59587 | 13.5425 |
| [1000,3000) | 65849 | 6.5854 | 28321 | 6.4366 |
| [3000,10000) | 777 | 0.0777 | 348 | 0.0791 |
| [30000,inf) | 1795 | 0.1795 | 660 | 0.1500 |

## WDL, White perspective

| Value | R14-B rows | R14-B % | Old rows | Old % |
|---|---:|---:|---:|---:|
| draw | 320203 | 32.0228 | 133297 | 30.2948 |
| loss | 253007 | 25.3027 | 111001 | 25.2275 |
| win | 426711 | 42.6745 | 195702 | 44.4777 |

## WDL, side-to-move perspective

| Value | R14-B rows | R14-B % | Old rows | Old % |
|---|---:|---:|---:|---:|
| draw | 320203 | 32.0228 | 133297 | 30.2948 |
| loss | 342947 | 34.2974 | 155747 | 35.3970 |
| win | 336771 | 33.6798 | 150956 | 34.3082 |

## Side to move

| Value | R14-B rows | R14-B % | Old rows | Old % |
|---|---:|---:|---:|---:|
| b | 499462 | 49.9501 | 220175 | 50.0398 |
| w | 500459 | 50.0499 | 219825 | 49.9602 |

## Piece count, including kings

| Value | R14-B rows | R14-B % | Old rows | Old % |
|---|---:|---:|---:|---:|
| 3 | 12901 | 1.2902 | 3156 | 0.7173 |
| 4 | 35537 | 3.5540 | 13424 | 3.0509 |
| 5 | 50066 | 5.0070 | 20131 | 4.5752 |
| 6 | 44274 | 4.4277 | 20061 | 4.5593 |
| 7 | 51188 | 5.1192 | 23234 | 5.2805 |
| 8 | 44479 | 4.4483 | 20440 | 4.6455 |
| 9 | 44199 | 4.4202 | 19327 | 4.3925 |
| 10 | 39860 | 3.9863 | 17527 | 3.9834 |
| 11 | 38572 | 3.8575 | 16520 | 3.7545 |
| 12 | 34709 | 3.4712 | 15526 | 3.5286 |
| 13 | 32059 | 3.2062 | 14127 | 3.2107 |
| 14 | 32395 | 3.2398 | 14173 | 3.2211 |
| 15 | 29295 | 2.9297 | 13548 | 3.0791 |
| 16 | 28280 | 2.8282 | 12470 | 2.8341 |
| 17 | 26737 | 2.6739 | 11770 | 2.6750 |
| 18 | 27466 | 2.7468 | 12215 | 2.7761 |
| 19 | 25222 | 2.5224 | 10817 | 2.4584 |
| 20 | 26131 | 2.6133 | 11482 | 2.6095 |
| 21 | 23265 | 2.3267 | 10896 | 2.4764 |
| 22 | 28108 | 2.8110 | 12068 | 2.7427 |
| 23 | 22922 | 2.2924 | 10839 | 2.4634 |
| 24 | 30514 | 3.0516 | 12974 | 2.9486 |
| 25 | 23127 | 2.3129 | 10595 | 2.4080 |
| 26 | 34329 | 3.4332 | 14942 | 3.3959 |
| 27 | 23439 | 2.3441 | 10874 | 2.4714 |
| 28 | 39006 | 3.9009 | 17074 | 3.8805 |
| 29 | 24869 | 2.4871 | 11387 | 2.5880 |
| 30 | 48027 | 4.8031 | 22152 | 5.0345 |
| 31 | 25234 | 2.5236 | 11716 | 2.6627 |
| 32 | 53711 | 5.3715 | 24535 | 5.5761 |

## Material-phase proxy

| Value | R14-B rows | R14-B % | Old rows | Old % |
|---|---:|---:|---:|---:|
| early | 329610 | 32.9636 | 147744 | 33.5782 |
| end | 495230 | 49.5269 | 212771 | 48.3570 |
| middle | 175081 | 17.5095 | 79485 | 18.0648 |

## Interpretation and limits

- The cohorts are different populations. Cross-cohort differences are descriptive, not paired label changes.
- R14-B paired old-score statistics compare each row only to its own original self-play score.
- Old labels were searched with castling/EP removed and clocks reset. Their duplicate-FEN rate uses that lossy representation and is not directly comparable as original-state diversity.
- The 440k baseline is the complete sealed prefix listed in its shards.tsv; its larger original relabel job is incomplete.
- A separate corrected 1k P5 proof exists at D:/o14a/p5/job_fix1k. It is not pooled into either cohort, nor used to repair old labels.
- R14-B IDs are inferred groups, not authentic original-game identifiers. No production game-separation PASS is claimed.
- JobB is used only for final-label content-hash reproducibility, not counted as extra data.
- Mate rows are flagged into a separate original-preserving file. No source score is clamped or rewritten.
- Full per-split distributions, duplicate counts and paired-score deltas are in statistics.json.
- Primary label/sidecar manifests are checked; historical probe logs and retained intermediate files are not reopened.

Material phase: N/B=1,R=2,Q=4 summed both sides; cap24; end0..8,middle9..16,early17..24; material proxy, not actual ply phase.

## Reproduction

Run `p5qc/reproduce.ps1 -RunName NEW_NAME` from the contained checkout. Existing run destinations are refused.
Tests: full inherited datafilter suite plus `tests/`, via `tools/run_tests.py` and the reviewed launcher.

Measured audit duration: 289.438 seconds.
Input result: `D:/a13/p5qc/statistics.json`. Complete consumed-input SHA256/MD5 receipts: adjacent `INPUTS.json`.
Final artifact checksums are in SHA256SUMS and MD5SUMS.
