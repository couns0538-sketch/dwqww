# R3-3 srand check

Every srand in GATE_PROPOSALS.md is new: it is not among the srands or seeds used or reserved in the searched paths (section 2: every PC gate, queue and planning location, all agents' scratch, every git branch and Sol's commit), and its decimal string does not occur anywhere in the scanned text (a stricter test than "not a known srand"). Everything was read-only; PC files were read in place or through copies in scratch.

## 1. How the values were chosen

- Candidates: `value(id, k) = 300000000 + uint32(SHA-256("forge-r3-gates/2026-10-27/<id>/<k>")[0:4]) mod 1700000000`, k = 0..3 per entry (`tools/make_cands.py`). This is the PC's own fresh-srand range (`common_autonomy.ps1` Fresh-Srand: 300000000 + uint32 mod 1700000000), so the values look like every recent gate's.
- Rule (`tools/choose_srands.py`): take the first candidate that (a) occurs in no scanned file or git blob as a digit-bounded 9-10 digit token, (b) is not in the set of used values below, (c) is not a srand or openings start in the live manifest copy. All 35 chosen values are the k = 0 candidates: no candidate was rejected.
- 6 spare values (R3-SPARE-01..06) were checked the same way for later sub-gates or re-runs by hand; the runner draws its own random srand for automatic retries and confirm gates.

| entry | srand | openings start |
|---|---:|---:|
| R3-01 | 603959610 | 390001 |
| R3-02 | 409099654 | 393001 |
| R3-03 | 1141420168 | 396001 |
| R3-04 | 942416262 | 399001 |
| R3-05 | 1201666468 | 402001 |
| R3-06 | 537949450 | 405001 |
| R3-07 | 1007365962 | 408001 |
| R3-08 | 1063419569 | 411001 |
| R3-09 | 350087856 | 414001 |
| R3-10 | 341349245 | 417001 |
| R3-11 | 450325920 | 420001 |
| R3-12 | 981103760 | 423001 |
| R3-13 | 647180553 | 426001 |
| R3-14 | 306251564 | 429001 |
| R3-15 | 1520453741 | 432001 |
| R3-16 | 303395056 | 435001 |
| R3-17 | 1816646849 | 438001 |
| R3-18 | 1851462305 | 441001 |
| R3-19 | 759711708 | 444001 |
| R3-20 | 1404525608 | 447001 |
| R3-21 | 938441364 | 450001 |
| R3-22 | 1199191854 | 453001 |
| R3-23 | 1127627755 | 456001 |
| R3-24 | 1602272685 | 459001 |
| R3-25 | 1153287325 | 462001 |
| R3-26 | 461303726 | 465001 |
| R3-27 | 1084240214 | 468001 |
| R3-28 | 1158455101 | 471001 |
| R3-29 | 794186013 | 474001 |
| R3-SPARE-01 | 652265577 | - |
| R3-SPARE-02 | 315502647 | - |
| R3-SPARE-03 | 412603278 | - |
| R3-SPARE-04 | 695967658 | - |
| R3-SPARE-05 | 1161992909 | - |
| R3-SPARE-06 | 1290988240 | - |

## 2. Paths searched

**File system** (`tools/srand_scan.py fs`; text files up to 8 MiB; `.git`, `.venv`, `__pycache__`, `selfplay_out` and engine_io logs skipped): 221921 files, 2389 MB.

| root | files | MB | what is there |
|---|---:|---:|---|
| `C:/Users/Administrator/.claude/projects/D--grok-pc-data-dwqww/memory` | 5 | 0 | session memory notes |
| `C:/Users/Administrator/Downloads` | 118 | 7 | depth 1 only: the user's downloaded briefs (TEST_PLAN_ALL_IDEAS_20261026.md = OPUS_TEST_PLAN.md byte for byte, CR notes, job prompts) |
| `C:/Users/Administrator/grok-pc` | 27968 | 1253 | queue runner + manifest + every backup/staged copy (`forge_push\autorestart\forge_gates.json*`, `forge_queue*.ps1`), `forge_queue_state.json`, `forge_queue.log`, `FORGE_RESULTS.csv/.md`, `chain_gates*.ps1/.log`, autonomy scripts, older run logs and archives |
| `D:/grok-pc-data` | 12466 | 150 | gate folders `forge_push\gate*\` (RUN_INFO.json, RESULT.md, config.json, partial_* subfolders), `FORGE_RESULTS*`, `dwqww\*.md` (OPUS_TEST_PLAN.md, SOL_LEFTOVERS_FOR_CLAUDE.md, OPUS_PROMPT.md), `.claude\skills` (forge-gate-stats etc.), `.claude\worktrees` (incl. the AL1 lock package 6_gate/7_history) |
| `F:/forge_push` | 51 | 2 | gate folders created since 2026-10-27 (gate39-gate47: RUN_INFO.json, RESULT.md, config.json) |
| `F:/opus_scratch` | 181313 | 977 | all agents' scratch and worktrees (job REPORTs, Sol inventory/status copies, R3 jobs in progress); excluded: this job's own scratch `r3\R3-3`, build export `build\r3_R3-3`, job folder `worktrees\opus_r3_gates\opus_r3\R3-3` |

189 text files over 8 MiB were not read: self-play data dumps, sensor CSVs, engine I/O logs and disassembly/MSan logs (no gate srand is written to such files; fastchess does not send its seed to engines).

**Git** (`tools/srand_scan.py git`): every branch of the repository, 388 local and origin refs (the other R3 agents' branches fetched again on 2026-10-27 before the scan), plus Sol's commit `17aa0cae` (branch forge/sol-pack31-20261025; its ref was left out of the batch list so that its own blobs are read only with `git show 17aa0cae:<path>`, the PC rule for Sol's branch). Blobs were de-duplicated: 12492 unique text blobs read with `git cat-file --batch`, 3275 blobs that exist only in Sol's tree read with `git show`; 336 MB in total.

Not searched: conversation transcripts of other sessions (`~\.claude\projects\*.jsonl`; they also contain this job's own candidate list) and binary files.

## 3. Used values

Extraction (`srand_scan.py`): JSON `"srand"`/`"seed"` fields, fastchess `-srand N`, `srand=N` / `srand: N`, prose ("srand 1556281522", "srand from the test plan (G-B3: 1162618901)"), PowerShell `$srand…=N`, `--seed N`, and every integer in a Markdown, pipe or CSV table column whose header names srand or seed. Loose matches (training seeds, counts near the word "seed") are kept: a larger exclusion set only makes the check stricter.

| source category | distinct values |
|---|---:|
| other | 629 |
| queue manifest forge_gates*.json (live + backups) | 158 |
| chain_gates*.ps1 / *.log (older runners) | 79 |
| FORGE_RESULTS / GATE_RESULTS ledgers | 75 |
| job REPORT.md / IDEA_SOURCE.md | 72 |
| gate RUN_INFO.json | 63 |
| fastchess config.json (seed) | 58 |
| gate RESULT.md | 58 |
| queue state / queue log | 39 |
| test plans (OPUS_TEST_PLAN / TEST_PLAN_ALL_IDEAS) | 18 |
| SOL_LEFTOVERS / OPUS_PROMPT | 4 |

Cross-checks (each value below is inside the used set):
- live manifest `forge_gates.json` (copy): 128 gates, 128 distinct srands, openings starts up to 366001;
- queue state: current gate `gate47_packf2_c80_vs_h256e12`, srand 20261133;
- `FORGE_RESULTS.csv` (copy): 57 srands; `forge_queue.log` (copy): 37 "srand N" values (incl. random retry srands);
- OPUS_TEST_PLAN.md / TEST_PLAN_ALL_IDEAS_20261026.md: the 18 reserved srands 1254856699, 869014820, 958591904, 507544535, 1065932896, 881917307, 885637590, 2115600525, 1162618901, 1894620847, 1325124880, 739447198, 1352390606, 2139766817, 1319449387, 610323748, 113016036, 817455375;
- job REPORTs: the test-plan srands quoted by O5 (1162618901), O8 (113016036), C5 (817455375), S-A2 (869014820) and S-A4 (507544535) are in the set; SOL_LEFTOVERS_FOR_CLAUDE.md names no further value; the forge-gate-stats skill names none. (O1's self-play seeds 9901-9905 have 4 digits, below the 6-digit minimum of the extraction and far from the 9-10 digit values chosen here.)

**srand-context values (406):**

```
0, 1, 11, 12, 21, 22, 23, 69, 77, 123
169, 230, 390, 981, 1024, 1031, 1051, 1061, 1112, 1234
1300, 1301, 1302, 1311, 1312, 1321, 1401, 1402, 1500, 1501
1502, 1590, 1601, 1602, 1611, 1701, 1702, 1750, 1801, 1802
1823, 1901, 1902, 2022, 2026, 2582, 2601, 2650, 2701, 2901
3001, 3038, 3101, 3102, 3143, 3401, 3525, 3624, 3964, 4000
4201, 5501, 5601, 5701, 5800, 5801, 5888, 5901, 6213, 6424
6600, 6605, 7001, 7408, 8000, 8177, 8726, 8819, 8976, 9006
9388, 9487, 9498, 9501, 9551, 9576, 9579, 9602, 9659, 9722
9733, 9767, 9801, 9805, 9868, 9901, 10000, 11901, 21704, 25219
27641, 36001, 36447, 36837, 39001, 42001, 45001, 45906, 48001, 51001
54001, 56790, 57001, 60001, 63001, 66001, 69001, 72001, 75001, 78001
81001, 84001, 84872, 87001, 90001, 93001, 96001, 98828, 99001, 99916
100000, 102001, 105001, 108001, 110225, 111001, 114001, 116300, 117001, 117247
120001, 123001, 124112, 124866, 126001, 130866, 132001, 135001, 138001, 141001
144001, 147001, 150001, 153001, 156001, 159001, 162001, 165001, 168001, 169011
171001, 174001, 177001, 312866, 330610, 401121, 425207, 456743, 858175, 862329
987308, 991785, 2519734, 2760596, 3024920, 3317599, 4101413, 4865609, 5840451, 6307193
6911538, 7456397, 9227945, 9564588, 12389307, 20261003, 20261009, 20261019, 20261023, 20261024
20261025, 20261026, 20261027, 20261028, 20261029, 20261030, 20261031, 20261101, 20261102, 20261103
20261104, 20261105, 20261106, 20261107, 20261108, 20261109, 20261111, 20261112, 20261113, 20261114
20261115, 20261116, 20261117, 20261118, 20261119, 20261120, 20261121, 20261122, 20261123, 20261124
20261125, 20261126, 20261127, 20261128, 20261129, 20261130, 20261131, 20261132, 20261133, 20261134
20261135, 20261136, 20261137, 20261138, 20261139, 20261140, 20261141, 20261142, 20261143, 20261144
20261145, 20261146, 20261147, 20261148, 20261149, 20261150, 20261151, 20261152, 20261153, 20261154
20261155, 20261156, 20261157, 20261158, 20261159, 20261160, 20261161, 20261162, 20261163, 20261164
20261165, 20261166, 20261167, 20261168, 20261169, 20261170, 20261171, 20261172, 20261173, 21638970
30782965, 34048354, 57701360, 85812173, 113016036, 193690690, 252550784, 300559119, 309521385, 344808634
374715874, 393391667, 405318834, 438935695, 440248183, 443871355, 462295914, 468953754, 475951932, 479262769
480620746, 507544535, 559254645, 559341020, 578451693, 610323748, 624700778, 660755887, 670395163, 700000001
700000002, 700000003, 700000004, 700000005, 700000006, 705392668, 715838599, 739447198, 817455375, 855901636
869014820, 870486763, 874150601, 881917307, 885637590, 899825575, 903841213, 931754974, 932140328, 932669363
943854542, 944005444, 958591904, 961929541, 973474437, 974255890, 999999991, 1000951531, 1050264640, 1057512028
1058230796, 1065932896, 1081675020, 1109753703, 1123039422, 1137667775, 1162618901, 1166240132, 1180590640, 1182725909
1228375209, 1254856699, 1262762038, 1287588297, 1295508054, 1319449387, 1325124880, 1327031726, 1352390606, 1357468390
1369309049, 1401777973, 1460372917, 1470520045, 1472976388, 1494339672, 1513640692, 1514304005, 1524622280, 1535500495
1548476429, 1549429135, 1556281522, 1568862887, 1576260791, 1585072642, 1602516321, 1680615474, 1699032863, 1721455178
1731846293, 1744548477, 1754428259, 1759272485, 1763995934, 1827529024, 1838728869, 1843331874, 1845839092, 1847387023
1867938095, 1882198661, 1894620847, 1910442104, 1910442204, 1910449999, 1921068996, 1979975444, 1983003762, 1985713414
1994807395, 2026100908, 2026101956, 2115600525, 2139766817, 40509722120, 40510697858, 40515643380, 40517374786, 40517374833
40521059492, 122228771232, 122228771391, 122228771495, 896137891531, 999999999999
```

**seed-context values (261; training/tool seeds, excluded as well):**

```
0, 2, 3, 4, 5, 6, 7, 8, 10, 13
14, 15, 16, 17, 25, 27, 49, 89, 99, 101
102, 103, 198, 200, 329, 502, 512, 513, 701, 721
12345, 100003, 1000003, 8675309, 12345678, 18675309, 20261006, 20261012, 20261013, 20261017
20261020, 20261021, 20261022, 20261927, 20261977, 20262007, 20262027, 20262028, 20262047, 20262057
20262067, 20262068, 20262077, 20262087, 20262097, 20262117, 20262137, 20262147, 20262217, 20262227
20262228, 20262247, 20262257, 20262267, 20262268, 20262277, 20271023, 31832729, 38609089, 40401860
40454647, 41502175, 54285825, 56275426, 81025001, 83982608, 85959966, 100000000, 101490761, 105182123
123456789, 130422461, 154856227, 160453547, 190706054, 191913961, 208462919, 211243867, 214980671, 216660173
216856421, 219601405, 220237498, 226612830, 241870919, 261340104, 268463240, 268895033, 279760011, 285366803
301537327, 322989999, 347450470, 356755647, 359222358, 376109287, 380097908, 384908324, 390123459, 414601552
422876745, 424356116, 430246481, 482127004, 490865527, 493737543, 494378944, 494499378, 517622717, 569446919
589316564, 605331677, 641343066, 644491842, 671221681, 674355926, 697538829, 721765377, 726724826, 726906327
764476583, 767093269, 782804761, 797591620, 804413134, 810031704, 813545014, 817424033, 833713338, 837662441
839166659, 839438204, 846177632, 863658898, 864364200, 865797948, 885018639, 924234855, 944282490, 958867423
1007037667, 1024193244, 1029615272, 1029921189, 1040914994, 1055632042, 1060430292, 1061239577, 1077375846, 1098466726
1110517379, 1111920197, 1126207722, 1165162038, 1166094531, 1178270043, 1188361283, 1197712714, 1201855108, 1206495802
1206741068, 1209682082, 1222252960, 1226633911, 1234567890, 1252684088, 1254159655, 1260336821, 1269450451, 1273510054
1274758556, 1302943207, 1317313384, 1318555982, 1371500626, 1373675033, 1374304053, 1416442513, 1424244880, 1432985819
1461999443, 1496883534, 1508023266, 1508617024, 1528175904, 1542935983, 1547052691, 1550709854, 1562332665, 1577566522
1592213980, 1595619368, 1652764040, 1694346063, 1707926020, 1719649740, 1729169361, 1740732229, 1758773109, 1772167523
1786049149, 1793405170, 1837678193, 1858297074, 1868414008, 1913797901, 1937625945, 1938475555, 1968429903, 1986974303
2026102301, 2026102302, 2026102303, 2026102648, 2026102733, 2026102734, 2026102735, 2026102736, 2026102737, 2026102738
2026102742, 2026102743, 2026102744, 2026102745, 2026102746, 2026102747, 2026102748, 2026102749, 2026102750, 2026102751
2026102752, 2026102753, 2026102848, 2026102849, 2026102948, 2026102949, 2026103048, 2026103049, 2057382236, 2718183590
3134027055, 3894723670, 116401669102, 202610263300, 202610263301, 202610263302, 202610263303, 202610263304, 202610263305, 515592365382
652400934700
```

## 4. Result

- Literal hits of the 140 candidates: file system 0, git 0.
- Every chosen srand is unique within the proposals, absent from the used set, absent from the manifest srands and openings starts, and occurs nowhere in the scanned text.
- Finding: `common_autonomy.ps1` Used-Srands (the QA helper that picks fresh srands) reads RUN_INFO files only under `D:\grok-pc-data\forge_push`; since 2026-10-27 new gate folders are on `F:\forge_push`, so srands recorded only there (e.g. random retry srands) are outside its set. Its manifest + FORGE_RESULTS.csv + queue-state sources still cover first-attempt srands.
- To protect the chosen values, install the entries (or at least their srands) into the manifest before other proposals pick srands; the runner's confirm generator excludes manifest srands only.
