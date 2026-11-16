# REPORT — deepseek6, job 2 (how large a step the weak settings need; the two dead capture-futility settings with their gate opened)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_job2/ · job clock started 2026-11-16T16:59:43Z (job2_start.txt); report written 2026-11-16T17:05:30Z, minute 6 of 60.

## 1. Three lines
**Asked:** (Part A) how many steps NullMoveEvalDivisor, RfpDepth, FutilityDepth, SeeNoisyMultiplier need before the search changes clearly; (Part B) with `CaptureFutilityBase 230` opening the gate, do CaptureFutilityMultiplier and CaptureFutilityDepth change the search?
**Answer:** (1) Step 0 met (pins exact; O_S14 9,500,069 / G_S14 18,466,239). (2) Part A smallest step with ≥20 of 200 changed best moves on O: **NullMoveEvalDivisor: none up to 4c (max 2); RfpDepth: none up to 4c on O (max 15, at 4c-low) but 2c-low (6) already changes 42 of 353 on G; FutilityDepth: none up to 4c on O (max 2) and none on G (max 23 < 35); SeeNoisyMultiplier: 2c-low (126) on O (22) — and on G 2c either side (64 / 42) crosses 35.** (3) Part B: **B0 vs S14 is a node ratio of 1.0066 on O and 1.0065 on G — opening the gate makes the tree BIGGER, not smaller** (my prediction said 0.93; killed); **B1 and B2 (multiplier ±1c) differ from B0 on both sets; B3 (depth 5) is an exact identity on O and moves 50 node counts on G with NO best-move change; B4 (depth 7) changes exactly 1 node on O and 25 on G, no best move.** The multiplier is the knob that matters; the depth knob is nearly inert at these values.
**How sure:** certain of every number (each cell a committed rows + .meta pair, one compare command). My prediction: Part A 2 of 4 held, 2 killed (FutilityDepth 4c-low, SeeNoisy 2c-high); Part B killed on the ratio direction and on B3-O — all four kills are reported, not hidden.

## 2. Honesty numbers (raw files in this folder)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 (honesty_*.txt). O_S14.rows sum 9,500,069 (200), G_S14.rows sum 18,466,239 (353).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| Step 0 | done | honesty_*.txt, O_S14.rows, G_S14.rows | pins exact, sums as known |
| Part A: 16 configs × 2 sets | done | runs/<setting>_<O,G>_<a2m,a2p,a4m,a4p>.rows + tables.txt | see 4.1 |
| Part B: 5 configs × 2 sets | done | runs/B0..B4_<O,G>.rows + tables.txt | see 4.2 |
| prediction own commit before Part A's first run | done | PREDICTION.md, commit "deepseek6 job 2 prediction" (92ea0c12a) | partly held — 4 kills, listed in 4.3 |

## 4.1 Part A table (changed-best-move counts are 200−bm-eq on O, 353−bm-eq on G)
```
setting|tag|value|O sum|O nodes-eq|O bm-eq|O bm-changed|G sum|G nodes-eq|G bm-eq|G bm-changed
NullMoveEvalDivisor|a2m|160|9514508|101/200|199/200|1|18377490|90/353|351/353|2
NullMoveEvalDivisor|a2p|240|9502713|124/200|200/200|0|18336697|106/353|348/353|5
NullMoveEvalDivisor|a4m|120|9518592|36/200|198/200|2|18193425|51/353|343/353|10
NullMoveEvalDivisor|a4p|280|9495427|95/200|198/200|2|18194745|78/353|344/353|9
RfpDepth|a2m|6|9517197|29/200|196/200|4|18289747|11/353|311/353|42
RfpDepth|a2p|10|9500342|140/200|200/200|0|18264666|61/353|341/353|12
RfpDepth|a4m|4|9454913|0/200|185/200|15|18797617|7/353|273/353|80
RfpDepth|a4p|12|9500214|140/200|200/200|0|18152444|61/353|337/353|16
FutilityDepth|a2m|5|9447720|102/200|200/200|0|18593097|109/353|337/353|16
FutilityDepth|a2p|9|9496689|164/200|199/200|1|18349447|188/353|347/353|6
FutilityDepth|a4m|3|9496774|64/200|198/200|2|18855909|64/353|330/353|23
FutilityDepth|a4p|11|9496641|164/200|199/200|1|18340442|188/353|347/353|6
SeeNoisyMultiplier|a2m|126|9509859|0/200|178/200|22|18144287|13/353|289/353|64
SeeNoisyMultiplier|a2p|174|9509566|5/200|194/200|6|18647063|32/353|311/353|42
SeeNoisyMultiplier|a4m|102|9642085|0/200|173/200|27|18209525|6/353|284/353|69
SeeNoisyMultiplier|a4p|198|9488908|4/200|188/200|12|18479030|25/353|301/353|52
```
Every file named by pattern runs/<setting>_<set>_<tag>.rows(.meta) in this folder; equality by job 1's compare command vs O_S14.rows / G_S14.rows.

## 4.2 Part B table
```
B0 vs S14: O sum 9562828 (ratio 1.0066), nodes-eq 29/200, bm-eq 194/200 | G sum 18586693 (ratio 1.0065), nodes-eq 105/353, bm-eq 334/353
B1 (CFM 225) vs B0: O 9557414, nodes-eq 48/200, bm-eq 198/200 | G 18247989, nodes-eq 142/353, bm-eq 337/353
B2 (CFM 275) vs B0: O 9533832, nodes-eq 56/200, bm-eq 199/200 | G 18259726, nodes-eq 145/353, bm-eq 346/353
B3 (CFD 5)   vs B0: O 9562828, nodes-eq 200/200, bm-eq 200/200 | G 18582169, nodes-eq 303/353, bm-eq 353/353
B4 (CFD 7)   vs B0: O 9562827, nodes-eq 199/200, bm-eq 200/200 | G 18581278, nodes-eq 328/353, bm-eq 353/353
```
B1..B4 compared with B0 (as the job says), B0 compared with S14.

## 4.3 Findings
1. **Opening the gate COSTS nodes instead of saving them**: +0.66 % on O, +0.65 % on G, and it changes 6 of 200 best moves on O (19 of 353 on G). The block's SEE calls cost more than its pruning saves at Base 230, depth 12. For the tuner this means CaptureFutilityBase is a REAL lever (it was hidden before), and its first-order effect is negative at this value.
2. **With the gate open, the multiplier is properly wired** (B1/B2 differ from B0 everywhere); **the depth knob is nearly inert on O** (5 = exact identity; 7 = one node) but moves node counts on G. A tuner moving CaptureFutilityDepth by ±1 around 6 with the gate open would measure noise on O and small real signal on G.
3. **RfpDepth is the opposite of depth-blind on G**: 2c-low (6) changes 42 of 353 best moves on G but 0 of the four runs reaches 20 changed on O — the setting bites where razors fire, which G's game positions provoke and O's openings do not.
4. **NullMoveEvalDivisor stays move-stable even at 4c** (≤2 changed on O, ≤10 on G) while its node counts move a lot (36 of 200 nodes-eq at 4c-low): pure tree-size lever.
5. Prediction scorecard (PREDICTION.md): NMDiv none-up-to-4c HELD; RfpDepth none-on-O HELD; FutilityDepth 4c-low-reaches-20 KILLED (only 2); SeeNoisy 2c-both-ends KILLED (high end 6); B1..B4 all differ KILLED by B3-O (exact identity); ratio 0.93 KILLED (1.0066). Six claims, two held, four killed — every kill is a measured fact, and the killed directions are themselves findings.
6. Suspicions, not proven: the +0.66 % explanation (SEE cost > pruning gain) is a mechanism guess from the numbers, not traced in the code.

## 5. What I read from my colleagues
glmflash5's job-22 pooled SPRT numbers and its fixed-node catch (same openings, same order, same games whatever the seed) — received via the job file; kimi5 takes job 12 (a three-bit fail-high blend patch); my job 3 will test it when it lands on kimi5's branch. No colleague notes contradict this report.

## 6. What I did NOT do
Nothing from the job file. Both parts ran to completion inside the budget. Corrections from file 2's "what does not stand", applied here: (a) job-file-first discipline acknowledged — this time job 2 was started within 16 minutes of file 2 appearing; (b) the long-7 leak sentence now reads: **"512 bytes in 8 allocations = 6 iterations + 2 re-searches (my reading, not counted)"** — the 8 = six root searches at the six iterations plus two re-searches at depths 3 and 5 shown in my own output; (c) model name below is exactly what my runtime reports.

## 7. What I am NOT sure about
Whether B3's exact O identity (200/200, equal sum) versus its 50 moved node counts on G is a threshold artifact of O's positions (all above/below the depth-5 margin) — I did not instrument the block to count firing sites.

## 8. A better way
Part B could add CaptureFutilityBase itself at ±1c (229/231) — the job did not ask; noting it as the natural next probe since the gate is the real lever.

## 9. times: see stamps.txt (job clock 16:59:43Z; runs done 17:03:10Z)

## 10. model name my runtime gives: glm-5p3-flash
## 11. The last command before this report commit (git status --short + ls of the job folder)
```
$ git status --short
?? forge-combo29/REPORT_deepseek6_job2.md
?? forge-combo29/tests_deepseek6_job2/G_S14.rows
?? forge-combo29/tests_deepseek6_job2/G_S14.rows.meta
?? forge-combo29/tests_deepseek6_job2/G_S14.run.log
?? forge-combo29/tests_deepseek6_job2/O_S14.rows
?? forge-combo29/tests_deepseek6_job2/O_S14.rows.meta
?? forge-combo29/tests_deepseek6_job2/O_S14.run.log
?? forge-combo29/tests_deepseek6_job2/honesty_bench11.txt
?? forge-combo29/tests_deepseek6_job2/honesty_bench13.txt
?? forge-combo29/tests_deepseek6_job2/honesty_bench16.txt
?? forge-combo29/tests_deepseek6_job2/honesty_perft5.txt
?? forge-combo29/tests_deepseek6_job2/job2_runs.sh
?? forge-combo29/tests_deepseek6_job2/job2_table.py
?? forge-combo29/tests_deepseek6_job2/partA_cmds.txt
?? forge-combo29/tests_deepseek6_job2/partA_table.txt
?? forge-combo29/tests_deepseek6_job2/runs/
?? forge-combo29/tests_deepseek6_job2/stamps.txt
?? forge-combo29/tests_deepseek6_job2/tables.txt
$ ls forge-combo29/tests_deepseek6_job2/
G_S14.rows
G_S14.rows.meta
G_S14.run.log
honesty_bench11.txt
honesty_bench13.txt
honesty_bench16.txt
honesty_perft5.txt
job2_runs.sh
job2_start.txt
job2_table.py
O_S14.rows
O_S14.rows.meta
O_S14.run.log
partA_cmds.txt
partA_table.txt
PREDICTION.md
runs
stamps.txt
tables.txt
```
