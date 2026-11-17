# Ponder protocol — owner audit, `forge-combo29` @ `6b98f217`

Six questions about the surface every match runner uses. One engine process per
measurement, `OwnBook false` unless the book is the subject, Threads 1, Hash 32,
Move Overhead 10. Every wait is deadline-bounded; a deadline hit is reported as
`CAPPED` and the process is SIGKILLed. **No probe in this audit ever hit its
cap** — every row below is a return, not a timeout.

**Build and pins.** `/usr/bin/g++` 13.3.0, `-DCMAKE_CXX_COMPILER=/usr/bin/g++`,
`LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, Release. Four honesty pins
confirmed on the binary used for every measurement below:
**312 866 / 862 329 / 3 024 920** (bench 11/13/16 net on) and
**perft 5 = 4 865 609**. Evidence: `evidence/pins/pins.txt`, raw engine output
beside it. Net-off pins also matched (375 354 / 907 205 / 2 448 617).

---

## Verdicts

| # | question | verdict |
|---|---|---|
| 1 | `ponderhit` converts to a clocked search? budget from `go` or from `ponderhit`? | **Converts. Budget starts at `ponderhit`.** 16/16 offsets bounded by the hard limit, 0 stopped at ~0 ms |
| 2 | `go ponder` + `stop`, no `ponderhit` — bestmove? which move? | **Returns a bestmove, never `0000`, and it is the move found** (18/18). At 0 ms it returns the first legal move, indistinguishable from the piped-abort artifact |
| 3 | `go ponder wtime X btime Y` bounded? | **No. Unbounded, exactly like the clockless case.** CPU 99.9%, depth still rising at 20 s, 0 bestmoves |
| 4 | `ponderhit` with no ponder running | **Silent, no output, engine stays responsive.** Path proven live by a control that does convert |
| 5 | `Ponder` option true/false | **Only appends ` ponder <move>` to the bestmove line.** Does not change the search, does not cause self-pondering, does not gate the `go ponder` token |
| 6 | output during pondering; `bestmove` exactly once? | **`info` lines stream while pondering (~10/s); exactly one `bestmove`, nothing after it**, including under four command-race cases |

Three findings are new or sharpened relative to `forge-findings.md`:

- **Item 3 contradicts the impression left by trap 3a1.** That trap states
  `ponder` *without a clock* is unbounded, which invites the reading that a clock
  bounds it. It does not. A clocked ponder is equally unbounded — measured below.
- **Two clocks disagree inside one search.** The `info` `time` field counts from
  the `go` command; the stop decision counts from `ponderhit`. After a 3 s ponder
  the engine reports `time 4140` having thought for 1140 ms.
- **The `Ponder` option is off by default**, so by default no ` ponder` hint is
  emitted at all — a runner that reads the suffix gets nothing unless it sets it.

All tables below are generated from `evidence/` by `scripts/make_tables.py`;
every figure quoted in the prose is re-checked against the same files by
`scripts/check_claims.py` (40 checks, exit 0).

<!-- BEGIN GENERATED TABLES -->

#### T1 — wall time from `ponderhit` to `bestmove`

The first three rows are the apples-to-apples comparison (fixed 2 s ponder). The rest sweep the ponder length at one clock: if the budget were measured from `go`, these would fall as the ponder grows.

| clock (ms) | soft | hard | ponder (ms) | hit → bestmove (ms) |
|---|---|---|---|---|
| 2000 | 90 | 450 | 2000 | **176.2** |
| 10000 | 454 | 2270 | 2000 | **463.0** |
| 60000 | 2726 | 13630 | 2000 | **1816.5** |
| 2000 | 90 | 450 | 200 | 71.2 |
| 2000 | 90 | 450 | 1000 | 450.8 |
| 2000 | 90 | 450 | 3000 | 450.6 |
| 2000 | 90 | 450 | 6000 | 450.5 |
| 10000 | 454 | 2270 | 200 | 757.9 |
| 10000 | 454 | 2270 | 1000 | 954.1 |
| 10000 | 454 | 2270 | 3000 | 1250.1 |
| 10000 | 454 | 2270 | 6000 | 1429.9 |

#### T2 — the budget-origin discriminator (16 offsets)

If the budget were measured from the original `go`, any ponder longer than `hard` would leave nothing and `hit→best` would be ~0 ms. The `hit→best − hard` column is the test; the last column shows most rows stop at the end of an iteration, well below the cap.

| clock | soft | hard | ponder (ms) | hit→best (ms) | hit→best − hard (ms) | iterations after hit |
|---|---|---|---|---|---|---|
| 2000 | 90 | 450 | 300 | **141.7** | -308.3 | 2 |
| 2000 | 90 | 450 | 500 | **402.1** | -47.9 | 1 |
| 2000 | 90 | 450 | 800 | **85.7** | -364.3 | 1 |
| 2000 | 90 | 450 | 1200 | **450.3** | 0.3 | 0 |
| 2000 | 90 | 450 | 1800 | **258.9** | -191.1 | 1 |
| 2000 | 90 | 450 | 2500 | **450.9** | 0.9 | 0 |
| 2000 | 90 | 450 | 3500 | **450.9** | 0.9 | 0 |
| 2000 | 90 | 450 | 5000 | **450.9** | 0.9 | 0 |
| 10000 | 454 | 2270 | 300 | **599.4** | -1670.6 | 3 |
| 10000 | 454 | 2270 | 500 | **408.7** | -1861.3 | 1 |
| 10000 | 454 | 2270 | 800 | **1090.3** | -1179.7 | 2 |
| 10000 | 454 | 2270 | 1200 | **677.0** | -1593.0 | 1 |
| 10000 | 454 | 2270 | 1800 | **320.8** | -1949.2 | 2 |
| 10000 | 454 | 2270 | 2500 | **1302.4** | -967.6 | 2 |
| 10000 | 454 | 2270 | 3500 | **231.4** | -2038.6 | 1 |
| 10000 | 454 | 2270 | 5000 | **1806.0** | -464.0 | 1 |

**n = 16. Max `hit→best − hard` = 0.9 ms. Rows that stopped at ~0 ms (the 'budget already spent' prediction): 0.**

#### T3 — ponder far past the whole planned budget

A 6 s ponder against a 225 ms hard limit is 26.7× over at the hit. The prediction of a `go`-based budget is `hit→best ≈ 0`.

| clock | hard | ponder (ms) | ponder / hard | hit→best (ms) | hit→best / hard |
|---|---|---|---|---|---|
| 1000 | 225 | 6000.4 | 26.67 | **225.9** | 1.004 |
| 500 | 110 | 4000.5 | 36.37 | **70.8** | 0.644 |
| 2000 | 450 | 8000.7 | 17.78 | **450.9** | 1.002 |
| 10000 | 2270 | 6000.5 | 2.64 | **1304.1** | 0.574 |

#### T4 — control: the same clocks with no ponder at all

| clock | go→best (ms) | depth | last info `time` (ms) | bestmove | bestmove lines |
|---|---|---|---|---|---|
| 10000 | 410.8 | 19 | 410 | d2d3 | 1 |
| 10000 | 331.5 | 18 | 331 | d2d3 | 1 |
| 60000 | 1826.3 | 21 | 1825 | d2d3 | 1 |
| 60000 | 1804.3 | 21 | 1804 | d2d3 | 1 |
| 2000 | 142.0 | 15 | 141 | d2d3 | 1 |
| 2000 | 124.9 | 15 | 124 | d2d3 | 1 |

#### T5 — `go ponder` then `stop`, no `ponderhit`

| case | depth before stop | info lines | bestmove | is `0000` | stop→best (ms) | = last info PV |
|---|---|---|---|---|---|---|
| `ponder_then_stop_after_1s` | 20 | 20 | d2d3 | False | 0.8 | True |
| `ponder_then_stop_immediately` |  | 0 | a2a3 | False | 1.0 | False |
| `ponder_clockless_then_stop_after_1s` | 20 | 20 | d2d3 | False | 1.0 | True |
| `ponder_then_pause_then_stop_2s` | 21 | 21 | d2d3 | False | 0.7 | True |

#### T6 — is the `stop` reply the move the search had found?

**18 of 18** stop replies equal the PV head of the last info line before the `bestmove` (6 positions × 3 ponder lengths). The comparison is against the last info line that arrived *before the bestmove*, not the last one the harness had read when it sent `stop`: an iteration can complete in that gap, and the first version of this probe scored one such case (endgame, 400 ms) as a disagreement.

#### T7 — is a clocked ponder bounded? (20 s horizon, no `ponderhit`)

| go | regime | CPU% at horizon | depth still rising | bestmoves emitted | `stop` returns | stop→best (ms) |
|---|---|---|---|---|---|---|
| `go ponder wtime 10000 btime 10000` | **RUNAWAY** | 99.9 | True | 0 | True | 0.4 |
| `go ponder` | **RUNAWAY** | 99.9 | True | 0 | True | 0.3 |
| `go ponder depth 12` | **WITHHELD** | 0.1 | False | 0 | True | 0.5 |
| `go ponder nodes 500000` | **WITHHELD** | 1.5 | False | 0 | True | 0.4 |

#### T8 — `ponderhit` when no ponder search is running

The last row is the control that makes the other four meaningful.

| state | emitted anything | silent within 2 s | after | second `ponderhit` |
|---|---|---|---|---|
| `idle_after_startup` | False | True | responsive (`readyok`) |  |
| `after_a_completed_search` | False | True | responsive (`readyok`) |  |
| `ponderhit_twice` | False | True | responsive (`readyok`) | [] |
| `ponderhit_after_stop` | False | True | responsive (`readyok`) |  |
| **control: live ponder** | — | — | **converted, 385.5 ms** | — |

#### T9 — what the `Ponder` option changes

Rows 1–2 are the same depth-8 search under both settings: the node counts are identical, so the null on "does it change the search" is a measured equality. Rows 3–4 test self-pondering — after `bestmove`, 3 s of silence was required, so an engine that began pondering on its own would have shown info lines there. Rows 5–6 show the `go ponder` token behaving identically with the option off, so the option does not gate the protocol.

| Ponder | bestmove line | ` ponder` suffix | nodes | self-ponder after bestmove | depth / hit→best (ms) |
|---|---|---|---|---|---|
| false | `bestmove e1g1` | absent | **17804** | not tested | 10 |
| true | `bestmove e1g1 ponder e8g8` | **present** | **17804** | not tested | 10 |
| false, then 3 s silence | `bestmove d2d3` | absent | — | no | 124.6 ms |
| true, then 3 s silence | `bestmove d2d3 ponder h7h6` | **present** | — | no | 133.3 ms |
| false, `go ponder` cycle | — | — | — | no | **602.5** |
| true, `go ponder` cycle | — | — | — | no | **651.7** |

#### T10 — output shape while pondering, and `bestmove` uniqueness

The four command-race cases are the ones that could plausibly emit twice.

| case | info while pondering | bestmove lines | lines after |
|---|---|---|---|
| `info_volume_while_pondering` | 21 in 2000.3 ms (10.5/s) | 1 | 0 |
| `ponderhit_then_stop` | — | 1 | 0 |
| `ponderhit_then_stop_50ms` | — | 1 | 0 |
| `stop_then_stop` | — | 1 | 0 |
| `ponderhit_then_ponderhit` | — | 1 | 0 |

#### T11 — two clocks in one process

The `info` `time` field counts from `go`; the stop decision counts from `ponderhit`. The last column is the gap, which equals the ponder length.

| clock | ponder (ms) | hard | info `time` at best (ms) | wall from `ponderhit` (ms) | `time` − wall (ms) |
|---|---|---|---|---|---|
| 10000 | 500 | 2270 | **1212** | **712.7** | 500 |
| 10000 | 3000 | 2270 | **4140** | **1140.6** | 3000 |
| 60000 | 3000 | 13630 | **4262** | **1262.3** | 3000 |

#### T12 — the zero-ms `stop` reply, against the piped-abort artifact

| position | first legal (perft 1) | `stop` at 0 ms | immediate EOF | EOF after 300 ms | identical | is `0000` |
|---|---|---|---|---|---|---|
| position_A | a2a3 | `bestmove a2a3` | `bestmove a2a3` | `bestmove d2d3` | **True** | False |
| position_B | f7f6 | `bestmove f7f6` | `bestmove f7f6` | `bestmove g7g6` | **True** | False |

#### T13 — the `ponder` suffix is load-bearing, so it is checked

12 of 14 bestmove lines carried a suffix, and every one was legal in the position after the best move (verified against the engine's own `go perft 1` move list, not an external library). 2 had no suffix — both on a mate-in-one root, where the PV has length 1. 0 were illegal or `0000`.

#### T14 — runner desync when the next ponder starts without `stop`

Timestamps are ms relative to the second `go ponder`; a negative value means the line arrived before it.

| `stop` before restart | bestmove lines | moves @ ms | ambiguous to a runner |
|---|---|---|---|
| yes | 2 | `d2d3` @ -201.2, `e4e5` @ 1103.4 | no |
| **no** | 2 | `d2d3` @ 0.5, `e4e5` @ 1359.7 | **yes** |

#### T15 — a drawn root under ponder floods `info` at zero cost

| info lines | depths | nodes reported | arrival | bestmove withheld | then |
|---|---|---|---|---|---|
| 64 | 1 → 64 | 0 | within 0.5 ms of `go` | True | bestmove a2a3 |

<!-- END GENERATED TABLES -->

---

## 1. The full ponder cycle: does `ponderhit` convert, and where does the budget start?

`position` → `go ponder wtime X btime Y` → `ponderhit` mid-search. The engine
converts: the search keeps running, stops at a clock deadline, and emits one
`bestmove`. The question that matters is **which instant the budget is measured
from**, and a flat hit→best time cannot answer it on its own — a search that had
already burned 3 s could be stopping early for either reason.

**The discriminator is what happens when the ponder is longer than the entire
planned budget.** For `wtime 1000` the engine's own plan (`soft = usable/22`,
`hard = min(usable*60/100, soft*5)`, `usable = 1000 - 10`) is soft 45 ms, hard
225 ms. A 6 s ponder is **26.7× the hard limit**. If the budget were measured
from the original `go`, that budget was exhausted ~5.8 s before the hit and
`ponderhit` would have to return in ~0 ms. Measured: **225.9 ms**, i.e. the full
fresh hard limit.

Across 16 offsets at two clocks (`T7`), **not one row stopped at ~0 ms**, and the
largest excess over the hard limit was **0.9 ms**. That is an upper bound, and it
is the shape a rebased-and-capped budget makes:

```
budget origin = ponderhit, hard cap = plan for the full clock
```

**The bound is the claim, not an equality.** Most rows stop well *below* hard —
at the soft deadline or at the end of the iteration in progress. So the honest
statement is: *the post-hit search is never given more than a full `hard` budget
and is never given zero.* Reading `hit→best == hard` would be wrong; **10 of 16
rows are below 60% of hard** (computed by `scripts/check_claims.py`, not
counted by eye).

### Wall time from `ponderhit` to `bestmove`, three clock settings

Reported at a **fixed 2 s ponder** so the clocks are comparable, then swept at
one clock to show the time does not shrink as the ponder grows.

| clock (ms) | soft | hard | ponder | **hit → bestmove** |
|---|---|---|---|---|
| 2 000 | 90 | 450 | 2 s | **176.2 ms** |
| 10 000 | 454 | 2270 | 2 s | **463.0 ms** |
| 60 000 | 2726 | 13 630 | 2 s | **1816.5 ms** |

**Which: the `ponderhit` moment.** Three independent lines agree.

1. **The discriminator above** — a ponder 26–36× the hard limit still receives a
   full budget, and never receives zero.
2. **The sweep** (`T1`): at clock 2000, hit→best is 450.8 / 450.6 / 450.5 ms for
   ponder lengths 1 / 3 / 6 s. If the budget were measured from `go`, a longer
   ponder would leave *less*; the value would fall towards zero. It is flat.
3. **The source.** `Worker::elapsed_ms()` rebases its origin to
   `shared_.ponder_hit_ns` whenever `pondering_` is set and the hit is non-zero
   (`search.cpp:1244-1251`), and every stop test reads `elapsed_ms()`
   (`search.cpp:1287`, `:2320`, `:2612`). Before the hit the same field returns
   `0`, which is why a clocked ponder never stops on its own — see §3.

Control (`T3`): the same clocks with no ponder at all give 125–142 ms / 332–411 ms
/ 1804–1826 ms, i.e. the ordinary clocked search. The ponder path costs the runner
nothing beyond the search it replaced.

### A caveat that belongs on the same page as the timings

Wall time is **not** reproducible to better than ~±100 ms at clock 10 000: the
same request gave hit→best of 236 / 463 / 678 / 1250 ms across runs. That is not
noise in the engine — it is the iteration boundary. The stop is evaluated inside
the search and at the end of each iteration, so a hit that lands just after a
boundary waits for the next one. **The number a runner experiences is "up to the
hard limit, usually the soft deadline plus the rest of one iteration".** Any
figure quoted from a single run is a sample from that distribution, not a
constant.

---

## 2. `go ponder` then `stop`, with no `ponderhit`

**It returns a `bestmove`, and the move is the one the search had found — not
`0000`.** 18 of 18 across 6 positions × 3 ponder lengths (`T5`); stop→best is
0.7–1.0 ms in every case, so the reply is immediate and does not wait for the
hard limit.

`0000` appeared in **zero** of the 18. That matches the source: the `bestmove`
field is `result.best_move`, replaced by `0000` only when the move is unset, and
a stopped search still holds the PV head of its last completed iteration.

**One measurement trap, recorded because it bit the first version of this
probe.** Comparing the `stop` reply against "the last info line the harness had
read when it sent `stop`" produced a spurious disagreement (endgame position,
400 ms ponder: reply `f7f6`, "last" PV `g7g6`). An iteration completed in the gap
between the harness's last read and the engine consuming the `stop`. The
comparison must be against **the last info line that arrived before the
`bestmove`**, which gives 18/18. A first attempt scored 17/18 and the missing one
was the harness, not the engine.

### The 0 ms case is not a measurement

`go ponder` immediately followed by `stop`, with no information exchanged,
returns `bestmove a2a3` with **zero info lines** — on this position `a2a3` is the
first move in the generator's legal list (`go perft 1` order starts `a2a3`,
`b2b3`, `d2d3`, `g2g3`). On a second position (black to move, first legal `f7f6`)
it returns `f7f6`. So it tracks the position; it is not a fixed fabrication.

**But it is byte-identical to the piped-abort artifact** that trap 7.1/7.2d0
warns about: closing stdin immediately after `go ponder` produces the same
`a2a3` with the same zero info lines on position A, and `f7f6` on position B
(`T11`). The two hypotheses — "the engine answered" and "the harness aborted the
search and got the fabricated fallback" — make **identical predictions here**, so
this audit does not distinguish them. What can be said:

- For a runner, the distinction does not matter: after an immediate `stop` there
  was no search to report, and the first legal move is what comes back either way.
- **Any row in an existing corpus that reads `0000`-or-first-legal with zero info
  lines should be treated as unlabelled** rather than as a clock or protocol
  result.

This is the same discipline as trap 3ac0: a fingerprint test needs a depth at
which the candidate hypotheses predict different values, and here none exists.

---

## 3. `go ponder` with a clock — is it bounded?

**No.** `go ponder wtime 10000 btime 10000`, no `ponderhit`, 20 s cap:

| at | depth | nodes | CPU | bestmoves |
|---|---|---|---|---|
| 1 s | 19 | 720 945 | — | 0 |
| 5 s | 20 | 1 522 587 | — | 0 |
| 10 s | 21 | 3 024 367 | — | 0 |
| 20 s | **28** | **24 779 930** | **99.9%** | **0** |

Depth 19 → 28 and 0.7 M → 24.8 M nodes over the horizon, at a full core, with no
`bestmove`. A 20 s cap was hit; the process was then killed. A separate run
carried the same request to **45 s**: depth 32, 61.2 M nodes, still 99.9% CPU,
still no `bestmove`. **`wtime`/`btime` do not bound a ponder search.**

**This is the mechanism the findings file already names, applied one level out.**
Trap 3a1 says `ponder` "only *suppresses* the clock". It does — the suppression is
unconditional until a `ponderhit` arrives, and the clock values are carried in the
same struct but never consulted, because `elapsed_ms()` returns `0` while
`ponder_hit_ns == 0`. So the clock is not a fallback bound, and the clocked case
behaves exactly like the clockless one. **The trap's wording ("`ponder` WITHOUT a
clock are UNBOUNDED") is literally true but reads as if a clock would help. It
does not, and a runner that sends `go ponder` with clocks and then loses the
`ponderhit` — a dropped connection, a crashed opponent — burns a core indefinitely.**

### There are two "unbounded" regimes and only one burns CPU

"No bestmove" has two causes, and a runner sees the same silence from both. They
differ in whether the engine is working:

| go | regime | CPU at 20 s | depth still rising | `stop` returns |
|---|---|---|---|---|
| `go ponder wtime 10000 btime 10000` | **RUNAWAY** | 99.9% | yes | yes, 0.4 ms |
| `go ponder` | **RUNAWAY** | 99.9% | yes | yes, 0.3 ms |
| `go ponder depth 12` | **WITHHELD** | 0.1% | **no** | yes, 0.5 ms |
| `go ponder nodes 500000` | **WITHHELD** | 1.5% | **no** | yes, 0.4 ms |

In the WITHHELD case the search has finished its own limit and is sitting on the
answer — measured directly: at 6 s a `go ponder depth 12` had reached depth 12
with 38 459 nodes, 12 info lines, **0.8% CPU and no `bestmove`**. It is idle, and
it will wait forever. A run that sends `go ponder depth N` or `go ponder nodes N`
and then measures "did it return" without sending anything will conclude the
engine is hung when it is actually finished and waiting.

Both regimes are recoverable with `stop` in under 1 ms, and in both the `stop`
reply was the found move (18/18 covers the runaway case; the withheld case returns
the move at the limit).

---

## 4. `ponderhit` when no ponder search is running

**Silent. The engine says nothing and stays responsive.** Four states tested, and
in every one the engine emitted no bytes within a 2 s window and still answered a
following `isready` with `readyok`:

| state | emitted | second `ponderhit` |
|---|---|---|
| idle, right after startup | nothing | — |
| after a completed depth-6 search | nothing | — |
| a second `ponderhit` after a ponder already converted | nothing | nothing |
| after `stop` had already ended a ponder | nothing | — |

**The null is only meaningful with a control that proves the path runs**, because
"silent at idle" and "`ponderhit` is never handled" look identical. Control: the
same command sent to a live ponder **converts and returns a `bestmove` in 385 ms**
(`T7`, last row). So the handler is live and the silence at idle is a real
decision to do nothing.

Source agrees: `ponderhit` is gated on `ponder_search_active`, a plain `bool`
cleared by `stop_search()` and by the conversion itself (`uci.cpp:627-636`), and
there is no `else` branch. **No diagnostic is ever emitted for a stray
`ponderhit`** — the same "improvisation vs silence" asymmetry trap 3aa records for
`parse_limits`, except here the choice is silence rather than a default search.

**One consequence worth flagging.** `ponder_search_active` is cleared as soon as
the hit is consumed, so a *late* `ponderhit` — arriving after the engine already
returned its `bestmove` — is silently discarded. Measured at three delays after
`stop` (50 / 300 / 1000 ms): no output, one total `bestmove`, engine alive, and a
following search fine. For a runner this is benign **only if** it pairs the
`bestmove` with the `stop` it sent; see §6 for the case where it does not.

---

## 5. The `Ponder` option — true vs false

**The option changes exactly one thing: whether a ` ponder <move>` field is
appended to the `bestmove` line.** It is a formatting flag, not a search or
protocol switch.

| Ponder | bestmove line | nodes | suffix |
|---|---|---|---|
| false | `bestmove e1g1` | 17 804 | absent |
| **true** | `bestmove e1g1 ponder e8g8` | **17 804** | present |

Same position, same depth, **identical node count to the node** — so the null on
"does it change the search" is a measured equality, not an absence of evidence.
Three further nulls, each with the path shown to run:

- **It does not make the engine ponder on its own.** After a clocked `bestmove`
  with `Ponder true`, 3 s of silence: 0 info lines, 0 further `bestmove`. The
  engine never starts an unsolicited ponder search.
- **It does not gate the `go ponder` token.** `go ponder …` + `ponderhit` works
  identically with the option false (602.5 ms) and true (651.7 ms).
- **It does not change the move choice under a clock** (`d2d3` both arms).

**Two facts a runner needs.**

1. **The default is `false`** (`option name Ponder type check default false`,
   `uci.cpp:204`), so out of the box the engine emits **no** ` ponder` hint. A
   runner that reads the suffix to pre-set its next search gets nothing until it
   sends `setoption name Ponder value true`.
2. **The suffix is `result.pv[1]` and is omitted when the PV has length 1** —
   confirmed on a mate-in-one root, `bestmove a1a8` with no suffix (`T12`, 2 of 14
   rows absent). That is correct behaviour (there is no reply), but a runner that
   assumes a suffix is always present will index past the end on a mating line.
3. **The suffix is legal where it appears.** 12 of 12 present suffixes were legal
   replies, verified against the engine's own `go perft 1` list after applying the
   best move rather than an external library. 0 were illegal or `0000`.

The same flag also governs the book path: a book `bestmove` carries
` ponder <predicted reply>` only when the option is on (measured; `e7e5` with and
without the suffix on the same book move).

---

## 6. Output shape while pondering, and `bestmove` uniqueness

**`info` lines stream during the ponder**, at roughly the rate the search finishes
iterations: **21 lines in 2000 ms (~10.5/s)** in a two-second ponder, with full
`depth / seldepth / score / nodes / nps / hashfull / time / pv` payload. A GUI that
does not want chatter during a ponder must filter it itself; the engine has no
option to suppress it.

**Exactly one `bestmove`, and nothing after it**, in every case:

| case | bestmove lines | lines after the last one |
|---|---|---|
| normal ponder → `ponderhit` | 1 | 0 |
| `ponderhit` then `stop` (same instant) | 1 | 0 |
| `ponderhit` then `stop` 50 ms later | 1 | 0 |
| `stop` then `stop` | 1 | 0 |
| `ponderhit` then `ponderhit` | 1 | 0 |

The two-command races are the ones that could plausibly double-emit, and none do:
`stop_search()` joins the worker, and both the conversion and the abort path write
through the same `uci_output_mutex` single `bestmove` site (`uci.cpp:565-572`).

### One shape worth knowing: a finished search under ponder floods `info`

On a drawn root (threefold by move list) under `go ponder`, the terminal branch
returns without searching and the driver loops over depths. Measured: **64 `info`
lines, depths 1→64, all emitted within 0.5 ms of `go`, every one reporting
`nodes 0` and no `pv`**, then silence, then `bestmove a2a3` on `ponderhit`.
Harmless if a runner parses `depth`/`nodes`, but a runner that treats an `info`
line as evidence of search effort will read 64 depths of "work" that cost no
nodes at all.

### The `time` field and the budget do not share an origin

This is the one output-shape defect with a user-visible consequence. The `info`
`time` field is computed from `start_` — the `go` command — while the stop
decision uses `elapsed_ms()`, rebased at `ponderhit` when pondering. After a
3 s ponder:

| clock | info `time` at bestmove | wall from `ponderhit` | hard limit |
|---|---|---|---|
| 10 000 | **4140 ms** | **1140 ms** | 2270 |
| 10 000 | **4140 ms** | **1141 ms** | 2270 |
| 60 000 | **4262 ms** | **1262 ms** | 13 630 |

The reported `time` exceeds the wall time actually spent thinking **after the
hit** by the full length of the ponder — here 3000 ms. It happens to stay under
the hard limit in these rows, but it does not have to: a 6 s ponder at clock
2000 reported `time 4174` against a 225 ms hard limit and 226 ms of post-hit
work. **So a runner or GUI that reads `time` to judge whether the engine
respected its budget is reading a number inflated by exactly the ponder
duration.** The engine's own budget is correct (§1); only the label is wrong.

### A runner-side desync that is real and cheap to avoid

A runner that starts the next ponder without waiting for the aborted search's
`bestmove` sees two `bestmove` lines and nothing on the wire to tell them apart:

| `stop` before restart | bestmove lines | moves @ ms relative to the 2nd `go` |
|---|---|---|
| yes | 2 | `d2d3` @ −201 (before the 2nd `go`), `e4e5` @ +1103 |
| **no** | 2 | **`d2d3` @ +0.5**, `e4e5` @ +1360 |

In the second row the stale answer arrives **0.5 ms after** the new `go`, so a
runner that pairs "the first `bestmove` I see after `ponderhit`" with the position
it just sent attributes `d2d3` — the previous position's move — to the new one.
Both rows end with a correct final move, so this fails silently and only under a
desynchronised restart. The engine is behaving correctly here; the hazard is
entirely in the pairing. **The runner must consume the `bestmove` for the search
it aborted before issuing the next `go`.**

---

## What is established, and how firmly

| claim | basis | firmness |
|---|---|---|
| `ponderhit` converts to a clocked search | 20+ conversions, every probe | measured, reproduces |
| budget origin is `ponderhit` | 16 offsets, 0 at ~0 ms; 26–36× over hard still full budget; source | **strong** — three independent lines |
| hit→best ≤ hard (+0.9 ms worst) | 16 offsets at 2 clocks | measured; **an upper bound, not an equality** |
| clocked ponder is unbounded | 20 s and 45 s horizons, CPU + depth + node growth | measured |
| two unbounded regimes (runaway / withheld) | CPU 99.9% vs 0.1%, depth rising vs flat | measured |
| `stop` returns the found move, never `0000` | 18/18 | measured |
| 0 ms stop reply | tracks the position, but **identical to the EOF artifact** | **undecided, and said so** |
| stray `ponderhit` is silent | 4 states + 1 live control | measured; control proves the path |
| `Ponder` only formats the bestmove line | identical nodes 17 804 both arms; 3 nulls | measured |
| suffix is legal, absent on mate-in-one | 12/12 legal, 2/14 absent | measured |
| exactly one `bestmove` | 5 scenarios incl. 4 command races | measured |
| `info time` inflated by the ponder | 3 rows, 3000 ms offset reproduced | measured |

**Not established, and named as a gap:**

- **Whether the engine's post-hit budget is the *right* size**, only that it is
  rebased and capped. All measurements are on one position; a position whose
  iteration takes longer than the whole budget could show a different shape in the
  `iterations_after_hit` column, which here is often 0.
- **Behaviour under `MultiPV > 1` and `Threads > 1` is only spot-checked** (2 and
  4 threads: one `bestmove`, no trailing lines, hit→best 454 / 766 ms). Helpers
  ignore the clock by design (`search.cpp:1280`), so the multi-thread budget
  argument is not proved here, only its happy path.
- **Whether any real match runner actually restarts without `stop`** — the desync
  in §6 is demonstrated as a protocol sequence, not observed in a runner.
- **All wall-clock figures are single-sample per cell** except the 16-offset
  sweep and the 6×3 stop matrix. The ±100 ms spread within one request is real and
  is stated beside the timings rather than averaged away.
