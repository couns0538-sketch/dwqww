# kimi5 job 18 report — A7 on the PC build: identities against Opus's port, depth scaling, where the saving sits

(1) **Step 0: MET** — all 8 numbers exact on the PC+A7 build, new options at defaults.
(2) **Step 1: all six known answers met exactly** (sums AND first three, O and G, ARR 0/1/2); position by
position against the job-17 rows that job 17 proved equal to Opus's port: **200 of 200 O and 353 of 353 G**
for ARR 0 and ARR 1 (node count AND best move). ARR 2: the written known answers (sums + first three) met;
no per-position rows of theirs exist to compare further.
(3) Step 2 table below (headline: the default window fades with depth — G ARR 2 ratio 0.5176 → 0.6487 →
0.6998 at d12→d16 — while AlphaRaiseMaxDepth 16 holds it at ~0.52).
(4) Step 3 table below; searches summed: 200 (O) and 353 (G) per setting, printed by `sum_alr.py`.

Three plain lines: I was asked to prove my AlphaQs port on the PC build equals Opus's own port (known-answer
identities), then measure what deeper searches do with A7, then locate the saving by entry-depth classes with
an observe-only counter. The ports are the same code (every known answer exact), the depth scaling and the
counter map are measured and committed. How sure: exact on every identity; the counter build is node-for-node
identical to the plain build on 553/553 positions at both settings; one known answer of Step 3 (the per-search
node bound) fails on 3 of 553 searches — reported plainly with the mechanism in Findings.

## Step 0 (raw files in `tests_kimi5_job18/step0/`; fresh process per number)

Base: work-branch 6b98f217 tree + `pc_r15.patch` (sha256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`, re-verified)
+ job 17's `AlphaQs.pc.patch.txt` (sha256 `e6ccc2413afb66910c42cdd703cabbdd157b2c9616d3213c1b368555e3197661`);
both applied with `patch -p1 -F0`, zero fuzz (`/tmp/patch_r15.log`, `/tmp/patch_aq.log`). g++ 13.3.0, Release,
`-DFORGE_MATE_ALPHA_GUARD=1`, machine has AVX-512+BMI2 (no FORGE_PORTABLE). Exe sha256
`f749372ccd987b968097fc37162d95a3b09d0a1b8486f5f5650bb8ce37a16e30` (`step0/step0.meta`).

| settings | bench 11 | bench 13 | bench 16 | go perft 5 |
|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ |
| S14 | 242796 ✓ | 656517 ✓ | – | – |
| PC20 | 278024 ✓ | 587276 ✓ | – | – |

Every `setoption` line quoted in `step0/*_input.log`. New options (AlphaRaiseReduce, AlphaRaiseMaxDepth,
QsLateMoves) never sent in Step 0 = their defaults.

## Prediction vs actual (committed as "kimi5 job 18 prediction" before Step 1, never edited)

| row | guess | kill range | measured | verdict |
|---|---|---|---|---|
| P1: ARR 1 / ARR 0 at depth 16 on G | 0.75 | killed < 0.68 or > 0.82 | **0.7876** | survives |
| P2: largest Step-3 class on G under ARR 1 | d7_8 | any other class larger | **d9_11** (2,100,893 vs d7_8 1,224,020) | **KILLED** |

P2's model (armed counts fall with entry depth, work per armed node grows, peak in the middle) had the right
shape and the wrong peak: the work per armed node grows faster than the count falls, so the peak sits at the
deepest populated class. Reported as a missed model, per the form.

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| 0: 8 numbers, fresh process each | done | `step0/*.txt`, `step0/step0.meta` | all exact |
| prediction (own commit, pre-Step 1) | done | `prediction.txt` | graded above |
| 1: six known answers | done | `compare_j18.py`, `compare_i.txt` | all six OK (sums + first three) |
| 1: position-by-position ARR 0/1 | done | `compare_i.txt` | 200/200 O, 353/353 G, nodes AND best move |
| 2: 24 rows (2 sets × 3 depths × 4 settings) | done | `rows/*_d{12,14,16}.json` (+`.meta`), `step2_j18.py`, `step2_table.txt` | table below; all rc=0, no refusal |
| 3: counter patch + build + 4 runs | done | `AlphaRaiseCount.pc.patch.txt`, `sum_alr.py`, `step3_table.txt` | table below; 553 searches per setting |

## Step 2 — depth scaling (PC20, Threads 1, Hash 16; printed by `step2_j18.py`, bootstrap 95 % over
positions, 2000 resamples, seed 12; ratios to ARR 0 at the same set and depth)

```
set depth  setting      nodes   ratio            boot95 bm!=arr0
O     12     arr0    8315168  1.0000 [ 1.0000, 1.0000]        0
O     12     arr1    5299861  0.6374 [ 0.5990, 0.6688]       53
O     12     arr2    3744289  0.4503 [ 0.4247, 0.4733]       68
O     12  arr2m16    3744289  0.4503 [ 0.4247, 0.4733]       68
O     14     arr0   19377109  1.0000 [ 1.0000, 1.0000]        0
O     14     arr1  14616964  0.7543 [ 0.7135, 0.7910]       47
O     14     arr2  12240077  0.6317 [ 0.5990, 0.6605]       53
O     14  arr2m16   9012103  0.4651 [ 0.4391, 0.4876]       61
O     16     arr0   43501586  1.0000 [ 1.0000, 1.0000]        0
O     16     arr1  33757883  0.7760 [ 0.7288, 0.8177]       48
O     16     arr2  31977339  0.7351 [ 0.6927, 0.7742]       47
O     16  arr2m16  20820843  0.4786 [ 0.4479, 0.5068]       53
G     12     arr0   17611204  1.0000 [ 1.0000, 1.0000]        0
G     12     arr1  12340273  0.7007 [ 0.6657, 0.7329]       91
G     12     arr2   9116305  0.5176 [ 0.4880, 0.5433]      103
G     12  arr2m16   9116305  0.5176 [ 0.4880, 0.5433]      103
G     14     arr0   41052503  1.0000 [ 1.0000, 1.0000]        0
G     14     arr1  30897678  0.7526 [ 0.7076, 0.7920]       80
G     14     arr2  26630990  0.6487 [ 0.5967, 0.6986]       87
G     14  arr2m16  22115416  0.5387 [ 0.5023, 0.5741]       95
G     16     arr0   98418208  1.0000 [ 1.0000, 1.0000]        0
G     16     arr1  77510211  0.7876 [ 0.6456, 0.8931]       78
G     16     arr2  68877050  0.6998 [ 0.5989, 0.7909]       96
G     16  arr2m16  50729267  0.5154 [ 0.4465, 0.5760]      105
```

Internal check: arr2m16 equals arr2 position by position at depth 12 (200/200 O, 353/353 G) — at go-depth 12
every entered depth is inside both windows. The d12 rows are Step 1's rows (same files).

## Step 3 — where the saving sits (counters, observe-only; printed by `sum_alr.py`, one ALR v1 line per
search, summed over ALL searches of each file; it prints how many it summed)

Counter semantics (the job's words fixed against its known answers): at a PV node, the first alpha raise that
FIRES AlphaRaiseReduce arms the node; the nodes from that raise until the node returns land in the bin of the
depth the node was ENTERED with (captured at function entry, before any A7 mutation). Patch:
`AlphaRaiseCount.pc.patch.txt` (applies `patch -p1 -F0` on 6b98f217 + pc_r15 + AlphaQs.pc — dry-run verified),
built with `-DFORGE_ALR_CHECK=1`, exe sha256 `b98a1116e0f4cdf4a0f41f84d24b1a62c81e638b8e3e28dfe5f9c956a93a9791`
(binary changed from the plain build: yes). Counting build equals the plain build node for node AND best move
for best move on 553/553 positions at both settings (Step 1's sums included).

```
rows/c_O_arr0_d12: summed 200 searches
  armed 0  d2 0  d3_4 0  d5_6 0  d7_8 0  d9_11 0  d12plus 0  other 0
  classes total 0  nodes_sum 8315168  ratio 0.0000
rows/c_O_arr1_d12: summed 200 searches
  armed 21094  d2 0  d3_4 136584  d5_6 418550  d7_8 871133  d9_11 1501364  d12plus 0  other 0
  classes total 2927631  nodes_sum 5299861  ratio 0.5524
  per-search max (classes/nodes) 0.9156 at position 187
rows/c_G_arr0_d12: summed 353 searches
  armed 0  d2 0  d3_4 0  d5_6 0  d7_8 0  d9_11 0  d12plus 0  other 0
  classes total 0  nodes_sum 17611204  ratio 0.0000
rows/c_G_arr1_d12: summed 353 searches
  armed 39771  d2 0  d3_4 207117  d5_6 604533  d7_8 1224020  d9_11 2100893  d12plus 0  other 0
  classes total 4136563  nodes_sum 12340273  ratio 0.3352
  per-search max (classes/nodes) 1.0504 at position 78
```

Known answers: counting build = plain build node sums at both settings — MET (200/200, 353/353 per position).
Planted class d2 stays 0 under ARR 1 — MET on both sets. Sum over the classes at most the search's node count
— MET on 550 of 553 searches and in both totals (0.5524 O, 0.3352 G); VIOLATED on 3 G searches (positions 78:
15,437/14,697; 130: 18,405/18,247; 335: 20,999/20,693 — each ≤ 5 % over). Mechanism: a re-searched PV child
can arm inside its already-armed PV parent's post-raise interval and the overlap is counted twice (nested
intervals). The ARR 0 runs arm nothing on all 553 searches — the counter is keyed to A7's fire, as built.

Under ARR 1 the post-raise work sits at d9_11 on both sets (O: 1,501,364 of 2,927,631 = 51 %; G: 2,100,893 of
4,136,563 = 51 %), then d7_8 (30 %), d5_6, d3_4. d12plus is 0 by construction at these settings (entered
depth ≥ 12 is outside the default AlphaRaiseMaxDepth 12 window, so A7 never arms there).

## Findings (each with file:line of the source and a reproducer)

- The two ports are the same code: every written known answer exact, and 200/200 O + 353/353 G position by
  position for ARR 0/1 (`compare_i.txt`; reproduce `cd forge-combo29/tests_kimi5_job18 && python3 compare_j18.py`).
- A7's saving with the default window FADES with search depth (`src/search.cpp:2331`: the
  `depth < tune::AlphaRaiseMaxDepth` gate; default 12 at line 147 of the AlphaQs patch): G ARR 2 ratio rises
  0.5176 → 0.6487 → 0.6998 (d12→d16), O likewise 0.4503 → 0.6317 → 0.7351. With AlphaRaiseMaxDepth 16 the
  saving holds (G 0.5176 → 0.5387 → 0.5154). Deeper searches put more work outside the 3..11 window (root-side
  depths 12+ and the leaf region), exactly the P1 model. Reproduce: `python3 step2_j18.py`.
- The post-raise work A7 cuts into sits deepest at d9_11 on both sets (51 % each), not in the middle classes
  (`step3_table.txt`; reproduce `python3 sum_alr.py rows/c_G_arr1_d12`). Reduction COUNTS fall with entry depth
  (job 15) but the work per armed node grows faster.
- The counter is observe-only: counting exe = plain exe on 553/553 positions at both settings, nodes AND best
  moves (`c_*` vs plain rows).
- The planted d2 class reads 0 under ARR 1 on both sets: at a node's first raise the depth equals the entry
  depth (nothing else mutates `depth` before the raise site), and A7 needs `depth > 2` (src/search.cpp:2331),
  so an entry depth of 2 can never arm. Structural, and confirmed by data.
- The per-search "sum over classes ≤ node count" bound fails on 3 of 553 searches by nested armed intervals
  (re-search PV child arming inside the armed parent's interval). Fix candidate in "A better way".

Suspicions, not proven: the wide bootstrap intervals at G depth 16 (e.g. ARR 1 [0.6456, 0.8931]) suggest a few
G positions dominate the ratio variance at d16; not investigated.

## From my colleagues

- deepseek5 (`for-fable-and-opus/deepseek5-work`, NOTES tail): the counter lesson from its job 29/30 — "when a
  counter reads a state variable, read it at the moment the event happens" — applied directly: `alr_entry_depth`
  is captured at the search function's entry, before A7 can mutate `depth` (that one-late read mislabelled two
  of its jobs). Its ucinewgame+isready discipline result (S3) is already the runner's protocol.
- glmflash5: the branch `for-fable-and-opus/glmflash5-work` does not exist on the remote (job 17 found the
  same; the nearest, glmflash4-work, has no NOTES file at that path). File 18 says glmflash5 plays A7 matches
  (its job 30) — nothing to read yet. Stated per the rule.
- deepseek6 (via file 18's recounting): its long 79 splits A7 reductions by every input; my Step 3 is the
  complementary view (post-raise WORK by entry depth, not reduction counts).

## What I did NOT do

- ARR 2 position-by-position against Opus's rows: the handoff branch carries only their sums and first three
  (both met); no per-position ARR 2 rows of theirs exist to compare. Every check the data allows was done.
- No games or matches (not asked); no other AlphaRaiseMaxDepth values than the job's four settings; Step 3 run
  only at depth 12 per the job (d12plus is structurally 0 there — an outcome, not a violation).
- deepseek6's branch was not read directly (this run's instructions name deepseek5 and glmflash5).

## What I am NOT sure about

- Whether Opus's own Step-3 counter suppresses nested arming (making the ≤-nodes bound exact) or shows the
  same 3/553 over-counts mine does; my semantics is written above so the difference, if any, is checkable.
- The G depth-16 bootstrap intervals are wide; whether that is a property of set G or of A7 at depth is open.

## A better way

Make the Step-3 counter path-disjoint: pass an "armed ancestor" flag down the search stack (one field read at
entry like `double_extensions`) and arm a node only when no ancestor on its path is armed. Then the counted
intervals are disjoint on every root-to-leaf path, so "sum over classes ≤ the search's node count" becomes a
hard bound instead of 550/553. Checkable: same four runs, the per-search max ratio must read ≤ 1.0000 on all
553 searches and the ARR-0 lines must stay all-zero; the class totals change only by the removed overlap
(≤ 5 % on 3 searches here).

## Times

See `tests_kimi5_job18/stamps.txt` (run start 2026-11-17T09:04:5xZ, claim 09:05:45Z, Step 0 09:08:22Z,
prediction commit 09:08:5xZ, queue 09:09:00–09:15:43Z, Step 3 09:15:4xZ, comparisons 09:16–09:17Z; every
run's own UTC stamps in `rows/*.meta`).

## Model

Kimi K3 (runtime model name: kimi-k3).

## Last command before the report commit

`git status --short` and `ls -R forge-combo29/tests_kimi5_job18` → `tests_kimi5_job18/final_ls.txt`.
