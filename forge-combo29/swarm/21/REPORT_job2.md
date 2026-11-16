# REPORT job2 — CHECK of 30-F6 (area 1 seat checking area 10's finding), seat 21

**What was asked.** THE CYCLE 2(a): take a finding marked NEW that nobody has confirmed or
refuted yet and reproduce it from its command file alone, with a harness of my own. Seat 30
(area 10) left 30-F6 unconfirmed.

**The answer.** 30-F6 is **CONFIRMED**: `ucinewgame` really does reset the board to the
start position, and a `position ...` command placed before it is discarded. Seven cases,
each in a fresh process, with controls that separate the tested position from startpos
(30 vs 28 vs 20 plies of perft 1). Additionally: the reset costs a GUI nothing if it sends
`ucinewgame` first (case E: 28 = the new position's own count), and it survives a search
having run (case R: 20).

**How sure.** High: every number is pasted from the committed script's summary, the
control case without `ucinewgame` reads 30 (the position's own count) so the harness can
see the difference, and the code agrees (`src/uci.cpp:254-257`).

## A defect in the finding's own evidence (not in the claim)

30-F6's evidence line compares `nodes 20` with "the 29 after e2e4". **Both are 20.**
After 1.e4 it is Black to move and Black has exactly 20 legal moves; startpos perft 1 is
also 20. So the finding's quoted command cannot distinguish the two positions, and its
"29" is wrong for perft 1 (29 is perft 1 *before* e2e4 is applied, i.e. the count of White's
moves at the start). The claim is still true — my controls (30 vs 20 vs 28) show it — but
the recorded evidence does not. This is worth telling seat 30: a reader re-running its
command gets 20 and could conclude the opposite.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read the board, find an unchecked NEW finding | done | `board.sh`, `confirms.sh` (no C line names 30-F) | 30-F6 chosen |
| prediction committed before the first measuring command | done | `job2/prediction.txt` | 6 predictions |
| first harness attempt | done, **discarded** | `job2/out_v0/` (startpos vs e2e4 both 20) | control was confounded; I found it and rewrote |
| second harness with separating positions | done | `job2/check_30f6.py`, `job2/out/` | CONFIRMS |
| measured startpos reference (not assumed) | done | `job2/out/REF_startpos_perft1.txt` | 20 |

## Table (pasted from `job2/out/summary.md`)

```
measured startpos perft 1 = 20

| case | perft 1 nodes | equals startpos? | what it shows |
|---|---|---|---|
| N1 position, NO ucinewgame (control) | 30 | False | the position's own count |
| N2 ucinewgame BEFORE position (control) | 30 | False | reset must not matter here |
| P position then ucinewgame | 20 | True | the claim |
| P2 FEN then ucinewgame | 20 | True | the claim, FEN form |
| R ucinewgame AFTER a perft 3 search | 20 | True | the claim with a search first |
| E ucinewgame, then a NEW position | 28 | False | GUI that resets per game |
| N3 pos2 without ucinewgame (control) | 28 | False | second position's own count |

controls separate positions from startpos: True
=> CONFIRMS 30-F6
```

## Suspicions, not proven

- Whether any real GUI sends `ucinewgame` in the order the finding warns about. Arena and
  CuteChess send `ucinewgame` *before* `position`, which case E shows is harmless. I did not
  install a GUI to check.
- Whether `ucinewgame`'s board reset is intentional or a bug. The code comment at
  `src/uci.cpp:254-257` has no explanation; the UCI spec says `ucinewgame` "is sent to the
  engine to inform it that the next search will be from a different game", which does not
  require resetting the board. Not proven which the owner wants.

## What I did NOT do

- Did not check seat 30's other findings (30-F1..F5, F7, F8).
- Did not run this check under a sanitizer: it is a protocol check with no memory access
  under test.
- Did not measure whether `ucinewgame` clears the transposition table (the TT-clear
  question is visible in the code as `searcher.clear()` but I did not measure its effect).

## What I am NOT sure about

- The exact perft 1 of the 5-ply Ruy Lopez position (30) is what the engine says and what
  my control case says; I did not cross-check it against python-chess. It is only used as
  "not 20", which the engine and python-chess cannot disagree about here.

## Times

see `job2/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job2
check_30f6.py  out  out_v0  prediction.txt  stamps.txt
```
