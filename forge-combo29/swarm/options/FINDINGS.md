# Option-surface audit: the 51 tunables, and two interference questions

Base commit: `6b98f217` (`forge-combo29`), built with the audit recipe
(`/usr/bin/g++` 13.3.0, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, Release).

## 0. What this file reports, and what it does not

Three questions were asked of the option surface:

1. **The 51 tunables behind `FORGE_EXPOSE_TUNABLES`** — do they clamp, refuse,
   and stay alive at their advertised extremes?
2. **Is there a second option pair where one silently overrides the other?**
3. **Is any option accepted but inert?**

Answer 1 is a clean row with counts. Answers 2 and 3 are a **null with a scope
limit that is the finding**, explained in §3: order-of-assignment cannot matter
in this engine, and the thing the report calls precedence is gating, not order.
Saying "no second precedence pair found" without that distinction would be a
false claim about what was tested.

**Not in this file, because they are already in the report** and the run order
this file was written under says not to re-spend on them: `NNUEArch` absent from
a default build, `eval` disagreeing with the search about `UseNNUE`,
`Move Overhead` being a cliff, and `Hash × Threads` being null under A/A control.

**The 18 switch rows are incomplete.** Section 6 states exactly what exists and
what does not, because a partial table that reads as a full one is the defect
this audit's own rules are about.

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

### 5b. Confirmed violation: `ContHist4PlyRead` reports a false mate

**This is a correctness failure, not an Elo loss, and it is the most serious
finding in this file.**

| | |
|---|---|
| FEN | `3k4/8/6K1/1Q6/8/8/8/8 w - - 6 4` |
| command | `go depth 12`, Threads 1, Hash 16, OwnBook false, cold (`ucinewgame`) |
| switch **on** | `score mate 12`, `bestmove g6f7`, 59,228 nodes |
| switch **off** | `score cp 1262`, no mate, 80,842 nodes |
| true distance | **mate in 5 plies (mate in 3 moves)** |

Three independent proofs that the claim is false rather than a convention
mismatch:

1. **The engine's own PV does not reach mate.** Replayed against python-chess:
   14 moves, every one legal, ending at `3Q4/8/4K3/8/8/8/8/8` — **not
   checkmate**. A `mate 12` claim needs 23 plies; the PV carries 14. This is the
   sharpest form of the defect and needs no convention to read.
2. **The true distance is 5 plies**, proved by a full-width unpruned minimax
   (`scripts/brute_mate.cpp`: no alpha-beta, no table, no pruning) which returns
   `PROVED 1 5`. The Python prover agrees.
3. **Deterministic and attributable.** 5 of 5 fresh processes with the switch on
   give `mate 12` / 59,228 nodes, bit-identical; 3 of 3 fresh processes with it
   off give no mate / 80,842 nodes.

**Scope, measured rather than assumed: 1 of 30 mate fixtures.** So this is a
narrow, position-specific false mate score and not a collapse of mate detection.
It is still a false forced-win claim at the depth a GUI displays.

**Mechanism: not established, and not claimed.** The switch adds a 4-ply-back
continuation-history term to quiet move ordering (`src/search.cpp:791`,
`:1327`, `:1337`). The plausible family is ordering-induced interaction with the
mate-score band or the TT, but that is a hypothesis with no isolation behind it.

### 5c. What is NOT measured

| property | status |
|---|---|
| 1 legality, 200 positions @ d12 | done for `ContHist4PlyRead` + baseline only |
| 2 mate, 30 proved fixtures | done for `ContHist4PlyRead` + baseline only |
| 3 terminal roots | done for `ContHist4PlyRead` + baseline only |
| 4 drawn-root bail | done for `ContHist4PlyRead` + baseline only |
| 5 ASan+UBSan per switch | **pipeline built and proved live; 1 of 18 switches run** |

The remaining 17 rows are `NOT RUN`, never PASS. The audit produced no evidence
against those switches and none for them.

### 5d. The sanitizer is proved live, which is what makes its silence mean anything

* The clean binary carries **35 `__asan_`** and **15 `__ubsan_`** symbols and its
  own `flags.make` contains `-fsanitize=address,undefined` — read from the build,
  not from the command that was typed.
* A control binary with **planted faults** caught a heap-buffer-overflow
  (`exit 1`, naming `planted_fault.cpp:22`) and a signed-integer-overflow
  (`exit 3`, naming `planted_fault.cpp:29`). A sanitizer run that reports nothing
  proves nothing unless these fire, so they run before every clean pass and the
  harness exits non-zero if they do not.
* The one full per-switch pass (`QuietExtinction`) searched **200 of 200**
  positions with **0 sanitizer lines**, and the position count is asserted so a
  run where the engine never searched cannot report a pass.

## 6. Reproducing

```bash
python3 scripts/tunables_matrix.py --engine <forge> --out evidence/tunables
python3 scripts/interference.py   --engine <forge> --out evidence/interference
python3 scripts/pins_sweep.py     --engine <forge> --out evidence
python3 scripts/audit.py --engine <forge> --corpus <corpus> --out <dir> --only BASELINE,ContHist4PlyRead
```

Each exits non-zero when any row is not clean, and each prints its row count so a
zero-failure result cannot be confused with a matrix that never ran.

