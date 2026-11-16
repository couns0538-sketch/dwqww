# The PC20 switches, isolated, on mate scores — seat 08, PC r15 build, Threads 1

Both tasks on **PC r15** (`/home/ubuntu/builds/pc/forge`), **Threads 1**, Hash 16, `go depth 12`, a fresh process
per cell. S14's 14 options are the base of every arm; `OwnBook false` also set.

- **B1** = seat 20's S-F19 / S-F38 board: `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`
- **B2** = seat 01's S-F19 board: `8/8/8/8/2K4Q/8/8/1k6 w - - 100 1`

## Task A — `MateAlphaGuard` alone, on top of S14

| board | arm | score | plies | nodes | pv length | bestmove | verdict |
|---|---|---|---|---|---|---|---|
| B1 | S14 only (no guard) | **mate −9** | 18 | 37,664 | 14 | c2b1 | — |
| B1 | S14 + **MateAlphaGuard true** | **mate −4** | **8** | 31,996 | 8 | c2b1 | **distance changed to the true one** |
| B1 | S14 + MateAlphaGuard false | mate −9 | 18 | 37,664 | 14 | c2b1 | no change |
| B2 | S14 only | cp 0 | — | 324 | 1 | h4e1 | — |
| B2 | S14 + MateAlphaGuard true | cp 0 | — | 324 | 1 | h4e1 | no change |
| B2 | S14 + MateAlphaGuard false | cp 0 | — | 324 | 1 | h4e1 | no change |

**Verdict on Task A: CONFIRMS seat 20's S-F38.** On B1 the guard alone moves the reported distance from
`mate −9` (18 plies) to `mate −4` (8 plies), the distance seat 20's exhaustive search established as true; the
same position with `MateAlphaGuard false` is byte-identical to no guard at all (same score, same 37,664 nodes).
So it is a **one-switch answer**, exactly as they said. My number differs from theirs (`mate −7` / 28,084 nodes in
their report, `mate −9` / 37,664 in mine) because they measured on bare defaults while I measured on top of S14 as
instructed; the switch's effect is the same in both.

The internal consistency check the brief names also passes: `mate −4` comes with an **8-ply PV** (= 2 × 4), while
`mate −9` comes with a 14-ply PV — a truncated line, which is itself consistent with a wrong distance.

**B2 is not a mate board for this purpose and I say so:** at halfmove 100 with a quiet-mate position the engine
returns `cp 0` in 324 nodes under every arm, so B2 cannot discriminate between switches. That is the draw
adjudication dominating (seat 01's S-F23 established B2's `cp 0` is *correct chess* there, since a draw is
claimable). No conclusion about the switches is drawn from B2.

## Task B — each PC20 SEARCH switch alone, on the same board

| arm (on top of S14) | B1 score | plies | nodes | bestmove | verdict |
|---|---|---|---|---|---|
| S14 only (baseline) | mate −9 | 18 | 37,664 | c2b1 | — |
| + CuckooRep true | **mate −13** | 26 | 26,914 | c2b2 | **distance WORSE** |
| + HistRework 2 | mate −7 | 14 | 22,910 | c2b2 | closer to true |
| + TtPruneV2 true | mate −7 | 14 | 22,457 | c2b1 | closer to true |
| + CorrHistV2 true | mate −8 | 16 | 22,693 | c2c3 | closer to true |
| + all four | mate −7 | 14 | 21,898 | c2b1 | closer to true |

One line per switch, against the true distance `mate −4`:

- **`CuckooRep true` alone is WORSE than doing nothing:** `mate −13` (26 plies) against the baseline `mate −9`
  (18 plies), and it also changes the move to `c2b2`. This is the switch the owner should not turn on alone.
- **`HistRework 2` alone**: `mate −7` (14 plies) — an improvement on the baseline, still short of the true −4.
- **`TtPruneV2 true` alone**: `mate −7` (14 plies) — same improvement, keeps the move `c2b1`, and is the cheapest
  of the improving arms at 22,457 nodes.
- **`CorrHistV2 true` alone**: `mate −8` (16 plies) — a small improvement, and it changes the move to `c2c3`.
- **All four together**: `mate −7` (14 plies) — no better than `TtPruneV2` alone, and it does not undo CuckooRep's
  move change.

`MateAlphaGuard true` remains the only arm that reaches the true distance on its own.

## The consequence for the owner, stated plainly

Turning on the four PC20 search switches does **not** fix the mate distance, and one of them (`CuckooRep`) makes it
worse by itself. The mate distance is fixed by **`MateAlphaGuard true`**, which is not a search switch but a guard
on the mate scoring — and PC20 happens to include it, which is why a PC20-vs-base comparison shows the distance
fixed and cannot say which option did it. This is exactly seat 20's S-F40 warning about the bundle, confirmed
independently from the other direction.

## Controls (enforced — a failure aborts rather than printing a verdict)
- every cell reached depth 12 with a parsable score;
- the S14 baseline was measured twice (once in Task A, once in Task B) and gave the **same** score on both boards
  (`mate −9` on B1, `cp 0` on B2), which is the repeatability proof that Threads 1 was stable throughout;
- the two arms with `MateAlphaGuard false` are byte-identical to no guard, so the option is being read and applied,
  not silently ignored;
- an `invalid FEN` or `unknown option` answer would have aborted the run — neither occurred.

## What I did NOT do
- Did not re-derive the true mate distance (8 plies); I rely on seat 20's exhaustive proof and checked only internal
  consistency (PV length against the score).
- Did not test more than one depth, one board per task A purpose (B2 does not discriminate), or any clock control.
- Did not test the switches at Threads > 1 (the rule, and 08-C8 shows why).

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_switches.py /tmp/sw.txt
