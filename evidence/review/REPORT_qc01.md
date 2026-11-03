# P5 relabel QC — R13

QC integrity: **PASS**. Authentic game separation: **UNVERIFIED**.
No strength, training-readiness or improved-label-quality claim.

| Measure | R14-B jobA | Old R13 baseline |
|---|---:|---:|
| Rows | 999921 | 440000 |
| Mate-range rows | 2717 | 1001 |
| Mean STM score | 35.62344025177989 | 24.821402272727273 |
| Mean White score | 169.25168288294776 | 179.01585227272727 |
| Exact-FEN duplicate rows | 0 | 0 |
| Exact-FEN duplicate rate | 0.0 | 0.0 |

## Score distribution

Buckets are STM centipawns, lower-inclusive and upper-exclusive. Mate flagging is separately inclusive at abs(score) >= 30000.

| Bucket | R14-B rows | Old rows |
|---|---:|---:|
| [-inf,-30000) | 922 | 341 |
| [-10000,-3000) | 487 | 223 |
| [-3000,-1000) | 64295 | 28718 |
| [-1000,-300) | 130337 | 59227 |
| [-300,-100) | 127092 | 56572 |
| [-100,0) | 152271 | 67017 |
| [0,100) | 187943 | 79441 |
| [100,300) | 134208 | 59545 |
| [300,1000) | 133945 | 59587 |
| [1000,3000) | 65849 | 28321 |
| [3000,10000) | 777 | 348 |
| [30000,inf) | 1795 | 660 |

## WDL, White perspective

| Value | R14-B rows | Old rows |
|---|---:|---:|
| draw | 320203 | 133297 |
| loss | 253007 | 111001 |
| win | 426711 | 195702 |

## WDL, side-to-move perspective

| Value | R14-B rows | Old rows |
|---|---:|---:|
| draw | 320203 | 133297 |
| loss | 342947 | 155747 |
| win | 336771 | 150956 |

## Side to move

| Value | R14-B rows | Old rows |
|---|---:|---:|
| b | 499462 | 220175 |
| w | 500459 | 219825 |

## Piece count, including kings

| Value | R14-B rows | Old rows |
|---|---:|---:|
| 3 | 12901 | 3156 |
| 4 | 35537 | 13424 |
| 5 | 50066 | 20131 |
| 6 | 44274 | 20061 |
| 7 | 51188 | 23234 |
| 8 | 44479 | 20440 |
| 9 | 44199 | 19327 |
| 10 | 39860 | 17527 |
| 11 | 38572 | 16520 |
| 12 | 34709 | 15526 |
| 13 | 32059 | 14127 |
| 14 | 32395 | 14173 |
| 15 | 29295 | 13548 |
| 16 | 28280 | 12470 |
| 17 | 26737 | 11770 |
| 18 | 27466 | 12215 |
| 19 | 25222 | 10817 |
| 20 | 26131 | 11482 |
| 21 | 23265 | 10896 |
| 22 | 28108 | 12068 |
| 23 | 22922 | 10839 |
| 24 | 30514 | 12974 |
| 25 | 23127 | 10595 |
| 26 | 34329 | 14942 |
| 27 | 23439 | 10874 |
| 28 | 39006 | 17074 |
| 29 | 24869 | 11387 |
| 30 | 48027 | 22152 |
| 31 | 25234 | 11716 |
| 32 | 53711 | 24535 |

## Material-phase proxy

| Value | R14-B rows | Old rows |
|---|---:|---:|
| early | 329610 | 147744 |
| end | 495230 | 212771 |
| middle | 175081 | 79485 |

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

Measured audit duration: 217.062 seconds.
Input result: `D:/a13/p5qc/runs/qc01/statistics.json`. Complete consumed-input SHA256/MD5 receipts: adjacent `INPUTS.json`.
Final artifact checksums are in SHA256SUMS and MD5SUMS.
