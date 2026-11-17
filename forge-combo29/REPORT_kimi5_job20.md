# kimi5 job 20 report — A4 (capture history in the two SEE tests; capture futility on) on the PC build

(1) **Step 0: MET** — all eight numbers exact on the A4 build with both new options at their
defaults, and the `uci` list shows both names with the job's ranges. One earlier build of this
run failed it (my flag mistake, see Step 0 below) — caught by Step 0, rebuilt, then met.
(2) **Prediction graded row by row** (file `tests_kimi5_job20/prediction.txt`, own commit
"kimi5 job 20 prediction" at 15:04:59Z before the first Step 1 run at 15:05:14Z, never edited):

| row | guess | kill range | measured | verdict |
|---|---|---|---|---|
| P1 all3/base nodes, G, d14 | 0.950 (smaller) | [0.905, 0.995] | 1.0085 | **KILLED** (the bundle shrank G −3.6 % at d12, GREW it +0.9 % at d14) |
| P2 flag-false share of good captures, gcd32, O, d12 | 0.55 | [0.40, 0.70] | 0.8445 | **KILLED** (far higher) |
| P3 snd32/base nodes, G, d14 | 1.030 (larger) | [1.005, 1.060] | 1.0338 | survives |

(3) **Step 1: every known answer met** (checker `check_s1.py`, output `check_s1.txt`): base
8,315,168 / 17,611,204; cfb230 8,354,110 / 17,566,677; snd32 8,153,620 / 17,928,118; gcd32
8,439,842 / 17,304,549; all3 8,582,039 / 16,979,165 — each with its exact first-three rows, on
O (200) and G (353). Identity: SeeNoisyHistDiv 0 and GoodCaptureHistDiv 0 SENT each equal base
on **200 of 200 O and 353 of 353 G** (nodes AND best move). Positions whose node count changes
vs base (file 21's rule, all well over half): cfb230 163/200 O, 235/353 G; snd32 194/200,
330/353; gcd32 200/200, 333/353; all3 200/200, 338/353.
(4) Step 2 table below. (5) Step 3 tables below, 200 (O) and 353 (G) searches summed per run.
(6) **Step 4: done** — T1 equals job 11's rows on 200/200 O and on 341/341 G of the a0 mask
(nodes AND best move, sums and first-three exact); C1 on 200/200 O.

Three plain lines: I was asked to port the research answer's A4 — SeeNoisyHistDiv (capture
history inside the noisy SEE pruning threshold), GoodCaptureHistDiv (capture history in the
picker's good/bad split, with the picker remembering what its t proved) — onto the PC build,
prove the port against Opus's own rows, scale it in depth, count what the terms do inside, and
run the owed LmrFine states. The port is proven the same code as theirs (every given known
answer exact, plus both at-0 identities per position), the counting build is proven
observe-only position by position, and Step 4 is met in full. How sure: identities exact on
all given answers; two of three predictions died (the depth-14 direction of the bundle, and
how often the picker hands out unproven-good captures).

## Step 0 (raw files in `tests_kimi5_job20/step0/`; a fresh process per line)

Base: 6b98f217 + `pc_r15.patch` (sha256 `d6bd72c531f785f4...`, re-extracted from swarm file 5
lines 56–2374 and re-verified) + `CaptureA4.pc.patch.txt`; g++ 13.3.0, Release,
`-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, AVX-512+BMI2 machine (no FORGE_PORTABLE).
A4 exe sha256 `ab2c7093e913dcd7bbc1215569cc1016ad38a176d7501262eb46115b0ab757c7`
(`step0/exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate`.

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | file |
|---|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ | `step0/none_*.txt` |
| S14 | 242796 ✓ | 656517 ✓ | – | – | `step0/s14_*.txt` |
| PC20 | 278024 ✓ | 587276 ✓ | – | – | `step0/pc20_*.txt` |

`step0/uci_list.txt`: `option name SeeNoisyHistDiv type spin default 0 min 0 max 1024` and
`option name GoodCaptureHistDiv type spin default 0 min 0 max 1024`. Every `setoption` line in
`step0/*_input.log`. At the defaults the patched engine computes exactly today's numbers.

**The build fault Step 0 caught:** my first builds configured `-DFORGE_MATE_ALPHA_GUARD=1` as a
CMake *variable*, which this CMakeLists does not read ("Manually-specified variables were not
used"). MateAlphaGuard was answered `unknown option`, PC20 bench came out 278016 / 587268 (8
nodes short each) on BOTH the plain and the A4 build; none/S14 rows were unaffected (they never
send it). Swarm file 5's recipe is `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`. I deleted the
first run's raw files myself before rerunning (`rm -rf step0`, against the job-17 lesson); the
faulty configuration is regenerated and kept in `step0_wrongbuild/` (same tree, same wrong
invocation, reproduces the same two numbers; its README says so). Both rebuilds from clean build
dirs then gave all eight numbers, on the plain base AND on the A4 build.

## The port (`CaptureA4.pc.patch.txt`, sha256 `b3edc7beff5ef050a60a037e30c8f29c9e2051033d4dfaeb0361385934abf976`)

Applies with `patch -p1 -F0`, zero fuzz, on 6b98f217 + pc_r15 (verified on a fresh copy; the
applied tree is byte-identical to the built one). All of the job file's line numbers matched my
tree exactly (699 split, 708 return, 780 `last_move_see_nonnegative`, 894
`move_score_threshold`, 2156 CaptureFutilityBase, 2166 threshold, 2167/2219 reads); the one
imprecision: the `quiet` test sits at line 2081, not 2084 (2084 is the `history` line; the
term uses both, guarded by `!quiet`, so the meaning is unchanged). Seven hunks, all in
`src/search.cpp`: two tune ints (default 0) after line 119, two table rows (spin 0..1024) after
line 201, `move_score_threshold` becomes a const member returning
`searcher_.capture_history_value(board_, move) / tune::GoodCaptureHistDiv` when the option is
above 0 (else 0), the GoodCaptures loop keeps the tested `t` and sets
`last_t_nonpositive_ = (t <= 0)` before each return, the flag is a new picker member (read only
while `stage_ == GoodCaptures`, which holds exactly after such a return),
`last_move_see_nonnegative()` = `stage_ == GoodCaptures && last_t_nonpositive_`, and the noisy
SEE threshold gets `- (tune::SeeNoisyHistDiv > 0 && !quiet ? history / tune::SeeNoisyHistDiv : 0)`.
A4 (a) needed no port: `CaptureFutilityBase` (line 2156) exists; cfb230 ran FIRST as the
harness-alone test and matched. At defaults (t always 0, term always 0) every path is the
base's own (Step 0's eight numbers, and the snd0/gcd0 identities below).

## Step 1 (checker `check_s1.py`, output `check_s1.txt`; rows `rows/{base,cfb230,snd32,gcd32,all3,snd0,gcd0}_{O,G}_d12.json`)

Every setting's sum and first three equal the job's known answers, on O (200) and on G (353)
— 20 of 20 checks OK. Identities: snd0 == base and gcd0 == base on 200/200 O and 353/353 G,
node count AND best move. Per-ON-setting change counts (all over half the positions, so each
identity is a real test of the port): table in `check_s1.txt`, quoted above.

## Step 2 (`step2_j20.py`, output `step2_table.txt`; depth-14 rows `rows/*_d14.json`; bootstrap 2000 resamples seed 12 over positions, best moves changed vs base at the same set and depth)

```
set depth  setting      nodes   ratio            boot95 bm!=base
O     12     base    8315168  1.0000 [ 1.0000, 1.0000]        0
O     12   cfb230    8354110  1.0047 [ 0.9800, 1.0249]        9
O     12    snd32    8153620  0.9806 [ 0.9393, 1.0141]       26
O     12    gcd32    8439842  1.0150 [ 0.9607, 1.0614]       41
O     12     all3    8582039  1.0321 [ 0.9793, 1.0807]       46
O     14     base   19377109  1.0000 [ 1.0000, 1.0000]        0
O     14   cfb230   19604512  1.0117 [ 0.9775, 1.0425]       12
O     14    snd32   20337220  1.0495 [ 0.9934, 1.1011]       23
O     14   gcd32   19805556  1.0221 [ 0.9696, 1.0714]       42
O     14     all3   19622625  1.0127 [ 0.9621, 1.0556]       37
G     12     base   17611204  1.0000 [ 1.0000, 1.0000]        0
G     12   cfb230   17566677  0.9975 [ 0.9738, 1.0167]       28
G     12    snd32   17928118  1.0180 [ 0.9793, 1.0519]       61
G     12    gcd32   17304549  0.9826 [ 0.9423, 1.0176]       77
G     12     all3   16979165  0.9641 [ 0.9237, 1.0008]       74
G     14     base   41052503  1.0000 [ 1.0000, 1.0000]        0
G     14   cfb230   42244244  1.0290 [ 0.9808, 1.0752]       38
G     14    snd32   42440787  1.0338 [ 0.9756, 1.0854]       58
G     14    gcd32   40955678  0.9976 [ 0.9445, 1.0438]       69
G     14     all3   41401546  1.0085 [ 0.9400, 1.0713]       74
```

No depth-14 sum equals a depth-12 sum (wrong-file check). Cross-check: base d14 sums
(O 19,377,109, G 41,052,503) equal job 19's base d14 sums exactly — same build recipe, same
sets, three hours apart.

## Step 3 (`CaptureA4Count.pc.patch.txt` sha256 `639657504ba45b8f2f99c81e6bf4428e974d485930a5b418e9333d552ee44fdd`, applies `patch -p1 -F0` on 6b98f217 + pc_r15 + CaptureA4 — verified; counting exe built with `-DFORGE_A4_CHECK=1`, differs from the plain A4 exe; summer `sum_a4c.py`, output `step3_table.txt`)

Known answers all met: (a) counting build counts the same nodes as the plain build at all
three settings — node sums equal, and stronger: **position by position (nodes AND best move)
on 200/200 O and 353/353 G for base, snd32, gcd32** (bottom of `step3_table.txt`); (b) under
base every "moved by the term", "changed sides" and flag-false count is **0** (O and G);
(c) "moved by the term" is **0** under GoodCaptureHistDiv 32 alone; (d) "changed sides" and
the flag-false counts are **0** under SeeNoisyHistDiv 32 alone.

Totals over ALL searches of each run (200 / 353 A4C lines summed per run; sign classes of the
capture history: neg, zero, pos; mp = pruned with the term but not without, ms = not pruned
with it but pruned without):

| run | sn tested n/z/p | pruned n/z/p | mp n/z/p | ms n/z/p | seeq |
|---|---|---|---|---|---|
| base O | 113,971 / 405,357 / 444,672 | 28,789 / 251,806 / 192,172 | 0/0/0 | 0/0/0 | 185,084 |
| snd32 O | 105,666 / 402,291 / 425,998 | 31,990 / 250,476 / 130,517 | 5,792/0/0 | 0/0/52,486 | 184,526 |
| base G | 379,145 / 392,629 / 974,693 | 85,749 / 236,668 / 484,712 | 0/0/0 | 0/0/0 | 1,512,145 |
| snd32 G | 373,974 / 381,542 / 984,629 | 147,529 / 229,728 / 359,945 | 56,116/0/0 | 0/0/136,246 | 1,492,173 |

| run | cap tested | to bad | changed sides | good out | of them flag false | flg 2167 | flg 2219 |
|---|---|---|---|---|---|---|---|
| base O | 2,193,184 | 1,285,272 | 0 | 907,912 | 0 | 0 | 0 |
| gcd32 O | 2,215,414 | 1,393,942 | 152,611 | 821,472 | 693,767 | 109,690 | 21,883 |
| base G | 3,885,850 | 2,201,949 | 0 | 1,683,901 | 0 | 0 | 0 |
| gcd32 G | 3,776,152 | 2,315,249 | 331,634 | 1,460,903 | 1,183,354 | 155,461 | 39,954 |

(gcd32's sn columns and base's/gcd32's flg are in `step3_table.txt`; every sn row under gcd32
has mp = ms = 0, and under base/snd32 every picker changed-sides and flg count is 0.)

## Step 4 (owed from job 17; rows `rows_lmr/`, checker `check_s4.py`, output `check_s4.txt`)

Build: 6b98f217 + pc_r15 + `LmrFine.pc.patch.txt` (job 17's, sha256 `986c10e44d25f194...`
re-verified, applies `patch -p1 -F0` — checked again), same guard flag, S14, depth 12.
- T1 (S14 + LmrFine 1 + LmrFineHistory 1): O equals job 11 `t1_s14fh_O_d12.json` on **200 of
  200** (nodes AND best move; sum 10,170,054, first three 42,893 / 29,118 / 29,414 — exact).
  G equals `t1_s14fh_G_d12.json` on **341 of 341** mask positions (nodes AND best move). The
  mask was recomputed from the raw rows (a0_G == job 11 i2_s14_G): 341, with the same 12
  outside positions job 17 listed (1-indexed 30, 37, 58, 76, 115, 123, 175, 193, 218, 236,
  275, 309). On all 353, nodes match on 341 and best moves on 349 — the node diffs are exactly
  the 12 known a0≠I2 endgame-repair positions.
- C1 (S14 + LmrFine 1 + LmrFineHistory 0 + LmrRoundF 0 + LmrTtPvF 1025): O equals job 11
  `c1_s14fine_tt1025_O_d12.json` on **200 of 200** (sum 13,036,988, first three
  22,466 / 44,041 / 47,235 — exact).
- Change counts vs file 17's a0 rows (file 20 asks these beside each): T1 changes 200/200 O
  and 339/341 mask-G; C1 changes 200/200 O. Both states CHANGE the tree on more than half the
  positions — the tests are real (this closes job 17's hole, where the tested state was an
  exact identity by construction).

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| 0: 8 numbers + uci ranges | done (2nd build config) | `step0/*`, `step0_wrongbuild/*` | all exact; both options listed; first config failed honestly |
| prediction, own commit pre-Step 1 | done | `prediction.txt` | 1 survives (P3), 2 KILLED (P1, P2) |
| port patch, `-F0` proof | done | `CaptureA4.pc.patch.txt` | zero fuzz, applied tree = built tree |
| 1: known answers + identities + change counts | done | `check_s1.py`, `check_s1.txt`, `rows/` | 20/20 exact; identities 200/200, 353/353 |
| 2: depth scaling + bootstrap | done | `step2_j20.py`, `step2_table.txt` | table above |
| 3: counter patch + build + 6 runs | done | `CaptureA4Count.pc.patch.txt`, `sum_a4c.py`, `step3_table.txt` | observe-only proven per position; all known answers met |
| 4: owed LmrFine T1/C1 | done | `rows_lmr/`, `check_s4.py`, `check_s4.txt` | 200/200 O both; 341/341 G mask for T1 |

## Findings (each: file and line of the source, command that shows it again)

Line numbers are the PC build's `src/search.cpp` (6b98f217 + pc_r15).

1. **SeeNoisyHistDiv 32 moves SEE pruning only in the designed direction, and the two sides
   are very unequal.** At the noisy SEE test (line 2166; the term added by the patch), the
   history term pruned 5,792 (O) / 56,116 (G) extra moves — ALL with negative capture history
   — and saved 52,486 (O) / 136,246 (G) moves from pruning — ALL with positive history; the
   zero class never moves (0 in every run). The saved side outweighs the pruned side ~9:1 on O
   and ~2.4:1 G. Show: `python3 sum_a4c.py rows` (mp/ms columns of `step3_table.txt`).
2. **…yet on O that net anti-pruning still SHRANK the tree at d12** (0.9806) and only grew it
   at d14 (1.0495): the threshold term also reorders which captures reach the bad list and
   when, so the direct prune/save balance does not set the tree's direction by itself.
   (Compare finding 1's counts with the step 2 table.) Show: `python3 step2_j20.py`.
3. **GoodCaptureHistDiv 32 re-sorts 6.9 % (O) / 8.8 % (G) of tested captures** across the
   good/bad line (line 699's `see_ge(move, -t)` with t from line 894), and hands out 84.5 %
   (O: 693,767 of 821,472) / 81.0 % (G) of its good captures with the flag FALSE — a t > 0
   pass does not prove SEE ≥ 0. That makes `last_move_see_nonnegative()` (line 780) nearly
   dead under this option, forcing 109,690 (O) / 155,461 (G) extra SEE tests at line 2167 and
   21,883 / 39,954 at line 2219 that base would have skipped. Show: `python3 sum_a4c.py rows`.
4. **CaptureFutilityBase 230 alone is nearly tree-neutral at d12 (O 1.0047, G 0.9975) but
   grows G +2.9 % at d14** — pruning more captures (line 2156) changes move order and history
   enough that the saved nodes come back deeper. Best moves barely move (9–38 changed).
   Show: `python3 step2_j20.py`.
5. **The all-three bundle flips sign with depth on G: 0.9641 at d12, 1.0085 at d14** — the
   d12 shrink is dominated by gcd32's deferral of captures to the bad list, the d14 growth by
   cfb230's and snd32's deeper-tree effects; on O the bundle grows at both depths (+3.2 %,
   +1.3 %). This is what killed P1: at d12 the bundle looked one-sidedly smaller, at d14 it is
   not. Show: `python3 step2_j20.py`.
6. **Under gcd32 the bad-list share RISES** (O: 58.6 % → 62.9 % of tested captures; G: 56.7 %
   → 61.3 %) although positive t makes the split easier to pass — negative-history captures
   get t < 0 and fail `see_ge(move, -t)` harder, and they are the majority of tested captures
   at these sets' depths. Show: `python3 sum_a4c.py rows` (pick columns, base vs gcd32).
7. **Step 4, the owed LmrFine proof**: T1 and C1 (states that change the tree, unlike job
   17's identity i4) reproduce job 11's plain-build rows on the PC build exactly (200/200 O;
   341/341 G mask for T1), so the LmrFine port is now proven by CHANGING states, and the
   12 G positions outside the mask are exactly job 17's known a0≠I2 endgame-repair positions.
   Show: `python3 check_s4.py`.

Suspicions, not proven:
- The all3 d12→d14 sign flip on G is attributed to cfb230/snd32 by component, but no pairwise
  (cfb+gcd, snd+gcd, cfb+snd) rows exist; the attribution is by the single-option rows only.
- The flag-false share (finding 3) is high partly because one good bonus already lifts capture
  history past 32 (S14 bonus sizes are hundreds); inferred from the bonus constants
  (`tune::HistoryBonus*` declarations, search.cpp lines ~150–165), not separately counted.

## From my colleagues

Read: `for-fable-and-opus/deepseek6-work` (tip 2026-11-17T00:17Z, long 77/78) and
`cursor/glmflash5-work-cb5c` (tip 2026-11-16T23:26Z, queue 5) — the branches file 21 names;
both stopped this morning per file 21, nothing newer since last night, and nothing in their
notes contradicts this job. Useful on file: deepseek6's "bench N is DEPTH" note (already
encoded in `step0_j20.sh` from job 19), their eval-print format for future eval questions;
glmflash5's TT-pollution-under-process-reuse question stays open but does not apply here
(one engine process per run, `ucinewgame` + `isready` before every search via the proven
runner); their pv1 lead and the 20k-node pools are match-side, not this job. Applied: none
directly — this job is fixed-depth single-process searches; I kept the proven harness.

## What I did NOT do

- No games / Elo (not asked). No pairwise A4 combinations (cfb+snd, cfb+gcd, snd+gcd) — not
  asked; would settle the suspicion about the all3 d14 flip.
- The 12 G positions outside the a0 mask were not re-investigated (they are the known
  endgame-repair positions of jobs 17/19; G position 193 among them, as deepseek6 found).
- The raw files of my first (misconfigured) step 0 were deleted by me before the rerun; the
  regeneration in `step0_wrongbuild/` reproduces the numbers but is not the original output.
- The seeq class (quiet checking moves reaching the SEE test) is counted for scale only; the
  job's known answers do not pin it and I did not analyze it.

## What I am NOT sure about

- Why snd32 shrinks O at d12 (0.9806) although its net effect at the SEE test is strongly
  anti-pruning (finding 2): plausible causes are the changed order into the bad list and
  history-side effects of newly kept captures; not separated.
- Whether the flag-false share stays ~0.84 at depth 14 (P2 was measured at d12 only, as
  asked); at deeper trees histories differentiate more, so plausibly higher — not measured.
- P2's kill: my model assumed histories stay near 0 for a large share of a search; one S14
  bonus already crosses the t = 1 bar, so the share was always going to be high. Whether ANY
  divisor in 0..1024 gives a mid-range share is unknown (32 is already near the top of what
  the history magnitudes make meaningful).

## A better way

- The flag-false finding (3) suggests a stronger design for the same idea: let the picker
  remember the SEE RESULT of the winning test, not only `t <= 0`. `see_ge` answers a bool,
  so today the picker cannot know whether a t > 0 pass also had SEE ≥ 0. A value-returning
  SEE (this engine has `capture_value` for the static side; an exact SEE value function would
  be new code) would let `last_move_see_nonnegative()` stay EXACT under GoodCaptureHistDiv:
  no 2167/2219 collateral SEE tests, and the noisy-SEE skip logic keeps working. How to check
  that it is better: under gcd32, compare tree ratios AND the flg-2167/2219 counts against
  this job's — a better variant keeps gcd32's tree shape (its d12 G shrink) while driving the
  two flg counts toward 0; strength is then readable from the tree shape without the
  collateral-search distortion.
- Process: my lost first-step-0 raw files would have been kept by naming the rerun output
  `step0_v2/` instead of `rm -rf step0` — one word in the batch habit, zero cost.

## Times

See `tests_kimi5_job20/stamps.txt` (every line from `date -u`; steps without one say
"not stamped"). Claim 15:00:59Z; measuring ended 15:11:02Z; report writing began 15:11:28Z.

## Model

Kimi K3 (runtime: "powered by Kimi K3").
