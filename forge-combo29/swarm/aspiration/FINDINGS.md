# Aspiration windows — no published bound, but two switches change the answer

Audit base `6b98f217`, engine folder `forge-combo29/`. Build: `/usr/bin/g++` 13.3.0 with
`LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, `-DFORGE_MARCH=x86-64-v4`, Release.

## The answer in one paragraph

**No bound is ever published as a value on the shipped configuration.** Over 5,320 traced
root iterations (133 positions × depth 10 × four deltas) every published score was strictly
inside its final window, so every published score was an exact value. The dangerous case —
a mate window — is also clean: 190 positive mate claims, 180 of them long enough to test,
and **not one** fails to mate. But the switches are not cosmetic. `AspirationDelta` moves
the published score on **126 of 133** positions, and each of the two switches moves it on a
different set: **`AspCappedReopen` on 114 of 141** and **`AspArmLate` on 111 of 141** (141 =
133 depth positions + 8 mate fixtures; the two sets overlap in 103 positions, with 10 moved
by `AspCappedReopen` alone and 7 by `AspArmLate` alone). Each switch also **loses a mate the
default finds** (2 of 8 mate fixtures). Aspiration here is **not** a pure speed optimisation.

## What I measured

| Question | Result |
|---|---|
| Bound published as a value | **0** in 5,320 traced iterations |
| Mate window clean | **0** false mates in 180 testable claims; PV always mates |
| `AspCappedReopen` bound-publishing break | **0** firings in 448 iterations, and provably unreachable in arithmetic |
| `AspCappedReopen` effect on scores | moves the score on **114 of 141** positions; reopen path runs (5 tries → 13 on one board) |
| `AspArmLate` | fires, **0** bounds, moves the score on **111 of 141**; **loses mates** at fixed depth |
| `AspirationDelta` changes the answer | **yes** — score on 126/133, move on 95/133 |
| Score jumps that come back (bound artefact) | **0** in the traced build |

Every row carries its build, its depth, and whether the score was exact. The engine
**never prints `lowerbound` / `upperbound`** — see "Protocol gap" below.

---

## 1. Returned score validity — clean, and here is how it is known

The engine prints no bound token, so "is this a value?" cannot be read off the wire. I
instrumented the root iterative-deepening loop instead of guessing from output
(`scripts/patches/asp-trace-fault-off.patch`, one file, `src/search.cpp`). After each
finished iteration it emits the final window and the returned score plus

```
inside = (alpha < score < beta) ? 1 : 0
```

which is computed on the internal integers. `inside == 0` on a published iteration is
exactly a published bound: the score sits at or beyond the window edge, meaning the search
established an inequality, not a value.

**Result — 1,330 iterations, 133 positions, depth 10, delta 18:**

| quantity | value |
|---|---|
| iterations traced | 1,330 |
| iterations with `inside == 0` | **0** |
| published scores that are bounds | **0** |

and at four deltas (4 / 18 / 50 / 200), 1,330 iterations each:

| delta | iterations | `inside == 0` |
|---|---|---|
| 4 | 1,330 | 0 |
| 18 | 1,330 | 0 |
| 50 | 1,330 | 0 |
| 200 | 1,330 | 0 |

**The control, because a clean run means nothing otherwise.** I built a third variant with
a planted defect: on a fail-high it publishes the bound and breaks without re-searching.
That build must be caught, or the checker is dead. Restricted to the rows where the fault
actually fires at the last iteration (**6 of 40** positions — the fault needs a fail-high
there and most positions do not have one), the detector flags **6 of 6**. So the zero above
is a real zero: the counter fires when the condition exists.

The corpus reaches the condition rather than dodging it: **133 of 133** positions engage
aspiration (a narrowed window), with up to **14** re-searches in a single iteration.

## 2. Mate windows — clean, with one honest limit

Eight positions whose DTM was **proved by an AND/OR search that does not involve the
engine** (`scripts/gen_mates.py`): mates in 1, 2, 3 and 4, two each. My first attempt
labelled eight positions by eye as "mate in 2/3/4" and **all eight were mate in 1** — the
brief's manufactured-pass trap, and the reason the labels now come from a proof.

Of 190 positive mate claims across five arms, **180 had a PV long enough to test the
claim**; all 180 play out to checkmate, and **0 are false**. The remaining **10** claims
have a PV **shorter** than the distance claimed (e.g. `mate 10` = 19 plies against a 13-ply
PV), so they are **unverifiable from the wire, not wrong** — an independent proof confirms a
real mate exists inside the claimed distance in every one. My first pass called these
"false mates"; that was wrong and I withdraw it.

A mate distance the search could not have earned is checkable without trusting the line:
`mate N` is 2N−1 plies, which cannot exceed the engine's own `seldepth`. **0 overclaims**
across all ladders and arms.

`go mate N` — the one place a bound could reach a caller, because the window narrows to
`[mated_in(ply), mate_in(ply+1)]` and an empty window returns alpha (`search.cpp:1431-1435`)
— published an exact mate on **8 of 8** fixtures, 0 bound iterations.

## 3. The two switches — both measured, and one is a dud in a specific way

### `AspCappedReopen` — its bound-publishing branch can never fire

The switch replaces the geometric reopen (`score ± delta`, then `delta += delta/2 + 4`)
with a fixed `±13` step, and it contains two `break` paths that would publish a bound. They
are **arithmetically unreachable**:

- `capped_fail_high(x)` for a non-mate, non-decisive `x` returns `min(x + 13, INF)`.
- The branch is entered only when `x >= beta`, and `beta` was just set to `x`, so
  `beta' = x + 13`, and the test `x >= x + 13` is false.
- The mate and `|x| ≥ 640` cases return `±Inf`, further away still.

Measured: **0** `high_break` / `low_break` exits in 448 iterations with the switch on,
against a **live** counter (the planted-fault build registered **15** `high_fault` exits in
the same channel). But the switch is **not** inert — its *reopen* path does run and changes
the windows materially: on one board, depth 7 needed **5** tries with the switch off and
**13** with it on, with a different window sequence. So `AspCappedReopen` is best described
narrowly: **its bound-publishing break cannot fire** (that is the arithmetic above), while its
reopen path still changes *which* search you run.

The distinction matters, so both halves are measured separately: **114 of 141 positions**
have a different published score with the switch on, and it **loses a mate** at fixed depth
(§4). "Cannot publish a bound" is not the same claim as "cannot change the answer", and only
the first one is proved by the arithmetic.

### `AspArmLate` — fires, sound, and loses mates

After an iteration that failed high or low, the next iteration uses a full window. This
runs, changes scores on 111 of 141 positions, and publishes **0** bounds. It also loses
mates at fixed depth (§4).

The `AspArmLate` unit test in `tests_r3_09` asserts only that `bench 13` *changes* when the
switch is on. It does. That test cannot tell a speed change from a verdict change, and the
verdict does change.

## 4. The finding worth acting on: aspiration moves the answer

Same position, same depth, only the window policy differs:

| fixture | true DTM | default | `AspCappedReopen` | `AspArmLate` | both |
|---|---|---|---|---|---|
| `8/8/8/5KQ1/8/5k2/8/8 w` | 7 plies (M4) | **M4** @d10 | M7 @d11 | M17 then **M4** @d14 | M6 @d15 |
| `8/8/8/3K4/6Q1/8/8/4k3 w` | 7 plies (M4) | **M4** @d14 | M10, M7, M6 | **M4** @d16 | — |

At a fixed depth, enabling either switch can replace a found mate with a centipawn score.
The engine still gets there eventually — this is a *when*, not a *whether* — so it is a
depth-efficiency cost, not a soundness defect. But a consumer that fixes depth (or a node
budget, which is the same thing under pressure) gets a materially different answer.

**`AspirationDelta` is not a free parameter.** From 18 to 50 changes the score on 126 of
133 positions; to 200, on 126 of 133. Nodes move too — median aspiration/wide node ratio
0.852 at d8, 0.865 at d10, 0.879 at d12 — so aspiration buys roughly **12–15% fewer nodes**
on the median position but is *worse* on some (max ratio 2.56 at d12).

That is a modest, position-dependent gain, and it is bought with answer instability. The
same table shows this directly: `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w`
reports `cp 517` at delta 18 and `mate 2` at delta 200 — and `g3g6` **really is mate in 2**,
independently proved. The default setting misses a forced mate that a wider window finds.

## 5. Depth-to-depth jumps: none that look like a bound

I logged score per depth 1–16 on 16 positions, five arms. Scores move (they must — search
is not monotone), but the specific artefact asked about — a score that jumps and comes back
*because a bound was published* — is absent: every rung in the traced build has
`inside == 1`. The wide-window and never-narrow ladders cross-check the same rungs and agree
in direction within each arm's own policy. The only discontinuities are mate transitions
(e.g. `cp 1076 → mate 4`), which are genuine.

## Protocol gap — the wire cannot distinguish a value from a bound

`grep` for `lowerbound` / `upperbound` across `src/` and `include/` at `6b98f217` returns
**nothing**: the engine has no way to say "this score is a bound". Combined with trap 1b
(empty PV means no move was chosen) and trap `3a0` (`go mate N` is a different search), a
GUI or training pipeline consuming this engine's `info` lines has **no field** that tells it
whether a score is exact. On this build that is currently harmless because no bound is ever
published — but it is a guarantee held only by the implementation, not by the protocol, and
nothing in the output would reveal it if that changed.

---

## What I withdrew

1. **Eight "verified mate in 2/3/4" fixtures were all mate in 1.** Labels came from my eye,
   not a proof. Corrected: DTM now comes from `gen_mates.py`'s AND/OR search, and every
   label is re-verified.
2. **A "false mate" finding, 8 rows, withdrawn.** I flagged PVs that did not end in mate.
   Inspecting them showed the PV was *shorter than the claimed distance* — a truncated PV
   cannot disprove a mate. Correctly classified: **0 false, 10 unverifiable-but-true**.
3. **A claimed pin mismatch on all builds.** My bench parser read the last field of
   `... nodes N time T nps R`, which is `nps`, not `nodes`. The pins were correct all along;
   the parser was not. Fixed to read the token after `nodes`.
4. **A claim that the pins require `OwnBook false`, and that the book changes bench.**
   Withdrawn after the coordinator checked it against the source and the binary. `bench`
   never touches the book: the book is gated in the **`go`** handler (`uci.cpp:523-542`,
   `game_search` at 525, the probe at 527, and `game_search` also requires a clock) and `bench` is a separate branch
   (`uci.cpp:590`). Measured on the audit base, bench 11 = **312,866** with `OwnBook true`,
   with `OwnBook false`, and with the option never sent. The 1,919,423 I attributed to the
   book was the `nps` field from the same parser bug as item 3
   (`312866 * 1000 / 163 = 1919423`). The pins are unconditional; `OwnBook false` is a
   harmless habit, not a precondition. This is the same failure mode as item 3 — a harness
   bug restated as a property of the engine — and it had reached three files plus a shell
   comment before it was caught.

## What is left untested, and why

- **Single-threaded only.** All measurements are `Threads 1`. Aspiration interacts with the
  shared TT across threads and this design cannot attribute a score to a thread.
- **Fixed depth, no clock.** Time-managed searches stop at iteration boundaries and inherit
  this logic, but I did not measure a clock arm.
- **The corpus cannot reach a mate-score aspiration window.** Aspiration narrows from depth
  4, and every mate in the corpus resolves before or at depth 3. So the "window around a
  mate score" case is tested via `go mate N` and the deep KQK ladders, **not** by placing a
  narrowed window directly on a mate score. I could not construct that case; saying so is
  more useful than implying I covered it.
- **Delta sweep is 4 points, not a curve.** 4 / 18 / 50 / 200 bracket the allowed 4–200 but
  cannot locate a threshold.

## Reproduction

The scripts resolve paths from their own location. `ASP_BUILD_ROOT` points at the four
`forge` binaries (default `<this folder>/../builds`, which is not committed — they are build
outputs and the brief forbids binaries); `ASP_EVIDENCE` defaults to the committed
`../evidence`. Build each variant with:

```sh
cmake -S <repo>/forge-combo29 -B builds/<name> \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release \
  -DFORGE_MARCH=x86-64-v4 -DCMAKE_CXX_FLAGS="-DFORGE_ASP_TRACE=<0|1> -DFORGE_ASP_FAULT=<0|1> -DFORGE_ASP_OFF=<0|1>"
make -C builds/<name> -j
```

with the per-build macro sets in `scripts/asp_paths.py`. The patch that introduces the three
macros is `scripts/patches/asp-trace-fault-off.patch` (one file, `src/search.cpp`).

```
ASP_BUILD_ROOT=/path/to/builds scripts/pin.sh builds/stock/forge
scripts/build_corpus.py                    # 133 depth + 8 proved-mate positions
scripts/gen_mates.py                       # DTM by AND/OR proof, engine not involved
scripts/measure_aspiration.py --depth 10   # measures 1, 3, 4 (validity/delta/switches)
scripts/measure_mate.py                    # measure 2
scripts/capped_reopen_reachability.py      # measure 3, with planted-fault control
scripts/stock_vs_wide.py                   # pinned stock vs never-narrow
scripts/scan_false_mate.py                 # per-depth mate-claim scan, four arms
scripts/classify_mate_claims.py            # FALSE / LOOSE / TRUE_TIGHT verdicts
```

Every evidence file in `evidence/` was produced by these scripts; re-running them from a
clean checkout reproduces the files byte-for-byte except for fields that record a build
*path*, which were deliberately replaced with build *names* for that reason.

Pins on the analysis build: bench 11 = 312,866; bench 13 = 862,329; bench 16 = 3,024,920;
`go perft 5` = 4,865,609. `bench N` sent on **stdin**, because `./forge bench 11` as argv
prints nothing and exits 0.

**Correction — `bench` does not consult the book, and the pins do not depend on `OwnBook`.**
An earlier version of this section claimed `OwnBook false` was required and that "a bench
with the book on gives 1,919,423 at depth 11". That is false, and it was corrected against
the source and the binary. Measured on the audit base, three ways:

| setting | bench 11 nodes |
|---|---|
| `setoption name OwnBook value true` | 312,866 |
| `setoption name OwnBook value false` | 312,866 |
| option never sent | 312,866 |

The source agrees. The book is gated inside the **`go`** handler (`uci.cpp:523-542`: `game_search` at 525,
probe at 527), where
`game_search` additionally requires `time_ms >= 0 || movetime_ms >= 0`, so the book applies
only to clocked game play — never to `go depth`, and never to analysis or pondering. `bench`
is a separate branch (`uci.cpp:590`) that builds its own `Searcher(16)`, its own `Board` per
FEN and its own `SearchLimits`, with no book call on the path. In this build the book is
empty anyway (`Book File` is `<empty>`), so the `!book.empty()` conjunct cannot hold.

**What actually produced 1,919,423:** my own bench parser read the *last* field of
`... nodes 312866 time 163 nps 1919423`, which is `nps`, not `nodes` — and `312866 * 1000 /
163 = 1919423` exactly. It was a units bug in the harness, not a different search. The same
bug is the third item in "What I withdrew". Setting `OwnBook false` remains harmless and the
scripts still do it, but it is a belt-and-braces habit, **not** a precondition of the pins.
