# forge-combo29 — option-pair interactions

**Build:** `6b98f217`, g++ 13, `-DFORGE_MARCH=x86-64-v4` (the brief's recipe), except the
loader arms which also use a second binary built from the same tree with `-DFORGE_NNUE_V3=1`.
**Pins:** bench 11 = 312,866 · bench 13 = 862,329 · bench 16 = 3,024,920 · `go perft 5` =
4,865,609 — all four matched before anything was recorded (`scripts/pins.sh`).
**Box:** 4 cores, no SMT. Every `Threads 8` row is eight threads on four cores.

**Method, in one line:** every cell is a fresh process, read to `bestmove` before anything else
is sent, on the same fixtures as the rest of its grid; a cell "differs" only if bestmove, score,
depth or nodes differ, and the table says which field moved. Every cell is checked for
`unknown option` / `invalid value` before its number is used.

## The answer

| pair | interacts? | what moves | evidence |
|---|---|---|---|
| **Hash × Threads** | **no** — not detectably, including where the table is 1 MB | nothing beyond Threads noise; pooled mean Δagreement **−0.012, p = 0.55** over 28 positions | `evidence/pair1*-analysis.json`, `pair1-pooled.json` |
| **Hash × drawn-root bail** | **no** | none: **0 of 8** bailing roots at Hash 1/8/64/256, with the Hash axis proved live 7 of 8 on searching roots | `pair3-analysis.json`, `pair3b-analysis.json` |
| **MultiPV × drawn-root bail** | **no** | bailing roots: 0 nodes, empty pv at MPV 1/2/3 — identical; only a *searching* control moves | `pair3-analysis.json` |
| **MultiPV × Threads** | **yes, and it removes Threads entirely** | Threads 4 at MPV 3 is **identical to Threads 1 on 6 of 6** while the MPV 1 control differs on **6 of 6** | `pair2-analysis.json` |
| **Book Depth × OwnBook × Book Variety** | **yes, and it splits three ways** | OwnBook and Book Depth decide *whether*; Book Variety decides *which* — and it is the only RNG | `pair5-*.json`, `pair5b-*.json`, `pair5c-variety.json` |
| **Move Overhead × clock floor** | **yes, and it is a regime switch, not a shift** | below `time ≤ overhead` the plan shrinks smoothly; at it, the engine stops planning and takes the emergency path | `pair4-analysis.json`, `pair4b-analysis.json` |
| **Threads × drawn-root bail** | **no** (already done) | cited, not re-run: 20 of 20 cells identical | §3 |
| **Threads × NNUE** | **no race found** | accumulators are per-`Worker`; TSan clean on 10 cases, **and the arm is proved able to fire** | `tsan.json`, `tsan-planted.json` |
| **UseNNUE × NnueFile × NNUEArch** | **yes — and `NNUEArch` is not in the shipped build at all** | precedence is UseNNUE > NNUEArch > NnueFile; plus a **real defect**: `eval` and the search disagree | `pair7-loader.json`, `pair7b-usennue-eval.json` |

Four things the audit should carry forward, in order of how much they cost to discover:

1. **`NNUEArch` does not exist in the build this audit ships.** The brief's CMake recipe never
   defines `FORGE_NNUE_V3` and `include/forge/nnue.hpp:11` defaults it to 0, so the engine answers
   `info string unknown option NNUEArch`. All the v3 work in this tree is unreachable from the
   locked binary. A cell testing it on the audit build is not a null — it is a different build.
2. **`eval` and the search disagree about whether NNUE is on.** With `UseNNUE false` and a v3 net
   loaded, the search uses the hand-crafted evaluation (**6 of 6** positions match the
   `UseNNUE false`, no-net arm exactly) while `eval` still reports `nnue_v3` (**6 of 6**). A
   tuning harness that reads `eval` to confirm a setting took effect is misled.
3. **Threaded cells are not labels, so "N of M differ" is not a test.** At Threads 4 with 6 repeats,
   the *same cell* differs from itself on **12 of 12** positions. Every Threads-4 comparison in this
   report therefore has an A/A control, and the Hash×Threads verdict is stated on the **delta**
   between A/B and A/A, not on a raw count.
4. **Two of my own instruments failed first and were caught, not published:** a wall-time measured
   around the whole subprocess (≈18–20 ms of startup) made honest clock plans look like 1.3×–4.3×
   overshoot; and a TSan harness that stopped reading at `bestmove` reported a clean run for a
   deliberately racy binary, because TSan prints at exit. Both are in `STATUS.md`.

---

## 1. Hash × Threads — no interaction detected

**The hazard:** with a shared table and helpers, a helper's writes could evict entries the main
worker would have used, so an effect of Hash at Threads 1 need not be the same effect at Threads 4.
**The design problem:** at Threads 4 the same cell already differs from itself, so a between-cell
count is guaranteed and measures nothing. Every arm here carries an **A/A control** — the same cell,
two independent groups of fresh processes — and the statistic is *move agreement* over cross-group
run pairs, so A/A and A/B are the same number and can be subtracted.

| grid | budget | A/A Threads 1 | Hash A/B at Threads 1 | **A/A Threads 4** | **Hash A/B at Threads 4** |
|---|---|---|---|---|---|
| pair1 | `go nodes 400000`, 12 pos, 6 reps | 1.000 / 0 cp | 1.000 / 0 cp (H16 vs H64) | **0.713** / 16 cp | **0.681** / 9.5 cp (H16 vs H64) |
| pair1b | `go nodes 2000000`, 8 pos, 4 reps | 1.000 / 0 cp | 0.875 / 10.5 cp (H16 vs H64) | **0.625** / 8 cp | **0.641** / 12.25 cp (H16 vs H256) |
| pair1c | `go nodes 400000`, 8 pos, 6 reps | 1.000 / 0 cp | 0.750 / 7 cp (H1 vs H256) | **0.653** / 4 cp | **0.642** / 6.25 cp (H1 vs H256) |

The decisive row is pair1c: **Hash 1 MB against Hash 256 MB at Threads 4** is where a shared table
has its best chance — every helper writing the same handful of clusters as the main worker — and the
A/B agreement is *lower than* A/A by 0.011, i.e. nothing.

Pooled over the three grids (28 position-cells, `pair1-pooled.json`):

| statistic | value |
|---|---|
| A/B agreement worse than A/A | 8 positions |
| better | 8 positions |
| equal | 12 positions |
| mean Δ | **−0.0124** (sd 0.1046) |
| sign-flip permutation, two-sided | **p = 0.547** |
| bootstrap 95% CI of mean Δ | **[−0.0501, +0.0260]** |
| score-gap Δ (A/B minus A/A) | −3.16 cp |

**What this does and does not say.** It says Hash does not change the *move* at Threads 4 by more
than rerunning the same cell does. It does **not** say threaded searches are reproducible — they are
not, and the A/A column is the measurement of that (0.62–0.71 agreement, 4–17 cp median score gap).
**The practical consequence is the one §3 already gives, arrived at from a new direction: at
Threads 4 the node count and the score are not labels, and Hash does not fix or worsen that.** Note
also that pair1's Threads-1 arm reproduces §3's "Hash 16 vs 64 is a null at ~400k nodes" (1.000
agreement, 0 cp) and pair1b/1c reproduce "it is not a null above ~750k" — so the Hash axis was live
in the two arms where the interaction question mattered.

## 2. Hash × drawn-root bail — no interaction, with the axis proved live

Prediction from source: the bail returns from `Worker::search` at `search.cpp:2253-2271`, before the
iterative-deepening loop and before any `probe_tt`, so the table cannot matter; and the trigger
(`is_repetition() || halfmove_clock() >= 100 || is_insufficient_material()`) is a property of the
root board, so a bigger table cannot create one.

The grid is 9 fixtures: **8 bailing roots** (six fifty-move, one repetition via a move list, one
insufficient material) and **1 twofold control** that searches. The counts below are over the 8
bailing roots; the control is reported separately because it is the only cell that can move.

| comparison | bailing roots differing (bestmove/score/depth/nodes) |
|---|---|
| Hash 1 vs 8 | **0 / 8** |
| Hash 1 vs 64 | **0 / 8** |
| Hash 1 vs 256 | **0 / 8** |
| Hash 256 (MPV 1) vs Hash 64 (MPV 3) | **0 / 8** |

On the eight bailing roots every cell reports the same signature: `0` nodes, **empty pv**, bestmove =
the head of the generated list.

**The liveness control that makes this a result rather than a dead grid** (`pair3b-analysis.json`):
the same Hash axis, same harness, same command shape, on **searching** roots at `go nodes 400000`,
differs on **7 of 8** positions between Hash 1 and 256 (bestmove on 2, score on 7, nodes on 7). The
`unknown option` fault control also fires. So the Hash axis can move a cell here, and it moves none
of the bailing ones.

## 3. MultiPV × drawn-root bail — no interaction (and one exception worth naming)

Bailing roots: **0 of 8** differ between MPV 1 and MPV 3, at **0 nodes** and **empty pv** in every
cell. That confirms §1b's "10 of 10 bailing cells" from a different harness and adds MPV 3 at Hash 64
against MPV 1 at Hash 256, which is the most favourable pair for an effect.

The exception is the twofold control `b09` (a position that looks repeated but searches): it moves
from 8 `info` lines to 16 to 24 and its score and node count change, which is exactly what MultiPV
is supposed to do to a *searching* root. It is in the grid so that the null on the eight bailing
roots is not a null across the whole grid — without it, every cell would agree no matter what
MultiPV did.

## 4. MultiPV × Threads — confirmed at maximum strength

The audit's claim (§3, `search.cpp:2699-2741`): above MultiPV 1 the helpers are never started, so
`Threads` silently does nothing. Re-run here on this build with a control that must differ:

| cell | distinct signatures across 5 repeats, per position |
|---|---|
| Threads 1, MultiPV 1 | 1, 1, 1, 1, 1, 1 |
| **Threads 4, MultiPV 1** | **5, 5, 5, 5, 5, 5** |
| Threads 1, MultiPV 3 | 1, 1, 1, 1, 1, 1 |
| **Threads 4, MultiPV 3** | **1, 1, 1, 1, 1, 1** |

| comparison | identical on every run |
|---|---|
| MultiPV 3: Threads 1 vs Threads 4 | **6 / 6** |
| MultiPV 1 control: Threads 1 vs Threads 4 | **0 / 6** |

The control is what makes this a measurement: the same harness at MultiPV 1 produces five distinct
signatures per position and 0 of 6 identical cells, so it can see threading when threading is there.
**Verdict unchanged from the audit and now earned on this build: anyone with a MultiPV corpus should
assume their `Threads` setting did nothing.**

## 5. Book: Depth × OwnBook × Variety — three options, two jobs

Source: `uci.cpp:527` gates on `game_search && own_book && !book.empty() && game_ply(board) < book_depth`,
and `game_ply = 2*(fullmove-1) + side` (`uci.cpp:141-143`). So OwnBook and Book Depth decide
*whether* a book move is played; Book Variety only chooses among entries.

**OwnBook and Book Depth, 2×4×2 grid, 3 repeats, 3 boards (`pair5-analysis.json`):**

| cell | fullmove 1 (ply 0) | fullmove 11 (ply 20) | fullmove 16 (ply 30) |
|---|---|---|---|
| OwnBook **true**, Depth 0 | 0/3 | 0/3 | 0/3 |
| OwnBook **true**, Depth 20 | **3/3** | 0/3 | 0/3 |
| OwnBook **true**, Depth 30 | **3/3** | **3/3** | 0/3 |
| OwnBook **true**, Depth 100 | **3/3** | **3/3** | **3/3** |
| OwnBook **false**, every Depth | 0/3 | 0/3 | 0/3 |

**The boundary is exact and it is in plies, not moves.** On a line that is in the book
(`pair5b-boundary.json`), at game_ply 0, 3 and 6 with Book Depth set to `ply` and `ply+1`:
**24 of 24** cells satisfy `book plays iff game_ply < Book Depth`, including all six pairs that
straddle the boundary by one ply. So `Book Depth 1` books only the start position, and a harness that
thinks in fullmove numbers will be off by up to one ply.

**Book Variety is the only RNG, and it is monotone (`pair5c-variety.json`, 12 fresh processes each):**

| Book Variety | book played | distinct moves | histogram |
|---|---|---|---|
| 0 | 12/12 | **1** | `e2e4`×12 |
| 5 | 12/12 | 1 | `e2e4`×12 |
| 30 | 12/12 | **2** | `e2e4`×5, `c2c4`×7 |
| 100 | 12/12 | **3** | `e2e4`×5, `d2d4`×5, `c2c4`×2 |

**`Book Variety 0` is deterministic on 12 of 12 fresh processes — that is the reproducibility pin
§3 asks for, and it holds.** Two extra facts a harness needs: the book's RNG is seeded from the wall
clock at process start (`uci.cpp:161-162`), so *the seed cannot be pinned, only the distribution
collapsed*; and at Variety 5 the extra band is still empty, so "0 or low single digits" is the same
behaviour as 0 on this board — 0 is still the right pin, because it is the only value whose
determinism does not depend on the board.

## 6. Move Overhead × the clock floor — a regime switch, not a shift

The audit's clock result is a floor of 111 ms at a 60 ms increment, measured at the default overhead
of 10. `plan_clock_budget` (`include/forge/clock_plan.hpp:32`) has a discontinuity the audit's
wording does not cover: **`if (time <= overhead) return reserve_empty`**, and `Worker::search`
(`search.cpp:2287-2301`) routes that to the emergency path — one ply, at most 2000 nodes, TT move if
legal — with **no time management at all**. So a large Move Overhead does not shrink the floor
smoothly; it eventually stops planning.

`go wtime 200 btime 200 winc 60 binc 60`, one midgame position, 5 repeats, **search time only**
(see `STATUS.md` for why that matters). Planned hard is recomputed from
`include/forge/clock_plan.hpp` with the engine's own defaults, not read from a log:

| Move Overhead | planned hard | wall (min of 5) | nodes | depth | emergency path |
|---|---|---|---|---|---|
| 0 | 120 | 64 | 115,512 | 12 | no |
| 10 *(default)* | 114 | 64 | 115,512 | 12 | no |
| 50 | 90 | 64 | 115,512 | 12 | no |
| 100 | 60 | 60 | 87,596 | 11 | no |
| 190 | 6 | 5 | 9,163 | 8 | no |
| 195 | 3 | 1 | 4,633 | 7 | no |
| **200** | **0** | **0** | **47** | **1** | **yes** |
| 250 | 0 | 0 | 47 | 1 | **yes** |
| 1000 | 0 | 0 | 47 | 1 | **yes** |

A second batch (`pair4b-analysis.json`) covers overhead 150 at the same clock on the same board:
planned hard 30 ms, wall 30 ms, mid-way between the two rows above it. Its absolute wall times run
**about 10% lower** than this table's on the same cells (57 vs 64 ms at overhead 0) — a batch effect
on a 4-core box, not a disagreement about the shape, and the two batches are not mixed in any row.

Three things this says that the audit does not:

- **The response is not smooth in the overhead.** Between overhead 0 and 50 at a 200 ms clock the
  plan falls from 120 ms to 90 ms and **the wall time does not move at all** (64, 64, 64); by
  overhead 100 the plan has halved to 60 ms and the wall time has moved 4 ms. The engine reports at
  the end of a whole iteration, so a plan shorter than one iteration is truncated to that iteration.
  That is the same "clock move costs its last completed iteration" fact §8 states, seen from the
  option's side — and it is why a modest overhead buys no safety.
- **The floor is not a floor in the overhead; it is a cliff at `time ≤ overhead`.** At overhead 195
  with a 200 ms clock the engine still plans (3 ms hard) and searches 7 plies; at 200 it stops
  planning entirely and returns 47 nodes at depth 1. **Anyone who "adds margin" by raising Move
  Overhead past the remaining clock gets the emergency path, not a safer search** — the one direction
  the option's name makes look safe.
- **The audit's 111 ms floor is reproduced at the default.** At `wtime 111 winc 60` the plan is 66 ms
  hard and the search takes 58 ms (`pair4b-analysis.json`), which is consistent with 111 ms being a
  *plan* number rather than a wall-time one.

The larger-clock arm is the control that the cliff is about `overhead`, not about small clocks: at
`wtime 6000` the same overheads 0 → 1000 leave the plan at 450 → 405 ms and the search at 438 → 188 ms,
with no emergency path at any cell.

## 7. Threads × NNUE — the accumulators are per-thread, and the arm is proved able to see a race

Source: `SearchStack` holds `nnue::Accumulator accumulator` (`search.hpp:420`), `SearchStack` is a
`std::array` member of `Worker` (`search.hpp:483` region), and there is one `Worker` per thread. Only
the weight table is shared, and it is written only by a load.

**Source reading is not a measurement, so the arm has three proofs:**

| proof | result |
|---|---|
| TSan planted race (control that the sanitizer reports at all) | **3 reports**, `WARNING: ThreadSanitizer: data race` |
| TSan on a deliberately shared accumulator built from this source | **3 reports**, `search.cpp:1090 in Worker::static_evaluate` |
| TSan on the real build, 10 threaded cases | **0 reports**, and every case proved it searched (8–30 `info` lines each) |

The 10 real cases: Threads 4 and 8, NNUE on and off, `Hash 1` (maximum collisions), `Hash 32`, a
2 s movetime, MultiPV 3, the drawn-root bail, and a `Hash 32 → 64` resize mid-process.

Behavioural arm, 6 repeats, 8 positions (`pair6-analysis.json`), `go depth 12`:

| cell | score range | insane scores | distinct moves | deterministic positions |
|---|---|---|---|---|
| UseNNUE true, T1 | −490 … 1111 | **0** | 8 | 8/8 |
| UseNNUE true, T4 | −486 … 1097 | **0** | 13 | 0/8 |
| UseNNUE false, T1 | −401 … 808 | **0** | 8 | 8/8 |
| UseNNUE false, T4 | −410 … 804 | **0** | 15 | 0/8 |
| UseNNUE true, T4, Hash 256 | −486 … 1107 | **0** | 17 | 0/8 |

The same at `go movetime 1500`, where the tree is deepest and a race would have the most chances:
**0 insane scores in all five cells**, ranges −499 … 1202. That no score falls outside the
evaluator's legal band at any thread count, at either budget, is the cheap signature a corrupted
shared accumulator would leave — not a proof, but the failure mode this pair asks about.

**`UseNNUE false` at Threads 4 also behaves like the HCE path** — its score range tracks the
Threads-1 HCE arm (−410 … 804 against −401 … 808), not the NNUE arm (−490 … 1111) — so the absence
of an NNUE-specific defect at Threads 4 is not the option being ignored.

**Limit, stated plainly:** TSan finds races that *execute* on these 10 cases. A race that needs a
schedule this box did not produce is not excluded, and the behavioural arm only sees corruption that
changes a score or a move.

## 8. UseNNUE × NnueFile × NNUEArch — precedence, and a real defect

**First, the build trap.** `NNUEArch` and `NNUEArchFile` are `#if FORGE_NNUE_V3` and the brief's
CMake recipe never sets it; `include/forge/nnue.hpp:11` defaults it to 0. On the audit build:

```
$ printf 'uci\nquit\n' | ./forge | grep NNUEArch          -> (nothing)
setoption name NNUEArch value true -> info string unknown option NNUEArch
```

so **the locked binary cannot reach any v3 code path**, and `tests_astra_v3/` exercises a build the
audit does not ship. This report therefore uses a second binary built from the same tree with
`-DFORGE_NNUE_V3=1`, and every pair 7 row names which binary it came from.

**Precedence, from `search.cpp:1073-1130`:** `UseNNUE false` → hand-crafted, nothing else;
else v3 if `active()`; else v2 (`NnueFile`) plus the residual HCE. Measured — 18 arms, 3 positions,
`go depth 8` (`pair7-loader.json`):

| arm | `eval` says | search on p05 | verdict |
|---|---|---|---|
| audit build, default | `hce 440 nnue −113 total 327` | `e2e3 cp 445 n=6549` | baseline |
| audit build + `NNUEArch true` | same | same | **option unknown** |
| v3 build, no net | same as baseline | same as baseline | control |
| `NnueFile v2zero` | `hce 440 nnue 0 total 440` | `e2d3 cp 456 n=5516` | v2 load changes both |
| `NnueFile v2double` | `hce 440 nnue −233 total 207` | `g1g4 cp 405 n=5542` | v2 load changes both |
| `NNUEArchFile v3a` + `NNUEArch true` | `nnue_v3 0` | `g1f1 cp 0 n=1588` | v3 wins |
| `NNUEArchFile v3b` + `NNUEArch true` | `nnue_v3 −7` | `g1g3 cp 8 n=8762` | v3 wins |
| `NnueFile v2double` **then** v3B | `nnue_v3 −7` | `g1g3 cp 8 n=8762` | **v3 wins regardless of order** |
| v3B **then** `NnueFile v2double` | `nnue_v3 −7` | `g1g3 cp 8 n=8762` | **same** |
| v3B then `NnueFile <empty>` | `nnue_v3 −7` | `g1g3 cp 8 n=8762` | **v2 unload does not disturb v3** |
| v3B then `NNUEArch false` | `hce 440 nnue −113 total 327` | `e2e3 cp 445 n=6549` | back to baseline exactly |
| `NNUEArchFile` corrupt checksum | — | engine exits | refused, and says why |
| `NNUEArchFile` a **residual** v3 net | — | engine exits | refused: `residual v3 networks are not supported` |
| `NNUEArch true`, no file | — | engine exits **2** | fail-loud, as designed |

**So the order is a strict precedence and not a race:** UseNNUE beats `NNUEArch`; `NNUEArch` beats
`NnueFile`; setting `NnueFile` cannot unload a loaded v3 net; and `NNUEArch false` returns the engine
to **exactly** the baseline signature, which is what proves the arm was really on v3 in the cells
above it. The two refusal paths are fail-loud rather than silent fallbacks, which is the right shape.

### The defect: `eval` and the search disagree

| arm | search uses | `eval` reports | agree? |
|---|---|---|---|
| UseNNUE **true**, v3 net | v3 | `nnue_v3` | yes |
| **UseNNUE false, v3 net** | **hand-crafted** | **`nnue_v3`** | **no** |
| UseNNUE true, no v3 net | v2 + HCE | `hce/nnue/total` | yes |
| UseNNUE false, no v3 net | hand-crafted | `hce/nnue/total` | yes |

Measured on **6 of 6** positions (`pair7b-usennue-eval.json`), with both proofs the brief demands:

- **the search path ran and it is the hand-crafted one**: `UseNNUE false` + v3 net has the *same*
  four-field signature as `UseNNUE false` + no net on **6 of 6**, and a *different* one from
  `UseNNUE true` + v3 net on **6 of 6**;
- **the other path did not run**: 0 of 6 match the NNUE arm at all.

Cause, from source: `uci.cpp:575-582` gates the `eval` command on `nnue::v3::active()` alone, which is
`requested && loaded()` (`nnue_v3.hpp:156-158`) and never consults `nnue::enabled`; the search gates
on `!nnue::enabled` **first**, at `search.cpp:1076`, before the v3 branch at `:1078`.

**Why it matters beyond tidiness:** `eval` is the natural way for a tuning or regression harness to
confirm an evaluator setting took effect without paying for a search. In this one cell it confirms
the opposite of what the search does. The fix is one predicate — gate `eval` on `nnue::enabled` as
well — and it is the owner's call, not this seat's, because it changes what the `eval` command
reports.

---

## What could not be tested, and why

- **The 35-option surface is not 35 independent options.** The binary advertises **82** option names
  on this build (`uci` reply, counted; the split is from `uci.cpp:200-248` and the tunable table at
  `search.cpp:114-152`):

  | class | count | examples |
  |---|---|---|
  | named engine settings | **12** | Hash, Threads, MultiPV, Move Overhead, Ponder, OwnBook, Book File, Book Depth, Book Variety, UseNNUE, NnueFile, Clear Hash |
  | search toggles (check) | **18** | ContHist4PlyRead … SoundMatePruning |
  | standalone spin | **1** | DrawJitter |
  | tunable spins (`FORGE_EXPOSE_TUNABLES`) | **51** | LmrQuietBase … FailLowContinuationBonus |

  "About 35" is roughly the 31 settings, toggles and DrawJitter, without the tunables. This report
  covers 12 of the 82 by name; the rest are unmeasured as pairs, and the 51 tunables are the largest
  untouched block — they are the ones a tuning run actually varies, so they are where an interaction
  would do the most damage.
- **`Threads 8` is unmeasured as a pair** except in TSan. It is 2× oversubscribed on this 4-core box,
  so a T8 pair row would be a claim about eight threads on four cores and would not generalise; the
  audit already records this for Threads alone.
- **The Hash×Threads null is about MOVES and this corpus.** 28 position-cells is enough to exclude a
  large interaction, not to exclude a small one; the CI on the mean Δ is ±0.04 in agreement, which
  would not detect a 2% effect. A score-level interaction at a much larger budget is also not
  excluded — the budget here was 400k–2M nodes, and §3 measures Hash itself only above ~750k.
- **A TSan-clean run is not a proof of race-freedom**, only that no race executed in 10 cases. The
  planted-accumulator build is what makes the clean run mean anything.
- **v3 was tested only with two synthetic 32-hidden-unit nets** (built by
  `scripts/make_v3_nets.py` to the loader's own format). No real v3 network exists in this tree, so
  v3 *evaluation quality* and any v3-specific interaction with `Hash` or `Threads` are untouched —
  only the loader path and the precedence were measured.
- **The drawn-root × Hash result is at `go depth 8`** and on 9 fixtures. The bail cannot depend on
  depth by construction (it returns before the loop), and the depth 8 command is only there to give
  the searching control something to do.
- **Move Overhead was measured at one increment (60 ms) and three clocks.** The cliff at
  `time ≤ overhead` is arithmetic and does not depend on the increment; the *shape* between the cliff
  and the default may.
- **Book play inside complete games** remains untested, as §10 says. This report walks lines, not games.
