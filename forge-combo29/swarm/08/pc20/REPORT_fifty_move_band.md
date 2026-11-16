# The fifty-move cliff: a SCORE band but a NODE SPIKE — seat 08, PC r15 under PC20

Follows 08-C6, which confirmed seat 05's fifty-move score floor at H=91 and noticed 7,251,835 nodes beside 14,470
at H=0. This section answers whether that cost is one counter or a band, by sweeping **every** counter from 85 to 99
on the same won board, one fresh process each, `go depth 10`, PC20, Threads 1.

| H | score | nodes | × median | |
|---|---|---|---|---|
| 85 | mate 8 | 35,652 | 0.4x | |
| 86 | cp 294 | 87,480 | 1.0x | |
| 87 | cp 342 | 67,952 | 0.8x | |
| 88 | cp 271 | 178,232 | 2.0x | |
| 89 | cp 279 | 306,279 | 3.5x | |
| 90 | cp 231 | 930,573 | 10.6x | climbing |
| **91** | **cp 0** | **7,251,835** | **82.9x** | **SPIKE** |
| 92 | cp 0 | 1,459,778 | 16.7x | shoulder |
| 93 | cp 0 | 1,004,522 | 11.5x | shoulder |
| 94 | cp 0 | 108,603 | 1.2x | |
| 95 | cp 0 | 81,364 | 0.9x | |
| 96 | cp 0 | 9,329 | 0.1x | |
| 97 | cp 0 | 4,729 | 0.1x | |
| 98 | cp 0 | 541 | 0.0x | |
| 99 | cp 0 | 200 | 0.0x | draw recognised at once |

## The two effects have different shapes, and only one of them is a band

**The SCORE defect is a band: H = 91 through 99 all score exactly cp 0** on a board where White is a rook up and no
draw can be claimed. Above 99 the engine short-circuits to a draw for 200 nodes, correctly in form (the counter has
reached the fifty-move limit) and wrongly in substance (the position is won, and a rook mate is well within 50
moves). So the wrong verdict covers at least nine consecutive counter values — this is not one unlucky counter.

**The NODE cost is a single spike at H=91**, with a short shoulder at 92–93, not a band:

| counters more than 20x the band median | H=91 only |
|---|---|
| counters scoring cp 0 | H=91 … 99 (nine) |
| median nodes over the band | 87,480 |
| largest | 7,251,835 at H=91 (82.9x the median) |
| smallest | 200 at H=99 |

So the honest statement is **two facts, not one**:
1. a scoring defect spanning H=91–99 (any long game approaching the fifty-move limit will be scored as drawn while
   still won);
2. a one-off performance cliff at exactly H=91, where the engine spends 7.25 million nodes to reach that wrong
   verdict — 82.9x the band's median and 500x its own cost at H=0.

The cliff at 91 is where the search horizon (depth 10 from H=91 reaches 101) first crosses the limit, so the engine
searches the full tree trying to prove a win it then refuses to score. From 92 on the refusal happens earlier in the
search and costs less; by 94 it is cheaper than a normal search of this position.

**Consequence for a long game:** the score is wrong for the whole 91–99 band, so the engine will steer to a "draw"
with a rook on the board for nine moves. The 7.25M-node spike is a one-move cost, not a repeated one — it is a
symptom of the same defect crossing its boundary, not a separate chronic performance problem.

## What this changes in the findings
- 08-C6 stands; this section refines its "500x blow-up" remark into the correct shape: the cost is a spike, the
  score is a band.
- New finding **08-F22** records the band-vs-spike distinction with these numbers.

## Controls (enforced, abort on failure)
- every counter produced a parsable depth-10 score, and depth 10 was reached at every counter;
- the node counts are not all equal (the harness reads a fresh search, not a cached value);
- H=0 scores **cp 490**, a win — the planted case proving this harness can report a win on this board, so the later
  cp 0 values cannot be a reading artefact.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 blowup_band.py ~/builds/pc/forge /tmp/bb.txt
