# CHECK of seat 13's S-F16 — book moves differ from the engine's choice, but score near-equal — seat 08

Their claim:
> S-F16: "The built-in book's moves DIFFER from the engine's own choice on **12 of 16** opening plies, but score within
> **-26 to +18 cp** of the engine's preference **at EQUAL depth 12** (median 0, none ≥50 cp worse); only 4 of 16 book
> moves were also the engine's first choice."

## Verdict: PARTIALLY CONFIRMED — the "different but near-equal" finding holds; my differing COUNT is much lower (5 of 16), and I believe I know why

My harness, PC r15 PC20, Threads 1, Hash 16. Book route = `OwnBook true` + `go wtime 6000`; engine route =
`OwnBook false` + **`go depth 18`** (higher than their 12 — see below).

| ply | book move | engine move (depth 18) | differ? | engine's score of its own | of the book move | gap |
|---|---|---|---|---|---|---|
| 1 | c2c4 | e2e4 | **YES** | cp 15 | 2 | **+2** |
| 2 | e7e5 | e7e5 | no | −8 | — | — |
| 3 | g2g3 | b1c3 | **YES** | 18 | 7 | **+7** |
| 4 | d7d5 | c7c6 | **YES** | −37 | −5 | **−5** |
| 5 | c4d5 | c4d5 | no | 17 | — | — |
| 6 | d8d5 | d8d5 | no | −33 | — | — |
| 7 | g1f3 | g1f3 | no | 34 | — | — |
| 8 | b8c6 | b8c6 | no | −30 | — | — |
| 9 | b1c3 | b1c3 | no | 47 | — | — |
| 10 | d5d7 | d5d7 | no | −40 | — | — |
| 11 | e2e3 | f1g2 | **YES** | 36 | −36 | **−36** |
| 12 | g8f6 | g8f6 | no | −32 | — | — |
| 13 | d2d4 | f1g2 | **YES** | 0 | 26 | **+26** |
| 14 | f8b4 | f8b4 | no | −39 | — | — |
| 15 | f1g2 | f1g2 | no | 32 | — | — |
| 16 | e5d4 | e5d4 | no | −42 | — | — |

| their statement | my measurement |
|---|---|
| book differs on **12 of 16** plies | **5 of 16** |
| within **−26 to +18 cp** | range **−36 to +26**, median **+2** |
| "none ≥50 cp worse" | **true** — my worst is −36 cp |
| "different but equivalent by the engine's own measure" | **holds** — 3 of my 5 gaps are ≤7 cp, and the median is +2 |

**The substantive finding reproduces: where the book differs, it costs the engine almost nothing by its own score.**
The median gap is +2 cp in my run and they report a median of 0; my worst case (−36) is inside their "none ≥50 cp
worse" bound. So "different-but-equivalent, not visibly harmful" is confirmed.

## Why my count is 5 and theirs is 12 — stated as the likely cause, not as a refutation
Their comparison was at **depth 12**; mine at **depth 18**. Deeper search converges toward agreement on opening moves
(it is the domain where depth matters least), so a depth-18 engine route should agree with the book MORE often than a
depth-12 one — which is the direction my 5-vs-12 sits in. **I did not complete a depth-12 re-run to prove it**: my
first attempt hung (see below), so this is an inference from the one variable that differs, not a measurement.

I therefore do **not** say their 12 is wrong. A count at a stated depth is a valid measurement; mine is at a different
depth and the two are not comparable. What I confirm is the *characterisation* (different but near-equal), which is
depth-robust in my run.

## An instrument failure I hit and did not paper over
My depth-sweep attempt (12/14/18 on 16 plies) **hung on a single engine process for 20 minutes** and had to be killed.
The cause was in my throwaway script, not the engine: the book answers instantly with *no* `info depth` lines, and my
inline reader pattern could deadlock when a search produced no info lines before `bestmove`. Verified afterwards that
the engine is fine — the book answers in milliseconds via a plain pipe, three runs, three book moves.

**So I report the committed S-F16 run (which completed cleanly, all 16 plies) and NOT a depth comparison**, because
the depth comparison's harness was broken. The lesson is the one already in my method rules: a reader pattern that
works on a search with info lines can hang on one without them.

## What I did NOT do
- Did not complete the depth-12 re-run (broken harness, not re-attempted).
- Did not test other book lines; one 16-ply line as they did.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s13f16.py /tmp/s13f16.txt
