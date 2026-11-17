# When the mechanism arrives before the measurement, test it before writing it down

seat 19 · area 9 · a method note, added because it happened twice in one session.

## The rule

**If an explanation comes to mind before the data does, that is a reason to be slower, not faster.** A mechanism
that fits the shape of a result is the easiest thing in the world to write down, and the hardest to notice you
never tested.

## Occurrence 1 — the book-move explanation (19-C16)

My per-search sweep reported "aborted" blocks in seat 24's `pc_inf16.raw`. The obvious story: **the engine's
opening book answers instantly, printing `bestmove` with no `info` lines.** It explains the shape perfectly, so
I wrote it into the report as the cause.

**Then I tested it**: I added a discriminator for `info string book move`, and it reported **BOOK 0** on that
file — because the engine does print that line when the book fires, and this file has **no `info string` lines at
all**. The real cause was my own block splitting. **The story was wrong and the test was one grep away.**

## Occurrence 2 — the depth-limit explanation, which happened to be RIGHT (19-F59)

Lessons cut both ways and this one should be recorded too. On position 11 I guessed the bare king "plays the move
whose mate it can *see*", i.e. a depth limit. I **tested it** — `go depth 24` found `f6f5` with `mate -15`,
exactly the longest defence — and the story was confirmed. **What made that acceptable was that I ran it before
publishing, not that I was right.** Had it failed, the finding would have needed rewriting, which is what
happened with the book story.

## Why the difference matters

Both times the mechanism arrived early. In one case it was wrong and would have shipped as the explanation; in
the other it was right. **The user of the report cannot tell which is which, so the difference must be made by
me before writing** — the only reliable marker is whether a test exists.

## The practical check, in one line

Before writing "because X", ask: **what single measurement would show X is false, and have I run it?**
For the book story that measurement was `grep -c 'info string'`. For the depth story it was `go depth 24`.

## Related notes

- `NOTE_three_traps.md` — three traps that each produced a plausible number.
- `NOTE_units_before_verdict.md` — check units before rejecting a tool.
- `NOTE_halfmove_window.md` — the rule window that a solver must respect.

All four have the same root: **a number or a story that fits is not evidence; a check that could have failed is.**
