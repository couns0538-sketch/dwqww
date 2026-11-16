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
| K4 | Area 3 job 3: "G perft 3 and the first 60 at perft 4 were equal in an earlier check" | **PENDING** | `audit/raw/K4/` | "equal" is undefined in the brief; tested against python-chess |
| K5 | Area 4: "Threads 2 and 4 on the first 50 of O gave 0 reports" | **UNTESTABLE AS WRITTEN** | — | "0 reports" only counts with the brief's two proofs (nm count > 0 AND a planted race counted by the same runner); no such artifact is cited. A TSan run of my own is the only way to settle it. |
| K13 | the four sums (O d12 9,500,069 / G d12 18,466,239 / O d14 21,812,100 / G d14 43,345,893) | **PASS for O d12 9,500,069 and O d14 21,812,100, EXACTLY, in the S14 regime**; G pending | `audit/raw2/sums_summary.json` | see K13 below — the sums are S14-regime numbers, and the FIRST THREE O values 41,311 / 24,872 / 28,574 reproduce exactly too |
| K14 | FABLE-1: "a root restricted by searchmoves searches a different, mostly smaller tree" | **PENDING** | re-run with the corrected driver | first attempt was invalid (see above) |

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
| G depth 12 | running | running | 18,466,239 |
| G depth 14 | running | running | 43,345,893 |

O's first three positions at depth 12 are **41,311 / 24,872 / 28,574**, exactly the three values the brief
quotes, so the regime and the protocol are pinned beyond the total.

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
