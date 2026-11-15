# deepseek2, job 3 report: four repairs, written and proven

## 1. First line

**All four repairs are written and proven: 4 of 4.** Each patch applies alone on 6b98f217, applies on
top of the other three in either order, makes its test fail-before / pass-after, and moves nothing
else:

| repair | patch | changed lines | test before to after |
|---|---|---|---|
| R1 root that is already drawn | `evidence/R1_root_drawn.patch.txt` | 11 (+5/-6) | 3 of 5 cases FAIL to 5 of 5 PASS |
| R2 `eval` names the search's evaluator | `evidence/R2_eval_names.patch.txt` | 5 (+4/-1) | 16 INCONSISTENT of 96 to **0** |
| R3 `isready` on an unfinished configuration | `evidence/R3_isready_pending.patch.txt` | 10 (+9/-1) | 1 of 8 sequences FAIL to 8 of 8 PASS |
| R4 `go` keeps its clock | `evidence/R4_go_parser.patch.txt` | 61 (+39/-22) | 2 of 57 lines past clock to **0**, all 13 slow lines now <=130 ms |

Proof that nothing else moved: `bench 11` 312866, `bench 13` 862329, `bench 16` **3024920** (my
unpatched number, unchanged), `go perft 5` 4865609; and **400 of 400 games identical** between the
unpatched and the fully patched engine at `nodes=20000` on UHO openings. The comparison can fail:
the same engine with `Hash 32` instead of `Hash 16` differs in **71 of 100 games**.

## 2. R1 - the root that is already drawn

**Patch** `evidence/R1_root_drawn.patch.txt`, `src/search.cpp` only, 11 changed lines (+5/-6).

**What it does.** `root_drawn` becomes `board.is_insufficient_material()` alone, and the `DrawJitter`
branch under it goes away. A root that is a third occurrence, or whose 50-move clock has expired, is
now searched like any other (a draw may be claimed but need not be). A position with no legal move is
still answered at once by the existing `root_candidates.empty() || root_drawn` test, and insufficient
material keeps its immediate answer.

**Why this is the smallest change.** The engine already had the right structure - one early-return
block for "no search needed". The repair narrows the condition that enters it. Nothing else in the
block needed touching: with `root_drawn` false the block is still entered for `legal.empty()` (no
move), and `score = -MateValue` for a mated root still applies there.

**Before / after** (`evidence/R1_before.json`, `evidence/R1_after.json`):

| case | unpatched | patched |
|---|---|---|
| `third_occurrence_mate` (job's position after its 8-ply list) | **FAIL** best `a1b1`, `cp 0`, 0 nodes | **PASS** best **`d1d8`**, **`mate 1`**, 390 nodes |
| `clock100_mate` (same position, clock 100) | **FAIL** best `a1b1`, `cp 0`, 0 nodes | **PASS** best **`d1d8`**, `mate 1`, 385 nodes |
| `third_occurrence_searched` (same structure, queen removed, third occurrence) | **FAIL** best `a1b1`, `cp 0`, 0 nodes | **PASS** searched, 389 nodes, legal move |
| `stalemate_root` | PASS `cp 0`, 0 nodes | **PASS unchanged** `cp 0`, 0 nodes |
| `checkmate_root` | PASS 0 nodes | **PASS unchanged** `mate 0`, 0 nodes |

**What I am not sure about in this patch.** (a) I removed the `DrawJitter` branch rather than keeping
it: with the root now searched, a jittered draw score at the root would be a search result, and the
search already applies `draw_leaf_score` at the repetition node itself (search.cpp:1569). If the root's
jitter is wanted for reporting, that is a second deliberate change - I did not see one. (b) A root whose
fifty-move clock has already expired is now searched and returns a draw score from the search, which
may differ by the jitter amount from the exact `0` it printed before; intended, but a visible output
change. (c) I did not test a root that is a third occurrence and has no legal move; the `legal.empty()`
path wins there in both versions.

## 3. R2 - `eval` and the search must name the same evaluator

**Patch** `evidence/R2_eval_names.patch.txt`, `src/uci.cpp` only, 5 changed lines (+4/-1).

**Which flag wins, and why.** `UseNNUE` wins. The search already decides that way
(`search.cpp:1076-1078`: `if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);`
comes before the `v3::active()` test), and `UseNNUE false` is the user's explicit request to turn the
network off. `NNUEArch` selects *which* network to use when networks are in use; it cannot mean "use a
network anyway" against an explicit off. So `eval` must report HCE in that state, which the patch makes
it do by copying the search's own condition instead of writing a second rule.

**Before / after** (`evidence/R2_before.json`, `evidence/R2_after_test.json`; the sweep is
`tests_deepseek2_job2/partA_fingerprint.py`, unchanged):

| | unpatched | patched |
|---|---|---|
| consistent | 48 | **64** |
| INCONSISTENT | **16** | **0** |
| UNIDENTIFIED | 0 | 0 |
| died before any search | 32 | 32 (unchanged, by design) |

Control `UseNNUE false` + `NNUEArch true`: unpatched `named V3 / ran HCE`; patched `named HCE / ran HCE`.

**What I am not sure about.** The patch tests `nnue::available()` as well as `nnue::enabled`, mirroring
1076 exactly; if `available()` ever becomes false while `enabled` is true, `eval` will now say HCE and so
will the search - consistent, but the printed `nnue <N>` component would be stale. That state does not
occur in my sweep, but I did not construct it deliberately.

## 4. R3 - `isready` must not end the engine for an unfinished configuration

**Patch** `evidence/R3_isready_pending.patch.txt`, three files (`include/forge/nnue_v3.hpp`,
`src/nnue_v3.cpp`, `src/uci.cpp`), 10 changed lines (+9/-1).

**What it does.** Adds `v3::pending()` - true exactly while `requested && loaded() == nullptr &&
g_problem.empty()`, i.e. "you asked for a network and have not given me one yet". `problem()` keeps its
text for that state, so a *search* request still stops, unchanged. `isready` checks `pending()` first:
it prints `info string NNUE v3: no network loaded yet` and answers `readyok` instead of exiting 2. A file
that cannot be opened still sets `g_problem`, so `pending()` is false and the old hard stop applies.

**Before / after** (`evidence/R3_before.json`, `evidence/R3_after.json`), 8 sequences:

| sequence | before | after |
|---|---|---|
| arch, **isready**, file(exists) | **FAIL exit 2** | **PASS survives** |
| arch, isready, file(missing) | PASS (dies, exit 2) | PASS unchanged |
| arch, file(exists) | PASS | PASS |
| arch, file(missing) | PASS (dies) | PASS unchanged |
| file(exists), isready, arch | PASS | PASS |
| file(missing), isready, arch | PASS (dies) | PASS unchanged |
| file(exists), arch | PASS | PASS |
| file(missing), arch | PASS (dies) | PASS unchanged |

**What I am not sure about.** The patch adds a public function to a header, the largest surface of the
four. An inline version in `uci.cpp` would avoid the header change but duplicates the condition; I chose
the named predicate. A **corrupt** net file is not tested (§9).

## 5. R4 - `go` must not lose its clock to a malformed token

**Patch** `evidence/R4_go_parser.patch.txt`, `src/uci.cpp` only, 61 changed lines (+39/-22; mostly new helpers).

**What it does.** One `take_value()` guard refuses to consume a token that `is_go_keyword()` recognises,
and every reader goes through it. A missing / non-numeric / negative / out-of-range value leaves **that
one** parameter absent and consumes nothing, so the rest of the line is parsed as written. `depth`,
`movestogo` and `mate` require a value > 0; `nodes` requires an in-range unsigned number. Clocks are
parsed locally instead of through `parse_clock_ms`, because that function saturates on overflow and the
job asks for an absent parameter instead.

**Before / after** (`evidence/R4_before_partC.json`, `evidence/R4_after2.json`): 2 of 57 lines past their
clock became **0 of 57**, and all 13 lines that used to run over 1 s:

| line | before | after |
|---|---|---|
| `go btime wtime 2000 btime 2000` | 7462 ms, needed stop | **114 ms** |
| `go movetime 99999999999999999999 wtime 2000 btime 2000` | 7547 ms, needed stop | **116 ms** |
| `go winc wtime 2000 btime 2000` | 7550 ms | 117 ms |
| `go binc wtime 2000 btime 2000` | 7531 ms | 116 ms |
| `go movestogo wtime 2000 btime 2000` | 7490 ms | 116 ms |
| `go nodes wtime 2000 btime 2000` | 7417 ms | 125 ms |
| `go mate wtime 2000 btime 2000` | 7498 ms | 117 ms |
| `go movestogo {winc 100, -500, 0, abc, huge} ...` | 1430-1516 ms | 115-121 ms |
| `go winc 99999999999999999999 ...` | 1195 ms | 115 ms |

Controls unchanged: `go wtime 2000 btime 2000` about 115 ms; `go infinite` still needs `stop`.

**What I am not sure about.** (a) `go nodes` with a valid value still ends at the node count, correct
but it means the `nodes` rows are answered by the clock, not the node limit; I checked both paths
separately. (b) I did not change `parse_clock_ms` itself; other callers, if any, keep the saturating
behaviour. `grep` says `parse_limits` was its only caller, but I did not audit beyond the grep.
(c) `movestogo 0` now leaves `moves_to_go` at its default instead of clamping to 1; that is what "the
parameter is absent" means, and it changes behaviour for callers that send `movestogo 0` deliberately.

## 6. The proof

### a. Fails before, passes after
Per repair, sections 2-5, with raw outputs in `evidence/`. Exit codes: `R1_test.py` unpatched **1**,
patched **0**; `R3_test.py` unpatched **1**, patched **0**; `R2_test.py` unpatched **1** (2 problems),
patched **0**; the Part C matrix unpatched **2 fails**, patched **0**.

### b. Nothing else moved (patched build against unpatched)

| check | unpatched | patched |
|---|---|---|
| `bench 11` | 312866 | **312866** |
| `bench 13` | 862329 | **862329** |
| `bench 16` | **3024920** | **3024920** |
| `go perft 5` | 4865609 | **4865609** |

### c. Identical play: 400 games
`match_identity.py`, `evidence/match_identity_400.json`, log `evidence/match_400b.log`.
400 UHO openings (`UHO_Lichess_4852_v1.epd`, official repository), `go nodes 20000`, `Threads 1`,
`Hash 16`, `OwnBook false`, one process per game, both engines playing the same opening from the same
side. Games end at a terminal position, at 300 plies, or at a third occurrence (the match-program
rule, so R1 can never act in a match).
**Result: games 400, games that differ 0, first difference None.**

### d. The comparison can fail
Same harness, 100 of the same openings, both sides at `Hash 32` instead of `Hash 16`
(`evidence/match_power_hash32_100.json`), compared against the `Hash 16` run:
**71 of 100 games differ**; first difference game 2, ply 106: `e1g3` (Hash 16) against `d5d4` (Hash 32).
So the equality in (c) is a measurement, not an artefact of a comparison that never fires.

### e. Sanitizers, planted fault first
ASan + UBSan build of the fully patched tree (`-fsanitize=address,undefined`, RelWithDebInfo, g++ 13).
The **planted-fault control ran first**: a 12-line program with a heap overflow and a signed overflow.
ASan reported `heap-buffer-overflow` and UBSan reported `store to address ... with insufficient space`,
so the harness can see a fault. Then all four test sets, with the sanitizer build of the engine:

| test set | result | stderr lines |
|---|---|---|
| `R1_test.py` | 5 of 5 PASS | **0** |
| `R2_test.py` (full 96-combination sweep) | PASS, 0 inconsistent | **0** |
| `R3_test.py` | 8 of 8 PASS | **0** |
| `partC_go_faults.py` (R4) | 57 rows, 0 fails | **0** |

`ASAN_OPTIONS=detect_leaks=0` was set, because the engine is stopped with `quit` mid-teardown; that can
hide a leak, which is stated rather than glossed over.

### The patches themselves
Each of the four applies with `patch -p1` on a clean 6b98f217 `forge-combo29/` **alone**, and all four
apply **in order 1-2-3-4 and in reverse order 4-3-2-1**. The tree built from the four patch files is
byte-identical to the tree I tested: `src/uci.cpp`, `src/search.cpp`, `src/nnue_v3.cpp` and
`include/forge/nnue_v3.hpp` all `diff`-clean against it.

## 7. Files of the repository I opened

`forge-combo29/src/search.cpp` (2245-2275, and 1070-1085, 1300-1310, 1551-1600, 1636-1645),
`src/uci.cpp` (60-135 the parser, 176-195 `v3_ready`, 245-262 `isready`, 340-400 the option handlers,
470-530 `go`, 575-590 `eval`), `src/nnue_v3.cpp` (390-410 `problem`, 25-40 globals),
`include/forge/nnue_v3.hpp` (150-170), `include/forge/uci_clock.hpp` (21-42),
`include/forge/search.hpp` (60-120), `CMakeLists.txt` (14-43), and the job files
`FABLE_TO_deepseek2_1.md` to `FABLE_TO_deepseek2_3.md` on the handoff branch.

## 8. Stamps

| point | UTC |
|---|---|
| job 3 start | 2026-11-15T15:28:51Z |
| four patches written and compiled together | about 15:31 |
| R1 proven before/after | about 15:33 |
| R3 proven before/after | about 15:37 |
| R2 proven, 0 of 96 | about 15:39 |
| bench and perft on both builds | about 15:39 |
| R4 proven; the missed `nodes` branch found and fixed | about 15:47 |
| 400-game identity match done | about 16:06 |
| ASan+UBSan build, planted fault, four test sets | 16:04-16:12 |
| Hash power test, 100 games | about 16:13 |
| report written | about 16:30 |

From the recorded `date -u` calls and the command sequence; I did not write a stamp file at each point.
Budget: 75 minutes from 15:28:51, i.e. 16:43.

## 9. What I did not do

- I did not test a **corrupt** (rather than missing) net file in R3. `pending()` is false whenever
  `g_problem` is set, so a corrupt file should still end the engine, but that is reasoning, not a
  measurement.
- I did not test R1 with `DrawJitter > 0`. The patch removes the root jitter branch; with jitter on the
  root's draw score now comes from the search. Untested.
- The 400-game match uses one game per opening and one opening set (UHO); two games per opening and
  other opening sets were not run.
- Sanitizer runs used `detect_leaks=0`, so a leak is not covered.
- I did not run a match to measure whether R1 gains anything in play. The job asked for identity, and
  identity is what I proved; R1 cannot act in a match that ends at a third occurrence, which is why
  identity holds.
- No engine source is committed; the four repairs and the two earlier fault models are text patches.
- No pull request.

## 10. What I am not sure about

- **R1's jitter removal** is the part of these four patches most likely to be wrong for a reason I
  cannot see from here. If the owner relies on the root's `DrawJitter` value being printed for a drawn
  position, this patch changes it.
- **R4 changes `movestogo 0`** from "treated as 1" to "absent". That follows the job's rule but is a
  behaviour change beyond the failure it repairs.
- **R3 adds a public function** to a header: the largest surface for the smallest behaviour change.
- The 400-game identity is strong evidence for *these* openings at *this* node limit. A patch that
  changes behaviour only on positions these games never reach would pass it.
- My first combined build of R4 was missing the `nodes` branch; I found it by re-testing and fixed it.
  The tree I report is the corrected one and is byte-identical to the tree built from the patch files.
  Anyone re-running an intermediate log of mine would see a different result for one line.

## 11. A better way

1. **State an identity proof as a hash plus a length assertion.** I compared 400 move lists game by
   game; one SHA-256 over the concatenated move lists of both runs would say the same thing in one line
   and cannot pass on empty data. My own first smoke test "passed" with four zero-length games and I
   only caught it by printing game lengths. A hash plus "no game shorter than 20 plies" would have
   caught it at once. I would make both mandatory in any future identity job.
2. **R4's test belongs in a unit test of `parse_limits`, not in 57 engine processes.** With the repair
   in place the whole matrix is a pure function of the token list; a table-driven test over
   `SearchLimits` would run in milliseconds and assert the exact field (`time_ms == 2000`,
   `movetime_ms == -1`) instead of "answered quickly".
3. **A repair that changes what is printed should say so in the proof list.** R1 changes what a drawn
   root prints - a search score (with jitter, if enabled) instead of a literal 0. The job's test list
   did not ask for that case, and a reviewer reading only the tests would not see it. For any repair of
   a reporting-path bug, I would add "what the output looks like now" as a proof item.

## 12. Model

deepseek2. As I know it: DeepSeek V4.1 Flash, build 1017, running as a Cursor cloud agent.
