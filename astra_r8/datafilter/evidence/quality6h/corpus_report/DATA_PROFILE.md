# Closed-source data profile — UNPROVEN

Inspected 304,999,573 rows across 37 complete owned self-play shards.
Sources are 001–039 excluding 013/014. Every source row received a full-board
validity check; original producer MD5 and complete SHA256 were recorded.
These are descriptive data statistics. No training input, game-ID separation,
full-corpus holdout clearance or playing-strength result is produced.

Known outcomes: 304,999,573; unknown outcomes: 0.

Aggregate STM score/result correlation: 0.6567069235.
This uses summed raw moments, not an average of per-shard correlations.

| Measurable rule | Kept | Keep rate |
|---|---:|---:|
| In check | 304,999,573 | 100.0000% |
| Mate score | 304,999,573 | 100.0000% |
| Ply >160 | 285,511,513 | 93.6105% |

Capture/promotion and qsearch coverage remain unavailable for these sources.
The matched recipes still use the separately cleared 999,953-row cohort.
The ply boundary remains an experiment, not an enabled recipe change.

| Shard | Rows | White W/D/L (known) | Correlation | Ply >160 |
|---|---:|---:|---:|---:|
| forge_selfplay_001 | 466,506 | 197,437/148,892/120,177 | 0.664703 | 42,231 |
| forge_selfplay_002 | 3,126,714 | 1,328,097/1,014,135/784,482 | 0.661387 | 271,743 |
| forge_selfplay_003 | 10,000,000 | 4,256,710/3,174,426/2,568,864 | 0.659879 | 801,812 |
| forge_selfplay_004 | 10,000,000 | 4,251,652/3,204,327/2,544,021 | 0.660013 | 778,784 |
| forge_selfplay_005 | 10,000,000 | 4,277,944/3,156,913/2,565,143 | 0.658504 | 744,677 |
| forge_selfplay_006 | 9,544,563 | 4,047,502/3,017,634/2,479,427 | 0.657784 | 691,806 |
| forge_selfplay_007 | 10,000,000 | 4,265,843/3,148,936/2,585,221 | 0.658234 | 710,488 |
| forge_selfplay_008 | 10,000,000 | 4,272,082/3,109,765/2,618,153 | 0.657329 | 684,406 |
| forge_selfplay_009 | 9,491,886 | 4,067,409/2,976,931/2,447,546 | 0.656650 | 653,274 |
| forge_selfplay_010 | 10,000,000 | 4,289,677/3,120,154/2,590,169 | 0.658122 | 675,348 |
| forge_selfplay_011 | 104,596 | 45,968/32,135/26,493 | 0.656114 | 6,136 |
| forge_selfplay_012 | 2,625,970 | 1,127,819/818,631/679,520 | 0.656427 | 173,945 |
| forge_selfplay_015 | 10,000,000 | 4,305,929/3,081,904/2,612,167 | 0.657045 | 636,037 |
| forge_selfplay_016 | 10,000,000 | 4,324,505/3,076,423/2,599,072 | 0.656205 | 648,825 |
| forge_selfplay_017 | 2,612,839 | 1,116,690/812,727/683,422 | 0.656556 | 167,634 |
| forge_selfplay_018 | 10,000,000 | 4,322,118/3,082,611/2,595,271 | 0.656912 | 633,343 |
| forge_selfplay_019 | 2,721,866 | 1,162,725/844,179/714,962 | 0.656377 | 172,520 |
| forge_selfplay_020 | 6,686,147 | 2,857,901/2,087,153/1,741,093 | 0.656207 | 426,773 |
| forge_selfplay_021 | 10,000,000 | 4,308,451/3,082,412/2,609,137 | 0.656987 | 627,903 |
| forge_selfplay_022 | 10,000,000 | 4,303,356/3,080,046/2,616,598 | 0.656387 | 614,250 |
| forge_selfplay_023 | 4,532,807 | 1,958,512/1,384,768/1,189,527 | 0.657961 | 274,384 |
| forge_selfplay_024 | 10,000,000 | 4,312,726/3,098,616/2,588,658 | 0.656931 | 622,705 |
| forge_selfplay_025 | 10,000,000 | 4,302,711/3,082,666/2,614,623 | 0.655184 | 604,268 |
| forge_selfplay_026 | 10,000,000 | 4,319,187/3,064,778/2,616,035 | 0.656033 | 610,861 |
| forge_selfplay_027 | 10,000,000 | 4,289,642/3,083,702/2,626,656 | 0.654630 | 603,346 |
| forge_selfplay_028 | 10,000,000 | 4,333,994/3,045,184/2,620,822 | 0.656796 | 593,690 |
| forge_selfplay_029 | 10,000,000 | 4,299,090/3,090,579/2,610,331 | 0.656629 | 596,762 |
| forge_selfplay_030 | 10,000,000 | 4,326,716/3,036,939/2,636,345 | 0.655460 | 598,952 |
| forge_selfplay_031 | 10,000,000 | 4,323,910/3,056,144/2,619,946 | 0.655599 | 594,339 |
| forge_selfplay_032 | 10,000,000 | 4,338,954/3,053,431/2,607,615 | 0.656325 | 584,713 |
| forge_selfplay_033 | 10,000,000 | 4,333,660/3,057,427/2,608,913 | 0.655859 | 582,136 |
| forge_selfplay_034 | 10,000,000 | 4,323,881/3,071,041/2,605,078 | 0.655007 | 588,026 |
| forge_selfplay_035 | 10,000,000 | 4,308,507/3,051,584/2,639,909 | 0.655656 | 578,263 |
| forge_selfplay_036 | 10,000,000 | 4,330,049/3,050,424/2,619,527 | 0.655363 | 575,784 |
| forge_selfplay_037 | 10,000,000 | 4,337,637/3,050,955/2,611,408 | 0.655134 | 576,036 |
| forge_selfplay_038 | 10,000,000 | 4,357,815/3,040,016/2,602,169 | 0.655860 | 568,170 |
| forge_selfplay_039 | 3,085,679 | 1,332,102/940,802/812,775 | 0.655717 | 173,690 |

## Absolute score (cp)

Bins are disjoint; each upper bound excludes the preceding bin.

| Upper bound | Rows | Share |
|---|---:|---:|
| <=0 | 8,194,328 | 2.6867% |
| <=20 | 26,002,915 | 8.5256% |
| <=50 | 34,133,173 | 11.1912% |
| <=100 | 45,176,737 | 14.8121% |
| <=200 | 55,465,517 | 18.1854% |
| <=400 | 54,762,133 | 17.9548% |
| <=800 | 45,197,913 | 14.8190% |
| <=1600 | 28,759,989 | 9.4295% |
| <=3000 | 7,306,868 | 2.3957% |

## Zero-based ply

Bins are disjoint; each upper bound excludes the preceding bin.

| Upper bound | Rows | Share |
|---|---:|---:|
| <=20 | 35,333,525 | 11.5848% |
| <=40 | 50,293,840 | 16.4898% |
| <=80 | 91,285,334 | 29.9297% |
| <=120 | 74,691,026 | 24.4889% |
| <=160 | 33,907,788 | 11.1173% |
| <=240 | 16,542,116 | 5.4237% |
| >240 | 2,945,944 | 0.9659% |

## Pieces

Bins are disjoint; each upper bound excludes the preceding bin.

| Upper bound | Rows | Share |
|---|---:|---:|
| <=6 | 30,757,008 | 10.0843% |
| <=12 | 80,465,445 | 26.3822% |
| <=20 | 72,923,350 | 23.9093% |
| <=32 | 120,853,770 | 39.6242% |

## Observed outcomes by signed STM score

Position-weighted counts are correlated within games. They are not independent
game samples, calibrated probabilities, confidence intervals or Elo evidence.

| Disjoint score bin | Loss | Draw | Win | Unknown |
|---|---:|---:|---:|---:|
| <=-800 | 18,060,199 | 41,596 | 633 | 0 |
| <=-400 | 21,795,163 | 952,458 | 31,998 | 0 |
| <=-200 | 22,914,812 | 4,215,177 | 414,604 | 0 |
| <=-100 | 14,826,006 | 11,355,280 | 1,600,162 | 0 |
| <=-50 | 8,690,975 | 11,145,076 | 2,734,274 | 0 |
| <=0 | 9,097,212 | 22,492,300 | 6,164,823 | 0 |
| <=50 | 5,953,879 | 15,742,965 | 8,365,500 | 0 |
| <=100 | 2,920,579 | 11,305,040 | 8,513,328 | 0 |
| <=200 | 1,748,314 | 11,586,705 | 14,539,773 | 0 |
| <=400 | 461,621 | 4,385,867 | 22,463,310 | 0 |
| <=800 | 35,772 | 1,066,566 | 21,381,493 | 0 |
| >800 | 692 | 40,360 | 17,955,061 | 0 |

Full source hashes, counters, raw correlation moments and profile identities are
in corpus_report.json. Audit reservoirs are evidence only, never recipe inputs.
