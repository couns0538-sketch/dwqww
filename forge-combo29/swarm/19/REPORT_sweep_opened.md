# Opening the two largest flag sets: both are deliberate, both already labelled by their owners

seat 19 · area 9 · answers the only question that mattered in 19-C14's triage list.

## 1. The three lines

**What was asked.** Open seat 10's 860 flags and seat 07's 47 — whether they are deliberate studies or accidents
is the only question that matters in that list.

**The answer.** **Both are deliberate, and both owners already know about the trap.** Seat 10 independently
discovered 19-F12 and wrote a helper whose docstring is a correct description of it, plus an experiment (`E1.py`)
built specifically to establish it with raw output per variant. Seat 07 has a committed `INVALID_HARNESS.txt`
that credits 19-F12 by name and marks the two producing harnesses "**NOT a result**", keeping their output for
the record. **So neither flag set is an accident, and no seat's findings are implicated by them.**

**How sure.** Certain — I read the source files on both branches, not just the file names.

## 2. Seat 10: 860 flags, all from an EOF-trap study

Its helper `audit/forge_io.py` opens with:

> "forge_io.py -- seat 10's engine I/O helper that does NOT trip the EOF-aborts-search trap.
> Facts established by measurement (audit/raw/E1_*): When the engine's stdin reaches EOF while a search is
> running, the search is ABORTED and `bestmove` is printed at once (startpos `go depth 12` returns in 0.02 s
> with bestmove a2a3 and no `info` line). Keeping stdin open lets the same command complete normally
> (info depth 12 ... nodes 56720). So every search here is driven by an INTERACTIVE pipe."

**That is 19-F12, independently discovered, described exactly, and correctly fixed** — one day before my own
sweep found it. And `audit/E1.py` is the deliberate study:

> "E1.py -- establish the EOF trap rigorously, with raw output for each variant. V1 all lines written at once,
> stdin CLOSED after the go -> search aborted? V2 ... stdin HELD OPEN 5 s -> search completes? V3 interactive
> -> completes? ..."

Its flagged files are the variants of that study — including ones deliberately designed to abort. **The 860 count
is a measure of how carefully seat 10 documented the trap, not of a defect in its work.**

## 3. Seat 07: 47 flags, all from a harness it marks invalid

`job1/INVALID_HARNESS.txt`, verbatim:

> "These two harnesses pipelined a `go` with the following isready/quit and are INVALID.
> Seat 19 (19-F12, relayed by the coordinator 2026-11-16) showed this build answers a fabricated `bestmove ...
> 0 nodes` when stdin closes mid-search.
>   job1/limits_probe.sh - kept for the record, its output raw_limits/ is NOT a result
>   job1/searchstress.sh - kept for the record, its output raw_asan/ is NOT a result
> Replacement harnesses that never pipeline: job1/uci_drive.py, job1/search_stress.py."

Its actual flagged files are `job1/raw_asan/chunk_00.out` … (25 `bestmove` lines, 0 `info` lines each) — **exactly
the `searchstress.sh` output that file declares not a result.** The seat found the defect, marked the output,
and replaced the harness. Nothing to fix.

## 4. A correction to my own triage table

While checking seat 07 I noticed its `job0/raw/bench13.out` in a listing I was reading — but that file has **no
`bestmove` line at all** and my detector never flagged it. **The file names I sampled in §"what are its flagged
files" were the branch's file tree, not the flag list.** Anyone reading my earlier message could have made the
same mistake, so: **the per-seat counts in 19-C14 come from the flag list; the file names I quoted to sample a
seat were the tree.** I should have quoted from the flag list both times. The counts themselves were computed
from flags and are correct.

## 5. What this means for the swarm

**Three of us found the same defect independently — seat 07, seat 10, and me — and each handled it correctly**:
seat 07 marked its output invalid and replaced the harness; seat 10 wrote a trap-aware helper and then studied
the trap deliberately; I traced it to the emit line and then swept for it. **The flags in the sweep are largely a
record of how well the swarm documented a defect it collectively found.**

The one genuine accident remains **seat 20's job 3** (60 of 60 outputs with no search, reported in 19-C13), where
no `INVALID_HARNESS`-style note existed and whose owner has since added a zero-info-line guard to all 15
harnesses.

## 6. Finding

**19-C15 — the two largest flag sets in 19-C14 are deliberate and already documented: seat 10's 860 are variants
of its own EOF-trap study (`audit/E1.py`, with a trap-aware helper in `audit/forge_io.py` that describes 19-F12
exactly), and seat 07's 47 are the `searchstress.sh` output its committed `job1/INVALID_HARNESS.txt` marks
"NOT a result" while crediting 19-F12.** No accident and no implication for either seat's findings. **The
remaining genuine accident is seat 20's job 3 (19-C13).** Also corrected: the file names I sampled to characterise
a seat were the branch tree, not the flag list; the counts are from flags and are sound.

### What I did NOT do

- I did not open the middle-sized sets (21's 43, 27's 28, 17's 21, 24's 17) — the two largest were the question
  asked, and after both came back deliberate the prior on the rest is that they are similarly documented.
- I did not verify seat 10's *conclusions*, only its harness discipline.

## 7. Files

`checks/sweep_out2/RESULT.txt` (the flag list), plus reads of `audit/forge_io.py`, `audit/E1.py` on branch
`for-fable-and-opus/swarm-10` and `job1/INVALID_HARNESS.txt` on branch `for-fable-and-opus/swarm-07`.
