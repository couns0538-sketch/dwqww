# kimi5 job 38 report — THE PRICE LIST OF THE MOVE LOOP'S PRUNING

First lines, in the order file 38 asks for:

**(1) Step 0.** Eight of eight known numbers exact (raw: `kimi5/job38/step0/none_bench11.txt` 312866,
`none_bench13.txt` 862329, `none_bench16.txt` 3024920, `none_perft5.txt` 4865609, `s14_bench11.txt`
242796, `s14_bench13.txt` 656517, `pc20_bench11.txt` 278024, `pc20_bench13.txt` 587276; inputs beside
them). K7: 12 of 12 cells EQUAL theirs (`step0/k7_p1..p4_{plain,two,all}.txt`; first attempt with a
shell harness failed — `go` is async, `quit` beat the search; redone with `k7_j38.py`, which waits for
`bestmove`).

**(2) Step 1** (`kimi5/job38/step1_reading.md`, chain 6b98f217 + pc_r15, all search.cpp of that tree):
the six K2 sites — late-move rule 2122 (threshold 319-321), quiet futility branch 2131, test 2132-2137,
fire 2138-2141; history prune 2143-2145; SEE of a plain quiet 2147-2151; capture futility 2153-2163
(gated on `CaptureFutilityBase > 0` at 2156, so dead under PC20); noisy SEE 2166-2176 with the
picker-good-capture exemption (`last_move_see_nonnegative`, 780). Block gate B 2096-2097, `prunable`
2126, move loop 2071. skip_quiets is read at Killer1 714, Killer2 718, CounterMove 722, GenerateQuiets
727, QuietMoves 731-739; never at the capture stages or the TT stages (684-688). A quiet check is
hidden like any quiet: checks live in the quiets list (generate_quiets 1003-1011) and are handed out
only in the QuietMoves stage, skipped whole at 731. Quiet promotions generate WITH the captures
(board.cpp 493-498) and are never hidden: HP = HC = 0. K3: the TT move leaves the picker before any
other stage (684-688) while `best_score > -MateInMaxPly` (2097) is still false, so it never enters the
block and T = 0. K7 anchors: root-list skip 2073-2075, restricted root never stored 2367, internal
iterative reduction 2033 takes a ply off a restricted root (PV node, tt_move none, IirDepth 2) — the
W oracle's D1 = d+1 / D2 = d+4 depths account for it.

**(3)** K1: 3 of 3 node sums exact (R 4294263, O 8315168, G 17611204; `s2/agg_output.txt`). K2: cells
equal 105 of 105 (35 of 35 rows, count build vs plain build on R/O/G). K3: T = 0 on every set
(`s2/agg_output.txt`, the identity check lines). K5: exact — Q38 3355, S38 3225, N38 3190, W38 2836
(`s3/log_R.qsnw.log`; rows 0 differing vs plain, node sum = K1, PRC sums = K2 on all 35 cells,
`s3/k1_k2_check.txt`). K6: all OK (LmpBase 20 probe: node 4003589, L 183745, WL 182358, HL 3446946,
F 36145, S 1104771, depth sum 9075; `s2/k6_output.txt`). Own count W0 = 924 WL/WF nodes of R with no
hidden quiet (WL 290972 + WF 53213 nodes in all).

**(4) Controls.** C-SIGN: ratio 13.64 (negated) vs 0.69 (no-negate) on job 34's 5365 P records —
PASS (bars 3 / 1.5). C-ALPHA: 200 Q records, alpha −29000: BEATS 197 of 197 non-mate records (3
mate-valued excluded as in job 34); alpha +29000: 0 of 197 — PASS. C-W: the whole log holds only 46
records with 1-6 hidden quiets (not 200; the 0.85 bar scales to 39.1 of 46). (a) THE SIGN: 18 of 20 =
0.900 — PASS, exactly at the 0.9 bar (15 of the 46 with |score| ≥ 150, plus 5 extension records with
n = 22..36; the first extension filter matched log lines by search idx and mixed in same-search
siblings — caught, rebuilt by exact line content, re-run; `ctrl/cw_output.txt`). (b) THE MEANING:
40 of 46 = 0.870 ≥ 0.85 — PASS; the W records are judged the searchmoves way. All three control
scripts' raw passes and verdicts: `kimi5/job38/ctrl/`.

**(5) The prediction, graded cell by cell** (`kimi5/job38/prediction.txt`, committed alone as
"kimi5 job 38 prediction" before any oracle run on Q/S/N/W, never edited):

| cell | predicted range (D2, per 1,000) | measured (D2) | inside? |
|---|---|---|---|
| Q | 0–40 | 3.0 [1.6, 5.5] | yes |
| S | 5–60 | 2.2 [1.1, 4.5] | NO — below |
| N captures | 1–40 | 6.8 [4.2, 10.8] | yes |
| N quiet checks | 20–150 | 2.9 [0.8, 10.6] | NO — below |
| W cause L | 100–350 | 273.7 [256.0, 292.1] | yes |
| W cause F | 60–300 | 10.3 [4.4, 23.9] | NO — below |
| dearest class | W cause L | W cause L (66.37 vs next 2.14) | yes |

**(6) The Step 5 table and the readings** — `kimi5/job38/table_j38.py` (committed, prints how many
records it read), output `kimi5/job38/step5_table.txt`. PRICE = class total on R / 1,200 × BEATS
share (the estimated pruned moves — for W: nodes — per search that would have beaten alpha):

| row | total on R | recs | D1 /1,000 [95%] | D2 /1,000 [95%] | D2 price |
|---|---|---|---|---|---|
| F (job 34's records) | 11633 | 11633 | 49.2 [45.4, 53.3] | 61.6 [57.4, 66.2] | 0.60 |
| P RAISED=1 (job 34) | — | 180 | 616.7 [543.9, 684.6] | 544.4 [471.5, 615.5] | — |
| P RAISED=0 (job 34) | — | 3627 | 45.2 [38.9, 52.5] | 68.9 [61.1, 77.6] | — |
| P RAISED=−1 (job 34) | — | 1558 | 4.5 [2.2, 9.2] | 5.8 [3.0, 10.9] | — |
| Q (quiet futility) | 58893 | 3355 | 0.6 [0.2, 2.2] | 3.0 [1.6, 5.5] | 0.15 |
| S (SEE, plain quiet) | 757864 | 3225 | 1.6 [0.7, 3.6] | 2.2 [1.1, 4.5] | 1.37 |
| N captures | 378267 | 2504 | 2.8 [1.4, 5.8] | 6.8 [4.2, 10.8] | 2.14 |
| N quiet checks | 94487 | 686 | 0.0 [0.0, 5.6] | 2.9 [0.8, 10.6] | 0.23 |
| W cause L | 290972 | 2342 | 266.4 [248.9, 284.7] | 273.7 [256.0, 292.1] | 66.37 |
| W cause F | 53213 | 485 | 16.5 [8.4, 32.2] | 10.3 [4.4, 23.9] | 0.46 |
| W no hidden quiet | 924 | 9 | no search, no BEATS | no search, no BEATS | — |

Splits (D2 per 1,000; D1 in `step5_table.txt`): Q at PV 24.3 vs 1.6 off PV; S 1.2 vs 2.5; N 20.6 vs
3.9; W 346.6 vs 211.7. S in check 0.0 (38 records) vs 2.2; N in check: 0 records exist. Q by
lmr_depth 0-1/2-3/4+: 2.5 / 3.7 / 6.2; S: 1.3 / 3.4 / 0.0. W by depth 1-2/3-4/5+: 250.1 / 178.2 /
154.4. W by hidden quiets 1-5/6-20/>20: 147.1 / 206.7 / 236.1.

Readings (D2 decides, D1 beside it in the file):
- THE RULE SELECTS for all four named rules: Q 3.0, S 2.2, N captures 6.8, N quiet checks 2.9 per
  1,000 — every one under half of the pooled P rows (66.5/1,000 → bar 33.3).
- THE DEAREST CLASS, order of all seven by D2 price: **W cause L 66.37** ≫ N captures 2.14 > S 1.37
  > F 0.60 > W cause F 0.46 > N quiet checks 0.23 > Q 0.15.
- PV IS DEARER for Q (ratio 15.3, intervals disjoint), for N (5.2, disjoint) and for W (1.64,
  disjoint). PV IS NOT DEARER for S (0.46).

---

In three plain lines: Fable asked what each pruning rule of the move loop costs — how often the
pruned move would have beaten alpha, and which class of pruning is the dearest per search. Answer:
the four active rules are all cheap and all "select" (≤ half the not-fired baseline), and by far the
dearest class is not a prune at all but the late-move rule's hidden quiets: about 66 nodes per search
hold an untried quiet the oracle says beats alpha, 31× the next class. How sure: the mechanism,
counts and oracle all passed their planted-fault controls and the known-answer cells; the W number
rests on the searchmoves reading of "hidden quiets", whose own control passed at 87% agreement — the
biggest caveat of the job, named below and in the job's own "what this check cannot see".

## Step table

| step | done | evidence | result |
|---|---|---|---|
| 0 numbers | done | `kimi5/job38/step0/` | 8/8 exact |
| 0 K7 | done | `kimi5/job38/step0/k7_*.txt`, `k7_j38.py` | 12/12 cells equal |
| 1 reading | done | `kimi5/job38/step1_reading.md` | six sites, picker readers, K3/K7 anchors |
| 2 counting copy | done | `kimi5/job38/s2/`, `prune_classes.patch.txt` (roundtrip `-p1 -F0`) | rows 0 differing; K1 3/3; K2 105/105; K6 OK; W0 924 |
| 3 logging copy | done | `kimi5/job38/s3/`, `prune_log.patch.txt` (roundtrip `-p1 -F0`) | K5 exact; rows and sums still equal |
| controls | done | `kimi5/job38/ctrl/` | C-SIGN, C-ALPHA, C-W(a), C-W(b) all PASS |
| prediction | done | `kimi5/job38/prediction.txt` | committed before the oracle runs; graded above |
| 4 oracle | done | `kimi5/job38/oracle/` (32 passes, plain build `068f0927768d` on every DONE line, all records, no fallback) | 13,606 records × D1+D2; `oracle/merge_checks.txt`: rows = K5 per file, no nulls outside the 9 n=0, 12 spot lines fen-matched, PROBLEMS none |
| 5 table | done | `kimi5/job38/table_j38.py`, `step5_table.txt` | above |

## Findings (each with source file:line of the mechanism; the measured numbers reappear with
`python3 forge-combo29/kimi5/job38/table_j38.py`)

1. **The dearest class is the late-move rule's hidden quiets, by a factor of 31.** Mechanism: when
   `move_count >= lmp_threshold(depth, improving)` the loop sets `skip_quiets = true`
   (search.cpp 2122 of the chain tree) and every later quiet — including quiet checks, which live in
   the quiets list (1003-1011) and are handed out only by the QuietMoves stage that `skip_quiets`
   skips whole (731) — is never tried. On R these nodes are 290,972 per 1,200 searches with 3,446,946
   hidden quiets (K2). The oracle (one restricted-root search per sampled node, depths corrected for
   the root losing a ply, search.cpp 2033) says 273.7 of 1,000 such nodes hold a hidden quiet that
   beats the node's end alpha: price 66.4 nodes per search. D1 says 266.4 — the verdict is nearly
   depth-flat, so this is a property of the nodes, not of the oracle's extra ply.
2. **A futility fire marks the position; a late-move-rule fire does not.** W cause F (nodes where a
   quiet failed futility, 2132-2141, and quiets were then hidden): 10.3/1,000. W cause L (pure
   late-move rule): 273.7/1,000 — 27× dearer on 5.5× the nodes. The futility test's `static_eval +
   margin <= alpha` already proves the position alpha-poor; LMP's move-count threshold proves nothing
   about the position.
3. **All four active rules select.** Q (3.0), S (2.2), N captures (6.8), N quiet checks (2.9) per
   1,000 at D2 against the 33.3/1,000 bar (half of pooled P). The pruned moves these rules choose
   are genuinely the worst: an order of magnitude under the not-fired baseline (66.5) and under
   job 34's history prune (61.6).
4. **PV nodes are the expensive seats** for Q (24.3 vs 1.6, disjoint intervals), N (20.6 vs 3.9,
   disjoint) and W (346.6 vs 211.7, disjoint); not for S (1.2 vs 2.5). The same was true in job 34's
   F splits. Whatever is bought at PV nodes is bought at the highest price per record.
5. **W cause L gets cheaper with node depth** (d 1-2: 250.1; 3-4: 178.2; 5+: 154.4 per 1,000) **and
   dearer with the number hidden** (1-5: 147.1; 6-20: 206.7; >20: 236.1) — the wider the hidden
   pack, the more likely one of them beats alpha; the deeper the node, the better the loop's
   ordering already is.
6. **Quiet promotions are generated with the captures** (board.cpp 493-498, inside
   `if constexpr (!quiets_only)`) so no legal capture or non-capture promotion is ever hidden:
   HP = HC = 0 on every set (K2 cells), and NRp > 0 confirms they reach the loop via the capture
   stages.
7. **The TT move never enters the pruning block** (picker returns it at 684-688 while the gate's
   `best_score > -MateInMaxPly` at 2097 is still false): T = 0 on every set, so `prunable` (2126) is
   true at every block entry.
8. **Capture futility is dead code under PC20** (gated on `tune::CaptureFutilityBase > 0`, 2156):
   CF = 0 on every set.
9. **N in check: 0 records; S in check: 38 records, 0 beats.** The noisy-SEE block effectively never
   fires in check on R; the SEE-of-a-quiet test does, rarely, and was never wrong in the sample.

Suspicions, not proven:
- The W oracle's 27% may overstate what a game would feel: a beaten end alpha at a fail-low-leaning
  node is not a changed game result (the job's own list below), and the restricted-root reading
  agreed with the one-by-one reading on 87% of the n ≤ 6 records — for n ≥ 7 records (2,164 of
  2,827) it is the only reading taken.
- The 46-record C-W(b) base is thin (the written 200 do not exist in the log); 0.870 on 46 is a
  weaker guarantee than 170/200 would be.
- The two C-W(a) sign mismatches (score −284 → BEST +15; score +264 → BEST −754) are both big-score
  records the two readings disagree on completely; not investigated further.

## From my colleagues
- deepseek5 (`for-fable-and-opus/deepseek5-work` 731fc808): NOTES tail and REPORT_deepseek5_job30
  read. Applied: his job-29/30 lesson "read a state variable at the moment the event happens, not
  one step later" is exactly the W record's design — end alpha, best score, cause and the hidden
  list are snapshotted at node end, not reconstructed later; and his corrected stage rates
  (CounterMove's history entry worse than Killer2's) are about the history table my F/P rows price,
  so his warning was carried into reading F alongside the new classes. Checked: his stand5 runner
  protocol (moves from the START position) is what my `replay_j38.py` does.
- glmflash5: the branch `for-fable-and-opus/glmflash5-work` does not exist (`git ls-remote`).
  `for-fable-and-opus/glmflash-work` (7b9e4ad1, tip "glmflash job 6 report", 2026-11-16) read
  instead; it holds no NOTES_glmflash.md and nothing touching this job. Said here as required.

## What I did NOT do
- No every-2nd fallback was needed (the oracle finished all 13,606 records at both depths in
  seconds); nothing was dropped: no kind, no depth, no control.
- The two C-W(a) sign-mismatch records were not individually explained.
- No match play, no engine change measured for strength: the price list says what the oracle says,
  not what wins games (that is glmflash5's and the PC's part).

## What I am NOT sure about
- C-W(a) passed exactly at its bar (18 of 20 = 0.900); one more mismatch would have stopped the W
  oracle. The W numbers stand on a control that passed with no margin.
- Whether "end alpha" is the right bar for a hidden quiet at a node that never raised alpha: the
  first quiet that beats alpha would have raised it, but at a node destined to fail low that raise
  might still lose to beta. The job defines BEATS against end alpha; I measured that.
- The W-no-hidden row's 9 records carry no information about the 924 nodes (no search exists for
  them by definition).

## A better way
The W question is now answered by a second, restricted-root search whose TT state, history table and
countermove context are all fresh — not the node's own. A cleaner instrument would be a debug option
(e.g. `DebugNoSkipQuiets`) that replays the SAME search with `skip_quiets` forced false at LMP nodes
while every other mechanism stays, on the same game and the same thread: the difference in node
outcomes is then attributable to the hidden quiets alone, with the real tables warm. It is
checkable against this job's method: on the same 20 games, the per-node BEATS verdict of both
methods should agree on ≥ 90% of the sampled WL nodes; if the warm-context number is much lower
than 27%, today's 66.4 overstates the case, and if it agrees, the searchmoves oracle is vindicated
cheaply. Cost: one guarded `if` at 2122, no behaviour change with the option off. Separately, a
purely procedural saving: W-L's D1 ≈ D2 (266.4 vs 273.7), so future W passes can run D1 only.

## What this check cannot see (from the job file, as written)
The PC's net (your runs use the built-in evaluation) and its engine build; go nodes 20000 and
deeper; more than one thread; the oracle is a second search from an empty table, not the truth, and
for W it is a root search with a move list, which the engine may treat differently from an inner
node (C-W says how far the two ways agree, no more); a move that beats alpha at the oracle's depth
is not a move that changes the game; and whether any threshold plays better at another value: that
is a match on the PC.

## Times
See `kimi5/job38/stamps.txt` (start of the run first; every line names its source; all stamps from
`date -u` or file mtimes).

## Model
Kimi K3 (runtime slug kimi-k3).

## git status and job folder listing (last command before the report commit)
```
$ git status --short
M  forge-combo29/NOTES_kimi5.md
A  forge-combo29/REPORT_kimi5_job38.md
A  forge-combo29/kimi5/job38/oracle_j38.py

$ ls -R forge-combo29/kimi5/job38
forge-combo29/kimi5/job38:
agg_j38.py
ctrl
k7_j38.py
oracle
oracle_j38.py
pc20_all1024.opt
pc20_lmp20.opt
pc20.opt
prediction.txt
prune_classes.patch.txt
prune_log.patch.txt
replay_j38.py
replay_j38s3.py
runner_j38.py
s14.opt
s2
s3
stamps.txt
step0
step0_j38.sh
step1_reading.md
step5_table.txt
table_j38.py

forge-combo29/kimi5/job38/ctrl:
csign_calpha_output.txt
cw_output.txt
p_d1_r01.jsonl
p_r01_nosign_d1.jsonl
q200_d1.jsonl
w200_16_1by1.jsonl
w200_16_d1.jsonl
wext5_1by1.jsonl
wext5b_1by1.jsonl
wext_g7_d1.jsonl

forge-combo29/kimi5/job38/oracle:
merge_checks.txt
n_d1_all.jsonl
n_d1_p0.jsonl
n_d1_p1.jsonl
n_d1_p2.jsonl
n_d1_p3.jsonl
n_d2_all.jsonl
n_d2_p0.jsonl
n_d2_p1.jsonl
n_d2_p2.jsonl
n_d2_p3.jsonl
q_d1_all.jsonl
q_d1_p0.jsonl
q_d1_p1.jsonl
q_d1_p2.jsonl
q_d1_p3.jsonl
q_d2_all.jsonl
q_d2_p0.jsonl
q_d2_p1.jsonl
q_d2_p2.jsonl
q_d2_p3.jsonl
s_d1_all.jsonl
s_d1_p0.jsonl
s_d1_p1.jsonl
s_d1_p2.jsonl
s_d1_p3.jsonl
s_d2_all.jsonl
s_d2_p0.jsonl
s_d2_p1.jsonl
s_d2_p2.jsonl
s_d2_p3.jsonl
w_d1_all.jsonl
w_d1_p0.jsonl
w_d1_p1.jsonl
w_d1_p2.jsonl
w_d1_p3.jsonl
w_d2_all.jsonl
w_d2_p0.jsonl
w_d2_p1.jsonl
w_d2_p2.jsonl
w_d2_p3.jsonl

forge-combo29/kimi5/job38/s2:
agg_output.txt
cnt_G_input.log
cnt_G.jsonl
cnt_G.meta
cnt_G.prc.log
cnt_O_input.log
cnt_O.jsonl
cnt_O.meta
cnt_O.prc.log
cnt_R_input.log
cnt_R.jsonl
cnt_R_lmp20_input.log
cnt_R_lmp20.jsonl
cnt_R_lmp20.meta
cnt_R_lmp20.prc.log
cnt_R.meta
cnt_R.prc.log
k6_output.txt
pln_G_input.log
pln_G.jsonl
pln_G.meta
pln_G.prc.log
pln_O_input.log
pln_O.jsonl
pln_O.meta
pln_O.prc.log
pln_R_input.log
pln_R.jsonl
pln_R.meta
pln_R.prc.log

forge-combo29/kimi5/job38/s3:
k1_k2_check.txt
log_R_input.log
log_R.jsonl
log_R.meta
log_R.prc.log
log_R.qsnw.log

forge-combo29/kimi5/job38/step0:
exe.sha256
k7_p1_all_input.log
k7_p1_all.txt
k7_p1_plain_input.log
k7_p1_plain.txt
k7_p1_two_input.log
k7_p1_two.txt
k7_p2_all_input.log
k7_p2_all.txt
k7_p2_plain_input.log
k7_p2_plain.txt
k7_p2_two_input.log
k7_p2_two.txt
k7_p3_all_input.log
k7_p3_all.txt
k7_p3_plain_input.log
k7_p3_plain.txt
k7_p3_two_input.log
k7_p3_two.txt
k7_p4_all_input.log
k7_p4_all.txt
k7_p4_plain_input.log
k7_p4_plain.txt
k7_p4_two_input.log
k7_p4_two.txt
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
```
