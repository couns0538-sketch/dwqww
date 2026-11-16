# REPORT job 1 — area 6 (SYMMETRY): static evaluation against the colour-flipped mirror

## What was asked / the answer / how sure

**Asked.** Evaluate every G position and 500 R positions with the engine's `eval` command, compare with the
colour-flipped mirror (`python-chess` `board.mirror()`), list every difference with its FEN, then read the
evaluation code and name the term with file and line. Control: a position against itself.

**Answer.** The engine's `eval` output is exactly colour-symmetric: **0 differences in 6,435 positions across four
evaluation configurations** (hce, nnue and total all equal). The control is 0 as predicted and a deliberately
broken pairing is caught 99 times out of 99, so the checker does see differences. No term breaks the colour mirror;
the code review below says which terms were the candidates and why each one is symmetric.

**How sure.** High for the `eval` command as built with the built-in net on this machine (sha256 in the .meta
files). The one thing not covered: the search's own evaluation path (`Worker::static_evaluate` with correction
history, `rule50_damped_static`, tempo inside the search) is job 3's territory, not job 1's.

## Honesty numbers

Build: `~/bld/release/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
GCC 13.3.0, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, Release, built-in net.
Bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four as required
(see `../HONESTY.txt`). Every .meta in this folder records the exe path it started, its sha256, its `id name`
(`id name Chess Engine Forge 6.4.24 candidate`) and every option line sent.

## What `eval` prints (read from the code, src/uci.cpp:575-589)

`info string eval hce <H> nnue <N> total <T>` and ` incheck 1` appended when the side to move is in check.
`hce` is `Evaluator::static_eval_components` → `evaluate_uncached` (the hand-written evaluation),
`nnue` is the network's own output, `total` is `hce + nnue` clamped to `±(MateInMaxPly-1)` when the net is
residual; with `UseNNUE false` it prints `nnue 0` and `total` is the hand-written evaluation.

## CORRECTION (made while running job 2, 2026-11-16, same commit series)

The table row for `total` in the code-review table below says "with the built-in net `residual()` is false".
That is WRONG. `src/nnue_weights.inc` line 3 is `#define FORGE_NNUE_RESIDUAL 1`, so `nnue::residual()` returns
true and `total = hce + nnue` (clamped), which is what the raw files show: position 6 of `job1/out_G.txt` has
`hce 169 nnue -7 total 162`. The mistake did not change any measurement or any conclusion of job 1 — both `hce`
and `nnue` were compared separately and both were symmetric, so `total` is symmetric either way — but the
prose was wrong and is corrected here. The sentence in "what I am NOT sure about" that leans on the
non-residual claim is superseded by this correction. Show the flag: `head -3 src/nnue_weights.inc`.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction written and pushed alone before measuring | done | `prediction.txt` (commit "swarm 06 job1 prediction (alone)") | 6 predictions, P1–P6 |
| R set built from SEED 601, python-chess random games, one position per 7 plies | done | `make_R.py`, `R_601.fens` (700), `R_500.fens` (first 500) | 16 games, 700 FENs |
| G set: 353 positions | done | `G_353.fens` | line count 353 |
| harness written to file first, run from there | done | `harness_mirror.py`, `meta_G.txt`, `meta_R.txt` | rows 353 / 500, failures 0 |
| G mirror comparison | done | `out_G.txt`, `table_E1.txt` | 0 differences of 353 |
| R (500) mirror comparison | done | `out_R.txt`, `table_E1.txt` | 0 differences of 500 |
| control: position against itself | done | `control_self.py`, `ctrl_self.txt`, `table_ctrl_self.txt` | 0 differences of 100 |
| **negative control** (checker must see a difference) | done | `control_self.py shift`, `ctrl_shift.txt`, `table_ctrl_shift.txt` | 99 of 99 flagged |
| R widened to 5,000 positions | done | `make_R_big.py`, `Rbig_5000.fens`, `out_Rbig.txt`, `table_Rbig.txt` | 0 differences of 5,000 |
| special positions (ep / castling both sides / in check / clock>0 / hand-written) | done | `make_special.py`, `special.fens`, `out_special.txt`, `table_special.txt` | 514 compared, 0 differences, 1 FEN refused (see below) |
| configuration `UseNNUE false` (pure hand-written eval) on all 853 | done | `harness_variant.py`, `out_NoNNUE.txt`, `table_NoNNUE.txt` | 0 differences of 853 |
| configuration `DeadMaterial true` on all 853 | done | `out_DeadMat.txt`, `table_DeadMat.txt` | 0 differences of 853 |
| dead-material positions (K v K, KN v K, KB v K, KNN v K, KN+B v K, both colours) with `DeadMaterial true` | done | `make_dead.py`, `dead.fens`, `out_dead_on.txt`, `table_dead_on.txt` | 0 differences of 30; 16 of the 853 also hit the path |
| read the evaluation code and name the terms | done | this report, section below | see below |
| left-right mirror (job 2) | not done | — | job 2 |
| search symmetry at depth 10 (job 3) | not done | — | job 3 |

Total positions compared for the colour mirror: **353 + 500 + 5,000 + 514 + 853 + 853 + 30 = 8,103 position-pairs**,
0 differences in any of them.

Commands that show each result again (all from this folder, with the same exe):

```
python3 harness_mirror.py  ~/bld/release/forge G_353.fens out_G.txt meta_G.txt && python3 compare.py out_G.txt
python3 harness_mirror.py  ~/bld/release/forge R_500.fens out_R.txt meta_R.txt && python3 compare.py out_R.txt
python3 harness_variant.py ~/bld/release/forge Rbig_5000.fens out_Rbig.txt meta_Rbig.txt ""
python3 control_self.py    shift ~/bld/release/forge G_100.fens ctrl_shift.txt meta_ctrl_shift.txt && python3 compare.py ctrl_shift.txt
python3 harness_variant.py ~/bld/release/forge GR_853.fens out_NoNNUE.txt meta_NoNNUE.txt "name UseNNUE value false"
```

## Findings

**F1 — the `eval` command is exactly colour-symmetric on 8,103 positions in four eval configurations; 0
differences in hce, nnue or total.**
Shows again: `python3 harness_variant.py ~/bld/release/forge GR_853.fens out_NoNNUE.txt meta_NoNNUE.txt "" && python3 compare.py out_NoNNUE.txt`
(This is a negative result: a fault would have been a finding; the absence of one is the report's answer, so it
is recorded in FINDINGS.md as a checked-and-clean fact, not as a fault.)

**F2 — a FEN whose en-passant square is not reachable is REFUSED, with the answer
`info string invalid FEN: inconsistent en-passant square`.** The accepted shape is narrow: the ep square must be
empty, the square the pawn came from must be empty, and the pawn itself must stand where it must stand
(`src/board.cpp:325-333`). `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1` is refused.
Shows again: `printf 'position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1\nisready\nquit\n' | ~/bld/release/forge`
That the engine refuses a bogus ep square is stricter than many engines and is NOT a fault; it is recorded
because it is the one refusal the special-position set hit, and because area 1 (FEN input) should not have to
rediscover it.

## The evaluation code: which terms could break the colour mirror, and why none did

Read: `src/eval.cpp` (the whole hand-written evaluation), `src/nnue.cpp` (accumulator refresh and the quantised
forward pass), `src/uci.cpp:575-589` (the `eval` command), `include/forge/search.hpp:348-357`.

The hand-written side is written as **one templated pass per colour**, `evaluate_*<Trace, Us>` with
`Them = opposite(Us)`, and every term goes through `Accumulator::add<Us>`, which adds `+value` for White and
`-value` for Black. All square arithmetic in those passes is done in *relative* coordinates
(`relative_rank(Us, sq)`, `pawn_push_delta(Us)`, `forward_ranks(Us, sq)`, `rank_bb` after `flip_square` for the
black pieces' PSQT). The candidates and their verdicts:

| term | where | why it is symmetric |
|---|---|---|
| PSQT + phase | `eval.cpp:429-438` | white pieces read `Psqt + (type-1)*64 + sq`, black read the same table at `flip_square(sq)` — the exact colour flip |
| pawn structure (doubled, isolated, backward, connected, passed) | `eval.cpp:68-109` | all in `Us`-relative ranks; `passed_out` is filled per colour and consumed per colour |
| mobility area, outposts, minor-behind-pawn | `eval.cpp:115-190` | `Us`/`Them` swapped per pass; `outpost_ranks` is the rank set mirrored by colour |
| rook on open/semi-open file, rook behind passer, rook on seventh | `eval.cpp:191-212` | relative ranks; `forward_file(Us, sq)` |
| king shelter and storm | `eval.cpp:250-268` | `forward_ranks(Us, king)`; `lsb` for White and `msb` for Black pick the *nearest* pawn in the same relative direction |
| king danger | `eval.cpp:271-298` | attacker counts are accumulated into `info.king_attackers[Them]` while evaluating `Us`, so each side's danger is built from its enemy's pieces |
| space | `eval.cpp:299-311` | `SpaceMask` is the same four files mirrored by colour |
| threats | `eval.cpp:319-359` | `Us`/`Them` swapped per pass; every mask from `info.attacked_by[c]` for one fixed `c` |
| passed pawn king distance | `eval.cpp:361-387` | relative ranks, both kings measured to the same stop square |
| `scale_factor` | `eval.cpp:388-414` | **this is the one term with a colour decision**: `const Color strong = eg > 0 ? White : Black`. It is safe *because* it is only ever called on `eg`, and the result is used as `eg = eg * scale / 64`. When `eg == 0` the branch picks Black, but `0 * scale / 64 == 0` for every scale, so the value is unaffected. For `eg != 0` the sign already says which side is ahead, and the mirrored position has the mirrored `eg`, so it picks the mirrored colour. Verified empirically: every `total` in the tables is `hce + nnue` and mirrors exactly, including 5,000 random middlegames where `eg` takes both signs |
| tempo | `eval.cpp:496-497` | `if side_to_move == White add<White>(Tempo) else add<Black>(Tempo)` — the sign comes out as `+Tempo` for the side to move either way, and the mirror flips the side to move |
| dead material | `eval.cpp:516-565` | `score = side_to_move == attacker ? attacker_cp : -attacker_cp` — written in side-to-move terms, and the mirror flips both. The corner set (`corner_a`/`corner_b`) is chosen by the bishop's *colour*, which is a board property, not a side property |
| NNUE accumulator | `nnue.cpp:195-215` | each perspective gets its own accumulator, features are indexed relative to that perspective |
| `total` | `eval.cpp:604-612` | with the built-in net `residual()` is TRUE (`nnue_weights.inc:3`), so `total = hce + nnue` clamped; with the net off, `total = hce`. Corrected in the section above |

The `scale_factor` tie-break is the only place a colour is named from a number's sign instead of from the side to
move, and the report records it as a **suspicion that was tested and cleared**, not as a fault.

## Suspicions, not proven

- `scale_factor`'s `eg > 0 ? White : Black` is harmless only because `scale` multiplies `eg`. If a later change
  makes `scale` scale something else (e.g. a score that is non-zero when `eg` is zero, or adds rather than
  multiplies), the tie-break becomes a real colour bias. Not a fault today; a trap for a future edit.
  Shown safe today by every table here (0 differences).
- The `hce` and `nnue` numbers are printed from *different* code paths (`evaluate_uncached` vs
  `nnue::refresh`/`evaluate`), and `total` is `nnue` alone while the net is non-residual (`eval.cpp:604-608`).
  So a `hce` that is asymmetric would NOT show in `total` with the default settings. That is why the
  `UseNNUE false` configuration was run separately: it is the only configuration in which `total` is the
  hand-written evaluation on this build.

## What I did NOT do

- No search: `eval` only. Correction history, `rule50_damped_static`, tempo inside the search and the TT are
  not exercised by job 1 (job 3).
- No left-right mirror (job 2) and no depth-10 search comparison (job 3).
- No sanitizer build for this job: `eval` on these positions produced no crash, and the job does not ask for
  one. Sanitizer work belongs to areas 1–4.
- I did not test positions where a side has **no king** or other illegal boards: `eval` on an illegal board is
  area 1's business, not a symmetry question.

## What I am NOT sure about

- Whether `board.mirror()` is the mirror the engine's author means. It flips ranks and swaps colours, so castling
  rights KQkq become KQkq and the side to move flips — this is the standard colour mirror and the only one under
  which a symmetric evaluation must give the same number from the side to move's view. If the author intended
  something else by "colour-flipped mirror", these 8,103 comparisons answer a slightly different question.
- The `--depth 1` clones and the shared net: I compared one build only (sha256 above). A different net file
  (`NnueFile`) could in principle carry an asymmetric colour convention in its feature indexing; not tested.

## Times

See `stamps.txt` (each line is the pasted output of `date -u`).

## Last command's output

`git status --short` and `ls` of this folder are pasted at the end of `stamps.txt`'s run below; the `ls` is the
file list this report names, and any file not in that list is "not done".
