# B5 bench records

Fresh processes, Threads=1, Hash=16, OwnBook=false. Observed NPS only; no speed or Elo claim.

| Mode | Depth | Nodes | ms | NPS |
|---|---:|---:|---:|---:|
| OFF | 11 | 312866 | 3656 | 85576 |
| OFF | 13 | 862329 | 937 | 920308 |
| OFF | 16 | 3024920 | 3573 | 846605 |
| OFF | 20 | 12389307 | 12733 | 973007 |
| OFF | 22 | 34048354 | 31507 | 1080659 |
| SingularV2 | 11 | 404121 | 427 | 946419 |
| SingularV2 | 13 | 1005954 | 1084 | 928001 |
| SingularV2 | 16 | 4120585 | 4631 | 889782 |
| SingularV2 | 20 | 11497954 | 12675 | 907136 |
| SingularV2 | 22 | 34264955 | 32936 | 1040349 |
| N1 | 11 | 277579 | 437 | 635192 |
| N1 | 13 | 814055 | 984 | 827291 |
| N1 | 16 | 2651984 | 3091 | 857969 |
| N1 | 20 | 18648191 | 19145 | 974050 |
| N1 | 22 | 40304213 | 41515 | 970834 |

## Release UCI regression bench records

All d11 records from the original completed CTest output.

| Case | Depth | Nodes | ms | NPS |
|---|---:|---:|---:|---:|
| OFF | 11 | 312866 | 358 | 873927 |
| manual_N1 | 11 | 277579 | 339 | 818817 |
| OFF_after_manual | 11 | 312866 | 327 | 956776 |
| preset_N1 | 11 | 277579 | 316 | 878414 |
| N1_after_refused_CorrExt | 11 | 277579 | 303 | 916102 |
| N1_after_invalid_values | 11 | 277579 | 305 | 910095 |
| B1_CorrExt | 11 | 280216 | 346 | 809872 |
| B1_CorrExt_after_refusals | 11 | 280216 | 342 | 819345 |
| final_OFF | 11 | 312866 | 502 | 623239 |

## ASan/UBSan UCI regression records

Instrumented times are not Release performance measurements.

| Case | Depth | Nodes | ms | NPS |
|---|---:|---:|---:|---:|
| OFF | 11 | 312866 | 5945 | 52626 |
| manual_N1 | 11 | 277579 | 4369 | 63533 |
| OFF_after_manual | 11 | 312866 | 4851 | 64495 |
| preset_N1 | 11 | 277579 | 4510 | 61547 |
| N1_after_refused_CorrExt | 11 | 277579 | 4471 | 62084 |
| N1_after_invalid_values | 11 | 277579 | 4478 | 61987 |
| B1_CorrExt | 11 | 280216 | 4509 | 62145 |
| B1_CorrExt_after_refusals | 11 | 280216 | 4817 | 58172 |
| final_OFF | 11 | 312866 | 4553 | 68716 |
