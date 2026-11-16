# seat 20 — job 33: confirmation of seat 30's 30-C4 at Threads 1, and a correction to my own audit

## The confirmation (highest-value item on my re-run queue)

Seat 30's 30-C4 claims: base tree collapses a halfmove-100 root to `cp 0`/0 nodes; the PC r15 build under PC20
searches it like any other, including on a quiet (non-mating) board. **Every number of theirs reproduces exactly**
on my harness, `Threads 1` stated explicitly, fresh process per search.

Their mate board `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1` (mate by `a1a8`), `go depth 6`:

| halfmove | base 6b98f217 + S14 | PC r15 + PC20 |
|---|---|---|
| 0 | a1a8 / **mate 1** / **126** nodes | a1a8 / **mate 1** / **126** nodes |
| 97 | a1a8 / mate 1 / 126 | a1a8 / mate 1 / 126 |
| 98 | a1a8 / mate 1 / 126 | a1a8 / mate 1 / 126 |
| 99 | a1a8 / mate 1 / 126 | a1a8 / mate 1 / 126 |
| **100** | **f2f3 / cp 0 / 0 nodes** | **a1a8 / mate 1 / 126** |
| 101 | f2f3 / cp 0 / 0 | a1a8 / mate 1 / 126 |
| 150 | f2f3 / cp 0 / 0 | a1a8 / mate 1 / 126 |

Their quiet board `r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1`, `go depth 6`:

| halfmove | base + S14 | PC r15 + PC20 |
|---|---|---|
| 0 | a2a3 / cp 6 / 1,742 | e1g1 / cp 8 / 1,738 |
| 99 | d2d3 / cp 3 / 1,084 | a2a3 / **cp 6 / 1,091** |
| **100** | **a2a3 / cp 0 / 0 nodes** | a2a3 / **cp 6 / 1,091** |

`cp 6 / 1091 nodes` at halfmove 100 on the PC build is **exactly** their published figure, and `126` on the mate
board likewise. Their sentence "the counter no longer changes the answer" is right: on the PC build hm 99 and hm 100
give the identical `cp 6 / 1091 / a2a3`.

**Verdict: CONFIRMS 30-C4** — build `PC r15` (base + file 5 patch, sha256 `d6bd72c531f785f4…`,
`-DFORGE_MATE_ALPHA_GUARD=1`), settings `PC20`, `Threads 1`, fresh process, `go depth 6`.

## Correction to my own audit — I mis-flagged that line

My thread audit put 30-C4 in the "UNSTATED" bucket. Reading their line again, it says explicitly
"**BASE 6b98f217, Threads 1/S14**" and "**PC r15, Threads 1/PC20**". So the flag was a **false positive** caused by
my regex looking for the digit `1` near the word "threads" within one line: their line writes "Threads 1/S14", which
my pattern did not match. My audit's 122-line count therefore includes an unknown number of false positives of this
kind, and the queue must be read with that in mind: a flagged line may already state its thread count.

I am not re-running the whole audit to fix the count (it would re-fetch every seat); I am recording the defect and
the one case I checked. What remains valid is the *method* (state the count, state the build) and the short list —
and the short list's top entry is now done.

## What this means for the PC-build picture
Seat 30's result and mine (S-F33) agree independently on the same pair of builds and settings:
- the drawn-root doors (halfmove and repetition) are **repaired on the PC build**;
- the repair holds on a *quiet* board too, not only on mate boards — seat 30's `cp 6 / 1091` is the evidence for
  that, and my own S-F33 used only mate boards;
- so the base-tree findings S-C1/S-C4/S-F13/S-F28 are confirmed base-tree-only by two independent harnesses.
