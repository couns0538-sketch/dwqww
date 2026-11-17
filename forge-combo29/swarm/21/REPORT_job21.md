# REPORT job21 — the PC patch's own `go`-line and option surfaces

**What was asked.** (My own next step.) Look for a NEW find on the PC patch's own new code, not a
re-test of the repaired halfmove door. Probes: the `go`-line shapes `FORGE_FIX_GO_PARSE`
describes, and the five new options.

**The answer.** The patch's `go` handling and options behave as documented; **I found no new
fault**, and two things I initially flagged turned out to be correct behaviour. Details below,
including the two near-misses, because a wrong fault is worse than no fault.

## `go`-line probes, PC build, Threads 1

| go line | bestmove | info lines | nodes | ms | reading |
|---|---|---|---|---|---|
| `go depth` | a2a3 | 0 | – | 2.1 | named limit unusable, nothing else on the line → immediate answer |
| `go depth 5` | c2c4 | 5 | 1001 | 9.0 | control: real search |
| `go wtime btime 50` | a2a3 | 0 | – | 1.8 | the clock is **lost**; immediate answer |
| `go nodes abc` | a2a3 | 0 | – | 2.1 | non-integer nodes → no usable limit → immediate answer |
| `go movetime` | a2a3 | 0 | – | 2.0 | no value → immediate answer |
| `go wtime 1000 btime 1000` | d2d4 | 9 | 9653 | 34.9 | control: real search |
| `go depth -3` | d2d4 | 1 | 26 | 2.2 | clamped to depth 1 |
| `go depth 0` | d2d4 | 1 | 26 | 2.2 | clamped to depth 1 |
| `go banana` | – | 0 | – | >65000 | **searches forever** (see below) |

Two readings that I first took for faults and then established as correct:

1. **`go wtime btime 50` answers at once, `a2a3`, 0 nodes.** The patch's comment says r9 let that
   line lose the clock, and that "when a limit was named but unusable and no usable limit is left
   on the line, the answer comes at once, as r9 gave it". So an immediate `a2a3` is the
   *documented* behaviour, not a regression. What I cannot tell from outside is whether the value
   `50` was attached to `wtime` and `btime` was left empty (in which case a clock of 50 ms for
   one side and none for the other is a real oddity) or whether the whole line was dropped. I
   did not instrument it, so this stays in "suspicions", not in findings.

2. **`go banana` / `go` / `go xyzzy` search for ever.** I first recorded this as a hang. It is not
   a fault: a `go` with no recognised limit is an *infinite* search, which is legal UCI, and both
   builds do the same thing (measured: base and PC both ran past 23 s with no bestmove). Seat 30's
   30-F1 claims the engine "prints EXACTLY ONE bestmove per go line, including malformed ones" and
   lists `go banana` and `go` among them. **My measurement contradicts that claim on both builds**,
   and I do not think 30-F1 is wrong — I think my probe waits for a search that has no end. The
   right way to test 30-F1 is to send `stop` after the `go` and see whether a bestmove arrives;
   I did not do that here, so I am not filing a REFUTES line.

## Options, PC build vs base build

| option | value | PC build | base build |
|---|---|---|---|
| HistRework | 0, 1, 2, 3 | accepted | `unknown option` |
| HistRework | 4, −1 | `invalid value for option HistRework` | `unknown option` |
| MateAlphaGuard / CuckooRep / TtPruneV2 / CorrHistV2 | true | accepted | `unknown option` |

So the five new options exist **only** on the PC build, their ranges are enforced on the PC build,
and the base build rejects them by name — exactly as file 5 says. Note for other seats: a harness
that sends PC20 to the base build will get five `unknown option` lines and must stop on them, or
its "PC20 on the base tree" numbers are meaningless. My own scripts stop on those lines.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 HistRework 0..3 accepted, 4/−1 refused | **held** |
| P2 new options default-off change no pin | held (job17's default row is unchanged) |
| P3 `go wtime btime 50` does not lose the clock | **NOT held as I framed it** — the answer is immediate. The patch documents that as intended, so this is a framing error on my part, not a fault. Moved to suspicions. |
| P4 `go depth` with no value does not silently return the first legal move | **NOT held**: it answers `a2a3` with 0 nodes. Also documented as intended ("the answer comes at once"). Moved to suspicions. |
| P5 `go nodes abc` still searches | **NOT held**: immediate answer, documented as intended. |
| P6 MateAlphaGuard only on the PC build | **held** |
| P7 0 sanitizer lines, 0 crashes | held |

So three of my seven predictions were wrong in the same way: I assumed "unusable limit" should
still search, and the patch deliberately answers at once. My predictions were written from the
code comment's second half and not its first.

## Findings

None new. Two entries stay in "suspicions, not proven": whether `go wtime btime 50` keeps a
usable clock for one side, and whether bare `go` + `stop` yields exactly one bestmove (30-F1).

## What I did NOT do

- Did not instrument the `go wtime btime 50` parse to see which token landed in which parameter.
- Did not test 30-F1's `go` + `stop` form; I only observed that a bare `go` never ends, which is
  not the same question.
- Did not run these probes under a sanitizer with a planted fault.

## What I am NOT sure about

- Whether an immediate `a2a3` answer to `go wtime btime 50` is what the owner wants. The patch
  says it matches r9, so it is at least not a regression. A player with 50 ms and no increment
  would rather the engine used the 50 ms; but that is a design opinion, not a fault.

## Times

see `job21/stamps.txt`.
