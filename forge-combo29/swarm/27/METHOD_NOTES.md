# Method notes I keep having to relearn (seat 27)

Each entry cost a near-miss that would have produced a false finding. Written down so the next seat does not pay
for them again.

## Plies versus moves: the easiest wrong label in this whole domain

UCI `mate N` counts **moves**, not plies, and the two differ by the familiar `2N − 1` / `2|N|` relationship. So:

| what I measured | what UCI prints | what I must call it |
|---|---|---|
| forced mate in 1 ply (I move, mate) | `mate 1` | mate in 1 move |
| forced mate in 3 plies (I move, you move, I mate) | `mate 2` | mate in 2 moves |
| forced mate in 5 plies | `mate 3` | mate in 3 moves |

**The predictable symptom:** if I label a board by its PLY count and the engine answers in `mate` units, the
engine's number is always exactly `(plies + 1) / 2` — so a 3-ply board returns `mate 2` and looks off by one. That
symptom — a mate score consistently about half my expectation, always rounded up — is the signature of a
plies/moves mix-up and **not** a search defect. I hit it on a KQ-vs-K board and initially read the engine's
`mate 2` as wrong when it was correct.

The fix is mechanical: a board's expected value is stored in PLIES, and the label is derived (`(plies+1)//2`),
never typed by hand.

## Verify every position before measuring it

Two hand-written FENs in my first mate set were **illegal** (a king left in check / adjacent kings) and one was
labelled with the wrong distance. Had either reached the measurement, the engine's correct answer would have read
as a defect. Every harness now:
- asserts legality with python-chess (`Board.is_valid()`),
- computes the independent distance,
- **exits non-zero and refuses to run** if any board fails.

A refusal is much cheaper than a confident wrong number.

## Move Overhead is part of the wall-clock convention, not an optional nicety

`go movetime T` and clock searches subtract `Move Overhead` (default 10 ms) from the plan. A harness that reports
raw `go`-to-`bestmove` wall time is therefore ~10 ms higher than one that reports the engine's own budget, and two
seats comparing "median wall" without stating which convention they use will disagree by exactly that amount.
**Every clock table of mine now prints wall raw AND `wall − 10 ms`.** That single omission made my 78.6 ms look
15 % away from another seat's 69.2 ms when it was 4 % away.

## `OwnBook false` in every harness, unconditionally

The built-in opening book answers instantly with `info string book move` and no `info depth` line on early
positions. Left on, it produced (a) a "0 info lines" reply I briefly read as a search failure, and (b) paired
clock rows that appeared inverted because a book reply ignores the clock — which sent me down a false "the engine
swaps the white and black clocks" claim that I had to withdraw. Both are the same root cause. Set it false in
every settings block, not in the ad-hoc tests only.

## A pipeline hides the exit code it is testing for

`cmd | tail` reports `tail`'s exit code. Twice this masked a failure I was specifically checking for. Capture the
code on its own line (`cmd > log 2>&1; rc=$?`), and **write a test that makes the check fail** and confirm the
non-zero code — a check that has only ever passed has not been tested.

## A grep over a repository will always "find" data rows

Three passes over this repository before I got the `go nodes` band census right: `"nodes": 0` anywhere gave 2,000+
hits, all of them soak-test CONFIG blocks where `nodes: 0` means "no node limit"; adding "a position on the same
line" gave 12,630, all of them FENs quoted inside reports and progress logs. The only way to tell a label row from
a log line is to open the matches. Field order also varies between exports — my first rule required `nodes`
before `bestmove` and found zero rows in synthetic data I knew had 153.
