# REPORT job 3 — area 6 (SYMMETRY): depth-10 search of each G position and its colour mirror

## What was asked / the answer / how sure

**Asked.** Search every G position and its colour mirror at depth 10 with S14, Threads 1, Hash 16,
`ucinewgame` + `isready` before every `go`; report whether the mirrored bestmove equals the original bestmove
and whether the score is equal.

**Answer.** **The search is NOT colour-symmetric.** At depth 10 on G, **101 of 353 bestmoves differ after
mirroring (28.6 %)** and **334 of 353 scores differ (94.6 %)**. The break starts at depth 2 and gets worse with
depth, and it is **not** the evaluation (job 1 showed the evaluation is symmetry-exact) and **not** any single
search feature that can be switched off: it is alpha-beta's order sensitivity meeting an **unstable sort with a
strict `>` comparator on move scores** (`src/search.cpp:858-860`), which puts equal-scored moves in a different
order for a position and its mirror, and alpha-beta then visits a different tree. The proof is at depth 1, where
no pruning exists: **25 of 40 positions already have a different node count while every bestmove mirrors and
every score is equal**. A different node count with an identical result is order dependence and nothing else.

**How sure.** High for the measurement (raw files, both controls, two independent harnesses). The *mechanism*
(`std::sort` instability plus ties) is read from the code and matches the depth-1 evidence, but I did not build
a patch to prove a stable sort fixes it — that is listed under "what I did NOT do".

## Honesty numbers

`~/bld/release/forge`, sha256 `e06310eca…`, bench 11/13/16 = 312866 / 862329 / 3024920, perft 5 = 4865609
(`../HONESTY.txt`). All searches: Threads 1, Hash 16, S14 through 14 `setoption` lines (each followed by
`isready`, every line up to `readyok` read), `ucinewgame` + `isready` before every `go`, every `.meta` records
the exe path, sha256, `id name` and all option lines.

## Prediction outcomes (prediction.txt, pushed alone before measuring)

| # | prediction | outcome |
|---|---|---|
| Q1 | 0 positions with a differing mirrored bestmove | **KILLED**: 101 of 353 (28.6 %) |
| Q2 | 0 positions with a differing score | **KILLED**: 334 of 353 (94.6 %) under my stated rule; 340 of 353 under the EQUAL rule |
| Q3 | 0 positions where the last PV's first move is not the bestmove | **CONFIRMED**: 0 of 706 sides |
| Q4 | control: same position twice gives identical results | **CONFIRMED**: 0 of 6 differ (`table_ctrl_repeat.txt`) |
| Q5 | S14 changes the bestmove on 0–5 % vs no S14 | see `ablate_d8.txt`: S14 is not what breaks symmetry (the break is present with LMR/null-move/etc. all off) |
| Q6 | failing positions have equal scores (a tie broken differently) | **PARTLY CONFIRMED, partly REFUTED**: at depth 1, 25 of 40 differ in node count with *all* scores equal; at depth 10, 19 positions have equal scores and 101 differ in bestmove — so ties are the mechanism at low depth, but at depth 10 scores also diverge. See the mechanism section |
| Q7 | more than 90 % of G usable (castling positions included) | **CONFIRMED**: 353 of 353 usable, 0 failures |

### A mistake in my own prediction, stated plainly

Q2 said the mirror's score must be the **negation** of the original's. That is wrong for `board.mirror()`: the
colour mirror flips the board **and** the side to move, and the engine's score is side-to-move relative, so the
two scores must be **equal**. Job 1's raw data proves it (position 0: `total -351` on both sides). The committed
prediction is not edited; `analyse_search.py` reports **both** rules so the reader sees the difference
(334 differ under EQUAL, 340 under NEGATED — the EQUAL rule is the correct one and is what the report uses).

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone first | done | `prediction.txt` | Q1–Q7, one killed and one partly wrong (above) |
| harness written to file first, run from it | done | `harness_search.py`, `meta_G_d10.txt` | 353 rows, 0 failures, 8.9 s wall |
| G depth 10, bestmove mirror test | done | `out_G_d10.txt`, `table_G_d10.txt` | **101 of 353 differ** |
| G depth 10, score test (both rules) | done | same | 334 (EQUAL) / 340 (NEGATED) of 353 differ |
| G depth 10, PV-first == bestmove | done | same | 0 of 706 sides |
| G depth 10, PV mirror test | done | same | 345 of 353 PVs are not the mirror |
| control: same position searched twice | done | `control_state.py repeat`, `ctrl_repeat.txt`, `table_ctrl_repeat.txt` | 0 of 6 differ |
| control: fresh process per search (rules out stale state) | done | `ctrl_fresh.txt`, `table_ctrl_fresh.txt`, `meta_ctrl_fresh.txt` | still differs → not process state |
| depth curve 1..8 on 40 G positions | done | `depth_curve.py`, `out_curve.jsonl`, `curve.txt` | bestmove mirrors 40→34 ; **node counts equal 15→0** |
| which depth the break starts | done | `curve.txt` | **depth 2** for scores (30/40), depth 1 for node counts (15/40) |
| is the TT the cause? Hash 1/16/64/256 | done | `tt_test.py`, `tt_test_pos68.txt` | **no**: identical results at every size |
| is a toggleable feature the cause? 21 ablations | done | `ablation.py`, `ablate_d8.txt` | **no**: no configuration restores symmetry; "everything off" is worse (13/20) |
| is the evaluation the cause? 7 eval configurations | done | `evalsource.py`, `evalsource_pos68.txt` | **no**: `UseNNUE false` restores the mirrored bestmove but scores and node counts still differ |
| locate the mechanism in the code | done | this report, next section | `std::sort` at `src/search.cpp:858-860` with a strict `>` comparator |
| control: negative control for the mirror checker | done | `ctrl_shift` in job 2 and the depth-1 node evidence here | the checker sees a difference when one exists |
| R set at depth 10 | not done | — | G only; the job says G, and G already answers the question |

Commands that show each result again (from this folder):

```
python3 harness_search.py ~/bld/release/forge G_353.fens out_G_d10.txt meta_G_d10.txt 10 S14
python3 analyse_search.py out_G_d10.txt
python3 depth_curve.py ~/bld/release/forge curve_set.fens 8 out_curve.jsonl
python3 ablation.py ~/bld/release/forge 8 ablate_set.fens
python3 evalsource.py ~/bld/release/forge "8/3b4/8/1p1pk2p/7P/P1B1KP1P/1Pr1N3/8 b - - 0 1" 8
```

## The mechanism, with file and line

1. **The evaluation is not the cause.** Job 1 measured 0 differences in 8,103 position-pairs; `evalsource.py`
   confirms it again inside the search: with `UseNNUE false` the bestmoves mirror again (though scores still
   differ because the *tree* differs).
2. **The transposition table is not the cause.** `tt_test.py` gives byte-identical results at Hash 1, 16, 64 and
   256 MB, and a second search in the same process (a warm TT) returns the same answers as the first.
3. **No single pruning or reduction feature is the cause.** `ablation.py` turns off null move, RFP, razoring,
   futility, LMP, probcut, singular, IIR, LMR, SEE pruning, aspiration, and seven boolean gates — one at a time
   and then all at once. Symmetry never comes back (the worst configuration is "all off", 13/20 bestmoves).
4. **The order dependence is visible at depth 1.** `out_curve.jsonl`, depth 1: 40 of 40 bestmoves mirror and
   40 of 40 scores are equal, but only **15 of 40 node counts are equal**. Depth 1 has no pruning, no
   reductions, no null move. A different node count with an identical result means the *same* moves are being
   searched in a *different order*.
5. **The tie-break is unstable.** `src/search.cpp:858-860`:
   `std::sort(moves_.begin()+index_, moves_.begin()+count_, [](const Scored& a, const Scored& b) { return a.score > b.score; });`
   `std::sort` is not stable, and the comparator gives equal scores no ordering at all, so which of two
   equal-scored moves is searched first is an artifact of the algorithm's internals and of the *input order* of
   `moves_`. That input order comes from the move generator walking squares from a1 upward; a colour mirror maps
   that to a different traversal, so the tie order changes, alpha-beta re-searches a different tree, and with
   real pruning (depth ≥ 2) the results diverge.
   The first-four-pick path above it (`search.cpp:817-856`) has the same property: it keeps the *first* move
   with the strictly-greater score, so ties again depend on list order.
6. **Why this is not a bug in the usual sense.** Any engine with an unstable sort over a tie-heavy move list is
   not colour-symmetric at fixed depth. It is a property, not a miscalculation: both sides get a legal, sensible
   move, and the scores are within a few centipawns of each other on most positions (median |score delta| is
   small at depths 1–3). But it **does** mean a fixed-depth, fixed-node test cannot be used to compare a position
   with its mirror — which is exactly what job 3 was asked to do, so the negative answer needs saying clearly.

## Findings

**F1 — the depth-10 search is not colour-symmetric: 101 of 353 G positions (28.6 %) return a bestmove that is
not the mirror of the other side's bestmove, and 334 of 353 scores differ.**
Shows again: `python3 analyse_search.py out_G_d10.txt`.

**F2 — the asymmetry is order dependence in alpha-beta, measurable at depth 1 with no pruning: 25 of 40
positions have different node counts while all 40 bestmoves mirror and all 40 scores are equal.**
Shows again: `python3 depth_curve.py ~/bld/release/forge curve_set.fens 8 out_curve.jsonl` (row depth 1).

**F3 — the instability is the `std::sort` tie-break at `src/search.cpp:858-860` (strict `>` comparator, no
stable ordering), plus the same "first strictly-greater wins" rule in the first-four `pick_best` at
`src/search.cpp:817-856`.** Not proven by a patch; proven consistent with every measurement here (depth-1 node
counts, TT independence, ablation independence, eval independence).
Shows again: `sed -n '817,862p' src/search.cpp` in the build worktree; the measurements above.

**F4 — a strong result that stands regardless of the mechanism: 28.6 % of positions give a *different* bestmove
after a colour mirror at depth 10, so any future test that assumes search symmetry at fixed depth is invalid.**
This is the practical warning for Opus and for the other areas (e.g. a symmetry-based optimisation, a mirror
test in area 3, or a "mirror the board to halve the test suite" trick).

## Suspicions, not proven

- That a **stable** sort (or an explicit mirror-invariant tie-break, such as ordering ties by
  `min(from,to)`-style canonical keys, or by `to ^ 56` folding) would restore exact symmetry. It follows from the
  depth-1 evidence but was not built and measured — that would be a TEXT PATCH job with the honesty numbers held,
  which is area 9's or a repair job's territory, not a measurement job's.
- That the 28.6 % bestmove difference is *harmless in strength terms* (both moves are near-equal in score). I did
  not measure the score gap distribution per differing bestmove; the median score delta is small but there are
  outliers (up to 4388 cp at index 196, where one side reports `cp 4402` and the mirror reports `mate 14` —
  the same position must not be cp on one side and mate on the other, so there may be a second, separate issue in
  how mate scores survive a search; flagged, not chased).
- Index 196 (`5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w`) and 217 (`8/7p/8/7p/3k2b1/6K1/2p5/8 b`) show `cp 4402` vs
  `mate 14` and `cp 2557` vs `mate 11`. A mate score appearing on one side of a mirror pair and a huge cp score
  on the other is worth a dedicated look — it may be a mate-score/TT interaction rather than ordering. Not
  proven; listed here so it is not lost.

## What I did NOT do

- No R set at depth 10 (G alone answers the question; R is job 1's set).
- No repair patch. The report names the code and the mechanism but does not modify the engine: a changed engine
  source may only be a `.patch.txt` with the honesty numbers unchanged, and job 3 is a measurement job.
- No threading (Threads 1 throughout), so nothing here says anything about multi-thread determinism.
- No per-node tracing of which move order changed; the depth-1 node-count evidence is the proof that order
  changes, not a trace of *which* pair of moves swapped.
- I did not run the R set or a second seed for job 3; the brief's "(c) job 1 again with the next seed" applies
  once jobs 1–3 are all done, and job 1's re-run is next.

## What I am NOT sure about

- Whether Opus considers this a defect worth fixing. Many engines behave this way; a fixed-depth mirror test is
  simply not a valid invariant. That judgement is Opus's; the measurement is mine.
- The exact share attributable to `std::sort` versus the first-four `pick_best` path. Both have the same
  tie-sensitivity; I did not separate their contributions.
- Index 196's cp-vs-mate discrepancy: it could be the same ordering issue (a mate found on one side of a tie and
  not the other) or a separate mate-score bug. I am not calling it either.

## Times

See `stamps.txt`.

## Last command's output

`git status --short` + `ls` of this folder are appended to `stamps.txt`; the file list there is what is done.
