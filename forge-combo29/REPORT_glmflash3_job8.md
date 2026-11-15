# glmflash3 job 8 report (2026-11-15)

## 1. First line

**`NullMoveHanging` does not gain strength per node at 20,000 nodes a move on this tree, in either
form: value 1 (refuse the null move at a node where a piece hangs) pools M1+M2 to +2.9 Elo
(95 % pair interval [−4.3, +10.1], 4000 games); value 2 (try it but verify the cutoff) pools
M3+M4 to +1.6 [−5.4, +8.5] (4000 games). Both intervals straddle zero. The option-off build is
proven identical (Step 0 + the 2000-position hash = `3c976155...`).** Context from P1: the guard
fires on 15.9 % (value 1) / 17.5 % (value 2) of null attempts — no rarity — and on this bench the
value-2 verification confirmed 100 % of the hanging-node cutoffs it checked (775/775), which is
the likely reason value 2 changes nothing: the engine's existing verification (every cutoff at
depth ≥ 14, plus `NullThreatVerify` below) plus the guard's rarity leave nothing for it to catch
in real searches either.

Cut or not reached, first paragraph as asked: nothing was cut — C (300/300) and all four M
matches completed their full 2000 games (the equal-share caps proved generous; measured rates
2.28-2.42 games/s), all proofs P1-P6 ran complete, and the report was written before the 70-minute
mark.

## 2. Step 0 (unpatched build; known numbers)

Tree: commit 6b98f217 (jobs 2-3's tree), build flags (once, every build):
`cmake -S patched -B build-patched -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++` with the
tree's own defaults (the combo29 CMakeLists sets `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`,
`FORGE_NNUE_HIDDEN=256`, `FORGE_SEARCH_SPEED2=1`, `FORGE_EXPOSE_TUNABLES=1`). Fresh engine process
per bench; input: Threads 1, Hash 16, OwnBook false, then the option lines. Raw outputs `saved8/*.out`.

| config | command | expected | printed | match |
|---|---|---|---|---|
| unpatched | bench 11 | 312866 | 312866 | yes |
| unpatched | bench 13 | 862329 | 862329 | yes |
| unpatched | bench 16 | 3024920 | 3024920 | yes |
| unpatched | go perft 5 | 4865609 | 4865609 | yes |
| patched, NullMoveHanging off | all four | the same | identical | yes |
| patched, NullMoveHanging 1 | bench 11 | (must differ) | 341351 | differs ✓ |
| patched, NullMoveHanging 1 | bench 13 | (must differ) | 929201 | differs ✓ |
| patched, NullMoveHanging 1 | bench 16 | (must differ) | 3246268 | differs ✓ |
| patched, NullMoveHanging 2 | bench 11 | (must differ) | 313045 | differs ✓ |
| patched, NullMoveHanging 2 | bench 13 | (must differ) | 789456 | differs ✓ |
| patched, NullMoveHanging 2 | bench 16 | (must differ) | 3215434 | differs ✓ |

**P2 identity** (2000 depth-9 answers, option off): unpatched sha256 = patched sha256 =
`3c976155ede937860062ac79eeefa01894ef0bd4a03360fa5d6d90065cd8353f` (the same hash as jobs 2/3/4 —
the unchanged lock search), smallest node count 4534 both sides (`p2_orig.txt`, `p2_patched_off.txt`).

## 3. The feature as built

**No new table** — the job's P1/P6 wording about table size has no object here; the feature is a
gate on the existing null-move block, reusing the engine's own threat scan.

- **The hanging test**: `cheaper_enemy_attacks_dearer(board)` (`src/search.cpp:154-170`) — the
  engine's existing whole-board scan written for `NullSeeVeto`: it walks the side-to-move's
  knights, bishops, rooks and queens and reports true when an ENEMY attacker of strictly lower
  `SeePieceValue` exists (pawn 1 < minor 3 < rook 5 < queen 9; a king is never an attacker — the
  same cheaper-attack definition the quiet-history threat index `quiet_threat_index`
  (`search.cpp:290+`) encodes per move). I reused it rather than writing a second attack scan; it
  is called at most ONCE per null-candidate node and only when the option is on (short-circuit on
  `tune::NullMoveHanging`), so the option-off cost is zero and the on-cost is one scan per null
  candidate (~a few hundred ns; P6 shows no measurable nps cost).
- **Value 1** (`search.cpp:1715`): appended to the null-move condition:
  `&& !(tune::NullMoveHanging == 1 && cheaper_enemy_attacks_dearer(board))` — at a hanging node
  the whole null try is skipped (the node is searched on as if the block did not exist).
- **Value 2** (`search.cpp:1741`): the early-cutoff line becomes
  `if (depth < 14 && !threat_gate && !(tune::NullMoveHanging >= 2 && cheaper_enemy_attacks_dearer(board)))`.
  With value 2 at a hanging node the null search runs, but its cutoff is NOT taken directly: the
  existing verification path runs instead — `search(board, ss, depth - reduction, beta - 1, beta,
  false)` on the REAL position (the null move is already unmade), same reduced depth, same window
  — and only `verification >= beta` takes the cutoff; otherwise the node continues as if no null
  move had been tried. This reuses the verification machinery the engine already has (it verifies
  every cutoff at depth >= 14 unconditionally, and below 14 when `NullThreatVerify` is on); my
  clause extends forced verification to hanging nodes at every depth. The verification does not
  block null moves inside itself (the existing `threat_gate` path blocks; mine does not — the job
  text does not ask for blocking and the depth-14 default does not block either).
- **UCI**: `NullMoveHanging` is a spin declared and parsed through the tree's tunables table
  (`tune::parameters()`, row `{"NullMoveHanging", &NullMoveHanging, 0, 2}` added after
  `FailLowContinuationBonus`): the `uci` answer lists it (`FORGE_EXPOSE_TUNABLES=1` is defined for
  this target) and the setoption handler clamps to [0, 2]. Flag defined `int NullMoveHanging = 0;`
  in `tune::` next to the other switches. With the option 0, not one node changes (Step 0 + P2).

## 4. P1 (counters, traced copy; `nh_trace.patch.txt`)

The traced build's counters (bench 13, option on; node counts identical to the untraced patched
build — 929201 for value 1, 789456 for value 2 — so tracing changed nothing):

| value | null candidates | at a hanging node | share | of those, cut off | share | of those cutoffs, verification confirms | share |
|---|---|---|---|---|---|---|---|
| 1 | 15161 | 2412 refused | **15.9 %** | — (refused, not played) | — | — | — |
| 2 | 12999 tried | 2275 tried at a hanging node | **17.5 %** | 775 | **34.1 %** of hanging-node attempts | 775 | **100.0 %** |

Read: the guard is no rarity — about one null attempt in six happens at a node where a piece
hangs (far above the 1 % "cannot matter" line, below the 30 % "costs depth" worry). On THIS bench
the value-2 verification confirmed every hanging-node cutoff (775/775) — on the bench the check
changes nothing but its own cost; whether that holds in games is what M3/M4 measure (the bench's
single position family is not a game sample). Raw outputs `saved8/trace_v1_bench13.out`,
`saved8/trace_v2_bench13.out`.

## 5. P4 (sanitizers)

ASan+UBSan build of the patched tree; planted-fault control first (`fault.c`, same as jobs 2/8:
one byte past a 4-byte heap block, same flags): exit 1, exactly one `ERROR: AddressSanitizer` on
stderr (`fault_stderr.txt`). Then option on: `bench 13` value 1 → rc 0, 929201 nodes, stderr 0
bytes; value 2 → rc 0, 789456 nodes, stderr 0 bytes (`asan_bench_v1.out/.stderr`,
`asan_bench_v2.out/.stderr`); 200 book positions at depth 9 with value 2 → 200 answers, stderr
0 bytes (`asan_200_answers.txt`, `asan_200_stderr.txt`).

## 6. P6 (speed, honestly)

10 interleaved `bench 16` pairs each (same binary, option in the input only; `speed_v1.txt`,
`speed_v2.txt`): **NullMoveHanging 1: mean ratio 0.9894** (spread 0.8945-1.0732);
**NullMoveHanging 2: mean ratio 1.0019** (spread 0.9569-1.0485). Both means sit inside their own
spread — no measurable nps cost on the bench; the real cost of value 2 is the extra verification
SEARCHES, which change the tree (789456 vs 862329 nodes at bench 13) rather than the per-node
speed. **No new table exists: the feature adds 0 bytes per thread.** Rough figures, different
trees, as always.

## 7. The matches

| match | cand | base | seed | games (complete pairs) | W-L-D | fastchess Elo ± | my Elo [95 % pair] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| C | nodes 20000 | nodes 10000 | 8200 | 300 / 300 (150) | 183-28-89 (fast) | +198.66 ± 33.07 | +198.7 [+167.1, +233.5] | 0 |
| M1 | NullMoveHanging 1 | off | 8201 | 2000 / 2000 (1000) | 592-549-859 | +7.47 ± 10.18 | +7.5 [−2.7, +17.7] | 0 |
| M2 | NullMoveHanging 1 | off | 8202 | 2000 / 2000 (1000) | 560-570-870 | −1.74 ± 10.13 | −1.7 [−11.9, +8.4] | 0 |
| M3 | NullMoveHanging 2 | off | 8203 | 2000 / 2000 (1000) | 607-582-811 | +4.34 ± 10.29 | +4.3 [−6.0, +14.6] | 0 |
| M4 | NullMoveHanging 2 | off | 8204 | 2000 / 2000 (1000) | 577-584-839 | −1.22 ± 9.42 | −1.2 [−10.6, +8.2] | 0 |

**Pools (complete pairs, both seeds of each value):**
- Value 1 (M1 8201 + M2 8202): 4000 games, 2000 pairs, W-L-D 1152-1119-1729, score 0.5041 →
  **+2.87, 95 % pair interval [−4.32, +10.05]**.
- Value 2 (M3 8203 + M4 8204): 4000 games, 2000 pairs, W-L-D 1184-1166-1650, score 0.5022 →
  **+1.56, 95 % pair interval [−5.41, +8.54]**.

## 8. How the games ended (per match, from fastchess's own finish lines; `endings.py` committed)

| match | total with reason | White mates | Black mates | 3-fold | fifty-move | insufficient material | stalemate | faults (crash/illegal/disconnect) |
|---|---|---|---|---|---|---|---|---|
| C | 300 | 95 | 116 | 63 | 12 | 13 | 1 | 0 |
| M1 | 2000 | 619 | 522 | 553 | 153 | 146 | 7 | 0 |
| M2 | 2000 | 609 | 521 | 559 | 145 | 162 | 4 | 0 |
| M3 | 2000 | 628 | 561 | 536 | 137 | 133 | 5 | 0 |
| M4 | 2000 | 643 | 518 | 555 | 124 | 154 | 6 | 0 |

Every game in every match carried a termination reason from fastchess itself; no game ended by
crash, illegal move, disconnect or timeout, and no game was left without a reason (the per-match
`endings` outputs are in the job folder as `endings_<match>.txt`).

## 9. Files of the repository I opened

- `src/search.cpp` — the null-move block (1703-1760: condition, make/unmake, cutoff, the existing
  verification path), `cheaper_enemy_attacks_dearer` (150-171), `null_see_veto_threat` (1177+,
  read to make sure my gate does not interact with it), `quiet_threat_index` (290+, re-read for
  the shared cheaper-attack definition), tune definitions (93-100) and `parameters()` (114-152).
- `include/forge/search.hpp` — the tune externs block (297+), parameters table (unchanged).
No engine source modified in the repository; the deliverable is `null_move_hanging.patch.txt`.

## 10. Stamps of every step

All UTC from `/tmp/g3job8/stamps.txt` (committed copy in the job folder). Job start (reading
file 8) ~22:53:00; budget end (80 min) 00:13:00; the 70-min stop-and-write mark 00:03:00 — every
step finished before it.

| step | start | end |
|---|---|---|
| patched tree written + built; diff generated + apply-verified | 22:53:0x | 22:53:52 |
| traced copy written + built (two fix cycles: namespace qualification) | 22:53:52 | 22:54:10 |
| battery: step 0 + P3 on-benches + P1 trace runs | 22:54:1x | 22:54:3x |
| P2 identity (first attempt failed on a relative path, rerun) | 22:54:31 | 22:55:17 |
| ASan build + fault control + benches both values | 22:55:20 | 22:55:44 |
| ASan 200 positions (value 2) | 22:55:46 | 22:56:01 |
| P6 speed pairs (both values) | 22:56:05 | 22:57:21 |
| chain launch | 22:57:26 | — |
| control C | 22:57:26 | 22:59:0x (300/300) |
| M1 (value 1) | 22:59:02 | 23:12:54 (2000/2000, cap 863 s unused) |
| M2 (value 1) | 23:13:00 | 23:25:41 (2000/2000) |
| M3 (value 2) | 23:25:46 | 23:39:17 (2000/2000) |
| M4 (value 2) | 23:39:23 | 23:54:49 (2000/2000) |
| pooled + report + commit + push | 23:54:50 | ~00:02 |

## 11. What I did not do

- No third seed for either value; no test of the two values TOGETHER (they are mutually exclusive
  settings of one spin by design; a "value 1 with a verify fallback" hybrid was not requested).
- No equal-time match (per-node figures only, as prescribed; the PC's adoption question is at
  250,000 nodes on its own tree — Fable's match, not mine).
- I did not instrument WHY the value-2 verification confirmed 100 % of bench hanging-cutoffs
  (e.g., whether the verification search finds the same move through the TT the null search
  warmed). The counters show the fact, not the cause.

## 12. What I am not sure about

- Both pooled results are nulls with intervals that would also admit a true gain of +8-10; my
  "does not gain" is the right reading of THESE matches, not a proof of absence at other node
  counts (the PC's 250,000-node match may still find something — the guard's share of null
  attempts could grow with depth; I did not measure the share at other depths).
- The value-2 100 %-confirmation on the bench: one position family, 775 cutoffs. If the
  verification confirms everything it is asked to, value 2 is pure cost in the bench's world —
  the matches' small positive/negative wobble around zero is consistent with "cost ≈ gain ≈ 0".
  A different book or much deeper searches could behave differently.
- The hanging test uses the engine's SEE values via `cheaper_enemy_attacks_dearer`; the job's
  phrasing (pawn attacks any of the four, minor attacks rook and queen, rook attacks the queen)
  matches SEE order exactly as far as I checked the table (kings excluded there and in my gate —
  a king can never "hang" by this definition even when attacked; the job text's list also omits
  the king).
- The speed ratios' spreads (0.89-1.07) are wide enough that a real ±2 % cost would hide inside
  them; the honest statement is "no measurable cost above ~±3 % on the bench".

## 13. A better way

1. **The existing verification machinery made value 2 nearly free to build — and its 100 %
   bench confirmation suggests the interesting experiment is not "verify hanging cutoffs" but
   "verify ALL cutoffs below depth 14"** (the engine verifies unconditionally only at depth ≥ 14).
   That is a one-line variant of my clause (drop the `cheaper_enemy_attacks_dearer` term) and one
   2×2000-game pair; if the all-cutoff verification is also ~0 per node, the depth-14 threshold
   itself is what carries the weight, which would be worth knowing before anyone tunes the
   threshold. How to check better than my nulls: run that variant's pair; if IT shows a gain,
   the hanging restriction was the blocker; if not, the threshold is arbitrary anyway.
2. **The P1-style counters should live in every feature job, not only the ones with tables** —
   this job's adapted P1 (fire rate, cutoff share, confirm share) is exactly what made the match
   results readable BEFORE they landed (I could predict "value 2 changes little" from the 100 %
   confirm rate alone). Suggest Fable put the three-share template in the standard job text for
   any gate-like feature.
3. **The endings counter (Fable's new rule) was 25 lines of python over the match output; it
   should become part of the standard runner** so every helper's reports carry it without each
   reinventing it (mine is committed as `endings.py`).

## 14. Model

GLM 5.3 Flash (glm-5.3-flash).
