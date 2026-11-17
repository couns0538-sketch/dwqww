# `setoption name Hash` during a live session — forge-combo29 @ `6b98f217`

Five questions, five verdicts, plus the memory curve and a runner recommendation.

Base commit `6b98f2170a3210e71beed04bbd2553972c253ed7`. Built with
`-DCMAKE_CXX_COMPILER=/usr/bin/g++` and `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`
(g++ 13.3.0). Sanitizer build adds `-fsanitize=address,undefined -DFORGE_PORTABLE=ON`.

## Honesty pins — confirmed before any measurement

`scripts/pins.py` drives `bench 11/13/16/20/22` with the net on and off, then
`go perft 5`, and asserts all eleven numbers:

```
net-on : 312866 862329 3024920 12389307 34048354     PASS
net-off: 375354 907205 2448617 13573040 24506465     PASS
perft5 : 4865609                                      PASS
PINS MATCH combo29
```

`evidence/pins.json`. The four pins named in the task (312,866 / 862,329 /
3,024,920 / perft 5 4,865,609) are inside that set.

---

## The one-line answer

`setoption name Hash value N` is **not a resize. It is a reallocation, and it is
a cache wipe at every size** — including when `N` is the value already set and
including when the table is already empty. The wipe is a **proper subset** of
what `ucinewgame` does, so it is *not* a cold reset, and the difference is
measured below. The reallocation also holds **two tables at once**, which is the
only finding here that changes the engine's memory *requirement* rather than its
speed or its answer.

---

## Verdict 1 — Correctness across a resize: **differs from a fresh process, 30/30 in both directions**

Depth 18, Hash 16 ↔ 256, 30 positions, engine deterministic (proved below).

| comparison | differs | bestmove changed | nodes changed |
|---|---|---|---|
| 16 → 256 vs fresh 256 | **30/30** | 3 | 30 |
| 256 → 16 vs fresh 16 | **30/30** | 2 | 30 |

Example, position 0: `fresh(256)` = 964,492 nodes / cp 174; `16 → 256` = 676,484
nodes / cp 188. `fresh(16)` = 735,057 / cp 173; `256 → 16` = 568,267 / cp 178.

**So the resize leaves the table in a different state than an allocation — but
"the table" is the wrong noun, and the decomposition below is the finding.**

### The table is emptied completely. The difference is in the histories.

The comparison above cannot separate two mechanisms, because the warm-up search
warms *both* the table and the per-worker history tables, and a resize only
touches the former. Two independent instruments separate them.

**Instrument 1 — an unsearching read of the table.** `go wtime 0` on a warm table
answers **0 nodes with no `info depth` line** (root is a TT hit); on a cold table
it answers 22–138 nodes with exactly one `info depth 1` line
(forge-findings.md §7 item 2d0). That is a binary read of "is the root in the
table", independent of depth and budget. 30 positions:

| arm | reads warm |
|---|---|
| no reset (positive control) | **30/30** |
| **same-value resize** | **0/30** |
| resize up 16 → 256 | **0/30** |
| resize down 256 → 16 | **0/30** |
| `Clear Hash` | **0/30** |
| `ucinewgame` | **0/30** |
| fresh process (negative control) | **0/30** |

Both controls hold: the probe reads warm when the table is warm and cold when it
is cold, so its zeroes are real. **The resize empties the table exactly.**

**Instrument 2 — the window where the two sizes are equivalent.** The audit
established that at `go nodes 50000`, Hash 16 and Hash 64 are indistinguishable
(**0 of 24** cells differ), and that they diverge above ~200k. That gives a
falsifiable prediction: if the post-resize difference were a property of *table
size*, it would vanish in that window; if it is a property of *uncleared
histories*, it must persist there, because a resize touches histories at no size.
24 positions, `go nodes 50000`, Hash 16 → 64:

| arm | prediction | result |
|---|---|---|
| E1 `fresh(64)` vs `fresh(16)` | 0 (the audit's own window) | **0/24** |
| E2 `[warm16 → resize 64]` vs `fresh(64)` | **>0** | **24/24**, 4 moves changed |
| E3 `[warm16 → ucinewgame]` vs `fresh(16)` | 0 | **0/24** |
| E4 `[warm16 → resize 64 → ucinewgame]` vs `fresh(64)` | 0 | **0/24** |

Replication on 30 fresh positions: **E1 0/30, E2 29/30 (6 moves), E3 0/30,
E4 0/30.**

**E1 = 0 with E2 = 24/24 is the whole finding.** Same endpoint size, same budget,
same table size at the end; the only difference is allocation versus resize. E1
rules out table size as the explanation. E2 says the difference survives where
size cannot matter. **E4 = 0 names the residue: it is the search histories, not
the table.**

So the accurate statement is: **a resize empties the table as thoroughly as
`Clear Hash`, and leaves the histories warm — which makes the following search
neither cold nor warm, but a third state.**

### The comparison can fail, and does

The two nulls above are not vacuous, and the failure is visible in the same run:

- `fresh(16)` vs `fresh(16)` in a second process: **0/30 differ** (repeat control
  passed).
- `fresh(256)` vs `fresh(256)` in a second process: **0/30 differ**.
- `fresh(16)` vs `fresh(256)`: **30/30 differ** — the comparison is capable of
  reporting a difference, on the same positions, at the same depth.
- E2 is **24/24** while E1 on the same positions is **0/24**.

**Every "matches" verdict in this document is a zero produced by an instrument
that returns a non-zero on the same positions when the thing is present.**

---

## Verdict 2 — Resizing mid-search: **a `bestmove` arrives, and it is the searched one, not a fabricated one**

`uci.cpp` calls `stop_search()` on entry to every `setoption`, so the search is
stopped before the option is applied. Confirmed on the wire, and the interesting
part is what the `bestmove` is.

Method: `go infinite`, wait until depth 14 has been *announced*, then send
`setoption name Hash value 256` (or `stop`, as the control). 30 positions.

| statistic | result |
|---|---|
| `bestmove` present after a mid-search `setoption` | **30/30** |
| equals the move from an explicit `stop` at the same point | **30/30** |
| equals the pre-stop announced PV head | **30/30** |
| equals a complete fresh `go depth 14` bestmove | **30/30** |
| equals a complete fresh `go depth 15` bestmove | 29/30 |
| equals **neither** (i.e. a move nobody searched) | **0/30** |
| `info depth` lines emitted after the stop | **0** |
| latency from `setoption` to `bestmove` | 0.2–1.0 ms |

**Verdict: searched, not fabricated.** The reply is the completed-iteration move
at the last announced depth, byte-identical to what `stop` produces — so a client
that resizes mid-search gets a truthful answer, not the `root_candidates.front()`
fabrication that the EOF and drawn-root paths produce (§7 items 3a, 3ab). It
carries **no `info` line of its own**, so the only in-band record of what was
searched is the pre-stop PV; a harness must not expect one.

**Harness trap found while building this**, worth recording because it silently
eats the answer: the `bestmove` is emitted *during* the `setoption` command, not
after it. A client written as `send(setoption); send(isready); read_until(readyok)`
**discards the bestmove** and then reports "no bestmove after resize" — which is a
harness bug that looks exactly like an engine hang. My first ASan run failed this
way; `scripts/exp_asan.py` now uses `send()` and keeps the note inline.

---

## Verdict 3 — RSS across a resize: **no leak across 20 cycles; the allocation moves and the old block is freed**

16 → 256 → 16 × 20 in one process, RSS after an `isready` round-trip (so the
option is applied), `evidence/D_rss_cycles.json`:

```
round   RSS@large   RSS@small   HWM@large  HWM@small   VSZ@small
    0      287304       25156      287304     287304       28168
    1      287304       25156      287304     287304       28168
   ..      (identical through round 19 — one distinct pair in the whole run)
   19      287304       25156      287304     287304       28168
```

- **small RSS: 25,156 kB every round. delta over 20 cycles = 0 kB.**
- **large RSS: 287,304 kB every round. delta = 0 kB.**
- `VmHWM` never moves after round 0 → no hidden peak later in the run.
- Same 20 cycles **with a search between every transition**: small RSS
  25,164 → 26,720 kB in round 1 and then **identical for the remaining 19
  rounds**, delta 0 kB. The one step is the search's own allocations, not the
  resize.
- One-size bounds measured separately: a process that only ever sees Hash 16
  settles at **25,172 kB**; only ever Hash 256 at **270,912 kB**. The observed
  endpoints (25,156 / 287,304) match those bands.
- **The engine is still correct at the end**: after 20 cycles, `bench 11` =
  **312,866** and `startpos go depth 13` = 72,062 nodes / `e2e4`, in both arms.

**Verdict: freed, not leaked.** Twenty cycles are indistinguishable from one, on
every metric.

**But the peak is not free, and question 2's transient is real.** `resize`
allocates the new cluster array and only then move-assigns it over the old one
(`search.cpp:362-370`), so for one instant both tables are alive. Sampling RSS is
the wrong instrument for that window — a fresh large allocation is often backed
by untouched zero pages and near-zero RSS until first write — so the reading
below is **peak RSS above the settled post-resize RSS**, a high-water comparison
that a missed sample cannot fake. Same-size resize, table pre-filled by a depth-20
search, **7 repeats each**:

| Hash | peak above post-resize RSS, 7 repeats | table | verdict |
|---|---|---|---|
| 16 MB | 16,388 ×7 | 16,384 kB | exactly one table |
| 32 MB | 32,772 ×7 | 32,768 kB | exactly one table |
| 64 MB | 65,540 ×7 | 65,536 kB | exactly one table |
| 128 MB | 131,076 ×7 | 131,072 kB | exactly one table |
| 256 MB | 262,148 ×7 | 262,144 kB | exactly one table |

**The transient is one full table, at every size, 7 of 7, with no variance.** Not
a sampling artefact: the excess is 4 kB over the exact table size every time.

Repeated same-size resizes do not ratchet: `VmHWM` moves +1,696 kB in round 0 and
**0 kB** in rounds 1–7.

### And the transient changes the engine's memory requirement

The audit bisected the memory cliff at `ulimit -v`: "Hash 16 needs 60 MB (dies at
56), Hash 256 needs 300 MB (dies at 290)". If two tables must coexist, a
same-value resize needs about twice what one allocation does. Bisected to **1 MB**
per arm, with a third arm that does the same two searches but no resize
(`evidence/K2_cliff_bisect.json`):

| Hash | fresh (1 alloc) | warm, 2 searches, no resize | **after same-value resize** | delta | ratio |
|---|---|---|---|---|---|
| 16 | **60 MB** | 60 MB | 60 MB | **0** | 1.00 |
| 32 | 76 MB | 76 MB | 85 MB | +9 | 1.12 |
| 64 | 108 MB | 108 MB | 149 MB | +41 | 1.38 |
| 128 | 172 MB | 172 MB | **341 MB** | **+169** | **1.98** |
| 256 | **300 MB** | 300 MB | **597 MB** | **+297** | **1.99** |

Three things to read off it:

1. **The fresh arm reproduces the audit's published cliffs exactly** — 60 MB at
   Hash 16 and 300 MB at Hash 256, both bisected to the megabyte. The
   measurement agrees with the earlier one where they overlap.
2. **The middle arm is identical to fresh at every size**, so the extra memory is
   not "a second search happened" — it is the resize.
3. **At Hash ≥ 128 the requirement roughly doubles** (1.98×, 1.99×). At smaller
   sizes fixed overhead absorbs part of the second table, so the ratio is not 2.0
   across the range; the delta is reported as measured rather than fitted to a
   formula. The boundary is stable: at Hash 256, dies at 596 / survives at 597,
   3 of 3 repeats.

**This is the finding that reaches a match runner.** A runner at Hash 256 that
re-sends its option block between games needs **597 MB of address space, not
300** — and under a memory cap (a container limit, a `ulimit`, a shared box with
several engines) the process dies where the same configuration launched with a
fresh process would have lived.

---

## Verdict 4 — Resize after `ucinewgame` versus before: **no difference; both are fully cold, 0/30**

Isolated by comparing **order** with no warm-up search in the process, so only
the sequence differs:

| arm | vs fresh(256) |
|---|---|
| `setoption Hash 256` → `ucinewgame` → search | **0/30 differ** |
| `ucinewgame` → `setoption Hash 256` → search | **0/30 differ** |

And with a populated table before both:

| arm | vs fresh(256) |
|---|---|
| search → `setoption Hash 256` → `ucinewgame` → search | **0/30** |
| search → `ucinewgame` → search | **0/30** |

**Verdict: no difference, in either direction and with or without a warm start.**
`ucinewgame` wipes the table *and* the histories (`Searcher::clear()`,
`search.cpp:2679`), which dominates whatever the resize did first, so it masks
the resize completely. **This is why a well-formed runner is safe**: the usual
pattern "`ucinewgame`, then the option block, then `go`" is cold regardless.

*The null's second proof:* the same comparison at the same depth does report a
difference when the thing is present — `search → setoption Hash 256 → search`
(no `ucinewgame`) differs from fresh **30/30**. So the zero above is the
`ucinewgame`, not a blind comparison.

---

## Verdict 5 — Resizing to the same value: **a table clear, identical to `Clear Hash` — and it fires even on an empty table, where it costs nothing**

**Reproduction of the coordinator's table first** (Hash 32, depth 12, 3 repeats
each, fresh process each, position 0):

| arm | bestmove | nodes | repeats |
|---|---|---|---|
| COLD | e3f4 | **83,108** | 3/3 |
| WARM (nothing sent) | e3f4 | **29,349** | 3/3 |
| RESEND-HASH | e3f4 | **63,572** | 3/3 |
| CLEAR HASH | e3f4 | **63,572** | 3/3 |
| UCINEWGAME | e3f4 | **83,108** | 3/3 |

Confirmed: `RESEND-HASH` == `CLEAR HASH` byte-identically, and `UCINEWGAME` ==
`COLD`. (My absolute node counts differ from the coordinator's because the
position and depth differ; the *relations* reproduce exactly, which is what the
claim rests on.)

Extended to **30 positions at depth 18**, in both sizes:

| comparison | result |
|---|---|
| same-value 16 vs `Clear Hash` at 16 | **30/30 identical** |
| same-value 256 vs `Clear Hash` at 256 | **30/30 identical** |

Identical bestmove, nodes, score and depth on every position — so as a **cache
operation** a same-value resize is indistinguishable from `Clear Hash`.

**But it is not literally the same operation, and the difference is worth
stating precisely rather than rounding off.** In source they are different
functions, and the resize one is the *smaller* set:

```2673:2683:forge-combo29/src/search.cpp
void Searcher::clear_hash() {
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear_caches();   // + evaluator_.clear()
}

void Searcher::clear() {                                     // ucinewgame
    shared_.tt.clear();
    for (auto& worker : workers_) worker->clear();           // + ALL histories
}
```

`resize` calls **neither** — it allocates a new array and drops the old one, so it
clears the *table* and nothing else. `Clear Hash` additionally empties the
evaluator's pawn cache (`clear_caches()` → `evaluator_.clear()`,
`search.hpp:452`). **The two measure identical 30/30 anyway, which is itself a
result: the evaluator pawn cache is not load-bearing at these depths and
positions.** The honest statement of the verdict is therefore "**equal to
`Clear Hash` as measured**, while clearing strictly less" — not "the same call".

### Does it wipe an already-empty table? Yes — and it changes nothing

12 positions, depth 12, Hash 32, five cold arms from a fresh process each
(`evidence/L_empty_table.json`):

| comparison | result |
|---|---|
| cold `Hash 32; Hash 32` vs cold `Hash 32` | **12/12 identical** |
| cold 3× `Hash 32` vs cold `Hash 32` | **12/12 identical** |
| never send Hash at all (default 32) vs cold `Hash 32` | **12/12 identical** |
| **POSITIVE: warm + same-value re-send vs warm** | **12/12 differ** |

**Verdict: the wipe executes unconditionally, but on an empty table it is
unobservable.** `resize` has no early return, so it always allocates, always
zeroes the generation and always bumps the epoch — but a table that was already
empty has nothing to lose, so the following search is bit-identical. This is why
the mechanism shows no symptom until a table has contents.

The positive control is what makes that null admissible: on the *same* 12
positions, the same re-send after a search differs **12/12**. So the instrument
sees the wipe when there is something to wipe.

### What it costs a runner

`evidence/I_runner_cost.json`, 30 positions, depth 18, Hash 32:

| pattern | total nodes | vs clean |
|---|---|---|
| **I1** first search of a game, options re-sent around `ucinewgame` | 26,555,951 | **identical, 30/30** |
| **I2** re-send between *moves* (pathological but legal) | 21,120,273 | 8,217,743 clean → **+157%**, 0/30 identical |

**I1 predicts zero and measures zero**: `ucinewgame` masks the wipe, so a runner
that re-sends options at game start pays nothing. **I2 costs 2.6× the nodes**,
because there is a real table to destroy and no `ucinewgame` to mask it.

Between **games**, where a runner without `ucinewgame` actually lands
(`evidence/J_between_games.json`, 30 position pairs):

| comparison | result |
|---|---|
| `search → ucinewgame → search` vs fresh | **0/30** (cold, as expected) |
| `search → same-value resize → search` vs fresh | **30/30 differ, 4 moves changed** |
| `search → Clear Hash → search` vs fresh | **30/30 differ, 4 moves** |
| same-value resize vs `Clear Hash` | **30/30 identical** |
| total nodes, resize vs fresh | 25,185,783 vs 27,312,210 → **−7.8%** |

Note the sign: the wiped state **searches fewer nodes** for the same depth
(−7.8%) because it has lost the hash move and the cutoffs that made the warm
search cheap. **A node-count or "nodes per second" metric will read that as an
improvement.** It is not — it is the cost of re-deriving what was thrown away,
and the answers differ in 4 of 30 positions.

**The two node deltas have opposite signs, and that is a consistency check
rather than a contradiction** — it is worth stating because a reader meeting
`+157%` and `−7.8%` in one document will otherwise suspect one of them:

- **I2 is measured against the WARM arm** (same position searched twice, table
  intact). The wipe destroys a table that was doing real work, so the resized
  arm must re-derive it: **+157%**.
- **J is measured against a FRESH process** (different position, table empty in
  both arms). Both arms start with no table — the resize arm's table was emptied,
  and the probe above puts that at 0/30 warm in both directions — so the wipe
  costs it nothing. But the resized process still has the **warm histories**,
  which the fresh process does not: **−7.8%**.

Both readings follow from the same two facts established independently — *the
table is emptied* (the `go wtime 0` probe: 0/30 warm) and *the histories survive*
(E1 zero with E2 non-zero, and E4 back to zero when `ucinewgame` clears them). A
resize is therefore a third state: **cold table, warm histories.** Against cold
it uses fewer nodes (−7.8%); against warm it uses many more (+157%). Neither
comparison alone describes it.

**One caveat on the −7.8%, stated rather than glossed:** fewer nodes is not the
same as better play, and the two arms disagree on the move in 4 of 30 positions.
The measurement is "the search does less work to reach the same depth", not "the
resized search is stronger". With the table cold in both arms and the table
proven empty, histories are the only difference between them — but *which*
history table produces the reduction was not isolated, and calling it a gain
would be reading a node count as a strength claim.

---

## Memory: the RSS curve

**Repeated 16 → 256 → 16 in one process, 20 cycles, nothing searched between
transitions** (`evidence/D_rss_cycles.json`):

```
RSS (kB)
300000 |  #################### 287,304 at Hash 256, all 20 rounds
       |
 25000 |  ####################  25,156 at Hash 16,  all 20 rounds
       +------------------------------------------------
          round 0                   round 19

one distinct (large, small) pair in 20 rounds.
VmHWM flat after round 0.   VmSize 28,168 kB at Hash 16 throughout.
```

With a search between every transition the same shape holds, one round later
(`25,164 → 26,720` and then flat for 19 rounds; large `287,312 → 288,868` and
flat). **No leak, no ratchet, no drift.**

**Single resize transient (same size, filled table, 7 repeats each):** the peak
is **one full table** above the settled RSS at every size, 16 → 256 MB, with 4 kB
of excess over the exact size every time and zero variance across repeats.

**Memory requirement (bisected to 1 MB):**

| Hash | fresh | **after same-value resize** | delta |
|---|---|---|---|
| 16 | 60 MB | 60 MB | 0 |
| 32 | 76 MB | 85 MB | +9 |
| 64 | 108 MB | 149 MB | +41 |
| 128 | 172 MB | **341 MB** | +169 |
| 256 | 300 MB | **597 MB** | +297 |

---

## What should a match runner do

**Omit the `Hash` line when the value is unchanged.** The number: at Hash 32,
depth 18, re-sending the option block around `ucinewgame` costs **0 nodes
(I1: 26,555,951 vs 26,555,951, identical on 30/30)** — so the recommendation is
*not* driven by the game-start cost, which is zero. It is driven by the two costs
that are not zero:

1. **Memory.** A same-value resize at Hash 256 needs **597 MB where one
   allocation needs 300** — 1.99× the address space, bisected to the megabyte and
   stable across 3 repeats. Under any cap near the audit's published cliff, a
   runner that re-sends its options **dies where the same configuration launched
   fresh would live.** No node count shows this; the process simply disappears.
2. **Any re-send that does not sit next to a `ucinewgame`.** Between games
   without `ucinewgame`, the resize costs **−7.8% nodes and 4 changed bestmoves
   in 30 positions**; between *moves*, **+157% nodes and 0/30 identical**. Both
   are wrong answers in the same way — a third cache state that is neither cold
   nor warm.

So, in order of preference:

| runner behaviour | cost | verdict |
|---|---|---|
| send `Hash` only when it changes | none | **preferred** |
| send options, then `ucinewgame`, then `go` | 0 nodes, but 2× address space at resize time | acceptable if memory headroom ≥ 2× Hash |
| re-send `Hash` between *moves* | +157% nodes, answers differ | **do not** |

**Do not "accept the wipe"** as a harmless equal-cost path. The wipe itself is
cheap *when `ucinewgame` follows it* and expensive otherwise, and the moment it
is expensive the symptom is either a changed best move or a dead process.

### The engine-side fix this implies

`TranspositionTable::resize` (`search.cpp:362-370`) has no size comparison. A
guard at the top — `if (mb == current_size_mb_ && clusters_) return;` — removes
the wipe, the 2× transient and the doubled memory requirement in one line, and
makes a same-value `setoption` the no-op every GUI already assumes it is. That
also makes `setoption Hash N` (unchanged) stop being a third reset path, leaving
`Clear Hash` and `ucinewgame` as the only two. **Not patched in this seat** — this
is an audit, and the recommendation is stated, not applied.

---

## Sanitizers

ASan + UBSan over nine resize lifecycle blocks (`evidence/G_asan.json`), engine
`FORGE_PORTABLE=ON` so the kernel does not mask the paths:

`same_value_cold`, `same_value_warm` (8 cycles), `up_down_cycles` (10×),
`extremes` (1 MB and 2048 MB), `during_search` (5×), `between_positions`,
`around_newgame`, `multipv_resize`, `quit_during_search` — **all alive at the end,
zero diagnostics on stderr**, and the engine answers a real search after each.

**Both controls fired, which is what makes the run admissible:**

1. a missing binary is detected as a failure — proves the harness can fail;
2. **a canary binary (`scripts/asan_canary.cpp`) that deliberately overflows a
   heap buffer on `setoption name Hash` produces an `AddressSanitizer` diagnostic
   that the detector reports** — proves the *detector* fires on a real report,
   not just on a dead process.

The second control was added because the first is not enough: a missing-binary
check proves an exception can be raised, not that a sanitizer line can be
recognised. **My first ASan probe failed to prove anything** — an optimised-away
`memset` produced no report and the run looked clean. It was the canary, not the
reading of the code, that showed the difference.

Note: `during_search` initially reported a failure that was **my harness, not the
engine** — `setoption()` calls `sync()`, which swallows the `bestmove` emitted
during the `setoption`. Fixed, kept as a comment, and reported in Verdict 2.

---

## Scope, and what is not established

- **The mechanism behind the history residue is not identified.** The
  decomposition (E1 zero, E2 non-zero, E4 zero) proves it is *histories*, and
  `Searcher::clear()` vs `clear_hash()` names the code path that clears them, but
  *which* history table carries the effect is not measured — that needs a build
  that clears them one at a time.
- **The 2× memory requirement is measured at 16/32/64/128/256 MB only**, and the
  delta is not a clean 2× below 128 MB. The curve is reported as measured rather
  than fitted; sizes above 2048 (unreachable, the advertised max) are untested.
- **The `-7.8%` node figure is a depth-18, 30-position sample**, not a match
  result, and it is *fewer nodes for a different answer*, not an efficiency.
- **`Threads > 1` is untested here**, as everywhere else in the audit. Every
  number in this document is at the default of 1.
- **The wall-clock numbers are not relied on.** The machine is shared; node
  counts at a fixed depth are the measure throughout.

---

## Files

```
scripts/pins.py              the eleven honesty pins
scripts/engine_client.py     UCI client (os.read, no EOF to a live search)
scripts/corpus.py            position selection, fixed before measurement
scripts/exp_resize_state.py  Q1/Q4/Q5 — fresh, resize, same-size, Clear Hash, order, controls
scripts/exp_table_probe.py   Q1 table half — the `go wtime 0` binary probe
scripts/exp_small_window.py  the sharp test: the window where the sizes agree
scripts/exp_midsearch.py     Q2 — bestmove after a mid-search setoption
scripts/exp_rss.py           Q3 — 20 resize cycles, RSS/HWM/VSZ
scripts/exp_samevalue.py     same-value: empty table, transient
scripts/exp_transient.py     the transient at 5 sizes, 7 repeats each
scripts/exp_empty_table.py   item 1 at width, with a positive control
scripts/exp_runner_cost.py   the number behind the recommendation
scripts/exp_between_games.py the between-games form
scripts/exp_cliff.py         the memory cliff per arm
scripts/exp_cliff_bisect.py  the cliff bisected to 1 MB
scripts/exp_asan.py          nine lifecycle blocks + two controls
scripts/asan_canary.cpp      the positive control for the sanitizer detector
evidence/*.json[l]           every number above, raw
```
