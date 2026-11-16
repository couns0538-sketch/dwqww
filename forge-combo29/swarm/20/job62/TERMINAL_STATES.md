# seat 20 — job 62: `score mate 0` on a checkmated root is CORRECT — I withdraw S-C20

Seat 11 measured the terminal-state ladder and concluded that `mate 0` on a checkmated root is correct, not a defect.
That supersedes **my S-C20** (which confirmed seat 21's 21-F11) and **seat 25's S-F6**.

## Why I was wrong
S-C20 said `mate 0` "is not a legal claim… a mate is at least one ply away" and that the info-line count showed a bogus
full-depth report. That was an **assertion about UCI semantics that I never checked against the UCI definition**. UCI
defines `score mate y` as *mate in y moves for the side to move*, so for a side that is **already checkmated**,
y = 0 is exactly right, and `bestmove 0000` is the only sensible reply. My finding described correct behaviour as a
fault.

## The ladder, measured myself (base 6b98f217 + S14, Threads 1, `go depth 5`)

| position | python-chess | engine answer |
|---|---|---|
| **checkmated now** (`4R1k1/5ppp/8/8/8/8/5PPP/6K1 b`) | checkmate, 0 legal moves | `0000` / **`mate 0`** / 0 nodes |
| **mate in 1** (`6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w`) | not terminal, 27 legal | `d1d8` / **`mate 1`** / 140 nodes |
| **stalemate** (`7k/5Q2/6K1/8/8/8/8/8 b`) | stalemate, 0 legal | `0000` / **`cp 0`** / 0 nodes |
| **KQ v K** (dead win) | not terminal, 27 legal | `h6f8` / **`cp 1131`** / 1,836 nodes |

This reproduces seat 11's ladder (my node counts differ only because my depth is 5 and my mate-in-1 board is a
different Q-mate — theirs was 280 nodes with `d1d8` at its own depth).

**The key observation:** a checkmate and a stalemate are reported **differently on purpose** — `mate 0` versus `cp 0`.
Both have 0 nodes and `bestmove 0000`, but the scores distinguish "you are mated" from "it is a draw". That is
correct reporting, not an inconsistency.

## Status of the affected findings
- **S-C20 — WITHDRAWN.** The `mate 0` behaviour is correct.
- **seat 21's 21-F11 — WITHDRAWN** for the same reason (relayed by the coordinator).
- **seat 25's S-F6 — superseded** (relayed by the coordinator).
- **What survives from that thread, and is still a real defect:** the **info-line count** tracking the requested depth
  with 0 nodes (my S-C7/S-F16 family and seat 25's S-F7 — 64 lines at `nodes 0`). That is a *reporting* oddity on a
  terminal root, not a wrong score, and it is independent of whether `mate 0` is right.

## The lesson I am recording for myself
I confirmed seat 21's claim without checking the UCI definition the claim depended on, because it *sounded* right
("mate 0 is impossible"). A confirmation of "X is wrong" is only as good as the definition of "right" behind it —
and for protocol semantics, the definition is checkable text, not intuition. I should have looked it up before
confirming, exactly as I would have looked up a source line before citing it.
