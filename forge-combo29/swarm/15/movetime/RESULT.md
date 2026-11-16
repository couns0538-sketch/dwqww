# Is there a character cutoff in `movetime`? — NO, in the range 1000–3000 ms

PC r15, **PC20**, **Threads 1**, Hash 16. 5 boards × `movetime 1000` and `3000` × 5 runs = 50 searches.
Prediction committed and pushed first. Raw: `mt_out.txt`, `mt.jsonl`.

## The table

| board | `movetime 1000` | `movetime 3000` |
|---|---|---|
| startpos | 990 ms (**99 %**), d20, 925,222 n | 2,990 ms (**100 %**), d26, 4,733,095 n |
| G-mid-1 | 990 ms (**99 %**), d24, 1,651,453 n | 2,990 ms (**100 %**), d26, 3,305,111 n |
| G-mid-2 | 990 ms (**99 %**), d21, 1,493,714 n | 2,990 ms (**100 %**), d22→27, 4,003,421 n |
| G-end-1 | **417–453 ms (42 %)**, **d64**, 2,196,864 n | **416–423 ms (14 %)**, **d64**, 2,196,864 n |
| G-end-2 | **22 ms (2 %)**, **d64**, 94,406 n | **21–22 ms (1 %)**, **d64**, 94,406 n |

## The answer

**There is no character cutoff between 1000 and 3000 ms.** On every board where real search work
exists, the engine honours the slice at **99–100 %** of both 1000 and 3000 ms — not merely
"proportionally", but to within 10 ms of the whole slice.

The two cells that stop early are the ones where **the depth ladder ends first**: G-end-1 and G-end-2
both hit **depth 64 — the engine's clamp maximum** — and produce **the identical node count at both
slices** (2,196,864 and 94,406 respectively). The clock never limited them; the ladder did. G-end-2 is
the one-legal-move board from 15-F31, and G-end-1 is a K+R-vs-two-rooks position that resolves to a
forced mate quickly.

So the earlier `movetime 100` result (~90 % of the slice) and these (~99–100 %) differ only because a
100 ms slice is short enough for one iteration's granularity to show; at 1 s and above the engine
lands within 10 ms of the requested time.

## Determinism — stronger than I predicted

**All 10 (board, movetime) cells gave identical node counts across 5 runs.** Not one varied. Combined
with 15-F33 (a single differing run at `movetime 100`), the picture is: **the time path is deterministic
once the slice is long enough that iteration granularity does not straddle it.**

## My prediction, honestly

| # | prediction | verdict |
|---|---|---|
| P1 | 1000 ms within 850–1100 ms everywhere | **held for 3 of 5 boards, refuted for the 2 depth-64 boards** |
| P2 | 3000 ms within 2550–3300 ms everywhere | **same** |
| P3 | fraction at 3000 not >10 points below 1000 | **refuted on G-end-1** (42 % → 14 %) — but for the depth-64 reason, not a clock change |
| P4 | exact node equality in ≥3 of 10 cells | **held, 10 of 10** |
| P5 | legal bestmove in all 50 runs | **held** |

P1–P3 were written as if every board could consume its slice. Two boards cannot, because their search
space is exhausted at depth 64. That is my prediction being under-specified, not a defect — and it is
the same lesson as 15-F31, which I had already learned and did not carry across. Recorded plainly.

## Scope

- One build, one regime, Threads 1, 5 boards, two slices. Not a survey.
- "No cutoff in 1000–3000" says nothing about 100–1000 or above 3000; the 100 ms observation is in
  `clockpath/RESULT.md`.
- The depth-64 early stop is a property of these positions, not a general statement about endgames.
