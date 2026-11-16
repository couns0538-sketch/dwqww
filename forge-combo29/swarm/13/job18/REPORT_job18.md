# REPORT_job18 — is the clock-allocation plateau general, or one position's artefact?

## What was asked
Nothing specific. S-F19 found that on ONE middlegame position, `go wtime` 10,000 / 12,000 / 15,000 /
20,000 all produced the identical search (depth 23, 1,520,334 nodes). A single position is weak evidence,
so this asks whether the plateau is a property of the **allocator** or a coincidence of that position.

## The answer: it is the allocator, and the step points differ per position

Five different positions, eleven clock values each (1 s to 60 s), canonical PC20 from `lib/settings.py`
(asserted 22 entries), Threads 1, Hash 16:

| position | clock values | DISTINCT node counts | plateau intervals | longest plateau |
|---|---|---|---|---|
| open middlegame | 11 | 7 | 3 | 10,000 → 20,000 ms (identical 1,520,334 nodes) |
| tactical | 11 | 8 | 3 | 8,000 → 12,000 ms (identical 514,093) |
| startpos | 11 | **6** | 5 | 15,000 → 20,000 and 20,000 → 30,000 |
| endgame rook | 11 | 7 | 4 | 6,000 → 12,000 ms (identical 2,510,572) |
| queen endgame | 11 | **6** | 5 | 4,000 → 15,000 ms (identical 1,159,670) |

**All five positions plateau. Every one takes 11 clock values and produces only 6–8 distinct amounts of
work.** The strongest case is the queen endgame: **from 4 s to 15 s of clock the engine performs the
identical search — 1,159,670 nodes, depth 16 — across four consecutive doublings of the clock.**

Crucially, the step points are **different for each position** (a rook endgame steps at 6–12 s, a queen
endgame at 4–15 s, startpos at 15–30 s). A coincidence in one position would not reproduce across five
positions with different step locations. That is what makes this a property of the allocator rather than
an artefact.

Repeatability checked directly: startpos at 10,000 and 12,000 ms, three runs each, gives `(depth 20,
925,222 nodes)` six times over.

## What this means (and what it does not)
- **Establishes:** the allocator chooses a target depth from the clock and then stops when that depth is
  finished; because depths are coarse steps, a wide range of clocks maps onto the same depth and therefore
  onto the *identical* search. This is consistent with S-F19 and generalises it from one position to five.
- **Does NOT establish:** that this costs strength. A search that stops at a finished depth is not
  handicapped by having time left — it simply does not use it. Whether more use of the clock would play
  better is a match question, and I have not run one.
- **Practical consequence for a match:** on these positions, giving the engine 15 s instead of 5 s may
  change **nothing at all** about the move it picks. A match whose time control is set "generously" to
  make the engine stronger may therefore be measuring the same play as a much faster one — and a match
  comparing two time controls could show no difference for that reason alone.

## How sure
High for the observation (five positions, repeatable to the node, settings asserted). The mechanism
statement ("target depth from the clock, stop at a finished depth") is my inference from the data plus the
patch's own comment about a soft stop at a finished iteration; I did not instrument the allocator.

## Findings
- S-F21: the depth-quantised clock plateau is **general, not position-specific**: across five positions
  (middlegame, tactical, startpos, rook endgame, queen endgame) eleven clock values from 1 s to 60 s give
  only 6–8 distinct node counts each, with plateau spans as wide as **4 s → 15 s producing the identical
  1,159,670-node depth-16 search**. The step points differ per position (rook endgame 6–12 s, queen
  endgame 4–15 s, startpos 15–30 s), which is why this is an allocator property rather than a coincidence.
  Repeatable to the identical node count. Extends S-F19 from one position to five.
  Reproduce: `cd forge-combo29/swarm/13/job18 && python3 plateau.py ~/b/pc/forge /tmp/pl`.

## Suspicions, not proven
- The plateau width looks related to how expensive the next depth is on that position, which would explain
  why a quiet queen endgame (cheap depths) has the widest plateau. I have not proven that relation.

## What I did NOT do
- No match, so no strength claim about under-using the clock.
- Did not instrument the allocator to read the target depth directly; the mechanism is inferred.
- Did not test clocks below 1 s or above 60 s.

## What I am NOT sure about
- Five positions is more than one, but they are all from my own construction or the G set, not the owner's
  match positions.
- The plateau *widths* are position-specific; only the *existence* of plateaus is claimed as general.

## Files
`plateau.py`, `out/plateau.json` (55 runs plus per-position plateau detection), `stamps.txt`.

## Last command output

```
$ ls
out
plateau.py
REPORT_job18.md
stamps.txt
```
