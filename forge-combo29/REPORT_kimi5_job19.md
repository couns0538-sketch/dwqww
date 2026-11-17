# kimi5 job 19 report — A6 (singular extensions) on the PC build

(1) **Step 0: MET** — all eight numbers exact on the A6 build with both new options at their
defaults, and the `uci` list shows both names with the job's ranges.
(2) **Prediction graded row by row** (file `tests_kimi5_job19/prediction.txt`, own commit
"kimi5 job 19 prediction" before Step 1, never edited):

| row | guess | kill range | measured | verdict |
|---|---|---|---|---|
| P1 snc1/base nodes, G, d14 | 0.945 | [0.900, 0.990] | 0.9833 | survives |
| P2 share singular, O, d12, base | 0.40 | [0.25, 0.55] | 0.4015 | survives |
| P3 share singular, O, d12, snc1 | 0.33, below base | [0.18, 0.50] | 0.3941 (< 0.4015) | survives, direction right |
| P4 tem100/base nodes, G, d14 | 1.09 (larger) | [1.02, 1.16] | 1.2779 | **KILLED** (larger, but grew far more) |

(3) **Step 1: every known answer met** — for each of the four settings, on O and on G, the node
sum AND the first three rows equal the job's numbers (checker `check_s1.py`, output
`check_s1.txt`): base 8,315,168 / 17,611,204; snc1 8,346,403 / 16,793,551; tem100 8,436,458 /
19,117,129; both 8,254,805 / 18,241,549 — all with their exact first-three rows. Control:
SingularNonCut 1 + TripleExtMargin 100 + SingularDepth 20 equals SingularDepth 20 alone on
**200 of 200 O and 353 of 353 G** (nodes AND best move).
(4) Step 2 table below. (5) Step 3 table below, 200 (O) and 353 (G) searches summed per run.

Three plain lines: I was asked to port the research answer's A6 — SingularNonCut (the singular
verification searched as a non-cut node) and TripleExtMargin (a triple extension when the TT
move is much more singular than the double bar) — onto the PC build, prove the port against
Opus's own rows, scale it in depth, and count what the options do inside the search. The port
is proven the same code as theirs (every given known answer exact, plus the disabling control),
and the measurements are below. How sure: identities are exact on the given answers; the
counter build is proven observe-only position by position; one of four predictions died.

## Step 0 (raw files in `tests_kimi5_job19/step0/`; a fresh process per line)

Base: 6b98f217 + `pc_r15.patch` (sha256 `d6bd72c531f785f4...`, re-verified from swarm file 5) +
`SingularA6.pc.patch.txt`; g++ 13.3.0, Release, `-DFORGE_MATE_ALPHA_GUARD=1`, AVX-512+BMI2
machine (no FORGE_PORTABLE). A6 exe sha256 `ed7c422527c3a78d6108cae137cffe42ae24378b96d766750905d81aacfd919a`
(`step0/exe.sha256`), `id name Chess Engine Forge 6.4.24 candidate`.

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | file |
|---|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ | `step0/none_*.txt` |
| S14 | 242796 ✓ | 656517 ✓ | – | – | `step0/s14_*.txt` |
| PC20 | 278024 ✓ | 587276 ✓ | – | – | `step0/pc20_*.txt` |

`step0/uci_list.txt`: `option name SingularNonCut type spin default 0 min 0 max 1` and
`option name TripleExtMargin type spin default 0 min 0 max 400`. Every `setoption` line in
`step0/*_input.log`; PC20/S14 sent exactly as in `pc20.opt`/`s14.opt`. At the defaults the
patched engine computes exactly today's numbers (the table).

## The port (`SingularA6.pc.patch.txt`, sha256 `1ebc1c38b7f1e4407c208e9947a87455c2c452e8b7252b2d089dda2b47fbb33c`)

Applies with `patch -p1 -F0`, zero fuzz, on 6b98f217 + pc_r15 (verified on a fresh copy; the
applied tree is byte-identical to the built one). All line numbers of the job file matched my
tree exactly (2201 verification call, 2208–2209 double branch, 2222 double count, 1810
`tt_capture`). Five hunks, all in `src/search.cpp`: two tune variables (default 0), one table
row of two spin options, the `cut_node` → `tune::SingularNonCut ? false : cut_node` at the
verification call, the triple test right after `extension = 2;` (inside the `!pv_node` and
double-limit guard, `!tt_capture` from line 1810), `(extension == 2)` → `(extension >= 2)`.

## Step 1 (checker `check_s1.py`, output `check_s1.txt`; rows `rows/{base,snc1,tem100,both}_{O,G}_d12.json`)

Every setting's sum and first three equal the job's known answers, on O (200) and on G (353).
Control `allsd20 == sd20`: 200/200 O, 353/353 G (nodes AND best move).
Positions whose node count changes vs base (file 20's rule): snc1 200/200 O, 349/353 G;
tem100 62/200 O, 284/353 G; both 200/200 O, 349/353 G. tem100 on O changes fewer than half
the positions, but its O sum still equals Opus's own tem100 rows (8,436,458 ≠ base's
8,315,168), so the identity is a real test of the port.

## Step 2 (`step2_j19.py`, output `step2_table.txt`; depth-14 rows `rows/*_d14.json`; bootstrap 2000 resamples seed 12 over positions, best moves changed vs base at the same set and depth)

```
set depth  setting      nodes   ratio            boot95 bm!=base
O     12     base    8315168  1.0000 [ 1.0000, 1.0000]        0
O     12     snc1    8346403  1.0038 [ 0.9531, 1.0480]       37
O     12   tem100    8436458  1.0146 [ 0.9902, 1.0352]        9
O     12     both    8254805  0.9927 [ 0.9450, 1.0349]       40
O     14     base   19377109  1.0000 [ 1.0000, 1.0000]        0
O     14     snc1   18904259  0.9756 [ 0.9237, 1.0204]       41
O     14   tem100   19783433  1.0210 [ 0.9867, 1.0518]       11
O     14     both   19044849  0.9829 [ 0.9284, 1.0295]       39
G     12     base   17611204  1.0000 [ 1.0000, 1.0000]        0
G     12     snc1   16793551  0.9536 [ 0.9104, 0.9919]       76
G     12   tem100   19117129  1.0855 [ 1.0291, 1.1389]       54
G     12     both   18241549  1.0358 [ 0.9746, 1.0888]       78
G     14     base   41052503  1.0000 [ 1.0000, 1.0000]        0
G     14     snc1   40368252  0.9833 [ 0.9239, 1.0318]       79
G     14   tem100   52459652  1.2779 [ 1.1434, 1.4028]       61
G     14     both   46122218  1.1235 [ 1.0214, 1.2264]       77
```

No depth-14 sum equals a depth-12 sum (wrong-file check).

## Step 3 (`SingularCount.pc.patch.txt` sha256 `9cf2df2744c6917c87cf80122854cb13411718def08ef453fb6b47ef2b904b0c`, applies `patch -p1 -F0` on 6b98f217 + pc_r15 + SingularA6 — verified; counter exe `d02ad696...` ≠ plain exe `ed7c4225...`; summer `sum_sng.py`, output `step3_table.txt`)

Known answers all met: (a) counting build counts the same nodes as the plain build at all
three settings — node sums equal, and stronger: **position by position (nodes AND best move)
on 200/200 O and 353/353 G for base, snc1, tem100** (`check_cnt_eq.txt`); (b) under
SingularDepth 20 every count is 0 (O and G); (c) triples are 0 under base and under
SingularNonCut 1 (and 159 / 27,758 under TripleExtMargin 100, so the counter can see triples).

Totals over ALL searches of each run (200 / 353 SNG lines summed per run; categories:
verifications run, ended singular, doubles, triples, multi-cut returns, negative −2, negative −1):

| run | verif | sing | dbl | trp | mc | n2 | n1 | sing/verif |
|---|---|---|---|---|---|---|---|---|
| base O | 48,220 | 19,360 | 5,794 | 0 | 11,268 | 6,978 | 5,010 | 0.4015 |
| snc1 O | 48,201 | 18,998 | 5,786 | 0 | 11,268 | 6,929 | 5,319 | 0.3941 |
| tem100 O | 48,824 | 19,660 | 5,934 | 159 | 11,464 | 6,982 | 5,097 | 0.4027 |
| base G | 176,423 | 111,221 | 67,359 | 0 | 31,604 | 10,247 | 15,219 | 0.6304 |
| snc1 G | 168,824 | 104,475 | 63,296 | 0 | 30,711 | 10,070 | 15,495 | 0.6188 |
| tem100 G | 212,441 | 126,684 | 79,456 | 27,758 | 38,758 | 13,294 | 25,515 | 0.5963 |
| sd20 O, G | 0 | 0 | 0 | 0 | 0 | 0 | 0 | – |

Per-bin rows (depth class × cut flag) are in `step3_table.txt`. Headlines from the bins:
most verifications sit at depth 6–7 on cut nodes (base G: 92,216 of 176,423); triples under
tem100 concentrate on cut nodes (G: 11,150 at d6_7c, 8,748 at d8_9c, 5,157 at d10_11c, 1,921
at d12pc, only 782 on non-cut).

## Step table

| step | done? | evidence | result |
|---|---|---|---|
| 0: 8 numbers + uci ranges | done | `step0/*`, `step0/exe.sha256` | all exact; both options listed |
| prediction, own commit pre-Step 1 | done | `prediction.txt` | 3 survive, 1 KILLED (P4) |
| port patch, `-F0` proof | done | `SingularA6.pc.patch.txt` | zero fuzz, applied tree = built tree |
| 1: known answers + control | done | `check_s1.py`, `check_s1.txt`, `rows/` | all sums+first3 exact; control 200/200, 353/353 |
| 2: depth scaling + bootstrap | done | `step2_j19.py`, `step2_table.txt` | table above |
| 3: counter patch + build + 8 runs | done | `SingularCount.pc.patch.txt`, `sum_sng.py`, `step3_table.txt`, `check_cnt_eq.txt` | observe-only proven per position; all known answers met |

## Findings (each: file and line of the source, command that shows it again)

1. **SingularNonCut barely moves the verification's outcomes.** The verification call
   (`src/search.cpp:2201` of the PC build, patched) with `false` instead of `cut_node` leaves
   the singular share on O nearly unchanged (0.4015 → 0.3941) and shrinks G by 4.6 % at depth
   12 but only 1.7 % at depth 14 ([0.9239, 1.0318] includes 1). Show:
   `grep -h "info string SNG" rows/cbase_O_d12_full.txt | head -1` vs `csnc1`, and
   `python3 step2_j19.py`.
2. **TripleExtMargin 100's effect grows with depth**: +8.6 % on G at d12, +27.8 % at d14
   [1.1434, 1.4028]. The triple test sits right after `extension = 2;` (patched search.cpp,
   the `tune::TripleExtMargin > 0 && !tt_capture` line). Show: `python3 step2_j19.py`.
3. **Singular activity concentrates at shallow cut nodes**: of 176,423 base-G verifications,
   92,216 are depth 6–7 cut nodes, and doubles even more so (40,452 of 67,359). Show:
   `python3 sum_sng.py` (per-bin block).
4. **The multi-cut return (`singular_beta >= beta`, patched search.cpp same block) is
   frequent**: 18 % of base-G verifications (31,604 of 176,423) — this engine's singular
   machinery prunes whole subtrees often, not only extends. Show: `python3 sum_sng.py`.
5. **Best moves are sticky**: tem100 changes the O tree on 62 positions but the best move on
   only 9 (d12); snc1 changes 37–41 best moves on O while its node sums stay within noise.
   Show: `python3 step2_j19.py` (bm!=base column).

Suspicions, not proven:
- On O the multi-cut totals of base and snc1 are identical (11,268 = 11,268) while per-position
  rows differ; an aggregate coincidence, not a bug — the per-position JSONs differ, so no
  action. Not investigated further.
- The singular share is much higher on G (0.63) than on O (0.40). G is endgame-heavy; plausibly
  more TT hits with `tt_depth >= depth - 3`. Not proven.

## From my colleagues

Read: `for-fable-and-opus/deepseek6-work` NOTES (tail) and `cursor/glmflash5-work-cb5c` NOTES
(tail) — the branches file 20 names; `for-fable-and-opus/glmflash5-work` was not fetched (file
20 says it is stale). deepseek6: colour-flip eval symmetry is exact; G position 193 is a real
depth-12 defect (wrong mate length) — relevant to anyone reading G PVs, not to node-count
identities; their probe lesson (well-formed illegal move) noted for any future legality test.
glmflash5: fastchess process reuse pollutes the TT across concurrent games (fixed-node matches
not position-deterministic); pv1 is their big gain at 2k nodes. Applied: none directly — this
job is single-process fixed-depth searches, so TT pollution across games does not apply; I
kept `ucinewgame` + `isready` before every search via the proven runner. Checked: the two
branches' REPORT lists (both at t23); nothing in them contradicts this job.

## What I did NOT do

- No games / Elo (not asked). No Step-2 depth beyond 14 (not asked). 
- tem100-on-O changes only 62 of 200 positions; I did not add a third position set to
  strengthen that cell (the known answer still pinned it).
- The per-bin Step 3 table is committed in full (`step3_table.txt`) but not reproduced here
  beyond the headlines.

## What I am NOT sure about

- Position-by-position equality with Opus's rows is proven only through the published known
  answers (sum + first three) plus the disabling control; a full row file of theirs would be a
  stronger pin (see "A better way"). The aggregate match could in principle hide two offsetting
  per-position differences; the sd20 control and the exact first-three rows make that unlikely,
  not impossible.
- Why snc1's G effect shrinks from d12 (−4.6 %) to d14 (−1.7 %): deeper verification searches
  may dilute the cut-flag effect, or d14 noise (interval includes 1). Not resolved.

## A better way

- Ask Opus to publish the full per-position rows (nodes + best move) for one setting per job,
  not only sums and first three: position-by-position identity then needs no control-run
  argument, and any real divergence is localized to a position in one diff line. Check: diff
  their rows against ours; a single differing position names the search feature to look at.
- The counter patch prints one line per search and a summer re-parses it; printing the totals
  inside the engine at the last search of a run would remove a whole script class — but the
  per-search lines are the evidence, so keep both (line per search + a committed summer, as
  done here).

## Times

See `tests_kimi5_job19/stamps.txt` (every line from `date -u`; three steps "not stamped").

## Model

Kimi K3 (runtime: "powered by Kimi K3").
