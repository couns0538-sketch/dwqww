# REPORT job 2 — area 6 (SYMMETRY): static evaluation against the LEFT-RIGHT mirror

## What was asked / the answer / how sure

**Asked.** The same as job 1 for the left-right mirror (`python-chess` `board.transform(chess.flip_horizontal)`,
files mirrored, colours and side to move untouched), on positions without castling; every difference with its
FEN; then read the evaluation code and name the term responsible.

**Answer.** The hand-written evaluation is **not** left-right symmetric, and that is **by design, not a fault**:
its parameters were Texel-tuned and the tuned PSQT table is asymmetric on 48/64 Pawn entries and 64/64 for every
other piece. The proof is a controlled experiment: with **only the PSQT table symmetrised** (a diagnostic build,
`/tmp/bld/diag/forge`) the hand-written component goes from 98.2 % of positions differing to **0 of 334 on G and
0 of 430 on R**. So every left-right asymmetry in `hce` is the tuned PSQT table and nothing else — no term
mirrors the board and forgets to mirror a file index. The NNUE net is separately and independently asymmetric
(97.9 % / 99.3 % of positions, unchanged by the PSQT patch), which is expected of a trained network.

**How sure.** High. The experiment has a clean before/after with one variable changed, two position sets, both
controls working (self 0/334; a deliberately mispaired run 333/333).

A correction to my own job 1 report came out of this job and is described at the end.

## Honesty numbers

Main build: `~/bld/release/forge`, sha256 `e06310eca…` — bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, perft 5 = 4865609 (all four; `../HONESTY.txt`).

**Diagnostic build** `/tmp/bld/diag/forge`: same source with `src/eval_params_table.inc` replaced by a
left-right-symmetrised copy (`symmetrise_psqt.py`). Its honesty numbers are **bench 11 = 350732,
bench 13 = 814110, bench 16 = 3742570, perft 5 = 4865609**. It is **NOT a candidate build and not used for any
result that needs the pinned numbers** — it exists only to answer "is the asymmetry structural or parametric".
It is a controlled perturbation: changing the evaluation must change the tree, and it does; perft, which does not
touch the evaluation, is unchanged at 4,865,609, which is the check that the patch did not break the move
generator. `src/eval_params_table.inc` in the repository is untouched — the experiment wrote to `/tmp` only, and
no engine source file is committed (rule).

## Prediction outcomes (prediction.txt, pushed alone before measuring)

| # | prediction | outcome |
|---|---|---|
| P1 | more than 90 % of positions differ in `total` | **CONFIRMED**: 99.4 % (G) and 99.8 % (R) |
| P2 | count of `nnue` differences EQUALS count of `total` differences | **KILLED**: 327 vs 332 (G), 427 vs 429 (R). Reason found, see below |
| P3 | median \|hce delta\| ≤ 120 and max ≤ 600 | **CONFIRMED**: median 20 (G) / 18 (R), max 143 / 182 |
| P4 | control (position against itself) gives 0 differences | **CONFIRMED**: 0 of 334 |
| P5 | both positive and negative deltas occur | **CONFIRMED**: 158/170 (G), 222/203 (R) for hce |
| P6 | hce and nnue deltas are not locked together | **CONFIRMED** (see P2 discussion: they cancel on 3 positions) |
| P7 | fewer than 15 % of G excluded for castling | **CONFIRMED**: 19 of 353 = 5.4 % (R: 70 of 500 = 14.0 %) |

**Why P2 was killed, and why it is my error, not the engine's.** P2 assumed `total = nnue` (I believed the net
was non-residual). It is not: `src/nnue_weights.inc:3` is `#define FORGE_NNUE_RESIDUAL 1`, so
`total = clamp(hce + nnue)`. Then a position can differ in `nnue` while `total` is unchanged **because the hce
delta cancels the nnue delta exactly**. That happened 3 times in 764 positions (an interesting and rare
coincidence — the PSQT and the network disagreeing by exactly opposite amounts). P2 also fails in the other
direction when `nnue` is equal but `hce` differs, which is the ordinary case (11 of the 14 disagreements). The
`nnue == total` equality does hold exactly on the symmetrised diagnostic build (0 == 0, 327 == 327, 427 == 427),
which is the harness self-consistency check P2 was meant to be.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone first | done | `prediction.txt` | commit "swarm 06 job2 prediction (alone)" |
| PSQT table checked for left-right symmetry before predicting | done | this report, table below | 48/64 Pawn, 64/64 others asymmetric → difference EXPECTED |
| G, 353 positions, castling positions excluded and counted | done | `harness_lr.py`, `out_G.txt`, `meta_G.txt`, `table_G.txt` | 334 compared, 19 skipped, 0 failures |
| R, 500 positions | done | `out_R.txt`, `meta_R.txt`, `table_R.txt` | 430 compared, 70 skipped |
| hce differing on G / R | done | `table_G.txt`, `table_R.txt` | 328 (98.2 %) / 425 (98.8 %) |
| nnue differing on G / R | done | same | 327 (97.9 %) / 427 (99.3 %) |
| total differing on G / R | done | same | 332 (99.4 %) / 429 (99.8 %) |
| delta magnitudes (|hce|) | done | same | median 20/18, p99 103/161, max 143/182 |
| control self-vs-self | done | `control_lr.py`, `ctrl_self.txt`, `table_ctrl_self.txt` | 0 of 334 differ |
| negative control (checker must see a difference) | done | `ctrl_shift.txt`, `table_ctrl_shift.txt` | 333 of 333 flagged |
| **diagnostic: PSQT symmetrised, G** | done | `symmetrise_psqt.py`, `out_diag_G.txt`, `meta_diag_G.txt`, `table_diag_G.txt` | **hce: 0 of 334 differ** |
| **diagnostic: PSQT symmetrised, R** | done | `out_diag_R.txt`, `meta_diag_R.txt`, `table_diag_R.txt` | **hce: 0 of 430 differ** |
| read the evaluation code for left-right handling | done | this report, section below | every mask and index is flip-symmetric; the only asymmetry is the tuned table |
| name the term with file and line | done | this report | PSQT, `src/eval.cpp:429-438`, table at `src/eval_params_table.inc` |

Total left-right comparisons: 334 + 430 + 334 (control) + 333 (negative control) = 1,431 pairs on the main
build, plus 764 pairs on the diagnostic build.

Commands that show each result again (from this folder):

```
python3 harness_lr.py  ~/bld/release/forge G_353.fens out_G.txt meta_G.txt && python3 analyse_lr.py out_G.txt
python3 harness_lr.py  ~/bld/release/forge R_500.fens out_R.txt meta_R.txt && python3 analyse_lr.py out_R.txt
python3 control_lr.py  shift ~/bld/release/forge G_353.fens ctrl_shift.txt meta_ctrl_shift.txt && python3 analyse_lr.py ctrl_shift.txt
python3 symmetrise_psqt.py /agent/repos/base/forge-combo29/src/eval_params_table.inc /tmp/symcheck.inc
# then build /tmp/diag with that include in place of src/eval_params_table.inc, and:
python3 harness_lr.py /tmp/bld/diag/forge G_353.fens out_diag_G.txt meta_diag_G.txt && python3 analyse_lr.py out_diag_G.txt
```

## Findings

**F1 — every left-right asymmetry in the hand-written evaluation comes from the Texel-tuned PSQT table and from
no other term; the evaluation code itself is left-right clean.** Evidence: 98.2 % of G positions differ with the
shipped table, **0 of 334** differ once only the PSQT table is symmetrised, and perft 5 is unchanged at
4,865,609 so the perturbation did not disturb the move generator.
Shows again: `python3 analyse_lr.py out_diag_G.txt` (needs the diagnostic build; the script and the symmetriser
are committed, the altered include is not — `symmetrise_psqt.py` regenerates it from the repository source).
This is a **negative** structural result and it is the useful answer for Opus: do not look for a mirroring bug in
`evaluate_pieces`/`evaluate_king`/`evaluate_threats`; the file-index mirroring there is consistent.

**F2 — the left-right asymmetry is large enough to be worth knowing about for correctness claims: 98–99 % of
real positions change their static score by a median of 20 cp (hce) / 60 cp (total) when the board is flipped
left-right, and up to 838 cp.**
Shows again: `python3 analyse_lr.py out_G.txt out_R.txt`.
Not a fault (chess is not left-right symmetric and the parameters are tuned), but it means **any test that
assumes left-right symmetry of the evaluation will fail** — e.g. a future "eval is up to symmetry" invariant test,
or a mirror-based comparison in a later optimisation. Recorded so nobody re-discovers it as a bug.

**F3 — 3 of 764 positions had the PSQT delta exactly cancel the net delta, leaving `total` bit-identical
under a left-right flip while both components moved.** Rare, but it is the reason a `total`-only comparison
("total is symmetric?") is a weak test — it can hide a component difference. Recorded as a methodology finding.
Shows again: the 14-line listing in this report's P2 section is regenerated by
`python3 analyse_lr.py out_G.txt` (counts) plus the `DISAGREE` listing produced by the inline script in
`stamps.txt`'s run.

## Suspicions, not proven

- The NNUE net's asymmetry is presumably ordinary trained asymmetry (the network was trained on data where file
  identity matters). I did not test the alternative — that some feature-index path drops the file bit — because
  the diagnostic shows the asymmetry is stable under a change that cannot affect the net. A targeted test would
  be: build with an all-zero `w1`/`w2` (net contributes 0) and confirm `total` becomes exactly `hce` for every
  position. Not done; would need a generated weights file.
- `analyse_lr.py` treats `delta == 0` as "equal". A position where both sides are 0 is counted as equal, which is
  correct for this question.

## Correction to job 1's report

My job 1 report said the built-in net is non-residual, so `total = nnue`. **That was wrong.**
`src/nnue_weights.inc:3` is `#define FORGE_NNUE_RESIDUAL 1`, and the raw file shows it plainly: `job1/out_G.txt`
position 6 is `hce 169 nnue -7 total 162`. `total = hce + nnue`, clamped. Job 1's measurements and conclusion
are unaffected (hce and nnue were compared separately and each was symmetric, so the sum is symmetric too), but
the prose was wrong. The correction is now written into `job1/REPORT_job1.md` with the evidence and the commit
that made it.

## What I did NOT do

- No search (job 3 covers depth-10 search symmetry).
- No castling positions at all: 89 of 853 were excluded by design. A rook on a1/a8 mirrored to h1/h8 cannot keep
  its castling right, so the flip is not a legal position. There is no meaningful test there without a different
  notion of "mirror".
- No position with a promotion-ready pawn on the a/h files specifically. `special.fens` in job 1 covers
  promotion-ready positions but its left-right use was not run.
- No sanitizer build: `eval` is a pure function with no allocation beyond the evaluator's own cache, and this
  job is not a memory-safety job.
- I did not modify the repository's `eval_params_table.inc` — the perturbation lives in `/tmp` only, per the
  rule against committing changed engine source.

## What I am NOT sure about

- Whether Opus *wants* the evaluation to be left-right symmetric. It is not, and cannot be while the parameter
  table is tuned freely. If a future invariant test asserts left-right symmetry, it will fail on 98 % of
  positions, and this report is the explanation.
- Whether the exact set of 19 excluded G positions matters. They are all opening/early-middlegame castling
  positions, so the excluded set is not random; the R set's exclusion rate (14 %) is close to P7's limit and a
  different R seed could exceed 15 %.

## Times

See `stamps.txt`.

## Last command's output

`git status --short` + `ls` of this folder are appended to `stamps.txt`; the file list there is what is done.
