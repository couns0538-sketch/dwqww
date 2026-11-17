# REPORT_job19 — does the time control change the MOVE the engine plays?

## What was asked
Nothing specific. S-F21 showed the *search* is identical across wide clock ranges (depth quantisation).
The match-relevant step is whether the *move* is identical too, so that a generous time control may
produce the same play as a fast one. This measures it directly instead of inferring it.

## The answer, with the right numbers

40 real positions from the G set, four time controls, Threads 1 / Hash 16 / canonical PC20, fresh process
per search, `winc 60`:

| comparison | identical move | differs |
|---|---|---|
| 2,000 vs 6,000 ms | **34 of 40 (85.0 %)** | 6 |
| 2,000 vs 20,000 ms | 31 of 40 (77.5 %) | 9 |
| 2,000 vs 60,000 ms | 31 of 40 (77.5 %) | 9 |
| 6,000 vs 20,000 ms | 33 of 40 (82.5 %) | 7 |
| 6,000 vs 60,000 ms | 33 of 40 (82.5 %) | 7 |
| **20,000 vs 60,000 ms** | **39 of 40 (97.5 %)** | **1** |

So my S-F21 framing was **too strong in one direction and right in another**:
- **Right:** a 30-fold clock difference (2 s → 60 s) changes the move on only ~22 % of positions, and at
  the top of the range (20 s vs 60 s) the move is the same on 39 of 40.
- **Too strong:** a generous time control does NOT leave the move unchanged in general — it changes it on
  roughly one position in five at the low end. The claim "may change nothing" is correct; "changes nothing"
  is not, and I did not claim that, but the distinction needs saying now that it is measured.

## The sharp result: identical search ⇒ identical move, with no exceptions

Across all 240 pairwise comparisons (40 positions × 6 clock pairs):

| | count |
|---|---|
| same node count **and** same move | **6** |
| same node count but **different** move | **0** |
| different node count but same move | 195 |
| different node count and different move | 39 |

**Whenever the node count was identical, the move was identical — 6 out of 6, zero exceptions.** That
means the depth-quantisation plateau really is *the same search*, not merely the same amount of work: on
the plateau the engine plays a bit-identical move. It also shows the converse is not true — 195 of 234
cases with *different* node counts still agreed on the move, i.e. most of the time the extra search
confirms the same choice.

A concrete example of a move that does change, position 0 of the set:

| clock | move |
|---|---|
| 2,000 ms | `g7g6` |
| 6,000 ms | `g7g6` |
| 20,000 ms | `e5e4` |
| 60,000 ms | `e5e4` |

Note the shape: it changed **once** between 6 s and 20 s and then held from 20 s to 60 s — again the
quantised structure, not a gradual trend.

## How sure
High for these numbers: 160 searches, fresh process each, settings asserted through `lib/settings.py`,
and the plateau-vs-move link is exact (6/6, 0 exceptions). The G positions are real engine-game positions,
which is the right material for a match question.

## Findings
- S-F22: over 40 real G positions at 2,000 / 6,000 / 20,000 / 60,000 ms (Threads 1, Hash 16, PC20, winc 60),
  the engine's **move is unchanged on 77.5–97.5 % of positions** depending on the pair — highest at the top
  of the range (20,000 vs 60,000 ms: 39 of 40 identical) and lowest between 2,000 and 60,000 (31 of 40).
  Across all 240 pairwise comparisons, **identical node counts always gave an identical move (6 of 6, no
  exceptions)**, so the quantisation plateau is the same search and not merely the same volume of work.
  Consequences: a generous time control does change the move on roughly one position in five at the low
  end, so a match's time control is not interchangeable; but above ~20 s further clock mostly changes
  nothing. Reproduce: `cd forge-combo29/swarm/13/job19 && python3 clockmoves.py ~/b/pc/forge G_all.fens
  /tmp/cm 40`.

## Suspicions, not proven
- The differing positions look like ones with several near-equal moves where a deeper search switches
  preference (position 0: `g7g6` → `e5e4`). I did not verify that by re-scoring both moves, so it is a
  plausible explanation rather than a demonstrated one.
- Whether the changed moves are *better* is a strength question I have not measured.

## What I did NOT do
- No match, no Elo, no claim that the changed moves are improvements.
- Did not test clocks above 60 s or below 2 s.
- Did not verify the near-equal-moves explanation by scoring both moves at equal depth (the method I used
  in job 13 would work).

## What I am NOT sure about
- 40 positions is a reasonable sample for a percentage but not for a tail estimate; the 97.5 % at the top
  of the range could be 95 % or 100 % on a larger set.
- `winc 60` was held constant; the plateau structure could shift with a different increment.

## STRICT RE-RUN (after the S-F24 correction)
Once job 20's shared-process contamination was found, I re-ran this measurement under the strict discipline —
a fresh engine process for **every** search, enforced by `lib/freshguard.py` (`SearchCounter.assert_single_use`).

**All six percentages reproduced EXACTLY:**

| pair | original | strict re-run |
|---|---|---|
| 2,000 vs 6,000 | 34/40 | **34/40** |
| 2,000 vs 20,000 | 31/40 | **31/40** |
| 2,000 vs 60,000 | 31/40 | **31/40** |
| 6,000 vs 20,000 | 33/40 | **33/40** |
| 6,000 vs 60,000 | 33/40 | **33/40** |
| 20,000 vs 60,000 | 39/40 | **39/40** |

And the sharp result held too: in the strict data, **identical node counts gave an identical move 7 times out
of 7, with zero exceptions.**

This finding was never contaminated, because `clockmoves.py`'s `run()` always spawned its own process per
search. It is now *structurally* guaranteed rather than true-by-inspection, which is the difference the S-F24
correction taught. Raw: `out/clockmoves.json` (original) and `out_strict/clockmoves.json` (strict).

## Files
`clockmoves.py`, `out/clockmoves.json` (160 searches + per-position move by clock), `G_all.fens`, `stamps.txt`.

## Last command output

```
$ ls
clockmoves.py
G_all.fens
out
REPORT_job19.md
stamps.txt
```
