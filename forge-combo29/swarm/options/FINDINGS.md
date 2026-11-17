# Option-surface audit: the 51 tunables, the 18 switches, and two interference questions

Base commit: `6b98f217` (`forge-combo29`), built with the audit recipe
(`/usr/bin/g++` 13.3.0, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, Release).

## 0. What this file reports, and what it does not

Four questions were asked of the option surface:

1. **The 51 tunables behind `FORGE_EXPOSE_TUNABLES`** — do they clamp, refuse,
   and stay alive at their advertised extremes?
2. **Is there a second option pair where one silently overrides the other?**
3. **Is any option accepted but inert?**
4. **The 18 search switches** — do they keep the engine legal, mate-correct, and
   terminal-correct, and do they preserve the honesty pins?

Answers 1 and 4's pin half are clean rows with counts. Answers 2 and 3 are a
**null with a scope limit that is the finding**, explained in §3:
order-of-assignment cannot matter in this engine, and the thing the report calls
precedence is gating, not order. Saying "no second precedence pair found" without
that distinction would be a false claim about what was tested.

**§5b is a withdrawn finding.** A switch was flagged as reporting a false mate;
that inference was unsound and the claim is retracted in place, with the
measurement that refutes it. Reading §5b before §5c matters: §5c is what the
measurements actually support.

**Not in this file, because they are already in the report** and the run order
this file was written under says not to re-spend on them: `NNUEArch` absent from
a default build, `eval` disagreeing with the search about `UseNNUE`,
`Move Overhead` being a cliff, and `Hash × Threads` being null under A/A control.

**All five properties are swept across all 18 switches.** The table in §5c is
complete: 18 rows, no gaps, no failures.

## 1. The 51 tunables: every row clean

Source of the count: `tune::parameters()` at `src/search.cpp:114-148` lists 51
entries. The engine advertises **55 spin options**; the four that are not
tunables are `Hash`, `Threads`, `MultiPV` and `Move Overhead`, plus the
non-tunable spin pair `Book Depth` / `Book Variety` and the standalone
`DrawJitter`. 51 + 4 non-tunable spins = 55, and those five are excluded by name
in the harness and asserted as the only exclusions.

For each tunable, five values were sent:

| value | expected | meaning |
|---|---|---|
| advertised `min` | accepted silently | a tuner must be able to reach it |
| advertised `max` | accepted silently | same |
| `min - 1` | reported and clamped | the report must exist |
| `max + 1` | reported and clamped | same |
| `abc` | refused, old value kept | no silent parse |

and then a **search was run**, so "accepted" is not read off the `setoption`
reply alone. `apply_spin` (`src/uci.cpp:278-287`) is the code path that decides
this, and it refuses a non-integer parse and reports-then-clamps an
out-of-range integer, so the expectation is derived from the source rather than
assumed.

### Result

**51 tunables, 5 values each = 255 cells.**

| | count |
|---|---|
| cells examined | 255 |
| tunables with every cell correct | **51 / 51** |
| crashes or hangs | **0** |
| rows not conforming | **0** |
| tunables that moved the probe search at some value | **51 / 51** |

The last row is the one that matters most, and it is the one that would have been
missing from a clamp-only check: **every one of the 51 changes the search when
set to an extreme**, so none is a dead option. That is a positive result, not a
null, and it is the opposite of the "accepted but inert" class the report's
bench-blindness finding is about.

### The six divisors, checked at their minimum as a LIVE value

`LmrQuietDivisor`, `LmrNoisyDivisor`, `NullMoveDepthDivisor`,
`NullMoveEvalDivisor`, `LmrHistoryDivisor`, `TmSoftDivisor`.

Their advertised minimum is the only thing standing between a tuning sweep and a
division by zero, so the minimum was not merely accepted — a search was run at
it. All six searched and returned a legal move. The minimums are 100, 100, 1,
50, 1000 and 5 respectively, so none is 0; a tuner that clamps to the advertised
minimum cannot reach a zero divisor.

### Controls that make the null worth having

* **The matrix can fail.** The same harness refuses an unknown option by name —
  sending `setoption name SOUNDTEST value 1` produced
  `info string unknown option SOUNDTEST` and the driver raised rather than
  recording an accept. (Logged: this happened during harness bring-up against
  `sanitizer.py`, which is the same `driver.Engine` code path.)
* **The refusal path is exercised.** 51 × 1 malformed cells all produced
  `info string invalid value for option <name>`, which is the same predicate the
  harness asserts on. A check that never saw a refusal would be satisfied by a
  build that refused everything; here the accept cells and the refusal cells are
  both populated in the same run.
* **The probe is sensitive.** `UseNNUE true` vs `false` on the probe FENs
  changes the fingerprint, so "no effect" is a measurement rather than a
  property of the comparison (§3).

### One caveat that belongs beside the number

The probe is two FENs at depth 10. "Every tunable moved the probe" is therefore
a statement about those two positions, not about the whole game. It is strong
enough to rule out a tunable that is never read anywhere (the value reaches the
search and changes its output), and it is **not** strong enough to rule out a
tunable that is read but ignored in the specific subtree where it belongs.

## 2. A second `UseNNUE > NNUEArch > NnueFile`-style precedence pair

**Not found — and this is a weaker null than it looks, which is the point of §3.**

16 pairs were tested by setting A then B and B then A and comparing a
(two FENs × depth 10) fingerprint. **0 of 16 were order-dependent.** The pairs
were chosen where one option could plausibly gate another: `UseNNUE` against each
search switch, `OwnBook` against `Book File` and `Book Depth`,
`NullMoveMinDepth` against the two null-move guards, `AspirationDelta` against
both aspiration switches, `TmSoftDivisor` against both clock switches, and
`DeadMaterial` / `EvalRule50Damp` against `MaterialCorrectionWeight`.

## 3. Why "0 order-dependent" is a weak result, stated as such

This is the most useful thing in this file for anyone reading the option
surface, and it corrects a reading that the word "precedence" invites.

**Every option handler in this engine is a plain assignment plus, at most, a
cache clear** (`src/uci.cpp:383-473`). Setting A then B leaves exactly the same
pair of stored values as setting B then A. So order-independence is **true by
construction** here and the 0-of-16 result is expected rather than discovered.
A detector that reports 0 of 16 on a mechanism that cannot produce a 1 is
reporting its own construction.

The control confirms the instrument would have fired if there were something to
fire on: the fingerprint is sensitive (the `UseNNUE` on/off control differs), and
the unrelated-pair control (`Book Variety` vs `CheckExtensionDepth`) comes back
null as it must.

**What the report calls `UseNNUE > NNUEArch > NnueFile` precedence is GATING, not
ordering.** `NnueFile` has no effect while `UseNNUE` is false, which is a
predicate on a *value*, not a dependency on *sequence*. That difference decides
which test can find a second instance:

* an **order** test, like the one in §2, cannot find a second gating pair;
* a **value** test can — set the gate off, set the dependent option, and see
  whether the dependent option's effect disappears.

The no-effect sweep is the value test, and it is the half of this section that
carries weight.

### The no-effect sweep, and what it found

Each option was set to a value that should matter if it is read at all, against a
cold baseline fingerprint, and restored afterwards.

**2 of the tested options produced no change on the probe: `OwnBook` and
`NnueFile`.**

* `OwnBook true` vs `false` changes nothing on the probe **because the probe uses
  `go depth`, and the book fires only on a clock form or `movetime`** — a
  documented behaviour of this engine, not a defect. The sweep's null here
  reproduces a known finding rather than adding one.
* `NnueFile` changes nothing **because `UseNNUE` was true and the built-in net is
  embedded** (`src/nnue_weights.inc`); a path that fails to load leaves the
  embedded net in place. This is the same gating the report already records, seen
  from the other side.

**So this sweep adds no new inert option, and the two nulls it does report are
both explained by behaviour already in the report.** Stated as a null: on these
two FENs at depth 10, with these values, no option other than `OwnBook` and
`NnueFile` failed to move the search.

**The limit, beside the result:** a fixed-depth probe cannot see an option that
only matters outside the positions searched. `NO_EFFECT` here means "no effect on
this probe", which is strictly weaker than "no effect" — the identical limit that
makes `bench` blind to a switch, and the reason §1's positive result (51 of 51
moved the probe) is more informative than this section's null.

## 4. Files

| path | what it is |
|---|---|
| `scripts/tunables_matrix.py` | the 51 × 5 matrix |
| `scripts/interference.py` | the 16 pairs, the two controls, the no-effect sweep |
| `scripts/pins_sweep.py` | the four honesty pins under each of the 18 switches |
| `scripts/driver.py` | UCI driver: no piped stdin, both streams scanned, per-command log windows |
| `evidence/tunables.json` | every cell, with the probe node count per cell |
| `evidence/interference.json` | every pair's two fingerprints, plus the sweep |
| `evidence/pins-per-switch.json` | bench 11/13/16 and perft 5 for baseline and all 18 switches |

## 5. The 18 switches: pins complete, five properties partial

### 5a. Honesty pins: all 18 clean

Bench node counts move for 15 of 18 switches. That is expected and is **not** a
pin violation: `bench` is a search, so a search heuristic changes it.

**Perft is the pin a search switch cannot legitimately move.** It walks every
legal move to a fixed depth and never consults evaluation, history, pruning or
the clock. A switch that moves perft has touched move generation or the board.

**18 of 18 leave perft 5 at exactly 4,865,609**, and the baseline arm reproduces
all four pins (bench 11/13/16 = 312866 / 862329 / 3024920, perft 5 = 4865609)
before any switch is tried. So the honesty gate passes for every switch, and the
five-property rows below are measured on builds whose pins were verified.

### 5b. A finding this audit withdrew, and why it is kept

**A false-mate claim against `ContHist4PlyRead` was raised during this run and is
withdrawn.** It is recorded here, before the results, because a reader who saw
the interim report needs to know the correction landed and on what evidence — and
because the withdrawal took three separate checker bugs to establish.

The short version, with the full account in §5e:

* The flag rested on the engine's `mate 12` arriving with a 14-move PV that does
  not end in checkmate. **That inference is unsound:** the PV comes from a
  depth-12 search, so it cannot exceed 12 moves, while `mate 12` needs 19–23
  plies. A short PV is guaranteed by the depth and says nothing about the mate.
* Re-decided by proving the position after each arm's own bestmove: **all five
  flagged rows across all arms are true claims with an over-long distance.
  Unsound 5 → 0.**
* **Read §5c for the results.** Nothing in this file is a correctness violation.

### 5c. The full table: 18 of 18 pass all four search properties

Generated by `scripts/report.py` from `evidence/switch-arms.json`; every cell is a
count, never a bare "ok".

| switch | 1 legality (200 @ d12) | 2 mate (30 proved) | 3 terminal | 4 drawn-root bail | 5 ASan+UBSan |
|---|---|---|---|---|---|
| `ContHist4PlyRead` | PASS 200/200 | PASS 25/25 proved; 2 missed vs base | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `NonPawnCorrection` | PASS 200/200 | PASS 25/25 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `LmrDeeperShallower` | PASS 200/200 | PASS 26/26 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `EvalRule50Damp` | PASS 200/200 | PASS 28/28 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `ThreatHistory` | PASS 200/200 | PASS 25/25 proved; 1 missed vs base | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `LmrSignedCorrection` | PASS 200/200 | PASS 25/25 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `LmrLateParentRelief` | PASS 200/200 | PASS 27/27 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `HindsightDepth` | PASS 200/200 | PASS 29/29 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `NullThreatVerify` | PASS 200/200 | PASS 24/24 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `NullSeeVeto` | PASS 200/200 | PASS 24/24 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `AspCappedReopen` | PASS 200/200 | PASS 25/25 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `AspArmLate` | PASS 200/200 | PASS 23/23 proved; 2 missed vs base | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `EvasionOrdering` | PASS 200/200 | PASS 24/24 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `DeadMaterial` | PASS 200/200 | PASS 24/24 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `QuietExtinction` | PASS 200/200 | PASS 18/18 proved; 7 missed vs base | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `TmFinishIteration` | PASS 200/200 | PASS 24/24 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `TmNodeShare` | PASS 200/200 | PASS 24/24 proved | PASS 6/6 | PASS 4/4 | PASS clean+F2 |
| `SoundMatePruning` | PASS 200/200 | PASS 24/24 proved; 2 missed vs base | PASS 6/6 | PASS 4/4 | PASS clean+F2 |

**18 of 18 rows fully clean across all five properties. Zero failures, zero gaps.**
Every claimed mate proved; every legality check replayed against python-chess;
every terminal verdict held; every bail verdict held with its control; and every
sanitizer pass ran 200 of 200 positions with 0 sanitizer lines while the planted
faults in the same build were caught.

**`clean+F2` means:** the sanitizer reported nothing on the clean run AND two
planted faults were caught by the same binary and harness. The second half is
what makes the first half a measurement.

### 5d. What "missed vs base" means, and why it is not a failure

Five arms report fewer mates than the baseline at the same depth. That is a
**depth-12 reachability difference**, not a correctness one, and the column says
so rather than folding it into PASS or FAIL:

* `QuietExtinction` misses 7 of 30. It prunes non-root quiet tails after wide
  fail-lows, which is exactly the mechanism that would reach a long mate's first
  quiet move later. The 18 it does claim are all proved true.
* `ContHist4PlyRead`, `AspArmLate`, `SoundMatePruning` miss 2 each; `ThreatHistory`
  misses 1.

**Zero of these misses is a false claim.** A missing mate at a fixed depth costs
search quality; a false mate would be a correctness bug. This table separates
them, and the separation is the finding: the switches change what a depth-12
search can reach and never make it claim something untrue.

### 5e. A withdrawn finding, kept because the withdrawal is the useful part

**Withdrawn: "`ContHist4PlyRead` reports a false mate."**

The original flag rested on the engine's `mate 12` arriving with a 14-move PV
that does not end in checkmate. **That inference was unsound:** the PV comes from
a depth-12 search, so it cannot exceed 12 moves, while a `mate 12` claim needs
19–23 plies. A short PV was guaranteed by the depth and carried no information
about the mate's existence.

Re-decided by proving the position after each arm's own bestmove, under longest
defence, the four flagged rows are all **true claims with an over-long distance**:

| arm | FEN | claimed | the move forces mate in |
|---|---|---|---|
| `ContHist4PlyRead` | `3k4/8/6K1/1Q6/8/8/8/8 w` | mate 12 | 9 plies |
| `LmrDeeperShallower` | `8/6k1/8/6K1/8/8/8/7Q w` | mate 10 | 9 plies |
| `LmrDeeperShallower` | `8/6k1/8/3Q1K2/8/8/8/8 w` | mate 8 | 7 plies |
| `ThreatHistory` | `7k/8/8/6K1/8/8/8/7Q b` | mate −14 | 6 plies |

`scripts/rejudge.py` re-decided all 19 arms from stored rows: **unsound 5 → 0**.
All five original flags were defects in this audit's checker, in three distinct
ways:

1. **PV length used as evidence of a mate's existence.** Fixed by proving the
   position after the bestmove instead.
2. **The wrong side assumed to move after the bestmove.** Backwards for every
   negative claim. The expected sign now derives from the claim's sign, and both
   directions are controls.
3. **`prove()` returning `None` for two different reasons** — no mate, and
   exhausted budget — folded into one verdict, which produced a confident FALSE
   on a position whose mate exists. A failure is now retried at 12× the budget
   before it counts as a refutation.

Each of the three was caught by a check disagreeing with another check, not by
reading the code. The controls that now guard them are in `mate_controls()`.

### 5f. Mate distance is imprecise on sparse endgames, and it predates the switches

The withdrawn rows still show something real, and it belongs to the base engine:

| FEN | true | baseline | `ContHist4PlyRead` |
|---|---|---|---|
| `3k4/8/6K1/1Q6/8/8/8/8 w` | mate 3 moves | `cp 1203`, **no mate at all** | `mate 12` |
| `8/6k1/8/6K1/8/8/8/7Q w` | mate 3 moves | `mate 4` | `mate 3` |
| `7k/8/8/6K1/8/8/8/7Q b` | mate 3 moves | `mate −5` | `cp −1053`, no mate |

The imprecision is **pre-existing on KQ-vs-K positions**, the switches move it in
**both** directions, and on one position the switch is *more* accurate than the
baseline. Reporting-accuracy property of the base engine, not a switch defect.
**Mechanism not established and not claimed.**

### 5g. The sanitizer sweep: 18 of 18 clean, and proved live before each pass

**18 of 18 switches ran the full 200-position set under ASan+UBSan with 0
sanitizer lines**, each pass searching 200 of 200 positions. The position count is
asserted, so a run where the engine never really searched cannot report a pass.

The evidence that the sanitizer was live, for every one of the 18:

* the binary carries **35 `__asan_`** and **15 `__ubsan_`** symbols, read with
  `nm`, and its own `flags.make` contains `-fsanitize=address,undefined` — read
  from the build, not from the command that was typed;
* a control binary with **planted faults** caught a heap-buffer-overflow
  (`exit 1`, naming `planted_fault.cpp:22`) and a signed-integer-overflow
  (`exit 3`, naming `planted_fault.cpp:29`) in every run's harness pass. The
  harness exits non-zero if either is missed, so a clean result cannot be
  reported by a broken sanitizer.

Per-switch JSON is in `evidence/sanitizer/<switch>/sanitizer.json`.

## 6. Reproducing

```bash
python3 scripts/tunables_matrix.py --engine <forge> --out evidence/tunables
python3 scripts/interference.py   --engine <forge> --out evidence/interference
python3 scripts/pins_sweep.py     --engine <forge> --out evidence
python3 scripts/audit.py --engine <forge> --corpus <corpus> --out <dir> --only BASELINE,ContHist4PlyRead
```

Each exits non-zero when any row is not clean, and each prints its row count so a
zero-failure result cannot be confused with a matrix that never ran.

