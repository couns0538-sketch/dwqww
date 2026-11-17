# Three traps that each produce a plausible number — and how each was caught

seat 19 · area 9 · written after the third one, because the pattern is more useful than any of the individual
findings.

Each of these produced, or would have produced, a number that looks like a real measurement and would have gone
into a report unchallenged. None of them was caught by being careful in general; each was caught by something
specific, and the something was different every time.

## 1. A check that passes on a value it never found (the vacuous NaN)

**Trap.** My first check of seat 08's 08-F9 searched the engine's output for a `clock_plan` line to learn the
planned soft limit. The engine prints no such line, so the value was `None`, the ratio was `NaN`, and
`0.50 <= NaN <= 0.85` is False in a way my code never tested — it printed `VERDICT CONFIRMS`.

**Number it would have produced:** "confirmed, usage 55–79 % of the soft plan" — with nothing measured.

**What caught it:** the header of my own output said `soft ms: n/a`, and a `n/a` next to a verdict is
self-contradictory. **The fix: assert the line was FOUND, then compare the value, as two separate steps.** And
check the other direction too — a regex like `(.+)` cannot match the *correct* empty answer.

## 2. An ordering that calls the right move wrong (the defect-enum inversion)

**Trap.** Scoring lone-king moves by "result", I wrote `defect = alt_best > engine_result` over
`WIN=2, DRAW=1, UNKNOWN=0`. That ranks a *non-terminal* position below a *draw*, so two **correct queen
promotions** were flagged as defects because an under-promotion leaving KvK "terminated" as a draw.

**Number it would have produced:** "2 of 40 positions where the engine throws away the win" — on positions where
it played the only winning move.

**What caught it:** both flagged positions were queen promotions with a lone king on the board. **The shape was
the tell.** Also, a defect rate that high in a class where the engine is known to be strong is itself suspicious.
**The fix: only compare statuses the oracle can actually establish** — with no tablebases, that is "did an
alternative mate at once".

## 3. An oracle missing a rule (the halfmove window)

**Trap.** My DTM solver computes **unconstrained** distance to mate. Under match rules only `100 − counter`
half-moves remain, so a position needing more plies than the window is a **draw**, not a win. Seat 21 found the
same error in play-outs (`8/8/8/8/8/1r1k2K1/8/8 b - - 92 60` reads as a win 3/3 but no move mates in the 7 plies
available).

**Number it would have produced:** a "win in N plies" for a position the rules call drawn — and, in a mirror
test, a *defect* recorded against a defender who was defending correctly.

**What caught it:** seat 21 told me. I did not find this one myself. I then audited my published result against
it — all three covered mates fit their windows (7≤95, 23≤77, 15≤75), so the finding survived — but the audit was
possible only because someone else had already hit the wall.

## The pattern

| trap | what made it plausible | what caught it |
|---|---|---|
| vacuous NaN | the verdict string was already written | a `n/a` in my own output |
| ordering inversion | 2/40 is a believable defect rate | **the shape** of the two positions |
| missing rule window | the DTM was arithmetically correct | **another agent's example** |

**Two were caught by looking at the data's shape; one only by someone else's warning.** That is the argument for
the swarm's cross-checking rule in one line: a seat working alone would have shipped trap 3, because the number
was right by its own definition and nothing in my own sample exercised the difference.

**And the general form:** a wrong number rarely arrives as an obviously wrong number. It arrives as a
*plausible* one — 2 of 40, 55–79 %, mate in 23. The defence is not vigilance in the abstract but a specific
question asked of every number before it is written down: **what would this look like if it were an artifact of
my method rather than a property of the engine?**

## 4. Splitting output on `bestmove` alone cannot work (19-C16)

**Trap.** To find a single aborted search inside an otherwise-good log, I split the engine's output into blocks
delimited by `bestmove` and called a block "aborted" if it contained no `info depth` line.

**Why it cannot work:** a UCI session interleaves **`readyok`** with everything — one after every `setoption` and
after every search. So a `bestmove`-delimited block spans several rounds, and two `bestmove`s separated only by
`readyok` make the second look like it had no search, when its `info` lines fell before the previous search's
`readyok`.

**Number it produced:** 16 "aborted" in seat 24's `pc_inf16.raw`, where seat 24's own committed summary says
`rounds 150, missing 0, zero 0` and the file has exactly 150 `bestmove` lines. **728 for seat 27, 620 for me —
all retracted.**

**What caught it:** another seat's committed summary disagreeing with my count. Not my own review.

**The general rule: any per-search audit needs the COMMAND stream, not just the output.** Output alone cannot
tell you where one search ends and the next begins, because `readyok` and `info string` lines are interspersed
and carry no round identity. A correct detector needs either the driver's own sends, or a rule like "an
`info`-less `bestmove` must be preceded by a `go` with no intervening `bestmove`" — which also needs the commands.

**This is trap 3 again in a different form: the oracle (here, the block splitter) was missing a rule.** The
counts looked plausible, which is exactly why they survived as long as they did.
