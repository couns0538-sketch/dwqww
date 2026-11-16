# THE EXPOSURE NUMBER FOR THE OWNER'S MATCHES: ZERO defects on 100 real game positions

Seat 25. PC r15, PC20, Threads 1, Hash 16, `go nodes 20000` - the owner's actual match setting. Positions: the
first 100 of set G (real game positions from played games).

## The result

| measure | count |
|---|---|
| positions tested | 100 |
| mate scores in the **final** info line | **1** |
| of those, final answer WRONG (PV illegal or not mate at the claimed distance) | **0** |
| mate scores across **all** info lines | **48** |
| lines whose PV contains an **illegal move** | **0** |

So on real game positions at the match setting, the defect I found in S-F27 **does not appear**: no wrong final
mate label, and no unreplayable PV in any of the 48 mate-scored intermediate lines.

## What this means, and how it changes the headline

I have to correct the emphasis I sent earlier. My S-F27 board
(`8/8/1p6/8/p3p3/8/2Kpk3/8 w`) is a **constructed bare endgame** where white is mated in 4 and the search burns
through mate lines fast. There, at `go nodes 20000`, an intermediate depth-8 line carries an illegal move
(`b2a2`) and a mate number the finished depth-8 search never had - and that is real, reproducible (5/5), and
caused by the partial-iteration publish that `FORGE_FIX_ABORT_PUBLISH` guards and which is **compiled out by
default** (`#define FORGE_FIX_ABORT_PUBLISH 0`, src/search.cpp:76-77; its own comment says it was measured and
"is not a repair").

But it is **not** what the owner's matches do. Middlegame positions at 20k nodes essentially never reach a mate
line (1 final mate score in 100 positions), and in those 48 mate-scored lines there were no illegal PVs.

**The corrected headline: a real but narrow display defect in intermediate mate PVs, which my measurements do not
show reaching the owner's match path. It is NOT a match-path defect.** My earlier "LIVE DEFECT on the owner's
match setting" wording was too strong and this file supersedes it; the correction is also recorded as S-C9/S-C10
in FINDINGS.md rather than edited away.

## Where it would still matter
A consumer that parses **every** `info` line rather than the final one, on **endgame** positions, at **small node
budgets**. That includes: a GUI drawing the PV live during an endgame, and any training pipeline that labels from
streaming info lines instead of the final one. If the owner's self-play labels only the final line (the normal
way), it is unaffected.

## The guard, confirmed from the source (task 1 of the previous message)
- `FORGE_FIX_ABORT_PUBLISH` **exists** (src/search.cpp:65-78) and documents exactly this failure: a search stopped
  mid-iteration answers with a move/line from the unfinished iteration.
- It is **compiled OUT by default** (`#define ... 0`), and the comment records that it was measured on 19,800
  exact-node stops over 300 opening positions and found **not** to be a repair (the finished move scored 14 cp
  lower on average), so it was deliberately left off.
- The publish block is additionally gated on `!stopped_by_nodes_` even when enabled, so a **node** stop never
  takes that path - which is why enabling the flag would not fix this case either.
- Instrumentation confirmed the sequence: `depth=11` finished (`mate -7`, 14-ply PV, verified mate), then
  `[NDB ABORTED] depth=12 stopped_by_nodes=1 pv_len=0` - the abort itself publishes nothing; the bad line came
  from an earlier depth's emission.

## Honest summary of what I got wrong tonight (all recorded, none edited away)
1. Concluded the clock-99 zero was correct; withdrew it (`debug/CORRECTION.md`).
2. Hand-wrote that `h6h5` was a pawn push; it is a capture (`debug/COST_FINAL.md`).
3. A check compared a regex match to `"cp 0"` when it returns `"score cp 0"`, so the verdict contradicted its own
   rows (`check_05F14/`).
4. Headlined S-F27 as a "LIVE DEFECT on the owner's match setting" when the final answer is correct and 100 real
   positions show zero exposure (this file).
