# kimi5 job 27 report — history carry-over between searches, and a HistoryAgeKeep option (PC build)

Asked: read what the history tables carry from one search to the next inside a game, add a spin option
HistoryAgeKeep that ages the quiet-history tables at every search start, prove it on known answers, then
measure 6 keep values x 2 budgets over a 20-game replay. Answer: the carried quiet histories ARE the
history pruning - aging to 7/8 per search (keep 896) collapses it to 14 % (soft) / 20 % (hard) of the
default and changes about a third of the 1,200 best moves; all known answers and controls PASS.
How sure: high. Every known answer matched exactly (0 differing rows of 1,200 against sol's rows on both
budgets, on two independently written harnesses); my own prediction was largely wrong (16 of 20 KILLED)
and is graded below.

## (1) Step 0 and the three source statements

Step 0 MET: 8 of 8 on the plain PC build (6b98f217 + pc_r15, -DFORGE_MATE_ALPHA_GUARD=1 via
CMAKE_CXX_FLAGS, g++ Release), a fresh process per line, raw files in `tests_kimi5_job27/step0/`:
none 312866 / 862329 / 3024920 / 4865609 (none_bench11/13/16.txt, none_perft5.txt),
S14 242796 / 656517 (s14_bench11/13.txt), PC20 278024 / 587276 (pc20_bench11/13.txt).
exe sha256 in step0/exe.sha256; every setoption line in the *_input.log files.

The three statements HOLD on my tree (all line numbers are the PC build's `src/search.cpp`,
`include/forge/search.hpp`, checked with the file open):

1. The root entry `Worker::search(Board, const SearchLimits&, ...)` (search.cpp:2459) resets the search
   stack and the killers but no history table: per-search counters at 2463-2481, the stack reset loop at
   2673-2685 (`ss.killers = {}` 2684, continuation sentinel 2679) and ply stamps 2686-2687. No history
   table is touched anywhere in 2459-3022 (read end to end).
2. `Worker::clear()` (1116; empties every history table, 1117-1135) runs only from: the Worker
   constructor (1111), `Searcher::clear()` (3056-3059, the per-worker loop at 3058) which `uci.cpp`
   calls on `ucinewgame` (388), on a setoption that CHANGES SoundMatePruning (586) or MateAlphaGuard
   (597), and on bench (779); and for the alternate MultiPV worker (2880). Nothing empties or ages the
   tables between the searches of one game in this job's protocol (PC20 options set once per process;
   none of them is SoundMatePruning/MateAlphaGuard).
3. `apply_history` (327-329) is a gravity update bounded by HistoryMax = 16384 (254):
   `entry + clamped - entry * |clamped| / HistoryMax` with clamped clamped to ±HistoryMax.

## (2) Step 1 as two tables

### (a) History tables of the PC build

All in `src/search.cpp` / `include/forge/search.hpp` of the PC build. "Gravity" = apply_history
(327-329), bound ±16384. `Worker::clear()` (1116) empties every one of them (line per table below).

| table | element type (hpp) | bound | updated at | read at | clear() empties |
|---|---|---|---|---|---|
| main_history_ (butterfly) | int16 [2][64][64] (390, member 494) | gravity | update_quiet_stats 1576/1585; TtCutoffHistory 1856; EvalSwing 1895; PV bonus /4 at 2349 | quiet_history 1463; MovePicker 1020/1042/1079; history var 2084 -> prune test 2143 (threshold 2128), LMR 2265 | yes (1117) |
| continuation_history_ | int16 [13][64][13][64] (406-407, 498) | gravity (4-ply bonus /2) | update_continuation 1555-1562 (backs 1/2/4), from 1581/1588, 1857; fail-low parent 2359-2362 | quiet_history via (ss-1)/(ss-2) 1464-1466 and (ss-4)/2 1467-1469 | yes (1123) |
| threat_history_ | int16 [2][4][64][64] (393, 495) | gravity | update_threat_quiet 1541, from 1577/1586 and 2351 | threat_quiet_bonus 1506 -> quiet_history 1476. OFF under PC20 (tune::ThreatHistory default false, search.cpp:164): stays all-zero | yes (1118) |
| rework_history_ (HistRework twin) | int16 [2][2][2][64][64] (b4.hpp:105, member 556) | gravity | update_rework_history 1497-1503 (from 1590); PV /4 at 2358 | rework_quiet_delta 1491-1494 -> quiet_history 1450 (tune::HistRework != 0; PC20 sets 2) | yes (1133) |
| pawn_history_ | COMPILED OUT (FORGE_PAWN_HISTORY not defined; hpp 394-404; pawn_history_value 1514-1528 returns 0 in the #else) | - | - | - | n/a |
| capture_history_ | int16 [13][64][7] (408, 497) | gravity | update_capture_stats 1597-1611 | capture_history_value 1548, used 995/1071 (MovePicker) and 2084 | yes (1122) |
| counter_moves_ | Move [13][64] (409, 499) | n/a (a move, not a score) | 1573 (update_quiet_stats) | 677, 2065 | yes (1124) |
| correction_history_, material_correction_, non_pawn_white/black_correction_ | int32 [2][16384] (410/413, 500-503) | clamp ±CorrectionLimit (hpp:412) in update_correction's apply (1331-1332) | update_correction 1326, applied 1333-1337 | corrected_eval 1297-1306 | yes (1127-1130) |
| joint_correction_ (HistRework) | int32 [2][16384] (557) | same clamp | 1342-1344 | 1308-1311 | yes (1133) |
| continuation_correction_ (CorrHistV2) | int32 [2][13][64] (b4.hpp:107, member 557-area) | same clamp | 1348-1353 | 1315-1320 | yes (1134) |

`Worker::quiet_history` (1448; the live branch is the #else at 1462-1477 - FORGE_SEARCH_SPEED2 is not
defined in this build) reads: main (1463), (ss-1) and (ss-2) continuation (1464-1466), (ss-4)
continuation /2 when ContHist4PlyRead (1467-1469), pawn_history_value (1471; compiled out here),
threat_quiet_bonus (1476), and the rework delta (1450). The option therefore ages exactly main,
continuation, threat and rework histories - the four the job names - and NOT capture history, counter
moves or any correction table.

### (b) Stockfish, master at fetch time (commit 5d03b6e578a5eedc822e4563bdbb89e762fc2a59, github.com/official-stockfish/Stockfish, depth-1 fetch today)

At the start of a new search inside one game Stockfish applies a SCALING to one table and nothing to
the rest (`src/search.cpp` of that commit):
- In `Search::Worker::iterative_deepening` (called from `start_searching`, 202 -> 209):
  lines 340-343: `mainHistory[c][i] = mainHistory[c][i] * 729 / 1024;` for both colors over the whole
  butterfly table - an aging of the main history by 729/1024 at EVERY search.
- Line 338: `lowPlyHistory.fill(102);` (a per-search refill; lowPlyHistory is a low-ply-local table).
- Everything else is filled only at a new game: `Search::Worker::clear()` (713-738, comment "Reset
  histories, usually before a new game"): mainHistory.fill(-5) 714, captureHistory.fill(-742) 715,
  correctionHistory clear_range(-5) 719, pawnHistory clear_range(-1338) 720, continuationHistory
  fill(-586) 727, ttMoveHistory = 0 (731), continuationCorrectionHistory fill(5) (733-734). Reached
  from the `ucinewgame` branch via `engine.search_clear()` (uci.cpp:297-300; engine.cpp:161).
So: Stockfish ages ONLY its main history (729/1024 per search) between the searches of one game; the
job's HistoryAgeKeep ages ALL FOUR quiet-history tables. Nothing else in Stockfish scales/fills
histories per search (the rest of the grep hits are updates inside the search itself).

## (3) Known answers 1-3 and the control

1. PASS. history_age build at its default (HistoryAgeKeep 1024 = the step is skipped), go depth 12,
   ucinewgame before each: O sum 8,315,168 and G sum 17,611,204, and EVERY position's node count and
   best move equal to my job-22 base rows (rows/age_O_d12.json, rows/age_G_d12.json vs
   tests_kimi5_job22/rows/base_O_d12.json/base_G_d12.json; recount in ka1_compare.txt).
2. PASS. Warm replay of sol's first 20 games (1,200 searches) on the counting copy at the default,
   per game ucinewgame + isready once, per ply `position fen <start FEN> moves <moves so far>`:
   at go softnodes 2000 every search's node count, best move and HP27 count equal sol's A-soft-warm
   rows 1-1,200 - 0 differing rows (ka2_compare.txt; HP sum 11,633; 929 searches above 0; first three
   nodes 2474/2668/3705, best f1e2/e5a5/g1f3, counts 0/0/0). At go nodes 20000: 0 differing rows vs
   B-hard-warm (HP sum 313,423; 1,194 above 0; first three best f1e2/g8f6/g1f3, counts 2/4/15).
   Two clarifications on the file's parentheticals, both RESOLVED in the file's favor:
   - "node sum 4,561,961" is the sum of sol's final_nodes (the softnodes string). My HP27 line's
     <nodes> = the search's result.nodes equals sol's final_nodes in all 1,200 soft searches
     (sum 4,561,961 exactly); the last-info-line node counts sum to 4,294,263. Both match sol exactly.
   - "every search 20,000 nodes" (hard) holds for the search's node count: my HP27 <nodes> is exactly
     20,000 in all 1,200 hard searches (result.nodes at return). sol's per-row "nodes" field (the last
     info line) varies (9,330 / 12,084 / 17,401 for the first three) and equals mine row for row.
3. PASS. Ply 0 of every game (the first search after ucinewgame, every table empty) is equal to the
   default at EVERY keep value and budget, 20 of 20 per keep and budget (step4_table.txt, KA3 block,
   computed over all 12 rows files).
4. PASS (control that must move). HistoryAgeKeep 0, go softnodes 2000: history pruning per 1,000 nodes
   0.112 vs 2.709 at the default = 0.0412 x, below 0.2 x (step4_table.txt, Control block; first run in
   rows/keep0_soft.jsonl, rerun confirmed in rows2/keep0_soft.jsonl). The option reaches the tables.

## (4) The prediction, graded row by row (survives within [g/1.5, g x 1.5])

Prediction commit: "kimi5 job 27 prediction" (pushed 18:11:51Z, after Step 3, before any Step-4 run;
prediction.txt unchanged since).

history pruning per 1,000 nodes, ratio to the default (guess soft/hard, measured soft/hard):
- keep 896: 0.90 / 0.92 -> 0.1418 / 0.2045  KILLED / KILLED
- keep 768: 0.78 / 0.82 -> 0.0561 / 0.0980  KILLED / KILLED
- keep 512: 0.52 / 0.60 -> 0.0321 / 0.0511  KILLED / KILLED
- keep 256: 0.25 / 0.32 -> 0.0392 / 0.0399  KILLED / KILLED

best moves differing from the default, share of 1,200 (guess soft/hard, measured soft/hard):
- keep 896: 2.0 % / 1.5 % -> 38.83 % / 32.58 %  KILLED / KILLED
- keep 768: 3.5 % / 2.5 % -> 37.25 % / 31.08 %  KILLED / KILLED
- keep 512: 6.0 % / 5.0 % -> 39.42 % / 33.58 %  KILLED / KILLED
- keep 256: 10.0 % / 8.0 % -> 39.75 % / 33.00 %  KILLED / KILLED

node sum ratio to the default (soft only; guess, measured):
- keep 896: 1.005 -> 0.9501  survives
- keep 768: 1.010 -> 0.9463  survives
- keep 512: 1.020 -> 0.9557  survives
- keep 256: 1.040 -> 0.9372  survives

16 of 20 KILLED. My prior was that one 2,000/20,000-node search rebuilds most of what the aging
removes; the measurement says the opposite: the tables carried across the 60 searches of a game drive
the overwhelming share of history pruning, and move ordering is sensitive enough to them that a third
of best moves move. The four surviving node-sum guesses survived only because the 1.5 x band is wide
and both guess and measurement sit near 1 - I grade the reasoning wrong there too (I guessed a small
RISE; the sums FELL 4-8 %).

## (5) The Step 4 table

The counting copy (PC build + history_age.patch.txt + count27.patch.txt), the same 20 games,
HistoryAgeKeep 1024/896/768/512/256/0 x go softnodes 2000 / go nodes 20000 = 12 rows files in
`tests_kimi5_job27/rows2/` (one HP27 line and the last info depth line kept per search, fields
depth/nodes/bestmove/hp27/hp27_nodes/info; .meta beside every file). Totals by the committed command
`python3 tests_kimi5_job27/step4_totals_j27.py` (output: step4_table.txt; it read 1,200 HP27 lines per
file, printed in its header). HP/1000 = HP27 sum / node sum x 1000; ratios to the keep-1024 row of the
same budget; depthMed = median completed root depth (soft); worstPlyGroup = the ply group holding most
changed best moves (30-59 in every non-default row).

| keep | budget | HP sum | node sum | HP/1000 | ratio HP | bm changed | bm % | node ratio | depth med | worst ply group |
|---|---|---|---|---|---|---|---|---|---|---|
| 1024 | soft | 11,633 | 4,294,263 | 2.709 | 1.0000 | 0 | 0.00 | 1.0000 | 8.0 | - |
| 896  | soft | 1,567  | 4,080,162 | 0.384 | 0.1418 | 466 | 38.83 | 0.9501 | 8.0 | 30-59 (250/466) |
| 768  | soft | 618    | 4,063,859 | 0.152 | 0.0561 | 447 | 37.25 | 0.9463 | 8.0 | 30-59 (231/447) |
| 512  | soft | 357    | 4,103,924 | 0.087 | 0.0321 | 473 | 39.42 | 0.9557 | 8.0 | 30-59 (238/473) |
| 256  | soft | 427    | 4,024,450 | 0.106 | 0.0392 | 477 | 39.75 | 0.9372 | 8.0 | 30-59 (246/477) |
| 0    | soft | 443    | 3,965,742 | 0.112 | 0.0412 | 505 | 42.08 | 0.9235 | 8.0 | 30-59 (261/505) |
| 1024 | hard | 313,423 | 16,349,279 | 19.170 | 1.0000 | 0 | 0.00 | 1.0000 | - | - |
| 896  | hard | 63,861  | 16,285,974 | 3.921  | 0.2045 | 391 | 32.58 | 0.9961 | - | 30-59 (216/391) |
| 768  | hard | 30,756  | 16,368,311 | 1.879  | 0.0980 | 373 | 31.08 | 1.0012 | - | 30-59 (193/373) |
| 512  | hard | 16,207  | 16,541,853 | 0.980  | 0.0511 | 403 | 33.58 | 1.0118 | - | 30-59 (199/403) |
| 256  | hard | 12,554  | 16,394,075 | 0.766  | 0.0399 | 396 | 33.00 | 1.0027 | - | 30-59 (209/396) |
| 0    | hard | 13,327  | 16,443,422 | 0.810  | 0.0423 | 397 | 33.08 | 1.0058 | - | 30-59 (204/397) |

## Findings (each reproducible from the raw files named)

1. The carried quiet histories drive history pruning. Aging to 7/8 per search (keep 896) leaves only
   14 % (soft) / 20 % (hard) of the default's pruning; the within-search rebuild floor is ~3-4 %
   (soft 512: 0.0321; keep 0: 0.0412 / 0.0423). Mechanism, from the source: the prune test
   (search.cpp:2143) fires on very NEGATIVE history (threshold 2128, about -HistoryPruneMultiplier x
   depth), and the carried tables hold most of that negative evidence; one search's own updates
   rebuild only a few % of it.
2. A third of best moves follow the tables. 31-34 % (hard) / 37-42 % (soft) of the 1,200 best moves
   change at any keep < 1024, concentrated at plies 30-59 in every row (the carry accumulates deepest
   into the game; plies 1-9 barely move: 49-74 changed). Ordering reads the same tables
   (quiet_history at MovePicker 1020/1042/1079; LMR term 2265).
3. The default warm rate is budget-dependent: 2.709 vs 19.170 HP per 1,000 nodes (soft vs hard) -
   deeper searches lean much more on the carried tables.
4. Node sums: at hard budgets the ratio straddles 1 (0.9961-1.0118, node-limited); at soft all ratios
   fall to 0.92-0.96. Read as a softnodes-stop artifact candidate, not a tree claim (suspicion 2).
5. The option's cost is sub-ms per search: the keep0 soft replay ran 1,200 searches in ~3 s, the
   default in ~4 s (.meta start/end stamps) - aging four tables (~1.4 M int16 entries, dominated by
   continuation_history_) per search is not measurable against the searches themselves.
6. For Opus (job-24 follow-up you asked me to check in my tree): same as r15d. `search_child`
   (search.cpp:2396-2399) routes to `search_cuckoo` (2406-2416) under CuckooRep; the cuckoo wrapper
   calls `search()` ONCE with alpha raised to the draw score (2413), never twice (the other paths are
   the plain single calls 2415 and the early 0 return 2412). Razoring calls `qsearch_child` (1927),
   not `search()`; the singular verification search runs only at depth >= tune::SingularDepth (gate at
   2192; 6 under S14), above every t5 refusal. "The cuckoo wrapper can call the node search twice"
   stands nowhere in the PC build either.

### Suspicions, not proven

- The soft floor is not monotone (keep 256 HP sum 427 > keep 512's 357; keep 0 443). Likely variance
  across the differing searches at the residual level, not an aging leak: keep 0 zeroes the same four
  tables and still prunes 443 from within-search updates. Not proven; a within-search-only counter
  would settle it.
- The soft node-sum drop (0.92-0.96) may be an iteration-boundary artifact of the softnodes stop
  (the budget is a finished-iteration target), not a true tree shrink. Not proven.
- sol's recounted warm rates (45.3 / 16.4 per 1,000) use a normalization I could not reproduce from
  their rows (plain sums give 2.709 / 19.170). Every per-row quantity of theirs matched mine exactly,
  so this is about their summary statistic's denominator only.

## From my colleagues

- deepseek5 (branch for-fable-and-opus/deepseek5-work fetched; newest REPORT_t23): notes tail read.
  Applied: their counter lesson (read state at the moment the event happens - my HP27 increments inside
  the taken branch itself, not from a later state variable). Noted, not applicable here: their
  corrected Killer2/CounterMove rates and the t23 mate/50-move findings (nothing in job 27 touches
  mate search); their HistExempt patch is for glmflash5's chain.
- glmflash5: branch for-fable-and-opus/glmflash5-work does not exist ("couldn't find remote ref").
  Nothing to read; said so here as instructed.
- sol (data, not instructions): job3 games.txt + A/B rows and the job2 counter site were read and
  replayed; the counter site (the taken branch of the history-prune test) is the same one my HP27 uses.
- Opus's job-24 judgment inside file 27: the search_child question answered above (finding 6); the
  bootstrap-index correction of file 28 is in my notes (three corrected interval tops) as ordered.

## What I did NOT do

- No strength games: file 27 says the games come later on the PC, not in this job.
- Jobs 28 and 29 on the handoff branch: untouched (one run, one job).
- The engine source in the repository: untouched. Both patches are text files in my job folder,
  `patch -p1 -F0` clean in chain (pc -> +history_age -> +count27), verified against a pristine tree
  (the chain's result equals my edited trees file for file). No binaries committed.
- The v1 rows (rows/) were not deleted; the rerun with depth recording went to a new folder (rows2/).

## What I am NOT sure about

- The three suspicions above.
- Whether aging threat_history_ matters for any current configuration: under PC20 ThreatHistory is
  false, so that table is all-zero and aging it is a no-op here; the option ages it anyway, as the job
  specifies (the table quiet_history reads when the feature is on).
- HP27 <nodes> semantics vs sol's "nodes" for soft searches: in 1,158 of 1,200 soft searches they are
  equal; in 42 the search overshoots the last completed iteration before the soft stop prints
  result.nodes. sol's rows show the same split (their final_nodes vs nodes), and both fields match
  mine exactly, so this is a definition detail, not a disagreement.

## A better way

The known answer for the option's neutrality at the default (KA1, KA2) exercises the SKIP path
("at 1024 the step is skipped"), never the arithmetic. A one-line scratch variant that forces the
scaling loop at keep 1024 (entry * 1024 / 1024) must reproduce the default's 1,200 rows exactly on
both budgets - that would prove the int arithmetic itself behavior-neutral at the boundary, which
today's checks only assume. Cost: one build (~7 s) and two replays (~20 s). Check: 0 differing rows
against rows2/keep1024_* on nodes, best moves and HP27, exactly as KA2 was checked against sol.

## Questions for Fable / Opus

1. sol's "per 1,000 nodes" rates (45.3 / 16.4): what denominator (main nodes only? a depth-weighted
   count?) - my plain-sum rates are 2.709 / 19.170 on identical rows.
2. For the PC tune games: HistoryAgeKeep deliberately leaves capture history, counter moves and the
   correction tables unaged (the job's spec; Stockfish ages only its main history). If a later job
   wants the full Stockfish-style "everything decays", say which tables.

times: see stamps.txt
model: kimi-k3 (Kimi K3)

## git status --short and ls -R of the job folder (last command before the report commit)

```
$ git status --short
M  forge-combo29/NOTES_kimi5.md
A  forge-combo29/REPORT_kimi5_job27.md
A  forge-combo29/tests_kimi5_job27/G.epd
A  forge-combo29/tests_kimi5_job27/O.epd
A  forge-combo29/tests_kimi5_job27/count27.patch.txt
A  forge-combo29/tests_kimi5_job27/history_age.patch.txt
A  forge-combo29/tests_kimi5_job27/ka1_compare.txt
A  forge-combo29/tests_kimi5_job27/ka2_compare.txt
A  forge-combo29/tests_kimi5_job27/pc20.opt
A  forge-combo29/tests_kimi5_job27/replay2_j27.py
A  forge-combo29/tests_kimi5_job27/replay_j27.py
A  forge-combo29/tests_kimi5_job27/rows/age_G_d12.json
A  forge-combo29/tests_kimi5_job27/rows/age_G_d12.json.meta
A  forge-combo29/tests_kimi5_job27/rows/age_G_d12_full.txt
A  forge-combo29/tests_kimi5_job27/rows/age_G_d12_input.log
A  forge-combo29/tests_kimi5_job27/rows/age_G_d12_input.log.meta
A  forge-combo29/tests_kimi5_job27/rows/age_O_d12.json
A  forge-combo29/tests_kimi5_job27/rows/age_O_d12.json.meta
A  forge-combo29/tests_kimi5_job27/rows/age_O_d12_full.txt
A  forge-combo29/tests_kimi5_job27/rows/age_O_d12_input.log
A  forge-combo29/tests_kimi5_job27/rows/age_O_d12_input.log.meta
A  forge-combo29/tests_kimi5_job27/rows/ka2_hard_dfl.jsonl
A  forge-combo29/tests_kimi5_job27/rows/ka2_hard_dfl.meta
A  forge-combo29/tests_kimi5_job27/rows/ka2_hard_dfl_input.log
A  forge-combo29/tests_kimi5_job27/rows/ka2_soft_dfl.jsonl
A  forge-combo29/tests_kimi5_job27/rows/ka2_soft_dfl.meta
A  forge-combo29/tests_kimi5_job27/rows/ka2_soft_dfl_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep0_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep0_hard.meta
A  forge-combo29/tests_kimi5_job27/rows/keep0_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep0_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep0_soft.meta
A  forge-combo29/tests_kimi5_job27/rows/keep0_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep256_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep256_hard.meta
A  forge-combo29/tests_kimi5_job27/rows/keep256_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep256_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep256_soft.meta
A  forge-combo29/tests_kimi5_job27/rows/keep256_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep512_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep512_hard.meta
A  forge-combo29/tests_kimi5_job27/rows/keep512_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep512_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep512_soft.meta
A  forge-combo29/tests_kimi5_job27/rows/keep512_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep768_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep768_hard.meta
A  forge-combo29/tests_kimi5_job27/rows/keep768_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep768_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep768_soft.meta
A  forge-combo29/tests_kimi5_job27/rows/keep768_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep896_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep896_hard.meta
A  forge-combo29/tests_kimi5_job27/rows/keep896_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows/keep896_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows/keep896_soft.meta
A  forge-combo29/tests_kimi5_job27/rows/keep896_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep0_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep0_hard.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep0_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep0_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep0_soft.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep0_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep1024_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep1024_hard.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep1024_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep1024_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep1024_soft.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep1024_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep256_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep256_hard.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep256_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep256_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep256_soft.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep256_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep512_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep512_hard.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep512_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep512_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep512_soft.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep512_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep768_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep768_hard.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep768_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep768_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep768_soft.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep768_soft_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep896_hard.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep896_hard.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep896_hard_input.log
A  forge-combo29/tests_kimi5_job27/rows2/keep896_soft.jsonl
A  forge-combo29/tests_kimi5_job27/rows2/keep896_soft.meta
A  forge-combo29/tests_kimi5_job27/rows2/keep896_soft_input.log
A  forge-combo29/tests_kimi5_job27/runner_j27.py
A  forge-combo29/tests_kimi5_job27/s14.opt
A  forge-combo29/tests_kimi5_job27/stamps.txt
A  forge-combo29/tests_kimi5_job27/step0/exe.sha256
A  forge-combo29/tests_kimi5_job27/step0/none_bench11.txt
A  forge-combo29/tests_kimi5_job27/step0/none_bench11_input.log
A  forge-combo29/tests_kimi5_job27/step0/none_bench13.txt
A  forge-combo29/tests_kimi5_job27/step0/none_bench13_input.log
A  forge-combo29/tests_kimi5_job27/step0/none_bench16.txt
A  forge-combo29/tests_kimi5_job27/step0/none_bench16_input.log
A  forge-combo29/tests_kimi5_job27/step0/none_perft5.txt
A  forge-combo29/tests_kimi5_job27/step0/none_perft5_input.log
A  forge-combo29/tests_kimi5_job27/step0/pc20_bench11.txt
A  forge-combo29/tests_kimi5_job27/step0/pc20_bench11_input.log
A  forge-combo29/tests_kimi5_job27/step0/pc20_bench13.txt
A  forge-combo29/tests_kimi5_job27/step0/pc20_bench13_input.log
A  forge-combo29/tests_kimi5_job27/step0/s14_bench11.txt
A  forge-combo29/tests_kimi5_job27/step0/s14_bench11_input.log
A  forge-combo29/tests_kimi5_job27/step0/s14_bench13.txt
A  forge-combo29/tests_kimi5_job27/step0/s14_bench13_input.log
A  forge-combo29/tests_kimi5_job27/step0/uci_input.log
A  forge-combo29/tests_kimi5_job27/step0/uci_list.txt
A  forge-combo29/tests_kimi5_job27/step0_j27.sh
A  forge-combo29/tests_kimi5_job27/step4_table.txt
A  forge-combo29/tests_kimi5_job27/step4_totals_j27.py

$ ls -R forge-combo29/tests_kimi5_job27
forge-combo29/tests_kimi5_job27:
count27.patch.txt
G.epd
history_age.patch.txt
ka1_compare.txt
ka2_compare.txt
O.epd
pc20.opt
prediction.txt
replay2_j27.py
replay_j27.py
rows
rows2
runner_j27.py
s14.opt
stamps.txt
step0
step0_j27.sh
step4_table.txt
step4_totals_j27.py

forge-combo29/tests_kimi5_job27/rows:
age_G_d12_full.txt
age_G_d12_input.log
age_G_d12_input.log.meta
age_G_d12.json
age_G_d12.json.meta
age_O_d12_full.txt
age_O_d12_input.log
age_O_d12_input.log.meta
age_O_d12.json
age_O_d12.json.meta
ka2_hard_dfl_input.log
ka2_hard_dfl.jsonl
ka2_hard_dfl.meta
ka2_soft_dfl_input.log
ka2_soft_dfl.jsonl
ka2_soft_dfl.meta
keep0_hard_input.log
keep0_hard.jsonl
keep0_hard.meta
keep0_soft_input.log
keep0_soft.jsonl
keep0_soft.meta
keep256_hard_input.log
keep256_hard.jsonl
keep256_hard.meta
keep256_soft_input.log
keep256_soft.jsonl
keep256_soft.meta
keep512_hard_input.log
keep512_hard.jsonl
keep512_hard.meta
keep512_soft_input.log
keep512_soft.jsonl
keep512_soft.meta
keep768_hard_input.log
keep768_hard.jsonl
keep768_hard.meta
keep768_soft_input.log
keep768_soft.jsonl
keep768_soft.meta
keep896_hard_input.log
keep896_hard.jsonl
keep896_hard.meta
keep896_soft_input.log
keep896_soft.jsonl
keep896_soft.meta

forge-combo29/tests_kimi5_job27/rows2:
keep0_hard_input.log
keep0_hard.jsonl
keep0_hard.meta
keep0_soft_input.log
keep0_soft.jsonl
keep0_soft.meta
keep1024_hard_input.log
keep1024_hard.jsonl
keep1024_hard.meta
keep1024_soft_input.log
keep1024_soft.jsonl
keep1024_soft.meta
keep256_hard_input.log
keep256_hard.jsonl
keep256_hard.meta
keep256_soft_input.log
keep256_soft.jsonl
keep256_soft.meta
keep512_hard_input.log
keep512_hard.jsonl
keep512_hard.meta
keep512_soft_input.log
keep512_soft.jsonl
keep512_soft.meta
keep768_hard_input.log
keep768_hard.jsonl
keep768_hard.meta
keep768_soft_input.log
keep768_soft.jsonl
keep768_soft.meta
keep896_hard_input.log
keep896_hard.jsonl
keep896_hard.meta
keep896_soft_input.log
keep896_soft.jsonl
keep896_soft.meta

forge-combo29/tests_kimi5_job27/step0:
exe.sha256
none_bench11_input.log
none_bench11.txt
none_bench13_input.log
none_bench13.txt
none_bench16_input.log
none_bench16.txt
none_perft5_input.log
none_perft5.txt
pc20_bench11_input.log
pc20_bench11.txt
pc20_bench13_input.log
pc20_bench13.txt
s14_bench11_input.log
s14_bench11.txt
s14_bench13_input.log
s14_bench13.txt
uci_input.log
uci_list.txt
```
