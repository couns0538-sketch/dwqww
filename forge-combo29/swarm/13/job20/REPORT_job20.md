# REPORT_job20 — do the moves that change with the clock get BETTER or WORSE?

> **THIS REPORT IS SUPERSEDED. Its numbers were contaminated by reusing one engine process across all
> searches, which shifts scores by up to 80 cp on identical requests and manufactured changes that do not
> exist in fresh processes. Read `CORRECTION_S-F24.md` in this folder for the corrected measurement
> (1 of 16 positions changes, +17 cp) and for the demonstration of the contamination. The findings line
> S-F24 now carries the corrected numbers. Everything below is kept unchanged as the record of what was
> measured and why it was wrong.**

## What was asked
Nothing directly; this closes a caveat I have repeated in every clock report: *"whether the changed moves
are better is not measured."* S-F22 showed the move changes on ~1 position in 5 between 2 s and 60 s. This
measures the direction of that change, as far as it can be done honestly without a match.

## The answer: the longer clock's move is better, 4 times out of 5

16 G positions, 2,000 ms vs 60,000 ms (PC20, Threads 1, Hash 16, winc 60). 5 positions changed their move:

| position | 2 s move (depth) | 60 s move (depth) | gap (long − short) |
|---|---|---|---|
| 0 | `g7g6` (d15) | `e5e4` (d25) | **+3 cp** |
| 6 | `c8c3` (d13) | `c8e8` (d26) | **+156 cp** |
| 7 | `g5h6` (d17) | `g5h5` (d21) | **+58 cp** |
| 14 | `e6d7` (d14) | `e6g4` (d25) | **−33 cp** |
| 15 | `c6b5` (d14) | `h6h5` (d24) | **+984 cp** |

| summary | value |
|---|---|
| positions changing move | 5 of 16 |
| longer-clock move **better** | **4** |
| longer-clock move **worse** | **1** |
| equivalent at depth 16 | 0 |
| median gap | **+58 cp** |
| median depth, 2 s | 15 |
| median depth, 60 s | **24** |

So the direction is clear even at this sample size: **when the clock changes the move, the slower move is
usually the better one**, by a median of about half a pawn, and the mechanism is visible in plain sight —
the longer clock reaches median depth 24 against 15.

## The outlier, checked rather than assumed
The +984 cp case is position 15, `8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - 0 1` — black to move, and black is
lost (engine: about −2,300). A gap that large deserved verification, so I re-derived it by hand:

| 2 s move `c6b5` | 60 s move `h6h5` |
|---|---|
| white's score at depth 16 = **+3,231** → black −3,231 | white's score at depth 16 = **+2,231** → black −2,231 |

So the gap is real: both moves lose, but the shallow search walks into something ~1,000 cp worse. That is
exactly the shape you would want — the 60 s search is avoiding a deeper disaster, not finding a win.

## How it was measured (the equal-depth step matters)
For each changed move I did not compare the two clock searches' own scores — they reach different depths, so
that would confound move quality with search time. Instead I **played each move and searched the resulting
position at a fixed depth 16**, negating for the side-to-move flip. Both candidates are therefore judged by
the same search. That is the same technique as job 13, adopted for the same reason.

## Limits, stated plainly
- **Self-consistency, not ground truth.** The judge is the same engine that chose the moves. A systematic
  bias in its evaluation would appear on both sides, so this measures "does more time make the engine's own
  opinion of its move better", not "is the move objectively better".
- **Depth 16 is an arbitrary judge.** It is deeper than either clock search on most of these positions but
  not all (the 60 s search reached depth 25–26 twice). Where the judge is shallower than the clock search,
  the comparison is weakest.
- **5 changed positions out of 16.** Small. The 4–1 split is suggestive, not significant; I am reporting the
  median and the direction, not a p-value.
- **A score difference is not a game result.** A +58 cp median improvement does not have to convert to Elo.

## Findings
- S-F24: when the time control changes the engine's move (5 of 16 G positions between 2,000 and 60,000 ms),
  the longer clock's move is **better by the engine's own equal-depth judgement in 4 of 5 cases**, median
  **+58 cp**, with the mechanism visible as median depth 15 → 24. One case is worse by 33 cp; the largest
  gain (+984 cp) was hand-verified as real (the shallow search walks into a ~1,000 cp worse continuation in
  an already-lost position). **This is a self-consistency measure, not ground truth, and no match was run** —
  it does not establish an Elo difference. Reproduce: `cd forge-combo29/swarm/13/job20 && python3
  clockgain.py ~/b/pc/forge G_all.fens /tmp/cg 16 16`.

## Suspicions, not proven
- The one case where more time made the move *worse* (−33 cp) is within plausible evaluation noise at
  depth 16; I have not tried to determine whether it is noise or a genuine horizon artefact.

## What I did NOT do
- No match, no Elo. This is the closest honest proxy I can build without one.
- Did not extend beyond 16 positions or beyond the 2 s / 60 s pair.
- Did not judge with an independent engine (would be a genuinely independent oracle, but that means
  importing another engine's opinion, which the brief's "do not copy code" rule does not forbid but which I
  did not do).

## What I am NOT sure about
- The direction is probably real, but 5 changed positions is a small base. A larger set would be needed to
  say more than "usually better".
- Depth 16 as judge is defensible but arbitrary; at depth 20 the gaps could shrink or grow.

## Files
`clockgain.py`, `out/clockgain.json` (16 positions, both clock results, both equal-depth scores), `G_all.fens`,
`stamps.txt`.

## Last command output

```
$ ls
clockgain.py
G_all.fens
out
REPORT_job20.md
stamps.txt
```
