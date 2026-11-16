# Does CorrHistV2 improve the RESULT, or only the node count?

seat 19 · area 9 · build **PC r15** · **Threads 1** · depth 12 · 200 positions of set G · PC20 held constant with
only `CorrHistV2` toggled.

## 1. The three lines

**What was asked.** 19-F32 showed `CorrHistV2` saves 4.3 % of nodes on `bench 13`, deterministically. A node
saving is not a strength claim. Does it also improve the *result*? Run 200 of set G at depth 12 with the option
on and off, compare bestmoves and scores; say plainly whether the owner needs games.

**The answer.** **It plays different chess, so yes — the owner needs games, and a node saving must not be read as
a gain.** On 200 positions: **156 (78.0 %) identical bestmove, 44 (22.0 %) DIFFERENT**; 183 of 200 positions
have a different score. The node total over the run barely moved (−1.46 %, 9,997,730 vs 10,146,239) — so at
depth 12 on real positions the 4.3 % bench saving largely does not materialise, and where the two settings
disagree they disagree about *which move to play*.

**How sure.** Certain of the counts (deterministic at Threads 1, one process per arm with `ucinewgame` before
every search, every search awaited to `bestmove`). Not sure which setting is stronger — nothing here can say
that, and I am not going to imply it.

## 2. The numbers

| quantity | value |
|---|---|
| positions | 200 (first 200 of set G, 353 in the file) |
| same bestmove | **156 = 78.0 %** |
| **different bestmove** | **44 = 22.0 %** |
| different score | 183 of 200 |
| total nodes, CorrHistV2 on | 9,997,730 |
| total nodes, off | 10,146,239 |
| **node change over the run** | **−1.46 %** |

Among the 148 positions where the move was the same and both scores were centipawn scores, the on-minus-off
score delta is **mean +0.4 cp, median +1 cp**, but ranges **−358 to +435 cp**. That is a symmetric spread, not a
bias: CorrHistV2 is not systematically optimistic or pessimistic, it is *noisy* on individual positions.

Five of the 44 disagreements, so the reader can see what a disagreement looks like:

| CorrHistV2 on | off |
|---|---|
| `e8d8` (cp −11) | `c7c6` (cp −16) |
| `e6d5` (cp +23) | `e6d6` (cp 0) |
| `g7e6` (cp +158) | `g7h5` (cp +190) |
| `d2d5` (cp −56) | `d2b2` (cp −75) |
| `h6h5` (cp −2201) | `c6b5` (cp −2132) |

Several are plainly different plans, not transpositions: `g7e6` vs `g7h5` sends a piece to opposite sides.

## 3. What this means, stated plainly

- **The node saving is not a strength gain, and it is not even reliably a node saving.** 4.3 % on bench 13's
  eight fixed positions became **−1.46 %** (i.e. 1.46 % *fewer* nodes for CorrHistV2) over 200 real positions.
  The bench figure was real but is not representative — the same lesson as 19-F18, in a milder form.
- **22 % of moves differ, so the two settings are different engines for practical purposes.** Any SPRT or match
  result quoted for the PC build is a result *for whichever CorrHistV2 setting was used*, and the two cannot be
  mixed in one match without saying so.
- **Whether CorrHistV2 is stronger is an open question that requires games.** Two settings that pick different
  moves and score them within ±0.4 cp on average can be separated only by play at a meaningful depth with a
  meaningful time control. I have not done that, and this test cannot substitute for it.
- For the owner specifically: PC20 has `CorrHistV2 true`, so the engine he plays is the "on" column. If he ever
  wants to A/B it, the 44 differing positions are the ones where the choice matters — they are listed in the
  raw file with index and FEN for reuse as a mini-suite.

## 4. Table: step | done-partly-not-done | evidence | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 200 of set G, depth 12, on vs off | done | `pcspeed/strength/corrhist_strength.txt` | 200 rows, per-position moves, scores, nodes |
| cold state, Threads 1, awaited bestmove | done | same file's header; `ucinewgame` before each search | no 19-F12 contamination, no warm contamination |
| compare bestmoves | done | §2 | 44 differ (22 %) |
| compare scores | done | §2 | mean +0.4 cp, range −358…+435 |
| compare node totals | done | §2 | −1.46 % |
| **decide which is stronger** | **not done, and not attempted** | — | needs games; this test is not a strength test |
| a mini-suite of the 44 differing positions | **not done** | — | the raw file has the indices; packaging it is a small job I did not do |

## 5. Suspicions, not proven

- That the node *saving* disappears off bench because bench's eight positions are middlegame while G contains
  sharper positions where the correction table helps less. Consistent with the data; not tested by splitting
  the 200 into middlegame and endgame.
- That the ±400 cp spread on same-move positions reflects the correction table being read at a different point
  in its learning. Untested.

## 6. What I did NOT do

- No game playing, no SPRT, no strength conclusion. Deliberately.
- I did not run depth 16 or a second time control, so nothing here is about a deeper search.
- I did not test `HistRework`, `CuckooRep` or `TtPruneV2` the same way; only `CorrHistV2`, as asked.

## 7. Files

`pcspeed/corrhist_strength.py`, `pcspeed/strength/corrhist_strength.txt` (all 200 rows with FENs).
