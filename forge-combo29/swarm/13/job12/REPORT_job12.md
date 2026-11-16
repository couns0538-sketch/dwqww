# REPORT_job12 — are the PC's six options wired, and the book asymmetry

## What was asked
Nothing specific; this is my own search for a real engine fault after a run in which every PC-path
result of mine turned out to be methodology rather than a defect. I tested whether the six options
FABLE file 5 added are actually wired, since a silently inert tuning option would waste the owner's
time.

## The answer, in two parts

### 1. Five of the six options are demonstrably wired; the sixth is wired but conditionally inert
Each option was changed alone against an S14 baseline, fresh process, Threads 1, Hash 16, on five
probes (bench 11, and depth-12 searches of a tactical, a middlegame, a mate-in-1 and a near-fifty
position):

| option | default -> variant | changed on | verdict |
|---|---|---|---|
| CuckooRep | false -> true | bench 11, tactical d12, middle d12 | **wired** |
| HistRework | 0 -> 2 | bench 11, tactical d12, middle d12 | **wired** |
| TtPruneV2 | false -> true | bench 11, tactical d12, middle d12 | **wired** |
| CorrHistV2 | false -> true | bench 11, tactical d12, middle d12 | **wired** |
| MateAlphaGuard | false -> true | bench 11 | **wired** (bench only, on these probes) |
| OwnBook | true -> false | nothing on these probes | wired but **conditionally inert** — see 2 |

### 2. `OwnBook` fires only on GAME searches, and the effect is large
`OwnBook true -> false` changed nothing on any of my five probes. That is **correct behaviour, not an
unwired option**: `src/uci.cpp:679` computes

```cpp
const bool game_search = (limits.time_ms >= 0 || limits.movetime_ms >= 0) && !limits.infinite &&
                         !limits.ponder && !limits.search_moves_specified && limits.mate_moves == 0;
if (game_search && own_book && !book.empty() && game_ply(board) < book_depth) { ... }
```

so the book applies to **clock or movetime searches only** — not to `go depth`, not to infinite, not to
ponder. My probes used `go depth 12`, which is analysis, so the book correctly stayed out of the way.

Testing the game path shows what it actually does. Startpos, PC r15, PC20, Threads 1, Hash 16:

| command | OwnBook | bestmove | info lines | book line |
|---|---|---|---|---|
| `go depth 12` | true | `e2e4` | 12 | none (analysis — correct) |
| `go depth 12` | false | `e2e4` | 12 | none |
| `go movetime 200` | **true** | `e2e4` | **0** | `info string book move e2e4` |
| `go movetime 200` | false | `e2e4` | 16 | none |
| `go wtime 6000 btime 6000 winc 60 binc 60` | **true** | **`e2e4`** | **0** | `info string book move e2e4` |
| `go wtime 6000 btime 6000 winc 60 binc 60` | false | **`d2d4`** | 18 | none |

Two things follow, and the second is the one that matters:

- With the book on, a clock search answers **instantly with zero nodes of search** — the engine plays a
  book move without searching at all.
- **The move differs**: with the book on the engine plays `e2e4`; with it off, the same position and
  clock play `d2d4`. So the book is not merely a speed optimisation, it changes what the engine plays.

### How much of the opening the book governs
Walking a game with `go movetime 100` and the book on, playing whatever the engine answers:

**16 consecutive plies — the whole opening, through ply 15 (`e8g8`) — were answered from the book with
zero `info` lines.** The clock-side ply 16 `b1c3` was the first real search (14 depth lines).

## Why this is worth reporting
It is not a defect — the code is doing what it says. But it has three practical consequences for the
owner's matches, none of which are obvious from the option list:

1. **A book-on match and a book-off match measure different things.** 16 plies of opening are not
   searched at all, so a strength measurement that includes them is partly a measurement of the book.
2. **`go depth` probes will never see the book.** A harness that validates the engine with `go depth`
   (as most of ours do, and as my own honesty checks do) cannot detect a book problem, because the book
   is not consulted on that path. File 3's note that seats observed "a few start positions answered
   from the built-in book" applies to clock/movetime searches.
3. **A book answer has no `info` lines at all.** A harness that waits for an `info depth` line, or that
   treats zero info lines as a failure/hang, will mis-classify every book move. This is a third trap in
   the same family as the depth-64 cap (S-F14) and 19-F12: an absence of output that is not an absence
   of function.

## Settings and build
PC r15 sha256 `068f0927...`, `-DFORGE_MATE_ALPHA_GUARD=1`. Baseline S14 with Threads 1 and Hash 16,
fresh process per run, every option name validated against the exe's `uci` list. The book is the
**built-in** one — `src/book_data.inc`, 2,616 Polyglot-compatible entries, `Book File` default
`<empty>` — so this needs no external file and applies out of the box.

## Findings
- S-F15: `OwnBook` is consulted **only** on game searches (`time_ms >= 0 || movetime_ms >= 0`, not
  infinite, not ponder, no searchmoves, no mate limit) per `src/uci.cpp:679-681`, so `go depth` never
  sees the book. On the game path it changes behaviour substantially: startpos `go movetime 200` with
  OwnBook true answers `e2e4` with **0 info lines and 0 search**, versus 16 depth lines with it false;
  a clock search switches bestmove from `d2d4` (book off) to `e2e4` (book on). Walking a game, the
  **first 16 plies were all book moves with zero search**. Not a defect — a property with match
  consequences, and a third "absence of output is not absence of function" trap for harnesses.
  Reproduce: `cd forge-combo29/swarm/13/job12 && python3 options_wired.py ~/b/pc/forge /tmp/ow`, then
  the book walk (`out/book_walk.json`).

## Suspicions, not proven
- Whether the book's 16 plies help or hurt the owner's match strength is a match question I have not
  run. The book's lines are short and mainline (e4 c5 c3 d5 …), so it is probably fine, but "probably"
  is all I can say.
- `book_depth` defaults to 30 plies, and my walk entered the book for 16 plies before leaving it — I did
  not test whether that is a book-entry limit or simply where the book has no entry.

## What I did NOT do
- No match, so no strength claim.
- Did not test `Book Depth` / `Book Variety` effects, or an external `Book File`.
- Did not test the book on the base build beyond confirming the same 2,616-entry `book_data.inc` is
  present and the same options are advertised.

## What I am NOT sure about
- The book walk used `go movetime 100`, which is a game search, so it is the right path; but the walk
  is one line, and a different first move would enter different book sub-trees.
- `info string book move` is easy to detect, but a harness may also see the `ponder` prediction on the
  same line in ponder mode; I did not test that.

## Files
`options_wired.py` (the six-option sweep), `out/options_wired.json` (all rows), `out/book_walk.json`
(the 24-ply walk with per-ply book/search classification), `stamps.txt`.

## Last command output

```
$ ls
options_wired.py
out
REPORT_job12.md
stamps.txt
```
