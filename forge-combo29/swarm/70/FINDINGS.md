# FINDINGS — seat 70, `searchmoves` protocol semantics

Branch `for-fable-and-opus/swarm-70`, folder `forge-combo29/swarm/70/`.
Engine: commit `6b98f217`, built at `/agent/repos/base` (worktree outside the work
tree), release, g++ 13.3.0, `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`,
sha256 `7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`.
Honesty pins all four match: `bench 11` 312866, `bench 13` 862329,
`bench 16` 3024920, `go perft 5` 4865609 (`honesty.txt`).

Every table below is the pasted output of a committed script that wrote a file.
Every FEN is validated with python-chess immediately before use, and every search
position is additionally checked with the engine's own `go perft 1` against
python-chess's legal-move count, so a silently-refused board cannot be mistaken
for a restriction effect. The `invalid FEN` diagnostic is scanned in BOTH the
`position` reply and the `go` output (`engine.py`, `_finish`).

---

## The one-line answer

`searchmoves` is not a filter over a fixed search. On this engine it is a
**different search**: a restricted root never stores a transposition-table entry
(`src/search.cpp:2093`), so the root has no hash move on the next iteration. That
single line is the whole of the reported bestmove perturbation, and it is what
makes a pinned score not the engine's score.

---

## F1 — naming all legal moves is not a no-op, and the cause is ONE line

`| 70-F1 | area 1 | a restricted root never stores a TT entry (src/search.cpp:2093), which alone reproduces the whole all-legal perturbation | job1/causal_split.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job1/causal_split.py
```

60 positions (`job1/pinpool.epd`), depth 12, `searchmoves <all legal>`, four builds:

| arm | what changed | bestmove == plain | score == plain |
|---|---|---|---|
| `base_all` | nothing (base engine) | 49/60 | 1/60 |
| `pA_all` | root TT store restored | **60/60** | **60/60** |
| `pB_all` | IIR spared at a restricted root | 51/60 | 7/60 |
| `pAB_all` | both | 60/60 | 60/60 |

Restoring the TT store alone returns the engine to its unrestricted answer on
every one of 60 positions and to its unrestricted score on every one of 60. The
IIR guard is a real but minor second contributor (51/60 moves, 7/60 scores).

The code, verbatim from the base commit:

```2093:2099:forge-combo29/src/search.cpp
    if (excluded.is_none() && !(root_node && root_restricted_)) {
#if FORGE_SPD_TT_NOTLS
        store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
#else
        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
#endif
    }
```

and the IIR line it interacts with:

```1784:1784:forge-combo29/src/search.cpp
    if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;
```

The patches are **scratch builds only**, never committed as source: `pA` deletes
`&& !(root_node && root_restricted_)`; `pB` adds the same negation to the IIR
condition. Both keep `bench 13` at 862329.

## F2 — the mechanism is NOT "reordering equal-scoring moves"

`| 70-F2 | area 1 | the changed bestmove carries a changed score in 22 of 22 cases, so the restriction changes the search, not a tie-break | job1/order_vs_search.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job1/order_vs_search.py
```

120 searches (60 positions x depths 10, 12). 22 changed bestmove. Of those 22,
**0/22 kept the same score**; 18/22 differ by >= 10 cp. The per-change deltas run
`-40 -12 8 248 1 -16 13 24 -62 29 -13 17 30 34 34 59 1 -50 -8 -46 -10 31`.
Only 4/120 searches had an unchanged score at all.

A tie-reordering account predicts exactly 22/22 unchanged. The 95% Wilson upper
bound on 0/22 is 0.149, so that account is rejected outright.

**But the tie question deserves its own instrument, and it gives a subtler
answer** — see F3.

## F3 — in positions whose tie is PROVEN, the restriction usually does not change the move

`| 70-F3 | area 1 | with a proven mate-in-1 tie set, `searchmoves <all legal>` keeps the same move in 53/60, so the ordinary-position changes are NOT tie-breaking | job1/ties.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/gen_positions.py     # proves the fixtures
python3 forge-combo29/swarm/70/job1/ties.py
```

Fixtures: positions where exactly 2, 3 or 5 legal moves deliver immediate
checkmate, proven by python-chess (`mate_in_1_moves`). Every mating move scores
mate at the root, so the tie is a **proof**, not the engine's opinion, and no
evaluation term or depth can separate them. 20 / 20 / 12 positions.

| set | depth | bestmove changed | base reported mate | all-legal reported mate | score equal |
|---|---|---|---|---|---|
| ties2 | 8 | 1/20 | 20/20 | 20/20 | 20/20 |
| ties2 | 10 | 1/20 | 20/20 | 20/20 | 20/20 |
| ties2 | 12 | 1/20 | 20/20 | 20/20 | 20/20 |
| ties3 | 8 | 1/20 | 20/20 | 20/20 | 20/20 |
| ties3 | 10 | 1/20 | 20/20 | 20/20 | 20/20 |
| ties3 | 12 | 1/20 | 20/20 | 20/20 | 20/20 |
| ties5 | 8 | 0/12 | 12/12 | 12/12 | 12/12 |
| ties5 | 10 | 0/12 | 12/12 | 12/12 | 12/12 |
| ties5 | 12 | 0/12 | 12/12 | 12/12 | 12/12 |

**Total 3/156 move changes on proven ties, against 22/120 on ordinary positions.**
The two changed positions are stable across all three depths:

- `5r2/2R5/K7/1R6/8/8/R4R2/4k3 w - - 0 1`: base `c7c1`, all-legal `b5b1`, both mate in 1.
- `6Q1/3n4/8/8/8/1K2R3/3R4/k7 w - - 0 1`: base `d2d1`, all-legal `e3e1`, both mate in 1.

So the restriction *can* pick a different member of a proven tie, but it rarely
does — and on ordinary positions it changes the move because it changes the
*score*, not because it re-shuffles a tie. **Both halves of the earlier account
are wrong in the direction claimed: the effect is a search change (F2) whose
tie-reordering component is small (3/156).**

## F4 — a pinned score is not the engine's score for that move

`| 70-F4 | area 1 | the pinned score of a move equals the score it got inside one unrestricted search in only 10 of 265 cases (sd 44 cp) | job1/pinned_vs_intree.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job1/pinned_vs_intree.py
```

For the engine's own top 5 moves, the score inside one unrestricted MultiPV 5
search vs the score that move gets when searched alone:

- (move, position) pairs: **265**
- identical: **10/265**  (95% CI 0.021–0.068)
- `|delta| >= 10 cp`: **211/265**
- `|delta| >= 50 cp`: **50/265**
- mean delta `-7.6`, median `-7.0`, min `-189`, max `+187`, **sd 44.2**
- top move only: identical **1/53**, `|delta| >= 10` **42/53**, mean `-12.5`

This is the precise defect: pinning does not *distort a known value*, it produces
a **different value** whose difference from the in-tree value has sd 44 cp.

## F5 — the distortion does NOT decrease with the number of pinned moves

`| 70-F5 | area 2 | pinning 1, 2, 4, 8 or all moves all distort about equally; more pins does not mean less damage | job2/pin_count.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job2/pin_count.py
```

60 positions, depth 12. `k=1` pins the move the plain search itself returned, so
it is exactly what a verifier does; larger `k` adds moves from the engine's own
MultiPV ranking.

| k pinned | n | bestmove preserved | score delta = 0 | `|delta| >= 10` | median `|delta|` |
|---|---|---|---|---|---|
| 1 | 60 | 60/60 | 1/60 | 48/60 | 28 |
| 2 | 60 | 54/60 | 1/60 | 47/60 | 24 |
| 4 | 60 | 54/60 | 3/60 | 45/60 | 23 |
| 8 | 60 | 51/60 | 2/60 | 44/60 | 22 |
| all | 60 | 49/60 | 1/60 | 46/60 | 26 |

There is no monotone trend: the median `|delta|` moves 28 → 24 → 23 → 22 → 26 and
the `|delta| >= 10` count moves 48 → 47 → 45 → 44 → 46. The distortion is
essentially **flat in k**, at about three-quarters of positions off by >= 10 cp.
A single pinned move is already fully distorted, which is the worst possible
answer for a verifier: there is no cheap "pin just the winner" escape.

## F6 — rank order is NOT preserved over 3 or 5 candidates

**This is the headline result and it contradicts the 8/8 two-candidate claim in
the brief for k >= 3.**

`| 70-F6 | area 3 | pinned-alone ranking agrees with the reference on 142/159 pairs at 3 candidates and 486/530 at 5, so a multi-candidate pinned comparison is not sound | job3/rank_final.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job3/rank_final.py
```

Reference validation is printed before any agreement number, because a bad
reference would make the whole table meaningless. 60 positions offered, depth 12:

- determinism, same command twice in fresh processes: **60/60**
- R1 = unrestricted MultiPV 5, rank-1 move == plain bestmove: **53/60**
- R1 rank-1 score == plain score: **53/60**
- R1 scores non-increasing over ranks: **60/60**

Because R1 is only right on 53/60 rank-1s, agreement is reported **only on those
53 positions**, with two references: R1 (unrestricted MultiPV) and R3 (MultiPV
restricted to the same candidate set the pin arm used, one search, main worker
for rank 1).

| ref | k | pair comparisons | agree | 95% Wilson | positions | exact full order |
|---|---|---|---|---|---|---|
| R1 | 2 | 53 | 48/53 | 0.797–0.959 | 53 | 48/53 |
| R1 | 3 | 159 | 139/159 | 0.814–0.917 | 53 | 35/53 |
| R1 | 5 | 530 | 475/530 | 0.867–0.919 | 53 | 20/53 |
| R3 | 2 | 53 | 47/53 | 0.774–0.947 | 53 | 47/53 |
| R3 | 3 | 159 | **142/159** | 0.835–0.932 | 53 | 40/53 |
| R3 | 5 | 530 | **486/530** | 0.890–0.938 | 53 | **30/53** |

**Answers to the question as asked: 142/159 pairs at 3 candidates, 486/530 at 5.
Full orderings exact in 40/53 and 30/53 positions.** Both intervals exclude 1.0,
so "pinning preserves rank order" is rejected at both k.

### F6a — the same result at depth 10, so it is not a depth-12 artefact

```bash
python3 forge-combo29/swarm/70/job3/rank_final.py --depth 10
```

Reference validity drops to 48/60 at depth 10, so the denominators shrink:

| ref | k | pair comparisons | agree | 95% Wilson | exact full order |
|---|---|---|---|---|---|
| R1 | 3 | 144 | 136/144 | 0.894–0.972 | 41/48 |
| R1 | 5 | 480 | 431/480 | 0.868–0.922 | 21/48 |
| R3 | 3 | 144 | 134/144 | 0.877–0.962 | 39/48 |
| R3 | 5 | 480 | 434/480 | 0.875–0.927 | 21/48 |

Same verdict, and the exact-full-ordering rate is the same story (about 80% at
k=3, 44% at k=5). Saved as `job3/rank_final_depth10.txt` and
`job3/rank_final_depth12.txt`.

### F6b — the strongest form of the test needs no reference at all

`| 70-F6b | area 3 | pinning each of the top 5 candidates alone makes the plain bestmove the top-scoring candidate in only 49 of 60 positions | job3/verifier_operation.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job3/verifier_operation.py
```

The reference in `rank_final` had a 53/60 caveat. This test removes the reference
entirely: take the plain search's answer `B`, pin `B` and each of four other
candidates alone, and ask whether `B`'s pinned number is the highest.

- pin arm's winner == plain bestmove: **49/60**
- pinned `B` strictly above all other candidates: **49/60**
- positions where some other candidate beat the plain best move: **11/60**
  (exactly one candidate beat it in 6, two in 4, three in 1)

Positions `[1, 2, 7, 19, 23, 25, 32, 43, 49, 53, 54]`. The plain search is
deterministic at 60/60, so this is the verifier's own procedure contradicting the
engine on 11 of 60 positions — with no reference to blame.

## F7 — but a comparison IS sound when the gap is large; the threshold is ~50 cp

`| 70-F7 | area 3 | pinned comparisons agree 313/317 when the candidates differ by >= 100 cp but only 478/511 at >= 10 cp, so the usable threshold is ~50-100 cp | job3/rank_why.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job3/rank_why.py
```

530 pair comparisons, 53 positions:

| reference gap | pairs | agree | fraction |
|---|---|---|---|
| >= 1 | 529 | 486/529 | 0.919 |
| >= 10 | 511 | 478/511 | 0.935 |
| >= 30 | 459 | 438/459 | 0.954 |
| >= 50 | 414 | 404/414 | 0.976 |
| >= 100 | 317 | 313/317 | 0.987 |

Compression, not noise: the median `|pinned gap| / |reference gap|` is 1.003 —
pinning does **not** systematically shrink gaps — but the 10th percentile is 0.475
and the maximum is 96x. So individual gaps can move by two orders of magnitude in
either direction; that is why small gaps scramble and large ones survive.

**This is the reconciliation with the brief's 8/8.** Two candidates pinned, when
they differ by a large margin, is sound. The 8/8 result is not wrong; it is a
large-gap sample. It does not license 3-way or 5-way comparisons, and it does not
license a top-pair comparison at 10 cp.

## F8 — what an empty, illegal, partial and malformed `searchmoves` does

`| 70-F8 | area 4 | an empty or all-illegal list gives bestmove 0000 + an info string and searches 0 nodes; a legal+illegal list silently DROPS the illegal member with no diagnostic | job4/degenerate.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job4/degenerate.py
```

Arms are built per position (a hard-coded `e2e4` is illegal once the e-pawn has
moved, which silently turns a "one legal move" control into another all-illegal
case — that bug bit this script first and the fix is in the file).

| arm | startpos | middlegame |
|---|---|---|
| E0 unrestricted | `d2d4` cp 14, n4523 | `b1c3` cp 48, n5295 |
| E1 bare `searchmoves` | `0000` cp 0, n0 + string | same |
| E2 one illegal move | `0000` cp 0, n0 + string | same |
| E3 legal + illegal | `g1h3` cp −40, n1359, **no string** | `c4f7` cp −248, n1475 |
| E4 illegal + legal | identical to E3 | identical to E3 |
| E5 one legal | identical to E3 | identical to E3 |
| E6 `0000` as a move | `0000` cp 0, n0 + string | same |
| E7 duplicated legal | identical to E3 | identical to E3 |
| E8 wrong case `E2E4` | `0000` cp 0, n0 + string | same |
| E9 zero-length | `0000` cp 0, n0 + string | same |
| EA two legal | `g1f3` cp −6, n2032 | `c4f7` cp −230, n960 |

Controls, all pass on both positions: C1 the harness distinguishes restricted from
unrestricted; C2 argument **order** is irrelevant (E3 == E4 exactly, nodes too);
C3 the plain search is deterministic.

Three consequences:

1. **Empty is an error, not a no-op.** `0000`, `cp 0`, `nodes 0`, plus
   `info string searchmoves restriction has no legal root moves`.
2. **A legal+illegal list is silently accepted with the illegal member dropped.**
   No `illegal move`, no `invalid value`. E3 is *byte-identical* to E5. So a
   corpus built from a mistyped move list is silently narrower than intended, and
   its scores carry the F5 distortion for a restriction you did not ask for.
3. **A fully-dropped list is indistinguishable from an empty one** (E6, E8, E9 all
   print the same string). The only honest way to distinguish them is the argument
   text, which a harness has.

## F9 — `0000` has four meanings and the stream can tell three of them apart

`| 70-F9 | area 4 | checkmate is `score mate 0`, stalemate `score cp 0`, restriction an `info string`; `0000` is not an unconditional error | job4/zero_move_meaning.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job4/zero_move_meaning.py
```

| case | 0000 | stream tell |
|---|---|---|
| checkmate | yes | `score mate 0`, no `info string` |
| stalemate | yes | `score cp 0`, no `info string` |
| empty restriction | yes | `info string searchmoves restriction has no legal root moves` |
| all tokens dropped | yes | same `info string` — indistinguishable from empty |

The brief's rule "treat `0000` as an error unconditionally" is therefore **wrong
for checkmate and stalemate roots**, which are legitimate terminal positions. The
correct rule is: `0000` is an error only when the `searchmoves` info string is
present.

## F10 — the `invalid FEN` diagnostic does land in the position reply

`| 70-F10 | CONFIRMS the coordinator's FEN-placement correction | job4/diagnostic_placement.txt | position reply contains the diagnostic, go output does not, when isready follows position |`

```bash
python3 forge-combo29/swarm/70/job4/diagnostic_placement.py
```

`position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1` with
`isready` after it gives, in the **position** reply before `readyok`:
`info string invalid FEN: castling right without king and rook`. The `go` output
contains no diagnostic. `engine.py` scans both streams regardless, which costs
nothing and is correct under either placement.

## F11 — every script can fail: planted faults

`| 70-F11 | control | seven planted faults are each caught by the corresponding check, and the one thing the check cannot see (a halfmove-clock edit) is named rather than hidden | selftest_falsify.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/selftest_falsify.py; echo $?
```

| check | planted fault | caught |
|---|---|---|
| F1 bad FEN | castling right without rook | yes (`perft1=None`, `err='invalid FEN'`, string in position reply) |
| F2 shifted board | one pawn moved | yes (`perft1` 20 -> 19) |
| F3 fake move | `e2e5` | yes (not in python-chess legal set) |
| F4 timeout | `go infinite`, 2 s | yes (`fatal='timeout waiting for bestmove'`) |
| F5 reversed order | pinned order inverted | yes (agreement 0/3) |
| F6 no mate | startpos | yes (`mate_in_1` returns `[]`) |
| F7 finds mates | known 2-mate position | yes (`['c7c1','b5b1']`) |
| F2b clock-only | halfmove counter +1 | **no, by design** — a perft check cannot see the clock; documented, not hidden |

`ALL PLANTED FAULTS HANDLED: True`, exit 0. The script exits non-zero if any
planted fault escapes.

Writing this test found two real bugs in my own code, which is the point of it:
`check()` was defined but never called (the results table was silently empty), and
`fake not in legal_set and legal_set` returned the legal-move *set* instead of a
boolean, so `True == <set>` was False. Both are fixed; a harness bug that prints a
confident wrong answer is worse than no harness.

## F12 — the one-line fix repairs the CONTROL and does NOT repair the MEASUREMENT

`| 70-F12 | area 1 | restoring the root TT store makes `searchmoves <all legal>` a true no-op (60/60) but leaves a single pinned score wrong (9/265 vs 10/265, p=1.00) | job1/fix_vs_pinned_score.txt | NEW |`

```bash
python3 forge-combo29/swarm/70/job1/fix_vs_pinned_score.py
python3 forge-combo29/swarm/70/job1/fix_significance.py
```

F1 showed patch A fixes the all-legal control. That is a statement about the
**control**. It says nothing about a one-move root, which is what a verifier
runs. This measures that question directly: 53 positions, 265 (move, position)
pairs, both builds.

| comparison | n | identical | `|d| >= 10` | `|d| >= 50` | mean | sd |
|---|---|---|---|---|---|---|
| `pinned_base − intree_base` (control, reproduces 10/265) | 265 | **10/265** | 211/265 | 50/265 | −7.6 | 44.2 |
| `pinned_pA − intree_pA` (does the fix restore a pinned score?) | 265 | **9/265** | 195/265 | 67/265 | −5.5 | 46.9 |
| `pinned_pA − intree_base` (fix vs the engine's real value) | 265 | **9/265** | 195/265 | 67/265 | −5.5 | 46.9 |

Exact McNemar on the discordant pairs: **8 fixed by the patch, 9 broken by it,
p = 1.0000.** Decisive null. **The patch is a control-restorer only; a single
pinned score remains a different number, sd 47 cp.**

### F12a — a post-hoc subgroup worth a pre-registered run, not a finding

The top move alone moves from 1/53 to 6/53 identical (5 fixed, 0 broken,
exact McNemar **p = 0.0625**). It does not clear 0.05, and the subgroup was chosen
*after* seeing the full-set result, so it is exploratory. Reported because a
future run should pre-register exactly this subgroup on a fresh position set, not
because it is a result.

**The generalisable rule this closes with:** *a fix that makes a CONTROL valid does
not necessarily make a MEASUREMENT valid.* Restoring the TT store repairs the
no-op baseline and leaves the one-move root a different search, because a
one-move root is a different search for reasons the TT store does not touch.

---

## Suspicions, not proven

- **Why the TT store matters so much at the root.** With no root entry, the next
  iteration's root `MovePicker` has `tt_move = none`, so the whole root move list
  is ordered by history/killers/captures instead of starting from last
  iteration's best. That is consistent with F1's magnitude, but I did not
  instrument the picker to show it move by move. It is a reading of the code plus
  a perfect intervention result, not a trace.
- **Whether `pB`'s residual 51/60 and 7/60 mean IIR matters independently or just
  perturbs the same ordering.** The `pAB` arm cannot separate them because `pA`
  already reaches 60/60.
- **Whether the F5 flatness holds below depth 12.** Measured only at depth 12 for
  k, and at 8/10/12 for the tie sets.

## What I did NOT do

- No engine source committed. The three patches exist only as scratch copies at
  `/tmp/patchA`, `/tmp/patchB`, `/tmp/patchAB`; they are described line-by-line in
  F1 so anyone can recreate them, but no `.patch.txt` was produced because the
  assignment did not ask for a repair.
- No MultiPV > 5, no time-managed or node-limited searches, no Threads > 1.
- No test of whether a *fixed* engine changes strength; that is an engine-strength
  question, not a protocol-semantics one.

## What I am NOT sure about

- The 53/60 R1 validity rate means my 3- and 5-candidate agreement denominators
  are 159 and 530 rather than 180 and 600. F6b exists precisely because of that
  doubt, and it agrees: the effect is real, not a reference artefact.
- The exact usable threshold in F7 (50 vs 100 cp) is read off a single depth and
  one position set; it is an operating point, not a law.
