# A huge opponent clock is not a bound: the no-stop leg

`S-C37` leg D / `S-F108`. Seat 02's `S-F4` is right that a `go` naming only the opponent's clock hangs the GUI
silently. Its aside — that a huge `btime` does bound a White-to-move search, so a big number works around it —
is wrong. This page is the evidence for the refutation, and it exists because the first form of that evidence
(one 20 s run quoted in chat) named no stopping condition in a file.

## Why an 8-second cap is not enough to settle it

`check_partial_clock.py` caps each search at 8 s (`MEASUREMENT_TRAPS.md` Trap 6). That is enough to show the
command does not answer, and not enough to say why. "Did not finish in 8 s" fits two different worlds:

- a slow but **bounded** search, which a large clock value could still be bounding; or
- **no bound at all**, in which case no clock value helps.

The aside is exactly the claim that the first world is the true one. So the test has to distinguish them, and
the only way is to record what the search does when nothing stops it.

## The two legs

`check_partial_clock_long.py`, PC r15 + PC20, `Threads 1`, `Hash 16`, position named as White to move:

    r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 w - - 0 1

both legs run `go btime 6000000`.

| leg | stopping condition | bestmove lines | deepest depth | nodes | last info `time` |
|---|---|---|---|---|---|
| D1 | **none** — process killed at 8 s | **0** | 26 | 6,330,884 | 6,884 ms |
| D2 | `stop` sent at 20 s | 1 (`a3b4`), at 20.0–20.2 s | 30 | 22,399,089 | 13,708–13,951 ms |

D1 is the decisive leg: **no bestmove was produced while nothing stopped it.** A bounded search answers. This one
was still deepening when the process was killed.

D2 is the same command allowed to run, and it produced its bestmove only after the explicit `stop`. Its own last
`info` line reports ~13.9 s of search, i.e. three orders of magnitude past any interpretation of a 6,000,000 ms
clock as a search bound.

Neither leg emitted a single `info string`. The protocol reports nothing wrong while the GUI waits.

## Reproducibility

Three complete runs gave **identical node counts** (22,399,089 in D2; 6,330,884 in D1) and the same bestmove. This
is the `S-C26`/`S-F83` property again — equal node count, equal move — so the demonstration is a fixed point, not
a lucky draw.

## Two runs, two option sets, not comparable numerically

The 20 s standalone capture (`standalone_D_huge_btime_20s.txt`) ran with **default options** and reached depth 27
at 31,011,772 nodes. The PC20 legs here reach depth 30 at 22,399,089 nodes. Different search parameters, so the
numbers differ and **must not be quoted against each other**. What both show is the structural fact: no
bestmove until a stop arrives.

Quote the PC20 numbers when citing this page, because they carry a named stopping condition in a file.

## The mechanism, and why it settles the fix

The engine cannot know when the opponent will move. Therefore the opponent's clock is not a quantity it can
convert into a search bound — not for a small value and not for a huge one. "Send a big number" cannot work,
because the engine is not reading that number as a limit at all.

That makes the fix statement narrow and testable: **print one `info string` and fall back to a bounded default.**
One diagnostic, so the GUI learns it sent a partial clock; one bounded default, so the search ends on its own.
The engine cannot wait for information it will never receive.

## What this does not claim

- Not that `S-F4`'s main half is wrong — it is confirmed, in `check_partial_clock.txt` legs A/B/C.
- Not that the engine should guess the opponent's clock or invent a move time from it.
- Not that D1's 8 s cap bounds anything. D1's cap is on the **test harness**, which is the only place a cap can
  honestly live here. See Trap 6.
