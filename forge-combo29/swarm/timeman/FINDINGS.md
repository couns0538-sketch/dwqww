# FINDINGS — time-manager accounting (`swarm/timeman`)

Audit base: **`6b98f217`** — a divergent commit, *not* an ancestor of `main`. Branch
`swarm/timeman` branches from it so every number here is against the same tree the rest of
the audit uses.

Build: `-DCMAKE_CXX_COMPILER=/usr/bin/g++` with `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`
(the `/usr/bin/c++` clang-18 header path is broken). Build takes ~6 s.

**Honesty pins on this build, checked before any measurement** (all four, `scripts/check_pins.sh`):
312,866 / 862,329 / 3,024,920 / perft 5 **4,865,609**. Net-off and the two higher depths also
match. The pins were re-checked on the *patched* build used for item 2 (§2 below).

---

## 0. Two inherited claims this seat had to correct

Both are corrections, not new findings, and they are stated first because a reader who trusts
them will mis-read every plan in this file.

### 0.1 `movestogo 0` is NOT sudden death in this source tree

The inherited statement is that `clock_plan.hpp:37` branching on `moves_to_go > 0` makes
`movestogo 0` mean sudden death, with `movestogo 0` giving 482 ms where omitting the token gave
57 ms — "8.4× the plan".

**That reads the pre-clamp value.** `src/uci.cpp:117` is

```cpp
else if (token == "movestogo") limits.moves_to_go = std::max(1, read_int());
```

so `0` and `-1` are rewritten to `1` *before* `clock_plan.hpp` ever sees them. Measured with the
engine's own header (`scripts/plan_table.cpp` links `clock_plan.hpp` and applies the real
`parse_limits` transform), at a 2000 ms clock, Move Overhead 10:

| token | parsed | soft | hard | behaviour |
|---|---|---|---|---|
| `movestogo 0` | 1 | **995** | 1592 | the `movestogo 1` plan |
| `movestogo 1` | 1 | **995** | 1592 | same |
| `movestogo -1` | 1 | **995** | 1592 | same |
| `movestogo 2` | 2 | 663 | 1592 | |
| `movestogo 50` | 50 | 39 | 156 | |
| `movestogo 100` | 100 | 39 | 156 | identical to 50 — the clamp is real |
| *(absent)* | 0 | **90** | 450 | the true sudden-death plan |

And the measurement follows the plan: `go wtime 2000 btime 2000 movestogo 0` returned in
**735 ms**, `movestogo -1` in **713 ms**, `movestogo 1` in **892 ms** — all one regime — while
omitting the token returned in **122 ms**. So `movestogo 0` is *not* sudden death; it is the
**`movestogo 1` branch**, which is the most aggressive movestogo plan there is (soft 995 ms, 11×
the sudden-death plan). The direction of the trap is unchanged — a value that looks like "ignore
me" buys the *largest* plan — but the mechanism is the `max(1, …)` clamp, not the `> 0` test.

**The `> 50 → 50` clamp does hold**, and it is exactly as reported: `51`, `100` and `200` are
indistinguishable in both plan and wall time.

### 0.2 "Hard limit is 60% of soft" is not what this planner does

`clock_plan.hpp:40` is `hard = std::min(available * hard_percent / 100, soft * hard_soft_multiple)`
with `TmHardPercent = 60` and `TmHardSoftMultiple = 5`. In sudden death `soft = available/22`, so
the second term is ≈ `0.227 × available`, which is **below** `0.6 × available` at every clock from
2000 ms down to 60 ms. So **the `5 × soft` term binds and hard is five times the soft plan**, not
0.6× of it:

| clock | available | soft | hard | 0.6×avail | 5×soft | which binds |
|---|---|---|---|---|---|---|
| 2000 | 1990 | 90 | 450 | 1194 | 450 | **5×soft** |
| 500 | 490 | 22 | 110 | 294 | 110 | **5×soft** |
| 111 | 101 | 4 | 20 | 60 | 20 | **5×soft** |
| 60 | 50 | 2 | 10 | 30 | 10 | **5×soft** |

The 60% percentage binds only where `available` is small relative to soft, which sudden death never
reaches. A reader who takes "hard = 60% of soft" as a rule will predict a hard limit 55% too high at
a 2000 ms clock.

---

## 1. Increment accumulation over real games

Four controls, **50 games requested each**: 200+0 (sudden death at a short clock), 1000+100,
3000+200, and 10000+1000. Self-play, book off, Threads 1, 400-ply cap. Legality is checked every
move against python-chess, never against the engine.

**How the clock is charged, and why this is stated rather than glossed.** Two bases are available
and neither is simply "the truth":

- the engine's own `time <elapsed>` field, read from the **last `info` line**;
- harness wall time, measured from just before the `go` write to the `bestmove` read.

The first excludes the harness's round trip (p50 **0.8–1.0 ms** here) but **understates real spend**
whenever the hard limit aborts an iteration, because the last completed iteration's `time` can be
far behind the search's actual end — measured directly: at `movetime 2000` the last `info` line
reports **453–1988 ms** while the call takes **1990–1991 ms**. The second includes the round trip and
so overstates by ~1 ms on typical moves, with a heavy tail (p99 335 ms at 1000+100, 898 ms at
3000+200) that is mostly *real search time in an aborted iteration*, not scheduling.

**So the headline counts below are reported under BOTH bases**, and the conclusions are the same:

| control | over hard (engine) | over hard (wall) | >5 ms over (wall) | **flags (engine)** | **flags (wall)** | util max (engine / wall) |
|---|---|---|---|---|---|---|
| 200+0 | 0 | 99 | 1 | **0** | **0** | 0.200 / 0.533 |
| 1000+100 | 0 | 157 | 0 | **0** | **0** | 0.592 / 0.595 |
| 3000+200 | 1 | 201 | 0 | **0** | **0** | 0.596 / 0.597 |

The wall column counts more "over hard" only because a 1 ms round trip is a large fraction of a
small plan; **not one of those overruns exceeds 5 ms** except a single 20 ms-wall/5 ms-plan move at
200+0, and **zero moves flag under either base**. The per-move table further down uses engine time;
the forfeit conclusion does not depend on that choice.

**Controls completed: 150 games / 19,630 plies** (200+0: 50 / 7,172; 1000+100: 50 / 5,769;
3000+200: 50 / 6,689). The 10000+1000 set was **still running** when this file was written and its
numbers are therefore **absent, not zero** — say so rather than reading a missing row as a clean
one.

| control | games | plies | **forfeits** | hangs | illegal | over hard plan | min final clock |
|---|---|---|---|---|---|---|---|
| 200+0 | 50 | 7,172 | **0** | 0 | 0 | 0 | 22 ms |
| 1000+100 | 50 | 5,769 | **0** | 0 | 0 | 0 | 277 ms |
| 3000+200 | 50 | 6,689 | **0** | 0 | 0 | **1** (see below) | 604 ms |
| 10000+1000 | — | — | *not run* | — | — | — | — |

**0 forfeits in 19,630 moves.** Every game ended by threefold (108), a completed game (41) or the
fifty-move rule (1) — none by a clock. `clock_mapping_errors` is **0** in all 150 games, so the
self-check added after §6's fault confirms the mover's clock really was the clock every move was
planned against.

### The single move that exceeded its hard plan

Exactly one move in 19,630 went over its hard limit, and it is reported rather than smoothed:

| control | clock | charged | plan soft/hard | ratio | harness tail |
|---|---|---|---|---|---|
| 3000+200, game 22, ply 39 | 1,144 ms | **681 ms** | 201 / **680** | **1.0015×** | 0.52 ms |

**+1 ms on a 680 ms plan.** The hard limit is polled on a 1024-node mask
(`search.cpp:1419,1561`) and compared with `>=`, so a stop lands on the first polled node at or past
the deadline; 1 ms is one poll interval's worth at this node rate, not an unbounded overrun. It is
also **not a clock risk**: the move was allowed 1,144 ms and used 681. Reported as an exact
exception so the "0 over hard" reading above is not taken as a claim of zero.

### Distribution of per-move wall time against the planner's prediction

`charged − soft` is the direct analogue of the established "+2.1 ms reproduces all 3,071 moves"
result, and **it does not reproduce on any control here**:

| control | charged p50 / p90 / p99 / max | `charged − soft` p50 / p95 / max | within ±2 ms |
|---|---|---|---|
| 200+0 | 1 / 6.9 / 16 / 29 ms | −1.0 / +4.0 / +23 ms | **6,061 of 7,172 (84.5%)** |
| 1000+100 | 81 / 192 / 369 / 604 ms | −25.0 / +137.6 / +480 ms | **126 of 5,769 (2.2%)** |
| 3000+200 | 172 / 400 / 804 / 1,356 ms | −61.0 / +279 / +1,062 ms | **71 of 6,689 (1.1%)** |

**So the planner formula is a bound, not a prediction, at any control above the floor.** The 200+0
agreement is an artefact of scale, and the number that shows it is this: **the median soft plan at
200+0 is 1 ms**, 87% of its moves have a plan of ≤ 5 ms, and none exceeds 8 ms. A ±2 ms tolerance
on a 1 ms plan is larger than the plan itself, so "84.5% within ±2 ms" there measures the
granularity of a millisecond clock, not accuracy. At 1000+100 and 3000+200 the median move uses
**73–76% of its soft plan** and the tail extends to **4.9–5.0× soft**, where the hard limit binds
(`charged/hard` max is 1.000 and 1.001). The established 2.1 ms figure came from a **1000+100
control with 3,071 plies**; this seat's 1000+100 control has 5,769 plies and reproduces the
*containment* (no move over hard, bar one) but **not** the ±2 ms reproduction. **That inherited
figure should be read as "the plan was never exceeded", not "wall time equals the plan".**

Two ratios make the shape concrete, and they are the ones to quote:

| control | `charged/hard` p50 | p95 | max | utilisation (`charged/clock`) p50 | p95 | max |
|---|---|---|---|---|---|---|
| 200+0 | 0.080 | 0.450 | 1.000 | 0.014 | 0.077 | 0.200 |
| 1000+100 | 0.202 | 0.634 | 1.000 | 0.118 | 0.373 | **0.592** |
| 3000+200 | 0.178 | 0.587 | 1.001 | 0.102 | 0.345 | **0.596** |

**Utilisation peaks at 0.592 and 0.596**, i.e. the worst move in 19,630 spent **59.6% of its
remaining clock** against a hard plan of `0.6 × available`. That matches the recorded max move-time
÷ clock of 0.5937 on the old 1000+100 run, and it is the single most reassuring number in this
section: the hard limit is what actually binds, and it binds just under 60%.

### The two controls behave qualitatively differently

Median `clock_before` by quintile of ply, per control — this is the shape, not an inference:

| control | 1st | 2nd | 3rd | 4th | 5th | final clock (median w/b) |
|---|---|---|---|---|---|---|
| 200+0 | 152 | 84 | 53 | 48 | 40 | 43 / 46 (min 22) |
| 1000+100 | 926 | 705 | 677 | 677 | 699 | 682 / 730 (min 277) |
| 3000+200 | 2,609 | 1,858 | 1,551 | 1,472 | 1,591 | 1,851 / 1,720 (min 604) |

- **200+0 drains, then flattens just above the overhead.** 200 → 152 → 84 → 53 → 40, and it is still
  drifting down at the end because the increment is zero and something must pay for each move. The
  flattening is the plan shrinking with the clock: at 40 ms the plan is 1/5, so a move costs ~1–5 ms
  and the drain is nearly nil. **It never reaches zero and 50 of 50 games finished with no forfeit**
  — this is the "clock can always be spent" regime, and it is why the floor (§4.3) does not
  apply to a zero-increment game: the engine keeps answering, at a **median depth of 7 over the
  whole game and depth 4 once the clock is below 60 ms** (2,641 of those moves at exactly depth 4),
  rather than flagging.
- **1000+100 and 3000+200 hold station.** Both fall to a plateau and stay there — 677–699 at
  1000+100 and 1,472–1,591 at 3000+200 — with median charge 81 and 172 ms against 100 and 200 ms
  increments, so **spend ≈ increment and the clock neither grows nor drains**. That is the
  equilibrium §4.3 derives, sitting far above the 111 ms floor because real play uses ~10–20% of the
  clock rather than the whole hard limit.

---

## 2. `movestogo` meeting the fallback clock — the recorded gap, now measured

Trap 19e records the repair: `parse_limits` keeps `wtime`/`btime` separately and resolves the budget
as **the mover's clock if given, the opponent's otherwise**. It also records, explicitly, that
"**the `movestogo`-plus-fallback interaction is unmeasured**". This section closes that.

**The audit base does not contain the repair.** `6b98f217:src/uci.cpp` still assigns
`limits.time_ms` only when the side to move owns the clock field, so on the base an
opponent-clock command never reaches the planner at all. Item 2 therefore needs two builds:

- **base** — `6b98f217` as-is;
- **patched** — `6b98f217` + `swarm/65/patches/trap1-clock-gate-both-clocks.patch`, applied
  cleanly, rebuilt, **all four pins re-verified on the rebuilt binary**.

> ### RULE: a pin check on a build whose compile failed checks the previous binary
>
> **Pins passing on a stale executable are indistinguishable from pins passing on a real one.**
> This fired here, and is written up as a rule because the failure mode is general and silent.
>
> The sequence: a worktree was copied that already contained `build/forge` from the *unpatched*
> tree; `cmake --build` returned **rc=1**; `scripts/check_pins.sh` printed **`PINS MATCH combo29`**
> with all four pins correct. Every indication said "the patched build is good". The binary was in
> fact **byte-identical to the unpatched build** — `cmp` said so.
>
> The pin script's correctness is not the issue: it answered the question it was asked ("do these
> pins reproduce?") about an object that was not the patched binary. A pin count cannot
> distinguish "the patch changed nothing observable" from "the patch was never compiled", and
> those two conclusions are opposites.
>
> **Required practice for any build-then-pin script**, cheapest first:
> 1. **`rm -rf` the build directory** before configuring, or build in a fresh directory;
> 2. **assert the compiler actually re-linked** — check the build's return code *and* that the
>    binary's mtime/hash changed;
> 3. **`cmp` the new binary against the previous one** when the patch is supposed to change
>    behaviour; identical output means the build did not happen, not that the patch is neutral.
>
> Note the compounding factor: a copied worktree can carry a `build/` directory whose binary
> already passes the pins, which is exactly the state that makes the check look strongest. Copying
> a worktree for a second arm is where this trap lives, and copying is what an A/B measurement
> encourages.

### Results

White to move, 2000 ms clock, `OwnBook false` so the book cannot short-circuit before the time
manager (trap 19e's own first-attempt error). `plan` is the soft/hard from `plan_table.cpp`.

| arm | command | base | patched | plan soft/hard |
|---|---|---|---|---|
| A own clock + mtg 1 | `wtime 2000 btime 2000 movestogo 1` | 892 ms | 865 ms | 995 / 1592 |
| A own clock + mtg 2 | `… movestogo 2` | 379 ms | 751 ms | 663 / 1592 |
| A own clock + mtg 20 | `… movestogo 20` | 82 ms | 66 ms | 94 / 376 |
| A own clock + mtg 50 | `… movestogo 50` | 77 ms | 69 ms | 39 / 156 |
| A own clock + mtg 100 | `… movestogo 100` | 35 ms | 67 ms | 39 / 156 |
| **B opponent clock + mtg 20** | `btime 2000 movestogo 20` | **12,000 ms — no answer** | **72 ms** | 94 / 376 |
| **B opponent clock + mtg 100** | `btime 2000 movestogo 100` | **12,000 ms — no answer** | **74 ms** | 39 / 156 |
| **B opponent clock + mtg 0** | `btime 2000 movestogo 0` | **12,000 ms — no answer** | **794 ms** | 995 / 1592 |
| **B opponent clock + mtg −1** | `btime 2000 movestogo -1` | **12,000 ms — no answer** | **730 ms** | 995 / 1592 |
| B' Black to move, only `wtime` + mtg 20 | `wtime 2000 movestogo 20` | **12,000 ms — no answer** | **101 ms** | 94 / 376 |
| C fallback, no movestogo | `btime 2000` | **12,000 ms — no answer** | **67 ms** | 90 / 450 |

**Every wall time in this table is a single run, and one row is known to be noise.** The own-clock
`movestogo 2` row reads 379 ms on base against 751 ms patched — a 2× gap on a command whose budget
cannot depend on the fallback patch, because White's own clock is given so `parse_limits` takes the
first branch on **both** builds. That row was re-measured with **12 interleaved runs per build in
ABBA order** (`scripts/p12_ownclock_mtg_repeat.py`):

| build | min | median | max | mean | sd | range |
|---|---|---|---|---|---|---|
| base | 367 | **489.5** | 1349 | 622.2 | 359.9 | 367–1349 ms |
| patched | 204 | **402.5** | 1359 | 526.2 | 301.4 | 204–1359 ms |

**The ranges overlap almost completely and the spread inside each build is larger than the
difference between builds**, so the 379/751 pair was load noise on a shared 4-core box, not an
effect of the patch. The distribution is bimodal — values cluster near 370, 490, 720 and 1350 ms,
which are successive completed-iteration costs, exactly the step function §3 describes — so a
single sample lands on any of four plateaus and two single samples can differ by 3× by chance. A
fixed-depth identity control on the same position agrees between builds exactly
(**depth 12: `e1g1`, 113,145 nodes on both**), confirming the two binaries are the same search and
that only timing differs.

**So the patch's invariant holds: an own-clock caller is not moved by it.** The 2.1 ms
"reproduces the plan" style of claim cannot be made from single runs on this machine at all, and
none of the wall-time columns above should be read as precise; the **plan** columns and the
**regime separations** are exact and are what the three conclusions rest on. This is also why §1
charges the engine's own `time` field and reports distributions rather than single runs.

**What the gap measurement establishes, in the three parts asked for:**

1. **The plan uses the fallback clock's value.** Arm B at `movestogo 20` plans 94/376 — computed
   from 2000 ms, the *opponent's* clock — and returns in 72 ms, against 82 ms for the own-clock arm
   on the base. The budget is the fallback number, not a default.
2. **The planner takes the `movestogo` branch, not the sudden-death branch.** Compare arm B
   *with* `movestogo 20` (72 ms, plan 94/376) against arm C, the same fallback **without**
   `movestogo` (67 ms, plan 90/450). Those are close in wall time but they are different plans, and
   the difference is visible at a movestogo far from the sudden-death plan: `movestogo 1` on the
   fallback plans **995/1592** and returns in 745 ms, while the fallback with no `movestogo` plans
   90/450 and returns in 67 ms — an **11× plan difference**, the same ratio the own-clock branch
   shows. So `movestogo` reaches the planner intact when the clock came from the opponent.
3. **The clamp still applies on the fallback path.** `movestogo 50`, `51`, `100` and `200` all plan
   **39/156** and return in 67–75 ms; `movestogo 49` plans 39/156 as well. `movestogo 0` and `-1`
   both plan 995/1592 and return in ~790/730 ms. So on the fallback path both clamps behave exactly
   as on the own-clock path: `0`/`-1` → `1` via `max(1, …)`, and `> 50` → `50`.

**What this does NOT change.** The fallback patch itself is not audited for correctness here; it is
the recorded repair from trap 19e and this seat only uses it. As the repeat analysis above shows,
the individual millisecond values in a single run are not trustworthy on this machine — the same
plan appears at 35 ms and 67 ms — so the claims above rest on **plan values and regime
separation**, which are exact, not on the wall times, which are not.

---

## 3. `movetime` accuracy — floor and ceiling, not a mean

**A mean is the wrong statistic here and it is worth saying why before quoting one.** A clock move
costs its last completed iteration, so wall time is a step function of the request: at `movetime
100` the engine either finishes the iteration inside 90 ms or overruns. Averaging ratios across
10/50/100 ms mixes three different regimes and an average would be dominated by whichever regime
the sample sat in. So each request is reported as a **floor** (the fastest observed), a **median**,
and a **ceiling** (the slowest observed), each as an absolute time *and* a ratio.

The limit the engine actually arms is `hard = max(1, movetime − MoveOverhead)` with `soft = hard`
(`src/search.cpp:2192-2193`) — the movetime path is *not* the clock path, and trap 18 says so. The
measurement confirms that arithmetic exactly.

15 repetitions × 4 positions (opening, midgame, endgame, bare K+R), Threads 1, book off,
`movetime` only. Aggregate (floor = min over positions, ceiling = max over positions):

| requested | armed limit | **floor** | **median** | **ceiling** | floor ×req | ceiling ×req |
|---|---|---|---|---|---|---|
| 10 ms | 1 ms | **1.10 ms** | 1.44 ms | **1.89 ms** | 0.110× | 0.189× |
| 50 ms | 40 ms | **40.28 ms** | 40.62 ms | **41.12 ms** | 0.806× | 0.822× |
| 100 ms | 90 ms | **90.28 ms** | 90.73 ms | **91.40 ms** | 0.903× | 0.914× |
| 500 ms | 490 ms | **490.35 ms** | 490.82 ms | **491.15 ms** | 0.981× | 0.982× |
| 2000 ms | 1990 ms | **1990.29 ms** | 1990.76 ms | **1991.17 ms** | 0.995× | 0.996× |

Three things follow, and the third is the one a mean would have hidden:

1. **The ratio is not stable — it is a predictable function of the request.** The ceiling is
   `armed_limit + 1.4 ms` at every request from 50 ms to 2000 ms. So overshoot is a **fixed ~1–1.5 ms
   constant**, not a proportional error, and the ratio therefore converges to 1.0 as the request
   grows. Reporting a single "movetime is accurate to 90%" would be wrong at 2000 ms (99.5%) and
   wrong at 50 ms (82%).
2. **There is a floor and it is the overhead, not the search.** At 2000 ms the engine returns at
   1990 ms, i.e. `requested − 10`: it never uses the last 10 ms. That is `MoveOverhead`
   subtracted on the movetime path, confirmed to the millisecond.
3. **There is a second, lower floor that is a process property.** `movetime 10` returns in
   **1.10–1.89 ms** — because `max(1, 10 − 10) = 1` ms, and 1 ms is not achievable as a *search
   duration*; what is measured is the round trip of a search that is told to stop immediately. **So
   the floor at 10 ms is not the engine being fast, it is the harness's own round-trip cost**, and a
   user asking for `movetime 10` gets roughly 1–2 ms of thinking, not 10. Both floors are
   real and neither is an error in the engine: one is documented arithmetic, one is the cost of
   answering at all.

No request timed out (0 of 300).

**One caveat this table cannot carry on its own, and it is worth stating here rather than only in
§1.** These figures are **wall** time, because that is what a caller experiences. The engine's own
`time` field on the last `info` line is *not* the same number: measured on one position at 12
repetitions, the last `info` line reports **453–1988 ms at `movetime 2000`** while the call takes
**1990–1991 ms**, because the final iteration is cut short and its `time` never gets printed. So the
2000 ms row above means "the call returns at 1990 ms", **not** "the engine thinks for 1990 ms and
reports so". Any reader comparing these numbers against an engine's self-reported time will find a
large discrepancy that is not a defect in either.

---

## 4. Sudden death versus increment, and clocks below the floor

All rows: 9 repetitions, Threads 1, book off. **The med/max figures are the engine's own `time`
field.** An earlier draft of this table printed **wall** times in the same columns as engine-derived
over-hard counts, and that mismatch alone made one cell (500 / inc 200) read `max 295.1` against a
294 ms hard plan while its engine maximum was **254 ms** — a scheduling tail, not an overshoot. The
distinction matters because the wall tail on this 4-core box reaches hundreds of milliseconds
(§6). `plan` is soft/hard.

### 4.1 Sudden death vs increment at short clocks

Engine time, median / max:

| clock | inc 0 (SD) | inc 50 | inc 100 | inc 200 |
|---|---|---|---|---|
| 200 | plan 8/40, 10 / 18 | 45/114, 40 / 68 | 83/114, 47 / 76 | 114/114, 66 / 104 |
| 500 | 22/110, 19 / 43 | 59/294, 58 / 126 | 97/294, 83 / 146 | 172/294, 147 / 254 |
| 1000 | 45/225, 60 / 128 | 82/410, 69 / 210 | 120/594, 106 / 271 | 195/594, 129 / 410 |
| 2000 | 90/450, 71 / 207 | 127/635, 109 / 261 | 165/825, 138 / 226 | 240/1194, 293 / 1025 |

**Not one of 144 runs exceeded its hard plan, and none exceeded the clock.** The increment changes
the plan in exactly the way `clock_plan.hpp` says: soft rises by `inc × 0.75` until the hard limit
clamps it. At 200 ms the three increment rows all converge on hard = 114 — the same
`0.6 × (200−10) = 114` ceiling the report records — so **at a short clock an increment buys plan
only until `0.6×available` binds, and past that it buys nothing.**

### 4.2 The 111 ms floor, and what happens below it

| clock | plan soft/hard | reserve empty | engine median | engine max | wall max | answered | over clock |
|---|---|---|---|---|---|---|---|
| 150 | 6/30 | no | 4 | 18 | 18.7 | 9/9 | 0/9 |
| **111** | 4/20 | no | 3 | 6 | 21.2 | 9/9 | 0/9 |
| 110 | 4/20 | no | 3 | 6 | 20.7 | 9/9 | 0/9 |
| 100 | 4/20 | no | 3 | 7 | 20.6 | 9/9 | 0/9 |
| 60 | 2/10 | no | 2 | 9 | 9.6 | 9/9 | 0/9 |
| 40 | 1/5 | no | 0 | 1 | 1.7 | 9/9 | 0/9 |
| 20 | 1/1 | no | 0 | 1 | 1.5 | 9/9 | 0/9 |
| 11 | 1/1 | no | 0 | 1 | 1.4 | 9/9 | 0/9 |
| **10** | 0/0 | **yes** | 0 | 0 | 1.1 | 9/9 | 0/9 |
| 5 | 0/0 | yes | 0 | 0 | 1.2 | 9/9 | 0/9 |
| **1** | 0/0 | yes | 0 | — | 1.2 | 9/9 | **0/9 (see below)** |

The `wall max` column is kept deliberately: at these clocks the engine's own search time is **0–9
ms** while the round trip reaches **21 ms**, so the harness tail is the whole measurement. Charging
wall time here would report an "overrun" on every row.

**The 1 ms row needs its own note, because the first version of this table got it wrong.** It
recorded `1/9 over clock`, from a run whose round trip was 1.18 ms against a 1 ms clock. But **8 of
9 runs at a 1 ms clock emit no `info` line carrying a `time` field at all** (`reserve_empty` means
the search stops before any timed iteration), so the script fell back to wall time and compared a
*round trip* against the clock. Under engine time the count is **0 of 9**. Nothing can answer inside
1 ms on this machine — the bare round trip is ~0.6 ms — but the engine does not overrun its own
budget; the earlier number was the harness measuring itself. Same class as §6, caught by checking
which quantity a fallback had substituted.

**Below the floor the engine degrades to "answer with no search", and it still answers.** From
111 ms down to 20 ms the plan shrinks smoothly and every run answers legally inside the clock. At
**10 ms and below** `clock <= overhead` so `plan_clock_budget` returns `reserve_empty`, and
`should_stop_with` returns true immediately (`search.cpp:1282-1285`): the engine plays depth 0–1 and
answers with **0 ms of reported search time** (0–1 ms by the harness's own round trip). That is the
correct failure mode — it does not panic, hang, or emit a null move.

**No clock in this sweep was overrun, measured against the engine's own time.** Of the 99 runs in
the eleven below-floor rows, **75 emitted a timed `info` line** and **0 of those 75 exceeded their
clock**; the remaining 24 (mostly the 1 ms row) never started a timed iteration, so they have no
search time to exceed anything. The earlier "1/9 late" figure at 1 ms is withdrawn as a wall-time
comparison — see the table's note.

### 4.3 Where the 111 ms floor comes from — it is an equilibrium, not a constant

The report records the floor as an observation ("converged from every start ≥ 111"). It is
reproducible from the planner and that is worth having, because a derived floor predicts an
increment nobody tested. Simulating a player that spends its whole hard limit each move
(`clock' = clock − hard + increment`, `scripts/p11_floor_derivation.py`):

| increment | fixed points | rests at (from a 60 s start) |
|---|---|---|
| 0 | none | drains to the overhead, 10 ms |
| 20 | 44 | 44 |
| **60** | **110, 111** | **111** |
| 100 | 177, 178 | 178 |
| 200 | 344 | 344 |
| 1000 | 1677, 1678 | 1678 |

**From every start ≥ 111 at a 60 ms increment the clock converges to 111 in 500 moves, and never
dips below it** — 7 of 7 starts from 111 to 60,000 ms. Above 111 the clock shrinks; below it the
clock grows (start 20 → 110, 60 → 110, 105 → 110); so 110/111 is a **stable** pair of fixed points
and the floor is the upper one. That is why the report's wording "cannot be lost by searching" is
right for a clock at or above the floor: it is not that the engine is careful, it is that the plan
is smaller than the increment there.

**Two closed forms were tried and both miss**, and the misses are recorded rather than the
derivation being re-worded to fit. `22×inc/5 + 10` (hard = increment) gives **274**, and
`22×floor(inc/5) + 9 + 10` (last clock with hard ≤ increment) gives **283**, against a simulated
floor of **111**. So the floor is **not** the fixed point of "spend the entire hard limit" in closed
form; it is an equilibrium of the integer plan, established by simulation. The control that shows
the equilibrium is real and not an artefact of the fraction: at 0.2 of the hard limit the clock
settles at **512 ms**, at 0.6 at **179 ms**, at 1.0 at **111 ms** — so the resting point tracks how
much of the plan is actually spent, which is why the observed floor of 111 corresponds to
*worst-case* play and real games sit far above it.

---

## 5. Threads 1 vs 4 (cheap arm only — not the main work)

One midgame position, `wtime/btime` only, 9 repetitions, **engine's own `time`**. Only the main
worker honours the clock (`search.cpp:1276-1278`); helpers poll the parent.

| clock | plan | T1 median | T1 max | T4 median | T4 max | over hard |
|---|---|---|---|---|---|---|
| 500 | 22/110 | 13 | 52 | 13 | 28 | 0/18 |
| 1000 | 45/225 | 43 | 105 | 41 | 90 | 0/18 |
| 3000 | 135/675 | 155 | 542 | **85** | 302 | 0/18 |

**Nothing material differs, and the one visible difference is not established.** T4's 3000 ms
median is lower (85 vs 155 ms) but the T1 samples are `[542, 155, 81, 167, 153, 131, 70, 167, 208]`
and T4's are `[114, 74, 71, 172, 302, 67, 149, 85, 16]` — **the ranges overlap almost entirely**, so
n=9 on one position does not separate them and the bold median is a hint, not a result. Neither
thread count exceeded the hard plan in 54 runs, which is the finding that matters here. This is one
position and is not offered as a population result; it is enough to say that the accounting findings
above are not a Threads 1 artefact.

---

## 6. A finding of this seat's own, withdrawn

A 3000+200 game appeared to flag. **It was my harness, twice over, and both faults are recorded
because each one alone would have produced a publishable-looking defect.**

1. **The clock was charged harness wall time, not the engine's own `time` field.** Wall time is
   measured from just before the `go` write to the `bestmove` read. On a shared 4-core box that
   carries scheduling delay: one replayed move showed a **452 ms wall tail over a 185 ms search**.
   Charging that to the engine invents forfeits. Fixed by charging the engine's `time` field and
   recording `tail_ms` per move so the tail is auditable.
2. **Black's clock was sent in `wtime`.** The base build reads `btime` for a Black mover, so a
   Black move was planned off *White's* clock — for the move in question, a 462 ms clock planned as
   if it were 1739 ms. That is the 2.3× "overrun". **42 isolated replays** of that position at that
   clock produced **0 of 42** moves over the hard plan, which is what exposed the mapping.

Both are now guarded: the game driver records `clock_sent` beside `clock_before` per move and
counts `clock_mapping_errors`, which is **0** on every game reported in §1. With both faults fixed
the 3000+200 forfeits disappeared.

**So the established "0 forfeits" result survives**, and this seat found no counter-example. The
withdrawal is stated here because the intermediate artefact — a flag at a real time control — is
exactly the kind of number that gets quoted without its correction.

### 6b. The engine's `time` field is not the search duration, in either direction

This is the third instance of the same shape in this seat and it is the most transferable, so it is
stated as its own finding.

**`info … time <ms>` is the elapsed time at the moment that line is emitted — the end of a
*completed* iteration — not the total the search ran.** When the hard limit cuts an iteration short,
that iteration never emits, so the last number on the stream is the *previous* iteration's end. The
gap is not small:

| request | last `info` `time` | actual call duration | gap |
|---|---|---|---|
| `movetime 2000` | 453–1988 ms (12 reps) | 1990–1991 ms | up to **1538 ms** |
| `movetime 500` | 104–469 ms | 490–491 ms | up to **387 ms** |
| `movetime 100` | 11–88 ms | 90–91 ms | up to **80 ms** |

So the field **understates** spend at the moment the clock matters most, and a harness that charges
it will systematically under-bill the engine exactly on the moves where the hard limit fired — which
are the moves a forfeit would occur on. The opposite error is equally available: harness wall time
**overstates** by the round trip and by any scheduling delay, which on this box reaches hundreds of
milliseconds at p99.

**Neither quantity is "the clock".** The only defensible practice found here is to compute every
conclusion under **both** bases and show that it does not move — §1 does this and both give 0
forfeits, 0 flags, and utilisation maxima of 0.596 (engine) and 0.597 (wall). A single-basis claim
about timing on a noisy box is a claim about which quantity the harness happened to read.

---

## 7. What is still not established

- **The 10000+1000 control did not finish.** 150 games / 19,630 plies at 200+0, 1000+100 and
  3000+200 are reported; the long control is **absent, not zero**. At ~2 min/game it was still
  running when this file closed.
- **Single-run wall times in §2 are not trustworthy individually** — proven, not assumed: the
  own-clock `movestogo 2` row differed 2× between builds and 12 interleaved repeats per build
  showed the ranges overlap almost entirely (sd 300–360 ms within each build). The §2 conclusions
  rest on plan values and regime separation only. Any future seat quoting a §2 millisecond figure
  as an effect is repeating the mistake this section documents.
- **The 111 ms floor is derived for one increment.** The equilibrium was simulated at increments
  0/20/60/100/200/1000 and reproduces the recorded floor exactly at 60 ms, but no **game** was run
  to confirm a non-60 increment settles where the simulation says. It is a derivation plus a
  simulation, not a measured equilibrium at a second increment.
- **The one-sided clock is still a hang on the unpatched base** — re-confirmed here (`btime 2000`
  with White to move: no answer in 12 s, every arm). That is trap 18/19 restated, not new; it is
  listed so the §2 table's base column is not mistaken for a claim that the base is usable.
- **The below-floor probe uses one position.** The `reserve_empty` behaviour at ≤ 10 ms is a
  structural path (`should_stop_with` returns immediately), so it should not be position-dependent,
  but that is an argument, not a measurement across positions.
- **`movestogo` was never exercised with an increment on the fallback path.** §2 used increment 0
  throughout. The plan formula adds `inc × 0.75` on the movestogo branch
  (`clock_plan.hpp:39`), and whether the fallback's increment resolution behaves identically is
  **unmeasured** — it is the same class of gap as the one this seat was asked to close, one level
  down.
- **The `> 50 → 50` clamp was measured at one clock (2000 ms).** It is a comparison of
  `moves_to_go` against a constant, so it should be clock-independent, but only 2000 ms was run.
- **Long games beyond 400 plies were not run**; threefold and fifty-move endings dominate the
  200+0 set before the ply cap.
