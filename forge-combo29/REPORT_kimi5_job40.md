# kimi5 job 40 report — the capped harness, the finished runaway cell, the extension scan, measured tune bounds

(1) Step 0: the eight numbers of file 30 on the plain r15d build, all exact (`tests_kimi5_job40/step0/`):
312866, 862329, 3024920, 4865609 (none_*); 242796, 656517 (s14_*); 278024, 587276 (pc20_*).
(2) C-CAP: 200 of 200 O rows and 353 of 353 G rows equal to the uncapped base rows, 0 exploded. C-TRIP: 200 of
200 O rows exploded. Both controls pass.
(3) Step 2 (CheckExtPlies 2 on G, capped): 42 exploded positions — indices
3 6 10 16 30 48 58 66 73 80 85 100 104 110 115 123 126 140 142 145 161 185 192 197 204 211 216 218 238 244 262
270 273 275 277 280 299 309 328 329 342 349 — K2's position 3 is among them (row: depth 10, 138,601 nodes,
bestmove g1g6, cap 844,570). Over the 311 non-exploded positions: node sum 23,320,981 vs base 14,232,523,
ratio 1.6386. Positions changed 351 of 353, best moves changed 103.
(4) Prediction, graded cell by cell (G; KNOWN cells not graded): 10 of 11 blind cells inside — inside:
DoubleExtLimit -1/8/12/24/64 (0,0,0,0,0), DoubleExtPlies 1 (0), SingularTtCutExt 0 (0), DoubleExtMargin 12/48/96
(0,0,0); outside: DoubleExtMargin 0 (predicted 3 to 20, measured 0). KNOWN: SingularExtPlies 0 (0), SingularExtPlies
2 (14, my 2 to 12 would have been short), SingularTtCutExt -1 (0), SingularCutNodeExt 0 (0), CheckExtPlies 0 (0).
"Most exploded": I named DoubleExtMargin 0 — WRONG; the only G run with explosions was SingularExtPlies 2 (14).
(5) Step 3's table: `tests_kimi5_job40/s3/s3_table.tsv` (33 runs, `table_j40.py` prints rows_files_read: 66);
the only exploding cell: SingularExtPlies 2 on G, 14 positions (6 10 20 26 27 72 122 142 189 213 257 283 297 328).
(6) tune_table_v2.tsv measured rows:
DoubleExtMargin 24 [0, 96] step 4; DoubleExtLimit 6 [-1, 64] step 1; DoubleExtPlies 2 [1, 2] step 1;
SingularExtPlies 1 [0, 1] step 1 (2 exploded 14 on G: max pulled back to the default); SingularTtCutExt -2 [-8, 0]
step 1; SingularCutNodeExt -1 [-8, 0] step 1; CheckExtPlies 1 [0, 1] step 1 (2 exploded 42 on G: max pulled back
to the default). All `measured`; the other 42 rows `spec`. Below the table: CheckExtPlies 2 (O 0, G 42),
SingularExtPlies 2 (O 0, G 14).
(7) Step 5: C-KEPT pass — base1 equals base2 on 353 of 353 rows (`s5/s5_base1.rows` = `s5/s5_base2.rows`).
TtAgePenalty is ALIVE with a kept table: at 3, 286 of 353 rows differ from base1 (sum 17,916,165 vs 18,740,484,
ratio 0.9560, 83 best moves); at 5, 163 of 353 (18,616,225, ratio 0.9934, 47 best moves).

## Three lines
- Asked: put the node cap into the harness with two controls, finish the runaway CheckExtPlies 2 G cell, scan the
  extension options to their spec bounds through the cap, write tune_table_v2 with measured bounds, and (time left)
  rerun TtAgePenalty with the table kept.
- Answer: all done. The cap harness is proven (C-CAP exact, C-TRIP exact); the runaway cell is finished (42
  exploded, position 3 among them); the scan ran 33 cells with ONE exploding value (SingularExtPlies 2 on G);
  the tune table now has seven measured rows; TtAgePenalty is ALIVE with a kept table, DEAD only with a cleared one.
- Sure: high on every counted table (each run with ucinewgame+isready, refusal scan, exe sha and full option list
  in each `.meta`; the two controls pass exactly; six cells replicate job 37's uncapped ratios to 4 decimals).
  Medium on the engine-side story of the cap (proved for position 3 by timing; not read to its code line — S1).

## Step table
| step | status | evidence | result |
|---|---|---|---|
| 0 | done | step0/*.txt + *_input.log | 8 of 8 numbers exact |
| 1 C-CAP | done | s1/ccapO.rows, ccapG.rows (+.caps,.meta) | 200/200, 353/353 equal to base, 0 exploded |
| 1 C-TRIP | done | s1/ctripO.rows (+.caps) | 200/200 exploded (all by depth<12; 0 rows reached the cap) |
| 2 | done | s2/s2_CheckExtPlies_2_G.rows (+.caps) | 42 exploded incl. position 3; ratio 1.6386; 351 chg; 103 bm |
| prediction | done | prediction.txt (own commit, before step 3) | 10/11 blind inside; most-exploded line wrong |
| 3 | done | s3/ (33 runs), s3_table.tsv | one exploding value: SingularExtPlies 2 G (14) |
| 4 | done | tune_table_v2.tsv, make_tune_table_v2.py (prints rows_files_read: 70) | 7 measured rows, 42 spec rows |
| 5 | done | s5/ (4 runs) | C-KEPT 353/353; TtAgePenalty ALIVE (286/353 at 3, 163/353 at 5) |

## Findings (each with file:line or a reproducing command)
- F1, the cap works as specified. C-CAP (cap = 10 x base nodes per position, `go depth 12 nodes <cap>`) reproduces
  the uncapped rows to the byte on both sets; C-TRIP (cap = base/2) explodes every row. Notable: all 200 C-TRIP
  rows are exploded by depth < 12 ALONE — 0 rows reached the cap (`agg_j40.py` on s1/ctripO): the engine aborts
  the unfinished iteration and reports the last completed one.
- F2, what a capped search does at the cap: it burns the budget in an iteration it never finishes, then returns
  the last completed iteration. Code: the budget check is `should_stop_with` (src/search.cpp:1656-1666,
  `total_nodes() + extra_nodes_ + pending_nodes >= node_limit_`), consulted at every node when a node limit is
  specified (search.cpp:1888, 2037), and the iteration loop keeps the last finished iteration (search.cpp:3259,
  3273-3274, comment at 3271-3272). Proof by timing (G position 3, CheckExtPlies 2, PC20, cap 844,570): the
  depth-10 line prints at engine time 73 ms with 138,601 nodes; `bestmove g1g6` arrives at wall 423 ms — the
  ~350 ms between (≈700,000 nodes at this VM's speed) is the remaining budget (844,570 − 138,601 = 705,969)
  spent in an iteration whose line never prints. Consequence for every capped table here and later: an exploded
  row's recorded nodes UNDERSTATE the true spend (≈ the cap); "depth below 12" is the mark that never lies
  (file 40's K3 said exactly this); the node sums I report are over non-exploded positions only, so they stay exact.
- F3, Step 2 (the finished runaway cell): numbers at the top. The uncapped 24M-node position 3 now stops inside
  its cap; the cell's measured meaning: 1.6386x nodes on the positions that survive, 42 that do not.
- F4, replication (harness trust, like a null-patch control): the six cells shared with job 37's UNCAPPED scan
  reproduce its ratios to 4 decimals: SingularExtPlies 0: 0.7046 O / 0.5363 G; SingularExtPlies 2 O: 2.0509
  (0 exploded on O); SingularTtCutExt -1: 1.0695 / 1.0174; SingularCutNodeExt 0: 1.0572 / 1.0044;
  CheckExtPlies 0: 0.9006 / 0.7536; CheckExtPlies 2 O: 1.1981. Where nothing explodes, the 10x cap changes nothing.
- F5, a mechanism cross-proof for free: DoubleExtLimit -1 and DoubleExtPlies 1 give BYTE-IDENTICAL rows on O and
  on G (`diff s3_DoubleExtLimit_m1_O.rows s3_DoubleExtPlies_1_O.rows`). Reading says they must: at limit -1 the
  gate `inherited_double_extensions <= tune::DoubleExtLimit` (search.cpp:2478) is never true, so every singular
  extension is SingularExtPlies (=1); at DoubleExtPlies 1 the double branch fires but sets extension = 1 as well
  (search.cpp:2477-2479, 2492). Two different switches, one tree — the harness sees it.
- F6, DoubleExtLimit is flat on O: values 8, 12, 24, 64 change 0 of 200 O rows (sums equal base to the node):
  the default budget 6 is never reached on O at depth 12. On G, 30 rows change and the sums DROP to 0.991-0.993
  (a looser budget slightly SHRINKS those trees — TT-order effects); 24 and 64 are identical to the node
  (the limit stops binding). The measured tune bound [-1, 64] rests on that.
- F7, DoubleExtMargin is mild: at 0 every singular non-pv node inside the budget double-extends
  (search.cpp:2478), yet ratios are only 1.1558 O / 1.0875 G with 0 exploded of 553; 48 and 96 shrink G trees
  (0.913 both). My 3-to-20 explosion prediction for margin 0 was wrong — singular non-pv nodes are rarer than
  the mechanism suggests.
- F8, the strongest knob is also the explosive one: SingularExtPlies 2 on G explodes 14 positions (indices above)
  and still costs 2.8139x on the 339 that survive (job 37's uncapped all-position ratio was 3.2526). On O it
  explodes none (2.0509x). 4 of its 14 G explosions (6, 10, 142, 328) also explode under CheckExtPlies 2 —
  a small shared set of positions that blow up under any extra extension.
- F9, Step 5 settles job 37's open DEAD call: with the table KEPT between positions (one process, isready only),
  TtAgePenalty moves 286/353 rows at value 3 and 163/353 at 5 (best moves 83 and 47). Job 37's ucinewgame-per-
  search runs cleared the table every search, and file 40's reading predicted exactly this: the penalty needs
  entries older than the current search to act on. Also: the changed rows at value 3 are CONTIGUOUS from index 68
  to 353 (at 5: 49, then 192-353) — the effect switches on once the table is warm. C-KEPT (base1 vs base2,
  same conditions twice): 353/353 equal — a kept table on one thread is deterministic, the control file 40 asked
  for. The kept-table base sum is 18,740,484 vs 17,611,204 fresh (+6.4%): a warm table GROWS these trees.
- F10, build provenance: plain r15d exe sha256 6b52e43e… and census-patched exe b96e8895…, both byte-identical
  to job 37's exes (tree rebuilt from 6b98f217 + pc_r15 d6bd72c5… + carbon2 a_speed_pc20_v3 + e1_legal_check_
  evasions, search.cpp sha256 174e07a5… pinned; census_r15d.patch.txt applied -p1 -F0; g++ 13.3.0 Release with
  -DFORGE_MATE_ALPHA_GUARD=1). Stale-build trap hit and handled: a build dir copied with the tree kept the old
  cache and "rebuilt" the plain exe — the fix was deleting the copied build dir (notes of job 35 were right).

## Suspicions, not proven
- S1, the target-depth puzzle: position 3 with `go depth 11` (with or without `nodes 844570`) completes iteration
  11 at 552,140 nodes; with `go depth 12 nodes 844570` iteration 11 never completes — no depth-11 line, ~706k
  nodes burned, abort (reproducible; the s2 full log from the real harness shows the same, so it is not a probe
  artifact; probe commands: the same setoption list as s2 plus `go depth 11` / `go depth 11 nodes 844570` /
  `go depth 12 nodes 844570` / `go depth 12 nodes 2000000` on G.epd line 3). I found NO reader of max_depth or
  limits.depth inside the iteration in the time (only search.cpp:2823, 3076), so why the same iteration costs
  413,539 under one target and >705,969 under the other is unexplained. It does not affect any table above:
  the mark (depth < 12) and the non-exploded sums are exact either way.
- S2, the step-5 onset rows (68 at value 3, 49 at value 5) look like a table-warmth threshold; one run each.
- S3, the +6.4% kept-table node growth: mechanism not shown (TT-cut candidates changing is my guess).
- S4, F2's hidden burn is proved by timing for position 3 only; run-level it is consistent (s2: 24 s wall,
  32.6M recorded + ≤24.5M hidden) but not per-row proved.

## From my colleagues
- deepseek5 (branch tip: "deepseek5 job 30 stamps"): notes read — the newest FOR kimi5 item (CounterMove rates
  298-302 per 1,000 worse than Killer2's 170-206 at every depth) targets step-mask bucket jobs, not this one;
  their stand5 self-play protocol note is for game claims (none here). Their newest report is REPORT_t23.md
  (`go mate N` misses forced mates within 2N-1 plies; stale scores near the 50-move rule; on carbon/t23, a
  different chain) — noted, nothing applied to this job. Applied from their craft, not their numbers: the planted-
  control habit (my F4 replication table is the same idea: prove the harness against known uncapped numbers).
- glmflash5: work branch still absent — said so, went on (their branch has never existed for any of my jobs).

## What I did NOT do
- No match, no Elo (the job forbids it); no reading of file 41's job (read for corrections only — none touch
  job 40); no per-row proof of the hidden burn (S4); no code-level answer to S1; no rerun of the scan at other
  cap factors (see "A better way"); the O-side flatness of DoubleExtLimit was not re-proved on G's changed 30
  rows beyond the sums.

## What I am NOT sure about
- S1's cause (listed above) — the one genuine puzzle of this job.
- Whether "max pulled back to the default" is what file 40 wants for an exploded side (SingularExtPlies max 1,
  CheckExtPlies max 1). The letter of the rule gives no 0-exploded value on those sides; the spec bound exploded;
  I chose the default and listed the exploding values below the table. A tuner reading the row sees "no room
  above default", which is the measured truth.
- The mixed sides of SingularTtCutExt / SingularCutNodeExt / DoubleExtPlies rows (one side spec, one measured)
  are all marked `measured` per row — the spec side is the rule's own fallback, stated here.

## A better way
- The cap is spent, not just reached: 42 of 353 positions in the s2 cell burned ≈24.5M nodes (caps) to produce
  9.3M nodes of usable rows. The engine's own comments describe the fix (search.cpp:2778-2781: a softnodes
  search keeps "the finished-iteration target" so "a runaway iteration still discards its partial move"): for a
  depth+nodes search, stop AFTER the last finished iteration when the next iteration cannot plausibly finish in
  the remaining budget (estimate = last iteration's cost x the last growth factor; S1 shows the pieces exist).
  The marks would be IDENTICAL (depth < 12 either way; the bestmove is already the last completed one), the s2
  cell would run in ~12 s instead of 24, and C-TRIP's rows would keep their depths. Checkable: a text patch,
  then C-CAP must stay 200/200 + 353/353 equal and the s2 cell's rows file must equal this job's.
- For gate-type options the O set carries no information: DoubleExtLimit 8..64 changed 0 of 200 O rows, and
  job 37's gated rows (LmrDeeper*/LmrShallower*) were equally flat. Scanning such options G-only halves the
  scan cost. Checkable: compare `changed == 0 on O` across the gated options of this scan and job 37's — if the
  class holds, adopt G-only for options whose mechanism is a path budget.

## What this check cannot see (file 40's text, as given)
The PC's net (its trees may explode at other values); searches limited by nodes or by the clock (there an
explosion shows only as a shallower search, never as a hang); more than one thread; whether any range plays
better (the PC's matches and the tuner decide that).

## Times
See `tests_kimi5_job40/stamps.txt` (run start first: 2026-11-21T00:01:48Z, recorded as `now 1795219308` in the
step-1 probe; claim 00:02:22Z; the duplicated start/end s1 pair and the double start s5 line are the two failed
harness attempts — an argument-parser bug, fixed in runner_j40.py before any measurement; both left in the
append-only file on purpose). Budget: every step finished well inside 50 minutes.

## Last commands before this commit
`git status --short` (before staging this report):
```
M  forge-combo29/NOTES_kimi5.md
A  forge-combo29/tests_kimi5_job40/... (s5 run files, opt files for TtAgePenalty, stamps.txt; all earlier
   folders already committed: step0, s1, s2, s3, opt, opt_src, prediction.txt, runlist.tsv, runner_j40.py,
   run_s3.sh, agg_j40.py, table_j40.py, make_tune_table_v2.py, tune_table_v2.tsv, step0.sh)
```
`ls -R forge-combo29/tests_kimi5_job40` (abbreviated; full listing reproducible):
```
agg_j40.py  make_tune_table_v2.py  prediction.txt  runlist.tsv  runner_j40.py  run_s3.sh  stamps.txt
step0.sh  table_j40.py  tune_table_v2.tsv
opt/       19 files (17 step-2/3 option files + opt_TtAgePenalty_{3,5}.txt)
opt_src/   pc20.opt, s14.opt
step0/     8 raw outputs + 8 input logs + exe.sha256
s1/        ccapO, ccapG, ctripO x (.rows .caps .rows.meta _input.log _full.txt) + 3 driver logs
s2/        s2_CheckExtPlies_2_G x (.rows .caps .rows.meta _input.log _full.txt) + s2.log
s3/        33 runs x (.rows .caps .rows.meta _input.log _full.txt .log) + s3_table.tsv
s5/        s5_base1, s5_base2, s5_TtAgePenalty_3, s5_TtAgePenalty_5 x (.rows .rows.meta _input.log _full.txt .log)
```

Model: Kimi K3 (runtime name kimi-k3).
