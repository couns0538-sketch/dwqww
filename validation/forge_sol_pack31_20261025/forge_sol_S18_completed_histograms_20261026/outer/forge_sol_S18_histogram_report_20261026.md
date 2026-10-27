# S18 five-arm read-only histogram batch — 2026-10-26

All five arms completed at EOF, with reconciled histograms and empty reaped owned groups. No filtering, Torch, training, postscore, engine or timing experiment ran. These are synthetic supplied-sample data counts, with no training or playing-strength claim.

| Arm | Kept | Dropped | Draw disagreement | Loss/positive | Win/negative |
|---|---:|---:|---:|---:|---:|
| none | 200000 | 0 | 0 | 0 | 0 |
| t200 | 132421 | 67579 | 33765 | 17137 | 16677 |
| t300 | 157666 | 42334 | 21122 | 10756 | 10456 |
| t400 | 175673 | 24327 | 12200 | 6096 | 6031 |
| t500 | 187141 | 12859 | 6422 | 3229 | 3208 |

Actual kept-row sum: **852901**. Every arm read the same 200,000 original training rows; the h000 holdout is separate and unchanged. Supplied synthetic holdout overlap, output duplicate positions and conflicting-label duplicate counts are zero in each arm. Real013/014 and authentic game isolation remain **UNVERIFIED**. The original t500 repeat remains **FAIL**, with its cause undetermined.

CPU 4, nice 19; each child had a 119-second work cutoff plus nominal 1-second cleanup reserve. No arm reached its cutoff. Whole batch elapsed 121.75598493599682 seconds across five sequential arms; peak child RSS 34176 KiB. Per-process parent/child AS caps were 128/768 MiB. Python: `3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]`. Raw parent and per-child stdout/stderr are preserved; all stderr files are empty. These durations are operational evidence, not speed measurements.

Phase is the unchanged current Forge HCE material phase, clamped at 24, taken from the pinned h256_e12 header. No new evaluation values were introduced. Counts below are kept rows; full input, kept, dropped, reason and disagreement maps are in the JSON artifacts.

| HCE phase | none | t200 | t300 | t400 | t500 |
|---|---:|---:|---:|---:|---:|
| 1 | 8 | 6 | 6 | 6 | 7 |
| 2 | 45 | 29 | 36 | 41 | 41 |
| 3 | 99 | 68 | 80 | 91 | 93 |
| 4 | 242 | 153 | 187 | 215 | 228 |
| 5 | 417 | 265 | 318 | 366 | 390 |
| 6 | 716 | 452 | 548 | 610 | 654 |
| 7 | 1148 | 754 | 902 | 1010 | 1070 |
| 8 | 1925 | 1261 | 1516 | 1700 | 1801 |
| 9 | 2586 | 1765 | 2083 | 2303 | 2447 |
| 10 | 3372 | 2289 | 2699 | 2997 | 3176 |
| 11 | 4442 | 2982 | 3541 | 3939 | 4185 |
| 12 | 5554 | 3595 | 4349 | 4875 | 5195 |
| 13 | 6587 | 4391 | 5176 | 5789 | 6156 |
| 14 | 7521 | 4984 | 5936 | 6605 | 7052 |
| 15 | 8561 | 5693 | 6769 | 7540 | 8033 |
| 16 | 9520 | 6272 | 7478 | 8362 | 8902 |
| 17 | 10323 | 6747 | 8074 | 9026 | 9648 |
| 18 | 10720 | 7043 | 8420 | 9365 | 9996 |
| 19 | 10917 | 7194 | 8596 | 9588 | 10227 |
| 20 | 10988 | 7206 | 8595 | 9582 | 10259 |
| 21 | 11045 | 7418 | 8787 | 9747 | 10380 |
| 22 | 10698 | 7192 | 8534 | 9480 | 10067 |
| 23 | 10371 | 6777 | 8074 | 9010 | 9644 |
| 24 | 72195 | 47885 | 56962 | 63426 | 67490 |

| Piece count | none | t200 | t300 | t400 | t500 |
|---|---:|---:|---:|---:|---:|
| 3 | 3 | 2 | 3 | 3 | 3 |
| 4 | 11 | 10 | 10 | 11 | 11 |
| 5 | 63 | 39 | 47 | 53 | 58 |
| 6 | 224 | 151 | 179 | 200 | 213 |
| 7 | 576 | 388 | 454 | 505 | 537 |
| 8 | 1333 | 893 | 1066 | 1170 | 1253 |
| 9 | 2802 | 1839 | 2218 | 2462 | 2608 |
| 10 | 5112 | 3418 | 4034 | 4510 | 4780 |
| 11 | 8401 | 5562 | 6668 | 7412 | 7880 |
| 12 | 12438 | 8164 | 9801 | 10946 | 11661 |
| 13 | 16585 | 10858 | 12996 | 14494 | 15490 |
| 14 | 20306 | 13473 | 16085 | 17896 | 19071 |
| 15 | 22443 | 14948 | 17721 | 19758 | 21005 |
| 16 | 22926 | 15181 | 17992 | 20081 | 21437 |
| 17 | 21639 | 14376 | 17121 | 19053 | 20273 |
| 18 | 18670 | 12329 | 14674 | 16358 | 17488 |
| 19 | 15191 | 10065 | 11965 | 13282 | 14181 |
| 20 | 11386 | 7510 | 8956 | 9996 | 10626 |
| 21 | 7941 | 5237 | 6258 | 6993 | 7407 |
| 22 | 5252 | 3518 | 4171 | 4632 | 4927 |
| 23 | 3105 | 2100 | 2457 | 2728 | 2895 |
| 24 | 1797 | 1169 | 1376 | 1553 | 1666 |
| 25 | 931 | 616 | 744 | 819 | 864 |
| 26 | 472 | 306 | 361 | 412 | 443 |
| 27 | 219 | 143 | 169 | 190 | 201 |
| 28 | 109 | 80 | 90 | 98 | 103 |
| 29 | 41 | 29 | 31 | 35 | 36 |
| 30 | 15 | 12 | 13 | 15 | 15 |
| 31 | 7 | 4 | 4 | 6 | 7 |
| 32 | 2 | 1 | 2 | 2 | 2 |

All four disagreement thresholds (200/300/400/500) and every phase, piece, result, sign and score-band bucket reconcile: kept plus dropped equals original input. At each arm’s own threshold all remaining rows are consistent by that filter definition. This is filter accounting, not validation that the labels improve a network.

Next action: publish/review this completed source/data checkpoint and prepare any exact arm index required for separately authorized diagnostic CPU training. No trainer import or training is authorized by these results.
