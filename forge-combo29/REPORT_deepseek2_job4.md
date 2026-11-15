# deepseek2, job 4 report: R4b and R5

## 1. First line

**Both repairs are written and proven: 2 of 2.** R4b replaces R4 with the corrected value rule; R5
removes the short-clock cliff. Both apply alone on 6b98f217 and all five patches (R1, R2, R3, R4b,
R5) apply together in either order.

**The three builds and a negative clock.** On `go wtime -50 btime -50` from the start position after
`e2e4`:

| build | what happens | why |
|---|---|---|
| **unpatched** | `bestmove` in **2 ms**, 29 nodes | `parse_clock_ms` clamps −50 to 0; "no time left" is an immediate answer |
| **R4 as delivered (job 3)** | **no `bestmove` for 5 s**, 3.8 million nodes, `stop` needed | my rule made a negative value mean "parameter absent", i.e. an unlimited search |
| **R4b** | `bestmove` in **1 ms**, 29 nodes | old clamping restored for a complete integer |

So Fable's reading is right and the flaw was in the job text; R4b repairs it. Same story for
`go movetime -1`, `go depth 0`, `go depth -3`: unpatched and R4b answer at once, R4 does not.

**R5:** the cliff is real but **only with more than one thread** — measured below, with `Threads 1`
the engine never takes the unsearched path at any clock from 1 to 50 ms.

## 2. R4b — the corrected value rule

**Patch** `evidence/R4b_go_parser.patch.txt`, `src/uci.cpp` only, **94 changed lines (+66/−28)**,
against clean 6b98f217. It replaces R4 and does not sit on top of it.

**The rule, as delivered.**
- next token missing, or a `go` keyword → parameter absent, **nothing consumed**;
- next token not a complete integer (letters, trailing junk, a second sign) → parameter absent, token
  **consumed**;
- next token is a complete integer → **the old clamping**: clocks and `movetime` through
  `parse_clock_ms` (negative → 0, too large → the ceiling); `depth` → `clamp(v,1,64)`; `movestogo` →
  `max(1,v)`; `mate` → `clamp(v,0,32)`; `nodes`/`softnodes` → a negative value or 0 becomes **1 node**
  (bounded, immediate), too large stays absent as before.

**One addition the job text did not ask for, and why.** R4b as specified still failed the job's own
"0 past their clock" requirement: `go movetime 99999999999999999999 wtime 2000 btime 2000` clamps
`movetime` to the ceiling, which is an effectively infinite search, while the line carries a 2000 ms
clock. I added one rule at the end of `parse_limits`: **if both `movetime` and a clock for the side to
move are present, `movetime` is capped at that clock.** A `movetime` is a request to think exactly
that long; it may not outlast the clock the same line gives. This is 4 lines, it is called out here
rather than buried, and it is the only place where I went beyond the job text. Without it, R4b
reintroduces the job-2 finding it was supposed to keep repaired.

**Known answers, all three builds** (`evidence/R4b_known_answers.json`; "at once" = `bestmove` within
150 ms without `stop`):

| line | unpatched | R4 (job 3) | R4b |
|---|---|---|---|
| `go wtime -50 btime -50` | at once, 1-2 ms | **NO, 5001 ms, stop** | at once, 1 ms |
| `go wtime 0 btime 0` | at once, 1 ms | at once, 1 ms | at once, 1 ms |
| `go movetime -1` | at once, 2 ms | **NO, 5001 ms** | at once, 2 ms |
| `go depth 0` | at once, 1 ms | **NO, 5001 ms** | at once, 1 ms |
| `go depth -3` | at once, 1 ms | **NO, 5001 ms** | at once, 1 ms |
| `go nodes -1` | **NO, 5001 ms** | **NO, 5001 ms** | at once, 1 ms |
| `go nodes 0` | at once, 1 ms | at once, 1 ms | at once, 1 ms |
| `go wtime btime 50` | **NO, 5001 ms** | at once, 2 ms | at once, 1 ms |
| `go movestogo 0 wtime 2000 btime 2000` | 663 ms inside clock | 162 ms inside clock | 644 ms inside clock |
| `go mate 0` | no answer in 5 s | no answer in 5 s | no answer in 5 s |
| `go btime wtime 2000 btime 2000` | 183 ms | 175 ms | 184 ms |
| `go movetime 99999999999999999999 wtime 2000 btime 2000` | **NO, 5001 ms** | at once, 174 ms | **1991 ms, inside its 2000 ms clock** |

`go mate 0` is identical in all three: `mate_moves` 0 means "no mate limit", so the line is a plain
`go` and searches until stopped. That is what the field means (`search.cpp:1452` and the `mate_depth`
computation both treat 0 as "no limit"), so I report it as behaviour, not as a fault. The last row is
the one the job text and its own requirement disagree on; R4b takes the requirement.

**The 57-row matrix again** (`evidence/R4b_partC_matrix.json`): **0 fails**, and no clocked line runs
past 2200 ms. The slowest clocked answer is the `movetime` huge row at 1991 ms, i.e. its own 2000 ms
clock. `go infinite` still needs `stop`.

## 3. Part B — a table test of `parse_limits` itself

**`table_test.cpp`** includes `src/uci.cpp` as text with `main` renamed by a macro, so `parse_limits`
is reachable and everything keeps internal linkage. It links the engine's other objects only for
`Board`. 64 rows, each checking the exact fields `time_ms`, `increment_ms`, `movetime_ms`, `depth`,
`nodes`, `nodes_specified`, `soft_nodes`, `moves_to_go`, `mate_moves`, `infinite`.

| build | rows | result |
|---|---|---|
| **R4b** | 64 | **64 pass, 0 fail** |
| **unpatched** | 64 | **41 pass, 23 fail** |

The 23 failing rows on the unpatched file are the ones R4b repairs, listed in
`evidence/table_unpatched_failures.txt`; the important ones:

- `go btime wtime 2000 btime 2000` → `time_ms` −1 (the clock is swallowed);
- `go movetime wtime 2000` / `go winc wtime 2000 btime 2000` / `go mate wtime 2000 btime 2000` /
  `go nodes wtime 2000 btime 2000` → `time_ms` −1;
- `go depth` (nothing after it) → `depth` 1, i.e. a value was invented from nothing;
- `go wtime` → `time_ms` 0, again invented;
- `go depth abc` / `go depth 7x` / `go depth +-7` → `depth` 1;
- `go nodes -1`, `go nodes 0`, `go softnodes 0` → `nodes` 0 with `nodes_specified` true (a zero-node
  search) instead of one node;
- `go wtime 500 movetime 2000` → `movetime_ms` 2000 (the clock ignored);
- `go wtime 2000 btime 2000 movetime 99999999999999999999` → `movetime_ms` at the ceiling.

**Power of the table itself.** Run with `--self-check` it evaluates a row whose expected `time_ms` is
1 where the parser gives 2000, and reports
`self-check row (deliberately wrong) was REJECTED as required: time_ms got 2000 want 1`. So a wrong
expectation does fail the table; the 64 passes are not free.

**What I am not sure about here.** The table asserts my reading of "the old clamping", including
`movestogo 0` → 1 and `nodes 0` → 1. Both are what R4b does; if Fable wants `nodes 0` to stay a
zero-node search, that is one line in `read_nodes`.

## 4. R5 — the short-clock cliff

**Patch** `evidence/R5_hard_limit_emergency.patch.txt`, `src/search.cpp` only, **12 changed lines
(+6/−6)**.

**What it does.** The empty-reserve emergency block and the "hard limit already passed" branch are the
same situation, so they become one: `clock_already_spent` is true when the reserve is not empty, the
worker is not waiting to ponder, `hard_limit_ms_ > 0` and `elapsed_ms() >= hard_limit_ms_`. When it
is true, the existing emergency path runs — play the hash move if it is legal, otherwise one ply with
at most 2000 nodes — instead of returning `root_candidates.front()` unsearched.

**Why it cannot overrun a clock the old code kept.** Both paths end at the same clock: the emergency
path sets `node_limit_ = 2000` and `max_depth = 1`, and `should_stop_with` still returns true at
`elapsed_ms() >= hard_limit_ms_` for the main worker (search.cpp:1285–1288), so the emergency ply is
cut by the same condition that cut the unsearched answer. The work it adds is bounded by 2000 nodes.
Measured: at `wtime 1` with `Threads 64` the worst answer time after the patch is **1.5 ms** against
1.9 ms before, and at `Threads 1` 1.4 ms against 1.6 ms — no answer is later.

**Measurement, step 1** (`evidence/R5_cliff_before.json`, `evidence/R5_cliff_after.json`; 50 checked
mate-in-one positions, fresh process each, `Move Overhead 10`, `OwnBook false`, `go wtime W btime W`):

| Threads | wtime | mate move before | mate move after | 0-node answers before | after |
|---|---|---|---|---|---|
| 1 | 1 … 50 (all 11 clocks) | **50/50 at every clock** | 50/50 | 0 | 0 |
| 8 | 1, 5, 9, 10 | 50/50 | 50/50 | 0 | 0 |
| 8 | 11 | **25/50** | **38/50** | 31 | 21 |
| 8 | 12 | 32/50 | 36/50 | 21 | 17 |
| 8 | 13 | 29/50 | 34/50 | 29 | 20 |
| 8 | 15 | 26/50 | 40/50 | 28 | 18 |
| 8 | 20 | 30/50 | 33/50 | 28 | 21 |
| 8 | 30 | 24/50 | 34/50 | 34 | 22 |
| 8 | 50 | 50/50 | 50/50 | 0 | 0 |
| 64 | 1 … 10 | 50/50 | 50/50 | 0 | 0 |
| 64 | 11 | **10/50** | **50/50** | 50 | 50 |
| 64 | 12 | **10/50** | **50/50** | 50 | 50 |
| 64 | 13 | **10/50** | **50/50** | 50 | 50 |
| 64 | 15 | **10/50** | **50/50** | 50 | 50 |
| 64 | 20 | **10/50** | **50/50** | 50 | 50 |
| 64 | 30 | **10/50** | **50/50** | 50 | 50 |
| 64 | 50 | **19/50** | **50/50** | 41 | 38 |

**What this says, plainly.** The cliff exists and R5 removes it: at `Threads 64` the engine goes from
10 of 50 correct mating moves to **50 of 50** at every clock from 11 to 50 ms, and at `Threads 8` it
improves at every clock in 11–30 ms. **With `Threads 1` there is no cliff at all** — the engine is
50/50 at every clock from 1 to 50 ms both before and after — so the reviewer's report is a
multi-thread finding, not a single-thread one, and on one thread `go wtime 11` was never worse than
`go wtime 10` in this test. The remaining 0-node rows after the patch at Threads 64 are the hash-move
answers, which are the *good* emergency outcome (a legal, previously best move, no search).

## 5. Part D — everything together

**All five patches apply alone** on clean 6b98f217, and **together forward (R1,R2,R3,R4b,R5) and
reverse (R5,R4b,R3,R2,R1)**. The tree built from the shipped patch files is the tree I tested: I found
and fixed one divergence (`nnue_v3.cpp` had an extra, logically equivalent `if (pending())`) by
rebuilding from the patch files and re-running the identity match — same sha256.

**Pins on the fully patched build:** `bench 11` **312866**, `bench 13` **862329**, `bench 16`
**3024920**, `go perft 5` **4865609**.

**Identity, as a hash plus a length assertion** (`match_hash.py`, job 4's improvement over job 3):

| run | games | shortest game | games below 20 plies | sha256 of all move lists |
|---|---|---|---|---|
| unpatched, Hash 16 | 400 | 26 plies | 0 | `b43828b014c8286bc57da7a31b08355c610b4296eadc528145bff3b678a272d0` |
| **all five patches, Hash 16** | 400 | 26 plies | 0 | **`b43828b014c8286bc57da7a31b08355c610b4296eadc528145bff3b678a272d0`** |
| all five patches, **Hash 32** | 400 | 26 plies | 0 | `72c9ac0b19a0e45b6a7c823bfd8141e0e9e3bd1cb84d530f762cf9c90b466e20` |

Identical hash for the patched build, different hash for Hash 32 — the comparison fires when it
should. The length assertion held (shortest 26 plies, none below 20), so an empty-game pass is
impossible.

**Sanitizers**, planted fault first: the same `sanitizer_planted_fault.cpp` as job 3 reported both a
UBSan `store to address … with insufficient space` and an ASan `heap-buffer-overflow`, so the harness
sees faults. Then, on an ASan+UBSan build of the fully patched tree: `R1_test.py` 5 of 5 PASS with
**0 stderr lines**; `table_test` 64 pass with **0 stderr lines**; an R5 spot check (12 positions,
`wtime 11`, `Threads 64`) with **0 stderr lines**; the 57-row `go` matrix 0 fails (release build).

## 6. What the output looks like now

For every repair that changes printed output:

- **R4b, `go movetime 99999999999999999999 wtime 2000 btime 2000`**: used to search until stopped;
  now prints `bestmove` after about 1990 ms with `time 1990`-ish info lines, i.e. it behaves as if
  `movetime 2000` had been sent. Nothing about the info format changes.
- **R4b, negative clocks**: `go wtime -50` prints an immediate `bestmove` with a handful of nodes,
  the same shape as `go wtime 0` — it does **not** print a long search.
- **R4b, `go nodes -1`**: prints one `info depth … nodes 1` line and a `bestmove`, instead of a
  five-second search or a zero-node answer.
- **R5**: an answer that used to be `bestmove <first legal move>` with **no `info` line at all**
  (0 nodes) is now `info depth 1 … nodes ≤2000` plus `bestmove`, and the move is the hash move or the
  best of one ply. A GUI that reads the first `info` line will now see one; it did not before.
- **R1** (job 3, unchanged here): a drawn root now prints search info lines with real node counts
  instead of `score cp 0 nodes 0` at every depth. Not new in this job, repeated because the output
  does change.

## 7. Files of the repository I opened

`forge-combo29/src/uci.cpp` (73–135 the parser, 245–262 `isready`, 575–590 `eval`),
`src/search.cpp` (1265–1300 `should_stop`, 2280–2330 the emergency paths, 2625–2650 the emergency
finish, 2245–2275 `root_drawn`), `src/nnue_v3.cpp` (393–405 `problem`),
`include/forge/nnue_v3.hpp` (150–170), `include/forge/uci_clock.hpp` (14–42),
`include/forge/search.hpp` (28–60 `SearchLimits`), `CMakeLists.txt` (14–43), and
`FABLE_TO_deepseek2_1..4.md` on the handoff branch.

## 8. Stamps

| point | UTC |
|---|---|
| job 4 start | 2026-11-15T16:31:49Z |
| `__pycache__` removed from the repository | 16:32 |
| R4b written and built | 16:32–16:33 |
| three-build known-answer table, first run (showed the movetime conflict) | 16:33 |
| R4b + `movetime` cap, table clean | 16:34 |
| table test compiled and passing 64/64 | 16:35 |
| 57-row matrix on R4b: 0 fails | 16:36 |
| R5 written and built | 16:38 |
| cliff measured before (124 s) and after (120 s) | 16:38–16:41 |
| five patches, combined tree, pins | 16:41 |
| identity match, three 400-game runs | 16:42–16:56 |
| sanitizer build and runs | 16:50–16:57 |
| report written | 17:00 |

From the recorded `date -u` calls and the command sequence. Budget: 75 minutes from 16:31:49, i.e.
17:46; the report is written at about 29 minutes.

## 9. What I did not do

- I did not test `Threads 2, 4, 16, 32` for R5; only 1, 8 and 64 as the job asked. The 8-thread row
  only *improves* rather than fully fixing, so the cliff's exact thread-count boundary is not mapped.
- I did not test R5 with `ponder` or with `movetime` (the emergency path is guarded by
  `!waiting_to_ponder` in both old and new code, but only by reading).
- I did not test R4b's `movetime` cap against a GUI that sends `movetime` larger than the clock on
  purpose.
- The 400-game identity uses one opening set (UHO), one node limit (20000) and one game per opening.
- Sanitizer runs used `detect_leaks=0`.
- I did not re-run the R2/R3 sweeps on the *combined* build; they were proven on their own trees and
  the patches are disjoint from R4b/R5, except that R3 and R4b both edit `uci.cpp` — verified by both
  applying and by the pins, not by a fresh 96-combination sweep.
- No engine source committed, no pull request, no binary files. The `__pycache__` file Fable found in
  job 3 is removed and `.gitignore` now excludes bytecode.

## 10. What I am not sure about

- **The `movetime` cap in R4b is my own addition**, not in the job text. It is the difference between
  "0 past their clock" holding and not holding, and Fable should read those 4 lines first. If the
  intent is that a `movetime` always wins over a clock, R4b as specified is the right patch and the
  matrix has one failure.
- **`nodes 0` → 1 node** is a judgement: "bounded, immediate answer" could also mean "zero nodes,
  first move", which is what the unpatched code does when `nodes_specified` is true. I chose one node
  because a zero-node answer prints no info at all.
- **R5 at Threads 8 only improves from 24–32/50 to 33–40/50** rather than reaching 50/50. The 0-node
  answers remaining there are hash-move answers, which I believe are fine, but they mean "wrong mating
  move" still occurs at 8 threads on 10–17 of 50 positions. I did not chase why.
- R5's bound argument rests on `should_stop_with` reading the same `hard_limit_ms_`; I checked that by
  reading (search.cpp:1285–1288), not by instrumenting a build.
- The identity proof cannot see a patch that changes behaviour only on positions these 400 games
  never reach; R5 in particular can only act under time pressure, and a `nodes 20000` match with no
  clock never expires a hard limit, so R5 is *not* exercised by it at all.

## 11. A better way

1. **The job text's own requirements disagreed, and only the table found it.** R4b was specified with
   "old clamping for an out-of-range value" and also with "0 lines past their clock"; those two
   cannot both hold for `go movetime <huge> wtime 2000`. One row in the known-answer table exposed it
   in seconds. I would add to the standing job form: *every requirement gets one row in the known-answer
   table*, so contradictory requirements surface before the patch is written rather than after.
2. **R5's measurement should include a `Threads` sweep, not three points.** The finding is entirely a
   function of thread count (no cliff at 1, partial at 8, full at 64), and the boundary is what tells a
   reader whether their machine is affected. A sweep from 1 to 64 in steps of 1 on one clock (11 ms)
   would cost about the same as the three points I ran.
3. **The table test is the artifact worth keeping.** It compiles the parser into a plain test binary
   and asserts fields; it found 23 broken rows on the unpatched file and would catch any future
   regression in `parse_limits` in about 1 second. My earlier "unit test instead of 57 processes"
   suggestion is now implemented and the cost of the full matrix is measurable against it.

## 12. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
