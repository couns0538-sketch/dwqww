# REPORT job5 — seat 20, area 10 job 1 (a second look): check of seat 02's S-F2

**what was asked** — The cycle's step 2(a): take a finding marked NEW that nobody has confirmed, and reproduce it
from its sentence, on my own build, with a harness I wrote. Seat 02's S-F2 was unconfirmed: `go searchmoves`
naming no legal root move answers `bestmove 0000` on a board with 20 legal moves.

**the answer** — **CONFIRMS.** On startpos with the book off, both `go searchmoves depth 2` (no move named) and
`go searchmoves e7e5 depth 2` (a move illegal for white) print `info string searchmoves restriction has no legal
root moves` and then `bestmove 0000`, with 0 nodes searched. The positive controls behave correctly: a restriction
naming legal moves is respected exactly (`go searchmoves a2a3 b2b3 depth 4` -> a2a3), and unrestricted `go depth 2`
/ `go movetime 20` search normally (54 / 13,102 nodes). Identical on the ASan+UBSan build, 0 sanitizer lines.

**how sure** — certain about the behaviour (six cases x two builds, full transcripts committed). The practical
risk depends on a GUI sending a malformed or illegal `searchmoves`, which I did not survey.

## Honesty numbers
Release build `/agent/repos/build-base/forge` sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`;
ASan+UBSan build `/agent/repos/build-asan/forge` (`nm` 35 `__asan_` / 15 `__ubsan_`, pins 312866 / 862329 also
equal). The sanitizer runner used is the one proven by the planted-fault copy (`../job3/plant_build.sh`,
`../job3/sanrun.sh`, `../job3/out/planted.meta` = 3 lines, `../job3/out/clean.meta` = 0 lines). Release pins:
4/4 in `../HONESTY.txt`.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction, alone | done | `PREDICTION.txt` (commit c1c4c7edf) | 5 predictions |
| my own harness | done | `check_s02f2.py` | reads the whole answer, counts nodes |
| empty searchmoves | done | `out_check.txt` case a | 0000 + info line, 0 nodes |
| illegal searchmoves | done | case b | same |
| legal restriction (control) | done | case c | a2a3, 56 nodes, no info line |
| unrestricted (control) | done | cases d, e | d2d4, 54 / 13,102 nodes |
| the source path | done | `src/search.cpp:2210-2214` + terminal-root branch | restriction-empty treated as terminal |
| ASan+UBSan repeat | done | `check_s02f2.txt` (asan rows) | same answers, 0 sanitizer lines |

## Findings
1. **S-C2 = CONFIRMS seat 02's S-F2.** Show it again: `python3 check_s02f2.py <release> <asan> .`
2. An illegal `searchmoves` name is treated the same as an empty one — both collapse to "no legal root moves".
   That is one behaviour, not two: the restriction is intersected with the legal list and the intersection is empty.
3. The reply is not a searched answer: 0 nodes, and the two `info depth` lines carry `nodes 0` (the drawn-root
   reporting loop). Anyone testing for it must test nodes = 0, not "no depth lines".

### Suspicions, not proven
- That a GUI receiving `bestmove 0000` in a live game loses on the spot (some GUIs substitute a move). Not tested;
  I have no GUI here and the PC's GUIs are not mine to survey.

## What I did NOT do
- I did not test `searchmoves` together with `ponder`, `infinite` or a clock.
- I did not test a restriction that names a move which becomes illegal only after the move list is applied.
- I did not test the PC's Windows build or its GUI behaviour after `0000`.

## What I am NOT sure about
- Whether Opus considers this already covered by the known-list line about `0000` on finished positions. Seat 02
  argues it is beyond it (a 20-move board), and I agree, but that is a judgement for Opus.

## Times: see `stamps.txt`
## The last command's output
```
$ ls forge-combo29/swarm/20/job5/
CHECK_s02F2.md  PREDICTION.txt  check_s02f2.json  check_s02f2.py  check_s02f2.txt
out_check.txt  stamps.txt
```
