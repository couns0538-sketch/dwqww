# S-C3 — CONFIRMS 27-F2 (`go nodes N` below one root iteration), and finds what N counts

Checked by seat 28 (area 8) on my own Release build (`~/build/base-release/forge`, sha256
`e06310ec…16a83`, all four honesty numbers matched — `../HONESTY.txt`). Seat 27's files were not read by
my harness; the claim was restated from its FINDINGS line alone.

## The claim
27-F2 (seat 27, area 7): "`go nodes N` below one root iteration (N < 26 at startpos) answers the first
legal move in generation order (a2a3) with no info line at all; N = 26 answers d2d4."

## Verdict: **CONFIRMS**, down to the exact number, with the book trap controlled
`check_27f2.py`, pasted:

| position | nodes | OwnBook | bestmove | info depth lines | book lines | answered | legal |
|---|---|---|---|---|---|---|---|
| startpos | 1 | false | a2a3 | 0 | 0 | True | True |
| startpos | 5 | false | a2a3 | 0 | 0 | True | True |
| startpos | 25 | false | a2a3 | 0 | 0 | True | True |
| startpos | 26 | false | d2d4 | 1 | 0 | True | True |
| startpos | 27 | false | d2d4 | 1 | 0 | True | True |
| startpos | 200 | false | d2d4 | 2 | 0 | True | True |
| NONBOOK | 1 | false | a2a3 | 0 | 0 | True | True |
| NONBOOK | 25 | false | a2a3 | 0 | 0 | True | True |
| NONBOOK | 26 | false | a2a3 | 0 | 0 | True | True |
| NONBOOK | 200 | false | c1f4 | 2 | 0 | True | True |
| startpos | 1 | TRUE (book control) | a2a3 | 0 | 0 | True | True |

The switch is exactly at 26 at startpos: 25 → `a2a3` with zero `info depth` lines, 26 → `d2d4` with one.
That is seat 27's number, reproduced on my build with my own harness.

## The book trap, controlled
Seat 20's S-F12 warns that with the default `OwnBook true` a startpos answer can look unsearched. Every
measured case above sets `OwnBook false` and the book-line count is 0 everywhere, so no answer in the
table is a book move. **Beyond the finding:** in my build the book does not answer startpos at all —
`go depth 8` on startpos with `OwnBook true` returns `d2d4` after 8 real `info depth` lines, with 0 book
lines, and `Book File` defaults to `<empty>`. So on THIS build the startpos appearance is not a book
artefact; it is genuine.

## Beyond the finding: what N actually counts
`threshold_27f2.py`, pasted (startpos has 20 legal moves, NONBOOK has 51):

startpos:

| nodes | bestmove | nodes in the last info line |
|---|---|---|
| 1..25 | a2a3 | 0 |
| 26..40 | d2d4 | 26 |
| 60..200 | d2d4 | 54 |

NONBOOK:

| nodes | bestmove | nodes in the last info line |
|---|---|---|
| 1..40 | a2a3 | 0 |
| 60..100 | e1g1 | 55 |
| 200 | c1f4 | 133 |

So:
1. **The threshold is not the constant 26 — it is one root iteration of THIS position.** NONBOOK keeps
   answering `a2a3` at 40 nodes and only moves at 60, with the first completed iteration reporting 55
   nodes. Startpos' first iteration reports 26. 27-F2's "26" is correct for startpos and should not be
   read as a global constant.
2. **The reported node count equals what the finished iteration consumed** (26, 54 at startpos; 55, 133
   at NONBOOK) and the answer is always `root_candidates.front()`, i.e. generation order — at NONBOOK
   that is `a2a3`, which is legal but is not the engine's considered move.
3. **The unsearched answer is not "no output"**: it is `bestmove` with zero `info depth` lines, so a GUI
   sees a legal move and no score. A harness that counts only `bestmove` lines records success.

## How to see it again
```
cd forge-combo29/swarm/28/checks
python3 check_27f2.py ~/build/base-release/forge /tmp/c27f2.tsv
python3 threshold_27f2.py ~/build/base-release/forge
```
Raw: `check_27f2_out.tsv`, `check_27f2_out.md`, `threshold_27f2_out.txt`.

## A harness mistake of my own, recorded
My first attempt at the book control was a `printf '...go depth 8\nquit\n' | forge` pipeline, which
answered `a2a3` with no info line and looked like the book. The cause was the shell pipeline: `quit`
reached the engine while the search was still queued, which is the "quit during a search" path (seat 20's
S-F11). Re-running through `timing.Engine`, which waits for `bestmove`, gives `d2d4` after 8 info lines.
Every number in this check comes from the waiting harness; the `printf` result is not used anywhere. This
is the same class of error as my job-1 `README_HARNESS_BUG.md`, so it is recorded rather than dropped.

## What I did NOT do
- Did not test `go nodes 0` (seat 20's S-F11 covers it) or `go softnodes`.
- Did not read the source to confirm which counter `go nodes` decrements; the finding is behavioural.
- Not under a sanitizer.

## What I am NOT sure about
- Whether "one root iteration" is the engine's intended meaning of `go nodes N` for small N or whether
  a minimum of one full iteration is a deliberate floor. The behaviour is confirmed; the intent is not mine
  to decide.
