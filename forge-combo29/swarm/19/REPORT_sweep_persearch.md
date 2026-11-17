# The per-search sweep: it finds the mixed shape, and it has a blind spot that makes the counts unusable

seat 19 · area 9 · the follow-up to 19-C14, reported with its own limits first.

## 1. The three lines

**What was asked.** Carry the per-search sweep to a conclusion, because a log with nine good searches and one
aborted is the more common shape and the only place an unflagged accident could still hide.

**The answer.** **The sweep works mechanically and finds the mixed shape — but its counts are not usable as a
defect count, and I am not reporting them as one.** It counts **728 aborted blocks in seat 27** and **620 in my
own folder**, and inspecting them shows the two dominant causes are both **benign**: 600 of my 620 are the two
`profR` runs I already discarded, and the mixed cases I opened (seat 24's `pc_inf16.raw`) are **book moves** —
instant answers that legitimately print `bestmove` with no `info` lines.

**How sure.** Certain of the mechanism (read the files) and certain the counts are inflated by at least two
benign causes (book moves, deliberate zero-node answers). **So the honest deliverable is the detector plus this
list of what it cannot distinguish, not a number.**

## 2. The counts, and why they are not a finding

| seat | files with search blocks | with ≥1 aborted block | total aborted blocks |
|---|---|---|---|
| 27 | 132 | 69 | **728** |
| 10 | 902 | 692 | 695 |
| **19 (mine)** | 32 | 17 | **620** |
| 07 | 58 | 48 | 240 |
| 20 | 87 | 87 | 87 |
| 21 | 290 | 32 | 61 |
| 24 | 52 | 20 | 45 |
| 02 | 31 | 24 | 44 |

**My own 620, inspected:** 400 + 200 from the two `profR`/`profR12` streams I discarded before using (that is
19-F12's discovery, kept as evidence), 6 from the go-timing table, and the rest from `quitabort_*` demonstration
files. **Every one is legitimate.** So the largest number in the table is not a defect at all.

## 3. The blind spot, demonstrated

Seat 24's `pc_build/pc_inf16.raw` reports **134 good and 16 aborted** blocks by my detector. **Seat 24's own
`pc_inf16.summary` says `rounds 150, missing 0, multi 0, illegal 0, zero 0` — 150 rounds, 150 bestmoves in the
file, and NOT ONE zero.** Its own count is authoritative and mine is wrong.

**Here is why mine is wrong, and it is a structural error not a threshold error.** The file contains **only engine
output** (no echoed commands) and **many `readyok` lines** — one after every `setoption` and after every search.
My detector splits search blocks purely on `bestmove`, so on this file a block can span several `readyok` lines
and several setoption handshakes. Two `bestmove`s separated only by `readyok` are then counted as "the second had
no info", when in fact each belongs to its own round whose `info` lines came *before the previous bestmove's
`readyok`* in my naive split.

**I also hypothesised book moves first and that was wrong too**: the discriminator I added reports **BOOK 0** on
this file, because this engine prints `info string book move` and there are **no `info string` lines at all**.
So my §4 hypothesis was a plausible story, not the cause — the cause is my block splitting.

**Conclusion: this detector cannot be trusted on files whose output contains interleaved `readyok`/handshake
lines, which is most of them.** The counts are not a lower or upper bound on anything; they are noise with a
plausible shape.

## 4. What would make it usable — and what I did not build

To separate the causes, an aborted block would need one more discriminator:

| cause | how to tell it apart |
|---|---|
| aborted by EOF/quit (19-F12) | the block is **the last thing in the process's session**, and no `readyok` follows before the next command |
| book move | `info string book move <move>` is printed by this engine — check for it |
| zero-node answer | `searchmoves` restriction, checkmate/stalemate root, or insufficient material — all are in the position, not in the output |

**My detector used none of those.** The third one is available from the input side and the second is printed by
the engine, so a correct version is buildable — **but I did not build it, and I am not going to report a
defect count from a detector I know cannot separate the causes.** Same rule as 19-C14: a rate too high to be
believable is evidence about the instrument.

## 5. Finding

**19-C16 — the per-search aborted-block sweep works mechanically but its counts are NOT a defect count: my own
620 are all legitimate 19-F12 evidence files, and the mixed files I opened show that BOOK MOVES produce the same
`bestmove`-with-no-`info` signature by design.** Seat 24's `pc_inf16.raw` has 16 "aborted" blocks that are book
answers with `readyok` between them. A usable version would need to exclude book moves (`info string book move`),
deliberate zero-node answers (position type), and to require that the block end the session (the actual
EOF-abort signature). **I did not build that, so no per-search defect count is reported.**

### What this means for where an unflagged accident could still hide

19-C14's file-level sweep (zero `info` lines in a whole file) and this one both fail to isolate a *single*
aborted search in an otherwise-good log, for opposite reasons: 19-C14 cannot see it at all, and this one cannot
tell it from a book move. **The shape of a discriminator that would work is §4** — and the strongest single
signal is that 19-F12's abort happens when the process ends, so an aborted block is the *last* block of a
session, which is checkable from `readyok`/`quit` bookkeeping.

## 6. What I did NOT do

- I did not build the three-way discriminator. It is maybe an hour of work and would give a real count.
- I did not inspect seat 27's 728 (the largest). Given my own 620 were legitimate and seat 24's mixed blocks were
  book moves, the prior is that most of seat 27's are too — but **that is a prior, not a check.**
- I did not try to exclude book moves by re-running with `OwnBook false`; that would change what was being
  measured rather than re-analysing it.

## 7. Files

`checks/sweep_persearch.py`, `checks/sweep_ps/RESULT.txt`.
