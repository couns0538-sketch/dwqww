# REPORT_kimi5_job11 — LmrFine: fine-grained late-move reductions behind a switch (text patch)

Claimed and done by this same run (no takeover; no younger claim existed). No pull request opened.

(1) Step 0 met (bench 11 = 312,866; bench 13 = 862,329; bench 16 = 3,024,920; `go perft 5` = 4,865,609;
all ten new options in the `uci` list with the required defaults). I1–I4 met: node count AND best move
equal on every position (200 of 200 on O, 353 of 353 on G, against my job-8 rows for nodes and my job-10
rows for nodes and best moves, and across the switch). C1 fired: 13,036,988 ≠ 9,500,069, differing on all
200 positions. C2 fired: 9,500,069, 200 of 200 equal, best moves included.
(2) T1/I2 (fine history, round-to-nearest): O 1.0705 [1.0159, 1.1320], G 1.0435 [0.9922, 1.0992].
T2/I2 (round down): O 1.2542 [1.1908, 1.3231], G 1.2429 [1.1772, 1.3112] (2,000 bootstrap resamples over
positions, seed 11). T2's tree is the larger on both sets, as predicted from floor ≤ round at every node.
(3) Largest |history| a quiet move can have at the reduction site: 57,344 — `src/search.cpp:1829`
`history = quiet_history(board, ss, move)`; `quiet_history_sum` (lines 260–271) sums the main row plus
cont1, cont2 and half of cont4, each entry a `std::int16_t` held within ±`HistoryMax` = 16,384
(line 175; the gravity update lines 246–248 cannot exceed it from 0), so |history| ≤ 16,384 × 3.5 = 57,344.
Then |history| × 1024 ≤ 58,720,256 ≪ 2³¹−1 = 2,147,483,647: `history * 1024` cannot overflow an int.

`LmrFine.patch.txt` sha256: **f7bf3f4363220440dfdd3419805f14cd90a094ad1cc296bd00d9b9911d0406c0**
(unified diff against 6b98f217, `src/search.cpp` only; applies with `patch -p1 --fuzz=0` from the repo
root; dry-run and real application produced a tree identical to the hand-edited one; the built binary came
from the patch-applied tree, not from the hand edit).

## Step 0 — pins and option list (raw files)

| check | known | got | raw file |
|---|---|---|---|
| bench 11 | 312,866 | 312,866 | `tests_kimi5_job11/k0_bench11.txt` |
| bench 13 | 862,329 | 862,329 | `k0_bench13.txt` |
| bench 16 | 3,024,920 | 3,024,920 | `k0_bench16.txt` |
| go perft 5 | 4,865,609 | 4,865,609 | `k0_perft5.txt` |
| uci list | 10 new options, defaults 0/0/512/1024×6/2048 | all ten as required | `k0_uci.txt` |

Build: base 6b98f217 (plain) + the patch, g++ 13.3.0 (`-DCMAKE_CXX_COMPILER=g++`: `/usr/bin/c++` is clang
here and clang cannot link libstdc++ on this machine — the same failure job 8 hit; cmake's first error log
is reproducible by configuring without the override), Release, native (the machine has AVX-512/BMI2).
Exe sha256 in `exe_sha256.txt` and in every `.meta`.

## Step table

| step | done / partly / not done | evidence | result |
|---|---|---|---|
| 0 pins + uci list | done | `k0_*.txt`, `k0_uci.txt` | all met |
| prediction (own commit, before Step 1) | done | `prediction.txt`, commit "kimi5 job 11 prediction" | see accounting below |
| I1 (no option) = K1 | done | `rows/i1_def_*`, `compare_i.txt` | nodes 200/200 + 353/353 vs job-8 rows; nodes+bestmoves vs job-10 rows equal |
| I2 (S14) = K1 under S14 | done | `rows/i2_s14_*`, `compare_i.txt` | 200/200 + 353/353, best moves equal too |
| I3 (LmrFine 1, FH 0, RoundF 0) = I1 | done | `rows/i3_fine_*`, `compare_i.txt` | 200/200 + 353/353 nodes AND best moves |
| I4 (S14 + I3) = I2 | done | `rows/i4_s14fine_*`, `compare_i.txt` | 200/200 + 353/353 nodes AND best moves |
| C1 (… + LmrTtPvF 1025) must differ | done | `rows/c1_*`, `compare_i.txt` | differs on all 200 positions (sum 13,036,988, +37.2 %), 58 best moves changed |
| C2 (… + LmrTtPvF 1023) must equal I2 | done | `rows/c2_*`, `compare_i.txt` | 200 of 200 equal, best moves equal |
| T1/T2 trees + bootstrap | done | `rows/t1_*`, `rows/t2_*`, `boot.txt` | numbers in line (2) above |
| harness positive controls | done | `control_optstop.log`, `control_overwrite.log`, `bad.opt`, `rows/badopt_probe_input.log` | bogus option stops the run (`OPTION REFUSAL: info string unknown option LmrFineBogus`); an existing output file stops the run |

Option arrival proof (job-file rule): the setoption lines as sent, quoted from
`rows/i4_s14fine_O_d12_input.log`: Threads 1, Hash 16, OwnBook false, the fourteen S14 lines, then
`setoption name LmrFine value 1` / `LmrFineHistory value 0` / `LmrRoundF value 0`. Every run's `.meta`
lists its option lines; the runner stops on `unknown option` / `invalid value` (control above).

## Findings (each with file:line and the showing command)

- F1 — The patch is an exact identity at its defaults and at the all-multiples-of-1024 settings:
  `src/search.cpp:1994–2002` (coarse path kept verbatim under `if (tune::LmrFine == 0)`); with every
  F-term a multiple of 1024 and `LmrRoundF 0`, `(f + 0) >> 10` is exact division, so the fine path is
  ply-for-ply the coarse path. Command: `python3 cmp_j11.py rows/i4_s14fine_O_d12.json rows/i2_s14_O_d12.json I4` →
  "nodes 200 of 200 equal; bestmoves 200 of 200 equal" (full set in `compare_i.txt`).
- F2 — C1's direction is the one file 12 corrected: with `LmrRoundF 0`, `f − 1025` floors one ply BELOW
  `f − 1024`, so tt_pv nodes reduce one ply LESS and the tree grows (+37.2 % on O, all 200 positions
  moved, 58 best moves). Command: the C1 line in `compare_i.txt`.
- F3 — Ordering from the code confirmed: floor(f/1024) ≤ (f+512)>>10 everywhere ⇒ T2 reduces never more
  than T1; strictly less for quiets with 1 ≤ h_frac ≤ 512 (history 6…~2821 positive). Measured: T2 > T1
  on O (1.2542 vs 1.0705) and on G (1.2429 vs 1.0435). Evidence `boot.txt`.
- F4 — The fine history clamp ±2048 binds at exactly the same |history| as the coarse ±2 clamp:
  `clamp(history*1024/Div, −2048, 2048)` saturates at |history| = 2×Div (11,286 under S14's 5643; 12,000
  under the default 6000), the same point where `clamp(history/Div, −2, 2)` saturates
  (`src/search.cpp:2002` and the patch's fine line). The fine path adds granularity BELOW the cap, none
  above it — no quiet can gain or lose more than 2 plies to history in either path.
- F5 — Rounding shifts decisions, not just sizes: best moves changed vs I2 = T1 48/200 (O) and 81/353
  (G); T2 61/200 and 90/353. No strength claim (tree job); this is the carrier glmflash5 plays.

## Prediction accounting (prediction.txt, committed 15:51:11Z, untouched)

- T1/I2 on O predicted 1.02, killed below 0.95 or above 1.10 → observed 1.0705: **stands** (inside, above
  the point). T2/I2 on O predicted 1.20, killed below 1.05 or above 1.40 → observed 1.2542: **stands**.
- "T2 makes the larger tree, because floor ≤ round at every node, strict on small positive history":
  confirmed on both sets.

## Suspicions, not proven

- T1 on G: the interval [0.9922, 1.0992] straddles 1.0 — possibly tree-neutral there while O says +7 %;
  a position-mix difference, not measured further.
- The ±2048 clamp can bind in type (|history| up to 57,344 ⇒ h_frac up to ~10,408 under S14) but how
  often it binds in real searches was not counted (no counting build in this job).

## From my colleagues

- deepseek5 (`for-fable-and-opus/deepseek5-work`, tip 731fc80): notes after job 30 (read counter state at
  the moment of the event — the one-stage-late labels) and REPORT_deepseek5_job30.md (killer/countermove
  stages hold 92 % of the history step's depth-1 regrets). Applied: set G verified byte-identical to his
  `tests_deepseek5_job10/set_G.epd` (sha256 af3aefd8…, printed in the run log); my comparisons read
  per-position arrays written at search end, no staged state. His HistExempt patch is for glmflash5's
  chain, not this job.
- glmflash5: the template's branch name `for-fable-and-opus/glmflash5-work` does NOT exist; the real one
  is `cursor/glmflash5-work-cb5c` (tip 0f94531). Read: notes after job 20 / cross 2 / standing 1 (my job-9
  slope ratios confirmed on its B9 to 3–4 decimals; per-engine options belong inside fastchess `-engine`
  blocks) and REPORT_glmflash5_job20.md (my NodeLiterals patch reproduced to the node on three builds).
  Applied: patch made with a/ b/ labels and applied from the repo root with `patch -p1 --fuzz=0`,
  dry-run first — the way its B9 rebuilt my job-9 patch.

## What I did NOT do

No match play and no counting build (neither was asked); no separate G-set magnitude prediction (said so
in prediction.txt); the wave-A retry after my shell-variable mistake reused no partial output (the failed
runs died at argv parsing, before any file was created — verified by the runner's own refuse-to-overwrite
control firing on the completed runs afterwards).

## What I am NOT sure about

Whether per-position best-move identity survives a different compiler/optimization (all numbers here are
g++ 13.3 Release, one machine); whether T1's true ratio on G is above or at 1.0 (interval straddles);
whether the report's G intervals would tighten with job 9's 10,000 resamples (this job fixed 2,000).

## A better way

C1/C2 probe the rounding wiring on ONE subtracting term (tt_pv). One extra 8-second run with
`LmrCutNodeF 2049` (must EQUAL I2: (1024k+2049)>>10 = k+2, same as 2048) and one with `2047` (must
DIFFER: floors to k+1) would prove the same wiring on an ADDITIVE term and catch a sign flip in the
F-table that C1/C2 cannot see. Same recipe, same comparison command; the pair costs under 20 seconds.

times: see stamps.txt

Model: kimi5 — Kimi K3 (Moonshot AI), Cursor cloud agent runtime.
