# glmflash3 job 9 report (2026-11-15)

## 1. First paragraph

**Every switch in this family is strength-neutral per node at 20,000 nodes on this tree:
`NullThreatVerify` alone +1.0 (95 % pair interval [−8.7, +10.8], 2000 games), `NullSeeVeto` alone
+1.4 [−8.9, +11.7], both together +0.9 [−9.6, +11.3], and my `NullMoveHanging` 1 head-to-head
against `NullThreatVerify` +1.0 [−9.4, +11.5] — dead even. Nothing was cut: all five matches ran
to their full 2000 games (300 for C), faults 0 everywhere.** With job 8 (my two values +2.9 and
+1.6 pooled): four independent measurements of one idea, four nulls — the hanging-piece guard
does not gain per node at this level, and my re-design matches the existing switches exactly where
the bench predicted it would (identical node counts, identical fire/confirm counts).

## 2. Step 0: what is already there

### a. The switches, quoted, and every place that reads them

The `uci` answer (patched tree, unchanged from the base):
```
option name NullThreatVerify type check default false
option name NullSeeVeto type check default false
```
(`src/uci.cpp:225-226`; set: `uci.cpp:393-395` assigns `NullThreatVerify` in its own branch,
`uci.cpp:405` and `:413` route `NullSeeVeto` through the shared check chain; declared
`include/forge/search.hpp:301-302`; defined `src/search.cpp:102-103`.)

Every place that READS the switches (`src/search.cpp`):
- `NullThreatVerify`: **:1697** — `(!tune::NullThreatVerify || !null_blocked_)` in the null-move
  condition (a null move is not TRIED while a verification search of an ancestor is running);
  **:1727** — `depth < 14 && tune::NullThreatVerify && cheaper_enemy_attacks_dearer(board)` — the
  cutoff gate (a null cutoff below depth 14 is verified when a cheaper enemy piece attacks a
  dearer piece); **:1735** — `if (threat_gate) null_blocked_ = true;` (the verification search
  itself may not try null moves).
- `NullSeeVeto`: **:1701** — `!(tune::NullSeeVeto && null_see_veto_threat(board))` in the
  null-move condition — the veto at TRY time; **:1176-1194** — `null_see_veto_threat(Board&)`:
  makes a null move, walks the opponent's pseudo-legal CAPTURES, and reports true when one wins
  material by SEE (`attacker < victim` and `see_ge(move, 0)` after the pass) — i.e. "after I pass,
  they can just take something".
- Support: `null_blocked_` member (`include/forge/search.hpp:523-525`), reset at `:2161`.

### b. How the existing design differs from mine (ten lines), and the counters side by side

- `NullThreatVerify` and my value 2 are the SAME shape: null tried, cutoff verified by a reduced
  real-position search with the window (beta-1, beta). Differences: NTV acts only BELOW depth 14
  (deeper cutoffs verify anyway, unconditionally); it BLOCKS null moves inside its verification
  (`null_blocked_`); my value 2 acts at every depth (redundant at ≥ 14) and does not block.
- `NullSeeVeto` and my value 1 both refuse the null at try time, but the TESTS differ: NSV asks
  "does a winning enemy capture exist AFTER the pass" (a null move + pseudo-legal capture walk +
  SEE per capture — sees discovered/unmasked captures and needs legality); mine asks "does a
  piece of the side to move hang RIGHT NOW" (one static cheaper-attack scan, no null made, no
  move legality, no SEE walk). NSV is stricter about real captures, cheaper about cost per scan.
- Counters on `bench 13` (`traced9`, node counts identical to the untraced patched build):

| design | fires per node (÷862329) | fired | base it fires on |
|---|---|---|---|
| NullThreatVerify (gate at cutoff, depth < 14) | checks 8552 → 0.0099/node; fired 775 → 0.0009/node | 775 of 8552 cutoff checks (9.1 %); **confirmed 775 of 775 (100 %)** | null CUTOFFS below depth 14 |
| NullSeeVeto (veto at try) | scans 15141 → 0.0176/node; vetoed 2398 → 0.0028/node | 2398 of 15141 candidates (15.8 %) | null CANDIDATES (try time) |
| my NullMoveHanging 1 (job 8) | candidates 15161 → 0.0176/node; refused 2412 → 0.0028/node | 2412 of 15161 (15.9 %) | null CANDIDATES (try time) |
| my NullMoveHanging 2 (job 8) | tried 12999 → 0.0151/node; at hanging nodes 2275 (17.5 %); cutoffs there 775 (34.1 % of those) | 775 cutoffs; confirmed 775 (100 %) | null ATTEMPTS at hanging nodes |

The two independent designs agree almost exactly on the bench: NTV's fired/confirmed (775/775) is
my value 2's cut/confirm (775/775); NSV's vetoed (2398/15141 = 15.8 %) is my value 1's refused
(2412/15161 = 15.9 %) — and the bench NODE COUNTS: NTV on = 789456 = my value 2's 789456
(exactly); NSV on = 929140 vs my value 1's 929201 (61 nodes apart). Two designs written without
seeing each other land within 0.007 % of each other's trees on the bench.

### c. New bench numbers (each switch on; everything off = the four known answers ✓ on this tree)

| config | bench 11 | bench 13 | bench 16 |
|---|---|---|---|
| off (known) | 312866 ✓ | 862329 ✓ | 3024920 ✓ (perft 5 4865609 ✓) |
| NullThreatVerify on | 313045 | 789456 | 3215434 |
| NullSeeVeto on | 341355 | 929140 | 3136178 |
| both on | 341356 | 929170 | 3203100 |
| (job 8: my value 1 / value 2) | 341351 / 313045 | 929201 / 789456 | 3246268 / 3215434 |

Raw outputs `saved9/*.out`; counters `saved9/j9_trace_ntv.out`, `saved9/j9_trace_nsv.out`.

## 3. The probes

- **probe_x1**: cand `Threads 1`, `Hash 16`, `OwnBook false`, `NullThreatVerify true`; base the
  three base options. **probe_x2**: cand `NullSeeVeto true`. **probe_x3**: cand both switches
  true. **probe_x4**: cand `NullMoveHanging 1`, base `NullThreatVerify true` — the head-to-head's
  two different feature lines, both seen arriving in the log before the match (`probe_x4.txt`).
  All probes ran BEFORE their matches (the template carries them; stamp pairs in §6); both sides
  always received the three base options first, in order, in both games.

## 4. The matches

| match | cand | base | seed | games (complete pairs) | W-L-D | fastchess Elo ± | my Elo [95 % pair] | faults |
|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 8210 | 300 / 300 (150) | 185-19-96 (fast) | +216.51 ± 32.95 | +216.5 [+185.2, +251.3] | 0 |
| X1 | NullThreatVerify on | off | 8211 | 2000 / 2000 (1000) | 582-576-842 | +1.04 ± 9.72 | +1.0 [−8.7, +10.8] | 0 |
| X2 | NullSeeVeto on | off | 8212 | 2000 / 2000 (1000) | 570-562-868 | +1.39 ± 10.25 | +1.4 [−8.9, +11.7] | 0 |
| X3 | both on | both off | 8213 | 2000 / 2000 (1000) | 564-559-877 | +0.87 ± 10.41 | +0.9 [−9.6, +11.3] | 0 |
| X4 | NullMoveHanging 1 | NullThreatVerify on | 8214 | 2000 / 2000 (1000) | 582-576-842 | +1.04 ± 10.46 | +1.0 [−9.4, +11.5] | 0 |

How the games ended (per match, `endings.py` over fastchess's own finish lines; committed as
`endings_<match>.txt` in the job folder):

| match | total | White mates | Black mates | 3-fold | fifty-move | insufficient | stalemate | faults |
|---|---|---|---|---|---|---|---|---|
| C | 300 | 115 | 89 | 69 | 11 | 15 | 1 | 0 |
| X1 | 2000 | 616 | 542 | 563 | 129 | 144 | 6 | 0 |
| X2 | 2000 | 614 | 518 | 598 | 130 | 136 | 4 | 0 |
| X3 | 2000 | 597 | 526 | 585 | 147 | 142 | 3 | 0 |
| X4 | 2000 | 628 | 530 | 569 | 135 | 132 | 6 | 0 |

No game in any match ended by crash, illegal move, disconnect or timeout; every game carried a
termination reason.

## 5. Files of the repository I opened

- `src/search.cpp` — the null-move block (1695-1745), `null_see_veto_threat` (1176-1194),
  `null_blocked_` reset (2161), tune definitions (102-103).
- `src/uci.cpp` — option lines (225-226), the NTV branch (393-395), the shared check chain
  (405, 413).
- `include/forge/search.hpp` — externs (301-302), `null_blocked_` comment (520-525).
The job-8 patched tree is the working tree; NO new feature code this job (the traced copy's
counters are measurement scaffolding, committed as `nh_trace9.patch.txt`).

## 6. Stamps of every step

All UTC from `/tmp/g3job8/stamps.txt` (job 9 appended to the same file; committed copy in the job
folder). Job start (reading file 9) ~23:55:40; budget end (80 min) 01:15:40; the 70-min
stop-and-write mark 01:05:40 — every step finished before it.

| step | start | end |
|---|---|---|
| step 0a/0b code reading (grep + read, no build) | 23:55:4x | 23:55:4x |
| traced9 written + built (counters for the EXISTING switches) | 23:55:45 | 23:55:52 |
| bench battery (16 runs: 4 off + 3×3 switch configs + 2 traces) | 23:56:0x | 23:56:1x |
| chain launch | 23:56:20 | — |
| control C | 23:56:20 | 23:58:16 (300/300) |
| X1 (NullThreatVerify) | 23:58:23 | 00:12:53 (2000/2000) |
| X2 (NullSeeVeto) | 00:12:59 | 00:25:08 (2000/2000) |
| X3 (both) | 00:25:13 | 00:36:58 (2000/2000) |
| X4 (mine vs NTV) | 00:37:04 | 00:48:45 (2000/2000) |
| endings + report + commit + push | 00:49 | ~00:57 |

Every match ran well inside its 950-1242 s deadline (rates 2.30-2.86 games/s — the deadline caps
were sized for ~2.1/s and never bound).

## 7. What I did not do

- No third seed anywhere; no SPRT (the nulls are clear enough that none was asked for).
- No speed measurement of the existing switches (P6 was not in this job's list; job 8's speed
  section covered my designs; NSV's per-try SEE walk is the one place a cost could hide — say
  the word and I will run its pairs).
- X4 used my value 1 ("the better value of job 8": higher pooled point +2.87 vs +1.56, and it is
  the cheaper design — one scan per candidate, no verification searches). Value 2 vs NTV was not
  played; the bench says the two trees are IDENTICAL (789456 both), so a strength difference
  would have been noise-on-noise.

## 8. What I am not sure about

- The head-to-head X4 dead heat (+1.0 ± 10.5): two designs whose BENCH trees differ by 61 nodes
  (value 1 929201 vs NSV 929140 — different switches though; NTV vs my v1 differ much more) play
  to a 0.5 % score difference over 2000 games. I read "equal"; a 3-seed pool would firm it.
- The whole family nulls at 20,000 nodes. Whether the guards matter at the PC's 250,000-node
  test (where null cutoffs are rarer and deeper) is open — the fire RATES I measured are per
  bench node at depth 13; the share could shrink or grow with depth and I did not measure it.
- `NullSeeVeto`'s veto test and my value 1 agree to 15.8 % vs 15.9 % on the bench and to ~61
  bench nodes — but they are NOT the same predicate (SEE-winning capture AFTER the pass vs static
  attack NOW). The near-equality could break on other position families; one bench is weak
  evidence of design equivalence.
- The traced9 counters count gate EVALUATIONS, and the &&-chain order matters: NTV's gate only
  evaluates on cutoffs below depth 14 (its clause sits after the cutoff), NSV's only on candidates
  that passed every earlier condition. Both are the right denominators for "how often does it
  fire" as the job asks, but they are different populations (cutoffs vs candidates) — the side-
  by-side table says which is which.

## 9. A better way

1. **The dead heat in X4 plus the identical bench trees (my v2 = NTV at 789456 exactly) suggest
   the engine already contains the right design and my patch adds only the depth-independence.**
   The cheapest useful follow-up is not another match but ONE question to the PC's 250,000-node
   match: does the PC's engine verify cutoffs at depth ≥ 14 already (it does — inherited from
   this line of code) — if yes, `NullMoveHanging` as a whole is redundant THERE too, and the
   honest conclusion is "the inventory item t22 listed was already built in an earlier round;
   the t22 list needs a pass against the current engine before the next feature job." A
   checklist job ("list every switch `uci` prints, next to the t22 inventory items") would have
   caught this before job 8 spent its budget — the same lesson Fable taught the other helper
   tonight, applied to the job-writer's side.
2. **The near-identity of the two independent designs (61 bench nodes apart) is itself a
   validation tool**: when two helpers write the same feature blind, a bench-node diff that small
   says both implementations compute the same predicate; a LARGE diff would point at a real
   semantic difference worth investigating before any match is spent. Cheap: two bench runs.

## 10. Model

GLM 5.3 Flash (glm-5.3-flash).
