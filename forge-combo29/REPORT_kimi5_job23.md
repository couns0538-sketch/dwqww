# kimi5 job 23 report — A1 (LmrFine: the reduction in 1/1024 ply, continuous history term) on the PC build

Three plain lines: I was asked to write my own port of the A1 change (the late-move reduction recomputed
in units of 1/1024 ply with a continuous history term, ten new spin options) onto the PC build
(6b98f217 + pc_r15, `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`), prove it is the same code as theirs by
known-answer rows, measure its depth scaling, and count which quiet reductions the fine history term moves.
The port is done and **every known answer of file 23 holds**: all eight Step 0 numbers, all eight depth-12
sums with first-threes, all sixteen row hashes, both identities (i2, i3) exact on 200/200 and 353/353, and
every Step 3 band rule with zero forbidden counts. How sure: node-for-node AND best-move-for-best-move
equality with their rows on 553 positions over four settings; the depth-14 sums and the 553 counter lines
are this run's own raw files.

(1) **Step 0: MET** (on the second build; the first build was the known wrong cmake invocation and its raw
files are kept in `step0_wrongbuild/`). (2) Prediction: **4 rows, 0 KILLED** (all four survive; details below).
(3) Step 1: base, fh, fhr, cn equal their known rows on 200 of 200 O and 353 of 353 G each; i2 and i3 equal
base on 200/200 and 353/353; changed-node positions per ON setting below. (4) Step 2 table below.
(5) Step 3 tables below; 200 + 353 searches summed.

## Step 0 (raw files in `tests_kimi5_job23/step0/`; a fresh process per line)

Build = 6b98f217 + `pc_r15.patch` (swarm file 5 lines 56-2374, sha256
`d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`, re-verified) + my
`LmrFine.pc.patch.txt` (sha256 `0f2dbb1b37eee8080def4b49607571c97f795bcb11b5c0d94605486012203058`,
applies with `patch -p1 -F0`, zero fuzz — round-trip verified against my build tree).
g++ 13.3.0, Release, `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, AVX-512+BMI2 (no FORGE_PORTABLE).
Exe sha256 `3fa2738141ae03a93c0849a88a820e9f5a2c1486d09575316ab1d03e70a21061` (`step0/exe.sha256`).

| settings | bench 11 | bench 13 | bench 16 | go perft 5 |
|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ |
| S14 | 242796 ✓ | 656517 ✓ | – | – |
| PC20 | 278024 ✓ | 587276 ✓ | – | – |

All ten new options in the `uci` list with the file-23 ranges and defaults (LmrFine spin 0..1 def 0;
LmrTtPvF/LmrNotImprovingF/LmrTtCaptureF/LmrGiveCheckF/LmrInCheckF/LmrCutoffAddF spin 0..4096 def 1024;
LmrCutNodeF spin 0..4096 def 2048; LmrFineHistory spin 0..1 def 0; LmrRoundF spin 0..1023 def 0) —
`step0/uci_list.txt`. No `unknown option`/`invalid value` in any Step 0 file. Every setoption line in
`step0/*_input.log`.

**Wrong first build (kept, not deleted):** I repeated job 20's documented mistake — configured with
`-DFORGE_MATE_ALPHA_GUARD=1` (a CMake variable this CMakeLists does not read). Result: `unknown option
MateAlphaGuard`, PC20 bench 278016 / 587268 (8 short of 278024 / 587276) — exactly the job-20 signature.
Raw files in `step0_wrongbuild/` with its README; the corrected build reran into `step0/`. Step 0 did its
job: it stopped me before any measuring on a wrong build.

## Prediction, graded row by row (`tests_kimi5_job23/prediction.txt`, own commit before Step 1, never edited)

| # | guess | kill range | measured | verdict |
|---|---|---|---|---|
| 1 fh/base, d14, G | 1.21 | KILLED outside [1.10, 1.32] | 1.2421 | survives |
| 2 fhr/base, d14, G | 1.02 | KILLED outside [0.90, 1.15] | 1.0654 | survives |
| 3 share of quiet reductions in fh's bands (base, G, d12) | 0.35 | KILLED outside [0.20, 0.55] | 0.3252 | survives |
| 4 share in fhr's moving bands (base, G, d12) | 0.12 | KILLED outside [0.04, 0.25] | 0.1820 | survives |

## Step 1: identities against their port (raw rows in `tests_kimi5_job23/rows/`, checker `check_s1_j23.py`, output `check_s1.txt`)

PC20, `go depth 12`, O = first 200 lines of `UHO_Lichess_4852_v1.epd`, G = set G (353). Row hashes = first
16 hex of sha256 of the values in position order, each followed by one LF.

| setting | O sum (first 3) | G sum (first 3) | row hashes (O n/m, G n/m) | equal |
|---|---|---|---|---|
| base | 8,315,168 (21812/26844/35173) ✓ | 17,611,204 (31779/46086/84457) ✓ | all four ✓ | 200/200, 353/353 |
| fh | 9,869,613 (22929/28167/38486) ✓ | 20,708,347 (45412/81149/83115) ✓ | all four ✓ | 200/200, 353/353 |
| fhr | 8,603,740 (18239/20201/33740) ✓ | 18,522,408 (36172/36206/46941) ✓ | all four ✓ | 200/200, 353/353 |
| cn | 8,443,473 (21882/22404/41424) ✓ | 16,949,824 (40008/45546/67388) ✓ | all four ✓ | 200/200, 353/353 |
| i2 = LmrFine 1 | = base on 200/200 O and 353/353 G (nodes AND best moves) | | | identity holds |
| i3 = LmrFine 1 + LmrRoundF 1023 | = base on 200/200 O and 353/353 G (nodes AND best moves) | | | identity holds |

Positions where an ON setting changes the node count against base (nodes / best moves):
fh: O 200/200 (64), G 352/353 (94). fhr: O 200/200 (58), G 350/353 (87). cn: O 200/200 (48), G 350/353 (90).
i2, i3: 0 everywhere. Every sum, first-three, and hash equals file 23's known answers — my port is the
same code as theirs.

## Step 2: depth scaling (`step2_j23.py`, `step2_table.txt`; depth-12 rows are Step 1's; depth-14 sums differ from depth-12 sums)

| set | depth | setting | nodes | ratio to base [boot95, 2000 resamples over positions, seed 12] | best moves changed |
|---|---|---|---|---|---|
| O | 12 | base | 8,315,168 | 1.0000 | 0 |
| O | 12 | fh | 9,869,613 | 1.1869 [1.1177, 1.2464] | 64 |
| O | 12 | fhr | 8,603,740 | 1.0347 [0.9879, 1.0766] | 58 |
| O | 14 | base | 19,377,109 | 1.0000 | 0 |
| O | 14 | fh | 24,430,655 | 1.2608 [1.1952, 1.3170] | 46 |
| O | 14 | fhr | 20,617,468 | 1.0640 [0.9981, 1.1210] | 51 |
| G | 12 | base | 17,611,204 | 1.0000 | 0 |
| G | 12 | fh | 20,708,347 | 1.1759 [1.1210, 1.2210] | 94 |
| G | 12 | fhr | 18,522,408 | 1.0517 [0.9882, 1.1130] | 87 |
| G | 14 | base | 41,052,503 | 1.0000 | 0 |
| G | 14 | fh | 50,992,706 | 1.2421 [1.1667, 1.3030] | 84 |
| G | 14 | fhr | 43,738,119 | 1.0654 [0.9863, 1.1322] | 82 |

fh's tree grows with depth on both sets (G 1.176 → 1.242; O 1.187 → 1.261); fhr straddles 1 at d12 and
leans bigger at d14 (G 1.0654 [0.9863, 1.1322]). Their net engine at d12: fh 1.212/1.220, fhr 1.036/0.964 —
same direction for fh on the built-in eval here.

## Step 3: what the fine history term moves (counters, observe-only; raw `LMRF` lines in `rows_count/count_{O,G}_d12_full.txt`)

Counting build = 6b98f217 + pc_r15 + `LmrFineCount.pc.patch.txt` (sha256
`2223fe47affe2618e843d485caafca37af8ff73a932e6b0677b576a38b6e9b75`; exe sha256
`3ea70d575eac2b9035eb9dc03d457290a20bb3d121f9db59a3a227b7c689b7a7`). Armed on eligibility: every computed
quiet late-move reduction (today's r exists), counted at the point r exists. One LMRF line per search;
totals by `sum_lmrf.py` over ALL lines (it prints how many it summed: 200 O, 353 G).
**Known answer 1: the counting build counts the same nodes as the plain build** — O 8,315,168 ✓, G 17,611,204 ✓
(`rows_count/count_*_d12.json` vs Step 1 base sums).

Under base, PC20, depth 12 (full tables `step3_O.txt`, `step3_G.txt`):

| set | searches | quiet reductions counted | fh r-1 / r / r+1 / other | fhr r-1 / r / r+1 / other |
|---|---|---|---|---|
| O | 200 | 3,131,227 | 1,046,836 / 2,084,391 / 0 / 0 | 310,229 / 2,647,046 / 173,952 / 0 |
| G | 353 | 7,210,050 | 2,344,514 / 4,865,536 / 0 / 0 | 681,932 / 5,897,833 / 630,285 / 0 |

Every fh r-1 has a positive history; fh never moves a negative or zero history and never gives r+1 or
other. fhr never gives "other"; fhr's r+1 comes only from negative histories. Each form's classes add up
to the reductions counted on both sets. Band splits (each class count checked against the band it must
come from; "outside" is 0 everywhere):

| set | fh r-1: +6..+5642 / +5649..+11285 / out | fhr r-1: +2828..+5642 / +8471..+11285 / out | fhr r+1: -5642..-2822 / -11285..-8465 / out |
|---|---|---|---|
| O | 825,360 / 221,476 / 0 | 223,077 / 87,152 / 0 | 169,534 / 4,418 / 0 |
| G | 1,872,045 / 472,469 / 0 | 498,802 / 183,130 / 0 | 597,479 / 32,806 / 0 |

The answer to the counters' question: on G, **32.5 %** of computed quiet reductions sit in fh's two
r-1 bands (history +6..+11285 minus the 5643..5648 equality gap) — a third of all quiet reductions lose
one ply under fh, which is what makes fh's tree ~18-24 % larger. fhr's moving bands hold **18.2 %** on G
(9.5 % r-1 + 8.7 % r+1); the two directions nearly cancel (1.05-1.07 tree ratios). History zero accounts
for 1,278,588 / 7,210,050 = 17.7 % of G's quiet reductions (untouched by both forms).

## Findings (file and line, PC build = 6b98f217 + pc_r15)

- The reduction's first line (the table value): `src/search.cpp:2257` (`int r = reduction(quiet, depth, move_count);`).
- The quiet-history term: `src/search.cpp:2265` (`if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);`).
- My port inserts the fine recomputation directly after 2265 (`LmrFine.pc.patch.txt`); every later term
  (LmrSignedCorrection 2266+, LmrLateParentRelief, bare-king cap, the reduced-depth clamp) is untouched.
- `history * 1024` in int32 is safe for every realistic history (|h| <= ~2.09M); the exact hash equality on
  553 positions x 4 settings shows no overflow divergence from their arithmetic. Reproduce: `git show` the
  patch, apply on the base, rerun `run_step1.sh 12` and `check_s1_j23.py`.

Suspicions, not proven: none. (The i2/i3 identities and all sixteen row hashes leave no room for a port
difference at these settings; a difference outside LmrFine/LmrFineHistory/LmrRoundF/LmrCutNodeF values
tested here is possible in principle and untested — e.g. LmrTtPvF != 1024 was not run.)

## From my colleagues

- **deepseek5** (branch read this run): notes tail — his stage-one-late counter lesson ("read a state
  variable at the moment the event happens") and his t23 report (`go mate N` misses forced mates because
  LMR/pruning/TT stay active under a mate horizon; the Zobrist key ignores the half-move clock). Applied:
  my LMRF counters read `history` and `r` at exactly the point today's r exists, and his band-arithmetic
  discipline (a planted rule the counter must reproduce) is what Step 3's known bands are — they held to
  the unit. His t23 is on `integrate/combo29-fixes`, another base; nothing in A1 to change for it, but his
  missed-mate mechanism is a warning for any "reduce less" change like fh near mate scores: not tested here
  (fixed-depth node-count rows only).
- **glmflash5**: the branch `for-fable-and-opus/glmflash5-work` does not exist (`fatal: couldn't find
  remote ref`). Nothing to read; said here as instructed.

## What I did NOT do

- No match/Elo measurement (not asked; fixed-depth rows and counters only).
- No runs of the remaining new options off their defaults except cn (LmrTtPvF, LmrNotImprovingF,
  LmrTtCaptureF, LmrGiveCheckF, LmrInCheckF, LmrCutoffAddF untested away from 1024/2048).
- I did not compare my port against job 17's `LmrFine.pc.patch.txt`: file 23 wants a second, independent
  writing, and the sixteen known row hashes already pin mine to theirs. Kept independent on purpose.
- Job 24 (NullCutOnly + TtNodeTypeDepth) is open; it belongs to the next run (lowest open then).

## What I am NOT sure about

- The fhr depth-14 intervals straddle 1.0 on both sets; "fhr is tree-neutral" is not established at d14
  (G 1.0654 [0.9863, 1.1322]).
- Whether fh's r-1 events concentrate in tactical or quiet phases of the tree (the counters split by
  history sign and band only, not by depth or node type).
- The equality gap history 5643..5648 exists arithmetically (fh = today's term there); no event outside
  the bands was seen, consistent with it, but I did not count the gap's population separately (it lands in
  fh's "r" class by construction).

## A better way

Fold the observe-only counters into the SAME build as the port behind one more default-0 option
(e.g. `LmrCount 1`), instead of a second counting binary. Why: Step 3's first known answer ("the counting
build counts the same nodes as the plain build") then holds by construction — same exe, same code path,
counters off — and one build serves Step 0, Step 1 and Step 3, removing a whole class of
wrong-binary mistakes (this run needed two rebuilds already). The cost: the delivered port patch carries
inert counting code. How to check it is better: bench pins and the base/fh/fhr/cn known hashes with the
option at 0 must be byte-identical to today's, and the LMRF totals of this run must reproduce with the
option at 1 (a one-run check on O and G at depth 12).

## Times and model

times: see `tests_kimi5_job23/stamps.txt` (run start 00:00:32Z, claim 00:01:13Z, report commit below).
Model: Kimi K3 (running as "kimi5"). `git status --short` and `ls -R` of the job folder: the last command
before the report commit, in `tests_kimi5_job23/final_ls.txt`.
