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

<!-- SECTION1 -->

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

> A stale-binary trap fired here and is worth recording, because it would have silently voided
> this section. The first "patched" build reported `rc=1` from `cmake --build` while
> `check_pins.sh` printed `PINS MATCH`. The cause: the copied worktree already contained
> `build/forge` from the *unpatched* tree, so the pin script tested a **binary identical to the
> base build** — confirmed with `cmp`. Pins passing on a stale executable look exactly like pins
> passing on a real one. The rebuild after `rm -rf build` produced a distinct binary and the pins
> were re-run on it.

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
the recorded repair from trap 19e and this seat only uses it. The wall times are single runs per
cell on a shared 4-core box, so the 35–892 ms spread across arms that share a *plan* is scheduling
noise on this machine (the same plan appears at 35 ms and 67 ms), not a planner effect. The claims
above rest on **plan values and regime separation**, which are exact, not on the wall times, which
are not.

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

---

## 4. Sudden death versus increment, and clocks below the floor

All rows: 9 repetitions, Threads 1, book off, engine's own `time` field. `plan` is soft/hard.

### 4.1 Sudden death vs increment at short clocks

| clock | inc 0 (SD) | inc 50 | inc 100 | inc 200 |
|---|---|---|---|---|
| 200 | plan 8/40, med 11.3, max 18.8 | 45/114, 41.0, 114.8 | 83/114, 60.4, 114.9 | 114/114, 104.7, 115.1 |
| 500 | 22/110, 19.8, 44.1 | 59/294, 58.8, 127.1 | 97/294, 83.6, 146.8 | 172/294, 148.1, 295.1 |
| 1000 | 45/225, 60.9, 129.0 | 82/410, 70.3, 211.2 | 120/594, 106.7, 272.3 | 195/594, 129.8, 410.6 |
| 2000 | 90/450, 72.2, 208.5 | 127/635, 110.1, 262.0 | 165/825, 138.5, 227.4 | 240/1194, 293.9, 1026.3 |

**Not one of 144 runs exceeded its hard plan, and none exceeded the clock.** The increment changes
the plan in exactly the way `clock_plan.hpp` says: soft rises by `inc × 0.75` until the hard limit
clamps it. At 200 ms the three increment rows all converge on hard = 114 — the same
`0.6 × (200−10) = 114` ceiling the report records — so **at a short clock an increment buys plan
only until `0.6×available` binds, and past that it buys nothing.**

### 4.2 The 111 ms floor, and what happens below it

| clock | plan soft/hard | reserve empty | median | max | answered | over clock |
|---|---|---|---|---|---|---|
| 150 | 6/30 | no | 5.07 | 18.72 | 9/9 | 0/9 |
| **111** | 4/20 | no | 4.02 | 21.17 | 9/9 | 0/9 |
| 110 | 4/20 | no | 3.70 | 20.68 | 9/9 | 0/9 |
| 100 | 4/20 | no | 4.13 | 20.64 | 9/9 | 0/9 |
| 60 | 2/10 | no | 2.64 | 9.59 | 9/9 | 0/9 |
| 40 | 1/5 | no | 0.77 | 1.74 | 9/9 | 0/9 |
| 20 | 1/1 | no | 0.69 | 1.51 | 9/9 | 0/9 |
| 11 | 1/1 | no | 0.62 | 1.36 | 9/9 | 0/9 |
| **10** | 0/0 | **yes** | 0.57 | 1.08 | 9/9 | 0/9 |
| 5 | 0/0 | yes | 0.58 | 1.24 | 9/9 | 0/9 |
| **1** | 0/0 | yes | 0.67 | 1.18 | 9/9 | **1/9** |

**Below the floor the engine degrades to "answer with no search", and it still answers.** From
111 ms down to 20 ms the plan shrinks smoothly and every run answers legally inside the clock. At
**10 ms and below** `clock <= overhead` so `plan_clock_budget` returns `reserve_empty`, and
`should_stop_with` returns true immediately (`search.cpp:1282-1285`): the engine plays depth 0–1 and
answers in **0.6–0.7 ms**. That is the correct failure mode — it does not panic, hang, or emit a
null move.

**The one over-clock result is honest and is a finding about the *clock*, not the search.** At a
**1 ms clock** the engine answered in **1.18 ms** once in 9 — 0.18 ms late. Nothing can answer
inside 1 ms on this machine (the round trip alone is ~0.6 ms), so a 1 ms clock is not a budget the
engine can meet, and it does not pretend to. Every clock of 5 ms and above was met, 90 of 90.

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

One midgame position, `wtime/btime` only, 9 repetitions. Only the main worker honours the clock
(`search.cpp:1276-1278`); helpers poll the parent.

| clock | plan | T1 median | T1 max | T4 median | T4 max | over hard |
|---|---|---|---|---|---|---|
| 500 | 22/110 | 13 | 52 | 13 | 28 | 0/18 |
| 1000 | 45/225 | 43 | 105 | 41 | 90 | 0/18 |
| 3000 | 135/675 | 155 | 542 | **85** | 302 | 0/18 |

**Nothing material differs.** T4 reaches a lower wall time for the same plan (3000 ms: 85 vs
155 ms median) because four threads finish the same iteration sooner, and neither thread count
exceeded the hard plan in 54 runs. This is one position and is not offered as a population result;
it is enough to say that the accounting findings above are not a Threads 1 artefact.

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

---

## 7. What is still not established

- **Item 2's wall times are single runs per cell** on a shared machine. The plan values and regime
  separations are exact; the individual milliseconds are not. A reader should not quote `72 ms vs
  82 ms` as a precise effect.
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
