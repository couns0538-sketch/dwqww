# REPORT job22 — 30-F1 checked properly on both builds (go + stop), Threads 1

**What was asked.** (My own next step after job21's near-miss.) Seat 30's 30-F1 claims the engine
prints EXACTLY ONE bestmove per `go` line, including malformed ones. My job21 probe could not test
it, because a bare `go` never ends without `stop`.

**The answer.** **CONFIRMS 30-F1 on BOTH builds.** Each of seven `go` lines yields exactly one
legal bestmove after a `stop`, and the answer arrives 0–4 ms after the stop.

**How sure.** High. Every case is a fresh process, Threads 1, `position startpos` + `isready`
before the `go`, a fixed 350 ms wait, then `stop`, then a 1.2 s read window counting bestmoves.
The latency is measured at the FIRST bestmove seen, not at the end of the window (my first
version timed the window and reported a false ~1201 ms for every case; that bug is fixed and the
corrected numbers are below — the old numbers are still in the git history of this folder).

## Table (pasted from `job22/out/summary.md`)

| build | go line | bestmoves | count | stop→bestmove ms | legal |
|---|---|---|---|---|---|
| pc | `go banana` | `e2e4` | 1 | 0.8 | yes |
| pc | `go depth -3` | `d2d4` | 1 | 0.0 | yes |
| pc | `go` | `e2e4` | 1 | 4.3 | yes |
| pc | `go depth 0` | `d2d4` | 1 | 0.0 | yes |
| pc | `go nodes 0` | `a2a3` | 1 | 0.0 | yes |
| pc | `go movetime 0` | `a2a3` | 1 | 0.0 | yes |
| pc | `go depth 5` (control) | `c2c4` | 1 | 0.1 | yes |
| base | `go banana` | `e2e4` | 1 | 0.8 | yes |
| base | `go depth -3` | `d2d4` | 1 | 0.0 | yes |
| base | `go` | `e2e4` | 1 | 1.4 | yes |
| base | `go depth 0` | `d2d4` | 1 | 0.0 | yes |
| base | `go nodes 0` | `a2a3` | 1 | 0.0 | yes |
| base | `go movetime 0` | `a2a3` | 1 | 0.0 | yes |
| base | `go depth 5` (control) | `c2c4` | 1 | 0.1 | yes |

## Prediction outcome

P1–P5 all held.

## Findings

`21-C7 | CONFIRMS 30-F1` — on the PC build AND the base build, seven `go` forms including four
malformed ones each produce exactly one legal bestmove after `stop`, within 4 ms. The finding was
made on the base tree; this extends it to the PC build and documents that a test of it must send
`stop` (without one, a bare `go` is a legal infinite search and never answers — which is how I
first mistook it for a hang).

## The mistake this job corrects

In job21 I recorded `go banana`, `go` and `go xyzzy` as "hangs" and nearly filed a REFUTES of
30-F1. They are legal infinite searches. 30-F1 was right and my harness was wrong. The REFUTES
was never filed; this job replaces the observation with the right experiment.

## Suspicions, not proven

- `go depth -3` and `go depth 0` both answer `d2d4` with 26 nodes in ~0 ms — i.e. depth clamped
  to 1, as the patch documents. Whether `go nodes 0` answering `a2a3` immediately is "one node
  searched" or "no limit recognised" I did not instrument.

## What I did NOT do

- Did not test `go` lines with a value *and* an unknown keyword interleaved beyond `go depth 5
  banana` in job21.
- Did not run this under a sanitizer with a planted fault (no memory question here).

## What I am NOT sure about

- Whether a GUI ever sends `stop` before the bestmove of a *finite* go; if it does, whether the
  engine's stop path is as clean there. My cases stop only infinite or instant searches.

## Times

see `job22/stamps.txt`.
