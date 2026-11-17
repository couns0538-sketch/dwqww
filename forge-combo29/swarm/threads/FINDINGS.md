# Threads above one — first measurement on the audit base

Base commit `6b98f217`. Branch `swarm/threads`. Machine: **4 cores**, Intel Xeon (KVM),
one hardware thread per core (`Thread(s) per core: 1`), 15 GB RAM, no SMT.

**Read this first: `Threads 8` on this box is 2.0x oversubscribed.** Every Threads 8
row below is a claim about eight software threads on four cores. It is *not* a claim
about eight cores, and nothing here licenses one.

Every number in this file is printed by a script in `scripts/` reading a file in
`evidence/`. Where a figure appears without a script behind it, the sentence says so.

---

## 0. The gate, and what the gate does and does not cover

The four honesty pins were checked **before any measurement**, on the binary these
results come from (sha256 `e06310ec…`), at default options, Threads 1:

| pin | expected | got |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| perft 5 | 4,865,609 | **4,865,609** |

`scripts/pins.py`, evidence in `evidence/pin_*.raw.txt` and `pin_summary.json`.
Gate: **PASS**.

### The gate does not cover `Threads` — and this is the first finding

`bench` builds its **own** searcher: `forge::Searcher bench_searcher(16);`
(`src/uci.cpp:611` on the base). `Searcher`'s second parameter `threads` defaults to `1`
(`include/forge/search.hpp:573`). So **`bench` never reads the `Threads` option at all.**

Measured, not inferred — `scripts/pins_by_threads.py`, `evidence/pins_by_threads.json`:

| pin | Threads 1 | Threads 2 | Threads 4 | Threads 8 |
|---|---|---|---|---|
| bench 11 | 312,866 | 312,866 | 312,866 | 312,866 |
| bench 13 | 862,329 | 862,329 | 862,329 | 862,329 |
| bench 16 | 3,024,920 | 3,024,920 | 3,024,920 | 3,024,920 |
| perft 5 | 4,865,609 | 4,865,609 | 4,865,609 | 4,865,609 |

3 repeats each, 16/16 cells reproducible. **The identical bench numbers across thread
counts are not evidence that threading is node-neutral.** They are evidence that
bench is single-threaded whatever you label it — the "a label is not a measurement"
trap (findings §7 trap 15) in a new place. `perft` is also single-threaded, but for a
different reason: the UCI `perft` branch runs on the calling thread and never touches
`searcher` (`src/uci.cpp:489-513`).

**So the four pins are a Threads-1 gate and nothing else.** A threaded bench number
cannot move, which means it also cannot fail, which means it certifies nothing about
Threads > 1.

### Controls that prove `Threads` reaches the engine at all

Before believing any threaded result, three controls (`scripts/multithread_control.py`,
`evidence/controls.json`), each with a direction that must come out the other way:

| claim | test | result |
|---|---|---|
| `Threads 4` starts helpers at MultiPV 1 | node count must differ from Threads 1 | **PASS** — T1 five identical at 80,137; T4 varies 127,563–262,164 |
| `Threads 4` starts **no** helpers at MultiPV 3 | MultiPV 3 must be *identical* at T1 and T4 | **PASS** — both five identical at 384,112 |
| that second test can fire at all | the MultiPV 1 control must differ | **PASS** — it does |

**`Threads × MultiPV > 1` silently runs single-threaded.** Confirmed from behaviour,
not just from the source line: `single_threaded = workers_.size() == 1 ||
worker_limits.multipv > 1` (`src/search.cpp:2711`) and `all` is cut to
`workers_.front()` when `multipv > 1` (`src/search.cpp:2700`). A "Threads 4 at
MultiPV 3" measurement is a Threads 1 measurement wearing a threaded label. Anyone
with a MultiPV corpus should assume their Threads setting did nothing.

**I had to fix this control once.** My first version required bench *wall time* to be
bit-identical at T1 and T8 and reported FAIL on a correct engine, because wall time is
scheduler noise. The criterion is now nodes-identical AND no speed-up (T1/T8 time ratio
0.952, i.e. none) — a two-sided test instead of an equality on a noisy quantity.

---

## 1. Determinism — the inherited claim is CONFIRMED, and it is worse than stated

The report's rule "`Threads 1` for anything reproducible; above it every position
differs between runs" was inherited, not measured. **It is now measured, and it holds.**

`scripts/determinism.py` + `scripts/analyse_det.py`, evidence
`evidence/det_depth12.jsonl` (480 searches) and `evidence/det_nodes100k.jsonl` (480).
40 positions (first 40 of set G), 3 repeats each, cold (`ucinewgame` + `position`
before every search), Hash 64.

**Q1 — reproducible AT a thread count** (do repeats of the same search agree?):

| threads | `go depth 12`: nodes | score | bestmove | `go nodes 100000`: nodes | score | bestmove |
|---|---|---|---|---|---|---|
| **1** | **0/40** | **0/40** | **0/40** | **0/40** | **0/40** | **0/40** |
| 2 | 40/40 | 37/40 | 20/40 | 40/40 | 40/40 | 19/40 |
| 4 | 40/40 | 39/40 | 13/40 | 40/40 | 39/40 | 19/40 |
| 8 | 40/40 | 38/40 | 17/40 | 40/40 | 40/40 | 22/40 |

Threads 1 is **exact**: 0 of 40 positions differ in node count, score, or move, at both
limits, over 120 searches. That half of the inherited claim is confirmed cleanly.

Above Threads 1, **every** position differs in node count (40/40 at every thread count
and both limits) and nearly every one differs in score. So the inherited rule is not
merely true — it is true at maximum strength on this fixture set.

**Q2 — same AS Threads 1** (`analyse_det.py` prints this separately because it fails for
a different reason): nodes agree on **0 of 40** at every thread count, which is expected
arithmetic — the reported node field above Threads 1 is a **sum over workers**
(`src/search.cpp:2700`). Bestmove agrees on 26/40 (T2), 27/40 (T4), 27/40 (T8).

### Magnitude, because a rate is not a size

`scripts/score_spread.py`, evidence `evidence/score_spread.txt`:

| limit | threads | median score spread across 3 repeats | max score spread | median node ratio max/min |
|---|---|---|---|---|
| depth 12 | 1 | **0 cp** | **0 cp** | **1.00** |
| depth 12 | 2 | 38 cp | 2,091 cp | 1.66 |
| depth 12 | 4 | 28 cp | 2,109 cp | 1.63 |
| depth 12 | 8 | 24 cp | 438 cp | 1.49 |
| nodes 100k | 1 | **0 cp** | **0 cp** | **1.00** |
| nodes 100k | 4 | 26 cp | 630 cp | 1.80 |
| nodes 100k | 8 | 32 cp | 802 cp | 2.01 |

The Threads 1 row is the control: spread exactly 0. A median 24–38 cp swing on a single
position between two runs of the same command is large next to the 42 cp noise floor
recorded for a *different* measurement in §7 — so a threaded score is not a number a
training corpus can use as a label.

### The one thing that is stable above Threads 1

**`script/drawn_root.py` below shows the drawn-root path is fully stable.** And of the
40 positions, the ones where bestmove changed are often near-ties — but see §4, where I
measure that properly and have to **decline** the conclusion.

---

## 2. Drawn-root bail — the bail is unaffected by threading

`scripts/drawn_root.py`, evidence `evidence/drawn_root.json`. 5 repeats per cell, all
four thread counts. Fingerprint of the bail: every `info depth` line has `nodes 0` and
an **empty pv** (trap 21's "is not a no-info path" note respected — it emits a line per
depth, and this script counts them).

| fixture | how delivered | Threads 1 | Threads 8 | score / move |
|---|---|---|---|---|
| repetition (3-fold) | **move list** | BAIL | **BAIL** | cp 0, `a2a3` |
| same board | **FEN** | SEARCH | SEARCH | cp 24, `d2d4` |
| fifty-move (hmc 100) | FEN | BAIL | **BAIL** | cp 0, `h1a1` |
| insufficient K v K | FEN | BAIL | **BAIL** | cp 0, `e3d2` |
| insufficient KB v K | FEN | BAIL | **BAIL** | cp 0, `f1e2` |
| insufficient KN v K | FEN | BAIL | **BAIL** | cp 0, `f1d2` |

**40/40 cells identical in score and move at every thread count.** The bail fires
before any helper can affect the returned move: the whole root-drawn block sits at
`src/search.cpp:2251-2275` and returns from `Worker::search` before the iterative-deepening
loop at `src/search.cpp:2392`; only the main worker's `SearchInfo` is returned by
`Searcher::search`. A threaded search
**cannot** return a different bestmove on a drawn root — measured, not argued.

Two controls that make this a test rather than a tautology:

- **`ctrl_fifty_99`** (hmc 99, one below the threshold) must search: **SEARCH at
  Threads 1 and 8**, cp 0, `h1h5`. So "bails" is not "answers with an empty pv".
- **`ctrl_repetition_1rep`** (one repetition, not three): **SEARCH** at both.
- The FEN/move-list pair is the sharpest: **the same board bails by move list and
  searches by FEN at every thread count**, confirming trap 2d on this build and showing
  the bail depends on history, not on the position.

The Threads 1 and Threads 8 columns agree everywhere, which is the point: this is the
one behaviour in the whole audit that threading leaves completely alone.

---

## 3. Book and clock — thread-invariant, with both proofs of the null

`scripts/book_clock.py`, evidence `evidence/book_clock.json`.

**Book.** The book is consulted in the UCI loop *before* the searcher is called
(`src/uci.cpp:527`), so `Threads` cannot change whether it fires. Measured: **9 of 15
searches booked at Threads 1, 2, 4 and 8 — identical count.** The book path's footprint
(`info string book move`, zero `info depth` lines) was seen at every thread count, so the
zero-difference is not an empty corpus.

**Clock.** `go movetime 300` wall time: median **0.2907 s (T1), 0.2909 (T2), 0.2910
(T4), 0.2932 (T8)** — inside 2.5 ms across a 2x oversubscribed box. And the clock
actually bound: the request was 300 ms and every arm returned at ~290 ms, so this is not
a search that finished early and pretended.

### One thing I have to withdraw here

My first book comparison reported "book moves differ across thread counts". **That was
my instrument, not the engine.** The book move is chosen by `Book::probe` using
`book_rng`, which is seeded from `steady_clock::now()` (`src/uci.cpp:162`), and `Book
Variety` defaults to 30 — so the book is *designed* to return different moves on repeat
runs at **any** thread count, including Threads 1.

Measured (`Book Variety 0`, 5 repeats per position, per FEN):

| Book Variety | Threads 1 | Threads 2 | Threads 4 | Threads 8 |
|---|---|---|---|---|
| 0 | 0/5 vary | 1/5 vary | 1/5 vary | 1/5 vary |
| 30 (default) | 3/5 vary | 4/5 vary | 4/5 vary | 3/5 vary |

**Threads 1 varies 3 of 5 at the default setting** — so variety, not threading, is the
cause. The 1/5 residue at variety 0 is on a position that does **not** book at all
(`rnbqkbnr/pppppppp/... b KQkq`, Black to move: the book fires on the mover's own clock,
trap 19, and `btime` is present but the black-side book lookup misses), so it is the
*search* varying, not the book. That is consistent with §1 and not a book finding.

**Therefore: book behaviour is unchanged by threading, and any harness comparing book
moves across runs must pin `Book Variety 0` or it will measure its own RNG.** The
earlier "book moves differ" row is withdrawn.

---

## 4. What threading buys, and what it costs — the headline

Two arms, deliberately reported differently because they answer different questions
(`scripts/walltime_depth.py`, `scripts/fixed_depth_cost.py`, evidence
`evidence/walltime_d16.json`, `evidence/fixed_depth_cost.txt`). 20 positions, depth 16,
2 repeats, Hash 64.

### Fixed depth: threading is SLOWER, and more threads is more slowly

| threads | median wall | summed nodes | node rate/s | node inflation | wall cost vs T1 |
|---|---|---|---|---|---|
| 1 | 0.171 s | 268,063 | 1,563,191 | 1.00 | 1.00 |
| 2 | 0.178 s | 657,976 | 3,688,712 | 2.45 | **1.04** |
| 4 | 0.213 s | 987,166 | 4,630,284 | 3.68 | **1.24** |
| 8 | 0.342 s | 1,431,065 | 4,182,417 | 5.34 | **2.00** |

The decomposition `wall_cost = inflation / rate_ratio` closes to 1.1e-16 (printed by the
script as a check, not asserted). Read it plainly:

- **Threads 4 needs 1.24x the wall time of Threads 1 to reach the same depth**, because
  it searches **3.68x the nodes** to buy only **2.96x the node rate**.
- **Threads 8 needs 2.00x the wall time**, because it searches 5.34x the nodes for 2.68x
  the rate — the rate *falls* from Threads 4, which is what 4-core oversubscription
  looks like.

**So on this engine, at fixed depth, `Threads` is a pessimisation at every value above
1.** That is not what an SMP search is supposed to do; the node inflation outruns the
rate gain.

### Fixed time: it does get deeper, and only at Threads 4

The fair test of an SMP search is what it reaches in a fixed clock. `scripts/
depth_reached.py`, `go movetime 1000`, 40 positions, evidence `evidence/depth_reached.json`:

| comparison | positions | mean Δdepth | deeper | same | shallower | sign test |
|---|---|---|---|---|---|---|
| T2 vs T1 | 40 | −0.175 | 17 | 7 | 16 | **p = 1.000** |
| **T4 vs T1** | 40 | **+1.375** | **24** | 9 | 7 | **p = 0.0033** |
| T8 vs T1 | 40 | −0.325 | 16 | 5 | 19 | **p = 0.736** |

`scripts/sign_test.py`, which carries the `min(k, n−k)` reflection, a
`p(k,n) == p(n−k,n)` assertion on every run, a floor and ceiling assertion, a
direct-enumeration cross-check, **and a negative control that feeds it a saturated
function and requires rejection** — all passing (`--selftest`).

**Only Threads 4 is resolved.** Threads 2 and Threads 8 are near-even splits and are
**not** "no effect": their intervals are wide and the honest statement is *no effect
detected at n=40*. Threads 8 is *not* faster than Threads 1 despite 2x the threads.

**The two arms are consistent and that is the finding**: Threads 4 buys about +1.4 ply
in a second, while costing 24% more wall time per ply at fixed depth. Both are true at
once because the extra nodes go to *parallel search overhead*, not to depth.

### Threads 8 is oversubscribed — say it every time

4 cores, 8 software threads. The Threads 8 row is a claim about 2x oversubscription. Its
node rate (2.68x) is *below* Threads 4's (2.96x) and its wall cost is double. **Do not
read "Threads 8 is slower than Threads 4" as a property of 8 cores; on this box it is a
property of 8 threads on 4 cores.**

---

## 5. `go nodes N` under threading — the budget holds, the search may not iterate

### The aggregate does not overshoot by the thread count

The concern was that each worker might treat N as its own budget. It does not:
`node_limit_specified_` is true on helpers (they have no `parent_worker_`), and
`should_stop_with` compares **`total_nodes()` — a sum over all workers — against
`node_limit_`**. Measured on 20 positions x 3 budgets x 2 repeats
(`scripts/node_budget.py`, `evidence/node_budget.json`):

| threads | N=10k ratio (median/max) | N=100k | N=1M | searches reporting > N |
|---|---|---|---|---|
| 1 | 0.603 / 0.993 | 0.742 / 0.975 | 0.807 / 0.967 | 0 / 120 |
| 2 | 0.723 / 0.952 | 0.827 / 0.987 | 0.820 / 0.983 | 0 / 120 |
| 4 | 0.690 / 0.981 | 0.759 / 0.992 | 0.743 / 0.982 | 0 / 120 |
| 8 | 0.624 / **1.000** | 0.649 / 0.993 | 0.820 / 0.998 | **1** / 120 |

**The budget is respected.** The reported total *under*-shoots, because the stop lands
mid-iteration and the reported node count is the last *completed* iteration's — the same
reason a `softnodes` search undershoots in the record. There is **one** row over budget
by exactly **1 node** out of 480 searches (`T8, N=10000, max 10001`), which is a race in
the last increment, not a per-worker budget. **This is a null with a footprint**: the
node counts are visibly nonzero and thread-dependent, so the code ran.

### The real finding: a small node budget at Threads 8 can complete ZERO iterations

`scripts/zero_info.py`, evidence `evidence/zero_info.json`. 20 positions, 3 repeats per
cell, interactive driver reading to `bestmove`:

| threads | N=1,000 | N=5,000 | N=10,000 | N=50,000 |
|---|---|---|---|---|
| **1** | **0/60** | **0/60** | **0/60** | **0/60** |
| 2 | **45/60** | 17/60 | 3/60 | 0/60 |
| 4 | 31/60 | 10/60 | 5/60 | 0/60 |
| 8 | 17/60 | 12/60 | 2/60 | 0/60 |

**At Threads 2 with `go nodes 1000`, 45 of 60 searches returned a `bestmove` with not
one `info depth` line.** This is not the piped-EOF fabricated move (trap 1/3a): the
driver keeps the process alive and reads to `bestmove`, and the Threads 1 control on the
same fixtures and budgets is **0 of 60**.

**Mechanism, proved rather than inferred** (`scripts/first_candidate.py`,
`evidence/first_candidate.json`): the reply is the engine's **first root candidate,
unsearched**. 7 of 7 zero-info replies across 7 fixtures x 4 thread counts returned the
first move in the engine's own generation order (from `go perft 1`), and **every one was
a move the searched answer did NOT pick**:

| position | engine's first candidate | Threads 1 answer | Threads 8 zero-info answer |
|---|---|---|---|
| `1r6/2k2pp1/…` | `d5d4` | `e5e4` | **`d5d4`** |
| `8/6k1/3p4/…` | `f4f5` | `e4f5` | **`f4f5`** |
| `8/5p2/8/pp1pkpKp/…` | `b2b3` | `g5h5` | **`b2b3`** |

Cause: `emit(depth, …)` runs only after a root iteration **completes**, the budget is
compared against the sum over workers, and at Threads 2+ the helpers can spend a small
budget inside iteration 1 before the main worker finishes it. `result.best_move` then
falls back to `root_candidates.front()` (`src/search.cpp:2640`).

**Why this matters beyond its own size.** The audit's *only* reliable detector for a
broken piped harness is "`info depth` line count of zero" (trap 3a, 60 of 60). **A
correctly-driven Threads > 1 search on a small node budget produces the same signature.**
So that detector now has a false-positive class, and a harness that rejects zero-info
replies will discard real threaded results — or, worse, treat a piped run as valid
because one position emitted a line. A `go nodes` corpus at Threads > 1 and N ≲ 50k
contains unsearched moves labelled with a node budget.

---

## 6. Thread-safety — no race found, with the two proofs that make the null mean something

### Static audit: the one lazy static is unreachable from helpers

`src/bitboard.cpp:139-143` uses `std::call_once` (the historical race is fixed on this
base — not re-reported as live). Searching for the same shape elsewhere:

- **One function-local static remains**: `src/nnue.cpp:92` `static Weights instance =
  make_builtin();` in `live_weights()`.
- It is **read** from worker threads via `apply_and_evaluate` → `weights()`
  (`src/nnue.cpp:466`), which is safe: C++11 guarantees thread-safe initialisation of a
  function-local static, and the read is after initialisation.
- Its two **mutating** call sites (`load_file`, `uci.cpp`'s NnueFile handler) run in the
  UCI thread, and every `setoption` begins with `stop_search()` (`src/uci.cpp:258`) which
  `join()`s the worker (`src/uci.cpp:176`). So no mutation can overlap a helper.
- No other mutable namespace-scope table is written after startup.

That makes a race *unlikely*, which is not the same as absent — hence the sanitizer.

### TSan: 0 reports on the clean build, and the runner is proved able to see a race

Two proofs, both required, and I got the first one wrong before getting it right:

1. **PROBE** — `scripts/tsan_run.py probe` builds a deliberately racy two-thread program
   and runs it through **the same runner**. It must report. **It reports 1 warning.**
2. **PLANTED** — a scratch copy of the engine with an unsynchronised global
   (`forge_planted_counter`) incremented on every node by every worker, built the same
   way (TSan, `nm -C | grep -c __tsan_` = **21**), run through the same runner at
   Threads 4: **25,960 ThreadSanitizer warnings**, stack pointing at
   its own `Worker::search` node path on threads T2 and T4 (the plant lives in the scratch
   copy, so no line in the audited base is cited for it).

Then the clean build, same runner:

| run | threads | positions | depth | TSan warnings | summed nodes (proof it searched) |
|---|---|---|---|---|---|
| `tsan_clean_t4.json` | 4 | 5 | 10 | **0** | 22,464–82,259 |
| `tsan_clean_t4_20.json` | 4 | 20 | 12 | **0** | 72,554–253,826 |
| `tsan_clean_t8_20.json` | 8 | 20 | 12 | **0** | 90,094–407,529 |

`TSAN_OPTIONS` was cleared of inherited values and set explicitly; stderr was captured
separately (TSan writes to stderr, and a harness reading only the info stream misses it
— the §7 "a harness that reads one stream misses the diagnostic" family).

**I have to report a fault in my own instrument here.** My first TSan run reported
"0 warnings" on the *planted* build. The cause: I built the `TSAN_OPTIONS` environment
dict and then never passed it to `Popen`, so TSan had no `log_path`, my counter read a
file that was never written, and **it counted nothing and printed 0** — an
absence-read-as-a-pass, in the tool built to detect exactly that class. It was caught
only because the planted build *should* have fired. The fix is the explicit `env=` in
`scripts/tsan_run.py` plus the `probe` mode that must fire on every run.

**What this establishes**: no data race detectable by TSan in the threaded search on
these fixtures. **What it does not**: TSan finds races it is scheduled through, not all
races; a race on an unscheduled interleaving, or in a path these 45 searches did not
reach (e.g. `go infinite` + `stop`, ponder, position changes mid-search), is not
covered. `stop`/`ponderhit`/`ucinewgame` racing a live search was **not** tested here —
area 4 job 3 in the swarm brief, and it is unmeasured by me.

### Changing `Threads` between searches: 200 switches, no illegal move

`scripts/thread_switch.py`, evidence `evidence/thread_switch.json`, seed 1017001. 200
searches cycling Threads 1/2/4/8, 20% with `ucinewgame`, depth 10, legality checked
against **the engine's own** `go perft 1` move set for the same FEN:

- **0 illegal bestmoves of 200.**
- **0 zero-info replies of 200** — because depth 10 is far above the zone where §5 bites.
- Median nodes rise with the declared thread count (`T1 20,499 < T2 35,492 < T4 64,269`),
  so the pool really does grow rather than the label changing alone. The fixed-Threads-4
  control's median (55,275) sits inside that range, as it should.

---

## 7. Predictions vs results — including the ones I got wrong

`PREDICTION.md` was committed alone, before the first measuring command.

| id | prediction | outcome |
|---|---|---|
| P1 | 40/40 differ in nodes above T1; ≥30/40 in score; ≥3/40 in move at T8 | **HOLDS** (40/40 nodes, 38/40 score, 17/40 move) |
| P2 | 0/40 at Threads 1 | **HOLDS** (0/40, 120 searches) |
| P3 | score differs more often than move, by ≥3x | **HOLDS** at T4 (39 vs 13) and T2 (37 vs 20); **weaker at T8** (38 vs 17, ratio 2.2) |
| P4 | drawn-root bail 40/40 identical at every thread count | **HOLDS** (40/40, all fixtures) |
| P5 | 0 differences in book behaviour | **HOLDS** on *booked-ness* (9/15 at every count); the *move* varies from `Book Variety`, which I first misread as a thread effect |
| P6 | bench bit-identical at every thread count | **HOLDS, and for a reason that makes the row worthless** — bench ignores `Threads` |
| P7 | Threads 4 wall time 1.5x–3.0x faster than Threads 1 | **KILLED.** Measured **1.24x SLOWER** at fixed depth. My prediction assumed an SMP search like a normal engine; this one's node inflation outruns its rate gain |

**P7 is the prediction I got wrong and it is the most useful result in the file.** I
predicted a speed-up because that is what `Threads` normally buys; the measurement says
the opposite, and the decomposition says why (3.68x nodes for 2.96x rate).

---

## 8. Withdrawn

1. **"Book moves differ across thread counts"** — withdrawn; caused by `book_rng`
   seeded from the clock plus default `Book Variety 30`, and reproduces at Threads 1
   (3/5 positions vary). Section 3.
2. **"Threads 8 is slower than Threads 4, therefore 8 cores is slower than 4"** — never
   claimed, and must not be inferred: this box has 4 cores and Threads 8 is 2.0x
   oversubscribed. Every T8 row is scoped that way.
3. **My first multithread control** reported FAIL on a correct engine because it
   required bench wall time to be bit-equal. Replaced by a two-sided criterion.
4. **My first TSan run** reported 0 warnings on a build with a planted race, because
   `TSAN_OPTIONS` never reached the subprocess. Fixed and re-proved with a probe mode.
5. **"Threaded moves are worse moves"** — I built the measurement
   (`scripts/move_quality.py`) and **decline the conclusion**. 13 move flips, pinned
   `searchmoves` gaps: median +4 cp, 6/13 within 10 cp, 3/13 worse by >10 cp. But
   **7 of 13 gaps change SIGN at depth+4** and the pinned measurement's own noise floor
   is 0 cp (`scripts/pinned_noise.py`, 26 cells, all identical), so the gaps are real
   *at their depth* and **not stable under deepening** — horizon artefacts, not a
   quality ordering. Recorded as measured-and-unresolved, not as a finding.

---

## 9. What I did NOT do

- **No SPRT / no Elo.** Nothing here says whether threaded play is stronger. A
  fixed-clock depth gain of +1.4 ply at Threads 4 is not an Elo claim.
- **No ponder, no `go infinite` + `stop` race test, no mid-search `setoption` race
  test.** TSan coverage is depth-limited searches only.
- **No Threads 16+.** 4 cores; 8 is already 2x.
- **One machine, one microarchitecture.** The wall-time and node-inflation numbers are
  properties of this 4-core Xeon. §6's rule in the record applies: **if the hardware
  changes, re-measure the model, not the table.**
- **No `Threads` × `Hash` interaction.** Hash was 64 MB throughout; §5's zero-info rate
  is measured at Hash 64 only.
- **No claim about why node inflation outruns rate gain.** The behaviour is measured;
  the mechanism is not. The record's open lead (`BARE_KING_LMR_CAP`, §9) suggests
  clamped reductions propagating through the pruning cascade, but I did not test it.

---

## 10. What to tell an owner in one paragraph

`Threads 1` is exactly reproducible and `Threads > 1` is not — score swings of 24–38 cp
median and up to 2,109 cp on a single position between two identical runs. Use
`Threads 1` for anything a corpus or a gate depends on. Threading is **not a speed-up on
this engine at fixed depth** (Threads 4 is 24% slower, Threads 8 is 2x slower on a
4-core box) but it *does* reach about +1.4 ply deeper in a fixed second at Threads 4,
which is the only resolved threading gain in the file. The drawn-root bail is completely
unaffected. `bench` and `perft` ignore `Threads` entirely, so bench numbers certify
nothing about threading. `Threads` with `MultiPV > 1` silently runs single-threaded. And
a `go nodes` budget below ~50k at Threads 2+ can return an unsearched first-legal move
with no `info depth` line — 45 of 60 at Threads 2, N=1000 — which is the same signature
the audit uses to detect a broken piped harness.
