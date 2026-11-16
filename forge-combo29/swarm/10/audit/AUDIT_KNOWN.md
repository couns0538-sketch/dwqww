# AUDIT — every "Known:" claim in the brief that asserts engine behaviour

seat 10 (area 10, CHECKING THE OTHERS) · commit 6b98f217 · release build
`~/builds/release/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`
4 cores · g++ 13.3.0 · python-chess 1.11.2 · sets from `for-fable-and-opus/kimi5-work`
(O = `tests_kimi5_job3/first200.fens`, 200; G = `tests_kimi5_job5/set_G.epd`, 353)

Predictions for every row were committed ALONE at `a306832b6` (`PREDICTIONS.md`) before the first
measuring command. This file is ADDED to as rows settle; nothing in it is typed from memory.

## Read this first — my own harness was broken, and this is the retraction

Seat 19's 19-F12 (broadcast by the coordinator) is **real and I reproduced it independently**:
if stdin reaches EOF while a search runs, the engine **aborts the search and prints a fabricated
`bestmove`** with no `info` line at all.

| variant | startpos `go depth 12` | info depth lines | bestmove |
|---|---|---|---|
| stdin CLOSED right after `go` | returns in 0.02 s | **0** | `a2a3` (never searched) |
| stdin HELD OPEN, read to `bestmove` | 0.03 s of search | **12** | `e2e4`, 56,720 nodes |

evidence: `audit/raw_E1/E1_V1_stdin_closed.txt`, `audit/raw_E1/E1_V2_stdin_held_open.txt`

**What this invalidates in my own earlier work, and what it does not.**
- **Unaffected (perft only):** `honesty/` (perft 5 and bench), `job2` (all perft-2 and UCI-sequence
  work), `check1` (bench as argv/stdin), `check2` (perft 2 divides), `check4` (perft 3 divides).
  `go perft N` completes and prints `nodes N` on its own before EOF, so these stand.
  `check3` used only the `eval` command, which also completes immediately; it stands.
- **Affected and re-run:** the first version of this audit's K-checks that used `go depth` through a
  piped subprocess, and the first `audit_sums.py` run. Their outputs are marked `INVALID` below and
  were discarded, not reported. Everything from here on uses `audit/drv.py`, an interactive reader
  that writes one command at a time and never closes stdin before `bestmove`.

## The table

| # | claim as the brief states it | result | evidence | note |
|---|---|---|---|---|
| K1 | Area 1 job 3: "an illegal move keeps the legal prefix (perft 1 = 29 after e2e4 e7e5 e1e3)" | **PASS** | `audit/raw/verdicts/K1.json`, `audit/raw/K1/illegal_prefix.txt` | engine 29 = python-chess 29 = 29 |
| K2 | Area 2 job 3: "`setoption name Hash value 0` answers `info string invalid value for option Hash`" | **PASS** | `audit/raw/verdicts/K2.json`, `audit/raw/K2/` | exact string reproduced verbatim |
| K3 | Area 3 job 3: "startpos perft 5 = 4,865,609" | **PASS** | `audit/raw/verdicts/K3.json`, `audit/raw/K3/perft5.txt` | also the STEP 2 pin |
| K6 | the honesty pins bench 11/13/16 | **REFUTED AS STATED** | `audit/raw2/pins.json` | see below — the pins hold ONLY on DEFAULT options |
| K7 | STEP 2: portable `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` | **PASS** | `audit/raw2/default_bench*.txt` (v3 build, `~/builds/v3/forge`) | identical pins on a non-AVX512/BMI2 build |
| K8 | FABLE-1: "consecutive digits are ADDED ('17'/'44' = 8 empties; '9' refused)" | **PASS** | `audit/raw/verdicts/K8.json`, `audit/raw/K8/` | `44` and `17` give startpos perft 2; `9` refused |
| K9 | FABLE-1: "a triple check by three knights is accepted; its moves are generated right" | **PASS** | `audit/raw/verdicts/K9.json` | attackers c2/d3/f3 all hit e1; perft 1 = 3 = python-chess |
| K10 | FABLE-1: "an unknown command is ignored without a line" | **PASS for a plain garbage line / REFUTED as a general claim** | `audit/raw/verdicts/K10.json`, `audit/raw/K10/` | `go banana` **SEARCHES and answers `bestmove a2a3`**; `setoption name` answers `info string unknown option` |
| K11 | FABLE-1: "an option without a value answers info string invalid value for option X" | **PASS** | `audit/raw/verdicts/K11.json` | same shape as K2 |
| K12 | FABLE-1: "`bestmove 0000` on a position without legal moves" | **PASS** | `audit/raw/verdicts/K12.json` | both checkmate and stalemate roots |
| K4 | Area 3 job 3: "G perft 3 and the first 60 at perft 4 were equal in an earlier check" | **PASS** | `audit/raw2/K4/summary.json` | 353/353 equal at depth 3, 60/60 equal at depth 4, 0 null totals; "equal" tested against python-chess 1.11.2 since the brief does not say equal to what |
| K5 | Area 4: "Threads 2 and 4 on the first 50 of O gave 0 reports" | **PASS (0 reports, SHOWN)** | `audit/raw2/K5/summary_direct.json`, `meta_direct.json`, `proof_planted_direct.json`, `sweep_direct_T2.json`, `sweep_direct_T4.json` | both proofs obtained on my own builds: `nm -C` = 21 `__tsan_` symbols, planted race counted (6 reports, exit 66) by the same runner, then 50 positions x Threads 2 and 50 x Threads 4 at depth 12 S14 = **0 reports, 0 null nodes** |
| K13 | the four sums (O d12 9,500,069 / G d12 18,466,239 / O d14 21,812,100 / G d14 43,345,893) | **PASS, ALL FOUR EXACT, in the S14 regime** | `audit/raw2/sums_summary.json` | see K13 below; the first three O depth-12 values 41,311 / 24,872 / 28,574 also reproduce exactly |
| K14 | FABLE-1: "a root restricted by searchmoves (even to every legal move) searches a different, mostly smaller tree: IIR fires at the root, and no hash entry is stored for a restricted root" | **REFUTED — and it is a genuine DEFECT, not "a smaller tree"** | `audit/raw2/K14_summary.json`, `audit/raw2/k14_tt_summary.json`, `audit/raw2/K14_summary.json` | "no hash entry is stored" is FALSE (repeat shrinks 21,640 -> 17,847). Beyond that: restricting to **all 20 of 20 legal moves** yields a *worse* answer that never converges to the unrestricted one (depth 16: score 23 vs 35), and it corrupts a LATER unrestricted search in the same process (36,745 vs 4,951 nodes, score 29 vs 30). See §K14 below. |

## K6 in detail — the pins and S14 are two different regimes

`audit/raw2/pins.json`, measured with `audit/audit_pins.py`:

| regime | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| DEFAULT options (no setoption beyond Threads 1 / Hash 16) | **312866** | **862329** | **3024920** | **4865609** |
| the brief's S14 setoptions applied first | 242796 | 656517 | 2155620 | 4865609 |
| second independent build of the same source | 312866 | 862329 | 3024920 | 4865609 |

So: all four pins are **PASS on default options**, and the S14 block the brief says to "use unless a
job says otherwise" **changes three of the four**. The two independent builds are not merely equal in
nodes, they are **bit-identical binaries** (sha256 `e06310ec...` from two different build directories).

This matters for every seat: a seat that applies S14 before checking the pins will read 242,796 where
the brief promises 312,866, and may wrongly conclude its checkout is broken. The pins are DEFAULT-regime
numbers; S14 is for the position-set sums (K13).

## Method

Every number above is the pasted output of a committed script reading committed raw files.
Engine I/O for all searches goes through `audit/drv.py` (interactive, EOF-safe). Engine I/O for
non-search commands may use a plain pipe, which is safe for `uci`/`isready`/`setoption`/`position`/
`eval`/`bench`/`go perft`.

## K13 in detail — the sums are the S14 regime, exactly

`audit/raw2/sums_summary.json`, EOF-safe driver, `ucinewgame` BEFORE `position` (see the reset trap below),
Threads 1, Hash 16, OwnBook false:

| set / depth | S14 regime (the brief's "plain build, S14") | DEFAULT regime | published |
|---|---|---|---|
| O depth 12 | **9,500,069** | 12,573,318 | 9,500,069 |
| O depth 14 | **21,812,100** | 29,799,803 | 21,812,100 |
| G depth 12 | **18,466,239** | 22,128,265 | 18,466,239 |
| G depth 14 | **43,345,893** | 56,971,881 | 43,345,893 |

O's first three positions at depth 12 are **41,311 / 24,872 / 28,574**, exactly the three values the brief
quotes, so the regime and the protocol are pinned beyond the total.

All four sums match to the digit, so the brief's sums are correct — **provided S14 is applied**.
This settles the K6 ambiguity in the other direction: the **pins** are default-regime and the **sums** are
S14-regime. A seat that uses one regime for both will see a mismatch on three of the four pins and on every
sum. Both statements in the brief are individually true; they are true of *different option sets*.

## A second trap that invalidated my first sums run — `ucinewgame` AFTER `position` resets the board

The brief says "`ucinewgame` + `isready` before every `go`". Taking that literally, a harness sends
`position fen F` and then `ucinewgame` — and **`ucinewgame` puts the board back to startpos**, so every
search silently measures startpos and every position returns an identical node count.

Proof (`audit/raw_reset/`): after `position fen <G>` the eval line is `total -351` and `go perft 1` gives
38; after a following `ucinewgame` the eval is `total 38` and `go perft 1` gives **20** (startpos).

Symptom in my discarded first run: every depth-12 position returned exactly 22,459 nodes and the O d12 total
came out 4,491,800 instead of 9,500,069. The identical-per-position pattern is the tell.

**Correct order:** `ucinewgame` + `isready` FIRST, then `position ...` + `isready`, then `go`.

## Method row (from seat 19's measurement-integrity warning)

For every claim in this table, the line being parsed was **located in the raw output before any verdict was
written**, and a missing line is reported as "the line is not there", never as a pass. Concretely, every K
check fails closed:

- node totals come from a `lines` list that must contain the parsed line; a `None` is counted in
  `null_nodes` and the row cannot be PASS while that count is above zero;
- `perft` totals are read from the `nodes N` line, and `drv.perft` raises if that line never arrives;
- the K2/K11 messages are matched as exact strings and the matched string is printed in the JSON;
- the sums comparison is `total == published` on integers, never on a float or a formatted string.

So a NaN-like comparison (seat 19's `clock_plan` case) cannot produce a PASS here: a missing number leaves
the field `null` and prints as `null`, which no equality test accepts. My own earlier `audit_known.py` K14
attempt did hit exactly this class of bug — it parsed `info ... nodes` from a build that prints no such line
for a piped search, got `None`, and the run died rather than reporting a result; that is the failure mode,
and it is why every row now names the line it parsed.

## K14 in detail — it is a genuine DEFECT, not a merely smaller tree

`audit/raw2/K14_summary.json`, depth 12, startpos, restricted to all 20 legal moves:

| run | nodes | bestmove |
|---|---|---|
| unrestricted, once | 56,720 | e2e4 |
| restricted to all 20, once | **21,640** | d2d4 |
| unrestricted twice in one process | 56,720 then **4,951** | e2e4, e2e4 |
| restricted twice in one process | 21,640 then **17,847** | d2d4, e2e4 |

- "a different, mostly smaller tree" — **TRUE**, 21,640 vs 56,720 (2.6x smaller).
- "no hash entry is stored for a restricted root" — **FALSE**. The restricted repeat drops from 21,640 to
  17,847, a 17.5 % reduction, so a root entry clearly IS stored and reused. The reduction is smaller than the
  unrestricted case (56,720 -> 4,951) because the restricted search's own tree was already small, but it is
  not zero, and "no entry is stored" predicts exactly zero reduction.
### Is that a defect or intended? A defect — and here is the experiment that separates them

"An entry is reused" is consistent with two very different things, so I ran the discriminating test
(`audit/k14_tt.py`, `audit/raw2/k14_tt_summary.json`): does a restricted search **corrupt a later
unrestricted search** in the same process?

| session (depth 12, startpos) | searches, in order |
|---|---|
| unrestricted alone | **56,720** nodes, e2e4, cp 30 |
| restricted, then unrestricted | 21,640 then **36,745** nodes, cp **29** |
| unrestricted, then unrestricted (control) | 56,720 then **4,951** nodes, cp 30 |
| restricted, then `ucinewgame`, then unrestricted | 21,640 then **56,720**, cp 30 (reset, back to cold) |

An unrestricted search that follows a *restricted* one runs **36,745 nodes and scores cp 29**; the control
runs **4,951** and scores cp 30. So the restricted search does not merely build a smaller tree — it changes
what a later *unrestricted* search computes, including its score. That is contamination of the shared table,
which is what "defect" means here. `ucinewgame` between them restores the cold behaviour, confirming the
state lives in the shared table rather than in the searcher's own stack.

Three repeats of every ordering gave byte-identical numbers, so this is deterministic, not a race.

And the restricted root is not merely *weaker*, it is wrong on the same board:

| what was searched | nodes | depth reached | score | bestmove |
|---|---|---|---|---|
| unrestricted depth 12 | 56,720 | 12 | **cp 30** | e2e4 |
| restricted to ALL 20 legal moves, depth 12 | 21,640 | 12 | **cp 23** | d2d4 |
| restricted to 19 of 20 (best move dropped) | 31,617 | 12 | cp 23 | d2d4 |
| unrestricted, `go nodes 220185` (same work as restricted depth 16) | 212,340 | — | cp 27 | e2e4 |
| unrestricted depth 16 | 267,839 | 16 | **cp 35** | e2e4 |
| restricted to ALL 20, depth 16 | 220,185 | 16 | **cp 23** | d2d4 |

The gap does **not** close with depth (30 vs 23 at d12, 35 vs 23 at d16) and does not close with a node
budget of comparable size (27 vs 23), so it is not "a smaller tree" and not "less work". Restricting to
20 of 20 moves — a filter that excludes nothing — changes the score by 12 cp and the chosen move. That is a
real search defect at the root, of the same family as seat 17's S-F1 (`bestmove 0000` from an empty
`root_candidates`).

Practical consequence for every seat: **node counts, scores and bestmoves from a `searchmoves` run are not
comparable to an unrestricted run**, and a `searchmoves` search in a long-lived process also perturbs the
next unrestricted search. If a match or a tuning run uses `searchmoves`, either use a fresh process per
search or expect both effects. The brief's claim is inverted: the problem is not that no entry is stored —
it is that the restricted root's search itself is unsound.

## K5 — SETTLED, and it needed its own retraction

The claim is a *report count*, so by the brief's own rule it counts only with **two** proofs: an
`nm -C <exe> | grep -c __tsan_` above 0, and a scratch copy with ONE planted race counted by the same runner.
My first attempt at this row produced `proof2: false` — and the reason is instructive:

**my `Drv` helper sends the engine's stderr to `DEVNULL`.** Every TSan report goes to stderr, so with that
helper "0 reports" is not a measurement at all; it is *guaranteed* to read zero for any build, planted race
included. That is precisely the class of error seat 19 warned about, in my own code. `audit/k5_direct.py`
therefore captures stderr explicitly (and still avoids the EOF trap by sending the `go` last and reading
stdout to `bestmove` before closing).

With stderr captured:

| step | result |
|---|---|
| `nm -C forge \| grep -c __tsan_` | 21 (real build) and 21 (planted build) |
| planted race at `Worker::search` (unsigned global counter, every thread) | **6 TSan reports, exit 66, 10,302 bytes of stderr** |
| same runner, real TSan build, first 50 of O, Threads 2, depth 12, S14 | 0 reports, 0 null node counts, 50/50 legal bestmoves |
| same, Threads 4 | 0 reports, 0 null node counts, 50/50 legal bestmoves |

So K5 is **PASS**: the brief's statement is true and is now a shown result rather than a trusted one.
Corroboration from the seat that owns area 4: seat 04's branch carries the same two proofs independently
(`job1/planted_proof_raw.txt` shows `WARNING: ThreadSanitizer: data race` at `search.cpp:2154` on a global
`forge::g_planted_race_counter`, and `job1/meta_planted.txt` records `nm __tsan_ count: 21`), plus its own
sweep to Threads 1/2/4/8 — two independent seats now agree.

## Totals

12 claims audited: **11 PASS**, **2 REFUTED or half-refuted** (K6 as stated, K14's "restricted tree is
merely smaller"), **1 PASS with a scope correction** (K10). Nothing is left UNTESTABLE — K5 was settled by
building the TSan proofs myself. The rows that matter most for other seats are K6 (pins are default-regime,
sums are S14-regime), the `ucinewgame`-after-`position` reset, and K14 (a `searchmoves` root is not merely a
smaller tree, it is a *wrong* one).

## Re-run of my own job2 legality check (this is the honest correction)

My `job2` report claimed "4,803 (position, go) pairs replayed one per fresh process: 0 illegal bestmoves",
and it concluded that deepseek6's four headline numbers hold. The *conclusion* is right, but the *evidence*
for the legality half was produced with a piped driver, which triggers the EOF-abort trap: each pair's
`go` was aborted and what I legality-checked was the engine's fallback move, not the search's choice.
A legality check on fallback moves is close to vacuous.

Re-run with the EOF-safe driver, same 4,803 pairs, OwnBook false, `ucinewgame` before `position`:
`audit/raw2/clean56_fixed_summary.json` -> **4,803 pairs, 4,803 legal, 0 illegal, 0 `0000`, 0 missing
bestmoves, 11 pairs with no `info` node line**. So the number stands and is now properly measured.

For the record, the trap is visible in the moves themselves: on `1r6/2k2pp1/...` (black to move) the piped
`go depth 3` answers `d5d4`, while the same search driven correctly answers `e5e4` at 1,232 nodes. Both are
legal, which is exactly why a legality test cannot detect this defect — only the node count can.
