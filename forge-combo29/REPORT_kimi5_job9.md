# kimi5 job 9 report - the node-level block's eight literals as options, and what each does to the S14 search

K0, K-stop, K1, K2: ALL MET (bench 312866/862329/3024920 + perft 4865609 on the patched build; the unpatched exe
stopped the runner on `info string unknown option NullStaticSlope`; the four known sums matched to the node and all
32 option-at-default runs were identical per position on 200/200 and 353/353; NullVerifyDepth 15 and 64 equalled the
base on 200 of 200).
Sentence 1: on G, per unit of its value, ProbcutReduction moves the tree most (+-1.4-1.8 % per ply step) but both its
intervals include 1.0; among settings whose 95 % intervals exclude 1.0 the null static gate moves the tree most, per
unit and overall: NullStaticSlope +15.9 % at 0 / -9.2 % at 48 per 24 units, NullStaticBase +18.7 % at 400 / -7.7 % at 0.
Sentences 2 and 3: nine setting-set pairs flip best moves in >10 % of positions while moving the tree <5 %
(NullStaticSlope 48 on O: 27.0 % of moves at +1.2 % tree; ProbcutImproving 0/100 on both sets 12.2-15.6 % at <=1.3 %
tree) - those are where a match can tell something a tree size cannot; NullVerifyDepth 8 changes 199 of 200 searches
on O and 342 of 353 on G at all, yet flips only 1/200 and 25/353 best moves and grows the tree 0.25 %/1.13 %:
verification fires nearly everywhere, costs almost nothing, and almost never changes the decision.

## Step 0 (the honesty check, base exe /tmp/forge_base, sha256 e06310ec..., one fresh process per line)
bench 11 = 312866 (step0_bench11.txt), bench 13 = 862329 (step0_bench13.txt), bench 16 = 3024920
(step0_bench16.txt), go perft 5 = 4865609 (step0_perft5.txt). All four match the known numbers.

## Step table
| step | done | evidence | result |
|---|---|---|---|
| claim/prediction | done | prediction.txt (commit "kimi5 job 9 prediction") | 13 settings predicted with kill ranges |
| Part 2 patch | done | NodeLiterals.patch.txt (114 lines, `diff -u`, applies `patch -p1 --fuzz=0` clean) | 8 options, defaults = today's literals; comment 1719 names NullVerifyDepth; literals_not_options.txt lists the rest |
| builds | done | /tmp/forge_base e06310ec..., /tmp/forge_patched f0daf1b6... (g++ 13.3, Release, -march=x86-64-v4) | two distinct binaries |
| K0 | done | k0_bench11/13.txt, k0_perft5.txt | 312866 / 862329 / 4865609 on the patched build |
| K-stop | done | kstop_input.log, kstop_stdout.txt | base exe: runner stopped on `info string unknown option NullStaticSlope` |
| K1 sums | done | rows/k1_def_O, k1_def_G, k1_s14_O, k1_s14_G (.json/.meta) | 12573318 (18407/25756/64000) / 22128265 / 9500069 (41311/24872/28574) / 18466239 - all match |
| K1 identity | done | rows/k1def_*, rows/k1s14_* (32 runs), agg_part4.txt | each option at its default = the no-option run per position, 200/200 and 353/353, defaults and S14 |
| K2 | done | rows/k2_v15_O, rows/k2_v64_O, agg_part4.txt | both equal the base per position on 200/200 |
| base AGAIN | done | rows/r2_s14_O, rows/r2_s14_G | identical per position to k1_s14_O/G - the runner carries no state |
| Part 3 step 5 | done | rows/s_*_O/G (26 runs), driver.log (66/66, fails=0) | all 13 settings on both sets measured |
| Part 4 table | done | agg_part4.txt (printed by `python3 agg_j9.py /tmp/j9/out`, the one committed command; agg_j9.py) | 66 rows files read, 200+353 positions per arm; bootstrap 10000 resamples seed 9 |

## Findings (each with its source line; show again: `grep -n "<literal>" /tmp/base/forge-combo29/src/search.cpp`, runs in rows/)
1. The null static gate (1694 `static_eval >= beta - 24*depth + 180`) is the tree's biggest lever of the eight.
   Slope 0 (flat beta+180 admission): O 1.1000 [1.0438,1.1620], G 1.1585 [1.0975,1.2227]. Slope 48: G 0.9083
   [0.8675,0.9499] but O 1.0118 [0.9605,1.0663] - the SIGN flips between the sets on O's quiet positions.
   Base 400: O 1.0942, G 1.1871 (both intervals exclude 1.0). Base 0: O 0.9829, G 0.9230.
2. NullEvalRedMax (1702 cap 3) is nearly INERT upward at depth 12: value 6 changes 0/200 searches on O and 3/353
   on G (factor 1.0000 both) - (eval-beta)/200 exceeds 3 almost never at these depths. Value 0: O 1.0019, G 0.9857,
   best moves 4/200 and 26/353.
3. NullVerifyDepth 8 (1724/1725): 199/200 (O) and 342/353 (G) searches change at all, but the tree grows only
   1.0025/1.0113 and best moves flip 1/200 (O), 25/353 (G). At S14 the verification search is shallow
   (depth - 5 - depth/3 - bonus), so it fires cheaply and its refusals are rare.
4. ProbCut's three knobs move the tree 1-2 % in EITHER direction with no interval excluding 1.0, yet flip best
   moves in 12-16 % of positions: ProbcutImproving 0/100 (1746), ProbcutReduction 3/5 (1767), ProbcutTtSlack 0
   (1748). ProbcutStoreReduction 0 (1773/1775): O 0.9916, G 1.0026, only 6/200 and 26/353 moves.
5. Suspicion, not proven: ProbcutTtSlack 0 GREW the tree (O 1.0093, G 1.0133) where I predicted a small shrink -
   at depth 12/Hash 16 running ProbCut more often may cost more than it saves; intervals include 1.0, so this is a
   lean, not a fact. Also unproven: whether NullStaticSlope 48's O-set growth (1.0118) is real - its interval is wide.

## Prediction accounting (Part 1 vs measured, O set)
Held: slope 0 (1.1000, edge of [1.01,1.10]), base 0, base 400, evalred 0, improving 0, reduction 5, ttslack 0,
store 0, evalred 6 (exactly 1.0000, boundary). Died: slope 48 (1.0118 outside [0.93,1.005] - sign wrong on O),
verify 8 (1.0025 vs [1.02,1.18] - 30x too big, and bm>20 wrong: 1/200), improving 100 (1.0113 vs [0.96,1.005]),
reduction 3 (1.0241 vs [0.94,1.005]). Lesson: I overestimated how much a shallow verification costs and how often
it refuses; the S14 null reduction (5 + depth/3 + bonus) makes everything at these depths shallower than my model.

## From my colleagues
Read: deepseek5-work NOTES (through stand5/cross4) and glmflash5 NOTES (through job 17) on
cursor/glmflash5-work-cb5c (the ref for-fable-and-opus/glmflash5-work does NOT exist - said so in my job-8 note).
Applied: deepseek5's S3 proof (ucinewgame+isready before every go is sufficient) is my runner's protocol; the
S14 bridge his job 26/27 verified is this job's measuring plane. glmflash5's fabricated-table fault is why every
table here is printed by ONE committed command with an identity line; his "tree says nothing about strength" is
why sentence 2 flags match candidates instead of reading strength from factors. Newest reports seen:
REPORT_deepseek5_job29.md, REPORT_glmflash5_job17.md (listed; the notes carried the content I used).

## What I did NOT do
No strength claims (per the job: games decide, on the PC). The per-search full info logs (66 files, ~60 MB) are
not committed (job-8 practice: json rows + metas only); they are reproducible by driver.log + jobs.txt + run_j9.py.
Job 10 (qsearch internals) untouched - it is the NEXT run's job, not this one's. K3's six starred settings are
measured and committed here; Fable's own rows are his comparison, not mine to make.

## What I am NOT sure about
The O/G sign flip of NullStaticSlope 48 (intervals wide on O). Whether NullEvalRedMax 6's 3 changed searches on G
are the cap binding or noise - they are real per-position differences, but 3/353 says the cap ~never binds at
depth 12, so a tuner should not expect resolution there. ProbcutTtSlack 0's direction. The bootstrap treats
positions as independent; opening-set correlations (O is 200 related openings) may narrow the true intervals.

## A better way
Sentence-2 hunting (options that flip moves without moving the tree) would be sharper with a paired per-position
SIGN test (Wilcoxon signed-rank on per-position node ratios) instead of the sum-ratio bootstrap: several options
change 170-200 of 200 searches' node counts while the sum moves <1 %, and a sign test on the per-position ratios
would say whether that drift is one-sided long before a match is affordable. Check: apply both methods to this
job's committed rows (they are all in rows/) and compare interval widths on NullEvalRedMax 0, where the sum ratio
is 1.0019 but 172/200 positions moved.

## Last command before the commit (pasted as required)
`git status --short` (run after every evidence file was in place; REPORT_kimi5_job9.md itself and the last
stamps.txt lines came after this capture):
```
 M forge-combo29/tests_kimi5_job9/stamps.txt
?? forge-combo29/tests_kimi5_job9/NodeLiterals.patch.txt
?? forge-combo29/tests_kimi5_job9/agg_j9.py
?? forge-combo29/tests_kimi5_job9/agg_part4.txt
?? forge-combo29/tests_kimi5_job9/driver.log
?? forge-combo29/tests_kimi5_job9/first200.fens
?? forge-combo29/tests_kimi5_job9/jobs.txt
?? forge-combo29/tests_kimi5_job9/k0_bench11.txt
?? forge-combo29/tests_kimi5_job9/k0_bench13.txt
?? forge-combo29/tests_kimi5_job9/k0_perft5.txt
?? forge-combo29/tests_kimi5_job9/k1_s14_O_input.log
?? forge-combo29/tests_kimi5_job9/kstop_input.log
?? forge-combo29/tests_kimi5_job9/kstop_stdout.txt
?? forge-combo29/tests_kimi5_job9/literals_not_options.txt
?? forge-combo29/tests_kimi5_job9/opt/
?? forge-combo29/tests_kimi5_job9/rows/
?? forge-combo29/tests_kimi5_job9/run_j9.py
?? forge-combo29/tests_kimi5_job9/set_G.epd
?? forge-combo29/tests_kimi5_job9/step0_bench11.txt
?? forge-combo29/tests_kimi5_job9/step0_bench13.txt
?? forge-combo29/tests_kimi5_job9/step0_bench16.txt
?? forge-combo29/tests_kimi5_job9/step0_perft5.txt
```
`ls forge-combo29/tests_kimi5_job9`:
```
agg_j9.py
agg_part4.txt
driver.log
first200.fens
jobs.txt
k0_bench11.txt
k0_bench13.txt
k0_perft5.txt
k1_s14_O_input.log
kstop_input.log
kstop_stdout.txt
literals_not_options.txt
NodeLiterals.patch.txt
opt
prediction.txt
rows
run_j9.py
set_G.epd
stamps.txt
step0_bench11.txt
step0_bench13.txt
step0_bench16.txt
step0_perft5.txt
```

## Model
kimi-k3 (Kimi K3, run name kimi5).

times: see stamps.txt (in the job folder; every line written by a command).
